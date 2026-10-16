"""Unit tests for check_slack_multiselect's user-id, distinct-count and
connection-binding rules."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_slack_multiselect as grader  # noqa: E402

CONNECTION_ID = "2bbc2253-29a4-4952-a436-6705d74e5943"
OTHER_CONNECTION_ID = "849e85d8-1aa9-4d52-8bbd-20041c8f05d8"
GOOD_BINDING = (
    f'<uipath:binding id="B" resource="Connection" propertyAttribute="ConnectionId" '
    f'resourceKey="{CONNECTION_ID}" default="{CONNECTION_ID}" />'
)


def _process(users, binding: str = GOOD_BINDING, connection: str = "=bindings.B") -> str:
    body = json.dumps({"users": users})
    return (
        f'<bpmn:definitions xmlns:bpmn="{grader.NS["bpmn"]}" xmlns:uipath="{grader.NS["uipath"]}">'
        f"<bpmn:process id=\"P\"><bpmn:extensionElements><uipath:bindings version=\"v1\">"
        f"{binding}</uipath:bindings></bpmn:extensionElements>"
        f'<bpmn:sendTask id="T"><bpmn:extensionElements><uipath:activity version="v1">'
        f'<uipath:type value="{grader.ACTIVITY_TYPE}" version="v1" /><uipath:context>'
        f'<uipath:input name="connectorKey" type="string" value="{grader.SLACK_KEY}" />'
        f'<uipath:input name="connection" type="string" value="{connection}" />'
        f"</uipath:context>"
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>'
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask></bpmn:process>"
        f"</bpmn:definitions>"
    )


def _task(root: ET.Element) -> ET.Element:
    return grader.slack_tasks(root)[0]


@pytest.mark.parametrize("value", ["U0BAW1WQT0F", "W012ABC"])
def test_is_user_id_accepts(value) -> None:
    assert grader.is_user_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "#general",
        "general",
        "IS-sandboxes@uipath.com",
        "",
        "Cgeneral",
        "C0123ABC",
        "G0123ABC",
        "D0123ABC",
        "U0123 general",
        "U0123ABC\n",
        "=vars.x",
        "E2E Nightly Summary",
        None,
        123,
    ],
)
def test_is_user_id_rejects(value) -> None:
    assert not grader.is_user_id(value)


def _run_main(tmp_path, monkeypatch, users, *argv: str) -> int:
    (tmp_path / "P.bpmn").write_text(_process(users), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_slack_multiselect.py", *argv])
    with pytest.raises(SystemExit) as exc:
        grader.main()
    return 0 if exc.value.code in (0, None) else 1


def test_three_distinct_ids_pass(tmp_path, monkeypatch) -> None:
    users = ["U0BAW1WQT0F", "U02EBQA5AD9", "U0A1U64L5EG"]
    assert _run_main(tmp_path, monkeypatch, users) == 0


def test_one_id_repeated_fails(tmp_path, monkeypatch) -> None:
    assert _run_main(tmp_path, monkeypatch, ["U0BAW1WQT0F"] * 3) == 1


def test_display_name_fails(tmp_path, monkeypatch) -> None:
    users = ["U0BAW1WQT0F", "U02EBQA5AD9", "E2E Nightly Summary"]
    assert _run_main(tmp_path, monkeypatch, users) == 1


def test_display_name_fails_populated(tmp_path, monkeypatch) -> None:
    assert _run_main(tmp_path, monkeypatch, ["Coder Eval Test"], "populated") == 1


def test_bound_connection_accepts_connection_binding() -> None:
    root = ET.fromstring(_process([]))
    assert grader.bound_connection(root, _task(root)) == CONNECTION_ID


@pytest.mark.parametrize(
    "binding, connection",
    [
        (GOOD_BINDING, CONNECTION_ID),
        (GOOD_BINDING.replace('resource="Connection"', 'resource="process"'), "=bindings.B"),
        (GOOD_BINDING.replace('propertyAttribute="ConnectionId"', 'propertyAttribute="folderKey"'), "=bindings.B"),
        (GOOD_BINDING.replace(CONNECTION_ID, OTHER_CONNECTION_ID), "=bindings.B"),
        (GOOD_BINDING.replace(f'default="{CONNECTION_ID}"', f'default="{OTHER_CONNECTION_ID}"'), "=bindings.B"),
        (GOOD_BINDING, "=bindings.Missing"),
    ],
    ids=["literal", "process", "folder-key", "wrong-id", "key-default-mismatch", "unknown-binding"],
)
def test_bound_connection_rejects(binding, connection) -> None:
    root = ET.fromstring(_process([], binding, connection))
    assert grader.bound_connection(root, _task(root)) != CONNECTION_ID


def test_require_connection(tmp_path, monkeypatch) -> None:
    (tmp_path / "P.bpmn").write_text(_process([]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    grader.require_connection(None, CONNECTION_ID)
    with pytest.raises(SystemExit):
        grader.require_connection(None, OTHER_CONNECTION_ID)


def test_require_ids(tmp_path, monkeypatch) -> None:
    (tmp_path / "P.bpmn").write_text(_process(["U0BAW1WQT0F"]), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    grader.require_ids(None, ("U0BAW1WQT0F",))
    with pytest.raises(SystemExit):
        grader.require_ids(None, ("U0BAW1WQT0F", "U02EBQA5AD9"))
