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
        ("Prepare Slack message", False),
        ("Slack message", False),
        ("Send digest", False),
    ],
)
def test_bare_task_must_name_the_slack_send(name: str, accepted: bool) -> None:
    root = _bpmn("", task=f'<bpmn:task id="bare" name="{name}"/>')
    assert bool(checker.bare_connector_tasks(root)) is accepted


def test_undeclared_folder_binding_fails() -> None:
    root = _bpmn(_binding("slack", "slack"))
    with pytest.raises(SystemExit, match="folderKey reads `=bindings.slackFolder`"):
        checker.require_connection_unresolved(root, _send(root))


def test_intsvc_payload_on_bare_task_is_not_a_placeholder() -> None:
    """A named bpmn:task carrying Intsvc would otherwise skip the binding check."""
    intsvc = (
        '<bpmn:task id="bare" name="Send Slack digest"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1"/>'
        f'<uipath:context><uipath:input name="connection" type="string" value="{GUID}"/></uipath:context>'
        "</uipath:activity></bpmn:extensionElements></bpmn:task>"
    )
    root = ET.fromstring(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        f'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="Process_1">{intsvc}</bpmn:process></bpmn:definitions>'
    )
    assert checker.bare_connector_tasks(root) == []
    assert checker.intsvc_nodes(root) == []


def _write(tmp_path: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


NOTES = "Blockers: connection binding, dynamic input schemas, bindings_v2.json, package metadata."


@pytest.mark.parametrize(
    ("files", "ok"),
    [
        ({"README.md": "Draft notes."}, True),
        ({"Proj/NOTES.md": NOTES}, True),
        ({"README.md": "   "}, False),
        ({"CLAUDE.md": NOTES, "AGENTS.md": NOTES, "SKILL.md": NOTES}, False),
        ({"node_modules/pkg/README.md": NOTES, ".claude/skills/x/guide.md": NOTES}, False),
    ],
    ids=["any-wording", "beside-the-bpmn", "blank", "instruction-files", "installed-or-hidden"],
)
def test_require_notes_reads_only_the_agents_notes(tmp_path, monkeypatch, files, ok) -> None:
    _write(tmp_path, files)
    monkeypatch.chdir(tmp_path)
    if ok:
        checker.require_notes()
    else:
        with pytest.raises(SystemExit, match="no README or notes"):
            checker.require_notes()


@pytest.mark.parametrize(
    ("text", "missing"),
    [
        (NOTES, None),
        ("Needs the connection and its schema, then refresh.", "connection binding"),
        ("connection binding, dynamic schemas, bindings_v2.json", "package metadata"),
    ],
)
def test_notes_vocabulary_is_loose_but_named(tmp_path, monkeypatch, text, missing) -> None:
    _write(tmp_path, {"README.md": text})
    monkeypatch.chdir(tmp_path)
    if missing is None:
        checker.notes_vocabulary()
    else:
        with pytest.raises(SystemExit, match=missing):
            checker.notes_vocabulary()
