"""Unit tests for rules_check.py. Run with ``pytest`` from any directory.

The uipath-rules graders evaluate the agent's decision table themselves, so
what these pin is that evaluator: the FEEL unary tests, the hit policies, the
decision-keyed contract, and the DMN profile checks. A regression here passes
a wrong table or fails a right one in every task that imports it.
"""

import json
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
            rc.unary_test('starts with("a")', 5)

    @pytest.mark.parametrize("cell, value, expected", [
        ('"High", "Medium"', "Medium", True),
        ('"High","Medium"', "Low", False),
        ('"a,b"', "a,b", True),
        ('not("High")', "Low", True),
        ('not("High", "Medium")', "Medium", False),
        ("not(< 10)", 5, False),
        ('"High"', None, False),
        ("< 10", None, False),
        ("-", None, True),
    ])
    def test_lists_negation_and_null(self, cell, value, expected):
        assert rc.unary_test(cell, value) is expected


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

    def test_accepts_a_business_knowledge_model(self, project):
        # Supported since the profile widened; a model is graded by check_knowledge_models.
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("</definitions>", '<businessKnowledgeModel id="b" name="b"/></definitions>'), encoding="utf-8")
        rc.load_rule(project)

    def test_rejects_a_knowledge_source(self, project):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("</definitions>", '<knowledgeSource id="k" name="k"/></definitions>'), encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_accepts_a_decision_whose_logic_is_a_literal_expression(self, project):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        table_start = text.index("<decisionTable")
        table_end = text.index("</decisionTable>") + len("</decisionTable>")
        literal = '<literalExpression id="le" typeRef="number"><text>1</text></literalExpression>'
        path.write_text(text[:table_start] + literal + text[table_end:], encoding="utf-8")
        rc.load_rule(project)

    def test_rejects_a_decision_with_no_logic_at_all(self, project):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        table_start = text.index("<decisionTable")
        table_end = text.index("</decisionTable>") + len("</decisionTable>")
        path.write_text(text[:table_start] + text[table_end:], encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)

    def test_the_designers_type_constructors_are_literals(self):
        # Critical Rule 5 offers these as column types, so a cell spelling one is not a call.
        for cell in ('date("2026-01-01")', 'time("09:30:00")', 'date and time("2026-01-01T09:30:00")',
                     'duration("P30D")', 'duration("P1Y2M")'):
            assert rc.literal(cell) == cell

    def test_a_dotted_upstream_field_resolves_instead_of_grading_as_text(self):
        names = {"risk": {"riskBand": "High", "score": 7.0}, "fee": 12.5}
        assert rc.read_name(names, "risk.riskBand") == (True, "High")
        assert rc.read_name(names, " risk.score ") == (True, 7.0)
        assert rc.read_name(names, "fee") == (True, 12.5)
        assert rc.read_name(names, "risk.missing") == (False, None)
        assert rc.read_name(names, "fee.anything") == (False, None)
        assert rc.read_name(names, "notAName") == (False, None)

    def test_a_call_in_an_output_cell_is_not_read_as_a_string(self):
        # Returning the raw source would grade a correct rule wrong; the engine grades calls. It
        # answers unevaluable rather than aborting, so a cell no case asks about cannot kill the
        # whole grade — the caller decides what an unevaluable cell means for it.
        assert rc.literal("scoreModel(1)") is rc.UNEVALUABLE
        assert rc.literal("base * 1.1") is rc.UNEVALUABLE
        assert rc.literal('"High"') == "High"
        assert rc.literal("12.5") == 12.5
        assert rc.literal("-3") == -3.0
        assert rc.literal("true") is True

    def test_a_single_decision_case_still_fails_loudly_on_a_call(self):
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        table = ET.fromstring(f'''<decisionTable {model} hitPolicy="UNIQUE">
          <input><inputExpression typeRef="number"><text>amount</text></inputExpression></input>
          <output name="fee" typeRef="number"/>
          <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>scoreModel(amount)</text></outputEntry></rule>
        </decisionTable>''')

        with pytest.raises(SystemExit):
            rc.check_cases(table, "fee", [({"amount": 1}, 1.0)])

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

    def test_fixture_rules_are_named(self, project):
        _, root = rc.load_rule(project)
        rc.check_named_rules(rc.table_of(root))

    @pytest.mark.parametrize("annotation", ["<annotationEntry><text>  </text></annotationEntry>", ""])
    def test_unnamed_rule_fails(self, project, annotation):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        start = text.index("<annotationEntry>")
        end = text.index("</annotationEntry>", start) + len("</annotationEntry>")
        path.write_text(text[:start] + annotation + text[end:], encoding="utf-8")
        _, root = rc.load_rule(project)
        with pytest.raises(SystemExit):
            rc.check_named_rules(rc.table_of(root))

    @pytest.mark.parametrize("entry", ["inputEntry", "outputEntry"])
    def test_rule_missing_an_entry_fails(self, project, entry):
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8")
        start = text.index(f"<{entry}")
        end = text.index(f"</{entry}>", start) + len(f"</{entry}>")
        path.write_text(text[:start] + text[end:], encoding="utf-8")
        _, root = rc.load_rule(project)
        with pytest.raises(SystemExit):
            rc.check_named_rules(rc.table_of(root))

    def test_annotation_entries_without_a_column_fail(self, project):
        path = dmn_of(project)
        path.write_text(path.read_text(encoding="utf-8").replace('<annotation name="Annotation" />', ""), encoding="utf-8")
        _, root = rc.load_rule(project)
        with pytest.raises(SystemExit):
            rc.check_named_rules(rc.table_of(root))


