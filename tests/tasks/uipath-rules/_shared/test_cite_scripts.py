"""Unit tests for skills/uipath-rules/scripts/cite.mjs and quotes.mjs. Run with ``pytest`` from any directory.

The fixture is the synthetic reimbursement policy in _setup/policy_digitized (dom.json built by build_dom.py),
plus small dom.json files written here for the matching edge cases.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "skills" / "uipath-rules" / "scripts"
CITE = SCRIPTS / "cite.mjs"
DOM = Path(__file__).resolve().parents[1] / "_setup" / "policy_digitized" / "dom.json"
UIPDM = "http://uipath.com/schema/1.0/dmn-ext/decision-model"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/" '
        'xmlns:uipath="http://uipath.com/schema/1.0/dmn/authoring" id="d" name="ReimbursementRules" namespace="urn:x">\n')
AUTHORING = '  <extensionElements><uipath:authoring surface="decision-table" /></extensionElements>\n'


def rule(rule_id, cell, out, extra=""):
    attr = f' id="{rule_id}"' if rule_id else ""
    return (f'      <rule{attr}>{extra}<inputEntry id="e_{rule_id}"><text>{cell}</text></inputEntry>'
            f'<outputEntry id="o_{rule_id}"><text>"{out}"</text></outputEntry></rule>\n')


def dmn(rules=None, lead=AUTHORING, inputs=None):
    rules = rules if rules is not None else [rule("deny_service", "&lt; 90", "Deny"), rule("refer_missing", "-", "Refer")]
    inputs = inputs if inputs is not None else [
        '  <inputData id="i1" name="serviceDays"><variable id="v1" name="serviceDays" typeRef="number" /></inputData>\n']
    return (HEAD + lead
            + '  <decision id="dec" name="ReimbursementRules"><variable id="dv" name="ReimbursementRules" typeRef="string" />\n'
            + '    <decisionTable id="t" hitPolicy="FIRST">\n'
            + '      <input id="c1"><inputExpression id="x1" typeRef="number"><text>serviceDays</text></inputExpression></input>\n'
            + '      <output id="o" name="outcome" typeRef="string" />\n'
            + "".join(rules) + "    </decisionTable>\n  </decision>\n" + "".join(inputs) + "</definitions>\n")


CITES = {
    "rules": {"deny_service": [{"page": 1, "quote": "eligible for reimbursement only after completing at least 90 days of service"}],
              "refer_missing": [{"page": 1, "quote": "the request is referred to the Finance team for review"}]},
    "inputs": {"serviceDays": {"sourceType": "document", "meaning": "Days of service completed",
                               "cites": [{"page": 1, "quote": "at least 90 days of service"}]}},
    "outcomes": {"Deny": {"none": "the policy says not eligible"},
                 "Refer": [{"page": 1, "quote": "referred to the Finance team"}]},
    "warnings": [{"text": "Not eligible read as Deny (p1)", "rule": "deny_service"}],
}


def run(text, cites=CITES, dom=DOM, write=True):
    with tempfile.TemporaryDirectory() as tmp:
        path, cpath = Path(tmp) / "rules.dmn", Path(tmp) / "cites.json"
        path.write_text(text, encoding="utf-8")
        cpath.write_text(json.dumps(cites), encoding="utf-8")
        args = ["node", str(CITE), "--dmn", str(path), "--cites", str(cpath), "--dom", str(dom)] + (["--write"] if write else [])
        done = subprocess.run(args, capture_output=True, text=True)
        report = json.loads(done.stdout)
        return done.returncode, report, path.read_text(encoding="utf-8")


def rerun(text, cites=CITES):
    """Write twice; the second run must change nothing."""
    code, report, once = run(text, cites)
    _, _, twice = run(once, cites)
    return code, report, once, twice


def problems(report):
    return [p["problem"] for p in report["problems"]]


def word_dom(lines_by_page):
    """A dom.json from lines of words, one visual line each, in the digitizer's [top, left, width, height] boxes."""
    pages = []
    for index, lines in enumerate(lines_by_page):
        words = []
        for n, line in enumerate(lines):
            x = 100
            for token in line.split(" "):
                words.append({"box": [100 + 50 * n, x, 10 * len(token), 30], "text": token, "visualLineNumber": n})
                x += 10 * len(token) + 8
        pages.append({"pageIndex": index, "sections": [{"words": words}]})
    return {"pages": pages}


def resolve(lines, quote):
    with tempfile.TemporaryDirectory() as tmp:
        dom = Path(tmp) / "dom.json"
        dom.write_text(json.dumps(word_dom([lines])), encoding="utf-8")
        script = (f"import {{ domPages, resolveQuote }} from '{(SCRIPTS / 'quotes.mjs').as_posix()}';"
                  f"import {{ readFileSync }} from 'node:fs';"
                  f"const p = domPages(JSON.parse(readFileSync({json.dumps(str(dom))}, 'utf8')));"
                  f"console.log(JSON.stringify(resolveQuote(p, 1, {json.dumps(quote)})))")
        done = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        return json.loads(done.stdout)


