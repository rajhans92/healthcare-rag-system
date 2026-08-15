import asyncio
from uuid import uuid4

from app.core.config import settings
from app.services.document_ingestion_service import DocumentIngestionService


def test_chunk_text_splits_document_into_overlapping_chunks():
    text = " ".join(f"clinical_note_{idx}" for idx in range(25))

    chunks = DocumentIngestionService.chunk_text(
        text,
        chunk_size=8,
        chunk_overlap=3,
    )

    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)
    assert chunks[0].startswith("clinical_note_0")
    assert chunks[1].split()[0] in chunks[0].split()[-3:]


def test_process_document_indexes_document_in_chunks(monkeypatch):
    monkeypatch.setattr(settings, "VECTOR_DB_BACKEND", "memory")

    service = DocumentIngestionService(session=None)
    patient_id = uuid4()
    document_id = uuid4()
    text = " ".join(f"patient_symptom_{idx}" for idx in range(90))

    result = asyncio.run(
        service.process_document(
            document_id=document_id,
            patient_id=patient_id,
            content=text,
            metadata={"source": "test"},
            chunk_size=8,
            chunk_overlap=3,
        )
    )

    assert result["status"] == "completed"
    assert result["chunks_indexed"] > 1
    assert len(result["indexed_chunks"]) == result["chunks_indexed"]

    hits = service.vector_store_service.search(
        patient_id=str(patient_id),
        query="patient_symptom_50",
        limit=5,
    )
    assert hits


def test_process_pending_documents_runs_queue(monkeypatch):
    service = DocumentIngestionService(session=None)
    document_id = uuid4()
    patient_id = uuid4()

    class DummyDocument:
        def __init__(self):
            self.id = document_id
            self.patient_id = patient_id
            self.file_key = "patients/abc/documents.txt"
            self.mime_type = "text/plain"
            self.title = "Lab report"
            self.file_name = "lab-report.txt"
            self.description = "Routine blood panel"
            self.document_type = type("DocType", (), {"value": "LAB_REPORT"})()
            self.source = type("Source", (), {"value": "PATIENT"})()

    async def fake_pending(limit):
        return [DummyDocument()]

    async def fake_parse(document):
        return "Hemoglobin normal. No critical issues found."

    async def fake_process(document_id, patient_id, content, metadata=None, **kwargs):
        return {
            "document_id": str(document_id),
            "patient_id": str(patient_id),
            "status": "completed",
            "chunks_indexed": 1,
            "message": "ok",
        }

    monkeypatch.setattr(service.document_repository, "get_pending_documents", fake_pending)
    monkeypatch.setattr(service, "parse_document_text", fake_parse)
    monkeypatch.setattr(service, "process_document", fake_process)

    result = asyncio.run(service.process_pending_documents(limit=5))

    assert result[0]["status"] == "completed"
    assert result[0]["document_id"] == str(document_id)
