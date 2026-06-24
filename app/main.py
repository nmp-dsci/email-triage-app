from __future__ import annotations

import logfire
from fastapi import FastAPI

from app.api import routes_health, routes_triage
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logfire.configure(
        service_name=settings.service_name,
        token=settings.logfire_token,
        send_to_logfire=settings.logfire_send,
    )
    app = FastAPI(title="Email Triage App", version="0.1.0")
    try:
        logfire.instrument_fastapi(app)
        logfire.instrument_httpx()
        if hasattr(logfire, "instrument_pydantic_ai"):
            logfire.instrument_pydantic_ai()
    except Exception:
        # Observability should not stop local demo/test boot.
        pass
    app.include_router(routes_health.router)
    app.include_router(routes_triage.router)
    return app


app = create_app()
