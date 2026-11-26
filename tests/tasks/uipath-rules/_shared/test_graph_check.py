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
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "LoanRules"
BROKEN = TASKS / "diagnose" / "repair_graph" / "fixtures" / "LoanRules"
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


def _without_loan_amount() -> ET.Element:
    """The fixture with the loanAmount input and its shape both gone, as a deletion leaves it."""
    root = fixture_root()
    root.remove(next(e for e in root if e.get("id") == "inputData_loanAmount"))
    diagram = next(root.iter(f"{{{gc.DMNDI_NS}}}DMNDiagram"))
    diagram.remove(next(s for s in diagram if s.get("dmnElementRef") == "inputData_loanAmount"))
    return root


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

    def test_shape_of_a_removed_element_may_go_for_a_repair(self):
        root = _without_loan_amount()
        gc.check_shapes_kept(fixture_root(), root, elements_may_go=True)

    def test_a_removed_element_fails_a_task_that_keeps_the_diagram(self):
        # The default reading, which an id rename also has to fail: the old id leaves the file
        # exactly as a deletion does, and narrowing to surviving ids graded both as clean.
        with pytest.raises(SystemExit):
            gc.check_shapes_kept(fixture_root(), _without_loan_amount())

    def test_fixture_has_no_overlap(self):
        gc.check_no_overlap(fixture_root())

    def test_a_file_with_no_diagram_passes(self):
        # Rule 10 tells the agent to leave DMNDI out of a new graph; the editor lays it out.
        root = fixture_root()
        root.remove(next(root.iter(f"{{{gc.DMNDI_NS}}}DMNDI")))
        gc.check_no_overlap(root)

    def test_an_element_the_diagram_never_placed_fails(self):
        # The edit added a decision and never ran `uip rules format`.
        root = fixture_root()
        ET.SubElement(root, f"{{{gc.DMN_NS}}}decision", {"id": "decision_approved", "name": "approved"})
        with pytest.raises(SystemExit):
            gc.check_no_overlap(root)

    def test_drawn_sizes_match_the_designer(self):
        # PO.Frontend DrdLayout.ts on main, after #8458. Ahead of the CLI on purpose: the
        # dmn-editor-utils the CLI pins still draws inputData 216 and a knowledge model 288,
        # so a file `uip rules format` wrote carries those and is right for its own layout.
        assert gc.DRAWN_SIZE == {"decision": (288, 96), "inputData": (240, 96),
                                 "businessKnowledgeModel": (224, 96), "textAnnotation": (224, 64)}

    def test_overlap_is_measured_at_the_drawn_size(self):
        # 200 apart clears a 180-wide box in the file but not the 288-wide card the designer draws.
        root = edited_root('<dc:Bounds x="640" y="64" width="288" height="96" />', '<dc:Bounds x="408" y="304" width="180" height="80" />')
        with pytest.raises(SystemExit):
            gc.check_no_overlap(root)


class TestLiteralExpressionDecisions:
    """A decision whose logic is a literal expression has no output columns of its own."""

    GRAPH = ('<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/" id="d" name="F" namespace="urn:f">'
             '<decision id="d_band" name="band"><variable id="v1" name="band" typeRef="string" />'
             '<decisionTable id="t1"><output id="o1" name="band" typeRef="string" />'
             '<rule id="r1"><outputEntry id="oe1"><text>"Large"</text></outputEntry></rule></decisionTable></decision>'
             '<decision id="d_fee" name="fee"><variable id="v2" name="fee" typeRef="number" />'
             '<informationRequirement id="ir"><requiredDecision href="#d_band" /></informationRequirement>'
             '<literalExpression id="le" typeRef="number"><text>loanAmount * 0.015</text></literalExpression>'
             "</decision></definitions>")

    def root(self):
        return ET.fromstring(self.GRAPH)

    def test_it_is_found_by_its_own_name(self):
        assert gc.decision_for_output(self.root(), "fee").get("id") == "d_fee"

    def test_a_table_is_still_found_by_its_output_column(self):
        assert gc.decision_for_output(self.root(), "band").get("id") == "d_band"

    def test_check_chain_reads_it_as_the_downstream_decision(self):
        # Regression: this raised AttributeError on output_names(None) and failed a correct rule.
        gc.check_chain(self.root(), "fee", "band")

    def test_a_name_no_decision_answers_under_still_fails(self):
        with pytest.raises(SystemExit):
            gc.decision_for_output(self.root(), "nothing")

    def test_cases_skip_it_rather_than_guessing(self):
        # The offline evaluator does not run FEEL, so a case expecting `fee` fails loudly.
        gc.check_graph_cases(self.root(), [({}, {"band": "Large"})])
        with pytest.raises(SystemExit):
            gc.check_graph_cases(self.root(), [({}, {"fee": 300.0})])


