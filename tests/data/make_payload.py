#!/usr/bin/env python3
"""Build an imitation Power Automate (Office 365 Outlook "When a new email
arrives (V3)") JSON payload for testing the /triage endpoint.

The output mirrors the native trigger body so a Power Automate flow can POST it
with minimal/zero field mapping. Attachments are base64-encoded into
`contentBytes`, exactly as the connector does when "Include Attachments" = Yes.

Examples
--------
# Use your own email text + attachments:
python make_payload.py \
    --subject "Quote for the Q3 fit-out" \
    --from "alice@contoso.com" \
    --to "ea@oatsy.com" \
    --importance High \
    --body-file body.html \
    --attachment ./invoice-INV-2045.pdf \
    --attachment ./floorplan.png \
    --out my_email.json

# Minimal (inline body):
python make_payload.py --subject "Hi" --from a@b.com --to ea@oatsy.com \
    --body "<p>Please action the attached.</p>" --out my_email.json
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _attachment_obj(path: Path) -> dict:
    data = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "@odata.type": "#Microsoft.OutlookServices.FileAttachment",
        "id": uuid.uuid4().hex,
        "name": path.name,
        "contentType": content_type,
        "size": len(data),
        "isInline": False,
        "contentBytes": base64.b64encode(data).decode("ascii"),
    }


def build_payload(
    *,
    subject: str,
    sender: str,
    to: str,
    cc: str,
    importance: str,
    body_html: str,
    attachments: list[Path],
) -> dict:
    atts = [_attachment_obj(p) for p in attachments]
    received = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # bodyPreview is the connector's plain-text preview (first ~255 chars).
    preview = body_html.replace("<", " <").strip()[:255]
    return {
        "id": f"AAMk{uuid.uuid4().hex}",
        "internetMessageId": f"<{uuid.uuid4().hex}@contoso.com>",
        "conversationId": uuid.uuid4().hex,
        "subject": subject,
        "from": sender,
        "to": to,
        "cc": cc,
        "importance": importance,
        "hasAttachments": bool(atts),
        "receivedDateTime": received,
        "bodyPreview": preview,
        "body": body_html,
        "attachments": atts,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--subject", required=True)
    p.add_argument("--from", dest="sender", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--cc", default="")
    p.add_argument("--importance", default="Normal", choices=["Low", "Normal", "High"])
    g = p.add_mutually_exclusive_group()
    g.add_argument("--body", help="Inline HTML body string")
    g.add_argument("--body-file", type=Path, help="Path to an .html/.txt body file")
    p.add_argument("--attachment", action="append", type=Path, default=[], help="Repeatable; file to attach")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    if args.body_file:
        body_html = args.body_file.read_text(encoding="utf-8")
    elif args.body:
        body_html = args.body
    else:
        body_html = "<p>(no body)</p>"

    for a in args.attachment:
        if not a.is_file():
            raise SystemExit(f"Attachment not found: {a}")

    payload = build_payload(
        subject=args.subject,
        sender=args.sender,
        to=args.to,
        cc=args.cc,
        importance=args.importance,
        body_html=body_html,
        attachments=args.attachment,
    )
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    n = len(payload["attachments"])
    print(f"Wrote {args.out}  ({n} attachment{'s' if n != 1 else ''})")


if __name__ == "__main__":
    main()
