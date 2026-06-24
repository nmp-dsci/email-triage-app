# S1 — App Init: Email → Structured, Prioritised Tasks (v1 Docker/FastAPI)

**Status:** Plan (not yet implemented)
**Date:** 2026-06-24
**Owner:** Nathan
**Predecessor:** [s0_init.md](./s0_init.md) (raw brief)
**Source brief:** [docs/brief-init.md](../docs/brief-init.md)

---

## 1. Goal

Stand up **version 1** of a Dockerised FastAPI service that:

1. Receives a `POST` from **Power Automate** carrying an Outlook email (headers, body, attachments).
2. Runs an **LLM agent (Claude, via Pydantic AI) with tools** that:
   - converts attachments (PDF, docx, xlsx, etc.) to Markdown with **MarkItDown**,
   - reads the email + converted attachments,
   - extracts a **list of prioritised tasks** as a **configurable Pydantic model**.
3. Returns that task list as JSON.
4. **Persists every request and every interim step** (raw payload, each converted document, every LLM call's prompt/response/reasoning) to a backend store for evaluation.
5. Emits full **observability/tracing** so every agent invocation can be stepped through.
6. Ships as a **Docker container** deployable on the **Azure** stack.

v1 is a **demo/skeleton that runs end-to-end** on pseudo data. It is intentionally simple but structured so the data model, prompt, and pipeline can evolve.

---

## 2. Key decisions & recommendations

| Concern | Decision | Why |
|---|---|---|
| Web framework | **FastAPI** + Uvicorn | Async, Pydantic-native, OpenAPI docs for free, standard for this shape. |
| Data models | **Pydantic v2** + **pydantic-settings** | Brief asks for a *configurable* structured model; Pydantic is the validation layer and Pydantic AI's output type. |
| Agent framework | **Pydantic AI** | Native structured output into a Pydantic model, first-class tool support, built-in Logfire instrumentation, model-agnostic. Far less glue than the raw SDK for "LLM + tools → typed object". |
| LLM | **Claude `claude-sonnet-4-6`** (default, configurable via env) | Chosen default: strong quality/cost/speed balance (~$3/$15 per 1M). Model id is a setting, so we can raise to `claude-opus-4-8` for hardest extraction or drop to `claude-haiku-4-5` for cost/volume without code change. |
| LLM provider | **First-party Anthropic API** (default) **with a config seam to Azure AI Foundry** | An `LLM_PROVIDER` setting selects the Claude backend. `foundry` routes Claude through **Azure AI Foundry**, keeping inference inside the Azure tenant (Australia East). Built in from P0 so moving the LLM to Foundry later is a config switch, **not** a rewrite — see §9 (seam) and §13 / **F1** (future step). |
| Attachment → Markdown | **Microsoft MarkItDown** | Handles PDF, Office docs, images, HTML → Markdown; exactly the brief's ask. Runs as an agent tool. |
| **Tracking / observability** | **Pydantic Logfire** (recommended over MLflow) — see §8 | MLflow is built for ML *experiment/model-registry* tracking. For an LLM agent we want per-call traces: prompts, tool calls, token usage, latency, reasoning — stepped through one invocation at a time. Logfire is built by the Pydantic team, instruments Pydantic AI + FastAPI in ~2 lines, is OpenTelemetry-based (so it also exports to Azure Monitor/any OTLP backend), and gives exactly the "step through every LLM call" UX the brief asks for. We **also** persist a self-contained artifact bundle per request to disk (§7) so evaluation does not depend on the tracing vendor. |
| Deployment | **Docker** image → **Azure Container Apps** for v1 | Container Apps is the lowest-friction Azure target for a single stateless HTTP container (scale-to-zero, managed ingress, easy secrets). AKS is overkill for v1; revisit if we need it. |
| Artifact storage (v1) | **Local filesystem** under a mounted volume | Simplest thing that works; abstracted behind a `Storage` interface so we can swap to **Azure Blob Storage** in v2 without touching the agent. |

> Open items to confirm with the client are listed in §12. None block starting implementation — defaults above are chosen so work can begin.

---

## 3. High-level architecture

```
 Outlook ──▶ Power Automate ──HTTP POST──▶  FastAPI service (this container)
 (mailbox)   (flow: on new mail)            │
                                            ├─ 1. Validate inbound payload  (Pydantic: InboundEmail)
                                            ├─ 2. Open a request "run" (run_id, run dir, Logfire span)
                                            ├─ 3. Persist raw payload + attachments
                                            ├─ 4. Agent (Pydantic AI + Claude)
                                            │      └─ tool: convert_attachment_to_markdown (MarkItDown)
                                            │      └─ tool: (future) lookup_history / classify
                                            │      └─ structured output ──▶ EmailTriageResult
                                            ├─ 5. Persist every interim artifact + LLM reasoning
                                            └─ 6. Return JSON  ◀── Power Automate (calendar / downstream)

 Cross-cutting: Logfire tracing on FastAPI + Pydantic AI + MarkItDown spans
                → console (dev) and Logfire/OTLP backend (Azure)
```

---

## 4. Tech stack & versions (pin in `pyproject.toml`)

Python **3.12** (3.13/3.14 fine; pin 3.12 in Docker for broad wheel availability). Managed with **uv**.

| Package | Target version | Role |
|---|---|---|
| `fastapi` | `~=0.138` | HTTP API |
| `uvicorn[standard]` | `~=0.49` | ASGI server |
| `pydantic` | `~=2.13` | Models / validation |
| `pydantic-settings` | `~=2.14` | Env-driven config |
| `pydantic-ai` | `~=2.0` | Agent (LLM + tools + structured output) |
| `anthropic` | `~=0.78`+ | Claude SDK (Pydantic AI dependency / direct fallback) |
| `markitdown[all]` | `~=0.1.6` | Attachment → Markdown |
| `logfire` | `~=4.37` | Tracing/observability (FastAPI + Pydantic AI + HTTPX instrumentation) |
| `python-multipart` | latest | (only if we accept multipart instead of JSON-base64) |
| dev: `pytest`, `pytest-asyncio`, `ruff`, `mypy` | latest | Test/lint/typecheck |

**LLM provider seam (Anthropic API ↔ Azure AI Foundry).** The default backend is the first-party Anthropic API. The same `anthropic` package already ships the Azure Foundry client (`AnthropicFoundry` / `AsyncAnthropicFoundry`), so Claude-via-Foundry needs **no extra dependency** — only config. A single `LLM_PROVIDER` setting (`anthropic` default | `foundry`) selects which client Pydantic AI is given (built in §9). Settings involved:

| Setting | Used when | Notes |
|---|---|---|
| `LLM_PROVIDER` | always | `anthropic` (default) or `foundry`. |
| `LLM_MODEL` | always | e.g. `claude-sonnet-4-6`. |
| `ANTHROPIC_API_KEY` | `anthropic` | First-party key. |
| `AZURE_FOUNDRY_RESOURCE` / `AZURE_FOUNDRY_BASE_URL` | `foundry` | Foundry endpoint (`…services.ai.azure.com/anthropic/v1`). |
| `AZURE_FOUNDRY_API_KEY` | `foundry` | Foundry key (or Entra ID — confirm in F1). |

Building this seam in P0 is what makes the later move (§13 / F1) a config flip rather than a refactor.

---

## 5. Project structure

Legend: **✅ exists today** · **▫ planned (not yet created)**. The `app/` tree is
created in phase P0 (§13); `tests/data/` already holds the validated Power
Automate fixtures and generator.

```
email-triage-app/
├─ ai_plan/                          # ✅ planning docs
│  ├─ s0_init.md                     # ✅ raw brief
│  └─ s1_app_init.md                 # ✅ this plan
├─ docs/
│  └─ brief-init.md                  # ✅ source brief (chat transcript)
├─ tests/
│  ├─ data/                          # ✅ imitation Power Automate fixtures + generator
│  │  ├─ README.md                   # ✅ fixture shape, flow mapping, curl usage
│  │  ├─ make_payload.py             # ✅ build a V3 payload from any email + files
│  │  ├─ sample_email_v3.json        # ✅ fixture: email + PDF attachment
│  │  ├─ sample_email_xlsx.json      # ✅ fixture: email + .xlsx attachment
│  │  ├─ sample_email_no_attachment.json  # ✅ fixture: body-only (task + FYI)
│  │  ├─ invoice-INV-2045.pdf        # ✅ source attachment (verified via MarkItDown)
│  │  ├─ may-expenses.xlsx           # ✅ source attachment (verified via MarkItDown)
│  │  └─ body*.html                  # ✅ email bodies used to build the fixtures
│  ├─ test_models.py                 # ▫ contract/validation tests
│  ├─ test_conversion.py             # ▫ MarkItDown wrapper tests
│  └─ test_triage_endpoint.py        # ▫ endpoint test w/ Pydantic AI TestModel (no live API)
├─ app/                              # ▫ the service (created in P0)
│  ├─ __init__.py
│  ├─ main.py                        # ▫ FastAPI app, Logfire init, router wiring
│  ├─ config.py                      # ▫ Settings (pydantic-settings): LLM provider/model, keys, vocab, paths
│  ├─ api/
│  │  ├─ routes_triage.py            # ▫ POST /triage
│  │  └─ routes_health.py            # ▫ GET /health, GET /version, GET /runs/{id} (dev)
│  ├─ models/
│  │  ├─ inbound.py                  # ▫ InboundEmail, InboundAttachment (§6.1)
│  │  └─ triage.py                   # ▫ TaskItem, EmailTriageResult — CONFIGURABLE output (§6.2)
│  ├─ agent/
│  │  ├─ triage_agent.py             # ▫ Pydantic AI Agent + system prompt builder
│  │  ├─ model.py                    # ▫ build_model(): provider seam (Anthropic API ↔ Azure Foundry)
│  │  └─ tools.py                    # ▫ convert_attachment_to_markdown, (future) lookup_history
│  ├─ services/
│  │  ├─ conversion.py               # ▫ MarkItDown wrapper
│  │  └─ storage.py                  # ▫ Storage interface + LocalFsStorage (v2: AzureBlobStorage)
│  └─ runlog/
│     └─ run.py                      # ▫ RunContext: run_id, run dir, artifact writers (§7)
├─ runs/                             # ▫ per-request artifact bundles (gitignored; mounted volume)
├─ evals/                            # ▫ eval suite — "run & review", Power-Automate-style (§15)
│  ├─ cases/                         # ▫ one folder per eval (one email = one run)
│  │  └─ <NN-name>/
│  │     ├─ request.json             # ▫ a Power Automate payload (via tests/data/make_payload.py)
│  │     └─ expected.json            # ▫ optional assertions (min tasks, categories, priorities, dates)
│  ├─ run_evals.py                   # ▫ POST every case to the live API → write dashboard/data/evals.json
│  └─ README.md                      # ▫ how to add a case
├─ dashboard/                        # ▫ static eval + client walkthrough UI (§15)
│  ├─ test-evaluation.html           # ▫ WhatsApp-style: pinned Methodology + one entry per eval email
│  ├─ assets/                        # ▫ app.js + styles.css (renders sidebar + request/output/trace)
│  ├─ methodology/                   # ▫ solution-diagram.svg + narrative (categories/config surfaced)
│  └─ data/evals.json                # ▫ GENERATED by evals/run_evals.py (cases + outputs + trace + config)
├─ Dockerfile                        # ▫ multi-stage, uv-based (§11)
├─ docker-compose.yml                # ▫ local: app + mounted ./runs
├─ pyproject.toml                    # ▫ deps pinned per §4 (uv)
├─ .env.example                      # ▫ LLM_PROVIDER, LLM_MODEL, ANTHROPIC_API_KEY, AZURE_FOUNDRY_*, LOGFIRE_TOKEN, TRIAGE_API_KEY, paths
├─ .gitignore                        # ▫ runs/, .env, __pycache__, .venv
└─ README.md                         # ▫ run/build/deploy instructions
```

---

## 6. Data contracts

### 6.1 Inbound (Power Automate → us)

Power Automate's "When a new email arrives (V3)" (Office 365 Outlook connector) exposes camelCase fields; with *Include Attachments* = Yes each attachment carries base64 `contentBytes`. We accept the native trigger shape so the flow can map dynamic content ~1:1 — `InboundEmail` uses aliases (`populate_by_name=True`) so both the connector keys and our snake_case names work. A validated working fixture lives in `tests/data/sample_email_v3.json` (built by `tests/data/make_payload.py`).

```python
# app/models/inbound.py
class InboundAttachment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    content_type: str | None = Field(None, alias="contentType")
    content_bytes: str = Field(alias="contentBytes")   # base64
    size: int | None = None
    is_inline: bool = Field(False, alias="isInline")

class InboundEmail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message_id: str | None = Field(None, alias="id")
    internet_message_id: str | None = Field(None, alias="internetMessageId")
    conversation_id: str | None = Field(None, alias="conversationId")
    subject: str = ""
    sender: str = Field("", alias="from")              # connector emits a plain string
    to: str = ""                                       # semicolon-separated if multiple
    cc: str = ""
    importance: Literal["Low", "Normal", "High"] = "Normal"
    received_at: datetime | None = Field(None, alias="receivedDateTime")
    body_preview: str = Field("", alias="bodyPreview")
    body: str = ""                                     # HTML
    has_attachments: bool = Field(False, alias="hasAttachments")
    attachments: list[InboundAttachment] = []
```

Note: the Microsoft *Graph* form nests sender/recipients as `{"emailAddress": {"address": ...}}` and body as `{"contentType", "content"}`; if a future flow posts that instead, add a small `@model_validator(mode="before")` to flatten it. The exact production field set is confirmed once we capture a real flow payload (§12, item 1).

### 6.2 Output — the configurable triage model

The brief's example `[{email, taskid, category, summary, priority}]` is the starting point; we make it a proper, **configurable** Pydantic model. "Configurable" = the enum sets (categories, priorities) and field set are defined in one place (and overridable via config/JSON) so they can evolve without code churn.

```python
# app/models/triage.py
class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    fyi = "fyi"

class TaskItem(BaseModel):
    task_id: int                       # 1-based, per email
    category: str                      # constrained by config-driven vocab
    summary: str = Field(description="One-line summary of the task")
    priority: Priority
    due_date: date | None = None       # extracted if present
    confidence: float | None = None    # 0..1, model's self-rated confidence
    source: Literal["body", "attachment", "both"] = "body"

class EmailTriageResult(BaseModel):
    email_message_id: str | None = None
    sender: str | None = None
    overall_priority: Priority
    tasks: list[TaskItem]
    reasoning: str = Field(description="Why these tasks/priorities were chosen")
```

**Configurability mechanism (v1):** category vocabulary + priority labels live in `config.py` / an env-pointed JSON file; the system prompt and (optionally) a dynamic JSON-schema constraint are built from them at startup. Each category and priority carries a human-readable **definition**, not just a label — this single source feeds both the system prompt *and* the dashboard's Methodology panel (§15), so what the client sees always matches what the model is told. v2 can promote this to a small admin endpoint. The API response is `EmailTriageResult` (a superset of the brief's shape — the flat `[{email, taskid, ...}]` list is trivially derivable and can be offered as an alternate response shape if Power Automate prefers it).