class TestMultiOutputUpstream:
    """A decision with two outputs answers with a structure; a reader names one field of it."""

    GRAPH = ('<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/" id="d" name="C" namespace="urn:c">'
             '<inputData id="in_amount" name="amount"><variable id="va" name="amount" typeRef="number" /></inputData>'
             '<decision id="d_assess" name="assessment"><variable id="v1" name="assessment" />'
             '<informationRequirement id="ir0"><requiredInput href="#in_amount" /></informationRequirement>'
             '<decisionTable id="t1" hitPolicy="FIRST">'
             '<input id="i1"><inputExpression id="ie1" typeRef="number"><text>amount</text></inputExpression></input>'
             '<output id="o1" name="severity" typeRef="string" /><output id="o2" name="fastTrack" typeRef="boolean" />'
             '<rule id="r1"><inputEntry id="ie_r1"><text>&lt; 1000</text></inputEntry>'
             '<outputEntry id="oe1a"><text>"Minor"</text></outputEntry>'
             '<outputEntry id="oe1b"><text>true</text></outputEntry></rule>'
             '<rule id="r2"><inputEntry id="ie_r2"><text>-</text></inputEntry>'
             '<outputEntry id="oe2a"><text>"Major"</text></outputEntry>'
             '<outputEntry id="oe2b"><text>false</text></outputEntry></rule>'
             "</decisionTable></decision>"
             '<decision id="d_queue" name="queue"><variable id="v2" name="queue" typeRef="string" />'
             '<informationRequirement id="ir1"><requiredDecision href="#d_assess" /></informationRequirement>'
             '<decisionTable id="t2" hitPolicy="FIRST">'
             '<input id="i2"><inputExpression id="ie2" typeRef="string"><text>assessment.severity</text></inputExpression></input>'
             '<output id="o3" name="queueName" typeRef="string" />'
             '<rule id="r3"><inputEntry id="ie_r3"><text>"Minor"</text></inputEntry>'
             '<outputEntry id="oe3"><text>"Desk"</text></outputEntry></rule>'
             '<rule id="r4"><inputEntry id="ie_r4"><text>-</text></inputEntry>'
             '<outputEntry id="oe4"><text>"Senior"</text></outputEntry></rule>'
             "</decisionTable></decision></definitions>")

    def test_a_dotted_field_is_read_as_a_value(self):
        root = ET.fromstring(self.GRAPH)
        gc.check_graph_cases(root, [({"amount": 500}, {"severity": "Minor", "fastTrack": True, "queueName": "Desk"}),
                                    ({"amount": 5000}, {"severity": "Major", "fastTrack": False, "queueName": "Senior"})])

    def test_an_output_cell_passing_a_dotted_field_through_resolves(self):
        # The queue table's output echoes a field of the upstream decision rather than a literal.
        root = ET.fromstring(self.GRAPH.replace('<text>"Desk"</text>', "<text>assessment.severity</text>"))
        gc.check_graph_cases(root, [({"amount": 500}, {"queueName": "Minor"})])


