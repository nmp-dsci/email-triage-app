# Test fixtures — imitation Power Automate payloads

These files imitate what **Power Automate** sends when the Office 365 Outlook
trigger **"When a new email arrives (V3)"** fires, so we can build and test the
`/triage` endpoint before the real flow exists.

## Fixture set

Three payloads covering distinct triage paths. Each is a ready-to-POST
`sample_email_*.json`; the matching `body_*.html` and source attachments are
kept alongside so they can be regenerated.

| Fixture | Attachment | Exercises | Expected triage |
|---|---|---|---|
| `sample_email_v3.json` | `invoice-INV-2045.pdf` | PDF → Markdown path; due-date that lives **only in the attachment** | 2 tasks (pay invoice by 15 Jul; book layout call), High priority |
| `sample_email_xlsx.json` | `may-expenses.xlsx` | Office/spreadsheet → Markdown table path | 1 task (approve May expenses, sign-off Thursday); should notice items > $500 |
| `sample_email_no_attachment.json` | *(none)* | Body-only; mixed task + FYI + low-priority | ~1 real task (renew parking permit by 30 Jun) + an FYI/low item, no attachment work |

All attachments are verified to convert with MarkItDown (the tool the agent
uses). Supporting files: `make_payload.py` (generator), `body*.html` (email
bodies), `invoice-INV-2045.pdf` / `may-expenses.xlsx` (source attachments).

## The payload shape (native V3 trigger output)

The JSON mirrors the connector's own field names (camelCase), so the flow can
map dynamic content **1:1** with little/no transformation:

```jsonc
{
  "id": "AAMk...",                       // message id
  "internetMessageId": "<...@contoso.com>",
  "conversationId": "...",
  "subject": "Q3 fit-out: pay deposit invoice + book layout call",
  "from": "alice@acme-fitouts.com",      // connector surfaces a plain string
  "to": "sam.ea@oatsy.com",              // (semicolon-separated if multiple)
  "cc": "",
  "importance": "High",                  // Low | Normal | High
  "hasAttachments": true,
  "receivedDateTime": "2026-06-24T00:50:40Z",
  "bodyPreview": "Hi Sam, ...",          // plain-text preview
  "body": "<html>...</html>",            // full HTML body
  "attachments": [
    {
      "@odata.type": "#Microsoft.OutlookServices.FileAttachment",
      "id": "...",
      "name": "invoice-INV-2045.pdf",
      "contentType": "application/pdf",
      "size": 1001,
      "isInline": false,
      "contentBytes": "JVBERi0xLjQK..."  // base64 of the file (the bit we OCR/convert)
    }
  ]
}
```

> **Why this shape:** the Office 365 Outlook V3 trigger exposes `contentBytes`
> (base64) for each attachment only when the flow's **Include Attachments** =
> **Yes**. That base64 blob is exactly what our agent decodes and feeds to
> MarkItDown. `from`/`to`/`cc` come through as plain strings on this connector
> (Microsoft Graph's nested `{ "emailAddress": { "address": ... } }` form is an
> alternative — our API accepts either).

## Build your own payload from a real email

1. Save the email body as `body.html` (or `.txt`).
2. Save each attachment locally (PDF, docx, xlsx, png, ...).
3. Run:

```bash
cd tests/data
python make_payload.py \
  --subject "Your subject" \
  --from "sender@example.com" \
  --to "ea@oatsy.com" \
  --importance High \
  --body-file body.html \
  --attachment ./your-file.pdf \
  --attachment ./another.docx \
  --out my_email.json
```

`make_payload.py --help` lists every flag. Attachments are base64-encoded for
you; content types are guessed from the file extension.

## Send it to the API (once the service is running)

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $TRIAGE_API_KEY" \
  --data @sample_email_v3.json
```

## How the real Power Automate flow will map to this

| Flow step | Detail |
|---|---|
| Trigger | **Office 365 Outlook → When a new email arrives (V3)**, *Include Attachments* = **Yes** |
| Action | **HTTP** (or a custom connector) → `POST {service-url}/triage` |
| Headers | `Content-Type: application/json`, `X-API-Key: <secret>` |
| Body | A JSON object built from the trigger's dynamic content, in the shape above. The simplest version is to pass the trigger body through and let our API read the fields it needs. |

When we have a sample of the **actual** flow output (see
`ai_plan/s1_app_init.md` §12, item 1), we confirm the exact field names/casing
and add any needed aliases to the `InboundEmail` model — the fixture here is the
working stand-in until then.
