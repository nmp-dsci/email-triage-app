from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InboundAttachment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str
    content_type: str | None = Field(None, alias="contentType")
    content_bytes: str = Field(alias="contentBytes")
    size: int | None = None
    is_inline: bool = Field(False, alias="isInline")


class InboundEmail(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    message_id: str | None = Field(None, alias="id")
    internet_message_id: str | None = Field(None, alias="internetMessageId")
    conversation_id: str | None = Field(None, alias="conversationId")
    subject: str = ""
    sender: str = Field("", alias="from")
    to: str = ""
    cc: str = ""
    importance: Literal["Low", "Normal", "High"] = "Normal"
    received_at: datetime | None = Field(None, alias="receivedDateTime")
    body_preview: str = Field("", alias="bodyPreview")
    body: str = ""
    has_attachments: bool = Field(False, alias="hasAttachments")
    attachments: list[InboundAttachment] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def flatten_graph_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        flattened = dict(data)
        sender = flattened.get("from")
        if isinstance(sender, dict):
            flattened["from"] = _email_address(sender)
        for key in ("to", "cc"):
            value = flattened.get(key)
            if isinstance(value, list):
                flattened[key] = ";".join(filter(None, [_email_address(item) for item in value]))
        body = flattened.get("body")
        if isinstance(body, dict):
            flattened["body"] = body.get("content", "")
        return flattened


def _email_address(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        email = value.get("emailAddress", value)
        if isinstance(email, dict):
            return str(email.get("address") or email.get("name") or "")
    return ""
