"""
RAG retrieval and generation quality evaluation.

Uses golden QA pairs to verify:
- Retrieved context is relevant to the question
- Generated answers are faithful to the context
- Token efficiency meets targets

These tests require LLM API access (via deepeval).
Run with: make test-eval
"""

import pytest

try:
    from deepeval import assert_test
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase
    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False

# Thresholds — these define the quality bar
RELEVANCY_THRESHOLD = 0.7
FAITHFULNESS_THRESHOLD = 0.8
ANSWER_RELEVANCY_THRESHOLD = 0.7


@pytest.mark.eval
@pytest.mark.skipif(not HAS_DEEPEVAL, reason="deepeval not installed")
class TestRetrievalQuality:
    """Evaluate retrieval context quality against golden dataset."""

    @pytest.fixture
    def relevancy_metric(self):
        return ContextualRelevancyMetric(threshold=RELEVANCY_THRESHOLD)

    @pytest.fixture
    def precision_metric(self):
        return ContextualPrecisionMetric(threshold=RELEVANCY_THRESHOLD)

    def test_context_relevancy(self, golden_qa_pairs, relevancy_metric):
        """All golden QA pairs should have relevant retrieval context."""
        for case in golden_qa_pairs:
            test_case = LLMTestCase(
                input=case["input"],
                actual_output=case["expected_output"],
                retrieval_context=case["context"],
            )
            assert_test(test_case, [relevancy_metric])


@pytest.mark.eval
@pytest.mark.skipif(not HAS_DEEPEVAL, reason="deepeval not installed")
class TestGenerationQuality:
    """Evaluate answer generation quality."""

    @pytest.fixture
    def faithfulness_metric(self):
        return FaithfulnessMetric(threshold=FAITHFULNESS_THRESHOLD)

    @pytest.fixture
    def answer_relevancy_metric(self):
        return AnswerRelevancyMetric(threshold=ANSWER_RELEVANCY_THRESHOLD)

    def test_answer_faithfulness(self, golden_qa_pairs, faithfulness_metric):
        """Answers must be faithful to the provided context."""
        for case in golden_qa_pairs:
            test_case = LLMTestCase(
                input=case["input"],
                actual_output=case["expected_output"],
                retrieval_context=case["context"],
            )
            assert_test(test_case, [faithfulness_metric])


@pytest.mark.eval
class TestTokenEfficiencyEval:
    """Evaluate TOON token efficiency on golden dataset contexts."""

    def test_toon_saves_tokens_on_golden_data(self, golden_qa_pairs):
        """TOON format should save tokens on all golden dataset contexts."""
        try:
            from seamless_rag.benchmark.compare import TokenBenchmark
            from seamless_rag.toon.encoder import encode_tabular
        except ImportError:
            pytest.skip("seamless_rag not yet implemented")

        benchmark = TokenBenchmark()

        for case in golden_qa_pairs:
            # Convert context list to tabular format
            context_data = [
                {"id": i + 1, "content": c, "relevance": 1.0 - i * 0.1}
                for i, c in enumerate(case["context"])
            ]
            result = benchmark.compare(context_data)
            assert result.toon_tokens < result.json_tokens, (
                f"TOON not saving tokens for: {case['input'][:50]}"
            )