---

## 7. Per-request artifact persistence (for evaluation)

Every request gets a `run_id` (UUID + timestamp) and a directory:

```
runs/2026-06-24/<run_id>/
├─ 00_request.json            # raw inbound payload (redacted secrets)
├─ attachments/
│  ├─ 01_quote.pdf            # decoded original
│  └─ 01_quote.md             # MarkItDown output
├─ llm/
│  ├─ 01_call.json            # model, messages, params
│  ├─ 01_response.json        # raw response, tool calls, usage, reasoning/thinking
│  └─ ...                     # one pair per LLM call in the agent loop
├─ result.json               # final EmailTriageResult
└─ run.json                  # manifest: timings, model, token usage, status, error
```

- Written through a `Storage` interface (`LocalFsStorage` now; `AzureBlobStorage` later — same method signatures).
- This is **independent of the tracing backend**, so evaluation/replay works even offline. The `runs/` tree is the eval dataset's raw material.
- Secrets (API keys) never written; PII handling flagged in §12.

---

## 8. Tracking / observability — why Logfire over MLflow

The brief asks: *"a good tracking app ... MLFlow?"* and *"step through every time this agent is invoked to inspect all steps."*

- **MLflow** excels at ML *experiment tracking* (params/metrics/artifacts across training runs) and *model registry*. It now has GenAI tracing, but it's a heavier fit for "inspect every prompt/tool-call of a live agent."
- **Logfire** (Pydantic team, OpenTelemetry under the hood) is purpose-built for this: one call instruments **FastAPI**, **Pydantic AI**, and **HTTPX**, capturing each request as a trace and each LLM/tool call as a nested span with prompts, responses, token usage, latency, and reasoning. That *is* the "step through every invocation" experience.

