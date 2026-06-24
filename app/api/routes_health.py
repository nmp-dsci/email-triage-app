from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
async def version() -> dict[str, str]:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }
