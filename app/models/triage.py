from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Priority(StrEnum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    fyi = "fyi"


class TaskItem(BaseModel):
    task_id: int = Field(ge=1)
    category: str
    summary: str = Field(min_length=1)
    priority: Priority
    due_date: date | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: Literal["body", "attachment", "both"] = "body"


class EmailTriageResult(BaseModel):
    email_message_id: str | None = None
    sender: str | None = None
    overall_priority: Priority
    tasks: list[TaskItem]
    reasoning: str


class TriageResponse(EmailTriageResult):
    run_id: str
    logfire_url: str | None = None