```python
# app/main.py (sketch)
import logfire
logfire.configure(service_name="ea-email-triage")   # token via env in Azure
logfire.instrument_fastapi(app)
logfire.instrument_pydantic_ai()
logfire.instrument_httpx()
```

- Because it's OTLP-based, on Azure it can export to **Azure Monitor / Application Insights** in addition to (or instead of) Logfire's SaaS — no lock-in.
- **Recommendation: Logfire as the live tracing layer + the filesystem run bundle (§7) as the durable, vendor-neutral eval record.** We can still add MLflow later *specifically* if/when we start scoring prompt versions as formal experiments — the two are complementary, not competing. (Confirm with client — §12.)

---

## 9. Agent design (Pydantic AI)

The agent is given a **model object built by a provider-aware factory**, so the
LLM backend (first-party Anthropic API vs Azure AI Foundry) is a config switch
with no change to the agent, tools, or output model:

```python
# app/agent/model.py — the one seam that makes the LLM backend swappable
from anthropic import AsyncAnthropic, AsyncAnthropicFoundry   # both ship in `anthropic`
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

def build_model(s: Settings) -> AnthropicModel:
    if s.llm_provider == "foundry":
        client = AsyncAnthropicFoundry(            # Claude served via Azure AI Foundry
            base_url=s.azure_foundry_base_url,     # …services.ai.azure.com/anthropic/v1
            api_key=s.azure_foundry_api_key,       # or Entra ID — confirm in F1
        )
    else:                                          # "anthropic" (default)
        client = AsyncAnthropic(api_key=s.anthropic_api_key)
    return AnthropicModel(s.llm_model, provider=AnthropicProvider(anthropic_client=client))

# app/agent/triage_agent.py (sketch)
triage_agent = Agent(
    model=build_model(settings),                 # provider chosen by LLM_PROVIDER
    output_type=EmailTriageResult,
    system_prompt=build_system_prompt(config),   # injects category/priority vocab
)

@triage_agent.tool
async def convert_attachment_to_markdown(ctx, attachment_ref: str) -> str:
    """Convert a stored attachment to Markdown via MarkItDown and persist it."""
    ...
```

