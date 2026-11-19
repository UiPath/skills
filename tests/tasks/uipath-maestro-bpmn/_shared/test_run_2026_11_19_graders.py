"""Graders that failed correct Studio Web output in run 2026-11-19_09-23-02.

Fixtures under ``fixtures/run_2026_11_19`` are the agents' real artifacts from that
run, byte for byte. Each positive test names the construct the canvas accepts and the
grader used to reject; each negative test changes that construct to something the
canvas does not read the same way and must still fail.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpmn_check  # noqa: E402

FIXTURES = HERE / "fixtures" / "run_2026_11_19"
SIMPLE_APPROVAL = HERE / "check_simple_approval_bpmn.py"
SCRIPT_JINT = HERE / "check_script_jint_guidance.py"

END_MAPPING = '<uipath:output name="decision" type="string" source="=js:vars.decisionValue" var="decision" />'
JINT_END_MAPPING = '<uipath:output name="riskScore" type="number" source="=js:vars.riskScoreValue" var="riskScore" />'


def _run(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True)


def _copy(tmp_path: Path, fixture: str) -> Path:
    shutil.copytree(FIXTURES / fixture, tmp_path, dirs_exist_ok=True)
    return tmp_path


def _bpmn(root: Path) -> Path:
    (path,) = root.rglob("Process.bpmn")
    return path


def _edit(root: Path, old: str, new: str) -> None:
    path = _bpmn(root)
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new), encoding="utf-8")


# ---- 1. `=js:vars.<id>` --------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "fields", "expected"),
    [
        ("=vars.a", False, "a"),
        ("=js:vars.a", False, "a"),
        (" =js: vars.a ", False, "a"),
        ("=js:vars.a.b", True, "a.b"),
        ("=js:vars.a.b", False, None),
        ("=js:vars.a + 1", True, None),
        ("=js:vars.a; vars.b", True, None),
        ("=vars", False, None),
        ("vars.a", False, None),
        ("=js:$vars.a", False, None),
        ("=result.response", False, None),
        ("", False, None),
        (None, False, None),
    ],
)
def test_vars_ref(value: str | None, fields: bool, expected: str | None) -> None:
    assert bpmn_check.vars_ref(value, fields=fields) == expected


def test_simple_approval_accepts_js_end_mapping(tmp_path: Path) -> None:
    root = _copy(tmp_path, "simple_approval")
    assert END_MAPPING in _bpmn(root).read_text(encoding="utf-8")
    result = _run(SIMPLE_APPROVAL, root)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "bad",
    [
        'source="=js:vars.decisionValue + \'x\'"',  # a script, not a read of the variable
        'source="=js:vars.notDeclared"',  # reads a variable that does not exist
        'source="decisionValue"',  # no expression prefix
    ],
)
def test_simple_approval_still_rejects_wrong_end_mapping(tmp_path: Path, bad: str) -> None:
    root = _copy(tmp_path, "simple_approval")
    _edit(root, 'source="=js:vars.decisionValue"', bad)
    result = _run(SIMPLE_APPROVAL, root)
    assert result.returncode == 1
    assert result.stderr.startswith("FAIL:")


def test_simple_approval_still_requires_the_end_mapping(tmp_path: Path) -> None:
    root = _copy(tmp_path, "simple_approval")
    _edit(root, END_MAPPING, "")
    result = _run(SIMPLE_APPROVAL, root)
    assert result.returncode == 1
    assert "bridge mutable 'decision'" in result.stderr


def test_script_jint_accepts_js_end_mapping_and_start_scoped_inputs(tmp_path: Path) -> None:
    # Both constructs at once, as the agent wrote them: `=js:vars.<id>` on the end
    # event and the mutable inputs scoped to the start event (#4891, #4892).
    root = _copy(tmp_path, "script_jint")
    text = _bpmn(root).read_text(encoding="utf-8")
    assert JINT_END_MAPPING in text
    assert 'id="amountIn" name="amountIn" type="number" elementId="Event_start"' in text
    result = _run(SCRIPT_JINT, root)
    assert result.returncode == 0, result.stderr


def test_script_jint_still_rejects_wrong_end_expression(tmp_path: Path) -> None:
    root = _copy(tmp_path, "script_jint")
    _edit(root, 'source="=js:vars.riskScoreValue"', 'source="=js:vars.riskScoreValue * 2"')
    result = _run(SCRIPT_JINT, root)
    assert result.returncode == 1


# ---- 2. start-event-scoped inputs ----------------------------------------------------


def test_script_jint_still_rejects_input_scoped_to_another_element(tmp_path: Path) -> None:
    root = _copy(tmp_path, "script_jint")
    _edit(
        root,
        '<uipath:inputOutput id="amountIn" name="amountIn" type="number" elementId="Event_start" />',
        '<uipath:inputOutput id="amountIn" name="amountIn" type="number" elementId="Event_end" />',
    )
    result = _run(SCRIPT_JINT, root)
    assert result.returncode == 1
    assert "amountIn" in result.stderr


def test_script_jint_still_rejects_unscoped_input(tmp_path: Path) -> None:
    root = _copy(tmp_path, "script_jint")
    _edit(
        root,
        '<uipath:inputOutput id="amountIn" name="amountIn" type="number" elementId="Event_start" />',
        '<uipath:inputOutput id="amountIn" name="amountIn" type="number" />',
    )
    assert _run(SCRIPT_JINT, root).returncode == 1


# ---- 3. stale scratch copy -----------------------------------------------------------


def _scratch_workspace(tmp_path: Path) -> Path:
    shutil.copy(FIXTURES / "escalation_preserve" / "root-ExpenseClaim.bpmn", tmp_path / "ExpenseClaim.bpmn")
    work = tmp_path / "ExpenseClaim-work"
    work.mkdir()
    shutil.copy(FIXTURES / "escalation_preserve" / "work-ExpenseClaim.bpmn", work / "ExpenseClaim.bpmn")
    return tmp_path


def test_find_bpmn_file_prefers_the_shallowest_exact_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_scratch_workspace(tmp_path))
    assert bpmn_check.find_bpmn_file("ExpenseClaim") == "ExpenseClaim.bpmn"


def test_find_bpmn_file_still_rejects_ambiguous_unhinted_copies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_scratch_workspace(tmp_path))
    with pytest.raises(SystemExit):
        bpmn_check.find_bpmn_file()


def test_find_bpmn_file_keeps_scratch_suffix_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_scratch_workspace(tmp_path))
    shutil.copy("ExpenseClaim.bpmn", "ExpenseClaim.original.bpmn")
    assert bpmn_check.find_bpmn_file("ExpenseClaim") == "ExpenseClaim.bpmn"


# ---- 5. Studio Web layout ------------------------------------------------------------


def test_resolve_bpmn_file_finds_studio_web_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "CustomerEscalationTriage" / "CustomerEscalationTriage"
    project.mkdir(parents=True)
    (project / "Process.bpmn").write_text("<x/>")
    (project / "project.uiproj").write_text("{}")
    monkeypatch.chdir(tmp_path)
    found = bpmn_check.resolve_bpmn_file("CustomerEscalationTriage.bpmn")
    assert found.relative_to(tmp_path) == Path("CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn")


def test_print_bpmn_path_resolves_both_layouts(tmp_path: Path) -> None:
    script = HERE / "print_bpmn_path.py"
    studio = tmp_path / "a" / "P" / "P"
    studio.mkdir(parents=True)
    (studio / "Process.bpmn").write_text("<x/>")
    (studio / "project.uiproj").write_text("{}")
    assert _run(script, tmp_path / "a", "P.bpmn").stdout.strip() == "P/P/Process.bpmn"
    node = tmp_path / "b" / "PSolution" / "P"
    node.mkdir(parents=True)
    (node / "P.bpmn").write_text("<x/>")
    (node / "project.uiproj").write_text("{}")
    assert _run(script, tmp_path / "b", "P.bpmn").stdout.strip() == "PSolution/P/P.bpmn"
    twin = tmp_path / "a" / "Other" / "P"
    twin.mkdir(parents=True)
    (twin / "Process.bpmn").write_text("<x/>")
    (twin / "project.uiproj").write_text("{}")
    assert _run(script, tmp_path / "a", "P.bpmn").returncode == 1  # two Studio Web projects: ambiguous


# ---- 1. bpmn_live --------------------------------------------------------------------


def test_input_echo_ids_follows_js_bridges() -> None:
    import xml.etree.ElementTree as ET

    import bpmn_live

    xml = f"""<bpmn:definitions xmlns:bpmn="{bpmn_live.BPMN_NS}" xmlns:uipath="{bpmn_live.UIPATH_NS}">
<bpmn:process id="Process_1"><bpmn:startEvent id="Start"><bpmn:extensionElements>
<uipath:output name="a" var="Var_A" source="=js:vars.input_A"/>
<uipath:output name="b" var="Var_B" source="=js:vars.input_A + 1"/>
</bpmn:extensionElements></bpmn:startEvent>
<bpmn:extensionElements><uipath:variables><uipath:input id="input_A" name="A" elementId="Start"/></uipath:variables></bpmn:extensionElements>
</bpmn:process></bpmn:definitions>"""
    process = ET.fromstring(xml).find(bpmn_live.q(bpmn_live.BPMN_NS, "process"))
    ids = bpmn_live.input_echo_ids(process)
    assert "Var_A" in ids
    assert "Var_B" not in ids  # a computed value is not an echo


