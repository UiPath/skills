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
import pathlib
import sys
import xml.etree.ElementTree as ET
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


class TestTheRewrittenCopyIsReadable:
    """Whatever the probe writes, the engine has to be able to read.

    `_write` re-declares the prefixes the file carried, because one used only inside an attribute
    value (`tns:` in a `dmnElementRef`) is invisible to ElementTree and its declaration would be
    dropped. Declaring a prefix ElementTree *does* emit writes the same `xmlns:` twice, and a
    duplicate attribute is not well-formed XML. Every rule this task accepts carries
    `uipath:authoring`, so getting that wrong corrupted every correct submission before the engine
    was asked anything — and the probe then reported the fee as not following the model.
    """

    DMNDI = "https://www.omg.org/spec/DMN/20230324/DMNDI/"

    def _write_and_read(self, tmp_path, xml: str) -> str:
        path = tmp_path / "Business rule.dmn"
        path.write_text(xml, encoding="utf-8")
        root = ET.fromstring(xml)
        probe._model_answers(root, "bkm_rate", probe.PROBE_RATE)
        probe._write(path, root)
        written = path.read_text(encoding="utf-8")
        ET.fromstring(written)      # the engine's first act; a ParseError here is the defect
        return written

    def test_a_rule_carrying_only_the_authoring_marker_round_trips(self, tmp_path):
        # The shape of every accepted submission: no diagram, but `uipath:authoring` is always
        # there, so this is the case that corrupted all of them.
        assert "surface" in self._write_and_read(tmp_path, FEE_RULES)

    def test_a_prefix_used_only_in_an_attribute_value_is_kept(self, tmp_path):
        # `tns:` appears nowhere ElementTree can see it, so without a literal declaration the
        # reference binds to nothing.
        xml = FEE_RULES.replace(
            'namespace="urn:fee">',
            'xmlns:tns="urn:fee" xmlns:dmndi="%s" namespace="urn:fee">' % self.DMNDI
        ).replace("</definitions>",
                  '<dmndi:DMNDI><dmndi:DMNShape id="s" dmnElementRef="tns:decision_fee"/>'
                  '</dmndi:DMNDI></definitions>')

        written = self._write_and_read(tmp_path, xml)

        assert 'xmlns:tns="urn:fee"' in written
        assert 'dmnElementRef="tns:decision_fee"' in written

    def test_no_namespace_is_declared_twice(self, tmp_path):
        import re
        xml = FEE_RULES.replace('namespace="urn:fee">',
                                'xmlns:dmndi="%s" namespace="urn:fee">' % self.DMNDI)
        written = self._write_and_read(tmp_path, xml)

        root_tag = written[written.index("<definitions"):written.index(">", written.index("<definitions"))]
        declarations = re.findall(r'xmlns:?[\w-]*="[^"]*"', root_tag)
        assert len(declarations) == len(set(declarations)), declarations

    def test_a_copy_the_probe_cannot_parse_is_a_probe_defect(self, tmp_path, monkeypatch, capsys):
        # The guard itself: if a future rewrite breaks the file, that must read as the probe
        # breaking, never as the agent's fee ignoring the model.
        path = tmp_path / "Business rule.dmn"
        path.write_text(FEE_RULES, encoding="utf-8")
        monkeypatch.setattr(probe.ET.ElementTree, "write",
                            lambda self, f, **kw: pathlib.Path(f).write_text("<a><b></a>", encoding="utf-8"))

        with pytest.raises(SystemExit) as raised:
            probe._write(path, ET.fromstring(FEE_RULES))

        assert raised.value.code == probe.PROBE_DEFECT_EXIT
        assert "does not parse" in capsys.readouterr().out