- **Provider seam:** `build_model()` is the only place that knows the backend.
  `LLM_PROVIDER=foundry` routes Claude through Azure AI Foundry (in-tenant,
  Australia East); everything downstream (tools, output schema, run bundle,
  Logfire) is identical. Exact async class name / auth (API key vs Entra ID) and
  that Foundry's Claude feature set (structured outputs etc., currently beta)
  covers our needs are confirmed when F1 is actioned (§13).
- The endpoint decodes/stores attachments, then runs the agent with the email text + references to the stored attachments; the agent calls the conversion tool as needed.
- Structured output is enforced by `output_type=EmailTriageResult` (Pydantic AI validates/retries).
- Every model call and tool call is captured by Logfire **and** mirrored into `runs/<id>/llm/` by a small message-history hook so the disk bundle is complete.
- Provider, model id, temperature/effort, and max steps come from `config.py`.

---

## 10. API surface (v1)

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/triage` | `InboundEmail` JSON | `EmailTriageResult` JSON (+ `run_id`) |
| `GET` | `/health` | — | `{status: "ok"}` |
| `GET` | `/version` | — | build/version info |
| `GET` | `/runs/{run_id}` | — | (dev only) manifest + artifact index for inspection |

Auth for `/triage`: shared-secret header (`X-API-Key`) validated against a setting, so only our Power Automate flow can call it. (Confirm auth approach — §12.)

The evaluation dashboard (§15) consumes the per-request run bundles (§7) via `evals/run_evals.py`; `GET /runs/{run_id}` exposes a single run's manifest/trace for inspection, and an optional `GET /runs` (list) can back a *live* dashboard later.

---

## 11. Docker & Azure deployment

**Dockerfile** (multi-stage, uv-based):
- Stage 1: `uv sync --frozen` into a venv.
- Stage 2: slim runtime (`python:3.12-slim`), copy venv + `app/`, install MarkItDown system deps as needed, `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- Non-root user; `runs/` mounted as a volume.

