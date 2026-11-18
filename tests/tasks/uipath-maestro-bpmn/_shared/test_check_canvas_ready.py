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
    result = _grade(tmp_path, body)
    out = result.stdout + result.stderr
    assert (result.returncode == 0) is ok, out
    assert ok or "not written as =js:" in out, out
