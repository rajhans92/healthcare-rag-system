from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.diagnosis import Severity
from app.models.encounter import EncounterStatus
from app.schemas.diagnosis import CreateDiagnosisRequest
from app.services.diagnosis_service import DiagnosisService


@pytest.mark.asyncio
async def test_create_diagnosis_persists_diagnosis_code(monkeypatch):
    service = DiagnosisService(session=None)
    encounter_id = uuid4()
    doctor = SimpleNamespace(id=uuid4())
    encounter = SimpleNamespace(
        id=encounter_id,
        doctor_id=doctor.id,
        status=EncounterStatus.OPEN,
    )

    created = None

    async def fake_get_by_id(encounter_id_arg):
        assert encounter_id_arg == encounter_id
        return encounter

    async def fake_create_diagnosis(diagnosis):
        nonlocal created
        diagnosis.id = uuid4()
        diagnosis.created_at = datetime.now(timezone.utc)
        diagnosis.updated_at = diagnosis.created_at
        created = diagnosis
        return diagnosis

    service.session = SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
        refresh=AsyncMock(),
    )

    monkeypatch.setattr(service.encounter_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.diagnosis_repository, "create_diagnosis", fake_create_diagnosis)

    request = CreateDiagnosisRequest(
        diagnosis_code="J20.9",
        diagnosis_name="Acute bronchitis",
        description="Cough and mild fever",
        severity=Severity.MEDIUM,
        is_primary=False,
    )

    response = await service.create_diagnosis(
        encounter_id=encounter_id,
        doctor=doctor,
        request=request,
    )

    assert response.diagnosis_code == "J20.9"
    assert response.description == "Cough and mild fever"
    assert response.severity == Severity.MEDIUM
    assert created.diagnosis_code == "J20.9"
