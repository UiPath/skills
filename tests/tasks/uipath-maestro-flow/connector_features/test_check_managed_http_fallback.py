from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_managed_http_fallback as checker  # noqa: E402

HTTP_TYPE = "core.action.http.v2"
HOST = {"url": "https://tasks.googleapis.com"}
REQUEST = {"path": "/tasks/v1/lists/@default/tasks", "method": "GET", "query": {"showHidden": True}}


def _flow(*inputs: dict) -> dict:
    return {"nodes": [{"type": HTTP_TYPE, "inputs": node_inputs} for node_inputs in inputs]}


def test_query_params_split_url_on_one_node_passes() -> None:
    checker._check_query_params(_flow({**HOST, **REQUEST}))


def test_query_params_evidence_across_two_nodes_fails() -> None:
    with pytest.raises(SystemExit, match="any one HTTP node"):
        checker._check_query_params(_flow(HOST, REQUEST))
