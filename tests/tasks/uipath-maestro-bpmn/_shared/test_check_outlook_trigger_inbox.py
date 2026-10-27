"""The bound connection check_outlook_trigger_inbox reads, V1 and V2."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_outlook_trigger_inbox as grader  # noqa: E402

CONNECTION_ID = "75dfafb4-3717-470c-a5f6-bdc144757a67"
FOLDER_ID = "AAMkAGNiNDVjZmJmAAEMAAA="
BINDING = (
    f'<uipath:binding id="bConn" default="{CONNECTION_ID}" resource="Connection" '
    f'resourceKey="{CONNECTION_ID}" propertyAttribute="ConnectionId" />'
)
V2_CONNECTION = '<uipath:input name="connection" type="string" value="=bindings.bConn" />'
V1 = "v1"
V2 = "v2"
V1_CONNECTION = '<uipath:input name="connectionId" type="string" value="=bindings.bConn" />'


# Trimmed from skill-bpmn-outlook-trigger-inbox 2026-10-23.
def _bpmn(connection: str, binding: str = BINDING, version: str = V2) -> str:
    v2_config = '<uipath:intsvcActivityConfig version="v2" />' if version == V2 else ""
    v2_flag = (
        '<uipath:input name="activityConfigurationVersion" type="string" value="v2" />'
        if version == V2
        else ""
    )
    return (
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="Process_1">'
        f'<bpmn:extensionElements><uipath:bindings version="v1">{binding}</uipath:bindings>'
        f"{v2_config}</bpmn:extensionElements>"
        '<bpmn:startEvent id="Event_start"><bpmn:extensionElements><uipath:event version="v1">'
        '<uipath:type value="Intsvc.EventTrigger" version="v1" /><uipath:context>'
        '<uipath:input name="connectorKey" type="string" value="uipath-microsoft-outlook365" />'
        f"{connection}"
        '<uipath:input name="objectName" type="string" value="Message" />'
        '<uipath:input name="operation" type="string" value="EMAIL_RECEIVED" />'
        f"{v2_flag}</uipath:context>"
        '<uipath:input name="body" type="json" target="body"><![CDATA['
        f'{{"queryParams":{{"parentFolderId":"{FOLDER_ID}"}}}}]]></uipath:input>'
        "</uipath:event></bpmn:extensionElements><bpmn:messageEventDefinition />"
        "</bpmn:startEvent></bpmn:process></bpmn:definitions>"
    )


@pytest.fixture
def project(tmp_path, monkeypatch):
    queried: list[str] = []

    def write(xml: str) -> list[str]:
        folder = tmp_path / "OutlookTriggerInbox"
        folder.mkdir(exist_ok=True)
        (folder / "OutlookTriggerInbox.bpmn").write_text(xml, encoding="utf-8")
        return queried

    def resources_run(tail_args: list[str]) -> dict:
        queried.append(tail_args[tail_args.index("--connection-id") + 1])
        return {"Data": [{"Id": FOLDER_ID, "DisplayName": "Inbox"}]}

    def no_default() -> tuple[str, str, str]:
        raise AssertionError("the bound connection must be checked, not the folder default")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(grader, "_uip_resources_run", resources_run)
    monkeypatch.setattr(grader, "_find_default_outlook_connection", no_default)
    return write


@pytest.mark.parametrize(
    ["connection", "version"],
    [
        (V2_CONNECTION, V2),
        (V1_CONNECTION, V1),
        ('<uipath:input name="connection" type="string" value=" " />' + V1_CONNECTION, V1),
    ],
    ids=["v2-connection", "v1-connectionId", "blank-connection-falls-back"],
)
def test_checks_the_bound_connection(project, connection, version, capsys) -> None:
    queried = project(_bpmn(connection, version=version))

    grader.check_folder_binding()
    grader.check_folder_id_fresh()

    assert queried == [CONNECTION_ID]
    assert "parentFolderId resolves on current connection" in capsys.readouterr().out


def test_connection_wins_over_connectionId(project) -> None:
    other = '<uipath:input name="connectionId" type="string" value="other-connection" />'
    queried = project(_bpmn(V2_CONNECTION + other))

    grader.check_folder_id_fresh()

    assert queried == [CONNECTION_ID]


def test_no_connection_fails_binding(project) -> None:
    project(_bpmn(""))

    with pytest.raises(SystemExit, match="no connection"):
        grader.check_folder_binding()


@pytest.mark.parametrize(
    "binding",
    ["", BINDING.replace('propertyAttribute="ConnectionId"', 'propertyAttribute="folderKey"')],
    ids=["undeclared", "not-connection-id"],
)
def test_unresolvable_binding_fails(project, binding) -> None:
    project(_bpmn(V2_CONNECTION, binding))

    with pytest.raises(SystemExit, match="no resolvable Connection binding"):
        grader.check_folder_id_fresh()
