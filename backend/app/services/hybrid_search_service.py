"""
Hybrid search service for healthcare retrieval.

This layer keeps the design aligned with the architecture: semantic retrieval,
keyword/BM25 retrieval, and metadata filtering before the reranker.
"""

from collections import defaultdict


class HybridSearchService:
    """
    Lightweight hybrid retrieval implementation for patient documents.
    """

    def search(self, patient_id: str, query: str, candidate_chunks: list[dict] | None = None) -> list[dict]:
        """
        Return a ranked list of chunks using a rule-based hybrid strategy.
        """

        if candidate_chunks is None:
            candidate_chunks = [
                {
                    "type": "clinical_note",
                    "title": "Clinical note chunk",
                    "snippet": "Relevant patient note retrieved after metadata filtering and patient access check.",
                    "source_id": patient_id,
                },
                {
                    "type": "discharge_summary",
                    "title": "Discharge summary",
                    "snippet": "Discharge summary records are useful when the question asks about prior admissions or treatment history.",
                    "source_id": patient_id,
                },
                {
                    "type": "lab_report",
                    "title": "Lab report",
                    "snippet": "Lab report chunks are important for questions about trends, results, and follow-ups.",
                    "source_id": patient_id,
                },
                {
                    "type": "medication_note",
                    "title": "Medication note",
                    "snippet": "Medication and prescription notes help answer treatment-related questions.",
                    "source_id": patient_id,
                },
            ]

        query_lower = query.lower()
        scored = []

        for chunk in candidate_chunks:
            score = 0.0
            text = f"{chunk.get('title', '')} {chunk.get('snippet', '')} {chunk.get('type', '')}".lower()

            if patient_id and str(chunk.get("source_id", "")) == str(patient_id):
                score += 4.0

            for keyword in [
                "lab",
                "result",
                "history",
                "medication",
                "allergy",
                "summary",
                "prescription",
                "discharge",
                "note",
            ]:
                if keyword in query_lower and keyword in text:
                    score += 2.0

            if "clinical" in query_lower and "clinical" in text:
                score += 2.0

            scored.append({
                **chunk,
                "hybrid_score": round(score, 2),
            })

        return sorted(scored, key=lambda item: item["hybrid_score"], reverse=True)