def test_first_stops_at_its_first_match():
    """A FIRST table never evaluates the rows below the one that answers."""
    # With `literal()` refusing a call, reading every matching row let an unused fallback row
    # abort grading on an expression the engine would never have looked at.
    model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
    table = ET.fromstring(f'''<decisionTable {model} hitPolicy="FIRST">
      <input><inputExpression typeRef="number"><text>amount</text></inputExpression></input>
      <output name="fee" typeRef="number"/>
      <rule><inputEntry><text>&gt; 5</text></inputEntry><outputEntry><text>1</text></outputEntry></rule>
      <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>scoreModel(amount)</text></outputEntry></rule>
    </decisionTable>''')

    assert rc.evaluate(table, {"amount": 10}) == {"fee": 1}


POLICY_FIXTURE = TASKS / "smoke" / "brownfield_extend" / "fixtures" / "RiskRules"


def data_point(name, inputs, band, copies=("exact-1",)):
    expected = {"decision1": {"riskBand": band}}
    return {"id": name, "name": name, "inputs": inputs, "expectedOutput": expected,
            "evaluationCriterias": {c: {"expectedOutput": expected} for c in copies}}


def write_evals(project, points, evaluator_type=rc.EXACT_MATCH):
    """The files `uip rules eval` writes: one evaluator and one set, in the shapes the CLI saves."""
    root = project / "evals" / "rule"
    (root / "evaluators").mkdir(parents=True, exist_ok=True)
    (root / "eval-sets").mkdir(parents=True, exist_ok=True)
    (root / "evaluators" / "exact-1.json").write_text(json.dumps({
        "version": "1.0", "id": "exact-1", "name": "exact", "evaluatorTypeId": evaluator_type,
        "evaluatorConfig": {"name": "exact", "targetOutputKey": "*"}}), encoding="utf-8")
    (root / "eval-sets" / "evaluation-set-smoke.json").write_text(json.dumps({
        "version": "1.0", "id": "set-1", "name": "Smoke", "evaluatorRefs": ["exact-1"],
        "evaluations": points}), encoding="utf-8")


@pytest.fixture
def policy_project(tmp_path, monkeypatch):
    shutil.copytree(POLICY_FIXTURE, tmp_path / "RiskRules")
    monkeypatch.chdir(tmp_path)
    return tmp_path / "RiskRules"


def policy_table(project):
    return rc.table_of(rc.load_rule(project)[1])


def smoke(project):
    return rc.find_eval_set(project, "Smoke")


def grade(project):
    eval_set = smoke(project)
    refs = rc.check_scored_by_exact_match(project, eval_set)
    rc.check_data_points(eval_set, policy_table(project), "decision1", refs)
    return refs


