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
import re
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
        if len(cells) != len(columns):
            fail(f"a rule has {len(cells)} input entries for {len(columns)} input columns")
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


def word_run_texts(dom: dict) -> dict[int, dict[str, str]]:
    """Per 1-based page, `left,top,width,height` -> text (letters and digits only) of every contiguous word run on one visual line."""
    def collect(node):
        if isinstance(node, list):
            return [w for item in node for w in collect(item)]
        if not isinstance(node, dict):
            return []
        own = node.get("words") if isinstance(node.get("words"), list) else []
        return own + [w for key, value in node.items() if key != "words" for w in collect(value)]

    runs: dict[int, dict[str, str]] = {}
    for page in dom["pages"]:
        lines: dict[int, list] = {}
        for word in collect(page["sections"]):
            lines.setdefault(word["visualLineNumber"], []).append(word)
        boxes: dict[str, str] = {}
        for line in lines.values():
            line.sort(key=lambda w: w["box"][1])
            for i in range(len(line)):
                for j in range(i, len(line)):
                    part = line[i:j + 1]
                    left = min(w["box"][1] for w in part)
                    top = min(w["box"][0] for w in part)
                    right = max(w["box"][1] + w["box"][2] for w in part)
                    bottom = max(w["box"][0] + w["box"][3] for w in part)
                    boxes[f"{left:g},{top:g},{right - left:g},{bottom - top:g}"] = squash("".join(w.get("text", "") for w in part))
        runs[page["pageIndex"] + 1] = boxes
    return runs


def word_runs(dom: dict) -> dict[int, set[str]]:
    """Per 1-based page, the `left,top,width,height` of every contiguous word run on one visual line."""
    return {page: set(boxes) for page, boxes in word_run_texts(dom).items()}


def squash(text: str) -> str:
    """Letters and digits only, lower case: a quote and a word run compare equal across spacing and punctuation."""
    return re.sub(r"[^0-9a-z]", "", text.lower())


def page_texts(markdown: str) -> dict[int, str]:
    """document.md split on its `<!-- page: N -->` markers, reduced by squash()."""
    parts = re.split(r"<!--\s*page:\s*(\d+)\s*-->", markdown)
    return {int(parts[k]): squash(parts[k + 1]) for k in range(1, len(parts) - 1, 2)}


def check_refs(refs: list[tuple[int, str]], cites: list[dict], pages: dict[int, str],
               texts: dict[int, dict[str, str]]) -> list[str]:
    """Problems tying every sourceRef box to a verbatim quote the agent cited: the quote is on its page of
    document.md, and the box is exactly the word run holding that quote (not just any word run)."""
    problems = []
    quotes: dict[int, set[str]] = {}
    for cite in cites:
        page, quote = int(cite.get("page", 0)), squash(str(cite.get("quote", "")))
        if not quote or quote not in pages.get(page, ""):
            problems.append(f"cite {cite.get('id')!r}: quote is not verbatim text on page {page} of document.md")
        quotes.setdefault(page, set()).add(quote)
    for page, box in refs:
        text = texts.get(page, {}).get(box)
        if text is None:
            problems.append(f"page {page} box {box!r} is not the box of any word run in dom.json (written or estimated by hand?)")
        elif text not in quotes.get(page, set()):
            problems.append(f"page {page} box {box!r} holds {text[:40]!r}, which no cited quote on that page matches")
    return problems


def grade_refs() -> None:
    _, _, root = load()
    refs = uipdm_elements(root, "sourceRef")
    if len(refs) < 4:
        fail(f"{len(refs)} uipdm:sourceRef elements; the policy has at least 6 rows and positions were supplied")
    cites = json.loads(find_one("cites.json").read_text(encoding="utf-8"))
    pages = page_texts(find_one("document.md").read_text(encoding="utf-8"))
    texts = word_run_texts(json.loads(DOM.read_text(encoding="utf-8")))
    pairs = [(int(ref.get("page", "0")), (ref.get("box") or "").replace(" ", "")) for ref in refs]
    problems = check_refs(pairs, cites, pages, texts)
    if problems:
        fail(f"{len(problems)} citation problems:\n  " + "\n  ".join(problems[:6]))
    print(f"OK: all {len(refs)} sourceRef boxes are word-run boxes holding a quote the agent cited")


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
