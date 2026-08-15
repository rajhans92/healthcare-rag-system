"""
Document ingestion service for the healthcare RAG pipeline.

This service defines the production stages for a medical document before it is
available for retrieval: upload, duplicate detection, OCR, parsing, chunking,
embedding generation, and vector indexing.
"""

import hashlib
import io
import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.medical_document import DocumentProcessingStatus
from app.repositories.medical_document_repository import MedicalDocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.s3_service import S3Service
from app.services.vector_store_service import VectorStoreService


class DocumentIngestionService:
    """
    Step-by-step ingestion pipeline for patient medical documents.
    """

    DEFAULT_CHUNK_SIZE = 600
    DEFAULT_CHUNK_OVERLAP = 80

    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()
        self.s3_service = S3Service()
        self.document_repository = MedicalDocumentRepository(session)
        self._seen_hashes: set[str] = set()

    @staticmethod
    def chunk_text(
        text: str,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list[str]:
        """
        Split a document into overlapping chunks for retrieval.
        """
        normalized = re.sub(r"\s+", " ", text or "").strip()
        if not normalized:
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        chunk_overlap = min(chunk_overlap, chunk_size - 1)
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or greater.")

        words = normalized.split()
        chunks: list[str] = []
        start = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            if not chunk_words:
                break
            chunks.append(" ".join(chunk_words))

            if end == len(words):
                break

            start = max(start + chunk_size - chunk_overlap, start + 1)

        return chunks

    def _build_document_summary(self, document) -> str:
        """
        Build a plain-language summary for document parsing fallback.
        """
        title = getattr(document, "title", None) or getattr(document, "file_name", "Document")
        document_type = getattr(getattr(document, "document_type", None), "value", None)
        if document_type is None:
            document_type = str(getattr(document, "document_type", "OTHER"))
        description = getattr(document, "description", None) or "No description provided."
        return (
            f"Document title: {title}. "
            f"Document type: {document_type}. "
            f"Description: {description}. "
            f"This document was uploaded for clinical review and retrieval."
        )

    def _extract_pdf_text(self, raw_pdf: bytes) -> str:
        """
        Parse text from PDF content when a PDF library is available.
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw_pdf))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(page for page in pages if page)
            if text.strip():
                return text
        except Exception:
            pass

        return ""

    def _extract_image_text(self, raw_image: bytes, *, mime_type: str) -> str:
        """
        Perform OCR for image uploads when the OCR dependencies and binary are available.
        """
        if not settings.OCR_ENABLED:
            return ""

        try:
            import PIL.Image
            import pytesseract
        except Exception:
            return ""

        try:
            if settings.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

            image = PIL.Image.open(io.BytesIO(raw_image))
            text = pytesseract.image_to_string(
                image,
                lang=settings.OCR_LANGUAGE,
            )
            if text.strip():
                return text
        except Exception:
            return ""

        return ""

    async def parse_document_text(self, document) -> str:
        """
        Extract text from a stored document using the configured storage backend.
        """
        try:
            raw = self.s3_service.download_object(document.file_key)
        except Exception:
            return self._build_document_summary(document)

        if document.mime_type == "text/plain":
            return raw.decode("utf-8", errors="replace") or self._build_document_summary(document)

        if document.mime_type == "application/pdf":
            text = self._extract_pdf_text(raw)
            if text.strip():
                return text
            return "PDF document uploaded for clinical review. " + self._build_document_summary(document)

        if document.mime_type.startswith("image/"):
            text = self._extract_image_text(raw, mime_type=document.mime_type)
            if text.strip():
                return text
            return (
                f"Image document '{getattr(document, 'file_name', 'uploaded file')}' uploaded for clinical review. "
                f"OCR is not available in the local fallback pipeline. "
                f"{self._build_document_summary(document)}"
            )

        return self._build_document_summary(document)

    async def queue_document_for_processing(
        self,
        patient_id: UUID,
        document_name: str,
        mime_type: str,
        file_size: int,
    ) -> dict:
        """
        Enqueue a new document for processing.

        In production, this should trigger a background task that will:
        - compute SHA-256 hash
        - check for duplicate document upload
        - perform OCR or parsing if required
        - extract metadata
        - chunk and vectorize the content
        - index to the vector store
        """

        return {
            "status": "queued",
            "patient_id": str(patient_id),
            "document_name": document_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "processing_steps": [
                "duplicate_check",
                "ocr_or_parse",
                "metadata_extraction",
                "chunking",
                "embedding",
                "vector_indexing",
            ],
        }

    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """
        Compute a stable SHA-256 hash for a document payload.
        """
        return hashlib.sha256(content).hexdigest()

    async def detect_duplicate_upload(
        self,
        file_hash: str,
    ) -> bool:
        """
        Check if an uploaded file hash has already been seen in the current worker.

        This is a local-development deduplication guard until the system persists
        a canonical file hash field in the database.
        """
        if file_hash in self._seen_hashes:
            return True
        return False

    def mark_file_hash_seen(self, file_hash: str) -> None:
        """
        Record a file hash as processed by the current worker runtime.
        """
        self._seen_hashes.add(file_hash)

    async def process_pending_documents(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """
        Process all pending documents in the queue and index them for retrieval.
        """
        documents = await self.document_repository.get_pending_documents(limit=limit)
        results: list[dict] = []

        for document in documents:
            try:
                await self.document_repository.update_processing_status(
                    document,
                    DocumentProcessingStatus.PROCESSING,
                )
                text = await self.parse_document_text(document)
                result = await self.process_document(
                    document_id=document.id,
                    patient_id=document.patient_id,
                    content=text,
                    metadata={
                        "file_name": document.file_name,
                        "mime_type": document.mime_type,
                        "document_type": getattr(document.document_type, "value", str(document.document_type)),
                        "source": getattr(document.source, "value", str(document.source)),
                    },
                )
                await self.document_repository.update_processing_status(
                    document,
                    DocumentProcessingStatus.COMPLETED,
                )
                result["status"] = "completed"
                results.append(result)
            except Exception as exc:  # pragma: no cover - defensive worker behavior
                await self.document_repository.update_processing_status(
                    document,
                    DocumentProcessingStatus.FAILED,
                    error=str(exc),
                )
                results.append(
                    {
                        "document_id": str(document.id),
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        return results

    async def process_document(
        self,
        document_id: UUID,
        patient_id: UUID,
        content: str,
        metadata: dict | None = None,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> dict:
        """
        Perform the actual document processing pipeline.
        """
        chunks = self.chunk_text(
            content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        if not chunks:
            return {
                "document_id": str(document_id),
                "patient_id": str(patient_id),
                "status": "completed",
                "chunks_indexed": 0,
                "embedding_dimension": self.embedding_service.DIMENSION,
                "message": "No content was available for indexing.",
            }

        indexed_chunks = []
        for index, chunk in enumerate(chunks):
            embedding = self.embedding_service.generate_embedding(chunk)
            vector_id = f"{document_id}:chunk-{index}"
            self.vector_store_service.upsert_document(
                vector_id,
                patient_id=str(patient_id),
                content=chunk,
                metadata={
                    **(metadata or {}),
                    "document_id": str(document_id),
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "embedding_dimension": len(embedding),
                },
            )
            indexed_chunks.append({
                "chunk_index": index,
                "document_id": str(document_id),
                "vector_id": vector_id,
                "length": len(chunk),
            })

        return {
            "document_id": str(document_id),
            "patient_id": str(patient_id),
            "status": "completed",
            "chunks_indexed": len(indexed_chunks),
            "embedding_dimension": self.embedding_service.DIMENSION,
            "message": "Document content was chunked, embedded, and indexed into the vector store.",
            "indexed_chunks": indexed_chunks,
        }
