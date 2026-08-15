from datetime import date, datetime, timezone
from uuid import uuid4

from types import SimpleNamespace

import pytest

from app.db.initializer import initialize_database  # noqa: F401
from app.exceptions.exceptions import AuthorizationException
from app.models.user import UserRole
from app.services.patient_access_service import PatientAccessService
from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
async def test_is_doctor_authorized_for_patient_returns_true_for_active_access(monkeypatch):
    service = PatientAccessService(session=None)
    patient_id = uuid4()
    doctor_id = uuid4()

    async def fake_get_active_access(patient_id_arg, doctor_id_arg):
        assert patient_id_arg == patient_id
        assert doctor_id_arg == doctor_id
        return object()

    monkeypatch.setattr(service.repository, "get_active_access", fake_get_active_access)

    assert await service.is_doctor_authorized_for_patient(doctor_id, patient_id) is True


@pytest.mark.asyncio
async def test_request_access_creates_pending_record(monkeypatch):
    service = PatientAccessService(session=None)
    patient_id = uuid4()
    doctor_id = uuid4()

    class DummyPatient:
        user_id = uuid4()

    class DummyDoctor:
        user_id = uuid4()

    class DummyAccess:
        def __init__(self):
            self.patient_id = patient_id
            self.doctor_id = doctor_id
            self.otp = "123456"
            self.status = "PENDING"
            self.expires_at = datetime.now(timezone.utc)
            self.approved_at = None
            self.remarks = None
            self.created_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    async def fake_get_by_id(entity_id):
        if entity_id == patient_id:
            return DummyPatient()
        if entity_id == doctor_id:
            return DummyDoctor()
        return None

    async def fake_get_by_patient_and_doctor(patient_id_arg, doctor_id_arg):
        return []

    async def fake_create_access(access):
        access.expires_at = datetime.now(timezone.utc)
        return access

    class DummySession:
        async def commit(self):
            return None

        async def refresh(self, entity):
            return None

    service.session = DummySession()
    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.doctor_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.repository, "get_by_patient_and_doctor", fake_get_by_patient_and_doctor)
    monkeypatch.setattr(service.repository, "create_access", fake_create_access)

    access = await service.request_access(
        patient_id,
        doctor_id,
        requester_id=uuid4(),
        requester_role="ADMIN",
        expires_days=30,
    )

    assert access.patient_id == patient_id
    assert access.doctor_id == doctor_id
    assert access.status.value == "PENDING"


@pytest.mark.asyncio
async def test_validate_patient_access_allows_patient_owner(monkeypatch):
    service = RetrievalService(session=None)
    patient_id = uuid4()
    user_id = uuid4()

    patient = SimpleNamespace(id=patient_id, user_id=user_id)
    current_user = SimpleNamespace(id=user_id, role=UserRole.PATIENT)

    async def fake_get_by_id(_):
        return patient

    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)

    await service.validate_patient_access(current_user, patient_id)


@pytest.mark.asyncio
async def test_validate_patient_access_requires_approved_doctor_access(monkeypatch):
    service = RetrievalService(session=None)
    patient_id = uuid4()
    patient_user_id = uuid4()
    doctor_user_id = uuid4()
    doctor_id = uuid4()

    patient = SimpleNamespace(id=patient_id, user_id=patient_user_id)
    doctor = SimpleNamespace(id=doctor_id, user_id=doctor_user_id)
    current_user = SimpleNamespace(id=doctor_user_id, role=UserRole.DOCTOR)

    async def fake_get_by_id(_):
        return patient

    async def fake_get_by_user_id(_):
        return doctor

    async def fake_get_active_access(*_):
        return None

    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.doctor_repository, "get_by_user_id", fake_get_by_user_id)
    monkeypatch.setattr(service.patient_access_repository, "get_active_access", fake_get_active_access)

    with pytest.raises(AuthorizationException, match="approved access"):
        await service.validate_patient_access(current_user, patient_id)


@pytest.mark.asyncio
async def test_validate_patient_access_allows_doctor_with_active_access(monkeypatch):
    service = RetrievalService(session=None)
    patient_id = uuid4()
    patient_user_id = uuid4()
    doctor_user_id = uuid4()
    doctor_id = uuid4()

    patient = SimpleNamespace(id=patient_id, user_id=patient_user_id)
    doctor = SimpleNamespace(id=doctor_id, user_id=doctor_user_id)
    current_user = SimpleNamespace(id=doctor_user_id, role=UserRole.DOCTOR)

    async def fake_get_by_id(_):
        return patient

    async def fake_get_by_user_id(_):
        return doctor

    async def fake_get_active_access(*_):
        return object()

    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(service.doctor_repository, "get_by_user_id", fake_get_by_user_id)
    monkeypatch.setattr(service.patient_access_repository, "get_active_access", fake_get_active_access)

    await service.validate_patient_access(current_user, patient_id)


@pytest.mark.asyncio
async def test_fetch_structured_patient_facts_includes_profile_and_recent_history(monkeypatch):
    service = RetrievalService(session=None)
    patient_id = uuid4()
    patient = SimpleNamespace(
        id=patient_id,
        gender=SimpleNamespace(value="MALE"),
        date_of_birth=date(1990, 1, 1),
        blood_group="O+",
        city="Mumbai",
    )

    encounter_id = uuid4()
    encounter = SimpleNamespace(
        id=encounter_id,
        encounter_type=SimpleNamespace(value="OPD"),
        chief_complaint="Cough",
        visit_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    diagnosis = SimpleNamespace(encounter_id=encounter_id, diagnosis_name="RTI")
    prescription = SimpleNamespace(id=uuid4(), encounter_id=encounter_id, instructions="Amoxicillin for 5 days")
    prescription_item = SimpleNamespace(
        prescription_id=prescription.id,
        medicine_name="Amoxicillin",
        dosage="500mg",
        frequency="BD",
    )
    report = SimpleNamespace(
        report_name="CBC",
        upload_status=SimpleNamespace(value="UPLOADED"),
    )

    async def fake_get_by_id(_):
        return patient

    class DummyResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return SimpleNamespace(all=lambda: self._rows)

    call_count = {"value": 0}

    async def fake_execute(_):
        call_count["value"] += 1
        if call_count["value"] == 1:
            return DummyResult([encounter])
        if call_count["value"] == 2:
            return DummyResult([diagnosis])
        if call_count["value"] == 3:
            return DummyResult([prescription])
        if call_count["value"] == 4:
            return DummyResult([prescription_item])
        if call_count["value"] == 5:
            return DummyResult([report])
        return DummyResult([])

    monkeypatch.setattr(service.patient_repository, "get_by_id", fake_get_by_id)
    service.session = SimpleNamespace(execute=fake_execute)

    facts = await service._fetch_structured_patient_facts(patient_id)

    assert any(fact["type"] == "patient_profile" for fact in facts)
    assert any(fact["type"] == "recent_encounters" for fact in facts)
    assert any(fact["type"] == "medication_history" for fact in facts)
    assert any(fact["type"] == "lab_summary" for fact in facts)
