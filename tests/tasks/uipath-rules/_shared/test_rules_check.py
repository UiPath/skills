"""Unit tests for rules_check.py. Run with ``pytest`` from any directory.

The uipath-rules graders evaluate the agent's decision table themselves, so
what these pin is that evaluator: the FEEL unary tests, the hit policies, the
decision-keyed contract, and the DMN profile checks. A regression here passes
a wrong table or fails a right one in every task that imports it.
"""

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_check as rc  # noqa: E402

TASKS = Path(__file__).resolve().parent.parent
FIXTURE = TASKS / "integration" / "diagnose_wrong_output" / "fixtures" / "RiskRules"


def table(hit_policy, rows, inputs=("creditScore",), outputs=("riskBand",)):
    """A decisionTable element; each row is (input cells, output cells)."""
    policy = f' hitPolicy="{hit_policy}"' if hit_policy else ""
    xml = [f'<decisionTable xmlns="{rc.DMN_NS}"{policy}>']
    xml += [f"<input><inputExpression><text>{name}</text></inputExpression></input>" for name in inputs]
    xml += [f'<output name="{name}"/>' for name in outputs]
    for cells, values in rows:
        xml.append("<rule>")
        xml += [f"<inputEntry><text>{escape(cell)}</text></inputEntry>" for cell in cells]
        xml += [f"<outputEntry><text>{escape(value)}</text></outputEntry>" for value in values]
        xml.append("</rule>")
    xml.append("</decisionTable>")
    return ET.fromstring("".join(xml))


class TestUnaryTest:
    @pytest.mark.parametrize("cell, value, expected", [
        ("-", 1, True),
        ("", "anything", True),
        ("< 580", 579, True),
        ("< 580", 580, False),
        ("<= 580", 580, True),
        (">= 700", 700, True),
        ("> 700", 700, False),
        ("700", 700, True),
        ("= 700", 701, False),
        ("-5.5", -5.5, True),
        ("[580..700)", 580, True),
        ("[580..700)", 700, False),
        ("(580..700]", 580, False),
        ("(580..700]", 700, True),
        ("]580..700[", 650, True),
        ("< 10, > 90", 95, True),
        ("< 10, > 90", 50, False),
        ("true", True, True),
        ("false", True, False),
        ('"EU"', "EU", True),
        ('"EU"', "US", False),
    ])
    def test_evaluates(self, cell, value, expected):
        assert rc.unary_test(cell, value) is expected

    def test_boolean_is_not_a_number(self):
        with pytest.raises(SystemExit):
            rc.unary_test("< 5", True)

    def test_unsupported_expression_fails_loudly(self):
        with pytest.raises(SystemExit):
            rc.unary_test("not(5)", 5)


class TestLiteral:
    @pytest.mark.parametrize("text, expected", [
        ('"High"', "High"), ("42", 42.0), ("-1.5", -1.5), ("true", True), ("false", False), ("null", "null"),
    ])
    def test_parses(self, text, expected):
        assert rc.literal(text) == expected