**docker-compose.yml** (local): app + bind-mounted `./runs`, `.env` for keys.

**Azure (v1 target: Azure Container Apps):**
1. Build & push image to **Azure Container Registry (ACR)**.
2. Deploy to **Azure Container Apps** in **Australia East** (single revision, external ingress on 8000/HTTPS).
3. Secrets (`ANTHROPIC_API_KEY`, `LOGFIRE_TOKEN`, `TRIAGE_API_KEY`) via Container Apps secrets / Key Vault.
4. `runs/` → mount **Azure Files** (v1) or switch `Storage` to **Azure Blob** (v2).
5. Logfire export configured; optionally also export OTLP → Application Insights.

---

## 12. Resolved decisions

All v1 open questions resolved 2026-06-24:

| # | Decision | Choice | Implication |
|---|---|---|---|
| 1 | Inbound contract | **Build against `tests/data` fixtures now** | Use the validated V3 fixtures; capture a real flow payload later and add aliases only if production differs. No blocker. |
| 2 | Tracking | **Logfire** | Pydantic-native tracing; FastAPI + Pydantic AI instrumented. OTLP export to Azure Monitor available. Needs a Logfire token (cloud) in env. |
| 3 | Category vocabulary | **I propose a starter set, client edits** | Seed config-driven vocab — e.g. `Finance/Invoice, Scheduling, Travel, Approvals, Admin/Office, FYI` — editable via config. |
| 4 | Output shape | **Rich `EmailTriageResult`** | Full object with per-task fields + reasoning; flat `[{email,taskid,...}]` derivable if ever needed. |
| 5 | API auth | **Shared-secret header (`X-API-Key`)** | Validated against a setting; secret in Container Apps / Key Vault. Simplest for the Power Automate HTTP action. |
| 6 | Data residency / retention | **Azure region: Australia East; retain all run bundles** | Full `runs/` artifacts kept for evaluation; redaction/short-retention revisited before scaling. |
| 7 | Default model | **`claude-sonnet-4-6`** | Quality/cost balance; env-configurable up to Opus or down to Haiku. |
| 8 | Calendar leg | **Out of scope for v1** | v1 returns the structured task list; calendar/Planner creation handled downstream by Power Automate (or a later phase). |

