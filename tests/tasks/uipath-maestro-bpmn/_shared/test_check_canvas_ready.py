"""Unit tests for check_canvas_ready --check js: what counts as an authored plain `=`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GRADER = Path(__file__).parents[1] / "expressions" / "canvas_ready" / "check_canvas_ready.py"
NS = 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn"'
DECLS = (
    '<uipath:variables><uipath:input id="amount" elementId="start"/>'
    '<uipath:inputOutput id="decision" elementId="review"/></uipath:variables>'
)


def _row(source: str) -> str:
    return f'<bpmn:extensionElements><uipath:output name="x" source=\'{source}\' var="x"/></bpmn:extensionElements>'


# Every case but "no authored expression" also carries one =js: expression.
COMPUTED = f'<bpmn:scriptTask id="calc">{_row("=js:vars.amount * 2")}</bpmn:scriptTask>'


def _grade(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    project = tmp_path / "P"
    project.mkdir()
    (project / "project.uiproj").write_text("{}")
    (project / "P.bpmn").write_text(
        f'<bpmn:definitions {NS}><bpmn:process id="p"><bpmn:extensionElements>{DECLS}'
        f"</bpmn:extensionElements>{body}</bpmn:process></bpmn:definitions>"
    )
    return subprocess.run(
        [sys.executable, str(GRADER), "P.bpmn", "--check", "js"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )


HITL_ARGS = (
    '<bpmn:extensionElements><uipath:input name="HitlTaskArguments" type="json">'
    '<![CDATA[{"x":"=vars.amount"}]]></uipath:input></bpmn:extensionElements>'
)

NONE = '<bpmn:task id="t"/>'

CASES = [
    ("form field read on a human task", f'<bpmn:userTask id="review">{_row("=decision")}</bpmn:userTask>', True),
    ("same read off a human task", f'<bpmn:serviceTask id="t">{_row("=decision")}</bpmn:serviceTask>', False),
    ("plain literal", f'<bpmn:task id="t">{_row("=true")}</bpmn:task>', False),
    ("human-task form input", f'<bpmn:userTask id="review">{HITL_ARGS}</bpmn:userTask>', True),
    ("plain arithmetic", f'<bpmn:scriptTask id="t">{_row("=vars.total * 0.9")}</bpmn:scriptTask>', False),
    ("=js: arithmetic", f'<bpmn:scriptTask id="t">{_row("=js:vars.total * 0.9")}</bpmn:scriptTask>', True),
    ("start-event input bridge", f'<bpmn:startEvent id="start">{_row("=vars.amount")}</bpmn:startEvent>', True),
    ("input read downstream", f'<bpmn:endEvent id="done">{_row("=vars.amount")}</bpmn:endEvent>', False),
    ("node result", f'<bpmn:scriptTask id="t">{_row("=result.response")}</bpmn:scriptTask>', True),
    ("bracket result read", '<bpmn:serviceTask id="t">' + _row('=this["test-123"]') + "</bpmn:serviceTask>", True),
    ("raw backslash bracket read", '<bpmn:serviceTask id="t">' + _row('=this["a\\b c"]') + "</bpmn:serviceTask>", True),
    ("bracket read of a key with a quote", '<bpmn:serviceTask id="t">' + _row('=this["a&quot;b"]') + "</bpmn:serviceTask>", False),
    ("bracket read of a key ending in a backslash", '<bpmn:serviceTask id="t">' + _row('=this["a\\"]') + "</bpmn:serviceTask>", True),
    ("computed bracket read", '<bpmn:serviceTask id="t">' + _row('=this["a"] + vars.b') + "</bpmn:serviceTask>", False),
    (
        "bracket read on an input",
        '<bpmn:serviceTask id="t"><bpmn:extensionElements><uipath:input name="a">=this["test-123"]</uipath:input>'
        "</bpmn:extensionElements></bpmn:serviceTask>",
        False,
    ),
    (
        "bracket read as a condition",
        '<bpmn:sequenceFlow id="f"><bpmn:conditionExpression>=this["test-123"]</bpmn:conditionExpression></bpmn:sequenceFlow>',
        False,
    ),
    (
        "plain gateway condition",
        '<bpmn:sequenceFlow id="f"><bpmn:conditionExpression>=vars.amount &gt; 5</bpmn:conditionExpression></bpmn:sequenceFlow>',
        False,
    ),
    (
        "plain expression in a JSON body",
        '<bpmn:serviceTask id="t"><bpmn:extensionElements><uipath:input name="body" type="json">'
        '<![CDATA[{"x":"=vars.total * 2"}]]></uipath:input></bpmn:extensionElements></bpmn:serviceTask>',
        False,
    ),
    ("computed result read", f'<bpmn:scriptTask id="t">{_row("=result.a + result.b")}</bpmn:scriptTask>', False),
    ("computed iterator read", f'<bpmn:scriptTask id="t">{_row("=iterator[0] + vars.tot")}</bpmn:scriptTask>', False),
    (
        "literal names and documentation",
        '<bpmn:scriptTask id="t" name="=vars.missing"><bpmn:documentation>=vars.total * 2</bpmn:documentation>'
        '<bpmn:extensionElements><uipath:output name="=vars.x" source="=js:vars.total" var="x"/>'
        "</bpmn:extensionElements></bpmn:scriptTask>",
        True,
    ),
    ("no authored expression", NONE, False),
    ("agent output read", f'<bpmn:serviceTask id="t">{_row("=Decision")}</bpmn:serviceTask>', True),
    (
        "canvas-written reads",
        f'<bpmn:serviceTask id="t">{_row("=bindings.b1")}{_row("=iterator[0]")}{_row("=jsonString:{}")}</bpmn:serviceTask>',
        True,
    ),
    (
        "script envelope",
        '<bpmn:scriptTask id="t"><bpmn:extensionElements><uipath:input name="args" type="json">'
        '<![CDATA[{"vars":"=vars","metadata":"=metadata"}]]></uipath:input></bpmn:extensionElements></bpmn:scriptTask>',
        True,
    ),
]


@pytest.mark.parametrize("body,ok", [(b, ok) for _, b, ok in CASES], ids=[c[0] for c in CASES])
def test_js_check(tmp_path: Path, body: str, ok: bool) -> None:
    result = _grade(tmp_path, body if body == NONE else COMPUTED + body)
    out = result.stdout + result.stderr
    assert (result.returncode == 0) is ok, out
    assert ok or "not written as =js:" in out or "no =js: expression" in out, out


def _scope(tmp_path: Path, data: dict) -> subprocess.CompletedProcess[str]:
    """Run --check scope against a stub `uip` that prints the given validate Data."""
    import json
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "uip"
    stub.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps({'Result': 'Success', 'Data': data})}\nEOF\n")
    stub.chmod(0o755)
    project = tmp_path / "P"
    project.mkdir()
    (project / "project.uiproj").write_text("{}")
    (project / "P.bpmn").write_text(f'<bpmn:definitions {NS}><bpmn:process id="p"/></bpmn:definitions>')
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(
        [sys.executable, str(GRADER), "P.bpmn", "--check", "scope"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, env=env,
    )


SCOPE_CASES = [
    ("no warnings", {"Status": "Valid"}, True),
    ("unrelated warning", {"Status": "Valid", "Warnings": "1 warning(s):\n  - [(xml)] unknown attribute <type>"}, True),
    (
        "input read downstream",
        {"Status": "Valid", "Warnings": "1 warning(s):\n  - [Event_done] VARIABLE_NOT_SET: Variable 'amount' is not set at this point in the flow"},
        False,
    ),
    ("warnings in a new shape", {"Status": "Valid", "Warnings": [{"code": "VARIABLE_NOT_SET"}]}, False),
    ("unreadable warning line", {"Status": "Valid", "Warnings": "1 warning(s):\n  VARIABLE_NOT_SET at Event_done"}, False),
    ("no status", {}, False),
]


@pytest.mark.parametrize("data,ok", [(d, ok) for _, d, ok in SCOPE_CASES], ids=[c[0] for c in SCOPE_CASES])
def test_scope_check_fails_closed(tmp_path: Path, data: dict, ok: bool) -> None:
    result = _scope(tmp_path, data)
    assert (result.returncode == 0) is ok, result.stdout + result.stderr
