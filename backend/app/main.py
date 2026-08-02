"""
Application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.core.config import settings
from app.exceptions.handlers import (
    register_exception_handlers,
)
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.logging import LoggingMiddleware
from app.core.logging import configure_logging
from app.middleware.timing import TimingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """

    # Startup
    print(f"Starting {settings.APP_NAME}...")

    yield

    # Shutdown
    print(f"Stopping {settings.APP_NAME}...")

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
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