class TestKnowledgeModels:
    """A knowledge model is callable, wired to a caller, and part of no cycle."""

    MODEL = ('<businessKnowledgeModel id="bkm_score" name="scoreModel">'
             '<variable id="v_bkm" name="scoreModel" />'
             '<encapsulatedLogic id="el"><literalExpression id="le"><text>1</text></literalExpression></encapsulatedLogic>'
             "</businessKnowledgeModel>")
    CALL = '<knowledgeRequirement id="kr"><requiredKnowledge href="#bkm_score" /></knowledgeRequirement>'

    def with_model(self, model=None, call=None):
        text = (FIXTURE / DMN).read_text(encoding="utf-8")
        text = text.replace("</definitions>", (model if model is not None else self.MODEL) + "</definitions>")
        return ET.fromstring(text.replace('<variable id="variable_risk" name="risk" typeRef="string" />',
                                          '<variable id="variable_risk" name="risk" typeRef="string" />'
                                          + (call if call is not None else self.CALL)))

    def test_a_wired_model_passes(self):
        gc.check_knowledge_models(self.with_model())

    def test_a_model_with_no_variable_fails(self):
        bare = '<businessKnowledgeModel id="bkm_score" name="scoreModel"><encapsulatedLogic id="el" /></businessKnowledgeModel>'
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(model=bare))

    def test_a_variable_named_differently_fails(self):
        mismatched = self.MODEL.replace('name="scoreModel" />', 'name="other" />', 1)
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(model=mismatched))

    def test_a_model_with_no_encapsulated_logic_fails(self):
        empty = ('<businessKnowledgeModel id="bkm_score" name="scoreModel">'
                 '<variable id="v_bkm" name="scoreModel" /></businessKnowledgeModel>')
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(model=empty))

    def test_a_model_nothing_calls_fails(self):
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(call=""))

    def test_a_requirement_naming_no_model_fails(self):
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(
                call='<knowledgeRequirement id="kr"><requiredKnowledge href="#bkm_missing" /></knowledgeRequirement>'))

    def test_models_calling_each_other_fail(self):
        pair = (self.MODEL.replace("</businessKnowledgeModel>",
                                   '<knowledgeRequirement id="kr2"><requiredKnowledge href="#bkm_other" /></knowledgeRequirement>'
                                   "</businessKnowledgeModel>")
                + '<businessKnowledgeModel id="bkm_other" name="other"><variable id="v_o" name="other" />'
                  '<encapsulatedLogic id="el2" />'
                  '<knowledgeRequirement id="kr3"><requiredKnowledge href="#bkm_score" /></knowledgeRequirement>'
                  "</businessKnowledgeModel>")
        with pytest.raises(SystemExit):
            gc.check_knowledge_models(self.with_model(model=pair))


class TestTextAnnotations:
    NOTE = '<textAnnotation id="ta_1"><text>Reviewed quarterly.</text></textAnnotation>'
    TIE = ('<association id="assoc_1"><sourceRef href="#decision_risk" />'
           '<targetRef href="#ta_1" /></association>')

    def with_note(self, note=None, tie=None):
        text = (FIXTURE / DMN).read_text(encoding="utf-8")
        extra = (note if note is not None else self.NOTE) + (tie if tie is not None else self.TIE)
        return ET.fromstring(text.replace("</definitions>", extra + "</definitions>"))

    def test_a_tied_annotation_passes(self):
        gc.check_annotations_attached(self.with_note())

    def test_an_empty_annotation_fails(self):
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.with_note(note='<textAnnotation id="ta_1"><text>  </text></textAnnotation>'))

    def test_an_annotation_tied_to_nothing_fails(self):
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.with_note(tie=""))

    def test_an_association_pointing_at_a_missing_element_fails(self):
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.with_note(
                tie='<association id="assoc_1"><sourceRef href="#decision_gone" />'
                    '<targetRef href="#ta_1" /></association>'))

    def test_ends_written_as_attributes_fail(self):
        # Parses and validates, but the designer reads no ends and drops the connector.
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.with_note(
                tie='<association id="assoc_1" sourceRef="#decision_risk" targetRef="#ta_1" />'))


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


MODEL_NS = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'


def decision_xml(body: str) -> ET.Element:
    return ET.fromstring(f'<decision {MODEL_NS} name="probe">{body}</decision>')


class TestFeelEquality:
    """FEEL keeps booleans and numbers apart; Python does not."""

    def test_a_number_does_not_satisfy_a_boolean(self):
        # SupplierRules asks for a boolean `approved`. `1 == True` in Python, so a decision
        # returning 1 passed every case of a contract it does not meet.
        assert not gc.same_value(1, True)
        assert not gc.same_value(0, False)
        assert not gc.same_value(True, 1)

    def test_a_boolean_satisfies_the_same_boolean(self):
        assert gc.same_value(True, True)
        assert gc.same_value(False, False)

    def test_an_integer_satisfies_a_fractional_number(self):
        # FEEL has one number type, so the engine answering 5 for an expected 5.0 is a match.
        assert gc.same_value(5, 5.0)
        assert gc.same_value(12.5, 12.5)

    def test_unequal_numbers_still_fail(self):
        assert not gc.same_value(8, 9)


class TestModelCalls:
    """A call is FEEL the engine runs, not any text that mentions the model."""

    def test_a_literal_expression_call_is_found(self):
        probe = decision_xml('<literalExpression><text>discounted(50, tier) + 1</text></literalExpression>')
        assert gc.model_calls(probe, "discounted") == ["50, tier"]

    def test_an_output_cell_call_is_found(self):
        probe = decision_xml('<decisionTable><rule><outputEntry><text>discounted(500, tier)</text>'
                             '</outputEntry></rule></decisionTable>')
        assert gc.model_calls(probe, "discounted") == ["500, tier"]

    def test_a_rule_annotation_is_not_a_call(self):
        # The flaw this replaces: a table can inline the rates and name the model in its
        # annotation column, and a search over all descendant text reads that as a call.
        probe = decision_xml('<decisionTable><rule><outputEntry><text>42</text></outputEntry>'
                             '<annotationEntry><text>discounted(50, tier) by hand</text></annotationEntry>'
                             '</rule></decisionTable>')
        assert gc.model_calls(probe, "discounted") == []

    def test_a_longer_name_ending_in_the_model_is_not_a_call(self):
        probe = decision_xml('<literalExpression><text>netDiscounted(1)</text></literalExpression>')
        assert gc.model_calls(probe, "discounted") == []

    def test_a_nested_call_keeps_its_whole_argument_list(self):
        probe = decision_xml('<literalExpression><text>discounted(sum(1, 2), tier)</text></literalExpression>')
        assert gc.model_calls(probe, "discounted") == ["sum(1, 2), tier"]


class TestCallsAreNotSourceText:
    """A call is what the engine invokes, not every occurrence of the name."""

    def test_a_call_inside_a_string_is_not_a_call(self):
        probe = decision_xml('<decisionTable><rule><outputEntry><text>"discounted(50, tier)"</text>'
                             '</outputEntry></rule></decisionTable>')
        assert gc.model_calls(probe, "discounted") == []

    def test_whitespace_before_the_parenthesis_is_still_a_call(self):
        # FEEL allows it, so refusing it failed a correct submission on spacing alone.
        probe = decision_xml('<literalExpression><text>discounted (50, tier)</text></literalExpression>')
        assert gc.model_calls(probe, "discounted") == ["50, tier"]

    def test_a_parenthesis_inside_a_string_argument_does_not_end_the_call(self):
        probe = decision_xml('<literalExpression><text>discounted("a)b", tier)</text></literalExpression>')
        assert gc.model_calls(probe, "discounted") == ['"a)b", tier']