**One deferred action item (non-blocking):** capture one real Power Automate trigger output during integration to confirm field casing and add any aliases to `InboundEmail` (§6.1).

---

## 13. Implementation phases (suggested order)

- **P0 — Scaffold:** repo layout, `pyproject.toml` (uv), config, `/health`, Dockerfile, Logfire init. App boots in Docker.
- **P1 — Contracts & storage:** `InboundEmail`/`EmailTriageResult` models, `Storage` + run bundle, `/triage` accepting payload and persisting raw request (no LLM yet).
- **P2 — Conversion:** MarkItDown service + tool; decode & convert attachments, persist `.md`.
- **P3 — Agent:** Pydantic AI agent with Claude, structured output, LLM-call mirroring to `runs/`. End-to-end on pseudo data.
- **P4 — Observability & tests:** Logfire spans verified; `pytest` with Pydantic AI `TestModel` (no live API), conversion tests, endpoint test.
- **P5 — Azure:** ACR build/push, Container Apps deploy, secrets, Azure Files/Blob for `runs/`.
- **P6 — Eval runner + dashboard:** `evals/run_evals.py` runs **all** cases against the live containerised API and writes `dashboard/data/evals.json`; `dashboard/test-evaluation.html` renders the Methodology walkthrough + per-email Request → Output → Trace. This phase satisfies the **Definition of Done** (§16) and is the client-facing demo surface (§15).

Each phase is independently demoable; P0–P3 deliver the brief's core v1 ("email in → prioritised tasks out, every step saved"). **The plan is "done" only when the §16 acceptance test passes (P6).**

### Future / next steps (post-v1)

