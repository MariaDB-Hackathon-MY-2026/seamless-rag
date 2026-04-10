"""RAG query engine with embedded token benchmark observation layer.

The benchmark is NOT a separate module called after the fact — it is woven
into the query pipeline so every `ask()` call automatically produces
token comparison data (per Judge Directive 2).
"""

from dataclasses import dataclass


@dataclass
class RAGResult:
    """Result of a RAG query, including token efficiency metrics."""

    answer: str
    context_toon: str
    context_json: str
    json_tokens: int
    toon_tokens: int
    savings_pct: float
    sources: list[dict]


class RAGEngine:
    """End-to-end RAG pipeline: question → embed → search → TOON → LLM → answer.

    Token benchmark is an observation layer: every query automatically computes
    JSON vs TOON token counts without extra API calls.
    """

    def __init__(self, provider: object, store: object) -> None:
        raise NotImplementedError("RAG engine not yet implemented")

    def ask(self, question: str, top_k: int = 5, context_window: int = 1) -> RAGResult:
        """Execute RAG query with automatic token benchmarking.

        Pipeline:
        1. Embed question via provider
        2. Vector search via store (top_k results + context window)
        3. Format results as JSON and TOON
        4. Count tokens for both (observation layer)
        5. Generate answer via LLM with TOON context
        6. Return RAGResult with all metrics
        """
        raise NotImplementedError