class TestUnevaluatedDecisions:
    """What the offline evaluator cannot run is absent, never a FEEL null."""

    @staticmethod
    def graph() -> ET.Element:
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        return ET.fromstring(f'''<definitions {model}>
          <inputData id="in_a" name="a"><variable name="a" typeRef="number"/></inputData>
          <decision id="d_lit" name="lit"><variable name="lit" typeRef="number"/>
            <informationRequirement><requiredInput href="#in_a"/></informationRequirement>
            <literalExpression typeRef="number"><text>a * 10</text></literalExpression></decision>
          <decision id="d_band" name="band"><variable name="band" typeRef="number"/>
            <informationRequirement><requiredDecision href="#d_lit"/></informationRequirement>
            <decisionTable hitPolicy="FIRST">
              <input><inputExpression typeRef="number"><text>lit</text></inputExpression></input>
              <output name="flag" typeRef="number"/>
              <rule><inputEntry><text>&gt; 5</text></inputEntry><outputEntry><text>1</text></outputEntry></rule>
              <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>0</text></outputEntry></rule>
            </decisionTable></decision>
        </definitions>''')

    def test_a_table_fed_by_a_literal_expression_publishes_nothing(self):
        # It used to read the unevaluated literal as null, fall through to the `-` row and answer
        # 0 — a value nothing computed, which a case expecting 0 accepted.
        assert "flag" not in gc.evaluate_graph(self.graph(), {"a": 1})

    def test_a_case_naming_an_unevaluated_output_fails_loudly(self):
        with pytest.raises(SystemExit):
            gc.check_graph_cases(self.graph(), [({"a": 1}, {"flag": 0})])


class TestAnUnsupportedCellIsLocal:
    """A cell only the engine can read makes its own decision unevaluable, not the whole grade."""

    @staticmethod
    def graph() -> ET.Element:
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        return ET.fromstring(f'''<definitions {model}>
          <inputData id="in_a" name="a"><variable name="a" typeRef="number"/></inputData>
          <businessKnowledgeModel id="bkm_rate" name="rate"><variable name="rate"/>
            <encapsulatedLogic><formalParameter name="x" typeRef="number"/>
              <literalExpression typeRef="number"><text>x * 2</text></literalExpression>
            </encapsulatedLogic></businessKnowledgeModel>
          <decision id="d_band" name="band"><variable name="band" typeRef="string"/>
            <informationRequirement><requiredInput href="#in_a"/></informationRequirement>
            <decisionTable hitPolicy="FIRST">
              <input><inputExpression typeRef="number"><text>a</text></inputExpression></input>
              <output name="band" typeRef="string"/>
              <rule><inputEntry><text>&gt;= 50</text></inputEntry><outputEntry><text>"Large"</text></outputEntry></rule>
              <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>"Small"</text></outputEntry></rule>
            </decisionTable></decision>
          <decision id="d_fee" name="fee"><variable name="fee" typeRef="number"/>
            <informationRequirement><requiredInput href="#in_a"/></informationRequirement>
            <knowledgeRequirement><requiredKnowledge href="#bkm_rate"/></knowledgeRequirement>
            <decisionTable hitPolicy="FIRST">
              <input><inputExpression typeRef="number"><text>a</text></inputExpression></input>
              <output name="fee" typeRef="number"/>
              <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>rate(a)</text></outputEntry></rule>
            </decisionTable></decision>
        </definitions>''')

    def test_an_independent_table_is_still_graded(self):
        # `evaluate_graph` visits every decision, so `rate(a)` in the fee table used to abort the
        # whole grade through `literal()` even though the case only asks about the band.
        gc.check_graph_cases(self.graph(), [({"a": 60}, {"band": "Large"}), ({"a": 10}, {"band": "Small"})])

    def test_the_model_calling_table_publishes_nothing(self):
        assert "fee" not in gc.evaluate_graph(self.graph(), {"a": 60})

    def test_a_case_naming_the_unevaluable_output_fails(self):
        with pytest.raises(SystemExit):
            gc.check_graph_cases(self.graph(), [({"a": 60}, {"fee": 120.0})])


