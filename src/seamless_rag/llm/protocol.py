"""LLM provider protocol — the interface all LLM providers must satisfy."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers. Implement this to add custom providers.

    Example:
        class MyLLM:
            def generate(self, prompt: str, context: str) -> str:
                return my_model.generate(f"Context: {context}\\n\\nQuestion: {prompt}")
    """

    def generate(self, prompt: str, context: str) -> str:
        """Generate an answer given a prompt and TOON-formatted context.

        Args:
            prompt: The user's question.
            context: TOON-formatted context from vector search results.

        Returns:
            Generated answer string.
        """
        ...
