"""Unit tests for rules_check.py. Run with ``pytest`` from any directory.

The uipath-rules graders evaluate the agent's decision table themselves, so
what these pin is that evaluator: the FEEL unary tests, the hit policies, the
decision-keyed contract, and the DMN profile checks. A regression here passes
a wrong table or fails a right one in every task that imports it.
"""

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_check as rc  # noqa: E402

TASKS = Path(__file__).resolve().parent.parent
FIXTURE = TASKS / "diagnose" / "wrong_output" / "fixtures" / "RiskRulesSolution" / "RiskRules"


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
        # Supported since the profile widened; a model is graded by check_knowledge_models. Only
        # the canvas draws a model, so adding one to a single-table rule also moves it to the
        # graph surface — `check_authoring_surface` refuses the pair that disagree.
        path = dmn_of(project)
        text = path.read_text(encoding="utf-8").replace(
            "</definitions>", '<businessKnowledgeModel id="b" name="b"/></definitions>').replace(
            f'surface="{rc.TABLE_SURFACE}"', f'surface="{rc.GRAPH_SURFACE}"')
        path.write_text(text, encoding="utf-8")
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


class TestFormatCheck:
    """`run_format_check` with `uip` stubbed, so these run without the CLI."""

    @staticmethod
    def stub(monkeypatch, project, files, returncode=0):
        def run(command, **_):
            assert Path(command[3]) != project  # formats a copy, never the agent's files
            body = json.dumps({"Data": {"Files": files}})
            return subprocess.CompletedProcess(command, returncode, stdout=body, stderr="")
        monkeypatch.setattr(rc.subprocess, "run", run)

    def test_passes_when_nothing_changes(self, project, monkeypatch):
        self.stub(monkeypatch, project, [{"File": "rule.dmn", "Changed": False}])
        rc.run_format_check(project)

    @pytest.mark.parametrize("files, returncode", [([{"File": "rule.dmn", "Changed": True}], 0), ([], 1)])
    def test_fails_on_a_change_or_a_failed_run(self, project, monkeypatch, files, returncode):
        self.stub(monkeypatch, project, files, returncode)
        with pytest.raises(SystemExit):
            rc.run_format_check(project)


class TestAuthoringSurface:
    """The surface decides which editor the designer opens, and `validate` reports neither value.

    Nothing graded it, so a rule authored with the wrong surface passed every task in the suite
    while opening in the wrong editor. Agents reached for `decision-graph` on single-table rules
    because the skill documented no other value — `uip rules init` scaffolds `decision-table`, and
    the skill never mentioned it.
    """

    @staticmethod
    def _dmn(body: str, surface: str | None) -> ET.Element:
        marker = (f'<extensionElements><uipath:authoring surface="{surface}" /></extensionElements>'
                  if surface is not None else "")
        return ET.fromstring(
            f'<definitions xmlns="{rc.DMN_NS}" xmlns:uipath="{rc.UIPATH_NS}" id="d" name="R" '
            f'namespace="urn:r">{marker}{body}</definitions>')

    TABLE = ('<decision id="d1" name="d1"><decisionTable id="t1" hitPolicy="FIRST">'
             '<input id="i1"><inputExpression id="ie1" typeRef="number"><text>a</text>'
             '</inputExpression></input><output id="o1" name="out" typeRef="string"/>'
             '<annotation name="Annotation"/><rule id="r1"><inputEntry><text>-</text></inputEntry>'
             '<outputEntry><text>"x"</text></outputEntry><annotationEntry><text>Any</text>'
             '</annotationEntry></rule></decisionTable></decision>')
    SECOND = (TABLE.replace('"d1"', '"d2"').replace('"t1"', '"t2"').replace('"i1"', '"i2"')
                   .replace('"ie1"', '"ie2"').replace('"o1"', '"o2"').replace('"r1"', '"r2"')
                   .replace('name="out"', 'name="out2"'))
    MODEL = ('<businessKnowledgeModel id="b1" name="b1"><variable id="vb" name="b1"/>'
             '<encapsulatedLogic/></businessKnowledgeModel>')
    NOTE = '<textAnnotation id="n1"><text>Owned by Finance</text></textAnnotation>'

    def test_one_table_on_the_table_surface_is_accepted(self):
        rc.check_authoring_surface(Path("r.dmn"), self._dmn(self.TABLE, rc.TABLE_SURFACE))

    def test_one_table_on_the_graph_surface_is_refused(self, capsys):
        # The reported defect: a single decision table authored as a DRD. It opens on the canvas
        # instead of the table editor, and nothing in `validate` says so.
        with pytest.raises(SystemExit):
            rc.check_authoring_surface(Path("r.dmn"), self._dmn(self.TABLE, rc.GRAPH_SURFACE))
        printed = capsys.readouterr().out
        assert "one decision table and nothing else" in printed
        assert "leave it as it is" in printed

    def test_two_decisions_on_the_table_surface_are_refused(self, capsys):
        # The other direction: a graph that opens as a bare table hides its requirement edges.
        with pytest.raises(SystemExit):
            rc.check_authoring_surface(Path("r.dmn"),
                                       self._dmn(self.TABLE + self.SECOND, rc.TABLE_SURFACE))
        assert "holds several decisions" in capsys.readouterr().out

    @pytest.mark.parametrize("extra", ["MODEL", "NOTE"])
    def test_an_element_only_the_canvas_draws_needs_the_graph_surface(self, extra, capsys):
        body = self.TABLE + getattr(self, extra)
        rc.check_authoring_surface(Path("r.dmn"), self._dmn(body, rc.GRAPH_SURFACE))
        with pytest.raises(SystemExit):
            rc.check_authoring_surface(Path("r.dmn"), self._dmn(body, rc.TABLE_SURFACE))
        assert "only the canvas draws" in capsys.readouterr().out

    def test_a_missing_marker_is_refused(self, capsys):
        with pytest.raises(SystemExit):
            rc.check_authoring_surface(Path("r.dmn"), self._dmn(self.TABLE, None))
        assert "declares no <uipath:authoring" in capsys.readouterr().out

    def test_a_single_literal_expression_decision_is_left_alone(self):
        # `editor` is per-decision, and which surface the designer wants for a file whose one
        # decision is a formula is not something this suite can evidence. Asserted on neither
        # value rather than guessed at.
        body = ('<decision id="d1" name="d1"><literalExpression id="le" typeRef="number">'
                '<text>a * 2</text></literalExpression></decision>')
        for surface in (rc.TABLE_SURFACE, rc.GRAPH_SURFACE):
            rc.check_authoring_surface(Path("r.dmn"), self._dmn(body, surface))

    def test_every_grader_goes_through_it(self, project):
        # Wired into `load_graph`, so no task can opt out. Without that an agent could author the
        # wrong surface and pass every criterion in the suite, which is what happened.
        path = dmn_of(project)
        path.write_text(path.read_text(encoding="utf-8").replace(
            f'surface="{rc.TABLE_SURFACE}"', f'surface="{rc.GRAPH_SURFACE}"'), encoding="utf-8")
        with pytest.raises(SystemExit):
            rc.load_rule(project)
