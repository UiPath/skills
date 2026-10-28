import importlib.util
import json
from pathlib import Path

import pytest


CHECKER_PATH = Path(__file__).with_name("check_webhook_waitfor_parallel.py")
SPEC = importlib.util.spec_from_file_location("check_webhook_waitfor_parallel", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


@pytest.mark.parametrize("http_type", ["core.action.http", "core.action.http.v2"])
def test_accepts_both_managed_http_representations(tmp_path, monkeypatch, http_type):
    monkeypatch.chdir(tmp_path)
    if http_type.endswith(".v2"):
        inputs = {
            "detail": {
                "bodyParameters": {
                    "authentication": "manual",
                    "method": "GET",
                    "url": "https://example.test/webhook/events/1",
                    "headers": {},
                    "query": {},
                }
            }
        }
    else:
        inputs = {
            "authenticationType": "manual",
            "method": "GET",
            "url": "https://example.test/webhook/events/1",
            "headers": {},
            "queryParams": {},
        }

    flow = {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {
                "id": "wait",
                "type": "uipath.connector.event.uipath-http-webhook.http-webhook",
            },
            {"id": "get", "type": http_type, "inputs": inputs},
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "wait"},
            {"sourceNodeId": "start", "targetNodeId": "get"},
            {"sourceNodeId": "wait", "targetNodeId": "end"},
            {"sourceNodeId": "get", "targetNodeId": "end"},
        ],
    }
    (tmp_path / "WebhookSelfTest.flow").write_text(json.dumps(flow))

    CHECKER.main()


def _write_fork_flow(tmp_path, arms):
    get_inputs = {"authenticationType": "manual", "method": "GET", "url": "https://example.test/webhook/events/1"}
    flow = {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {"id": "fork", "type": "core.logic.merge"},
            {"id": "wait", "type": "uipath.connector.event.uipath-http-webhook.http-webhook"},
            {"id": "get", "type": "core.action.http", "inputs": get_inputs},
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "targetNodeId": "fork"},
            *({"sourceNodeId": "fork", "targetNodeId": arm} for arm in arms),
            {"sourceNodeId": "wait", "targetNodeId": "end"},
            {"sourceNodeId": "get", "targetNodeId": "end"},
        ],
    }
    (tmp_path / "WebhookSelfTest.flow").write_text(json.dumps(flow))


def test_accepts_fan_out_through_merge_fork(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_fork_flow(tmp_path, ["wait", "get"])

    CHECKER.main()


def test_rejects_merge_fork_with_one_arm(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_fork_flow(tmp_path, ["wait"])

    with pytest.raises(SystemExit, match="must fan out into >=2 branches"):
        CHECKER.main()
