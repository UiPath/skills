"""Unit tests for graph_check.py. Run with ``pytest`` from any directory.

The decision-graph tasks grade what each decision returns by evaluating the
agent's tables in dependency order, and grade the diagram by comparing shape
positions. A regression here passes a wrong graph or fails a right one in
every task that imports it.
"""

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graph_check as gc  # noqa: E402
import rules_check as rc  # noqa: E402

TASKS = Path(__file__).resolve().parent.parent
FIXTURE = TASKS / "smoke" / "graph_extend_arranged" / "fixtures" / "LoanRules"
BROKEN = TASKS / "smoke" / "graph_repair" / "fixtures" / "LoanRules"
DMN = "Business rule.dmn"


def fixture_root(folder=FIXTURE):
    return ET.parse(folder / DMN).getroot()


def edited_root(old, new, folder=FIXTURE):
    text = (folder / DMN).read_text(encoding="utf-8")
    assert text.count(old) == 1
    return ET.fromstring(text.replace(old, new))


@pytest.fixture
def project(tmp_path, monkeypatch):
    shutil.copytree(FIXTURE, tmp_path / "LoanRules")
    monkeypatch.chdir(tmp_path)
    return tmp_path / "LoanRules"


class TestEvaluateGraph:
    def test_fixture_returns_the_loan_policy(self):
        gc.check_graph_cases(fixture_root(), gc.LOAN_CASES)

    def test_downstream_reads_the_upstream_result(self):
        outputs = gc.evaluate_graph(fixture_root(), {"creditScore": 650, "income": 60000, "loanAmount": 150000})
        assert outputs == {"riskBand": "Medium", "interestRate": 9.0}

    def test_wrong_value_fails(self):
        root = edited_root("<text>12.5</text>", "<text>13</text>")
        with pytest.raises(SystemExit):
            gc.check_graph_cases(root, gc.LOAN_CASES)

    def test_missing_output_fails(self):
        with pytest.raises(SystemExit):
            gc.check_graph_cases(fixture_root(), [({"creditScore": 1, "income": 1, "loanAmount": 1}, {"approved": True})])

    def test_cycle_fails(self):
        with pytest.raises(SystemExit):
            gc.evaluate_graph(fixture_root(BROKEN), {"creditScore": 650, "income": 60000, "loanAmount": 1})

    def test_requirement_on_a_missing_input_fails(self):
        root = edited_root('<requiredInput href="#inputData_loanAmount" />', '<requiredInput href="#inputData_amount" />')
        with pytest.raises(SystemExit):
            gc.evaluate_graph(root, {"creditScore": 650, "income": 60000, "loanAmount": 1})

    def test_reading_a_decision_without_requiring_it_fails(self):
        root = edited_root(
            '<informationRequirement id="informationRequirement_rate_risk">\n      <requiredDecision href="#decision_risk" />\n    </informationRequirement>',
            "",
        )
        with pytest.raises(SystemExit):
            gc.evaluate_graph(root, {"creditScore": 650, "income": 60000, "loanAmount": 1})

    def test_output_entry_passes_an_upstream_result_through(self):
        root = edited_root("<text>12.5</text>", "<text>risk</text>")
        outputs = gc.evaluate_graph(root, {"creditScore": 500, "income": 0, "loanAmount": 1})
        assert outputs == {"riskBand": "High", "interestRate": "High"}

    def test_upstream_without_a_match_reads_as_null(self):
        root = edited_root("<text>&gt;= 700</text>", "<text>&gt;= 900</text>")
        outputs = gc.evaluate_graph(root, {"creditScore": 750, "income": 0, "loanAmount": 1})
        assert outputs == {"riskBand": None, "interestRate": None}


class TestChain:
    def test_fixture_rate_requires_risk(self):
        gc.check_chain(fixture_root(), "interestRate", "riskBand")

    def test_reverse_direction_fails(self):
        with pytest.raises(SystemExit):
            gc.check_chain(fixture_root(), "riskBand", "interestRate")

    def test_unknown_output_fails(self):
        with pytest.raises(SystemExit):
            gc.decision_for_output(fixture_root(), "approved")


class TestDiagram:
    def test_shapes_are_read_by_element_id(self):
        assert gc.shapes(fixture_root())["decision_risk"] == (208.0, 304.0)

    def test_prefixed_and_hash_references_resolve(self):
        root = edited_root('dmnElementRef="decision_risk"', 'dmnElementRef="tns:decision_risk"')
        assert "decision_risk" in gc.shapes(root)
        root = edited_root('dmnElementRef="decision_risk"', 'dmnElementRef="#decision_risk"')
        assert "decision_risk" in gc.shapes(root)

    def test_unchanged_diagram_is_kept(self):
        gc.check_shapes_kept(fixture_root(), fixture_root())

    def test_moved_shape_fails(self):
        root = edited_root('<dc:Bounds x="208" y="304" width="288" height="96" />', '<dc:Bounds x="0" y="0" width="288" height="96" />')
        with pytest.raises(SystemExit):
            gc.check_shapes_kept(fixture_root(), root)

    def test_dropped_shape_fails(self):
        root = fixture_root()
        diagram = next(root.iter(f"{{{gc.DMNDI_NS}}}DMNDiagram"))
        diagram.remove(diagram[0])
        with pytest.raises(SystemExit):
            gc.check_shapes_kept(fixture_root(), root)

    def test_shape_of_a_removed_element_may_go(self):
        root = fixture_root()
        root.remove(next(e for e in root if e.get("id") == "inputData_loanAmount"))
        diagram = next(root.iter(f"{{{gc.DMNDI_NS}}}DMNDiagram"))
        diagram.remove(next(s for s in diagram if s.get("dmnElementRef") == "inputData_loanAmount"))
        gc.check_shapes_kept(fixture_root(), root)

    def test_fixture_has_no_overlap(self):
        gc.check_no_overlap(fixture_root())

    def test_overlap_is_measured_at_the_drawn_size(self):
        # 200 apart clears a 180-wide box in the file but not the 288-wide card the designer draws.
        root = edited_root('<dc:Bounds x="640" y="64" width="288" height="96" />', '<dc:Bounds x="408" y="304" width="180" height="80" />')
        with pytest.raises(SystemExit):
            gc.check_no_overlap(root)


class TestProject:
    def test_fixture_passes_the_chain_grade(self, project):
        gc.grade_chain()

    def test_fixture_rules_are_named(self, project):
        gc.check_all_named(rc.load_graph(project)[1])

    def test_load_rule_still_rejects_a_graph(self, project):
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_entry_points_kept(self, project):
        gc.check_entry_points_kept(project, FIXTURE)

    def test_new_unique_id_fails(self, project):
        path = project / "entry-points.json"
        path.write_text(path.read_text(encoding="utf-8").replace("7dc5b983", "00000000"), encoding="utf-8")
        with pytest.raises(SystemExit):
            gc.check_entry_points_kept(project, FIXTURE)

    def test_contract_missing_an_output_fails(self, project):
        dmn_file, _ = rc.load_graph(project)
        with pytest.raises(SystemExit):
            gc.check_whole_file_contract(project, dmn_file, gc.LOAN_INPUTS, {"approved": "boolean"})