class TestUnsupportedIsPerOutput:
    """One output only the engine can work out does not take its siblings down with it."""

    @staticmethod
    def graph() -> ET.Element:
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        return ET.fromstring(f'''<definitions {model}>
          <inputData id="in_a" name="a"><variable name="a" typeRef="number"/></inputData>
          <businessKnowledgeModel id="bkm_rate" name="rate"><variable name="rate"/>
            <encapsulatedLogic><formalParameter name="x" typeRef="number"/>
              <literalExpression typeRef="number"><text>x * 2</text></literalExpression>
            </encapsulatedLogic></businessKnowledgeModel>
          <decision id="d_both" name="both"><variable name="both"/>
            <informationRequirement><requiredInput href="#in_a"/></informationRequirement>
            <knowledgeRequirement><requiredKnowledge href="#bkm_rate"/></knowledgeRequirement>
            <decisionTable hitPolicy="FIRST">
              <input><inputExpression typeRef="number"><text>a</text></inputExpression></input>
              <output name="band" typeRef="string"/>
              <output name="fee" typeRef="number"/>
              <rule><inputEntry><text>-</text></inputEntry>
                <outputEntry><text>"Large"</text></outputEntry>
                <outputEntry><text>rate(a)</text></outputEntry></rule>
            </decisionTable></decision>
        </definitions>''')

    def test_the_literal_output_of_a_mixed_row_is_still_graded(self):
        # Raising the unsupported `fee` to the whole decision marked `band` unknown too, so a
        # case asking only for the band failed on a value the evaluator had in hand.
        gc.check_graph_cases(self.graph(), [({"a": 10}, {"band": "Large"})])

    def test_the_model_computed_output_of_the_same_row_publishes_nothing(self):
        assert "fee" not in gc.evaluate_graph(self.graph(), {"a": 10})


class TestAnsweringCell:
    """The row that fires is the one graded; the others are free to say anything."""

    @staticmethod
    def freight(gold_cell: str, rest_cell: str) -> ET.Element:
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        return ET.fromstring(f'''<decision {model} name="freight">
          <decisionTable hitPolicy="FIRST">
            <input><inputExpression typeRef="number"><text>tier</text></inputExpression></input>
            <output name="freight" typeRef="number"/>
            <rule><inputEntry><text>15</text></inputEntry><outputEntry><text>{gold_cell}</text></outputEntry></rule>
            <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>{rest_cell}</text></outputEntry></rule>
          </decisionTable></decision>''')

    def test_each_tier_reads_the_row_that_fires(self):
        decision = self.freight("discounted(50, tier)", "discounted(50, tier)")
        assert gc.answering_cell(decision, {"tier": 15}) == "discounted(50, tier)"
        assert gc.answering_cell(decision, {"tier": 10}) == "discounted(50, tier)"

    def test_a_row_no_earlier_row_shadows_is_not_skipped(self):
        # One correct row and the rest returning 0 used to pass: the check read the first cell
        # that held a call and never looked at the others.
        decision = self.freight("discounted(50, tier)", "0")
        assert gc.answering_cell(decision, {"tier": 10}) == "0"

    def test_a_literal_expression_decision_answers_with_its_text(self):
        probe = decision_xml('<literalExpression><text>discounted(50, tier)</text></literalExpression>')
        assert gc.answering_cell(probe, {"tier": 15}) == "discounted(50, tier)"

    def test_a_table_keyed_on_nothing_the_check_supplies_is_refused(self):
        # `all(...)` over no column is vacuously true, so the first row would always "fire" and
        # a table keyed on something else entirely would be graded on row one.
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        decision = ET.fromstring(f'''<decision {model} name="freight">
          <decisionTable hitPolicy="FIRST">
            <input><inputExpression typeRef="number"><text>listPrice</text></inputExpression></input>
            <output name="freight" typeRef="number"/>
            <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>discounted(50, tier)</text></outputEntry></rule>
          </decisionTable></decision>''')
        with pytest.raises(SystemExit):
            gc.answering_cell(decision, {"tier": 10})

    def test_a_decision_carrying_both_kinds_of_logic_is_refused(self):
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        decision = ET.fromstring(f'''<decision {model} name="freight">
          <literalExpression><text>discounted(50, tier)</text></literalExpression>
          <decisionTable hitPolicy="FIRST">
            <input><inputExpression typeRef="number"><text>tier</text></inputExpression></input>
            <output name="freight" typeRef="number"/>
            <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>0</text></outputEntry></rule>
          </decisionTable></decision>''')
        with pytest.raises(SystemExit):
            gc.answering_cell(decision, {"tier": 10})