# ---- the happy path ----------------------------------------------------------------------------------------------

def test_clean_cites_write_every_element_and_pass_the_schema_check():
    code, report, once, twice = rerun(dmn())
    assert code == 0, report["problems"]
    assert report["coverage"] == {"rules": "2/2", "inputs": "1/1", "outcomes": "2/2"}
    assert report["written"] == {"rules": 2, "inputs": 1, "warnings": 1}
    assert "0 invalid" in report["uipdmCheck"]
    assert once.count("<uipdm:sourceRefs>") == 2 and 'sourceType="document"' in once
    assert once == twice


def test_a_box_is_left_top_width_height_of_the_quoted_words():
    _, _, text = run(dmn())
    box = re.search(r'<uipdm:sourceRef page="1" box="([^"]+)"', text).group(1)
    left, top, width, height = map(float, box.split(","))
    words = [w for s in json.loads(DOM.read_text())["pages"][0]["sections"] for g in s["wordGroups"] for w in g["words"]]
    first = next(w for w in words if w["text"] == "eligible")
    assert (left, top) == (first["box"][1], first["box"][0]) and width > 0 and height == first["box"][3]


def test_without_write_the_file_is_untouched():
    code, _, text = run(dmn(), write=False)
    assert code == 0 and text == dmn()


# ---- what cite.mjs reports ---------------------------------------------------------------------------------------

def test_uncited_unknown_and_missing_ids_are_reported():
    cites = {**CITES, "rules": {"deny_service": CITES["rules"]["deny_service"], "ghost": [{"page": 1, "quote": "x y"}]}}
    code, report, _ = run(dmn(), cites)
    assert code == 1 and "not cited" in problems(report) and "not a rule in the .dmn" in problems(report)


def test_a_row_without_an_id_or_with_a_duplicate_id_is_reported():
    rows = [rule("deny_service", "&lt; 90", "Deny"), rule("deny_service", "-", "Refer"), rule("", "-", "Refer")]
    code, report, _ = run(dmn(rows), {**CITES, "rules": {"deny_service": CITES["rules"]["deny_service"]}})
    assert code == 1
    assert "two rule rows share this id" in problems(report)
    assert any("has no id" in p for p in problems(report))


def test_an_outcome_the_document_does_not_state_may_cite_none():
    code, report, _ = run(dmn())
    assert code == 0 and report["coverage"]["outcomes"] == "2/2"


def test_none_needs_a_reason():
    cites = {**CITES, "outcomes": {**CITES["outcomes"], "Deny": {"none": " "}}}
    assert '"none" needs a reason' in problems(run(dmn(), cites)[1])


def test_a_one_word_quote_is_too_short():
    cites = {**CITES, "rules": {**CITES["rules"], "refer_missing": [{"page": 1, "quote": "referred"}]}}
    assert "quote at least 2 words" in problems(run(dmn(), cites)[1])


def test_a_quote_on_the_wrong_page_says_where_it_is():
    cites = {**CITES, "rules": {**CITES["rules"], "refer_missing": [{"page": 2, "quote": "referred to the Finance team for review"}]}}
    report = run(dmn(), cites)[1]
    assert any(p.get("foundOnPage") == 1 for p in report["problems"])


def test_malformed_cites_are_a_usage_error_not_a_crash():
    with tempfile.TemporaryDirectory() as tmp:
        path, cpath = Path(tmp) / "r.dmn", Path(tmp) / "c.json"
        path.write_text(dmn(), encoding="utf-8")
        cpath.write_text("null", encoding="utf-8")
        done = subprocess.run(["node", str(CITE), "--dmn", str(path), "--cites", str(cpath), "--dom", str(DOM)], capture_output=True, text=True)
    assert done.returncode == 2 and json.loads(done.stdout)["status"] == "error"


def test_citations_need_dom_json():
    done = subprocess.run(["node", str(CITE), "--dmn", "x.dmn", "--cites", "c.json"], capture_output=True, text=True)
    assert done.returncode == 2 and "dom.json" in done.stdout


# ---- where --write puts things -----------------------------------------------------------------------------------

def test_a_warning_names_its_row_in_the_text_not_as_conditionId():
    _, _, text = run(dmn())
    assert "conditionId" not in text
    assert "<uipdm:qualityWarning>[row deny_service] Not eligible read as Deny (p1)</uipdm:qualityWarning>" in text


def test_warnings_join_the_definitions_extension_after_a_description_and_comment():
    lead = "  <!-- note -->\n  <description>Policy v3</description>\n" + AUTHORING
    code, _, once, twice = rerun(dmn(lead=lead))
    assert code == 0 and once == twice
    assert once.count("<extensionElements>") == 1 + 2 + 1  # definitions, two rows, one input
    head = once.split("<decision")[0]
    assert head.index("<description>") < head.index("<uipdm:qualityWarning") < head.index("<uipath:authoring")


