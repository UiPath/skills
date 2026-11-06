"""check_integration_service_boundary grades the draft node, not the notes' wording (UiPath/builder-sdk#1808)."""

from __future__ import annotations

import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_GRADER = Path(__file__).parent / "check_integration_service_boundary.py"
GUID = "3f2b8c1e-9a4d-4e7b-8c21-5d6e7f8a9b0c"


def _load():
    spec = importlib.util.spec_from_file_location("check_integration_service_boundary", _GRADER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load()


def _bpmn(bindings: str, connection: str = "=bindings.slack", task: str = "") -> ET.Element:
    """The send node as both arms write it: v1 by hand, v2 from `.connector()`."""
    return ET.fromstring(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="Process_1">'
        f'<bpmn:extensionElements><uipath:bindings version="v1">{bindings}</uipath:bindings></bpmn:extensionElements>'
        '<bpmn:sendTask id="send" name="Send Slack digest"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1"/>'
        f'<uipath:context><uipath:input name="connection" type="string" value="{connection}"/>'
        '<uipath:input name="folderKey" type="string" value="=bindings.slackFolder"/></uipath:context>'
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask>{task}</bpmn:process></bpmn:definitions>"
    )


def _binding(bid: str, default: str, resource_key: str = "slack") -> str:
    return f'<uipath:binding id="{bid}" resource="Connection" resourceKey="{resource_key}" default="{default}"/>'


def _send(root: ET.Element) -> ET.Element:
    return checker.intsvc_nodes(root)[0]


@pytest.mark.parametrize(
    "connection_default",
    ["slack", "&lt;connection-id&gt;", ""],
    ids=["v2-symbolic-name", "v1-placeholder", "no-default"],
)
def test_unresolved_connection_binding_passes(connection_default: str) -> None:
    root = _bpmn(_binding("slack", connection_default) + _binding("slackFolder", "slackFolder"))
    checker.require_connection_unresolved(root, _send(root))


def test_resolved_connection_id_fails() -> None:
    root = _bpmn(_binding("slack", GUID) + _binding("slackFolder", "slackFolder"))
    with pytest.raises(SystemExit, match="resolved id in default"):
        checker.require_connection_unresolved(root, _send(root))


def test_resolved_folder_key_fails() -> None:
    root = _bpmn(_binding("slack", "slack") + _binding("slackFolder", GUID))
    with pytest.raises(SystemExit, match="folderKey binding `slackFolder`"):
        checker.require_connection_unresolved(root, _send(root))


def test_undeclared_binding_fails() -> None:
    root = _bpmn(_binding("slackFolder", "slackFolder"))
    with pytest.raises(SystemExit, match="declares no such binding"):
        checker.require_connection_unresolved(root, _send(root))


def test_literal_connection_id_fails() -> None:
    root = _bpmn(_binding("slackFolder", "slackFolder"), connection=GUID)
    with pytest.raises(SystemExit, match="literal connection id"):
        checker.require_connection_unresolved(root, _send(root))


@pytest.mark.parametrize(
    ("name", "accepted"),
    [
        ("Send Slack digest (uipath-salesforce-slack / send-message-to-channel, unresolved)", True),
        ("Post digest to SLACK", True),
        ("Prepare Slack digest", False),
        ("Send digest", False),
    ],
)
def test_bare_task_must_name_the_slack_send(name: str, accepted: bool) -> None:
    root = _bpmn("", task=f'<bpmn:task id="bare" name="{name}"/>')
    assert bool(checker.bare_connector_tasks(root)) is accepted
