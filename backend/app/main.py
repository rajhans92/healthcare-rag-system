"""
Application entry point.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.diagnosis import router as diagnosis_router
from app.api.doctor import router as doctor_router
from app.api.encounter import router as encounter_router
from app.api.medical_document import router as medical_document_router
from app.api.patient import router as patient_router
from app.api.patient_access import router as patient_access_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.database import AsyncSessionLocal
from app.db.initializer import initialize_database
from app.exceptions.handlers import (
register_exception_handlers,
)
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.timing import TimingMiddleware
from app.services.medical_document_service import MedicalDocumentService

logger = logging.getLogger(__name__)


async def run_document_ingestion_worker(stop_event: asyncio.Event) -> None:

    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as session:
                service = MedicalDocumentService(session)
                processed = await service.process_pending_documents(
                    limit=settings.INGESTION_WORKER_BATCH_SIZE,
                )
                if processed:
                    logger.info(
                        "Processed %s queued medical documents.",
                        len(processed),
                    )
        except Exception:  # pragma: no cover - worker safety net
            logger.exception("Background document ingestion worker failed.")

        await asyncio.sleep(settings.INGESTION_WORKER_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """
    await initialize_database()
    print(f"Starting {settings.APP_NAME}...")

    stop_event = asyncio.Event()
    worker_task: asyncio.Task | None = None
    if settings.INGESTION_WORKER_ENABLED:
        worker_task = asyncio.create_task(
            run_document_ingestion_worker(stop_event)
        )

    try:
        yield
    finally:
        print(f"Stopping {settings.APP_NAME}...")
        if worker_task is not None:
            stop_event.set()
            await worker_task

configure_logging()


app = FastAPI(
title=settings.APP_NAME,
version=settings.APP_VERSION,
debug=settings.DEBUG,
lifespan=lifespan,
swagger_ui_parameters={
    "persistAuthorization": True,
}
)

register_exception_handlers(app)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

# CORS configuration — controllable via environment for safer toggling.
# Use CORS_ALLOW_ALL=true in .env for temporary wildcard allowance during local debugging.
if getattr(settings, "CORS_ALLOW_ALL", False):
    allow_origins = ["*"]
else:
    raw = getattr(settings, "CORS_ALLOWED_ORIGINS", None)
    if raw:
        allow_origins = [o.strip() for o in raw.split(",") if o.strip()]
    else:
        # sensible default for local development
        allow_origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Root Endpoint
# ------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "UP",
    }


# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "UP",
    }


# ------------------------------------------------------------------
# API Routes
# ------------------------------------------------------------------

app.include_router(
    auth_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    patient_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    doctor_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    encounter_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    diagnosis_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    medical_document_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    patient_access_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    chat_router,
    prefix=settings.API_V1_PREFIX,
)