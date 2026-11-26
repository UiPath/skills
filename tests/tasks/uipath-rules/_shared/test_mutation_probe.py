"""The mutation probe must never delete anything outside its own temp directory.

The probe copies the solution, rewrites the knowledge model's body to a constant and re-runs the
engine, then removes the copy in a `finally`. It derived that `finally`'s target from
`project.parent.name`, which the root-level layout `uip solution init .` produces leaves empty —
the solution *is* the sandbox, so the project's parent has no name. The copy then became the temp
root itself, its parent became the sandbox, and the cleanup deleted the grader's whole working
directory: the agent's project, the fixtures, everything.

That is unrecoverable and silent (`ignore_errors=True`), so both layouts are pinned here, and the
probe is run through to its own `finally` in each.
"""

import json
import sys
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SUITE / "e2e" / "graph_formula_and_model_debug"))

import check_graph_formula_and_model_debug as probe  # noqa: E402
import rules_check as rc  # noqa: E402

FEE_RULES = f'''<?xml version="1.0" encoding="UTF-8" ?>
<definitions xmlns="{rc.DMN_NS}" xmlns:uipath="{rc.UIPATH_NS}" id="d" name="FeeRules"
             namespace="urn:fee">
  <extensionElements><uipath:authoring surface="{rc.GRAPH_SURFACE}" /></extensionElements>
  <decision id="decision_fee" name="fee">
    <variable id="v_fee" name="fee" typeRef="number"/>
    <informationRequirement id="ir_fee"><requiredInput href="#inputData_loanAmount"/></informationRequirement>
    <knowledgeRequirement id="kr_fee"><requiredKnowledge href="#bkm_rate"/></knowledgeRequirement>
    <literalExpression id="le_fee" typeRef="number"><text>loanAmount * rate(loanAmount)</text></literalExpression>
  </decision>
  <businessKnowledgeModel id="bkm_rate" name="rate">
    <variable id="v_rate" name="rate" typeRef="number"/>
    <encapsulatedLogic>
      <formalParameter id="fp_amount" name="amount" typeRef="number"/>
      <literalExpression id="le_rate"><text>0.02</text></literalExpression>
    </encapsulatedLogic>
  </businessKnowledgeModel>
  <inputData id="inputData_loanAmount" name="loanAmount">
    <variable id="vi_amount" name="loanAmount" typeRef="number"/></inputData>
</definitions>'''


def _project(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "project.uiproj").write_text(
        json.dumps({"Name": "FeeRules", "ProjectType": "BusinessRules"}), encoding="utf-8")
    (folder / "Business rule.dmn").write_text(FEE_RULES, encoding="utf-8")
    return folder


@pytest.fixture
def engine(monkeypatch):
    """`engine_outputs` answering as a fee the model really computes would."""
    monkeypatch.setattr(probe, "engine_outputs",
                        lambda project, inputs: {"fee": inputs["loanAmount"] * probe.PROBE_RATE})


def _sandbox_contents(sandbox: Path) -> set[str]:
    return {p.relative_to(sandbox).as_posix() for p in sandbox.rglob("*")
            if probe.PROBE_PREFIX not in p.relative_to(sandbox).as_posix()}


class TestTheProbeDeletesOnlyItsOwnCopy:

    def test_the_root_level_solution_layout_survives(self, tmp_path, engine, monkeypatch):
        # `uip solution init .`: the solution IS the sandbox, so `project.parent.name` is "".
        # This is the layout that made the cleanup delete the working directory.
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        monkeypatch.chdir(sandbox)
        project = _project(Path("FeeRules"))
        Path("FeeRules.uipx").write_text("{}", encoding="utf-8")
        (sandbox / "fixtures").mkdir()
        (sandbox / "fixtures" / "policy.md").write_text("do not delete me", encoding="utf-8")
        before = _sandbox_contents(sandbox)
        assert project.parent.name == "", "the layout under test is the one with no parent name"

        probe._fee_follows_the_model(project)

        assert _sandbox_contents(sandbox) == before
        assert (sandbox / "fixtures" / "policy.md").read_text(encoding="utf-8") == "do not delete me"
        assert (project / "Business rule.dmn").read_text(encoding="utf-8") == FEE_RULES

    def test_a_grader_that_fails_mid_probe_still_deletes_only_its_copy(self, tmp_path, monkeypatch):
        # The `finally` runs on the failure path too, which is where the wrong target bit.
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        monkeypatch.chdir(sandbox)
        project = _project(Path("FeeRules"))
        monkeypatch.setattr(probe, "engine_outputs",
                            lambda p, i: {"fee": 1.0})  # not what the probed model would answer
        before = _sandbox_contents(sandbox)

        with pytest.raises(SystemExit):
            probe._fee_follows_the_model(project)

        assert _sandbox_contents(sandbox) == before

    def test_the_probe_rewrites_only_its_copy(self, tmp_path, monkeypatch):
        # What the copy exists for: the agent's own file must read the same afterwards, whatever
        # the probe did to the model's body.
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        monkeypatch.chdir(sandbox)
        project = _project(Path("FeeRules"))
        seen = {}

        def record(copied, inputs):
            seen["body"] = (copied / "Business rule.dmn").read_text(encoding="utf-8")
            return {"fee": inputs["loanAmount"] * probe.PROBE_RATE}

        monkeypatch.setattr(probe, "engine_outputs", record)

        probe._fee_follows_the_model(project)

        assert str(probe.PROBE_RATE) in seen["body"], "the copy was not mutated"
        assert "0.02" in (project / "Business rule.dmn").read_text(encoding="utf-8")
