"""
Chat service for the healthcare RAG flow.

This is intentionally a production-oriented scaffold. The real pipeline will
later connect to structured patient retrieval, hybrid vector search, reranking,
and the LLM adapter.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.exceptions import ValidationException
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatCitation, ChatResponse
from app.services.audit_service import AuditService
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ChatService:
    """
    Service responsible for authorized chat interactions over patient records.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.retrieval_service = RetrievalService(session)
        self.llm_service = LLMService()
        self.audit_service = AuditService(session)

    async def ask_question(
        self,
        current_user: User,
        request: ChatMessageRequest,
    ) -> ChatResponse:
        """
        Process a clinical question against authorized patient context.

        The flow supports both patients and doctors. Doctors can only query a
        patient after the patient access check has been approved.

        1. validate patient access
        2. retrieve the minimum required patient context
        3. produce grounded answer text and citations
        4. return token estimate and context count
        """

        if not request.question.strip():
            await self.audit_service.log_event(
                user_id=current_user.id,
                action="chat_question_rejected",
                resource_type="patient",
                resource_id=request.patient_id,
                status="FAILED",
                details={"reason": "empty_question"},
            )
            raise ValidationException(
                message="Question cannot be empty.",
            )

        await self.audit_service.log_event(
            user_id=current_user.id,
            action="chat_question_received",
            resource_type="patient",
            resource_id=request.patient_id,
            status="SUCCESS",
            details={
                "include_medical_knowledge": request.include_medical_knowledge,
                "include_patient_summary": request.include_patient_summary,
            },
        )

        retrieval_context = await self.retrieval_service.retrieve_patient_context(
            current_user=current_user,
            patient_id=request.patient_id,
            question=request.question,
        )

        structured_facts = retrieval_context["structured_facts"]
        document_chunks = retrieval_context["document_chunks"]

        citations = [
            ChatCitation(
                source_type=item["type"],
                source_id=UUID(str(item["source_id"])) if item.get("source_id") else None,
                title=item["title"],
                snippet=item["snippet"],
            )
            for item in structured_facts + document_chunks
        ]

        final_context = structured_facts + document_chunks

        user_role = getattr(current_user, "role", None)
        role_name = user_role.value if hasattr(user_role, "value") else str(user_role)

        answer = self.llm_service.generate_answer(
            question=request.question,
            context=final_context,
            user_role=role_name,
            doctor_context=request.doctor_context,
        )

        context_count = len(final_context)

        response = ChatResponse(
            answer=answer,
            citations=citations,
            patient_id=request.patient_id,
            token_estimate=self._estimate_token_usage(
                question=request.question,
                include_medical_knowledge=request.include_medical_knowledge,
                include_patient_summary=request.include_patient_summary,
            ),
            retrieved_context_count=context_count,
            message="Grounded retrieval pipeline is active and access is validated before the answer is generated.",
        )

        await self.audit_service.log_event(
            user_id=current_user.id,
            action="chat_response_generated",
            resource_type="patient",
            resource_id=request.patient_id,
            status="SUCCESS",
            details={
                "retrieved_context_count": context_count,
                "token_estimate": response.token_estimate,
            },
        )

        return response

    def _estimate_context_count(
        self,
        include_medical_knowledge: bool,
        include_patient_summary: bool,
    ) -> int:
        """
        Estimate how many retrieval chunks will be built into the final LLM context.
        """

        base_count = 2
        if include_patient_summary:
            base_count += 2
        if include_medical_knowledge:
            base_count += 2

        return base_count

    def _estimate_token_usage(
        self,
        question: str,
        include_medical_knowledge: bool,
        include_patient_summary: bool,
    ) -> int:
        """
        Return a lightweight estimate of token usage used in the request context.

        This is a rough planning value; real token counting should use the exact
        LLM tokenizer chosen for the deployment.
        """

        base_tokens = 180
        question_tokens = max(20, len(question.split()) * 2)
        context_tokens = 600

        if include_patient_summary:
            context_tokens += 400
        if include_medical_knowledge:
            context_tokens += 500

        return base_tokens + question_tokens + context_tokens
