from __future__ import annotations

import time
from pathlib import Path

from app.agent.triage_agent import ConvertedAttachment
from app.models.inbound import InboundAttachment
from app.runlog.run import RunContext
from app.services.conversion import convert_to_markdown


def convert_attachment_to_markdown(
    run: RunContext,
    source_path: Path,
    attachment: InboundAttachment,
    index: int,
) -> ConvertedAttachment:
    started = time.perf_counter()
    markdown = convert_to_markdown(source_path, attachment.content_type)
    markdown_path = run.write_text(f"attachments/{source_path.stem}.md", markdown)
    run.write_json(
        f"attachments/{source_path.stem}.conversion.json",
        {
            "type": "attachment_conversion",
            "step": index,
            "name": attachment.name,
            "content_type": attachment.content_type,
            "source_path": str(source_path),
            "markdown_path": str(markdown_path),
            "markdown_chars": len(markdown),
            "duration_ms": int((time.perf_counter() - started) * 1000),
        },
    )
    return ConvertedAttachment(
        name=attachment.name,
        content_type=attachment.content_type,
        source_path=source_path,
        markdown_path=markdown_path,
        markdown=markdown,
    )
