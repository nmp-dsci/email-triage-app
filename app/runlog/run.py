from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel


class RunContext:
    def __init__(self, root_dir: Path, config_snapshot: dict[str, Any]) -> None:
        now = datetime.now(UTC)
        self.run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
        self.root_dir = root_dir / now.strftime("%Y-%m-%d") / self.run_id
        self.attachments_dir = self.root_dir / "attachments"
        self.llm_dir = self.root_dir / "llm"
        self.started_at = now
        self._timer = time.perf_counter()
        self._config_snapshot = config_snapshot
        self._status = "running"
        self._error: str | None = None
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.llm_dir.mkdir(parents=True, exist_ok=True)
        self.write_json("run.json", self._manifest())

    def write_json(self, relative_path: str, data: Any) -> Path:
        path = self.root_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_text(self, relative_path: str, text: str) -> Path:
        path = self.root_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, relative_path: str, data: bytes) -> Path:
        path = self.root_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def llm_call_path(self, index: int, kind: str) -> str:
        return f"llm/{index:02d}_{kind}.json"

    def complete(self, result: Any) -> None:
        self._status = "completed"
        self.write_json("result.json", result)
        self.write_json("run.json", self._manifest())

    def fail(self, exc: BaseException) -> None:
        self._status = "failed"
        self._error = f"{type(exc).__name__}: {exc}"
        self.write_json("run.json", self._manifest())

    def _manifest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self._status,
            "started_at": self.started_at.isoformat(),
            "duration_ms": int((time.perf_counter() - self._timer) * 1000),
            "config": self._config_snapshot,
            "error": self._error,
        }


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value
