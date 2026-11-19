"""check_product_run.py grades its own debug run, built from a real one.

Fixtures come from Studio Web run adhoc-2026-11-17_15-00-15: the agent's
ProductCalc.bpmn and the debug + runtime-variables payloads of its run
(`Globals: {"Product": 42}`, a completed ScriptTask). variables-all returns
that scope inside `Data.Variables`; `codex_variables_all_2026-11-18.json` is a
real variables-all payload (codex nightly 2026-11-18_04-25-00).
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def _load():
    spec = importlib.util.spec_from_file_location("check_product_run", HERE / "check_product_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()
from _shared.bpmn_live import DebugEvidence  # noqa: E402  (importable once the checker set sys.path)
RUN = json.loads((FIXTURES / "sw_run_2026-11-17.json").read_text())
DEBUG = RUN["debug"]
VARIABLES_ALL = {"Variables": [RUN["variables_scope"]]}


def _sandbox(root: Path, bpmn_text: str | None = None) -> Path:
    project = root / "ProductCalc" / "ProductCalc"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "ProductCalc", "ProjectType": "ProcessOrchestration"}')
    (project / "ProductCalc.bpmn").write_text(bpmn_text or (FIXTURES / "ProductCalc.bpmn").read_text())
    return project


def _patch_live(monkeypatch, debug=DEBUG, variables=VARIABLES_ALL):
    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project, solution: project)
    monkeypatch.setattr(checker, "run_debug", lambda *a, **k: (debug, debug["InstanceId"]))
    monkeypatch.setattr(checker, "debug_evidence", lambda instance_id: DebugEvidence(variables, "", [], []))


def test_real_run_passes(tmp_path, monkeypatch):
    _sandbox(tmp_path)
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    checker.main()


def test_studio_web_process_bpmn_is_found(tmp_path, monkeypatch):
    project = _sandbox(tmp_path)
    (project / "ProductCalc.bpmn").rename(project / "Process.bpmn")
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    graded = []
    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project, solution: graded.append(bpmn.name) or project)
    checker.main()
    assert graded == ["Process.bpmn"]


def test_product_must_read_back_42(monkeypatch):
    wrong = copy.deepcopy(VARIABLES_ALL)
    wrong["Variables"][0]["Globals"]["Product"] = None
    with pytest.raises(checker.CheckFailure, match="not 42"):
        checker.assert_product(wrong)
    checker.assert_product(VARIABLES_ALL)


def test_product_is_read_by_its_declared_name_not_any_42():
    other = copy.deepcopy(VARIABLES_ALL)
    scope = other["Variables"][0]
    scope["Globals"] = {"Result": 42}
    scope["GlobalDefinitions"] = {"Result": {"Name": "result", "Type": "integer"}}
    with pytest.raises(checker.CheckFailure):
        checker.assert_product(other)


def test_a_run_without_a_completed_script_task_fails(tmp_path, monkeypatch):
    _sandbox(tmp_path)
    monkeypatch.chdir(tmp_path)
    debug = copy.deepcopy(DEBUG)
    debug["ElementExecutions"] = [e for e in debug["ElementExecutions"] if e["ElementType"] != "ScriptTask"]
    _patch_live(monkeypatch, debug=debug)
    with pytest.raises(checker.CheckFailure, match="no script task completed"):
        checker.main()


def test_hardcoded_answer_fails(tmp_path, monkeypatch):
    hardcoded = (FIXTURES / "ProductCalc.bpmn").read_text().replace("return 6 * 7;", "return 42;")
    _sandbox(tmp_path, hardcoded)
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    with pytest.raises(checker.CheckFailure, match="written into the process"):
        checker.main()


@pytest.mark.parametrize(
    "script",
    ["return 6 * 7; // 42", "return 6 * 7; /* 42 */", "/* product\n is 42 */\nreturn 6 * 7;"],
)
def test_a_42_in_a_comment_is_not_a_hardcoded_answer(tmp_path, monkeypatch, script):
    _sandbox(tmp_path, (FIXTURES / "ProductCalc.bpmn").read_text().replace("return 6 * 7;", script))
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    checker.main()


def test_a_hardcoded_answer_beside_a_comment_still_fails(tmp_path, monkeypatch):
    _sandbox(tmp_path, (FIXTURES / "ProductCalc.bpmn").read_text().replace("return 6 * 7;", "return 42; // 6 * 7"))
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    with pytest.raises(checker.CheckFailure, match="written into the process"):
        checker.main()


def test_a_real_variables_all_payload_reads_product_42():
    """codex nightly 2026-11-18_04-25-00: the agent saved the raw
    `debug-instance variables-all` output of its own run."""
    from _shared.bpmn_live import get_ci, parse_json_output

    payload = parse_json_output((FIXTURES / "codex_variables_all_2026-11-18.json").read_text(), "variables-all")
    checker.assert_product(get_ci(payload, "Data"))


@pytest.mark.parametrize("script", ["var u = 'a//b'; return 42;", 'var u = "a/*b*/"; return 42;', "var u = `//`; return 42;"])
def test_a_comment_marker_inside_a_string_does_not_hide_a_hardcoded_answer(tmp_path, monkeypatch, script):
    _sandbox(tmp_path, (FIXTURES / "ProductCalc.bpmn").read_text().replace("return 6 * 7;", script))
    monkeypatch.chdir(tmp_path)
    _patch_live(monkeypatch)
    with pytest.raises(checker.CheckFailure, match="written into the process"):
        checker.main()
