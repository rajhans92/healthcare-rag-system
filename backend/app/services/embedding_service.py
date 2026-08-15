"""
Embedding service for healthcare document retrieval.

This implementation is intentionally dependency-light so it works immediately in a
local backend without adding external ML libraries. It generates deterministic
vectors from text content and can later be replaced by a provider-specific
embedding model (OpenAI, Gemini, Qdrant, etc.).
"""

import hashlib
import math
import re


class EmbeddingService:
    """
    Simple deterministic embedding generator for local retrieval prototypes.
    """

    DIMENSION = 32

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate a compact embedding vector from the provided text.
        """

        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        if not normalized:
            return [0.0] * self.DIMENSION

        tokens = re.findall(r"[a-z0-9]+", normalized)
        if not tokens:
            return [0.0] * self.DIMENSION

        vector = [0.0] * self.DIMENSION

        for index, token in enumerate(tokens):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            bucket_index = int(digest[:8], 16) % self.DIMENSION
            value = 1.0 / math.sqrt(index + 1)
            vector[bucket_index] += value

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return [0.0] * self.DIMENSION

        return [value / norm for value in vector]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for several texts.
        """

        return [self.generate_embedding(text) for text in texts]
