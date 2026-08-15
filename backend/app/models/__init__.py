"""Import all SQLAlchemy model modules so mapper relationships resolve consistently."""

from app.models.audit_log import AuditLog  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.chat_session import ChatSession  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.encounter import Encounter  # noqa: F401
from app.models.diagnosis import Diagnosis  # noqa: F401
from app.models.prescription import Prescription  # noqa: F401
from app.models.doctor_note import DoctorNote  # noqa: F401
from app.models.medical_report import MedicalReport  # noqa: F401
from app.models.medical_document import MedicalDocument  # noqa: F401
from app.models.prescription_item import PrescriptionItem  # noqa: F401
from app.models.patient_access import PatientAccess  # noqa: F401
