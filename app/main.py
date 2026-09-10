"""
app.main
~~~~~~~~
FastAPI application entry point.

This module creates and configures the FastAPI app instance.
In Phase 1, the app runs with a single /health endpoint as a skeleton.
Business routes, database, and bot webhook are wired in later phases.

Run locally:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Destrucyion Telegram Bot",
        description=(
            "Multi-tenant Telegram media preservation service. "
            "Preserves timed/self-destructing Telegram media to Saved Messages."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    @application.get("/api/health", tags=["health"])
    async def health() -> JSONResponse:
        """Return application health status.

        This endpoint is always available and requires no authentication.
        Used by load balancers, monitoring, and CI pipelines.
        """
        return JSONResponse(
            content={
                "status": "ok",
                "service": "destrucyion-telegram-bot",
                "version": "0.1.0",
                "environment": settings.app_env,
            }
        )

    log.info("app_created", env=settings.app_env)
    return application


app = create_app()
