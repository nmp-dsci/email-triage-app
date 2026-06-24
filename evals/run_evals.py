#!/usr/bin/env python3
"""Run all live API eval cases and write the static dashboard data file."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_DIR = PROJECT_ROOT / "evals" / "cases"
DEFAULT_OUT = PROJECT_ROOT / "dashboard" / "data" / "evals.json"
DEFAULT_DATA_JS = PROJECT_ROOT / "dashboard" / "assets" / "evals-data.js"
DEFAULT_RUNS_DIR = PROJECT_ROOT / "runs"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_CATEGORIES = [
    {
        "label": "finance",
        "definition": "Invoices, expenses, approvals, payments, budgets, or reconciliation work.",
    },
    {
        "label": "scheduling",
        "definition": "Calendar, meeting, call, booking, deadline, or coordination work.",
    },
    {
        "label": "operations",
        "definition": "Office, facilities, vendor, compliance, or process tasks.",
    },
    {
        "label": "admin",
        "definition": "General assistant tasks that do not fit a more specific category.",
    },
    {
        "label": "fyi",
        "definition": "Information-only items with no action required.",
    },
]

DEFAULT_PRIORITIES = [
    {"label": "urgent", "definition": "Needs immediate action or has same-day risk."},
    {"label": "high", "definition": "Important, time-sensitive, or financially material."},
    {"label": "medium", "definition": "Actionable with a known deadline, but not urgent."},
    {"label": "low", "definition": "Useful action with low risk or flexible timing."},
    {"label": "fyi", "definition": "No task required; keep for awareness only."},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    env_api_url = os.environ.get("TRIAGE_API_URL") or os.environ.get("EVAL_API_URL")
    parser.add_argument(
        "--api-url",
        default=normalize_api_url(env_api_url or "http://localhost:8000/triage"),
        help="Full triage endpoint URL. Defaults to TRIAGE_API_URL or localhost.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("TRIAGE_API_KEY"),
        help="Optional X-API-Key header value. Defaults to TRIAGE_API_KEY.",
    )
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=DEFAULT_CASES_DIR,
        help="Directory containing eval case folders.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Dashboard JSON output path.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path(os.environ.get("RUNS_DIR", DEFAULT_RUNS_DIR)),
        help="Run bundle root directory.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("EVAL_TIMEOUT_SECONDS", "120")),
        help="HTTP timeout per case in seconds.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run evals through the FastAPI app in-process; no uvicorn/Docker server required.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero when any case fails.",
    )
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_api_url(value: str) -> str:
    value = value.rstrip("/")
    return value if value.endswith("/triage") else f"{value}/triage"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def write_data_js(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    json_payload = json.dumps(payload, indent=2, ensure_ascii=True)
    path.write_text(f"window.EMAIL_TRIAGE_EVALS = {json_payload};\n", encoding="utf-8")


def discover_cases(cases_dir: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    if not cases_dir.exists():
        return cases

    for case_dir in sorted(path for path in cases_dir.iterdir() if path.is_dir()):
        request_path = case_dir / "request.json"
        if not request_path.exists():
            continue
        expected_path = case_dir / "expected.json"
        request_payload = read_json(request_path)
        expected = read_json(expected_path) if expected_path.exists() else None
        cases.append(
            {
                "id": case_dir.name,
                "title": request_payload.get("subject") or case_dir.name,
                "request": request_payload,
                "expected": expected,
            }
        )
    return cases


def post_case(
    api_url: str,
    api_key: str | None,
    timeout: float,
    payload: dict[str, Any],
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    request = urllib.request.Request(api_url, data=body, headers=headers, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            duration_ms = round((time.perf_counter() - started) * 1000)
            return {
                "http_status": response.status,
                "duration_ms": duration_ms,
                "headers": dict(response.headers.items()),
                "raw_body": raw,
                "json": parse_json_body(raw),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        duration_ms = round((time.perf_counter() - started) * 1000)
        return {
            "http_status": exc.code,
            "duration_ms": duration_ms,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "raw_body": raw,
            "json": parse_json_body(raw),
            "error": f"HTTP {exc.code}: {exc.reason}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        duration_ms = round((time.perf_counter() - started) * 1000)
        return {
            "http_status": None,
            "duration_ms": duration_ms,
            "headers": {},
            "raw_body": "",
            "json": None,
            "error": str(exc),
        }


def post_case_offline(client: Any, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    started = time.perf_counter()
    response = client.post("/triage", json=payload, headers={"X-API-Key": api_key})
    duration_ms = round((time.perf_counter() - started) * 1000)
    raw = response.text
    return {
        "http_status": response.status_code,
        "duration_ms": duration_ms,
        "headers": dict(response.headers.items()),
        "raw_body": raw,
        "json": parse_json_body(raw),
        "error": None if response.status_code < 400 else f"HTTP {response.status_code}",
    }


def build_offline_client(api_key: str, runs_dir: Path) -> Any:
    os.environ["TRIAGE_API_KEY"] = api_key
    os.environ["RUNS_DIR"] = str(runs_dir)
    os.environ.setdefault("LLM_PROVIDER", "mock")

    from fastapi.testclient import TestClient

    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    return TestClient(app)


def parse_json_body(raw: str) -> Any:
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_output(response_json: Any) -> Any:
    if not isinstance(response_json, dict):
        return response_json
    for key in ("result", "triage", "data", "output"):
        value = response_json.get(key)
        if isinstance(value, (dict, list)):
            return value
    return response_json


def extract_tasks(output: Any) -> list[dict[str, Any]]:
    if isinstance(output, list):
        return [task for task in output if isinstance(task, dict)]
    if isinstance(output, dict):
        tasks = output.get("tasks")
        if isinstance(tasks, list):
            return [task for task in tasks if isinstance(task, dict)]
    return []


def extract_run_id(response_json: Any, headers: dict[str, str]) -> str | None:
    candidates: list[Any] = []
    if isinstance(response_json, dict):
        candidates.extend(
            [
                response_json.get("run_id"),
                response_json.get("runId"),
                response_json.get("request_id"),
                response_json.get("requestId"),
            ]
        )
        run = response_json.get("run")
        if isinstance(run, dict):
            candidates.extend([run.get("id"), run.get("run_id"), run.get("runId")])
    candidates.extend(
        [
            headers.get("X-Run-Id"),
            headers.get("x-run-id"),
            headers.get("X-Request-Id"),
            headers.get("x-request-id"),
        ]
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def find_run_dir(runs_dir: Path, run_id: str | None) -> Path | None:
    if not run_id or not runs_dir.exists():
        return None

    direct = runs_dir / run_id
    if direct.is_dir():
        return direct

    for path in runs_dir.rglob(run_id):
        if path.is_dir():
            return path
    return None


def load_run_bundle(runs_dir: Path, run_id: str | None) -> tuple[list[dict[str, Any]], str | None]:
    run_dir = find_run_dir(runs_dir, run_id)
    if run_dir is None:
        return [], None

    trace: list[dict[str, Any]] = []
    step = 1

    attachments_dir = run_dir / "attachments"
    if attachments_dir.exists():
        for markdown_path in sorted(attachments_dir.glob("*.md")):
            trace.append(
                {
                    "step": step,
                    "type": "attachment_conversion",
                    "name": markdown_path.name,
                    "markdown": safe_read_text(markdown_path),
                }
            )
            step += 1

    llm_dir = run_dir / "llm"
    if llm_dir.exists():
        used: set[Path] = set()
        for call_path in sorted(llm_dir.glob("*call.json")):
            response_path = call_path.with_name(
                call_path.name.replace("call.json", "response.json")
            )
            call_json = safe_read_json(call_path)
            response_json = safe_read_json(response_path) if response_path.exists() else None
            used.add(call_path)
            used.add(response_path)
            trace.append(
                {
                    "step": step,
                    "type": "llm_call",
                    "name": call_path.stem,
                    "model": find_first(call_json, ("model", "model_name")),
                    "prompt": call_json,
                    "response": response_json,
                    "reasoning": find_first(
                        response_json,
                        ("reasoning", "thinking", "explanation"),
                    ),
                    "tool_calls": find_first(response_json, ("tool_calls", "tools")) or [],
                    "usage": find_first(response_json, ("usage", "token_usage")) or {},
                    "duration_ms": find_first(response_json, ("duration_ms", "elapsed_ms")),
                }
            )
            step += 1

        for artifact_path in sorted(llm_dir.glob("*.json")):
            if artifact_path in used:
                continue
            trace.append(
                {
                    "step": step,
                    "type": "llm_artifact",
                    "name": artifact_path.name,
                    "json": safe_read_json(artifact_path),
                }
            )
            step += 1

    run_manifest = safe_read_json(run_dir / "run.json")
    logfire_url = None
    if isinstance(run_manifest, dict):
        logfire_url = find_first(run_manifest, ("logfire_url", "trace_url", "traceUrl"))
        trace.append(
            {
                "step": step,
                "type": "run_manifest",
                "name": "run.json",
                "json": run_manifest,
            }
        )

    return trace, logfire_url if isinstance(logfire_url, str) else None


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Unable to read {path}: {exc}"


def safe_read_json(path: Path) -> Any:
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def find_first(payload: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload:
                return payload[key]
        for value in payload.values():
            found = find_first(value, keys)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = find_first(item, keys)
            if found is not None:
                return found
    return None


def evaluate_case(
    request_payload: dict[str, Any],
    response: dict[str, Any],
    output: Any,
    expected: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    tasks = extract_tasks(output)

    add_check(checks, "HTTP 200", response["http_status"] == 200, response.get("error"))
    add_check(checks, "JSON response", response["json"] is not None, "Response body was not JSON")

    if response["http_status"] == 200:
        add_check(
            checks,
            "Task list present",
            bool(tasks),
            "No tasks found at output.tasks or top level",
        )

    if not expected:
        return checks

    if "min_tasks" in expected:
        add_check(
            checks,
            f"At least {expected['min_tasks']} task(s)",
            len(tasks) >= int(expected["min_tasks"]),
            f"Found {len(tasks)} task(s)",
        )

    if "max_tasks" in expected:
        add_check(
            checks,
            f"At most {expected['max_tasks']} task(s)",
            len(tasks) <= int(expected["max_tasks"]),
            f"Found {len(tasks)} task(s)",
        )

    expected_priorities = expected.get("overall_priority_in")
    if expected_priorities is None and "overall_priority" in expected:
        expected_priorities = [expected["overall_priority"]]
    if expected_priorities is not None:
        actual = normalized_value(
            output.get("overall_priority") if isinstance(output, dict) else None
        )
        allowed = {normalized_value(item) for item in expected_priorities}
        add_check(
            checks,
            "Overall priority",
            actual in allowed,
            f"Expected one of {sorted(allowed)}, got {actual or 'missing'}",
        )

    check_in_task_field(checks, tasks, expected, "priorities_include", "priority")
    check_in_task_field(checks, tasks, expected, "categories_include", "category")
    check_in_task_field(checks, tasks, expected, "sources_include", "source")

    searchable_output = json.dumps(output, sort_keys=True, ensure_ascii=False).lower()
    for needle in expected.get("summaries_include", []):
        add_check(
            checks,
            f"Output mentions {needle}",
            str(needle).lower() in searchable_output,
            "Substring not found in JSON output",
        )

    for needle in expected.get("due_dates_include", []):
        add_check(
            checks,
            f"Due date mentions {needle}",
            str(needle).lower() in searchable_output,
            "Due date substring not found in JSON output",
        )

    attachment_names = {
        str(attachment.get("name", "")).lower()
        for attachment in request_payload.get("attachments", [])
        if isinstance(attachment, dict)
    }
    for name in expected.get("attachment_names_include", []):
        add_check(
            checks,
            f"Input includes attachment {name}",
            str(name).lower() in attachment_names,
            f"Available attachments: {sorted(attachment_names)}",
        )

    return checks


def check_in_task_field(
    checks: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    expected: dict[str, Any],
    expected_key: str,
    task_key: str,
) -> None:
    values = {normalized_value(task.get(task_key)) for task in tasks}
    for expected_value in expected.get(expected_key, []):
        normalized = normalized_value(expected_value)
        add_check(
            checks,
            f"Task {task_key} includes {expected_value}",
            normalized in values,
            f"Found {sorted(value for value in values if value)}",
        )


def normalized_value(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str | None = None) -> None:
    check = {"name": name, "ok": bool(ok)}
    if detail and not ok:
        check["detail"] = detail
    checks.append(check)


def build_dashboard_payload(
    cases: list[dict[str, Any]],
    api_url: str,
    api_key: str | None,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "config": {
            "llm_provider": os.environ.get("LLM_PROVIDER", "anthropic"),
            "llm_model": os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
            "categories": load_json_env("TRIAGE_CATEGORIES_JSON", DEFAULT_CATEGORIES),
            "priorities": load_json_env("TRIAGE_PRIORITIES_JSON", DEFAULT_PRIORITIES),
            "region": os.environ.get("AZURE_REGION", "Australia East"),
            "auth": "X-API-Key" if api_key else "none configured for eval run",
            "api_url": api_url,
            "mode": "offline" if api_url == "offline" else "http",
        },
        "methodology": {
            "diagram": "methodology/solution-diagram.svg",
            "summary_md": (
                "Power Automate posts an Outlook email payload to the FastAPI triage "
                "service. The service validates the request, persists the run, converts "
                "attachments to Markdown, asks the LLM agent for a structured task list, "
                "and saves trace artifacts for review."
            ),
        },
        "cases": cases,
    }


def load_json_env(name: str, fallback: Any) -> Any:
    raw = os.environ.get(name)
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def main() -> int:
    args = parse_args()
    args.api_url = "offline" if args.offline else normalize_api_url(args.api_url)
    api_key = args.api_key or os.environ.get("TRIAGE_API_KEY") or "dev-secret"
    case_inputs = discover_cases(args.cases_dir)
    results: list[dict[str, Any]] = []
    offline_client = build_offline_client(api_key, args.runs_dir) if args.offline else None

    if not case_inputs:
        print(f"No eval cases found in {args.cases_dir}", file=sys.stderr)

    try:
        for case in case_inputs:
            print(f"Running {case['id']} -> {args.api_url}")
            if offline_client is not None:
                response = post_case_offline(offline_client, case["request"], api_key)
            else:
                response = post_case(args.api_url, args.api_key, args.timeout, case["request"])
            output = extract_output(response["json"])
            run_id = extract_run_id(response["json"], response["headers"])
            trace, logfire_url = load_run_bundle(args.runs_dir, run_id)
            checks = evaluate_case(case["request"], response, output, case["expected"])
            passed = all(check["ok"] for check in checks)

            results.append(
                {
                    "id": case["id"],
                    "title": case["title"],
                    "request": case["request"],
                    "output": output,
                    "expected": case["expected"],
                    "checks": checks,
                    "status": "passed" if passed else "failed",
                    "http_status": response["http_status"],
                    "duration_ms": response["duration_ms"],
                    "run_id": run_id,
                    "logfire_url": logfire_url,
                    "trace": trace,
                    "error": response["error"],
                    "raw_response": response["raw_body"] if output is None else None,
                }
            )
    finally:
        if offline_client is not None:
            offline_client.close()

    dashboard_payload = build_dashboard_payload(results, args.api_url, api_key)
    write_json(args.out, dashboard_payload)
    write_data_js(DEFAULT_DATA_JS, dashboard_payload)

    passed_count = sum(1 for case in results if case["status"] == "passed")
    print(f"Wrote {args.out}")
    print(f"Wrote {DEFAULT_DATA_JS}")
    print(f"{passed_count}/{len(results)} cases passed")

    if args.fail_on_error and passed_count != len(results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
