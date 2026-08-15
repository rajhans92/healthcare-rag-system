"""
Chat API endpoints for the healthcare RAG flow.
"""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser
from app.db.database import get_db
from app.schemas.chat import ChatMessageRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/ask",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def ask_question(
    request: ChatMessageRequest,
    current_user: CurrentUser,
    service: ChatService = Depends(lambda db=Depends(get_db): ChatService(db)),
) -> ChatResponse:
    """
    Ask a clinical question using the authorized patient context.

    This endpoint is intentionally a lightweight orchestration scaffold. The true
    version should perform access validation, retrieval, reranking, and full LLM
    grounding before returning a final response.
    """

    return await service.ask_question(
        current_user=current_user,
        request=request,
    )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
)
async def chat_status() -> dict:
    """
    Simple health/status endpoint for the chat pipeline.
    """

    return {
        "status": "ready",
        "pipeline": "authorized_patient_retrieval",
    }
