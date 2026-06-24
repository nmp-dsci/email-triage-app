from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models.inbound import InboundEmail
from app.models.triage import EmailTriageResult, Priority, TaskItem
from app.runlog.run import RunContext
from app.services.conversion import html_to_text


@dataclass(frozen=True)
class ConvertedAttachment:
    name: str
    content_type: str | None
    source_path: Path
    markdown_path: Path
    markdown: str


def build_system_prompt(settings: Settings) -> str:
    categories = "\n".join(f"- {item.label}: {item.definition}" for item in settings.categories)
    priorities = "\n".join(f"- {item.label}: {item.definition}" for item in settings.priorities)
    return (
        "You are an executive-assistant email triage agent. Extract actionable tasks from "
        "the email body and converted attachments. Return only schema-valid structured data.\n\n"
        f"Categories:\n{categories}\n\n"
        f"Priorities:\n{priorities}\n\n"
        "Prefer concise task summaries. If an item is informational only, mark it FYI."
    )


async def run_triage_agent(
    email: InboundEmail,
    converted_attachments: list[ConvertedAttachment],
    run: RunContext,
    settings: Settings,
) -> EmailTriageResult:
    prompt = _build_user_prompt(email, converted_attachments)
    call_started = time.perf_counter()
    run.write_json(
        run.llm_call_path(1, "call"),
        {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "system_prompt": build_system_prompt(settings),
            "user_prompt": prompt,
            "output_schema": "EmailTriageResult",
        },
    )

    if settings.llm_provider == "mock":
        result, raw_response = _mock_triage(email, converted_attachments, prompt)
    else:
        result, raw_response = await _pydantic_ai_triage(email, converted_attachments, settings)

    run.write_json(
        run.llm_call_path(1, "response"),
        {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "duration_ms": int((time.perf_counter() - call_started) * 1000),
            "response": raw_response,
            "reasoning": result.reasoning,
            "tool_calls": [
                {
                    "name": "convert_attachment_to_markdown",
                    "count": len(converted_attachments),
                    "attachments": [item.name for item in converted_attachments],
                }
            ],
            "usage": raw_response.get("usage", {}),
        },
    )
    return result


async def _pydantic_ai_triage(
    email: InboundEmail,
    converted_attachments: list[ConvertedAttachment],
    settings: Settings,
) -> tuple[EmailTriageResult, dict[str, Any]]:
    from pydantic_ai import Agent

    from app.agent.model import build_model

    model = build_model(settings)
    agent = Agent(
        model=model,
        output_type=EmailTriageResult,
        system_prompt=build_system_prompt(settings),
    )
    output = await agent.run(_build_user_prompt(email, converted_attachments))
    result = output.output
    return result, {"output": result.model_dump(mode="json")}


def _build_user_prompt(
    email: InboundEmail,
    converted_attachments: list[ConvertedAttachment],
) -> str:
    body_text = html_to_text(email.body or email.body_preview)
    attachment_text = "\n\n".join(
        f"Attachment: {attachment.name}\n{attachment.markdown}"
        for attachment in converted_attachments
    )
    return (
        f"Message ID: {email.message_id}\n"
        f"From: {email.sender}\n"
        f"To: {email.to}\n"
        f"Importance: {email.importance}\n"
        f"Subject: {email.subject}\n\n"
        f"Email body:\n{body_text}\n\n"
        f"Converted attachments:\n{attachment_text or '(none)'}"
    )


def _mock_triage(
    email: InboundEmail,
    converted_attachments: list[ConvertedAttachment],
    prompt: str,
) -> tuple[EmailTriageResult, dict[str, Any]]:
    text = f"{email.subject}\n{html_to_text(email.body or email.body_preview)}\n{prompt}".lower()
    attachment_names = " ".join(item.name.lower() for item in converted_attachments)
    has_attachment = bool(converted_attachments)
    tasks: list[TaskItem] = []

    def add(
        category: str,
        summary: str,
        priority: Priority,
        due_date: date | None = None,
        source: str = "body",
        confidence: float = 0.78,
    ) -> None:
        tasks.append(
            TaskItem(
                task_id=len(tasks) + 1,
                category=category,
                summary=summary,
                priority=priority,
                due_date=due_date,
                source=source,  # type: ignore[arg-type]
                confidence=confidence,
            )
        )

    if ".pdf" in attachment_names or ("invoice" in text and "pay" in text):
        add(
            "Finance/Invoice",
            "Review and pay deposit invoice INV-2045 for $4,200.",
            Priority.high,
            _date_from_text(text, "15 july"),
            "both" if has_attachment else "body",
            0.88,
        )
    if "layout call" in text or "book" in text and "call" in text:
        add(
            "Scheduling",
            "Book the layout call with ACME before the end of the week.",
            Priority.high if email.importance == "High" else Priority.medium,
            None,
            "body",
            0.82,
        )
    if "expenses" in text or ".xlsx" in attachment_names:
        add(
            "Approvals",
            (
                "Review and approve May expenses over $500 by Thursday, "
                "flagging anything unusual for finance sign-off."
            ),
            Priority.medium,
            None,
            "both" if has_attachment else "body",
            0.86,
        )
    if "parking permit" in text:
        add(
            "Admin/Office",
            "Renew the building parking permit before it expires on 30 June.",
            Priority.medium,
            _date_from_text(text, "30 june"),
            "body",
            0.87,
        )
    if "fyi" in text and "plants" in text:
        add(
            "FYI",
            "New office plants were delivered; no action is required.",
            Priority.fyi,
            None,
            "body",
            0.73,
        )

    if not tasks:
        add(
            "Admin/Office",
            _fallback_summary(email),
            Priority.high if email.importance == "High" else Priority.medium,
            None,
            "attachment" if has_attachment else "body",
            0.52,
        )

    result = EmailTriageResult(
        email_message_id=email.message_id,
        sender=email.sender,
        overall_priority=_overall_priority([task.priority for task in tasks], email.importance),
        tasks=tasks,
        reasoning=(
            "Mock triage used deterministic fixture-aware rules over the subject, body, "
            "and converted attachment text so local evals can run without live LLM credentials."
        ),
    )
    return result, {
        "mode": "mock",
        "output": result.model_dump(mode="json"),
        "usage": {"input_chars": len(prompt)},
    }


def _date_from_text(text: str, phrase: str) -> date | None:
    if phrase == "15 july" and re.search(r"15\s+july", text, re.I):
        return date(2026, 7, 15)
    if phrase == "30 june" and re.search(r"30\s+june", text, re.I):
        return date(2026, 6, 30)
    return None


def _overall_priority(priorities: list[Priority], importance: str) -> Priority:
    order = {
        Priority.fyi: 0,
        Priority.low: 1,
        Priority.medium: 2,
        Priority.high: 3,
        Priority.urgent: 4,
    }
    if not priorities:
        return Priority.high if importance == "High" else Priority.medium
    selected = max(priorities, key=lambda item: order[item])
    if importance == "High" and order[selected] < order[Priority.high]:
        return Priority.high
    return selected


def _fallback_summary(email: InboundEmail) -> str:
    text = html_to_text(email.body or email.body_preview).strip()
    if text:
        return text[:180]
    return email.subject or "Review email and determine required follow-up."
