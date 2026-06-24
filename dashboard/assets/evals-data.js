window.EMAIL_TRIAGE_EVALS = {
  "generated_at": "2026-06-24T01:52:11.538664Z",
  "config": {
    "llm_provider": "mock",
    "llm_model": "claude-sonnet-4-6",
    "categories": [
      {
        "label": "finance",
        "definition": "Invoices, expenses, approvals, payments, budgets, or reconciliation work."
      },
      {
        "label": "scheduling",
        "definition": "Calendar, meeting, call, booking, deadline, or coordination work."
      },
      {
        "label": "operations",
        "definition": "Office, facilities, vendor, compliance, or process tasks."
      },
      {
        "label": "admin",
        "definition": "General assistant tasks that do not fit a more specific category."
      },
      {
        "label": "fyi",
        "definition": "Information-only items with no action required."
      }
    ],
    "priorities": [
      {
        "label": "urgent",
        "definition": "Needs immediate action or has same-day risk."
      },
      {
        "label": "high",
        "definition": "Important, time-sensitive, or financially material."
      },
      {
        "label": "medium",
        "definition": "Actionable with a known deadline, but not urgent."
      },
      {
        "label": "low",
        "definition": "Useful action with low risk or flexible timing."
      },
      {
        "label": "fyi",
        "definition": "No task required; keep for awareness only."
      }
    ],
    "region": "Australia East",
    "auth": "X-API-Key",
    "api_url": "offline",
    "mode": "offline"
  },
  "methodology": {
    "diagram": "methodology/solution-diagram.svg",
    "summary_md": "Power Automate posts an Outlook email payload to the FastAPI triage service. The service validates the request, persists the run, converts attachments to Markdown, asks the LLM agent for a structured task list, and saves trace artifacts for review."
  },
  "cases": [
    {
      "id": "01-invoice-pdf",
      "title": "Q3 fit-out: pay deposit invoice + book layout call",
      "request": {
        "id": "AAMk596af063ab0746d69420db693dabbc3c",
        "internetMessageId": "<c5a64d131da34d64bb74713b5a483f55@contoso.com>",
        "conversationId": "85e97a971daf418da1cdde8e85f81755",
        "subject": "Q3 fit-out: pay deposit invoice + book layout call",
        "from": "alice@acme-fitouts.com",
        "to": "sam.ea@oatsy.com",
        "cc": "",
        "importance": "High",
        "hasAttachments": true,
        "receivedDateTime": "2026-06-24T00:50:40Z",
        "bodyPreview": "<html> <body>\n <p>Hi Sam, </p>\n <p>Two things before end of week: </p>\n <ol>\n   <li>Please review and  <b>pay the attached deposit invoice </b> (INV-2045, $4,200) by  <b>15 July </b> so ACME can lock in our install slot. </li>\n   <li>Can you also  <b>book",
        "body": "<html><body>\n<p>Hi Sam,</p>\n<p>Two things before end of week:</p>\n<ol>\n  <li>Please review and <b>pay the attached deposit invoice</b> (INV-2045, $4,200) by <b>15 July</b> so ACME can lock in our install slot.</li>\n  <li>Can you also <b>book a 30-min call</b> with their project lead next week to confirm the boardroom layout? Anytime Tue/Wed works for me.</li>\n</ol>\n<p>This is fairly urgent &mdash; the slot is only held until Friday.</p>\n<p>Thanks,<br>Alice</p>\n</body></html>\n",
        "attachments": [
          {
            "@odata.type": "#Microsoft.OutlookServices.FileAttachment",
            "id": "e976041ba3b0478f8da2928fd222722d",
            "name": "invoice-INV-2045.pdf",
            "contentType": "application/pdf",
            "size": 1001,
            "isInline": false,
            "contentBytes": "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA2MTIgNzkyXSAvUmVzb3VyY2VzIDw8IC9Gb250IDw8IC9GMSA1IDAgUiA+PiA+PiAvQ29udGVudHMgNCAwIFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA0NTcgPj4Kc3RyZWFtCkJUIC9GMSAxMiBUZiA3MiA3NDAgVGQgMTYgVEwKKEFDTUUgT2ZmaWNlIEZpdC1PdXRzIEx0ZCAgICAgICAgICAgIElOVk9JQ0UpIFRqClQqICgpIFRqClQqIChJbnZvaWNlIG5vOiAgSU5WLTIwNDUpIFRqClQqIChCaWxsIHRvOiAgICAgT2F0c3kgUHR5IEx0ZCkgVGoKVCogKElzc3VlIGRhdGU6ICAyMDI2LTA2LTIwKSBUagpUKiAoRHVlIGRhdGU6ICAgIDIwMjYtMDctMTUpIFRqClQqICgpIFRqClQqIChEZXNjcmlwdGlvbiAgICAgICAgICAgICAgICAgICAgICAgICBBbW91bnQpIFRqClQqIChRMyBib2FyZHJvb20gZml0LW91dCBcKGRlcG9zaXRcKSAgICAgICQ0LDIwMC4wMCBBVUQpIFRqClQqICgpIFRqClQqIChUb3RhbCBkdWU6ICAgJDQsMjAwLjAwIEFVRCkgVGoKVCogKFBsZWFzZSByZW1pdCBwYXltZW50IGJ5IHRoZSBkdWUgZGF0ZSBhbmQgY29uZmlybSB0aGUgaW5zdGFsbCBkYXRlLikgVGoKRVQKZW5kc3RyZWFtCmVuZG9iago1IDAgb2JqCjw8IC9UeXBlIC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGljYSA+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQxIDAwMDAwIG4gCjAwMDAwMDA3NDkgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA2IC9Sb290IDEgMCBSID4+CnN0YXJ0eHJlZgo4MTkKJSVFT0Y="
          }
        ]
      },
      "output": {
        "email_message_id": "AAMk596af063ab0746d69420db693dabbc3c",
        "sender": "alice@acme-fitouts.com",
        "overall_priority": "high",
        "tasks": [
          {
            "task_id": 1,
            "category": "Finance/Invoice",
            "summary": "Review and pay deposit invoice INV-2045 for $4,200.",
            "priority": "high",
            "due_date": "2026-07-15",
            "confidence": 0.88,
            "source": "both"
          },
          {
            "task_id": 2,
            "category": "Scheduling",
            "summary": "Book the layout call with ACME before the end of the week.",
            "priority": "high",
            "due_date": null,
            "confidence": 0.82,
            "source": "body"
          }
        ],
        "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
        "run_id": "20260624T015211Z-11133cac29",
        "logfire_url": null
      },
      "expected": {
        "description": "PDF attachment path: invoice payment plus follow-up scheduling.",
        "min_tasks": 2,
        "overall_priority_in": [
          "high",
          "urgent"
        ],
        "priorities_include": [
          "high"
        ],
        "summaries_include": [
          "invoice",
          "layout"
        ],
        "due_dates_include": [
          "2026-07-15"
        ],
        "attachment_names_include": [
          "invoice-INV-2045.pdf"
        ]
      },
      "checks": [
        {
          "name": "HTTP 200",
          "ok": true
        },
        {
          "name": "JSON response",
          "ok": true
        },
        {
          "name": "Task list present",
          "ok": true
        },
        {
          "name": "At least 2 task(s)",
          "ok": true
        },
        {
          "name": "Overall priority",
          "ok": true
        },
        {
          "name": "Task priority includes high",
          "ok": true
        },
        {
          "name": "Output mentions invoice",
          "ok": true
        },
        {
          "name": "Output mentions layout",
          "ok": true
        },
        {
          "name": "Due date mentions 2026-07-15",
          "ok": true
        },
        {
          "name": "Input includes attachment invoice-INV-2045.pdf",
          "ok": true
        }
      ],
      "status": "passed",
      "http_status": 200,
      "duration_ms": 33,
      "run_id": "20260624T015211Z-11133cac29",
      "logfire_url": null,
      "trace": [
        {
          "step": 1,
          "type": "attachment_conversion",
          "name": "01_invoice-INV-2045.md",
          "markdown": "ACME Office Fit-Outs Ltd            INVOICE\n\nInvoice no:  INV-2045\nBill to:     Oatsy Pty Ltd\nIssue date:  2026-06-20\nDue date:    2026-07-15\n\nDescription                         Amount\nQ3 boardroom fit-out (deposit)      $4,200.00 AUD\n\nTotal due:   $4,200.00 AUD\nPlease remit payment by the due date and confirm the install date."
        },
        {
          "step": 2,
          "type": "llm_call",
          "name": "01_call",
          "model": "claude-sonnet-4-6",
          "prompt": {
            "model": "claude-sonnet-4-6",
            "output_schema": "EmailTriageResult",
            "provider": "mock",
            "system_prompt": "You are an executive-assistant email triage agent. Extract actionable tasks from the email body and converted attachments. Return only schema-valid structured data.\n\nCategories:\n- Finance/Invoice: Payments, invoices, expenses, budgets, or approvals.\n- Scheduling: Meetings, calls, bookings, deadlines, or calendar coordination.\n- Travel: Flights, accommodation, transport, or trip logistics.\n- Approvals: Review, sign-off, authorization, or decision requests.\n- Admin/Office: Office operations, permits, facilities, supplies, or admin tasks.\n- FYI: Informational items where no action is required.\n\nPriorities:\n- urgent: Needs same-day action or has severe consequence if missed.\n- high: Important and time-bound, usually within days.\n- medium: Action is needed but not immediately critical.\n- low: Low consequence or flexible timing.\n- fyi: Information only, no action required.\n\nPrefer concise task summaries. If an item is informational only, mark it FYI.",
            "user_prompt": "Message ID: AAMk596af063ab0746d69420db693dabbc3c\nFrom: alice@acme-fitouts.com\nTo: sam.ea@oatsy.com\nImportance: High\nSubject: Q3 fit-out: pay deposit invoice + book layout call\n\nEmail body:\n\n Hi Sam,\nTwo things before end of week:\nPlease review and pay the attached deposit invoice (INV-2045, $4,200) by 15 July so ACME can lock in our install slot.\nCan you also book a 30-min call with their project lead next week to confirm the boardroom layout? Anytime Tue/Wed works for me.\nThis is fairly urgent \u2014 the slot is only held until Friday.\nThanks,\nAlice\n\nConverted attachments:\nAttachment: invoice-INV-2045.pdf\nACME Office Fit-Outs Ltd            INVOICE\n\nInvoice no:  INV-2045\nBill to:     Oatsy Pty Ltd\nIssue date:  2026-06-20\nDue date:    2026-07-15\n\nDescription                         Amount\nQ3 boardroom fit-out (deposit)      $4,200.00 AUD\n\nTotal due:   $4,200.00 AUD\nPlease remit payment by the due date and confirm the install date."
          },
          "response": {
            "duration_ms": 0,
            "model": "claude-sonnet-4-6",
            "provider": "mock",
            "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
            "response": {
              "mode": "mock",
              "output": {
                "email_message_id": "AAMk596af063ab0746d69420db693dabbc3c",
                "overall_priority": "high",
                "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
                "sender": "alice@acme-fitouts.com",
                "tasks": [
                  {
                    "category": "Finance/Invoice",
                    "confidence": 0.88,
                    "due_date": "2026-07-15",
                    "priority": "high",
                    "source": "both",
                    "summary": "Review and pay deposit invoice INV-2045 for $4,200.",
                    "task_id": 1
                  },
                  {
                    "category": "Scheduling",
                    "confidence": 0.82,
                    "due_date": null,
                    "priority": "high",
                    "source": "body",
                    "summary": "Book the layout call with ACME before the end of the week.",
                    "task_id": 2
                  }
                ]
              },
              "usage": {
                "input_chars": 939
              }
            },
            "tool_calls": [
              {
                "attachments": [
                  "invoice-INV-2045.pdf"
                ],
                "count": 1,
                "name": "convert_attachment_to_markdown"
              }
            ],
            "usage": {
              "input_chars": 939
            }
          },
          "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
          "tool_calls": [
            {
              "attachments": [
                "invoice-INV-2045.pdf"
              ],
              "count": 1,
              "name": "convert_attachment_to_markdown"
            }
          ],
          "usage": {
            "input_chars": 939
          },
          "duration_ms": 0
        },
        {
          "step": 3,
          "type": "run_manifest",
          "name": "run.json",
          "json": {
            "config": {
              "auth": "X-API-Key",
              "categories": [
                {
                  "definition": "Payments, invoices, expenses, budgets, or approvals.",
                  "label": "Finance/Invoice"
                },
                {
                  "definition": "Meetings, calls, bookings, deadlines, or calendar coordination.",
                  "label": "Scheduling"
                },
                {
                  "definition": "Flights, accommodation, transport, or trip logistics.",
                  "label": "Travel"
                },
                {
                  "definition": "Review, sign-off, authorization, or decision requests.",
                  "label": "Approvals"
                },
                {
                  "definition": "Office operations, permits, facilities, supplies, or admin tasks.",
                  "label": "Admin/Office"
                },
                {
                  "definition": "Informational items where no action is required.",
                  "label": "FYI"
                }
              ],
              "llm_model": "claude-sonnet-4-6",
              "llm_provider": "mock",
              "priorities": [
                {
                  "definition": "Needs same-day action or has severe consequence if missed.",
                  "label": "urgent"
                },
                {
                  "definition": "Important and time-bound, usually within days.",
                  "label": "high"
                },
                {
                  "definition": "Action is needed but not immediately critical.",
                  "label": "medium"
                },
                {
                  "definition": "Low consequence or flexible timing.",
                  "label": "low"
                },
                {
                  "definition": "Information only, no action required.",
                  "label": "fyi"
                }
              ],
              "region": "Australia East"
            },
            "duration_ms": 24,
            "error": null,
            "run_id": "20260624T015211Z-11133cac29",
            "started_at": "2026-06-24T01:52:11.475435+00:00",
            "status": "completed"
          }
        }
      ],
      "error": null,
      "raw_response": null
    },
    {
      "id": "02-expenses-xlsx",
      "title": "May expenses for approval (sign-off Thursday)",
      "request": {
        "id": "AAMkf1cc216067a44030b0742b30ae823f37",
        "internetMessageId": "<03fa363defe64f2c8ecdfce847b91463@contoso.com>",
        "conversationId": "0cf43e836c8745cbb473867b0576c5cb",
        "subject": "May expenses for approval (sign-off Thursday)",
        "from": "alice@acme-fitouts.com",
        "to": "sam.ea@oatsy.com",
        "cc": "",
        "importance": "Normal",
        "hasAttachments": true,
        "receivedDateTime": "2026-06-24T00:54:06Z",
        "bodyPreview": "<html> <body>\n <p>Hi Sam, </p>\n <p>Attached are the  <b>May expenses </b>. Please  <b>review and approve anything over $500 </b>, and flag anything that looks off &mdash; finance needs sign-off by  <b>Thursday </b>. </p>\n <p>The ACME line is the fit-out d",
        "body": "<html><body>\n<p>Hi Sam,</p>\n<p>Attached are the <b>May expenses</b>. Please <b>review and approve anything over $500</b>, and flag anything that looks off &mdash; finance needs sign-off by <b>Thursday</b>.</p>\n<p>The ACME line is the fit-out deposit; that one ties to invoice INV-2045 if you're cross-checking.</p>\n<p>Thanks,<br>Alice</p>\n</body></html>\n",
        "attachments": [
          {
            "@odata.type": "#Microsoft.OutlookServices.FileAttachment",
            "id": "71369c1aa78845fea1c55737c05c8f2e",
            "name": "may-expenses.xlsx",
            "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "size": 5220,
            "isInline": false,
            "contentBytes": "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"
          }
        ]
      },
      "output": {
        "email_message_id": "AAMkf1cc216067a44030b0742b30ae823f37",
        "sender": "alice@acme-fitouts.com",
        "overall_priority": "medium",
        "tasks": [
          {
            "task_id": 1,
            "category": "Approvals",
            "summary": "Review and approve May expenses over $500 by Thursday, flagging anything unusual for finance sign-off.",
            "priority": "medium",
            "due_date": null,
            "confidence": 0.86,
            "source": "both"
          }
        ],
        "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
        "run_id": "20260624T015211Z-ae7b40749b",
        "logfire_url": null
      },
      "expected": {
        "description": "Spreadsheet attachment path: review May expenses and approve lines over $500.",
        "min_tasks": 1,
        "overall_priority_in": [
          "medium",
          "high"
        ],
        "summaries_include": [
          "expenses",
          "approve",
          "$500"
        ],
        "due_dates_include": [
          "Thursday"
        ],
        "attachment_names_include": [
          "may-expenses.xlsx"
        ]
      },
      "checks": [
        {
          "name": "HTTP 200",
          "ok": true
        },
        {
          "name": "JSON response",
          "ok": true
        },
        {
          "name": "Task list present",
          "ok": true
        },
        {
          "name": "At least 1 task(s)",
          "ok": true
        },
        {
          "name": "Overall priority",
          "ok": true
        },
        {
          "name": "Output mentions expenses",
          "ok": true
        },
        {
          "name": "Output mentions approve",
          "ok": true
        },
        {
          "name": "Output mentions $500",
          "ok": true
        },
        {
          "name": "Due date mentions Thursday",
          "ok": true
        },
        {
          "name": "Input includes attachment may-expenses.xlsx",
          "ok": true
        }
      ],
      "status": "passed",
      "http_status": 200,
      "duration_ms": 31,
      "run_id": "20260624T015211Z-ae7b40749b",
      "logfire_url": null,
      "trace": [
        {
          "step": 1,
          "type": "attachment_conversion",
          "name": "01_may-expenses.md",
          "markdown": "## May Expenses\n| Date | Vendor | Category | Amount (AUD) | Notes |\n| --- | --- | --- | --- | --- |\n| 2026-05-03 | Qantas | Travel | 842.5 | Flight SYD-MEL client visit |\n| 2026-05-09 | The Grounds | Meals | 96.0 | Client lunch |\n| 2026-05-14 | Officeworks | Supplies | 213.4 | NaN |\n| 2026-05-21 | Hilton Brisbane | Accom | 640.0 | 2 nights, fit-out site |\n| 2026-05-28 | Uber | Travel | 58.2 | NaN |\n| 2026-05-30 | ACME Fit-Outs | Deposit | 4200.0 | See separate invoice INV-2045 |"
        },
        {
          "step": 2,
          "type": "llm_call",
          "name": "01_call",
          "model": "claude-sonnet-4-6",
          "prompt": {
            "model": "claude-sonnet-4-6",
            "output_schema": "EmailTriageResult",
            "provider": "mock",
            "system_prompt": "You are an executive-assistant email triage agent. Extract actionable tasks from the email body and converted attachments. Return only schema-valid structured data.\n\nCategories:\n- Finance/Invoice: Payments, invoices, expenses, budgets, or approvals.\n- Scheduling: Meetings, calls, bookings, deadlines, or calendar coordination.\n- Travel: Flights, accommodation, transport, or trip logistics.\n- Approvals: Review, sign-off, authorization, or decision requests.\n- Admin/Office: Office operations, permits, facilities, supplies, or admin tasks.\n- FYI: Informational items where no action is required.\n\nPriorities:\n- urgent: Needs same-day action or has severe consequence if missed.\n- high: Important and time-bound, usually within days.\n- medium: Action is needed but not immediately critical.\n- low: Low consequence or flexible timing.\n- fyi: Information only, no action required.\n\nPrefer concise task summaries. If an item is informational only, mark it FYI.",
            "user_prompt": "Message ID: AAMkf1cc216067a44030b0742b30ae823f37\nFrom: alice@acme-fitouts.com\nTo: sam.ea@oatsy.com\nImportance: Normal\nSubject: May expenses for approval (sign-off Thursday)\n\nEmail body:\n\n Hi Sam,\nAttached are the May expenses . Please review and approve anything over $500 , and flag anything that looks off \u2014 finance needs sign-off by Thursday .\nThe ACME line is the fit-out deposit; that one ties to invoice INV-2045 if you're cross-checking.\nThanks,\nAlice\n\nConverted attachments:\nAttachment: may-expenses.xlsx\n## May Expenses\n| Date | Vendor | Category | Amount (AUD) | Notes |\n| --- | --- | --- | --- | --- |\n| 2026-05-03 | Qantas | Travel | 842.5 | Flight SYD-MEL client visit |\n| 2026-05-09 | The Grounds | Meals | 96.0 | Client lunch |\n| 2026-05-14 | Officeworks | Supplies | 213.4 | NaN |\n| 2026-05-21 | Hilton Brisbane | Accom | 640.0 | 2 nights, fit-out site |\n| 2026-05-28 | Uber | Travel | 58.2 | NaN |\n| 2026-05-30 | ACME Fit-Outs | Deposit | 4200.0 | See separate invoice INV-2045 |"
          },
          "response": {
            "duration_ms": 0,
            "model": "claude-sonnet-4-6",
            "provider": "mock",
            "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
            "response": {
              "mode": "mock",
              "output": {
                "email_message_id": "AAMkf1cc216067a44030b0742b30ae823f37",
                "overall_priority": "medium",
                "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
                "sender": "alice@acme-fitouts.com",
                "tasks": [
                  {
                    "category": "Approvals",
                    "confidence": 0.86,
                    "due_date": null,
                    "priority": "medium",
                    "source": "both",
                    "summary": "Review and approve May expenses over $500 by Thursday, flagging anything unusual for finance sign-off.",
                    "task_id": 1
                  }
                ]
              },
              "usage": {
                "input_chars": 996
              }
            },
            "tool_calls": [
              {
                "attachments": [
                  "may-expenses.xlsx"
                ],
                "count": 1,
                "name": "convert_attachment_to_markdown"
              }
            ],
            "usage": {
              "input_chars": 996
            }
          },
          "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
          "tool_calls": [
            {
              "attachments": [
                "may-expenses.xlsx"
              ],
              "count": 1,
              "name": "convert_attachment_to_markdown"
            }
          ],
          "usage": {
            "input_chars": 996
          },
          "duration_ms": 0
        },
        {
          "step": 3,
          "type": "run_manifest",
          "name": "run.json",
          "json": {
            "config": {
              "auth": "X-API-Key",
              "categories": [
                {
                  "definition": "Payments, invoices, expenses, budgets, or approvals.",
                  "label": "Finance/Invoice"
                },
                {
                  "definition": "Meetings, calls, bookings, deadlines, or calendar coordination.",
                  "label": "Scheduling"
                },
                {
                  "definition": "Flights, accommodation, transport, or trip logistics.",
                  "label": "Travel"
                },
                {
                  "definition": "Review, sign-off, authorization, or decision requests.",
                  "label": "Approvals"
                },
                {
                  "definition": "Office operations, permits, facilities, supplies, or admin tasks.",
                  "label": "Admin/Office"
                },
                {
                  "definition": "Informational items where no action is required.",
                  "label": "FYI"
                }
              ],
              "llm_model": "claude-sonnet-4-6",
              "llm_provider": "mock",
              "priorities": [
                {
                  "definition": "Needs same-day action or has severe consequence if missed.",
                  "label": "urgent"
                },
                {
                  "definition": "Important and time-bound, usually within days.",
                  "label": "high"
                },
                {
                  "definition": "Action is needed but not immediately critical.",
                  "label": "medium"
                },
                {
                  "definition": "Low consequence or flexible timing.",
                  "label": "low"
                },
                {
                  "definition": "Information only, no action required.",
                  "label": "fyi"
                }
              ],
              "region": "Australia East"
            },
            "duration_ms": 27,
            "error": null,
            "run_id": "20260624T015211Z-ae7b40749b",
            "started_at": "2026-06-24T01:52:11.504019+00:00",
            "status": "completed"
          }
        }
      ],
      "error": null,
      "raw_response": null
    },
    {
      "id": "03-body-only",
      "title": "FYI + please renew the parking permit by 30 June",
      "request": {
        "id": "AAMk674cc5f5ca5e45ee9553ad07cf3bb19f",
        "internetMessageId": "<0e28e7f753814ba4884ee35c22ab30bb@contoso.com>",
        "conversationId": "c4a0dbd3823d419ea1edeca7ff465ab5",
        "subject": "FYI + please renew the parking permit by 30 June",
        "from": "alice@acme-fitouts.com",
        "to": "sam.ea@oatsy.com",
        "cc": "",
        "importance": "Normal",
        "hasAttachments": false,
        "receivedDateTime": "2026-06-24T00:54:06Z",
        "bodyPreview": "<html> <body>\n <p>Hi Sam, </p>\n <p>Couple of bits: </p>\n <ul>\n   <li>FYI &mdash; the new office plants were delivered this morning, all good, nothing needed from you. </li>\n   <li>The building  <b>parking permit expires 30 June </b>. Can you renew it befo",
        "body": "<html><body>\n<p>Hi Sam,</p>\n<p>Couple of bits:</p>\n<ul>\n  <li>FYI &mdash; the new office plants were delivered this morning, all good, nothing needed from you.</li>\n  <li>The building <b>parking permit expires 30 June</b>. Can you renew it before then? We can't afford to lose the two bays.</li>\n  <li>No rush, but sometime this month it'd be good to tidy the shared stationery cupboard.</li>\n</ul>\n<p>Cheers,<br>Alice</p>\n</body></html>\n",
        "attachments": []
      },
      "output": {
        "email_message_id": "AAMk674cc5f5ca5e45ee9553ad07cf3bb19f",
        "sender": "alice@acme-fitouts.com",
        "overall_priority": "medium",
        "tasks": [
          {
            "task_id": 1,
            "category": "Admin/Office",
            "summary": "Renew the building parking permit before it expires on 30 June.",
            "priority": "medium",
            "due_date": "2026-06-30",
            "confidence": 0.87,
            "source": "body"
          },
          {
            "task_id": 2,
            "category": "FYI",
            "summary": "New office plants were delivered; no action is required.",
            "priority": "fyi",
            "due_date": null,
            "confidence": 0.73,
            "source": "body"
          }
        ],
        "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
        "run_id": "20260624T015211Z-a17f38503b",
        "logfire_url": null
      },
      "expected": {
        "description": "Body-only path: extract a real task and keep FYI content low priority.",
        "min_tasks": 1,
        "overall_priority_in": [
          "low",
          "medium",
          "fyi"
        ],
        "summaries_include": [
          "parking permit",
          "30 June"
        ],
        "priorities_include": [
          "fyi"
        ],
        "due_dates_include": [
          "2026-06-30"
        ]
      },
      "checks": [
        {
          "name": "HTTP 200",
          "ok": true
        },
        {
          "name": "JSON response",
          "ok": true
        },
        {
          "name": "Task list present",
          "ok": true
        },
        {
          "name": "At least 1 task(s)",
          "ok": true
        },
        {
          "name": "Overall priority",
          "ok": true
        },
        {
          "name": "Task priority includes fyi",
          "ok": true
        },
        {
          "name": "Output mentions parking permit",
          "ok": true
        },
        {
          "name": "Output mentions 30 June",
          "ok": true
        },
        {
          "name": "Due date mentions 2026-06-30",
          "ok": true
        }
      ],
      "status": "passed",
      "http_status": 200,
      "duration_ms": 4,
      "run_id": "20260624T015211Z-a17f38503b",
      "logfire_url": null,
      "trace": [
        {
          "step": 1,
          "type": "llm_call",
          "name": "01_call",
          "model": "claude-sonnet-4-6",
          "prompt": {
            "model": "claude-sonnet-4-6",
            "output_schema": "EmailTriageResult",
            "provider": "mock",
            "system_prompt": "You are an executive-assistant email triage agent. Extract actionable tasks from the email body and converted attachments. Return only schema-valid structured data.\n\nCategories:\n- Finance/Invoice: Payments, invoices, expenses, budgets, or approvals.\n- Scheduling: Meetings, calls, bookings, deadlines, or calendar coordination.\n- Travel: Flights, accommodation, transport, or trip logistics.\n- Approvals: Review, sign-off, authorization, or decision requests.\n- Admin/Office: Office operations, permits, facilities, supplies, or admin tasks.\n- FYI: Informational items where no action is required.\n\nPriorities:\n- urgent: Needs same-day action or has severe consequence if missed.\n- high: Important and time-bound, usually within days.\n- medium: Action is needed but not immediately critical.\n- low: Low consequence or flexible timing.\n- fyi: Information only, no action required.\n\nPrefer concise task summaries. If an item is informational only, mark it FYI.",
            "user_prompt": "Message ID: AAMk674cc5f5ca5e45ee9553ad07cf3bb19f\nFrom: alice@acme-fitouts.com\nTo: sam.ea@oatsy.com\nImportance: Normal\nSubject: FYI + please renew the parking permit by 30 June\n\nEmail body:\n\n Hi Sam,\nCouple of bits:\nFYI \u2014 the new office plants were delivered this morning, all good, nothing needed from you.\nThe building parking permit expires 30 June . Can you renew it before then? We can't afford to lose the two bays.\nNo rush, but sometime this month it'd be good to tidy the shared stationery cupboard.\nCheers,\nAlice\n\nConverted attachments:\n(none)"
          },
          "response": {
            "duration_ms": 0,
            "model": "claude-sonnet-4-6",
            "provider": "mock",
            "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
            "response": {
              "mode": "mock",
              "output": {
                "email_message_id": "AAMk674cc5f5ca5e45ee9553ad07cf3bb19f",
                "overall_priority": "medium",
                "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
                "sender": "alice@acme-fitouts.com",
                "tasks": [
                  {
                    "category": "Admin/Office",
                    "confidence": 0.87,
                    "due_date": "2026-06-30",
                    "priority": "medium",
                    "source": "body",
                    "summary": "Renew the building parking permit before it expires on 30 June.",
                    "task_id": 1
                  },
                  {
                    "category": "FYI",
                    "confidence": 0.73,
                    "due_date": null,
                    "priority": "fyi",
                    "source": "body",
                    "summary": "New office plants were delivered; no action is required.",
                    "task_id": 2
                  }
                ]
              },
              "usage": {
                "input_chars": 551
              }
            },
            "tool_calls": [
              {
                "attachments": [],
                "count": 0,
                "name": "convert_attachment_to_markdown"
              }
            ],
            "usage": {
              "input_chars": 551
            }
          },
          "reasoning": "Mock triage used deterministic fixture-aware rules over the subject, body, and converted attachment text so local evals can run without live LLM credentials.",
          "tool_calls": [
            {
              "attachments": [],
              "count": 0,
              "name": "convert_attachment_to_markdown"
            }
          ],
          "usage": {
            "input_chars": 551
          },
          "duration_ms": 0
        },
        {
          "step": 2,
          "type": "run_manifest",
          "name": "run.json",
          "json": {
            "config": {
              "auth": "X-API-Key",
              "categories": [
                {
                  "definition": "Payments, invoices, expenses, budgets, or approvals.",
                  "label": "Finance/Invoice"
                },
                {
                  "definition": "Meetings, calls, bookings, deadlines, or calendar coordination.",
                  "label": "Scheduling"
                },
                {
                  "definition": "Flights, accommodation, transport, or trip logistics.",
                  "label": "Travel"
                },
                {
                  "definition": "Review, sign-off, authorization, or decision requests.",
                  "label": "Approvals"
                },
                {
                  "definition": "Office operations, permits, facilities, supplies, or admin tasks.",
                  "label": "Admin/Office"
                },
                {
                  "definition": "Informational items where no action is required.",
                  "label": "FYI"
                }
              ],
              "llm_model": "claude-sonnet-4-6",
              "llm_provider": "mock",
              "priorities": [
                {
                  "definition": "Needs same-day action or has severe consequence if missed.",
                  "label": "urgent"
                },
                {
                  "definition": "Important and time-bound, usually within days.",
                  "label": "high"
                },
                {
                  "definition": "Action is needed but not immediately critical.",
                  "label": "medium"
                },
                {
                  "definition": "Low consequence or flexible timing.",
                  "label": "low"
                },
                {
                  "definition": "Information only, no action required.",
                  "label": "fyi"
                }
              ],
              "region": "Australia East"
            },
            "duration_ms": 1,
            "error": null,
            "run_id": "20260624T015211Z-a17f38503b",
            "started_at": "2026-06-24T01:52:11.535812+00:00",
            "status": "completed"
          }
        }
      ],
      "error": null,
      "raw_response": null
    }
  ]
};
