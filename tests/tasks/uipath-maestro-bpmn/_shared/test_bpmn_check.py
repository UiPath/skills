"""Unit tests for shared Maestro BPMN checker contracts."""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpmn_check  # noqa: E402
import pytest  # noqa: E402
from bpmn_check import (  # noqa: E402
    NS,
    all_node_values,
    context_value,
    has_type,
    has_typed_uipath_extension,
    has_uipath_extension,
)


def _service_task(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:serviceTask xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}" id="Task_1">{payload}</bpmn:serviceTask>'
    )


def test_typed_extension_accepts_nested_type_child() -> None:
    task = _service_task(
        """
        <bpmn:extensionElements>
          <uipath:activity version="v1">
            <uipath:type value="Orchestrator.StartJob" version="v1" />
          </uipath:activity>
        </bpmn:extensionElements>
        """
    )

    assert has_typed_uipath_extension(task, "activity", "Orchestrator.StartJob")
    assert has_uipath_extension(task, "Orchestrator.StartJob")


def test_typed_extension_accepts_registry_direct_type_attribute() -> None:
    task = _service_task(
        '<uipath:activity type="Orchestrator.StartAgentJob" version="v1" />'
    )

    assert has_typed_uipath_extension(task, "activity", "Orchestrator.StartAgentJob")
    assert has_uipath_extension(task, "Orchestrator.StartAgentJob")


def test_typed_extension_rejects_wrong_wrapper_or_type() -> None:
    task = _service_task(
        '<uipath:event type="Orchestrator.StartAgentJob" version="v1" />'
    )

    assert not has_typed_uipath_extension(task, "activity", "Orchestrator.StartAgentJob")
    assert not has_typed_uipath_extension(task, "event", "Orchestrator.StartJob")


def test_bundled_start_agent_contract_matches_runtime_registry() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    start_agent = spec["extensionTypes"]["Orchestrator.StartAgentJob"]

    assert [field["name"] for field in start_agent["contextFields"]] == [
        "name",
        "folderPath",
    ]
    assert start_agent["bindingInfo"]["contextField"] == "name"
    assert '<uipath:activity type="Orchestrator.StartAgentJob"' in start_agent[
        "xmlTemplate"
    ]
    assert "<bpmn:extensionElements>" not in start_agent["xmlTemplate"]
    assert "releaseKey" not in start_agent["xmlTemplate"]


def test_bundled_context_inputs_declare_a_type() -> None:
    """The canvas parser rejects a uipath:context input with no `type`, so a
    template pasted verbatim from the bundle would fail `validate`/`refresh`."""
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    untyped = []
    for name, extension in spec["extensionTypes"].items():
        template = extension.get("xmlTemplate") or ""
        if "<uipath:context>" not in template:
            continue
        context = template.split("<uipath:context>")[1].split("</uipath:context>")[0]
        declared = {field["name"]: field["type"] for field in extension["contextFields"]}
        # Opening tag only: a context input is self-closing or, for metadata,
        # wraps CDATA. The count guards the pattern against silently skipping one.
        tags = re.findall(r"<uipath:input\b[^>]*>", context)
        assert len(tags) == len(re.findall(r"<uipath:input\b", context)), (
            f"{name}: the input pattern skipped a context input"
        )
        for tag in tags:
            field = re.search(r'name="([^"]+)"', tag).group(1)
            match = re.search(r'type="([^"]+)"', tag)
            if match is None:
                untyped.append(f"{name}.{field}")
            elif field in declared:
                assert match.group(1) == declared[field], f"{name}.{field} type mismatch"

    assert not untyped, f"context inputs missing type=: {untyped}"


def test_bundled_intsvc_activity_contract_matches_cli_manifest() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    activity = spec["extensionTypes"]["Intsvc.ActivityExecution"]

    assert [field["name"] for field in activity["contextFields"]] == [
        "activityConfigurationVersion",
        "connectorKey",
        "connection",
        "folderKey",
        "operation",
        "objectName",
        "method",
        "path",
        "metadata",
    ]
    assert activity["outputName"] == "response"
    assert activity["outputType"] == "jsonSchema"
    assert activity["outputSource"] == "=response"
    assert activity["xmlTemplate"].startswith("<bpmn:sendTask")
    assert "=bindings.{connectionBindingId}" in activity["xmlTemplate"]


def test_bundled_intsvc_event_contracts_match_cli_manifest() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    for extension_type in ("Intsvc.EventTrigger", "Intsvc.WaitForEvent"):
        event = spec["extensionTypes"][extension_type]
        connection = next(
            field for field in event["inputFields"] if field["name"] == "connectionId"
        )
        assert connection["bindingInfo"] == {
            "resource": "Connection",
            "resourceKeyPattern": "${resourceKey}",
            "propertyAttribute": "ConnectionId",
        }
        assert "<uipath:context>" in event["xmlTemplate"]
        assert "=bindings.{connectionBindingId}" in event["xmlTemplate"]