def test_a_definitions_without_extension_elements_gets_one():
    code, _, once, twice = rerun(dmn(lead=""))
    assert code == 0 and once == twice and "<uipdm:qualityWarning>" in once.split("<decision")[0]


def test_an_empty_extension_elements_on_a_row_is_filled_not_duplicated():
    rows = [rule("deny_service", "&lt; 90", "Deny", "<extensionElements/>"), rule("refer_missing", "-", "Refer")]
    _, _, once, twice = rerun(dmn(rows))
    row = once.split('<rule id="deny_service">')[1].split("</rule>")[0]
    assert row.count("extensionElements>") == 2 and "<uipdm:sourceRefs>" in row and once == twice


def test_source_refs_never_land_inside_an_input_entry():
    rows = [rule("deny_service", "&lt; 90", "Deny").replace("<text>&lt; 90", "<description>under 90</description><text>&lt; 90"),
            rule("refer_missing", "-", "Refer")]
    _, _, text = run(dmn(rows))
    entry = text.split('<inputEntry id="e_deny_service">')[1].split("</inputEntry>")[0]
    assert "sourceRefs" not in entry


def test_a_self_closing_input_data_does_not_swallow_the_next_one():
    inputs = ['  <inputData id="i0" name="age"/>\n',
              '  <inputData id="i1" name="serviceDays"><variable id="v1" name="serviceDays" typeRef="number" /></inputData>\n']
    cites = {**CITES, "inputs": {**CITES["inputs"], "age": {"sourceType": "system", "cites": {"none": "from the HR system"}}}}
    code, report, text = run(dmn(inputs=inputs), cites)
    assert '<inputData id="i0" name="age"/>' in text
    service = text.split('name="serviceDays">')[1].split("</inputData>")[0]
    assert service.count("<uipdm:inputVariable") == 1 and 'sourceType="document"' in service


def test_dollar_signs_in_a_meaning_are_written_as_they_are():
    cites = {**CITES, "inputs": {"serviceDays": {**CITES["inputs"]["serviceDays"], "meaning": "costs $' and $& and $$5"}}}
    _, _, once, twice = rerun(dmn(), cites)
    assert "sourceMapping=\"costs $' and $&amp; and $$5\"" in once and once == twice


def test_data_type_is_written_only_for_a_categorical_string():
    inputs = ['  <inputData id="i1" name="serviceDays"><variable id="v1" name="serviceDays" typeRef="number" /></inputData>\n',
              '  <inputData id="i2" name="tier"><variable id="v2" name="tier" typeRef="string" /></inputData>\n']
    cites = {**CITES, "inputs": {"serviceDays": {**CITES["inputs"]["serviceDays"], "values": [90]},
                                 "tier": {"sourceType": "system", "values": ["Gold", "Silver"], "cites": {"none": "plan data"}}}}
    _, _, text = run(dmn(inputs=inputs), cites)
    assert 'dataType="numeric"' not in text and text.count('dataType="categorical"') == 1


def test_a_removed_citation_takes_its_boxes_with_it():
    _, _, once = run(dmn())
    cites = {**CITES, "rules": {**CITES["rules"], "refer_missing": {"none": "catch-all"}}}
    _, _, again = run(once, cites)
    assert again.count("<uipdm:sourceRefs>") == 1


# ---- quote matching ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("line, quote", [
    ("defined as ≥ 15 days per month", "defined as ≥ 15 days per month"),
    ("defined as ≥ 15 days per month", "defined as 15 days per month"),
    ("Approved by Pharmacy & Therapeutics Committee", "Approved by Pharmacy & Therapeutics Committee"),
    ("Beta blockers - Metoprolol 200 mg", "Beta blockers - Metoprolol 200 mg"),
    ("Patient is <18 years or >65 years of age", "Patient is <18 years or >65 years of age"),
    ("hemoglobin < 10 g/dL and ferritin > 100", "hemoglobin < 10 g/dL and ferritin > 100"),
    ("the ﬁrst dose of 5–10 mg", "the first dose of 5-10 mg"),
    ("costs $1,000 or 1.5% of the loan.", "costs $1,000 or 1.5% of the loan"),
], ids=["symbol word", "symbol dropped", "ampersand", "dash word", "lt gt thresholds", "spaced lt gt", "ligature and en dash", "money"])
def test_quotes_resolve(line, quote):
    assert resolve([line, "an unrelated line of text"], quote)["status"] == "resolved"


def test_html_table_markup_in_a_quote_is_ignored():
    assert resolve(["Drug name Dose limit"], "<td>Drug name</td><td>Dose limit</td>")["status"] == "resolved"


def test_a_quote_on_two_lines_resolves_and_a_repeated_one_is_ambiguous():
    assert resolve(["the patient must be", "at least 18 years old"], "must be at least 18 years")["status"] == "resolved"
    assert resolve(["at least 18 years", "at least 18 years"], "at least 18 years")["status"] == "ambiguous"


def test_a_reworded_quote_is_not_found():
    assert resolve(["the patient must be at least 18 years old"], "patients must be 18 or older")["status"] == "unresolved"
