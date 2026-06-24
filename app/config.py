from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class VocabItem(BaseModel):
    label: str
    definition: str


DEFAULT_CATEGORIES = [
    VocabItem(
        label="Finance/Invoice",
        definition="Payments, invoices, expenses, budgets, or approvals.",
    ),
    VocabItem(
        label="Scheduling",
        definition="Meetings, calls, bookings, deadlines, or calendar coordination.",
    ),
    VocabItem(label="Travel", definition="Flights, accommodation, transport, or trip logistics."),
    VocabItem(
        label="Approvals",
        definition="Review, sign-off, authorization, or decision requests.",
    ),
    VocabItem(
        label="Admin/Office",
        definition="Office operations, permits, facilities, supplies, or admin tasks.",
    ),
    VocabItem(label="FYI", definition="Informational items where no action is required."),
]

DEFAULT_PRIORITIES = [
    VocabItem(
        label="urgent",
        definition="Needs same-day action or has severe consequence if missed.",
    ),
    VocabItem(label="high", definition="Important and time-bound, usually within days."),
    VocabItem(label="medium", definition="Action is needed but not immediately critical."),
    VocabItem(label="low", definition="Low consequence or flexible timing."),
    VocabItem(label="fyi", definition="Information only, no action required."),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "ea-email-triage"
    environment: str = "local"
    llm_provider: Literal["mock", "anthropic", "foundry"] = "mock"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str | None = None
    azure_foundry_base_url: str | None = None
    azure_foundry_api_key: str | None = None
    logfire_token: str | None = None
    logfire_send: bool = False
    triage_api_key: str = "dev-secret"
    runs_dir: Path = Path("runs")
    max_attachment_bytes: int = 15 * 1024 * 1024
    category_vocab_file: Path | None = None
    priority_vocab_file: Path | None = None
    azure_region: str = "Australia East"

    @field_validator("runs_dir", mode="before")
    @classmethod
    def _expand_runs_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser()

    @property
    def categories(self) -> list[VocabItem]:
        return _load_vocab(self.category_vocab_file, DEFAULT_CATEGORIES)

    @property
    def priorities(self) -> list[VocabItem]:
        return _load_vocab(self.priority_vocab_file, DEFAULT_PRIORITIES)

    def public_config(self) -> dict[str, object]:
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "categories": [item.model_dump() for item in self.categories],
            "priorities": [item.model_dump() for item in self.priorities],
            "region": self.azure_region,
            "auth": "X-API-Key",
        }


def _load_vocab(path: Path | None, default: list[VocabItem]) -> list[VocabItem]:
    if path is None:
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    return [VocabItem.model_validate(item) for item in data]


@lru_cache
def get_settings() -> Settings:
    return Settings()