class TestEvaluate:
    ROWS = [(["< 580"], ['"High"']), (["< 700"], ['"Medium"']), (["-"], ['"Low"'])]

    def test_first_takes_the_first_matching_row(self):
        assert rc.evaluate(table("FIRST", self.ROWS), {"creditScore": 500}) == {"riskBand": "High"}
        assert rc.evaluate(table("FIRST", self.ROWS), {"creditScore": 650}) == {"riskBand": "Medium"}
        assert rc.evaluate(table("FIRST", self.ROWS), {"creditScore": 800}) == {"riskBand": "Low"}

    def test_no_match_is_none(self):
        assert rc.evaluate(table("FIRST", [(["< 580"], ['"High"'])]), {"creditScore": 600}) is None

    def test_default_policy_is_unique(self):
        with pytest.raises(SystemExit):
            rc.evaluate(table("UNIQUE", self.ROWS), {"creditScore": 500})
        with pytest.raises(SystemExit):
            rc.evaluate(table(None, self.ROWS), {"creditScore": 500})

    def test_unique_without_overlap_passes(self):
        rows = [(["< 580"], ['"High"']), (["[580..700)"], ['"Medium"']), ([">= 700"], ['"Low"'])]
        assert rc.evaluate(table("UNIQUE", rows), {"creditScore": 700}) == {"riskBand": "Low"}

    def test_any_requires_agreeing_outputs(self):
        agreeing = [(["< 580"], ['"High"']), (["< 600"], ['"High"'])]
        assert rc.evaluate(table("ANY", agreeing), {"creditScore": 500}) == {"riskBand": "High"}
        with pytest.raises(SystemExit):
            rc.evaluate(table("ANY", self.ROWS), {"creditScore": 500})

    @pytest.mark.parametrize("policy", ["COLLECT", "PRIORITY", "RULE ORDER", "OUTPUT ORDER"])
    def test_multi_result_policies_are_rejected(self, policy):
        with pytest.raises(SystemExit):
            rc.evaluate(table(policy, self.ROWS), {"creditScore": 500})

    def test_row_with_wrong_cell_count_fails(self):
        with pytest.raises(SystemExit):
            rc.evaluate(table("FIRST", [(["< 580", "-"], ['"High"'])]), {"creditScore": 500})

    def test_check_cases_reports_the_wrong_band(self):
        rc.check_cases(table("FIRST", self.ROWS), "riskBand", [({"creditScore": 500}, "High")])
        with pytest.raises(SystemExit):
            rc.check_cases(table("FIRST", self.ROWS), "riskBand", [({"creditScore": 500}, "Low")])


class TestOutputProperties:
    def test_flat_schema(self):
        schema = {"properties": {"riskBand": {"type": "string"}}}
        assert rc.output_properties(schema) == {"riskBand": {"type": "string"}}

    def test_decision_keyed_schema_is_flattened(self):
        schema = {
            "x-uipath-decision-keyed": True,
            "properties": {"decision1": {"type": "object", "properties": {"riskBand": {"type": "string"}}}},
        }
        assert rc.output_properties(schema) == {"riskBand": {"type": "string"}}


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A copy of the RiskRules fixture with the sandbox as the working directory."""
    shutil.copytree(FIXTURE, tmp_path / "RiskRules")
    monkeypatch.chdir(tmp_path)
    return tmp_path / "RiskRules"


def dmn_of(project):
    return next(project.glob("*.dmn"))


class TestProject:
    def test_finds_the_project_by_name(self, project):
        assert rc.find_project().resolve() == project.resolve()

    def test_missing_project_fails(self, project):
        with pytest.raises(SystemExit):
            rc.find_project("OtherRules")

    def test_fixture_passes_the_profile_and_contract(self, project):
        dmn_file, root = rc.load_rule(project)
        rc.check_input_data(root, rc.POLICY_INPUTS)
        entry = rc.check_contract(project, dmn_file, root, rc.POLICY_INPUTS, rc.POLICY_OUTPUTS)
        assert entry["filePath"].startswith(f"/{dmn_file.name}#")

    @pytest.mark.parametrize("injected", [
        "<!-- note -->",
        "<?pi data?>",
    ])
    def test_rejects_comments_and_processing_instructions(self, project, injected):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("<extensionElements>", injected + "<extensionElements>", 1), encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_rejects_a_second_dmn(self, project):
        shutil.copy(dmn_of(project), project / "Copy.dmn")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_rejects_a_second_decision(self, project):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("</definitions>", '<decision id="d2" name="d2"/></definitions>'), encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_rejects_a_business_knowledge_model(self, project):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("</definitions>", '<businessKnowledgeModel id="b" name="b"/></definitions>'), encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_renamed_decision_id_breaks_the_contract(self, project):
        dmn_file, root = rc.load_rule(project)
        rc.decision_of(root).set("id", "decision_renamed")
        with pytest.raises(SystemExit):
            rc.check_contract(project, dmn_file, root, rc.POLICY_INPUTS, rc.POLICY_OUTPUTS)

    def test_contract_missing_an_input_fails(self, project):
        dmn_file, root = rc.load_rule(project)
        with pytest.raises(SystemExit):
            rc.check_contract(project, dmn_file, root, {**rc.POLICY_INPUTS, "age": "number"}, rc.POLICY_OUTPUTS)

    def test_missing_input_data_fails(self, project):
        _, root = rc.load_rule(project)
        with pytest.raises(SystemExit):
            rc.check_input_data(root, {"age": "number"})
