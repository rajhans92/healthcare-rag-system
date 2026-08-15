"""
Chat request and response schemas for the healthcare RAG flow.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """
    Request for asking a question against a patient's authorized records.
    """

    patient_id: UUID

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Clinical question to answer using retrieved patient context.",
    )

    doctor_context: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional doctor-specific objective or context such as 'summarize patient history for follow-up care'.",
    )

    include_medical_knowledge: bool = Field(
        default=False,
        description="Whether to include approved clinical knowledge in the retrieval flow.",
    )

    include_patient_summary: bool = Field(
        default=True,
        description="Whether to include the patient summary context in the answer generation step.",
    )


class ChatCitation(BaseModel):
    """
    Source citation returned with a grounded answer.
    """

    source_type: str = Field(
        ...,
        description="Type of evidence such as patient_record, lab_result, note, or guideline.",
    )

    source_id: UUID | None = None

    title: str | None = None

    snippet: str | None = None

    url: str | None = None


class ChatResponse(BaseModel):
    """
    Response returned after a grounded clinical retrieval and generation step.
    """

    model_config = ConfigDict(from_attributes=True)

    answer: str

    citations: list[ChatCitation] = Field(
        default_factory=list,
        description="Evidence supporting the answer.",
    )

    patient_id: UUID

    token_estimate: int = Field(
        default=0,
        description="Estimated input token budget used for the request.",
    )

    retrieved_context_count: int = Field(
        default=0,
        description="Number of relevant chunks or records retrieved before LLM generation.",
    )

    message: str = Field(
        default="Answer generated from authorized patient context and grounded evidence.",
    )


class ChatSessionResponse(BaseModel):
    """
    Lightweight chat session metadata response.
    """

    session_id: UUID

    patient_id: UUID

    last_question: str

    created_at: str
