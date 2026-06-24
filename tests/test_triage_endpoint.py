from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

DATA_DIR = Path(__file__).parent / "data"
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _sample_payload() -> dict[str, Any]:
    return json.loads((DATA_DIR / "sample_email_no_attachment.json").read_text())


def _fake_result() -> dict[str, Any]:
    return {
        "email_message_id": "mock-message-id",
        "sender": "sender@example.com",
        "overall_priority": "high",
        "tasks": [
            {
                "task_id": 1,
                "category": "Admin/Office",
                "summary": "Mocked triage task from the endpoint test.",
                "priority": "high",
                "due_date": None,
                "confidence": 0.99,
                "source": "body",
            }
        ],
        "reasoning": "Mock triage behavior; no live LLM was called.",
    }


class FakeAgentResult:
    def __init__(self, output: Any) -> None:
        self.output = output
        self.data = output


class FakeTriageAgent:
    async def run(self, *_args: Any, **_kwargs: Any) -> FakeAgentResult:
        return FakeAgentResult(_fake_result_model())

    def run_sync(self, *_args: Any, **_kwargs: Any) -> FakeAgentResult:
        return FakeAgentResult(_fake_result_model())


def _fake_result_model() -> Any:
    triage = importlib.import_module("app.models.triage")
    return triage.EmailTriageResult.model_validate(_fake_result())


async def _fake_async_triage(*_args: Any, **_kwargs: Any) -> Any:
    return _fake_result_model()


def _fake_sync_triage(*_args: Any, **_kwargs: Any) -> Any:
    return _fake_result_model()


def _install_mock_triage(monkeypatch: pytest.MonkeyPatch) -> None:
    patched = False
    module_names = (
        "app.main",
        "app.api.routes_triage",
        "app.agent.triage_agent",
    )
    async_function_names = (
        "triage_email",
        "run_triage_agent",
        "run_triage",
        "process_triage",
        "extract_tasks",
    )

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        for name in async_function_names:
            if hasattr(module, name):
                monkeypatch.setattr(module, name, _fake_async_triage)
                patched = True

        for name in ("triage", "triage_service"):
            if hasattr(module, name):
                monkeypatch.setattr(module, name, _fake_sync_triage)
                patched = True

        for name in ("triage_agent", "agent"):
            if hasattr(module, name):
                monkeypatch.setattr(module, name, FakeTriageAgent())
                patched = True

    if not patched:
        pytest.fail(
            "No triage seam was available to monkeypatch. Expose a route-level "
            "triage function/service/agent so /triage can be tested without a "
            "live LLM."
        )


def _response_json(response: Any) -> dict[str, Any]:
    payload = response.json()
    if "result" in payload and isinstance(payload["result"], dict):
        return payload["result"]
    return payload


def test_triage_endpoint_returns_mocked_structured_result_without_live_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    testclient = pytest.importorskip("fastapi.testclient")

    monkeypatch.setenv("TRIAGE_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    config = importlib.import_module("app.config")
    config.get_settings.cache_clear()

    main = pytest.importorskip("app.main")
    app = getattr(main, "app", None)
    if app is None:
        pytest.fail("app.main must expose a FastAPI instance named app.")

    _install_mock_triage(monkeypatch)

    client = testclient.TestClient(app)
    response = client.post(
        "/triage",
        json=_sample_payload(),
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200, response.text
    body = _response_json(response)

    assert body["overall_priority"] == "high"
    assert body["tasks"][0]["summary"] == "Mocked triage task from the endpoint test."
    assert "live LLM" in body["reasoning"]
