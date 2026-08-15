from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.user import UserRole
from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_chat_allows_doctor_with_approved_patient_access(monkeypatch):
    service = ChatService(session=None)
    patient_id = uuid4()
    doctor_id = uuid4()
    current_user = SimpleNamespace(id=doctor_id, role=UserRole.DOCTOR)
    request = ChatMessageRequest(
        patient_id=patient_id,
        question="What is the patient history?",
        doctor_context="Summarize the patient's history for follow-up care.",
        include_medical_knowledge=False,
        include_patient_summary=True,
    )

    async def fake_log_event(**kwargs):
        return None

    async def fake_retrieve_patient_context(**kwargs):
        assert kwargs["current_user"] is current_user
        assert kwargs["patient_id"] == patient_id
        assert kwargs["question"] == request.question
        return {
            "structured_facts": [
                {
                    "type": "patient_profile",
                    "title": "Patient profile",
                    "snippet": "Age 32",
                    "source_id": str(patient_id),
                }
            ],
            "document_chunks": [
                {
                    "type": "clinical_note",
                    "title": "Clinical note",
                    "snippet": "Previous visit for cough",
                    "source_id": str(patient_id),
                }
            ],
        }

    captured = {}

    def fake_generate_answer(**kwargs):
        captured.update(kwargs)
        return "Patient has prior cough history."

    monkeypatch.setattr(service.audit_service, "log_event", fake_log_event)
    monkeypatch.setattr(service.retrieval_service, "retrieve_patient_context", fake_retrieve_patient_context)
    monkeypatch.setattr(service.llm_service, "generate_answer", fake_generate_answer)

    response = await service.ask_question(current_user=current_user, request=request)

    assert response.patient_id == patient_id
    assert "Patient has prior cough history." in response.answer
    assert response.retrieved_context_count == 2
    assert any(citation.source_type == "patient_profile" for citation in response.citations)
    assert captured["user_role"] == "DOCTOR"
    assert captured["doctor_context"] == "Summarize the patient's history for follow-up care."
