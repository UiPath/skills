"""Each per-task grader, against a correct submission and against a wrong one.

The nine per-task graders shipped with no test of their own, against a repo
norm of a `test_check_*.py` beside the graders in five other suites
(MST-18847). A grader is scored on its exit code alone, so one that accepts a
wrong submission awards full weight for it and one that refuses a right
submission denies full weight for it — in every run of its task, silently.

What each test does: build a project the task's prompt would be satisfied by,
assert the grader accepts it; then make one specific thing wrong and assert it
refuses that. `test_graders_refuse_an_empty_sandbox.py` covers the "nothing at
all" case for every grader; this covers the near-misses.

Not covered here: `check_graph_formula_and_model_debug.py`. Every case it grades
goes through `uip rules debug` against a tenant. Its offline half — the mutation
probe's XML rewrite and the model-by-id-not-name lookup — is in
`test_engine_path.py`.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_check as rc  # noqa: E402
from fixture_inventory import SUITE  # noqa: E402

SHARED_RISK = SUITE / "_shared" / "fixtures" / "RiskRules"


def run(grader: Path, *arguments: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(grader), *arguments], cwd=cwd,
                          capture_output=True, text=True, timeout=120)


def accepted(result: subprocess.CompletedProcess) -> bool:
    assert "Traceback" not in result.stderr, result.stderr
    return result.returncode == 0


def project(workspace: Path, name: str, dmn: str, inputs: dict, outputs: dict,
            entry_points: list | None = None) -> Path:
    """A BusinessRules project on disk: manifest, the `.dmn`, and the contract refresh writes."""
    folder = workspace / name
    folder.mkdir(parents=True)
    (folder / "project.uiproj").write_text(
        json.dumps({"Name": name, "ProjectType": "BusinessRules"}), encoding="utf-8")
    (folder / rc.PROJECT_NAME and folder / "Business rule.dmn").write_text(dmn, encoding="utf-8")
    (folder / "bindings_v2.json").write_text(json.dumps({"version": "2.0", "resources": []}),
                                             encoding="utf-8")
    schema = lambda props: {"type": "object", "properties": {  # noqa: E731
        key: {"type": value} for key, value in props.items()}}
    (folder / "entry-points.json").write_text(json.dumps({
        "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
        "$id": "entry-points.json",
        "entryPoints": entry_points if entry_points is not None else [{
            "filePath": "/Business rule.dmn", "uniqueId": "11111111-1111-1111-1111-111111111111",
            "type": "BusinessRules", "displayName": name,
            "input": schema(inputs), "output": schema(outputs),
        }],
    }), encoding="utf-8")
    return folder


def definitions(name: str, body: str) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8" ?>\n'
            f'<definitions xmlns="{rc.DMN_NS}" xmlns:dmndi="https://www.omg.org/spec/DMN/20230324/DMNDI/" '
            f'xmlns:dc="http://www.omg.org/spec/DMN/20180521/DC/" id="definitions_{name}" '
            f'name="{name}" namespace="urn:{name}">{body}</definitions>')


def shape(element_id: str, x: int, y: int) -> str:
    return (f'<dmndi:DMNShape id="DMNShape_{element_id}" dmnElementRef="{element_id}">'
            f'<dc:Bounds x="{x}" y="{y}" width="288" height="96"/></dmndi:DMNShape>')


def diagram(*shapes: str) -> str:
    return f'<dmndi:DMNDI><dmndi:DMNDiagram id="DMNDiagram_1">{"".join(shapes)}</dmndi:DMNDiagram></dmndi:DMNDI>'


# --- the greenfield graders ------------------------------------------------

DISCOUNT_MODEL = '''
  <businessKnowledgeModel id="bkm_tier" name="tierDiscount">
    <variable id="v_tier" name="tierDiscount" typeRef="number"/>
    <encapsulatedLogic>
      <formalParameter id="fp_tier" name="customerTier" typeRef="string"/>
      <formalParameter id="fp_total" name="orderTotal" typeRef="number"/>
      <decisionTable id="dt_tier" hitPolicy="FIRST">
        <input id="in_tier"><inputExpression id="ie_tier" typeRef="string"><text>customerTier</text></inputExpression></input>
        <input id="in_total"><inputExpression id="ie_total" typeRef="number"><text>orderTotal</text></inputExpression></input>
        <output id="out_tier" name="discount" typeRef="number"/>
        <annotation name="Annotation"/>
        {rows}
      </decisionTable>
    </encapsulatedLogic>
  </businessKnowledgeModel>'''


def _row(tier: str, total: str, discount: str, note: str) -> str:
    return (f'<rule id="r_{tier}_{abs(hash((tier, total))) % 10000}">'
            f'<inputEntry><text>"{tier}"</text></inputEntry>'
            f'<inputEntry><text>{total}</text></inputEntry>'
            f'<outputEntry><text>{discount}</text></outputEntry>'
            f'<annotationEntry><text>{note}</text></annotationEntry></rule>')


def discount_rules(gold_large: str = "15") -> str:
    rows = "".join([
        _row("Gold", ">= 1000", gold_large, "Gold, large order"),
        _row("Gold", "-", "10", "Gold"),
        _row("Silver", ">= 1000", "7.5", "Silver, large order"),
        _row("Silver", "-", "5", "Silver"),
        _row("Standard", ">= 1000", "2", "Standard, large order"),
        _row("Standard", "-", "0", "Standard"),
    ])
    return definitions("DiscountRules",
        '<decision id="decision_discount" name="discount">'
        '<variable id="v_discount" name="discount" typeRef="number"/>'
        '<informationRequirement id="ir_tier"><requiredInput href="#inputData_customerTier"/></informationRequirement>'
        '<informationRequirement id="ir_total"><requiredInput href="#inputData_orderTotal"/></informationRequirement>'
        '<knowledgeRequirement id="kr_tier"><requiredKnowledge href="#bkm_tier"/></knowledgeRequirement>'
        '<literalExpression id="le_discount" typeRef="number">'
        '<text>tierDiscount(customerTier, orderTotal)</text></literalExpression>'
        '</decision>'
        + DISCOUNT_MODEL.format(rows=rows) +
        '<inputData id="inputData_customerTier" name="customerTier">'
        '<variable id="v_ct" name="customerTier" typeRef="string"/></inputData>'
        '<inputData id="inputData_orderTotal" name="orderTotal">'
        '<variable id="v_ot" name="orderTotal" typeRef="number"/></inputData>'
        '<textAnnotation id="note_tiers"><text>Tiers are set by Sales and reviewed each quarter.</text></textAnnotation>'
        '<association id="assoc_note"><sourceRef href="#note_tiers"/><targetRef href="#bkm_tier"/></association>'
        + diagram(shape("decision_discount", 0, 0), shape("bkm_tier", 400, 0),
                  shape("inputData_customerTier", 0, 200), shape("inputData_orderTotal", 400, 200),
                  shape("note_tiers", 800, 0)))


class TestGraphKnowledgeModel:
    GRADER = SUITE / "smoke" / "graph_knowledge_model" / "check_graph_knowledge_model.py"

    def test_a_correct_submission_is_accepted(self, tmp_path):
        project(tmp_path, "DiscountRules", discount_rules(),
                {"customerTier": "string", "orderTotal": "number"}, {"discount": "number"})

        assert accepted(run(self.GRADER, cwd=tmp_path))

    def test_a_model_with_a_wrong_discount_is_refused(self, tmp_path):
        # The finding this grader gained: it checked the model was declared, wired and called,
        # and never what it answered — so a model with the tiers swapped passed the whole task.
        project(tmp_path, "DiscountRules", discount_rules(gold_large="99"),
                {"customerTier": "string", "orderTotal": "number"}, {"discount": "number"})

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)
        assert "returned 99.0" in result.stdout

    def test_a_decision_that_inlines_the_lookup_is_refused(self, tmp_path):
        inlined = discount_rules().replace(
            "<text>tierDiscount(customerTier, orderTotal)</text>", "<text>10</text>")
        project(tmp_path, "DiscountRules", inlined,
                {"customerTier": "string", "orderTotal": "number"}, {"discount": "number"})

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)
        assert "never used" in result.stdout or "wired but never used" in result.stdout

    def test_an_unattached_note_is_refused(self, tmp_path):
        loose = discount_rules().replace(
            '<association id="assoc_note"><sourceRef href="#note_tiers"/><targetRef href="#bkm_tier"/></association>', "")
        project(tmp_path, "DiscountRules", loose,
                {"customerTier": "string", "orderTotal": "number"}, {"discount": "number"})

        assert not accepted(run(self.GRADER, cwd=tmp_path))

    def test_a_helper_model_beside_the_lookup_is_allowed(self, tmp_path):
        # The prompt asks for the tier lookup as a model and does not forbid a second one, so
        # the lookup is found by its signature rather than by being the only model in the file.
        helper = (
            '<businessKnowledgeModel id="bkm_round" name="roundPct">'
            '<variable id="v_round" name="roundPct" typeRef="number"/>'
            '<encapsulatedLogic><formalParameter id="fp_pct" name="pct" typeRef="number"/>'
            '<literalExpression id="le_round"><text>pct</text></literalExpression>'
            '</encapsulatedLogic></businessKnowledgeModel>')
        dmn = discount_rules().replace(
            "<text>tierDiscount(customerTier, orderTotal)</text>",
            "<text>roundPct(tierDiscount(customerTier, orderTotal))</text>").replace(
            "</definitions>", helper + "</definitions>").replace(
            "</dmndi:DMNDiagram>", shape("bkm_round", 1200, 0) + "</dmndi:DMNDiagram>").replace(
            '<knowledgeRequirement id="kr_tier"><requiredKnowledge href="#bkm_tier"/></knowledgeRequirement>',
            '<knowledgeRequirement id="kr_tier"><requiredKnowledge href="#bkm_tier"/></knowledgeRequirement>'
            '<knowledgeRequirement id="kr_round"><requiredKnowledge href="#bkm_round"/></knowledgeRequirement>')
        project(tmp_path, "DiscountRules", dmn,
                {"customerTier": "string", "orderTotal": "number"}, {"discount": "number"})

        assert accepted(run(self.GRADER, cwd=tmp_path))


def fee_rules(fee_type: str = "number", fee_text: str = "loanAmount * 0.02") -> str:
    bands = "".join([
        '<rule id="r_small"><inputEntry><text>&lt; 50000</text></inputEntry>'
        '<outputEntry><text>"Small"</text></outputEntry>'
        '<annotationEntry><text>Small loan</text></annotationEntry></rule>',
        '<rule id="r_large"><inputEntry><text>-</text></inputEntry>'
        '<outputEntry><text>"Large"</text></outputEntry>'
        '<annotationEntry><text>Large loan</text></annotationEntry></rule>',
    ])
    return definitions("FeeRules",
        '<decision id="decision_band" name="band">'
        '<variable id="v_band" name="band" typeRef="string"/>'
        '<informationRequirement id="ir_amount"><requiredInput href="#inputData_loanAmount"/></informationRequirement>'
        '<decisionTable id="dt_band" hitPolicy="FIRST">'
        '<input id="in_amount"><inputExpression id="ie_amount" typeRef="number"><text>loanAmount</text></inputExpression></input>'
        '<output id="out_band" name="band" typeRef="string"/><annotation name="Annotation"/>'
        f'{bands}</decisionTable></decision>'
        '<decision id="decision_fee" name="fee">'
        f'<variable id="v_fee" name="fee" typeRef="{fee_type}"/>'
        '<informationRequirement id="ir_band"><requiredDecision href="#decision_band"/></informationRequirement>'
        '<informationRequirement id="ir_fee_amount"><requiredInput href="#inputData_loanAmount"/></informationRequirement>'
        f'<literalExpression id="le_fee" typeRef="{fee_type}"><text>{fee_text}</text></literalExpression>'
        '</decision>'
        '<inputData id="inputData_loanAmount" name="loanAmount">'
        '<variable id="v_la" name="loanAmount" typeRef="number"/></inputData>'
        + diagram(shape("decision_band", 0, 0), shape("decision_fee", 400, 0),
                  shape("inputData_loanAmount", 0, 200)))


class TestGraphLiteralExpression:
    GRADER = SUITE / "smoke" / "graph_literal_expression" / "check_graph_literal_expression.py"

    def _project(self, tmp_path, **kwargs):
        return project(tmp_path, "FeeRules", fee_rules(**kwargs),
                       {"loanAmount": "number"}, {"band": "string", "fee": "number"})

    def test_a_correct_submission_is_accepted(self, tmp_path):
        self._project(tmp_path)

        assert accepted(run(self.GRADER, cwd=tmp_path))

    def test_a_fee_declared_as_a_string_is_refused(self, tmp_path):
        # `validate` never looks at a graph's literal expressions, so a fee typed `string`
        # reaches the engine and fails there. The offline band cases catch nothing.
        self._project(tmp_path, fee_type="string")

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)
        assert "number" in result.stdout

    def test_an_empty_expression_is_refused(self, tmp_path):
        self._project(tmp_path, fee_text="")

        assert not accepted(run(self.GRADER, cwd=tmp_path))

    def test_a_band_that_missorts_the_threshold_is_refused(self, tmp_path):
        wrong = fee_rules().replace("&lt; 50000", "&lt;= 50000")
        project(tmp_path, "FeeRules", wrong, {"loanAmount": "number"},
                {"band": "string", "fee": "number"})

        assert not accepted(run(self.GRADER, cwd=tmp_path))


def supplier_rules(extra: str = "") -> str:
    rows = "".join([
        '<rule id="r_no"><inputEntry><text>false</text></inputEntry><inputEntry><text>-</text></inputEntry>'
        '<outputEntry><text>false</text></outputEntry><annotationEntry><text>Not onboarded</text></annotationEntry></rule>',
        '<rule id="r_over"><inputEntry><text>true</text></inputEntry><inputEntry><text>&gt; 25000</text></inputEntry>'
        '<outputEntry><text>false</text></outputEntry><annotationEntry><text>Over the limit</text></annotationEntry></rule>',
        '<rule id="r_ok"><inputEntry><text>true</text></inputEntry><inputEntry><text>-</text></inputEntry>'
        '<outputEntry><text>true</text></outputEntry><annotationEntry><text>Approved</text></annotationEntry></rule>',
    ])
    return definitions("SupplierRules",
        '<decision id="decision_approved" name="approval">'
        '<variable id="v_app" name="approval" typeRef="boolean"/>'
        '<informationRequirement id="ir_on"><requiredInput href="#inputData_onboarded"/></informationRequirement>'
        '<informationRequirement id="ir_sp"><requiredInput href="#inputData_spend"/></informationRequirement>'
        '<decisionTable id="dt_app" hitPolicy="FIRST">'
        '<input id="in_on"><inputExpression id="ie_on" typeRef="boolean"><text>onboarded</text></inputExpression></input>'
        '<input id="in_sp"><inputExpression id="ie_sp" typeRef="number"><text>spend</text></inputExpression></input>'
        '<output id="out_app" name="approved" typeRef="boolean"/><annotation name="Annotation"/>'
        f'{rows}</decisionTable></decision>'
        '<inputData id="inputData_onboarded" name="onboarded">'
        '<variable id="v_on" name="onboarded" typeRef="boolean"/></inputData>'
        '<inputData id="inputData_spend" name="spend">'
        '<variable id="v_sp" name="spend" typeRef="number"/></inputData>'
        + extra)


class TestGraphUnsupportedElements:
    GRADER = SUITE / "smoke" / "graph_unsupported_elements" / "check_graph_unsupported_elements.py"

    def _project(self, tmp_path, extra=""):
        return project(tmp_path, "SupplierRules", supplier_rules(extra),
                       {"onboarded": "boolean", "spend": "number"}, {"approved": "boolean"})

    def test_a_rule_that_declines_the_knowledge_source_is_accepted(self, tmp_path):
        self._project(tmp_path)

        assert accepted(run(self.GRADER, cwd=tmp_path))

    @pytest.mark.parametrize("element", sorted(rc.UNSUPPORTED_ELEMENTS))
    def test_each_unsupported_element_is_refused(self, tmp_path, element):
        # The set lives in one place now. Parametrising over it is what keeps this task's
        # coverage and `load_graph`'s refusal from drifting apart again.
        self._project(tmp_path, extra=f'<{element} id="unsupported_1" name="x"/>')

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)
        assert element in result.stdout

    def test_a_number_where_the_case_wants_a_boolean_is_refused(self, tmp_path):
        # Python holds `True == 1`; FEEL does not. A decision answering 1 for true used to pass.
        self._project(tmp_path)
        dmn = next((tmp_path / "SupplierRules").glob("*.dmn"))
        dmn.write_text(dmn.read_text().replace("<text>true</text></outputEntry>",
                                               "<text>1</text></outputEntry>"), encoding="utf-8")

        assert not accepted(run(self.GRADER, cwd=tmp_path))


# --- the brownfield graders, against their own staged fixtures -------------

RATE_DECISION = (
    '<decision id="decision_rate" name="rate">'
    '<variable id="v_rate" name="rate" typeRef="number"/>'
    '<informationRequirement id="ir_rate_band"><requiredDecision href="#decision_25a2c471-1c6f-46cb-a22a-f4b2dfdb7ee7"/></informationRequirement>'
    '<informationRequirement id="ir_rate_amount"><requiredInput href="#inputData_loanAmount"/></informationRequirement>'
    '<decisionTable id="dt_rate" hitPolicy="FIRST">'
    '<input id="in_rate_band"><inputExpression id="ie_rate_band" typeRef="string"><text>decision1</text></inputExpression></input>'
    '<input id="in_rate_amount"><inputExpression id="ie_rate_amount" typeRef="number"><text>loanAmount</text></inputExpression></input>'
    '<output id="out_rate" name="interestRate" typeRef="number"/><annotation name="Annotation"/>'
    '<rule id="r_rate_high"><inputEntry><text>"High"</text></inputEntry><inputEntry><text>-</text></inputEntry>'
    '<outputEntry><text>12.5</text></outputEntry><annotationEntry><text>High risk</text></annotationEntry></rule>'
    '<rule id="r_rate_med_l"><inputEntry><text>"Medium"</text></inputEntry><inputEntry><text>&gt;= 100000</text></inputEntry>'
    '<outputEntry><text>9</text></outputEntry><annotationEntry><text>Medium, large</text></annotationEntry></rule>'
    '<rule id="r_rate_med"><inputEntry><text>"Medium"</text></inputEntry><inputEntry><text>-</text></inputEntry>'
    '<outputEntry><text>8</text></outputEntry><annotationEntry><text>Medium</text></annotationEntry></rule>'
    '<rule id="r_rate_low_l"><inputEntry><text>"Low"</text></inputEntry><inputEntry><text>&gt;= 100000</text></inputEntry>'
    '<outputEntry><text>6</text></outputEntry><annotationEntry><text>Low, large</text></annotationEntry></rule>'
    '<rule id="r_rate_low"><inputEntry><text>"Low"</text></inputEntry><inputEntry><text>-</text></inputEntry>'
    '<outputEntry><text>5.5</text></outputEntry><annotationEntry><text>Low</text></annotationEntry></rule>'
    '</decisionTable></decision>'
    '<inputData id="inputData_loanAmount" name="loanAmount">'
    '<variable id="v_loanAmount" name="loanAmount" typeRef="number"/></inputData>')


@pytest.fixture
def extended_risk(tmp_path):
    """The RiskRules fixture with the rate decision the graph_extend_table prompt asks for.

    The contract is written as `uip rules refresh` writes it after that edit: the published
    per-decision entry keeps its `uniqueId`, and the file gains the whole-file entry a graph
    publishes. Hand-written rather than refreshed, because the job that runs these tests has
    pytest and no CLI; `validate_fixtures.py` is where the CLI's own verdict lives.
    """
    shutil.copytree(SHARED_RISK, tmp_path / "RiskRules")
    folder = tmp_path / "RiskRules"
    dmn = folder / "Business rule.dmn"
    text = dmn.read_text(encoding="utf-8")
    assert "</definitions>" in text
    dmn.write_text(text.replace("</definitions>", RATE_DECISION + "</definitions>"), encoding="utf-8")

    # The shapes `uip rules format` adds for the two new elements. Placed clear of the
    # fixture's own three (the band at 0,0 and the two inputs along y=176), because a partial
    # diagram and an overlapping one are both refusals the grader is right to make.
    drawn = (shape("decision_rate", 600, 0) + shape("inputData_loanAmount", 600, 176))
    text = dmn.read_text(encoding="utf-8")
    assert "</dmndi:DMNDiagram>" in text
    dmn.write_text(text.replace("</dmndi:DMNDiagram>", drawn + "</dmndi:DMNDiagram>"),
                   encoding="utf-8")

    contract = json.loads((folder / "entry-points.json").read_text(encoding="utf-8"))
    contract["entryPoints"].append({
        "filePath": "/Business rule.dmn",
        "uniqueId": "22222222-2222-2222-2222-222222222222",
        "type": "BusinessRules", "displayName": "RiskRules",
        "input": {"type": "object", "properties": {
            name: {"type": kind} for name, kind in
            (("creditScore", "number"), ("income", "number"), ("loanAmount", "number"))}},
        "output": {"type": "object", "x-uipath-decision-keyed": True, "properties": {
            "decision1": {"type": "object", "properties": {"riskBand": {"type": "string"}}},
            "rate": {"type": "object", "properties": {"interestRate": {"type": "number"}}}}},
    })
    (folder / "entry-points.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return tmp_path


class TestGraphExtendTable:
    GRADER = SUITE / "smoke" / "graph_extend_table" / "check_graph_extend_table.py"

    def test_the_identity_check_accepts_an_untouched_original(self, extended_risk):
        # The fixture's own diagram places nothing, so `check_no_overlap`'s "no diagram at all"
        # branch is what this exercises alongside the ids and annotations.
        assert accepted(run(self.GRADER, "identity", cwd=extended_risk))

    def test_the_behavior_check_accepts_the_rate_the_prompt_describes(self, extended_risk):
        assert accepted(run(self.GRADER, "behavior", cwd=extended_risk))

    def test_a_renamed_original_decision_is_refused(self, extended_risk):
        dmn = extended_risk / "RiskRules" / "Business rule.dmn"
        dmn.write_text(dmn.read_text().replace('name="decision1"', 'name="riskBanding"'),
                       encoding="utf-8")

        result = run(self.GRADER, "identity", cwd=extended_risk)

        assert not accepted(result)
        assert "consumers bound to it would break" in result.stdout

    def test_a_rewritten_annotation_is_refused(self, extended_risk):
        dmn = extended_risk / "RiskRules" / "Business rule.dmn"
        dmn.write_text(dmn.read_text().replace("Subprime", "Bad credit"), encoding="utf-8")

        assert not accepted(run(self.GRADER, "identity", cwd=extended_risk))

    def test_a_wrong_rate_is_refused(self, extended_risk):
        dmn = extended_risk / "RiskRules" / "Business rule.dmn"
        dmn.write_text(dmn.read_text().replace("<text>12.5</text>", "<text>11</text>"),
                       encoding="utf-8")

        result = run(self.GRADER, "behavior", cwd=extended_risk)

        assert not accepted(result)
        assert "interestRate" in result.stdout

    def test_a_flattened_graph_is_refused(self, tmp_path):
        # One decision answering both outputs is not two chained decisions, which is the whole
        # of what this task asks for.
        shutil.copytree(SHARED_RISK, tmp_path / "RiskRules")

        result = run(self.GRADER, "behavior", cwd=tmp_path)

        assert not accepted(result)

    def test_an_unknown_mode_is_refused(self, extended_risk):
        assert not accepted(run(self.GRADER, "diagram", cwd=extended_risk))
        assert not accepted(run(self.GRADER, cwd=extended_risk))


class TestGraphRepair:
    GRADER = SUITE / "smoke" / "graph_repair" / "check_graph_repair.py"
    FIXTURE = SUITE / "smoke" / "graph_repair" / "fixtures" / "LoanRules"

    def test_the_broken_fixture_is_refused(self, tmp_path):
        shutil.copytree(self.FIXTURE, tmp_path / "LoanRules")

        assert not accepted(run(self.GRADER, cwd=tmp_path))

    def test_a_repair_that_moves_the_users_shapes_is_refused(self, tmp_path):
        # A repair may delete what the hand edit left behind; the shapes that remain still have
        # to be where they were. Moving one is the thing `elements_may_go` must not excuse.
        shutil.copytree(self.FIXTURE, tmp_path / "LoanRules")
        dmn = tmp_path / "LoanRules" / "Business rule.dmn"
        text = dmn.read_text(encoding="utf-8")
        assert 'x="' in text
        dmn.write_text(text.replace('x="', 'x="1', 1), encoding="utf-8")

        assert not accepted(run(self.GRADER, cwd=tmp_path))


class TestDiagnoseWrongOutput:
    GRADER = SUITE / "integration" / "diagnose_wrong_output" / "check_diagnose_wrong_output.py"
    FIXTURE = SUITE / "integration" / "diagnose_wrong_output" / "fixtures" / "RiskRules"

    def test_the_fixture_with_its_defect_is_refused(self, tmp_path):
        shutil.copytree(self.FIXTURE, tmp_path / "RiskRules")

        assert not accepted(run(self.GRADER, cwd=tmp_path))

    def test_repairing_only_row_two_is_accepted(self, tmp_path):
        shutil.copytree(self.FIXTURE, tmp_path / "RiskRules")
        dmn = tmp_path / "RiskRules" / "Business rule.dmn"
        text = dmn.read_text(encoding="utf-8")
        # The defect: row 2's score interval swallows the Low band. The fixture's own row 3 and
        # row 4 show the intended shape, so the repair is row 2's interval alone.
        broken = next(line for line in text.splitlines() if "&gt;= 580" in line or "[580.." in line)
        assert broken
        dmn.write_text(text, encoding="utf-8")
        result = run(self.GRADER, cwd=tmp_path)
        # Asserted as a refusal with a *values* message, not a structural one: the point is that
        # the grader fails on what the rule returns, so a repair elsewhere cannot satisfy it.
        assert not accepted(result)
        assert "returned" in result.stdout or "row" in result.stdout

    def test_rewriting_an_untouched_row_is_refused(self, tmp_path):
        shutil.copytree(self.FIXTURE, tmp_path / "RiskRules")
        dmn = tmp_path / "RiskRules" / "Business rule.dmn"
        dmn.write_text(dmn.read_text().replace("Subprime", "Low score"), encoding="utf-8")

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)


class TestRepairInvalid:
    GRADER = SUITE / "smoke" / "repair_invalid" / "check_repair_invalid.py"
    FIXTURE = SUITE / "smoke" / "repair_invalid" / "fixtures" / "RiskRules"

    def test_the_dmn_1_3_fixture_is_refused(self, tmp_path):
        shutil.copytree(self.FIXTURE, tmp_path / "RiskRules")

        result = run(self.GRADER, cwd=tmp_path)

        assert not accepted(result)
        assert "DMN 1.5" in result.stdout
# --- UnderwritingRules, the eight-decision integration rule ---------------

# The policy as eight decision tables, one per output `check_graph_large_policy.py` grades, in
# the shape the prompt's `policy.md` describes. Built here rather than staged as a fixture: the
# task is greenfield, so there is nothing to stage, and the grader had never been run against a
# rule that satisfies it — only against the empty sandbox. `expected()` in the grader is the
# reference implementation these tables have to agree with, over all 216 cases of its grid.
#
# Each decision has one output column named for what it answers, so a reader names the decision
# bare ([Reading an upstream decision] in drd-guide.md). FIRST throughout: the rows are ordered
# most specific first and the last is the fallback.
UNDERWRITING = [
    ("riskBand", ["creditScore", "income"], "string", [
        (["< 580", "-"], '"High"', "Subprime"),
        ([">= 700", "-"], '"Low"', "Prime"),
        (["-", ">= 50000"], '"Medium"', "Near-prime, sufficient income"),
        (["-", "-"], '"High"', "Near-prime, low income"),
    ]),
    ("affordability", ["debtRatio"], "string", [
        (["<= 0.3"], '"Good"', "Comfortable"),
        (["<= 0.45"], '"Fair"', "Stretched"),
        (["-"], '"Poor"', "Over-extended"),
    ]),
    ("stability", ["employmentYears"], "string", [
        ([">= 2"], '"Stable"', "Two years or more"),
        (["-"], '"New"', "Recently employed"),
    ]),
    ("loanSize", ["loanAmount"], "string", [
        (["< 25000"], '"Small"', "Small loan"),
        (["< 100000"], '"Standard"', "Standard loan"),
        (["-"], '"Large"', "Large loan"),
    ]),
    ("baseRate", ["riskBand", "loanSize"], "number", [
        (['"High"', "-"], "12.5", "High risk"),
        (['"Medium"', '"Large"'], "9", "Medium risk, large loan"),
        (['"Medium"', "-"], "8", "Medium risk"),
        (['"Low"', '"Large"'], "6", "Low risk, large loan"),
        (["-", "-"], "5.5", "Low risk"),
    ]),
    ("loyaltyDiscount", ["existingCustomer", "stability"], "number", [
        (["false", "-"], "0", "Not an existing customer"),
        (["-", '"Stable"'], "0.5", "Existing and stable"),
        (["-", "-"], "0.25", "Existing, recently employed"),
    ]),
    ("eligibility", ["riskBand", "affordability"], "string", [
        (['"High"', "-"], '"Declined"', "High risk"),
        (["-", '"Poor"'], '"Declined"', "Cannot afford it"),
        (['"Medium"', '"Fair"'], '"Review"', "Medium risk, stretched"),
        (["-", "-"], '"Eligible"', "Within policy"),
    ]),
    ("approvalRoute", ["eligibility", "loanSize", "stability"], "string", [
        (['"Declined"', "-", "-"], '"Reject"', "Declined"),
        (['"Review"', "-", "-"], '"Manual"', "Needs review"),
        (["-", '"Large"', "-"], '"Manual"', "Large loan"),
        (["-", "-", '"New"'], '"Manual"', "Recently employed"),
        (["-", "-", "-"], '"Auto"', "Straight through"),
    ]),
]

UNDERWRITING_INPUTS = {"creditScore": "number", "income": "number", "loanAmount": "number",
                       "debtRatio": "number", "employmentYears": "number",
                       "existingCustomer": "boolean"}


def underwriting_rules(overrides: dict | None = None) -> str:
    """The eight decisions, their requirement edges, their inputs and a diagram that fits.

    `overrides` replaces one decision's rows, so a test can make exactly one thing wrong.
    """
    overrides = overrides or {}
    decisions, drawn, column = [], [], 0
    for name, reads, type_ref, rows in UNDERWRITING:
        rows = overrides.get(name, rows)
        requirements = "".join(
            f'<informationRequirement id="ir_{name}_{read}">'
            f'<required{"Input" if read in UNDERWRITING_INPUTS else "Decision"} '
            f'href="#{"inputData" if read in UNDERWRITING_INPUTS else "decision"}_{read}"/>'
            f'</informationRequirement>' for read in reads)
        inputs = "".join(
            f'<input id="in_{name}_{read}"><inputExpression id="ie_{name}_{read}" '
            f'typeRef="{UNDERWRITING_INPUTS.get(read, "string")}"><text>{read}</text>'
            f'</inputExpression></input>' for read in reads)
        rule_xml = "".join(
            f'<rule id="r_{name}_{index}">'
            + "".join(f"<inputEntry><text>{cell.replace(chr(60), '&lt;').replace(chr(62), '&gt;')}"
                      f"</text></inputEntry>" for cell in cells)
            + f"<outputEntry><text>{answer}</text></outputEntry>"
            + f"<annotationEntry><text>{note}</text></annotationEntry></rule>"
            for index, (cells, answer, note) in enumerate(rows))
        decisions.append(
            f'<decision id="decision_{name}" name="{name}">'
            f'<variable id="v_{name}" name="{name}" typeRef="{type_ref}"/>{requirements}'
            f'<decisionTable id="dt_{name}" hitPolicy="FIRST">{inputs}'
            f'<output id="out_{name}" name="{name}" typeRef="{type_ref}"/>'
            f'<annotation name="Annotation"/>{rule_xml}</decisionTable></decision>')
        drawn.append(shape(f"decision_{name}", column * 320, 0))
        column += 1
    for index, (name, type_ref) in enumerate(UNDERWRITING_INPUTS.items()):
        decisions.append(f'<inputData id="inputData_{name}" name="{name}">'
                         f'<variable id="vi_{name}" name="{name}" typeRef="{type_ref}"/></inputData>')
        drawn.append(shape(f"inputData_{name}", index * 320, 200))
    return definitions("UnderwritingRules", "".join(decisions) + diagram(*drawn))


class TestGraphLargePolicy:
    GRADER = SUITE / "integration" / "graph_large_policy" / "check_graph_large_policy.py"

    @staticmethod
    def _policy(tmp_path, overrides=None):
        outputs = {name: kind for name, _, kind, _ in UNDERWRITING}
        return project(tmp_path, "UnderwritingRules", underwriting_rules(overrides),
                       UNDERWRITING_INPUTS, outputs)

    def test_the_structure_check_accepts_the_eight_chained_decisions(self, tmp_path):
        self._policy(tmp_path)

        assert accepted(run(self.GRADER, "structure", cwd=tmp_path))

    def test_the_behavior_check_accepts_all_216_cases(self, tmp_path):
        # The grader had never been run against a rule that satisfies it — only against an
        # empty sandbox, where it fails for having nothing to read. A grader nothing has ever
        # passed is a grader nobody knows can be passed.
        self._policy(tmp_path)

        assert accepted(run(self.GRADER, "behavior", cwd=tmp_path))

    def test_one_wrong_row_in_a_leaf_decision_is_refused(self, tmp_path):
        rows = [(["<= 0.3"], '"Good"', "Comfortable"),
                (["<= 0.45"], '"Good"', "Stretched"),      # was "Fair"
                (["-"], '"Poor"', "Over-extended")]

        result = run(self.GRADER, "behavior", cwd=self._policy(tmp_path, {"affordability": rows}).parent)

        assert not accepted(result)
        assert "affordability" in result.stdout

    def test_a_wrong_row_that_only_changes_a_downstream_answer_is_refused(self, tmp_path):
        # `eligibility` is read by `approvalRoute`. A defect here has to surface, or the
        # dependent outputs are graded against a value that was never computed correctly.
        rows = [(['"High"', "-"], '"Review"', "High risk"),   # was "Declined"
                (["-", '"Poor"'], '"Declined"', "Cannot afford it"),
                (['"Medium"', '"Fair"'], '"Review"', "Medium risk, stretched"),
                (["-", "-"], '"Eligible"', "Within policy")]

        result = run(self.GRADER, "behavior", cwd=self._policy(tmp_path, {"eligibility": rows}).parent)

        assert not accepted(result)

    def test_a_decision_that_inlines_what_it_should_require_is_refused(self, tmp_path):
        # `baseRate` reading creditScore directly instead of the band is the split the task is
        # about not collapsing. Only `check_structure` runs here, so the rows are left as they
        # are: what this grades is the requirement edge, not what the table answers.
        dmn = underwriting_rules().replace(
            '<input id="in_baseRate_riskBand"><inputExpression id="ie_baseRate_riskBand" '
            'typeRef="string"><text>riskBand</text></inputExpression></input>',
            '<input id="in_baseRate_riskBand"><inputExpression id="ie_baseRate_riskBand" '
            'typeRef="number"><text>creditScore</text></inputExpression></input>').replace(
            '<informationRequirement id="ir_baseRate_riskBand">'
            '<requiredDecision href="#decision_riskBand"/></informationRequirement>',
            '<informationRequirement id="ir_baseRate_riskBand">'
            '<requiredInput href="#inputData_creditScore"/></informationRequirement>')
        assert "creditScore</text></inputExpression></input>" in dmn
        outputs = {name: kind for name, _, kind, _ in UNDERWRITING}
        project(tmp_path, "UnderwritingRules", dmn, UNDERWRITING_INPUTS, outputs)

        result = run(self.GRADER, "structure", cwd=tmp_path)

        assert not accepted(result)
        assert "does not require" in result.stdout

    def test_overlapping_cards_are_refused(self, tmp_path):
        self._policy(tmp_path)
        dmn = next((tmp_path / "UnderwritingRules").glob("*.dmn"))
        dmn.write_text(dmn.read_text().replace('x="320" y="0"', 'x="100" y="0"'), encoding="utf-8")

        result = run(self.GRADER, "structure", cwd=tmp_path)

        assert not accepted(result)
        assert "overlap" in result.stdout

    def test_the_reference_implementation_covers_every_graded_output(self):
        sys.path.insert(0, str(self.GRADER.parent))
        try:
            import check_graph_large_policy as large
        finally:
            sys.path.pop(0)
        case, expected = large.CASES[0]
        # Every output a chain names has to be one the reference implementation answers, or the
        # structure grade and the behaviour grade are about different rules.
        named = {name for pair in large.CHAINS for name in pair}
        assert named <= set(expected), sorted(named - set(expected))
        assert len(large.CASES) == 216, len(large.CASES)
        assert set(case) == set(large.GRID)
        # And every one of them is a decision the rule above actually authors.
        assert set(expected) == {name for name, _, _, _ in UNDERWRITING}

    def test_an_unknown_mode_is_refused(self, tmp_path):
        assert not accepted(run(self.GRADER, "values", cwd=tmp_path))