- **F1 — Move the LLM to Azure AI Foundry.** Flip `LLM_PROVIDER=foundry` and set the Foundry endpoint + credential; Claude inference then runs through **Azure AI Foundry** (in-tenant, Australia East) instead of the first-party Anthropic API. Because the provider seam (§9, `build_model()`) is built in v1, this is a **config + secrets change plus a smoke test — no code refactor**. When actioned, confirm: (a) `claude-sonnet-4-6` (or chosen model) and Australia East are in the Foundry catalog; (b) the exact `AsyncAnthropicFoundry` constructor/auth (API key vs Entra ID); (c) Foundry's Claude feature set (structured outputs, tool use — currently beta) covers our needs; (d) update the Dockerfile/Container Apps secrets accordingly.
- **F2 — Azure Blob storage** for `runs/` (swap `LocalFsStorage` → `AzureBlobStorage` behind the existing `Storage` interface).
- **F3 — Calendar/Planner leg, history-aware classification, and prompt-version eval** (e.g. add MLflow alongside Logfire if formal experiment scoring is wanted) as the brief's "make it smart with historical data" goal matures.

---

## 14. Risks / notes

- **MarkItDown system deps** (e.g. for some PDF/OCR paths) can bloat the image — pin `markitdown[all]` and verify the slim image converts the client's sample PDFs.
- **Structured-output retries** cost tokens; cap agent steps and surface failures as a clear error in `run.json`.
- **Large attachments** — enforce a size limit; stream/decode carefully to avoid memory spikes.
- **Prompt/vocab drift** — because the model is configurable, snapshot the active config (including `LLM_PROVIDER` + `LLM_MODEL`) into each `run.json` so past runs remain interpretable.
- **Azure Foundry (F1) is beta for Claude** — Claude-on-Foundry features are largely beta and model/region availability lags the first-party API. Keep the seam, but verify catalog availability and feature parity before flipping `LLM_PROVIDER=foundry` in any environment that matters.

---

## 15. Evaluation & walkthrough dashboard (`dashboard/test-evaluation.html`)

A single static HTML that does double duty: **(a)** walks clients/stakeholders
through the whole solution, and **(b)** lets anyone review every eval run — the
email request, the structured output, and the agent's interim steps — like a
Power Automate "run history". No build step, no framework, no backend: it
`fetch`es one generated JSON file and renders it.

### Layout (WhatsApp-style)

```
┌───────────────────────┬─────────────────────────────────────────────┐
│ SIDEBAR (chat list)   │ CONVERSATION VIEW (selected item)           │
│                       │                                             │
│ 📖 Methodology  (pin) │  ── when an email is selected ──            │
│ ───────────────────── │  ▸ REQUEST   subject / from / body / files  │
│ ✅ 01 Invoice (High)  │  ▸ OUTPUT    EmailTriageResult + pass/fail  │
│ ✅ 02 Expenses (Med)  │  ▾ TRACE / INTERIM STEPS (stepped)          │
│ ⚠️ 03 Body-only (Low) │      1. attachment → markdown (MarkItDown)   │
│ … one per eval email  │      2. LLM call: prompt / response /        │
│                       │         reasoning / tool calls / tokens     │
│                       │      3. … → final structured output         │
└───────────────────────┴─────────────────────────────────────────────┘
```