def test_find_bpmn_file_without_hint_prefers_the_project_file(tmp_path, monkeypatch) -> None:
    """Two .bpmn files and no hint: the one beside project.uiproj wins.

    Flow graders aggregated over every ``*.flow``; BPMN graders that pass no
    name hint must not die on a stray draft or fixture copy.
    """
    project = tmp_path / "Proj"
    project.mkdir()
    (project / "Proj.bpmn").write_text("<x/>", encoding="utf-8")
    (project / "project.uiproj").write_text("{}", encoding="utf-8")
    (tmp_path / "draft.bpmn").write_text("<draft/>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert bpmn_check.find_bpmn_file().endswith("Proj/Proj.bpmn")

    (tmp_path / "project.uiproj").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        bpmn_check.find_bpmn_file()


def test_find_bpmn_file_with_hint_prefers_the_project_file(tmp_path, monkeypatch) -> None:
    """A hint narrows to a basename, not to a project.

    ``Proj-old.bpmn`` matches the hint ``Proj`` and sorts before ``Proj.bpmn``
    (``-`` is 0x2D, ``.`` is 0x2E), so returning the first match graded the
    stray draft -- the hazard resolve_project's docstring names.
    """
    project = tmp_path / "Proj"
    project.mkdir()
    (project / "Proj.bpmn").write_text("<x/>", encoding="utf-8")
    (project / "project.uiproj").write_text("{}", encoding="utf-8")
    (tmp_path / "Proj-old.bpmn").write_text("<x/>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert bpmn_check.find_bpmn_file("Proj").endswith("Proj/Proj.bpmn")

    # Two hint matches beside a project.uiproj: the rule cannot pick, so the
    # pre-existing first-match behaviour stands rather than a spurious FAIL.
    (tmp_path / "project.uiproj").write_text("{}", encoding="utf-8")
    assert bpmn_check.find_bpmn_file("Proj") == "Proj-old.bpmn"


def test_context_value_strips_and_falls_back_to_element_text() -> None:
    """One canonical reading of an input, so one artifact gets one verdict.

    The copies this replaced disagreed on whitespace: some stripped, some did
    not, so the same file read as two different values depending on which
    grader opened it.
    """
    task = _service_task(
        """
        <bpmn:extensionElements>
          <uipath:activity type="Intsvc.ActivityExecution">
            <uipath:context>
              <uipath:input name="objectName" value="  send_files_to_channel  " />
              <uipath:input name="path">
                /v1/messages
              </uipath:input>
              <uipath:input name="empty" value="" />
            </uipath:context>
          </uipath:activity>
        </bpmn:extensionElements>
        """
    )

    assert context_value(task, "objectName") == "send_files_to_channel"
    # No value attribute: the element text carries it, stripped the same way.
    assert context_value(task, "path") == "/v1/messages"
    # An empty value attribute falls through to the (absent) text, not to the
    # literal "" of the attribute -- either way the caller sees "".
    assert context_value(task, "empty") == ""
    assert context_value(task, "notThere") == ""
    # Exact name matching: a re-cased name is a miss, not a loose hit.
    assert context_value(task, "objectname") == ""
    # all_node_values is the raw sweep: it keeps the attribute verbatim and
    # strips only the text form, which is why callers substring-match on it.
    assert sorted(all_node_values(task)) == [
        "  send_files_to_channel  ",
        "/v1/messages",
    ]


def test_has_type_matches_any_token_in_the_serialised_node() -> None:
    task = _service_task(
        '<uipath:activity type="Intsvc.ActivityExecution" version="v1" />'
    )

    assert has_type(task, "Intsvc.ActivityExecution")
    assert not has_type(task, "Orchestrator.StartJob")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # The CLI quotes the identifier; this is the artifact that made CI run
        # 35538478362 fail with `found 0` score-sorted nodes.
        ("ORDER BY 'score' ASC", ("score", "asc")),
        ("ORDER BY score DESC", ("score", "desc")),
        ("order by [score]", ("score", "")),
        ('ORDER BY "score"', ("score", "")),
        ("`score`", ("", "")),
        ("('active' = true)", ("", "")),
        ("", ("", "")),
    ],
)
def test_order_by_reads_every_identifier_quoting(text: str, expected: tuple) -> None:
    assert bpmn_check.order_by(text) == expected


def test_order_by_accepts_backticked_identifier() -> None:
    assert bpmn_check.order_by("... ORDER BY `score` desc") == ("score", "desc")