class TestSoleCallArguments:
    def test_a_bare_call_gives_its_arguments(self):
        assert gc.sole_call_arguments("discounted(50, tier)", "discounted") == "50, tier"

    def test_arithmetic_around_the_call_is_refused(self):
        with pytest.raises(SystemExit):
            gc.sole_call_arguments("discounted(50, tier) + 100", "discounted")

    def test_a_cell_that_does_not_call_the_model_is_refused(self):
        with pytest.raises(SystemExit):
            gc.sole_call_arguments("0", "discounted")


class TestRedundantParentheses:
    """`(f(x))` is the expression `f(x)`; refusing it failed correct FEEL."""

    def test_one_pair_is_the_same_expression(self):
        assert gc.sole_call_arguments("(discounted(50, tier))", "discounted") == "50, tier"

    def test_nested_pairs_are_too(self):
        assert gc.sole_call_arguments("((discounted(50, tier)))", "discounted") == "50, tier"

    def test_parentheses_round_only_part_of_the_cell_stay_refused(self):
        with pytest.raises(SystemExit):
            gc.sole_call_arguments("(discounted(50, tier)) + (100)", "discounted")


class TestHitPolicyIsRespected:
    def test_a_collect_table_is_not_graded_on_one_row(self):
        # COLLECT answers with every matching row, so the first is only part of the answer.
        # `rules_check.evaluate` already refuses these policies; this path has to agree.
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        decision = ET.fromstring(f'''<decision {model} name="freight">
          <decisionTable hitPolicy="COLLECT">
            <input><inputExpression typeRef="number"><text>tier</text></inputExpression></input>
            <output name="freight" typeRef="number"/>
            <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>discounted(50, tier)</text></outputEntry></rule>
            <rule><inputEntry><text>-</text></inputEntry><outputEntry><text>999</text></outputEntry></rule>
          </decisionTable></decision>''')
        with pytest.raises(SystemExit):
            gc.answering_cell(decision, {"tier": 15})


class TestANoteIsAboutSomething:
    """An association joins a note to the element it describes, not to a note."""

    @staticmethod
    def document(source: str, target: str, second_note: bool = False) -> ET.Element:
        model = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"'
        other = '<textAnnotation id="n2"><text>another note</text></textAnnotation>' if second_note else ""
        return ET.fromstring(f'''<definitions {model}>
          <decision id="d" name="d"><decisionTable/></decision>
          <textAnnotation id="n"><text>percentages are whole numbers</text></textAnnotation>
          {other}
          <association id="a"><sourceRef href="#{source}"/><targetRef href="#{target}"/></association>
        </definitions>''')

    def test_a_note_tied_to_a_decision_is_attached(self):
        gc.check_annotations_attached(self.document("d", "n"))

    def test_a_note_tied_to_itself_is_attached_to_nothing(self):
        # Both ends in `notes` satisfied "tied", so a self-association passed while telling a
        # reader nothing about which element the note is for.
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.document("n", "n"))

    def test_a_note_tied_to_another_note_is_attached_to_nothing(self):
        with pytest.raises(SystemExit):
            gc.check_annotations_attached(self.document("n", "n2", second_note=True))


class TestFeelEqualityInsideAList:
    def test_a_list_of_numbers_does_not_satisfy_a_list_of_booleans(self):
        assert not gc.same_value([True], [1])
        assert not gc.same_value([1, True], [1, 1])

    def test_a_list_of_integers_satisfies_a_list_of_fractional_numbers(self):
        assert gc.same_value([1, 2], [1.0, 2.0])

    def test_lists_of_different_length_do_not_match(self):
        assert not gc.same_value([1], [1, 2])
