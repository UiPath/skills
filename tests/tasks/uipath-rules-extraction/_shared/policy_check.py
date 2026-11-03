#!/usr/bin/env python3
"""Shared grading for the uipath-rules-extraction tasks.

The agent turns `policy/document.md` (a remote-work equipment reimbursement
policy) into a BusinessRules project named ReimbursementRules. Modes:

  validate  `uip rules validate` passes.
  profile   inputs/outputs as the prompt fixed them, a uipdm:inputVariable per
            input, no pipeline-state elements, no input built from the policy's
            permissive "may submit receipts" sentence.
  outcomes  the table returns the expected outcome for every SCENARIO (the
            answer key; it lives here and is never staged into the sandbox).
  norefs    no uipdm:sourceRef anywhere (no digitizer positions were supplied).
  notes     review-notes.md exists and records the assumptions made.
  refs      every uipdm:sourceRef box is exactly the box of a contiguous run of
            words in _setup/policy_digitized/dom.json, on the page it names.

The DMN is authored by the agent under test and parsed with stdlib ElementTree.
Single-decision tables only; helpers come from the vendored rules_check.py.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_check as rc  # noqa: E402  (a copy of ../../uipath-rules/_shared/rules_check.py; test_policy_check.py pins them equal)

PROJECT_NAME = "ReimbursementRules"
INPUTS = {"serviceDays": "number", "requestAmount": "number",
          "hasDirectorPreApproval": "boolean", "hasMedicalAccommodation": "boolean"}
OUTPUT = "outcome"
UIPDM = "http://uipath.com/schema/1.0/dmn-ext/decision-model"
PIPELINE_STATE = ("review", "ruleState", "parkedRule", "scoreBand", "conditionState", "agentAssessment")
DOM = HERE.parent / "_setup" / "policy_digitized" / "dom.json"

# (serviceDays, requestAmount, hasDirectorPreApproval, hasMedicalAccommodation) -> outcome
SCENARIOS = [
    ("S01 typical small request", (120, 300, False, False), "Approve"),
    ("S02 boundaries: 90 days, $500", (90, 500, False, False), "Approve"),
    ("S03 one day short of eligibility", (89, 300, False, False), "Deny"),
    ("S04 medical accommodation waives service length", (30, 300, False, True), "Approve"),
    ("S05 mid band with pre-approval", (200, 501, True, False), "Approve"),
    ("S06 mid band without pre-approval", (200, 501, False, False), "Deny"),
    ("S07 boundary: $2,000 with pre-approval", (200, 2000, True, False), "Approve"),
    ("S08 above $2,000 even with pre-approval", (200, 2001, True, False), "Deny"),
    ("S09 service length not stated", (None, 300, False, False), "Refer"),
    ("S10 amount not stated", (200, None, False, False), "Refer"),
    ("S11 accommodation does not lift the $2,000 cap", (30, 3000, False, True), "Deny"),
    ("S12 accommodation plus pre-approval, short service", (30, 800, True, True), "Approve"),
    ("S13 short service, no accommodation, mid band", (89, 800, True, False), "Deny"),
    ("S14 accommodation does not waive director pre-approval", (150, 1500, False, True), "Deny"),
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def load() -> tuple[Path, Path, ET.Element]:
    project = rc.find_project(PROJECT_NAME)
    dmn_file, root = rc.load_rule(project)
    return project, dmn_file, root


def split_list(cell: str) -> list[str]:
    """Split a FEEL list of unary tests on the commas that sit outside double quotes."""
    parts, current, quoted = [], "", False
    for char in cell:
        if char == '"':
            quoted = not quoted
        if char == "," and not quoted:
            parts.append(current)
            current = ""
        else:
            current += char
    return [part.strip() for part in parts + [current]]


def cell_matches(cell: str, value: object) -> bool:
    """A FEEL unary test where a missing (null) input matches only `-`, `null`, or a list containing `null`."""
    cell = cell.strip()
    if cell in ("", "-"):
        return True
    parts = split_list(cell)
    if len(parts) > 1:
        return any(cell_matches(part, value) for part in parts)
    if cell == "null":
        return value is None
    if cell == "not(null)":
        return value is not None
    if value is None:
        return False
    return rc.unary_test(cell, value)


def evaluate(table: ET.Element, inputs: dict) -> str | None:
    columns = rc.input_columns(table)
    names = rc.output_names(table)
    out = names.index(OUTPUT)
    hits = []
    for rule in table.findall("dmn:rule", rc.NS):
        cells = [(e.findtext("dmn:text", default="", namespaces=rc.NS) or "") for e in rule.findall("dmn:inputEntry", rc.NS)]
        if all(cell_matches(cell, inputs[column]) for cell, column in zip(cells, columns)):
            values = [(e.findtext("dmn:text", default="", namespaces=rc.NS) or "") for e in rule.findall("dmn:outputEntry", rc.NS)]
            hits.append(rc.literal(values[out]))
    policy = table.get("hitPolicy", "UNIQUE")
    if policy == "UNIQUE" and len(hits) > 1:
        fail(f"{inputs} matches {len(hits)} rows of a UNIQUE table")
    if policy not in ("FIRST", "UNIQUE", "ANY"):
        fail(f"hit policy {policy} is outside the single-result policies this check evaluates")
    return hits[0] if hits else None


def grade_outcomes() -> None:
    _, _, root = load()
    table = rc.table_of(root)
    columns = rc.input_columns(table)
    unknown = [c for c in columns if c not in INPUTS]
    if unknown:
        fail(f"input columns {unknown} are not among the inputs the prompt named")
    wrong = []
    for label, values, expected in SCENARIOS:
        inputs = dict(zip(INPUTS, values))
        actual = evaluate(table, inputs)
        if actual != expected:
            wrong.append(f"{label}: returned {actual!r}, expected {expected!r}")
    if wrong:
        fail(f"{len(wrong)} of {len(SCENARIOS)} scenarios wrong:\n  " + "\n  ".join(wrong))
    print(f"OK: all {len(SCENARIOS)} scenarios match")


def uipdm_elements(root: ET.Element, name: str) -> list[ET.Element]:
    return [el for el in root.iter(f"{{{UIPDM}}}{name}")]


def grade_profile() -> None:
    project, dmn_file, root = load()
    rc.check_input_data(root, INPUTS)
    outputs = rc.output_names(rc.table_of(root))
    if outputs != [OUTPUT]:
        fail(f"output columns are {outputs}, expected {[OUTPUT]}")
    rc.check_contract(project, dmn_file, root, INPUTS, {OUTPUT: "string"})
    declared = {el.get("source") or "" for el in uipdm_elements(root, "inputVariable")}
    if len(uipdm_elements(root, "inputVariable")) < len(INPUTS):
        fail(f"{len(uipdm_elements(root, 'inputVariable'))} uipdm:inputVariable elements, expected one per input ({len(INPUTS)})")
    for el in uipdm_elements(root, "inputVariable"):
        if el.get("sourceType") not in ("document", "system"):
            fail(f"inputVariable sourceType is {el.get('sourceType')!r}, expected document or system")
    for state in PIPELINE_STATE:
        if uipdm_elements(root, state):
            fail(f"wrote uipdm:{state}, which only the extraction pipeline or a reviewer sets")
    text = dmn_file.read_text(encoding="utf-8").lower()
    if any(word in text for word in ("receiptformat", "receipttype", "receiptpdf")):
        fail("built an input from the permissive 'may submit receipts as a PDF or photo' sentence")
    print(f"OK: inputs, output, contract and uipdm inputVariables hold ({len(declared)} sources)")


def grade_norefs() -> None:
    _, _, root = load()
    found = uipdm_elements(root, "sourceRef")
    if found:
        fail(f"{len(found)} uipdm:sourceRef elements written although no digitizer positions were supplied")
    print("OK: no sourceRef without digitizer positions")


def find_one(name: str) -> Path:
    found = sorted(Path(".").rglob(name))
    if not found:
        fail(f"no {name} written under the sandbox")
    return found[0]


def grade_notes() -> None:
    text = find_one("review-notes.md").read_text(encoding="utf-8").lower()
    if "assum" not in text:
        fail("review-notes.md does not record the assumptions made")
    print("OK: review-notes.md records the assumptions made")


def word_runs(dom: dict) -> dict[int, set[str]]:
    """Per 1-based page, the `left,top,width,height` of every contiguous word run on one visual line."""
    def collect(node):
        if isinstance(node, list):
            return [w for item in node for w in collect(item)]
        if not isinstance(node, dict):
            return []
        own = node.get("words") if isinstance(node.get("words"), list) else []
        return own + [w for key, value in node.items() if key != "words" for w in collect(value)]

    runs: dict[int, set[str]] = {}
    for page in dom["pages"]:
        lines: dict[int, list] = {}
        for word in collect(page["sections"]):
            lines.setdefault(word["visualLineNumber"], []).append(word["box"])
        boxes = set()
        for line in lines.values():
            line.sort(key=lambda b: b[1])
            for i in range(len(line)):
                for j in range(i, len(line)):
                    part = line[i:j + 1]
                    left = min(b[1] for b in part)
                    top = min(b[0] for b in part)
                    right = max(b[1] + b[2] for b in part)
                    bottom = max(b[0] + b[3] for b in part)
                    boxes.add(f"{left:g},{top:g},{right - left:g},{bottom - top:g}")
        runs[page["pageIndex"] + 1] = boxes
    return runs


def grade_refs() -> None:
    _, _, root = load()
    refs = uipdm_elements(root, "sourceRef")
    if len(refs) < 4:
        fail(f"{len(refs)} uipdm:sourceRef elements; the policy has at least 6 rows and positions were supplied")
    runs = word_runs(json.loads(DOM.read_text(encoding="utf-8")))
    invalid = []
    for ref in refs:
        page, box = int(ref.get("page", "0")), (ref.get("box") or "").replace(" ", "")
        if box not in runs.get(page, set()):
            invalid.append(f"page {page} box {box!r}")
    if invalid:
        fail(f"{len(invalid)} of {len(refs)} sourceRef boxes are not the box of any word run in dom.json "
             f"(written or estimated by hand?): {invalid[:5]}")
    print(f"OK: all {len(refs)} sourceRef boxes are word-run boxes from dom.json")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "outcomes"
    if mode == "validate":
        rc.run_validate(rc.find_project(PROJECT_NAME))
        print("OK: uip rules validate passes")
    elif mode in ("profile", "outcomes", "norefs", "refs", "notes"):
        {"profile": grade_profile, "outcomes": grade_outcomes, "norefs": grade_norefs, "refs": grade_refs,
         "notes": grade_notes}[mode]()
    else:
        fail(f"unknown mode {mode!r}")