class TestEvals:
    def test_right_data_points_pass(self, policy_project):
        write_evals(policy_project, [data_point("a", {"creditScore": 550, "income": 90000}, "High"),
                                     data_point("b", {"creditScore": 700, "income": 0}, "Low")])
        assert grade(policy_project) == ["exact-1"]
        assert rc.data_point_inputs(smoke(policy_project))[1] == {"creditScore": 700, "income": 0}
        assert [e["id"] for e in rc.check_exact_match_only(policy_project)] == ["exact-1"]

    def test_wrong_band_fails(self, policy_project):
        write_evals(policy_project, [data_point("a", {"creditScore": 720, "income": 30000}, "Medium")])
        with pytest.raises(SystemExit):
            grade(policy_project)

    def test_stale_evaluator_copy_fails(self, policy_project):
        point = data_point("a", {"creditScore": 720, "income": 30000}, "Low")
        point["evaluationCriterias"]["exact-1"]["expectedOutput"] = {"decision1": {"riskBand": "Medium"}}
        write_evals(policy_project, [point])
        with pytest.raises(SystemExit):
            grade(policy_project)

    @pytest.mark.parametrize("criterias", [{}, {"exact-1": None}, {"exact-1": {}}])
    def test_missing_evaluator_copy_fails(self, policy_project, criterias):
        """A hand-written data point without the copy the run scores against."""
        point = data_point("a", {"creditScore": 720, "income": 30000}, "Low")
        point["evaluationCriterias"] = criterias
        write_evals(policy_project, [point])
        with pytest.raises(SystemExit):
            grade(policy_project)

    @pytest.mark.parametrize("expected", [{}, {"Decision": {"riskBand": "Low"}}, {"decision1": {}},
                                          {"decision1": {"riskBand": "Low"}, "extra": {"riskBand": "Low"}},
                                          {"decision1": {"riskBand": "Low", "score": 1}}])
    def test_expected_not_every_output_of_the_decision_fails(self, policy_project, expected):
        point = data_point("a", {"creditScore": 720, "income": 30000}, "Low")
        point["expectedOutput"] = expected
        point["evaluationCriterias"]["exact-1"]["expectedOutput"] = expected
        write_evals(policy_project, [point])
        with pytest.raises(SystemExit):
            grade(policy_project)

    @pytest.mark.parametrize("inputs", [{"creditScore": 650}, {}, {"creditScore": 650, "income": 1, "age": 3}])
    def test_inputs_other_than_the_rules_fail(self, policy_project, inputs):
        """The engine reads a left-out input as null; {"creditScore": 650} would return High, not Medium."""
        write_evals(policy_project, [data_point("a", inputs, "Medium")])
        with pytest.raises(SystemExit):
            grade(policy_project)

    def test_empty_set_fails(self, policy_project):
        write_evals(policy_project, [])
        with pytest.raises(SystemExit):
            grade(policy_project)

    @pytest.mark.parametrize("refs", [[], ["missing"]])
    def test_set_not_linked_to_an_evaluator_on_disk_fails(self, policy_project, refs):
        write_evals(policy_project, [data_point("a", {"creditScore": 700, "income": 0}, "Low")])
        path = policy_project / "evals" / "rule" / "eval-sets" / "evaluation-set-smoke.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps({**doc, "evaluatorRefs": refs}), encoding="utf-8")
        with pytest.raises(SystemExit):
            grade(policy_project)

    def test_other_evaluator_type_fails(self, policy_project):
        write_evals(policy_project, [], evaluator_type="uipath-llm-judge-output-semantic-similarity")
        with pytest.raises(SystemExit):
            rc.check_exact_match_only(policy_project)
        with pytest.raises(SystemExit):
            rc.check_scored_by_exact_match(policy_project, smoke(policy_project))

    def test_no_evaluators_fails(self, policy_project):
        with pytest.raises(SystemExit):
            rc.check_exact_match_only(policy_project)

    def test_missing_set_fails(self, policy_project):
        with pytest.raises(SystemExit):
            smoke(policy_project)

    def test_two_sets_of_one_name_fail(self, policy_project):
        write_evals(policy_project, [])
        sets = policy_project / "evals" / "rule" / "eval-sets"
        (sets / "evaluation-set-copy.json").write_text((sets / "evaluation-set-smoke.json").read_text())
        with pytest.raises(SystemExit):
            smoke(policy_project)

    def test_invalid_json_fails(self, policy_project):
        write_evals(policy_project, [])
        (policy_project / "evals" / "rule" / "eval-sets" / "broken.json").write_text("{", encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.eval_sets(policy_project)
