from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.encounter import Encounter, EncounterStatus, EncounterType
from app.schemas.encounter import CreateEncounterRequest, EncounterSummaryResponse
from app.services.encounter_service import EncounterService


@pytest.mark.asyncio
async def test_list_patient_encounters_filters_by_doctor(monkeypatch):
    service = EncounterService(session=None)
    patient_id = uuid4()
    doctor_id = uuid4()

    async def fake_get_patient_encounters(patient_id_arg, page, page_size, doctor_id=None):
        assert patient_id_arg == patient_id
        assert page == 2
        assert page_size == 10
        assert doctor_id == expected_doctor_id
        encounter = SimpleNamespace(
            id=uuid4(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            encounter_number="ENC-20240601-01",
            encounter_type=EncounterType.OPD,
            encounter_date=datetime.now(timezone.utc),
            status=EncounterStatus.OPEN,
            chief_complaint="Test complaint",
        )
        return ([encounter], 1)

    expected_doctor_id = doctor_id

    monkeypatch.setattr(service.encounter_repository, "get_patient_encounters", fake_get_patient_encounters)

    response = await service.list_patient_encounters(
        patient_id=patient_id,
        page=2,
        page_size=10,
        doctor_id=doctor_id,
    )

    assert response["total"] == 1
    assert len(response["items"]) == 1


@pytest.mark.asyncio
async def test_create_encounter_uses_authenticated_doctor(monkeypatch):
    service = EncounterService(session=None)
    patient_id = uuid4()
    doctor_user_id = uuid4()
    doctor_id = uuid4()
    current_user = SimpleNamespace(id=doctor_user_id)
    request = CreateEncounterRequest(
        patient_id=patient_id,
        doctor_id=None,
        encounter_type=EncounterType.OPD,
        chief_complaint="Fever",
        encounter_date=datetime.now(timezone.utc),
    )

    created_encounter = None

    async def fake_get_by_id(entity_id):
        if entity_id == patient_id:
            return SimpleNamespace(id=patient_id)
        return None

    async def fake_get_by_user_id(user_id):
        assert user_id == doctor_user_id
        return SimpleNamespace(id=doctor_id)

    async def fake_create_encounter(encounter):
        nonlocal created_encounter
        encounter.id = uuid4()
        encounter.created_at = datetime.now(timezone.utc)
        encounter.updated_at = encounter.created_at
        created_encounter = encounter
        return encounter

    class DummySession:
        async def commit(self):
            return None

        async def refresh(self, entity):
            return None

        async def rollback(self):
            return None

    service.session = DummySession()
    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.doctor_repository, "get_by_user_id", fake_get_by_user_id)
    monkeypatch.setattr(service.encounter_repository, "create_encounter", fake_create_encounter)
    monkeypatch.setattr(service.encounter_repository, "get_by_encounter_number", AsyncMock(return_value=None))

    response = await service.create_encounter(current_user, request)

    assert response.patient_id == patient_id
    assert response.doctor_id == doctor_id
    assert created_encounter.patient_id == patient_id
    assert created_encounter.doctor_id == doctor_id
    assert created_encounter.visit_date == request.encounter_date


def test_encounter_summary_maps_visit_date_to_encounter_date():
    encounter = Encounter(
        encounter_number="ENC-20240601-ABC12345",
        patient_id=uuid4(),
        doctor_id=uuid4(),
        encounter_type=EncounterType.OPD,
        visit_date=datetime(2024, 6, 1, 9, 30, tzinfo=timezone.utc),
        chief_complaint="Back pain",
        status=EncounterStatus.OPEN,
    )
    encounter.id = uuid4()
    encounter.created_at = datetime(2024, 6, 1, 9, 45, tzinfo=timezone.utc)
    encounter.updated_at = encounter.created_at

    response = EncounterSummaryResponse.model_validate(encounter)

    assert response.encounter_date == encounter.visit_date
    assert response.doctor_id == encounter.doctor_id
    assert response.patient_id == encounter.patient_id
