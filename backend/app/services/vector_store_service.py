"""
Vector store service for healthcare retrieval.

This service is deliberately backend-agnostic: the storage engine is selected from
configuration instead of hard-coded into application logic.
"""

from __future__ import annotations

import asyncio
import json
import threading
from abc import ABC, abstractmethod
from math import sqrt

import asyncpg

from app.core.config import settings
from app.services.embedding_service import EmbeddingService


class BaseVectorBackend(ABC):
    """Common contract for every vector store backend."""

    @abstractmethod
    def upsert_document(
        self,
        document_id: str,
        *,
        patient_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Store a single document and vector."""

    @abstractmethod
    def search(
        self,
        *,
        patient_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """Retrieve the most relevant document chunks for the patient."""


class MemoryVectorBackend(BaseVectorBackend):
    """Simple in-memory vector store for local development and tests."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self._documents: dict[str, dict] = {}

    def upsert_document(
        self,
        document_id: str,
        *,
        patient_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        vector = self.embedding_service.generate_embedding(content)
        payload = {
            "document_id": document_id,
            "patient_id": patient_id,
            "content": content,
            "metadata": metadata or {},
            "vector": vector,
        }
        self._documents[document_id] = payload
        return {
            "document_id": document_id,
            "patient_id": patient_id,
            "metadata": metadata or {},
        }

    def search(
        self,
        *,
        patient_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        query_vector = self.embedding_service.generate_embedding(query)
        ranked = []

        for document in self._documents.values():
            if str(document.get("patient_id")) != str(patient_id):
                continue

            similarity = self._cosine_similarity(query_vector, document["vector"])
            if similarity <= 0:
                continue

            ranked.append(
                {
                    "document_id": document["document_id"],
                    "patient_id": document["patient_id"],
                    "content": document["content"],
                    "metadata": document["metadata"],
                    "score": round(similarity, 4),
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:limit]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot / (left_norm * right_norm)


class QdrantVectorBackend(BaseVectorBackend):
    """Qdrant-backed backend selected by configuration."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.collection_name = getattr(settings, "VECTOR_COLLECTION_NAME", "healthcare_documents")
        self.client = None

        if settings.QDRANT_URL:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams

                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                )

                try:
                    self.client.get_collection(self.collection_name)
                except Exception:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=settings.EMBEDDING_DIMENSION,
                            distance=Distance.COSINE,
                        ),
                    )
            except Exception:
                self.client = None

    def upsert_document(
        self,
        document_id: str,
        *,
        patient_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        if self.client is None:
            return MemoryVectorBackend(self.embedding_service).upsert_document(
                document_id,
                patient_id=patient_id,
                content=content,
                metadata=metadata,
            )

        vector = self.embedding_service.generate_embedding(content)
        payload = {
            "document_id": document_id,
            "patient_id": patient_id,
            "content": content,
            "metadata": metadata or {},
        }

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": document_id,
                    "vector": vector,
                    "payload": payload,
                }],
            )
        except Exception:
            pass

        return {
            "document_id": document_id,
            "patient_id": patient_id,
            "metadata": metadata or {},
        }

    def search(
        self,
        *,
        patient_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        if self.client is None:
            return MemoryVectorBackend(self.embedding_service).search(
                patient_id=patient_id,
                query=query,
                limit=limit,
            )

        query_vector = self.embedding_service.generate_embedding(query)

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter={
                    "must": [{
                        "key": "patient_id",
                        "match": {"value": patient_id},
                    }]
                },
                limit=limit,
                with_payload=True,
            )

            return [
                {
                    "document_id": str(item.id),
                    "patient_id": str(item.payload.get("patient_id")),
                    "content": item.payload.get("content", ""),
                    "metadata": item.payload.get("metadata", {}),
                    "score": float(getattr(item, "score", 0.0)),
                }
                for item in results
            ]
        except Exception:
            return MemoryVectorBackend(self.embedding_service).search(
                patient_id=patient_id,
                query=query,
                limit=limit,
            )


def _run_async_sync(coro):
    """Run async coroutines from sync methods even when a loop is already active."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}
    error = {}

    def _runner():
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover - defensive fallback
            error["value"] = exc

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]
    return result["value"]


class PGVectorBackend(BaseVectorBackend):
    """Postgres + pgvector backend. This is the runtime choice for this local setup."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.table_name = "document_vectors"
        self.dimension = settings.EMBEDDING_DIMENSION
        self._ensure_schema()

    @property
    def dsn(self) -> str:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is required for pgvector backend")
        return settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

    def _ensure_schema(self) -> None:
        async def _setup() -> None:
            conn = await asyncpg.connect(self.dsn)
            try:
                await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                await conn.execute(
                    f'''
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding VECTOR({self.dimension}) NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    '''
                )
                await conn.execute(
                    f'CREATE INDEX IF NOT EXISTS {self.table_name}_patient_idx ON {self.table_name}(patient_id);'
                )
                await conn.execute(
                    f'CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx ON {self.table_name} USING hnsw (embedding vector_cosine_ops);'
                )
            finally:
                await conn.close()

        _run_async_sync(_setup())

    def upsert_document(
        self,
        document_id: str,
        *,
        patient_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        vector = self.embedding_service.generate_embedding(content)
        metadata_json = json.dumps(metadata or {})

        async def _write() -> dict:
            conn = await asyncpg.connect(self.dsn)
            try:
                await conn.execute(
                    f'''
                    INSERT INTO {self.table_name} (id, patient_id, content, metadata, embedding)
                    VALUES ($1, $2, $3, $4::jsonb, $5::vector)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        patient_id = EXCLUDED.patient_id,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    ''',
                    document_id,
                    str(patient_id),
                    content,
                    metadata_json,
                    str(vector),
                )
                return {
                    "document_id": document_id,
                    "patient_id": str(patient_id),
                    "metadata": metadata or {},
                }
            finally:
                await conn.close()

        return _run_async_sync(_write())

    def search(
        self,
        *,
        patient_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        query_vector = self.embedding_service.generate_embedding(query)

        async def _search() -> list[dict]:
            conn = await asyncpg.connect(self.dsn)
            try:
                rows = await conn.fetch(
                    f'''
                    SELECT id, patient_id, content, metadata,
                           1 - (embedding <=> $1::vector) AS score
                    FROM {self.table_name}
                    WHERE patient_id = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3;
                    ''',
                    str(query_vector),
                    str(patient_id),
                    int(limit),
                )
                return [
                    {
                        "document_id": row["id"],
                        "patient_id": row["patient_id"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "score": float(row["score"]),
                    }
                    for row in rows
                ]
            finally:
                await conn.close()

        return _run_async_sync(_search())


class VectorStoreService:
    """Factory-based vector store that selects the configured backend from env."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.backend_name = (settings.VECTOR_DB_BACKEND or "memory").lower()
        self.backend = None

    def _get_backend(self) -> BaseVectorBackend:
        if self.backend is None:
            self.backend = self._build_backend()
        return self.backend

    def _build_backend(self) -> BaseVectorBackend:
        if self.backend_name == "qdrant":
            return QdrantVectorBackend(self.embedding_service)
        if self.backend_name == "pgvector":
            return PGVectorBackend(self.embedding_service)
        return MemoryVectorBackend(self.embedding_service)

    def upsert_document(
        self,
        document_id: str,
        *,
        patient_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        return self._get_backend().upsert_document(
            document_id,
            patient_id=patient_id,
            content=content,
            metadata=metadata,
        )

    def search(
        self,
        *,
        patient_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        return self._get_backend().search(
            patient_id=patient_id,
            query=query,
            limit=limit,
        )
