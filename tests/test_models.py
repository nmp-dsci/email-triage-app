from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_fixture(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def test_inbound_email_accepts_power_automate_fixture_aliases() -> None:
    inbound = pytest.importorskip("app.models.inbound")

    email = inbound.InboundEmail.model_validate(load_fixture("sample_email_v3.json"))

    assert email.message_id
    assert email.internet_message_id
    assert email.conversation_id
    assert email.subject
    assert email.sender
    assert email.importance in {"Low", "Normal", "High"}
    assert email.received_at is not None
    assert email.has_attachments is True
    assert len(email.attachments) == 1

    attachment = email.attachments[0]
    assert attachment.name == "invoice-INV-2045.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.content_bytes
    assert attachment.size is not None
    assert attachment.is_inline is False


def test_inbound_email_accepts_snake_case_for_internal_callers() -> None:
    inbound = pytest.importorskip("app.models.inbound")

    email = inbound.InboundEmail.model_validate(
        {
            "message_id": "msg-1",
            "internet_message_id": "<msg-1@example.com>",
            "conversation_id": "conv-1",
            "subject": "Approve the quote",
            "sender": "sender@example.com",
            "to": "owner@example.com",
            "importance": "High",
            "received_at": "2026-06-24T01:02:03Z",
            "body_preview": "Please approve",
            "body": "<p>Please approve</p>",
            "has_attachments": True,
            "attachments": [
                {
                    "name": "quote.pdf",
                    "content_type": "application/pdf",
                    "content_bytes": "cGRm",
                    "is_inline": True,
                }
            ],
        }
    )

    assert email.message_id == "msg-1"
    assert email.sender == "sender@example.com"
    assert email.received_at is not None
    assert email.attachments[0].content_type == "application/pdf"
    assert email.attachments[0].is_inline is True


def test_inbound_email_rejects_unknown_importance() -> None:
    inbound = pytest.importorskip("app.models.inbound")
    validation_error = pytest.importorskip("pydantic").ValidationError

    payload = load_fixture("sample_email_no_attachment.json")
    payload["importance"] = "Critical"

    with pytest.raises(validation_error):
        inbound.InboundEmail.model_validate(payload)


def test_triage_result_serializes_expected_output_contract() -> None:
    triage = pytest.importorskip("app.models.triage")

    result = triage.EmailTriageResult(
        email_message_id="msg-1",
        sender="sender@example.com",
        overall_priority=triage.Priority.high,
        tasks=[
            triage.TaskItem(
                task_id=1,
                category="Finance/Invoice",
                summary="Pay the fit-out deposit invoice.",
                priority=triage.Priority.high,
                due_date="2026-07-01",
                confidence=0.92,
                source="attachment",
            )
        ],
        reasoning="The attachment is an invoice with a due date.",
    )

    dumped = result.model_dump(mode="json")

    assert dumped == {
        "email_message_id": "msg-1",
        "sender": "sender@example.com",
        "overall_priority": "high",
        "tasks": [
            {
                "task_id": 1,
                "category": "Finance/Invoice",
                "summary": "Pay the fit-out deposit invoice.",
                "priority": "high",
                "due_date": "2026-07-01",
                "confidence": 0.92,
                "source": "attachment",
            }
        ],
        "reasoning": "The attachment is an invoice with a due date.",
    }


@pytest.mark.parametrize("bad_confidence", [-0.01, 1.01])
def test_task_item_rejects_confidence_outside_zero_to_one(
    bad_confidence: float,
) -> None:
    triage = pytest.importorskip("app.models.triage")
    validation_error = pytest.importorskip("pydantic").ValidationError

    with pytest.raises(validation_error):
        triage.TaskItem(
            task_id=1,
            category="Admin/Office",
            summary="Follow up.",
            priority=triage.Priority.medium,
            confidence=bad_confidence,
        )
