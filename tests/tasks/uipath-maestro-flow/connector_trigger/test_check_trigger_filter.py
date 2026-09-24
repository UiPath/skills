from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


CHECKER = Path(__file__).with_name("check_trigger_filter.py")
NODE_TYPE = "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"


def _leaf(field: str, operator: str, value: str) -> dict:
    return {"id": field, "operator": operator, "value": {"value": value, "rawString": json.dumps(value), "isLiteral": True}}


# Shape the SDK 6.9.3 `onEvent({ filters })` lowering emits; the CLI's
# `node configure` writes the same tree and `((a)&&(b))` expression form.
GOOD_TREE = {
    "groupOperator": 0,
    "index": 0,
    "filters": [_leaf("subject", "Contains", "good day"), _leaf("from.emailAddress.address", "Equals", "abc@xyz.com")],
    "groups": [],
}
GOOD_EXPRESSION = (
    "parentFolderId == 'AAMk=' && ((contains(subject,'good day'))&&(from.emailAddress.address=='abc@xyz.com'))"
)


def _flow(tree, expression) -> dict:
    configuration = {"essentialConfiguration": {"filter": tree}}
    detail = {"configuration": "=jsonString:" + json.dumps(configuration), "filterExpression": expression}
    return {"nodes": [{"id": "start", "type": NODE_TYPE, "inputs": {"detail": detail}}], "edges": []}


def _run(tmp_path: Path, flow: dict, mode: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "GoodDayMailTrigger.flow").write_text(json.dumps(flow), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECKER), mode], cwd=tmp_path, capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize("mode", ["node", "tree", "expression"])
def test_accepts_both_encodings(tmp_path: Path, mode: str) -> None:
    result = _run(tmp_path, _flow(GOOD_TREE, GOOD_EXPRESSION), mode)
    assert result.returncode == 0, result.stdout + result.stderr


def test_rejects_missing_tree(tmp_path: Path) -> None:
    result = _run(tmp_path, _flow(None, GOOD_EXPRESSION), "tree")
    assert result.returncode != 0 and "not a filter tree" in result.stdout + result.stderr


def test_rejects_tree_without_sender(tmp_path: Path) -> None:
    tree = {**GOOD_TREE, "filters": GOOD_TREE["filters"][:1]}
    result = _run(tmp_path, _flow(tree, GOOD_EXPRESSION), "tree")
    assert result.returncode != 0 and "from.emailAddress.address" in result.stdout + result.stderr


def test_rejects_or_group(tmp_path: Path) -> None:
    result = _run(tmp_path, _flow({**GOOD_TREE, "groupOperator": 1}, GOOD_EXPRESSION), "tree")
    assert result.returncode != 0 and "non-AND" in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("expression", "reason"),
    [
        ("", "is empty"),
        ("parentFolderId == 'AAMk='", "lacks"),
        ("((contains(subject,'good day'))||(from.emailAddress.address=='abc@xyz.com'))", "does not AND"),
    ],
)
def test_rejects_incomplete_expression(tmp_path: Path, expression: str, reason: str) -> None:
    result = _run(tmp_path, _flow(GOOD_TREE, expression), "expression")
    assert result.returncode != 0 and reason in result.stdout + result.stderr


def test_rejects_wrong_node_type(tmp_path: Path) -> None:
    flow = {"nodes": [{"id": "start", "type": "core.trigger.manual"}], "edges": []}
    result = _run(tmp_path, flow, "node")
    assert result.returncode != 0
