"""
LLM adapter for the healthcare RAG pipeline.

This adapter supports a real OpenAI-compatible provider when configured, while
falling back to a deterministic grounded response for local development.
"""

from app.core.config import settings


class LLMService:
    """
    Returns a grounded answer using the assembled context bundle.
    """

    def generate_answer(self, question: str, context: list[dict]) -> str:
        """
        Use a provider-based LLM if configured, otherwise return a safe fallback
        response that still respects the grounded-context pattern.
        """

        if settings.OPENAI_API_KEY and settings.LLM_MODEL:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = self._build_prompt(question=question, context=context)

                response = client.responses.create(
                    model=settings.LLM_MODEL,
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "You are an AI assistant for authorized clinical knowledge retrieval. "
                                "Answer only using the provided patient and medical context. "
                                "Never invent patient facts. If evidence is missing, state that explicitly. "
                                "Cite the evidence used in your answer."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    max_output_tokens=settings.MAX_OUTPUT_TOKENS,
                )

                if hasattr(response, "output_text") and response.output_text:
                    return response.output_text.strip()

                if hasattr(response, "output") and response.output:
                    text_parts = []
                    for item in response.output:
                        if hasattr(item, "content"):
                            for content in item.content:
                                if hasattr(content, "text"):
                                    text_parts.append(content.text)
                    if text_parts:
                        return "\n".join(text_parts).strip()
            except Exception:
                pass

        return self._fallback_answer(question, context)

    def _build_prompt(self, question: str, context: list[dict]) -> str:
        """
        Assemble a compact evidence prompt for an LLM.
        """

        evidence_blocks = []
        for item in context[: settings.MAX_RETRIEVED_CHUNKS]:
            title = item.get("title", "Evidence")
            snippet = item.get("snippet", "")
            evidence_blocks.append(f"- {title}: {snippet}")

        context_text = "\n".join(evidence_blocks) if evidence_blocks else "No evidence available."

        return (
            f"Question: {question}\n\n"
            f"Authorized evidence:\n{context_text}\n\n"
            "Provide a concise answer based only on the evidence above. "
            "Describe missing information honestly. Cite the evidence used."
        )

    def _fallback_answer(self, question: str, context: list[dict]) -> str:
        """
        Safe local fallback answer when no provider is configured.
        """

        evidence_summary = "; ".join(
            item.get("title", "retrieved evidence") for item in context[:3]
        )

        return (
            f"Based on the authorized context for this query, the answer should be grounded in the evidence set: "
            f"{evidence_summary}. If the available context does not contain a definitive answer, the system must state that "
            f"the evidence is insufficient and avoid making unsupported medical claims."
        )
