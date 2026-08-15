"""
Reranking service for retrieved clinical chunks.

The production version should use a cross-encoder or stronger reranker, but the
initial implementation is intentionally lightweight and deterministic.
"""


class RerankerService:
    """
    Sort retrieved candidates by relevance and keep the most useful evidence.
    """

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        Return the highest-scoring candidates for the final LLM context.
        """

        query_lower = query.lower()
        scored = []

        for item in candidates:
            raw_text = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('type', '')}".lower()
            score = float(item.get('hybrid_score', 0.0))

            for keyword in [
                "lab",
                "report",
                "history",
                "medication",
                "allergy",
                "summary",
                "diagnosis",
                "discharge",
                "note",
            ]:
                if keyword in query_lower and keyword in raw_text:
                    score += 2.0

            scored.append({
                **item,
                "rerank_score": round(score, 2),
            })

        ranked = sorted(scored, key=lambda item: item["rerank_score"], reverse=True)
        return ranked[:top_k]