- **Sidebar** = the chat list. **"📖 Methodology" is pinned at the top**; below it, **one entry per eval case** (one email = one "conversation"), each with subject, a pass/fail dot, and a priority chip.
- **Conversation view** for a selected email, top → bottom:
  - **Request** — the inbound Power Automate payload rendered readably (subject, from, body, attachment names).
  - **Output** — the `EmailTriageResult` (each task's category/priority/summary/due-date/confidence, overall priority, reasoning) + pass/fail against `expected.json`.
  - **Trace / interim steps** — collapsible, ordered, from the run bundle (§7): each attachment→Markdown conversion, then every LLM call (prompt, response, reasoning, tool calls, token usage, timing). This is the "walk through the answer" view. Optional deep-link to the Logfire trace.

### Methodology panel (the pinned item) — the client-facing explainer

Surfaces the things normally buried in code so a non-technical stakeholder can understand the whole solution:

- **Solution diagram** — the architecture (Outlook → Power Automate → FastAPI/agent → prioritised tasks; Azure deployment), embedded as `methodology/solution-diagram.svg` (the §3 diagram).
- **How it works** — the request lifecycle in plain language (validate → persist → convert attachments → agent reasons with tools → structured output → trace saved).
- **Configuration, surfaced** — the **email category definitions** and **priority definitions**, the active **model + provider** (`claude-sonnet-4-6`; Anthropic API or Azure Foundry), the output schema, region (**Australia East**), and auth. Emitted by the runner from the **live config** (§6.2) so the page can never drift from reality.
- **Deployment & integration** — deployed to **Azure Container Apps**, **receives requests from Power Automate** (Office 365 Outlook trigger), and the roadmap (F1–F3).

### Data flow — how it "always runs all evals available"

- The HTML is **static** and renders whatever cases are present in `dashboard/data/evals.json`; it never executes evals itself.
- **`evals/run_evals.py` is the runner.** It **globs every case in `evals/cases/`**, POSTs each `request.json` to the **live containerised API** (`/triage`), captures the HTTP response, reads the matching run bundle from `runs/<run_id>/` (converted markdown, per-LLM-call prompt/response/reasoning, timings, usage), evaluates any `expected.json` checks, and writes the combined `dashboard/data/evals.json` (including the active config for the Methodology panel).
- **Add a test** = add `evals/cases/<NN-name>/` — a Power Automate payload (built with `tests/data/make_payload.py`) plus an optional `expected.json` — and re-run. Same "run & review" mental model as Power Automate's run history. Re-running the runner refreshes the dashboard.

### evals.json shape (runner ↔ HTML contract)

```jsonc
{
  "generated_at": "2026-06-24T…Z",
  "config": { "llm_provider": "anthropic", "llm_model": "claude-sonnet-4-6",
              "categories": [{"label": "...", "definition": "..."}],
              "priorities": [{"label": "...", "definition": "..."}],
              "region": "Australia East", "auth": "X-API-Key" },
  "methodology": { "diagram": "methodology/solution-diagram.svg", "summary_md": "…" },
  "cases": [
    { "id": "01-invoice-pdf", "title": "Q3 fit-out: pay deposit invoice…",
      "request": { /* InboundEmail payload */ },
      "output": { /* EmailTriageResult */ },
      "expected": { /* optional */ }, "checks": [{"name": "…", "ok": true}],
      "status": "passed", "http_status": 200, "duration_ms": 1234,
      "run_id": "…", "logfire_url": "…",
      "trace": [
        {"step": 1, "type": "attachment_conversion", "name": "invoice-INV-2045.pdf", "markdown": "…"},
        {"step": 2, "type": "llm_call", "model": "…", "prompt": "…", "response": "…",
         "reasoning": "…", "tool_calls": [], "usage": {}, "duration_ms": 0}
      ]
    }
  ]
}
```

**Tech:** plain HTML/CSS/vanilla JS so it's one openable artifact; serve as a static page (`python -m http.server` in dev, or alongside the API / from Azure Blob static hosting later). A future "Run all" button can call a `POST /evals/run` endpoint if in-browser triggering is wanted; v1 keeps the runner as a CLI / CI step.

---

## 16. Definition of Done (acceptance test)

v1 is **"fully implemented"** when this end-to-end acceptance test passes against the **containerised** app (the same image we deploy to Azure). Automatable as `make eval` / CI; it is exactly P6.

1. **Image builds & API boots.** `docker compose up --build` builds the image and the app comes healthy (`GET /health` → 200).
2. **All eval requests succeed.** `evals/run_evals.py` POSTs **every** case in `evals/cases/` to the running container's `/triage`, and each returns **HTTP 200** with a schema-valid `EmailTriageResult` (≥1 task where expected; all `expected.json` checks pass).
3. **Every interim step is captured.** Each request produced a complete run bundle under `runs/<run_id>/` (raw request, converted markdown, per-LLM-call prompt/response/reasoning, manifest).
4. **Dashboard renders the runs.** `dashboard/test-evaluation.html` loads `dashboard/data/evals.json` and shows the Methodology walkthrough plus every eval email with Request → Output → Trace.

Passing 1–4 is the v1 acceptance gate. **P5** then proves the same image runs on Azure Container Apps (Australia East) and Power Automate is pointed at the deployed `/triage` — i.e. the acceptance test, re-run against the cloud deployment.
