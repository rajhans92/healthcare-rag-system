"""
Context builder for ground-truth LLM prompts.

This service assembles a compact evidence bundle from structured facts plus the
most relevant retrieved document chunks.
"""

from app.core.config import settings


class ContextBuilderService:
    """
    Assemble a compact context bundle with a strict token budget.
    """

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Return a lightweight approximation of token usage for a string."""
        return max(20, len(text.split()) * 2)

    def build_context(
        self,
        structured_facts: list[dict],
        document_chunks: list[dict],
        max_tokens: int | None = None,
    ) -> list[dict]:
        """
        Combine structured facts and retrieved chunks into a compact evidence list.
        """

        max_tokens = max_tokens if max_tokens is not None else settings.MAX_CONTEXT_TOKENS
        combined = structured_facts + document_chunks
        context = []
        current_tokens = 0

        for item in combined:
            snippet = item.get("snippet", "")
            estimated_tokens = self.estimate_tokens(snippet)

            if current_tokens + estimated_tokens > max_tokens:
                break

            context.append(item)
            current_tokens += estimated_tokens

        return context
