from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


CHECKER = Path(__file__).with_name("check_dtl_load_by_default_false.py")
NODE_TYPE = "uipath.connector.uipath-automattic-woocommerce.search-products"
CONNECTION = "3f0c2a8e-6d1b-4c7e-9a41-2b5d8e7f1c03"


def _flow(detail: dict | None) -> dict:
    node: dict = {"id": "listProducts", "type": NODE_TYPE}
    if detail is not None:
        node["inputs"] = {"detail": detail}
    return {"nodes": [{"id": "start", "type": "core.trigger.manual"}, node], "edges": []}


def _run(tmp_path: Path, flow: dict) -> subprocess.CompletedProcess[str]:
    (tmp_path / "DTLLoadByDefaultFalseTest.flow").write_text(json.dumps(flow), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize("value", ["42", 42, "=js:$vars.start.output.term"])
def test_accepts_term_id_or_expression_on_a_real_connection(tmp_path: Path, value) -> None:
    result = _run(tmp_path, _flow({"connectionId": CONNECTION, "queryParameters": {"attribute_term": value}}))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("detail", "reason"),
    [
        # v1 shape from adhoc-2026-09-24: node added, never configured.
        (None, "never configured"),
        # v2 shape from adhoc-2026-09-24: unresolved lookup kept as prose, no connection.
        ({"queryParameters": {"attribute_term": "selected attribute term"}}, "not free text"),
        ({"connectionId": CONNECTION, "queryParameters": {}}, "no inputs.detail.queryParameters"),
        ({"queryParameters": {"attribute_term": "42"}}, "not bound to a real connection"),
        (
            {"connectionId": "00000000-0000-0000-0000-000000000001", "queryParameters": {"attribute_term": "42"}},
            "not bound to a real connection",
        ),
    ],
)
def test_rejects_unconfigured_or_unbound_builds(tmp_path: Path, detail, reason) -> None:
    result = _run(tmp_path, _flow(detail))
    assert result.returncode != 0
    assert reason in result.stdout + result.stderr
