"""
Retrieval service for the healthcare RAG pipeline.

This is the first production-oriented retrieval layer. It keeps the flow aligned
with the architecture described for the project: patient access validation,
structured retrieval first, then unstructured retrieval, then a compact context
bundle passed to the LLM.
"""

from datetime import date
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.exceptions import AuthorizationException
from app.models.diagnosis import Diagnosis
from app.models.encounter import Encounter
from app.models.medical_report import MedicalReport
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.user import User, UserRole
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_access_repository import PatientAccessRepository
from app.repositories.patient_repository import PatientRepository
from app.services.context_builder_service import ContextBuilderService
from app.services.hybrid_search_service import HybridSearchService
from app.services.reranker_service import RerankerService
from app.services.vector_store_service import VectorStoreService


class RetrievalService:
    """
    Retrieve patient facts and document chunks for grounded clinical answers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repository = PatientRepository(session)
        self.doctor_repository = DoctorRepository(session)
        self.patient_access_repository = PatientAccessRepository(session)
        self.hybrid_search_service = HybridSearchService()
        self.reranker_service = RerankerService()
        self.context_builder_service = ContextBuilderService()
        self.vector_store_service = VectorStoreService()

    async def validate_patient_access(
        self,
        current_user: User,
        patient_id: UUID,
    ) -> None:
        """
        Enforce patient-level access restrictions before any retrieval.
        """

        patient = await self.patient_repository.get_by_id(patient_id)
        if patient is None:
            raise AuthorizationException(
                message="Patient record not found.",
            )

        if current_user.role == UserRole.PATIENT:
            if patient.user_id != current_user.id:
                raise AuthorizationException(
                    message="You are not authorized to access this patient record.",
                )
            return

        if current_user.role == UserRole.DOCTOR:
            doctor = await self.doctor_repository.get_by_user_id(current_user.id)
            if doctor is None:
                raise AuthorizationException(
                    message="Doctor profile not found for the current user.",
                )

            access = await self.patient_access_repository.get_active_access(
                patient_id,
                doctor.id,
            )
            if access is None:
                raise AuthorizationException(
                    message="You do not have approved access to this patient record.",
                )
            return

        if current_user.role == UserRole.ADMIN:
            return

        raise AuthorizationException(
            message="You are not authorized to access this patient record.",
        )

    async def _fetch_structured_patient_facts(self, patient_id: UUID) -> list[dict]:
        """Collect patient profile, recent encounters, diagnoses, and report metadata."""
        patient = await self.patient_repository.get_by_id(patient_id)
        if patient is None:
            return []

        facts: list[dict] = []
        profile_parts: list[str] = []

        gender = getattr(patient, "gender", None)
        if gender is not None:
            value = gender.value if isinstance(gender, Enum) else gender
            profile_parts.append(f"gender={value}")

        dob = getattr(patient, "date_of_birth", None)
        if dob is not None:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            profile_parts.append(f"age={age}")

        blood_group = getattr(patient, "blood_group", None)
        if blood_group:
            profile_parts.append(f"blood_group={blood_group}")

        city = getattr(patient, "city", None)
        if city:
            profile_parts.append(f"city={city}")

        if profile_parts:
            facts.append(
                {
                    "type": "patient_profile",
                    "title": "Patient profile",
                    "snippet": "; ".join(profile_parts),
                    "source_id": str(patient_id),
                }
            )

        if self.session is None:
            return facts

        encounters_result = await self.session.execute(
            select(Encounter)
            .where(Encounter.patient_id == patient_id)
            .order_by(Encounter.visit_date.desc(), Encounter.created_at.desc())
            .limit(3)
        )
        encounters = list(encounters_result.scalars().all())
        if encounters:
            encounter_ids = [encounter.id for encounter in encounters]
            diagnoses_result = await self.session.execute(
                select(Diagnosis)
                .where(Diagnosis.encounter_id.in_(encounter_ids))
                .order_by(Diagnosis.created_at.desc())
            )
            diagnoses_by_encounter: dict[UUID, list[str]] = {}
            for diagnosis in diagnoses_result.scalars().all():
                diagnoses_by_encounter.setdefault(diagnosis.encounter_id, []).append(diagnosis.diagnosis_name)

            prescriptions_result = await self.session.execute(
                select(Prescription)
                .where(Prescription.encounter_id.in_(encounter_ids))
                .order_by(Prescription.created_at.desc())
            )
            prescriptions = list(prescriptions_result.scalars().all())
            prescriptions_by_encounter: dict[UUID, list[str]] = {}
            for prescription in prescriptions:
                if prescription.instructions:
                    prescriptions_by_encounter.setdefault(prescription.encounter_id, []).append(prescription.instructions)

            prescription_ids = [prescription.id for prescription in prescriptions]
            medication_lines: list[str] = []
            if prescription_ids:
                prescription_items_result = await self.session.execute(
                    select(PrescriptionItem)
                    .where(PrescriptionItem.prescription_id.in_(prescription_ids))
                    .order_by(PrescriptionItem.created_at.desc())
                )
                for item in prescription_items_result.scalars().all():
                    dosage = getattr(item, "dosage", "")
                    frequency = getattr(item, "frequency", "")
                    medicine = getattr(item, "medicine_name", "")
                    if medicine:
                        medication_lines.append(f"{medicine} {dosage} {frequency}".strip())

            if medication_lines:
                facts.append(
                    {
                        "type": "medication_history",
                        "title": "Medication history",
                        "snippet": "; ".join(medication_lines[:6]),
                        "source_id": str(patient_id),
                    }
                )

            recent_encounter_parts: list[str] = []
            for encounter in encounters:
                details: list[str] = []
                encounter_type = getattr(encounter, "encounter_type", None)
                if encounter_type is not None:
                    details.append(f"type={encounter_type.value if isinstance(encounter_type, Enum) else encounter_type}")
                chief_complaint = getattr(encounter, "chief_complaint", None)
                if chief_complaint:
                    details.append(f"chief_complaint={chief_complaint}")
                if encounter.id in diagnoses_by_encounter:
                    details.append(f"diagnoses={'; '.join(diagnoses_by_encounter[encounter.id])}")
                if encounter.id in prescriptions_by_encounter:
                    details.append(f"prescription={'; '.join(prescriptions_by_encounter[encounter.id])}")
                recent_encounter_parts.append(" | ".join(details) if details else "recent encounter")

            facts.append(
                {
                    "type": "recent_encounters",
                    "title": "Recent encounters",
                    "snippet": "; ".join(recent_encounter_parts),
                    "source_id": str(patient_id),
                }
            )

        reports_result = await self.session.execute(
            select(MedicalReport)
            .where(MedicalReport.patient_id == patient_id)
            .order_by(MedicalReport.created_at.desc())
            .limit(3)
        )
        reports = list(reports_result.scalars().all())
        if reports:
            report_parts = [
                f"{report.report_name} ({report.upload_status.value if isinstance(report.upload_status, Enum) else report.upload_status})"
                for report in reports
            ]
            facts.append(
                {
                    "type": "lab_summary",
                    "title": "Recent reports",
                    "snippet": "; ".join(report_parts),
                    "source_id": str(patient_id),
                }
            )

        return facts

    async def retrieve_patient_context(
        self,
        current_user: User,
        patient_id: UUID,
        question: str,
    ) -> dict:
        """
        Retrieve the minimum necessary evidence for a patient-specific question.

        In production, this method should integrate with:
        - PostgreSQL for structured patient facts
        - vector search for document chunks
        - hybrid ranking and reranking
        """

        await self.validate_patient_access(
            current_user=current_user,
            patient_id=patient_id,
        )

        question_lower = question.lower()

        structured_facts = await self._fetch_structured_patient_facts(patient_id)
        if not structured_facts:
            structured_facts = [
                {
                    "type": "patient_record",
                    "title": "Authorized patient record",
                    "snippet": "Clinical evidence is retrieved only after patient authorization is verified.",
                    "source_id": str(patient_id),
                },
            ]

        if ("lab" in question_lower or "result" in question_lower or "test" in question_lower) and not any(
            fact["type"] == "lab_summary" for fact in structured_facts
        ):
            structured_facts.append(
                {
                    "type": "lab_result",
                    "title": "Lab result summary",
                    "snippet": "The system should query structured lab tables and retrieve only relevant test results for the patient.",
                    "source_id": str(patient_id),
                }
            )

        if ("med" in question_lower or "medicine" in question_lower or "prescription" in question_lower) and not any(
            fact["type"] == "medication_history" for fact in structured_facts
        ):
            structured_facts.append(
                {
                    "type": "medication",
                    "title": "Medication history",
                    "snippet": "Medication facts should be fetched from the structured medication and prescription datasets before model generation.",
                    "source_id": str(patient_id),
                }
            )

        if ("allergy" in question_lower or "sensitivity" in question_lower) and not any(
            fact["type"] == "allergy" for fact in structured_facts
        ):
            structured_facts.append(
                {
                    "type": "allergy",
                    "title": "Allergy information",
                    "snippet": "Allergy information should be retrieved from structured patient metadata and allergy tables.",
                    "source_id": str(patient_id),
                }
            )

        vector_hits = self.vector_store_service.search(
            patient_id=str(patient_id),
            query=question,
            limit=settings.MAX_RETRIEVED_CHUNKS,
        )

        document_chunks = [
            {
                "type": "clinical_note",
                "title": "Most relevant patient document chunk",
                "snippet": item["content"],
                "source_id": item["document_id"],
                "score": item["score"],
            }
            for item in vector_hits
        ]

        if not document_chunks:
            document_chunks = [
                {
                    "type": "clinical_note",
                    "title": "Most relevant patient document chunk",
                    "snippet": "Top relevant document snippets are retrieved and reranked before final answer generation.",
                    "source_id": str(patient_id),
                }
            ]

        if "history" in question_lower or "summary" in question_lower:
            document_chunks.append(
                {
                    "type": "summary",
                    "title": "Patient timeline summary",
                    "snippet": "Conversation and patient history can be summarized by the application after relevant records are retrieved.",
                    "source_id": str(patient_id),
                }
            )

        hybrid_candidates = self.hybrid_search_service.search(
            patient_id=str(patient_id),
            query=question,
            candidate_chunks=document_chunks,
        )

        reranked_chunks = self.reranker_service.rerank(
            query=question,
            candidates=hybrid_candidates,
            top_k=3,
        )

        final_context = self.context_builder_service.build_context(
            structured_facts=structured_facts,
            document_chunks=reranked_chunks,
            max_tokens=settings.MAX_CONTEXT_TOKENS,
        )

        return {
            "structured_facts": structured_facts,
            "document_chunks": final_context,
            "summary": (
                "Context assembled from authorized patient records, metadata-filtered retrieval, "
                "hybrid search, reranking, and a compact evidence set before model generation."
            ),
        }
