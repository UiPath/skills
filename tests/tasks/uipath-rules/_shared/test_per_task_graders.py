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
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_check as rc  # noqa: E402
from fixture_inventory import SUITE  # noqa: E402


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
    """A `.dmn` whose authoring surface matches what `body` holds.

    Derived rather than passed, so a test that adds a second decision or a knowledge model to a
    submission cannot forget to flip it — which is the mistake the surface check exists to catch.
    """
    needs_canvas = (body.count("<decision ") > 1
                    or "<businessKnowledgeModel" in body or "<textAnnotation" in body)
    surface = rc.GRAPH_SURFACE if needs_canvas else rc.TABLE_SURFACE
    return (f'<?xml version="1.0" encoding="UTF-8" ?>\n'
            f'<definitions xmlns="{rc.DMN_NS}" xmlns:dmndi="https://www.omg.org/spec/DMN/20230324/DMNDI/" '
            f'xmlns:dc="http://www.omg.org/spec/DMN/20180521/DC/" '
            f'xmlns:uipath="{rc.UIPATH_NS}" id="definitions_{name}" '
            f'name="{name}" namespace="urn:{name}">'
            f'<extensionElements><uipath:authoring surface="{surface}" /></extensionElements>'
            f'{body}</definitions>')


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
# --- UnderwritingRules, the eight-decision integration rule ---------------

# --- graph_extend_brownfield, whose criteria used to score an untouched fixture ---

FREIGHT_DECISION = (
    '<decision id="decision_freight" name="freight" label="Freight">'
    '<variable id="variable_freight" name="freight" typeRef="number" />'
    '<informationRequirement id="ir_freight_tier">'
    '<requiredDecision href="#decision_tier"/></informationRequirement>'
    '<knowledgeRequirement id="kr_freight">'
    '<requiredKnowledge href="#bkm_discounted"/></knowledgeRequirement>'
    '<decisionTable id="dt_freight" hitPolicy="FIRST">'
    '<input id="in_freight_tier"><inputExpression id="ie_freight_tier" typeRef="number">'
    '<text>tier</text></inputExpression></input>'
    '<output id="out_freight" name="freight" typeRef="number" /><annotation name="Annotation"/>'
    '<rule id="r_freight"><inputEntry><text>-</text></inputEntry>'
    '<outputEntry><text>discounted(50, tier)</text></outputEntry>'
    '<annotationEntry><text>Flat 50, tier discount</text></annotationEntry></rule>'
    '</decisionTable></decision>')


@pytest.fixture
def priced(tmp_path):
    """The PricingRules fixture with the freight decision its prompt asks for, card drawn."""
    fixture = SUITE / "smoke" / "graph_extend_brownfield" / "fixtures" / "PricingRules"
    shutil.copytree(fixture, tmp_path / "PricingRules")
    dmn = tmp_path / "PricingRules" / "Business rule.dmn"
    text = dmn.read_text(encoding="utf-8").replace(
        "</definitions>", FREIGHT_DECISION + "</definitions>")
    # Clear of every shape the fixture placed, so `check_no_overlap` is not what fails.
    right = max(int(x) for x in re.findall(r'x="(\d+)"', text)) + 400
    card = (f'<dmndi:DMNShape id="DMNShape_freight" dmnElementRef="decision_freight">'
            f'<dc:Bounds x="{right}" y="0" width="288" height="96" /></dmndi:DMNShape>')
    dmn.write_text(text.replace("</dmndi:DMNDiagram>", card + "</dmndi:DMNDiagram>"),
                   encoding="utf-8")
    return tmp_path


class TestGraphExtendBrownfield:
    """`kept` and `diagram` awarded 5.0 of this task's 12.0 for staging the fixture and stopping.

    Both now ask whether there is an edit before grading what survived it. The point of these
    tests is the other direction: a correct submission still passes, so the fix did not simply
    make the task harder.
    """

    GRADER = SUITE / "smoke" / "graph_extend_brownfield" / "check_graph_extend_brownfield.py"

    @pytest.mark.parametrize("mode", ["kept", "wired", "diagram"])
    def test_a_correct_edit_is_accepted(self, priced, mode):
        assert accepted(run(self.GRADER, mode, cwd=priced))

    def test_an_added_decision_with_no_card_is_refused_by_diagram(self, tmp_path):
        # Adding the decision and skipping `uip rules format` leaves it off the canvas, which is
        # the failure `diagram` exists to catch and the half its docstring already claimed.
        fixture = SUITE / "smoke" / "graph_extend_brownfield" / "fixtures" / "PricingRules"
        shutil.copytree(fixture, tmp_path / "PricingRules")
        dmn = tmp_path / "PricingRules" / "Business rule.dmn"
        dmn.write_text(dmn.read_text(encoding="utf-8").replace(
            "</definitions>", FREIGHT_DECISION + "</definitions>"), encoding="utf-8")

        result = run(self.GRADER, "diagram", cwd=tmp_path)

        assert not accepted(result)
        assert "uip rules format" in result.stdout

    def test_moving_a_users_shape_is_still_refused(self, priced):
        # The survival half has to keep working beside the new "was anything added" half.
        dmn = priced / "PricingRules" / "Business rule.dmn"
        text = dmn.read_text(encoding="utf-8")
        dmn.write_text(text.replace('x="', 'x="1', 1), encoding="utf-8")

        assert not accepted(run(self.GRADER, "diagram", cwd=priced))

    def test_rewriting_the_kept_formula_is_still_refused(self, priced):
        dmn = priced / "PricingRules" / "Business rule.dmn"
        text = dmn.read_text(encoding="utf-8")
        assert "amount * (1 - pct / 100)" in text
        dmn.write_text(text.replace("amount * (1 - pct / 100)", "amount"), encoding="utf-8")

        assert not accepted(run(self.GRADER, "kept", cwd=priced))
