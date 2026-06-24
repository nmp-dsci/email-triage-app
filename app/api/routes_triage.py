from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.agent.tools import convert_attachment_to_markdown
from app.agent.triage_agent import run_triage_agent as run_triage
from app.config import Settings, get_settings
from app.models.inbound import InboundEmail
from app.models.triage import TriageResponse
from app.services.storage import LocalFsStorage

router = APIRouter()
SettingsDep = Annotated[Settings, Depends(get_settings)]
ApiKeyHeader = Annotated[str | None, Header(alias="X-API-Key")]


def require_api_key(
    settings: SettingsDep,
    x_api_key: ApiKeyHeader = None,
) -> None:
    if settings.triage_api_key and x_api_key != settings.triage_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@router.post("/triage", response_model=TriageResponse, dependencies=[Depends(require_api_key)])
async def triage_email(
    email: InboundEmail,
    settings: SettingsDep,
) -> TriageResponse:
    storage = LocalFsStorage(settings.runs_dir)
    run = storage.start_run(settings.public_config())
    try:
        storage.save_raw_request(run, email.model_dump(mode="json", by_alias=True))
        converted = []
        attachment_index = 1
        for attachment in email.attachments:
            if attachment.is_inline:
                continue
            source_path = storage.save_attachment(
                run=run,
                attachment=attachment,
                index=attachment_index,
                max_bytes=settings.max_attachment_bytes,
            )
            converted.append(
                convert_attachment_to_markdown(
                    run=run,
                    source_path=source_path,
                    attachment=attachment,
                    index=attachment_index,
                )
            )
            attachment_index += 1
        result = await run_triage(email, converted, run, settings)
        result_data = result if isinstance(result, dict) else result.model_dump(mode="json")
        response = TriageResponse(run_id=run.run_id, **result_data)
        run.complete(response)
        return response
    except Exception as exc:
        run.fail(exc)
        raise


@router.get("/runs/{run_id}")
async def get_run(run_id: str, settings: SettingsDep) -> dict[str, Any]:
    matches = list(settings.runs_dir.glob(f"*/{run_id}"))
    if not matches:
        raise HTTPException(status_code=404, detail="Run not found")
    run_dir = matches[0]
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "manifest": _read_json(run_dir / "run.json"),
        "artifacts": [
            str(path.relative_to(run_dir)) for path in sorted(run_dir.rglob("*")) if path.is_file()
        ],
    }


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