def test_query_filter_text_excludes_binding_values() -> None:
    """The filter blob must not inherit an `=` from a binding reference.

    With every input value in the blob, `=bindings.Binding_DataFabricFolder`
    satisfied the `string` row's `equals|=` operator half for free, so the
    operator assertion could not fail.
    """
    import importlib.util

    here = Path(__file__).parent
    spec = importlib.util.spec_from_file_location(
        "_check_df_smoke_query_filter", here / "check_df_smoke_query_filter.py"
    )
    grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grader)

    task = ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{NS["bpmn"]}" xmlns:uipath="{NS["uipath"]}" id="Q">'
        "<bpmn:extensionElements><uipath:activity type=\"Intsvc.ActivityExecution\">"
        '<uipath:input name="folderKey" value="=bindings.Binding_DataFabricFolder" />'
        '<uipath:input name="queryExpression" target="query" '
        "value=\"'title' LIKE 'FilterFixture-Matrix'\" />"
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )
    _pairs, text = grader.node_representation(task)

    assert "=bindings" not in text
    assert "folderkey" not in text
    field, tokens, operators = grader.EXPECTED["string"]
    assert not grader.has_expected_filter(text, field, tokens, operators)
    # The same node with a real equality operator still passes.
    assert grader.has_expected_filter(
        text + " 'title' = 'filterfixture-matrix'", field, tokens, operators
    )


def _load(name: str):
    import importlib.util

    path = Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _outlook_receive_task(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:receiveTask xmlns:bpmn="{NS["bpmn"]}" xmlns:uipath="{NS["uipath"]}" '
        f'id="Wait_1"><bpmn:extensionElements><uipath:event '
        f'type="Intsvc.WaitForEvent">{payload}'
        "</uipath:event></bpmn:extensionElements></bpmn:receiveTask>"
    )


def test_waitfor_rejects_a_bare_filter_expression_string() -> None:
    """Flow rejects the bare string by design (MST-8802); the port must too.

    A text-blob fallback also let the three tokens come from three unrelated
    inputs, so "contain" could arrive inside an unrelated word.
    """
    grader = _load("check_outlook_waitfor_email")

    bare = _outlook_receive_task(
        '<uipath:input name="filterExpression" '
        "value=\"subject contains 'TestWaitFor'\" />"
    )
    assert not grader.has_subject_contains_filter(bare)

    scattered = _outlook_receive_task(
        '<uipath:input name="subject" value="container" />'
        '<uipath:input name="note" value="TestWaitFor" />'
    )
    assert not grader.has_subject_contains_filter(scattered)

    structured = _outlook_receive_task(
        '<uipath:input name="metadata" type="json"><![CDATA['
        '{"essentialConfiguration":{"filter":{"filters":['
        '{"id":"subject","operator":"Contains","value":"TestWaitFor"}]}}}'
        "]]></uipath:input>"
    )
    assert grader.has_subject_contains_filter(structured)


def test_validate_bpmn_fails_malformed_xml_without_calling_the_cli(tmp_path, monkeypatch) -> None:
    """`validate` tokenizes tolerantly, so the CLI cannot carry this criterion.

    An unbound namespace prefix is the case the skill calls out: the CLI
    reports Valid, a real parser does not.
    """
    validate_bpmn = _load("validate_bpmn")

    (tmp_path / "Broken.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
        '<bpmn:process id="p"><ghost:task id="t"/></bpmn:process></bpmn:definitions>',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def _no_cli(*args, **kwargs):
        raise AssertionError("CLI must not run on a file that does not parse")

    monkeypatch.setattr(validate_bpmn.subprocess, "run", _no_cli)

    assert validate_bpmn.main([]) == 1


def test_find_bpmn_file_without_hint_accepts_identical_copies(tmp_path, monkeypatch) -> None:
    """Two byte-identical .bpmn files, both beside a project.uiproj: one
    artifact, not ambiguity (the agent copied its scaffold into the solution
    wrapper on CI run 35538279757). Differing content still fails."""
    for d in ("Proj", "ProjSolution/Proj"):
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "Proj.bpmn").write_text("<x/>", encoding="utf-8")
        (tmp_path / d / "project.uiproj").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert bpmn_check.find_bpmn_file().endswith("Proj.bpmn")

    (tmp_path / "Proj" / "Proj.bpmn").write_text("<y/>", encoding="utf-8")
    with pytest.raises(SystemExit):
        bpmn_check.find_bpmn_file()


def test_resolve_project_excludes_the_live_run_copy(tmp_path, monkeypatch) -> None:
    """A live grader's ephemeral solution holds an imported copy of the
    project; ``exclude_under`` keeps it out of the candidate set."""
    for d in ("ProjSolution/Proj", "proj-live/ProjLiveEval/Proj"):
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "Proj.bpmn").write_text("<x/>", encoding="utf-8")
        (tmp_path / d / "project.uiproj").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        bpmn_check.resolve_project("Proj.bpmn")
    resolved = bpmn_check.resolve_project("Proj.bpmn", exclude_under=[Path("proj-live")])
    assert resolved == tmp_path / "ProjSolution" / "Proj"
