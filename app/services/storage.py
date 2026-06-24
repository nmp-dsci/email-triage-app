from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path

from fastapi import HTTPException

from app.models.inbound import InboundAttachment
from app.runlog.run import RunContext

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, fallback: str = "attachment") -> str:
    cleaned = _SAFE_NAME.sub("_", Path(name).name).strip("._")
    return cleaned or fallback


class LocalFsStorage:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def start_run(self, config_snapshot: dict[str, object]) -> RunContext:
        return RunContext(self.root_dir, config_snapshot)

    def save_raw_request(self, run: RunContext, payload: dict[str, object]) -> None:
        run.write_json("00_request.json", payload)

    def save_attachment(
        self,
        run: RunContext,
        attachment: InboundAttachment,
        index: int,
        max_bytes: int,
    ) -> Path:
        try:
            decoded = base64.b64decode(attachment.content_bytes, validate=True)
        except binascii.Error as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid base64 attachment {attachment.name}",
            ) from exc
        if len(decoded) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Attachment {attachment.name} exceeds size limit",
            )
        filename = f"{index:02d}_{safe_filename(attachment.name)}"
        return run.write_bytes(f"attachments/{filename}", decoded)
