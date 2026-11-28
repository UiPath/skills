#!/usr/bin/env python3
"""Grading for the uipath-rules tasks that build a rule from a policy document (the Extraction Guide).

The agent turns `policy/document.md` (a remote-work equipment reimbursement policy, with `dom.json` when the
digitizer ran) into a BusinessRules project named ReimbursementRules. Modes:

  validate  `uip rules validate` passes.
  profile   inputs and output as the prompt named them, the entry-point contract, a <description> on every
            inputData, and no input built from the policy's permissive "may submit receipts" sentence.
  outcomes  the table returns the expected outcome on every SCENARIO (the answer key; it lives here and is
            never staged into the sandbox), including requests whose facts are missing.
  tests     tests.json follows the guide's format, covers every outcome, names rows the table has, and has a
            missing-input case.
  norefs    no uipdm:sourceRefs (no digitizer output was supplied, so the rule carries no citations).
  refs      cites.json passes cite.mjs, and the .dmn's uipdm elements are exactly what cite.mjs writes from it:
            no box written or edited by hand. check-uipdm.mjs passes and no qualityWarning has a conditionId.
  engine    `uip rules debug` returns the expected outcome on every SCENARIO with both numbers stated, and
            test-results.json records a run of every tests.json case, all passing.

The DMN is authored by the agent under test and parsed with stdlib ElementTree.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_check as rc  # noqa: E402

PROJECT_NAME = "ReimbursementRules"
INPUTS = {"serviceDays": "number", "requestAmount": "number",
          "hasDirectorPreApproval": "boolean", "hasMedicalAccommodation": "boolean"}
OUTPUT = "outcome"
OUTCOMES = ("Approve", "Deny", "Refer")
UIPDM = "http://uipath.com/schema/1.0/dmn-ext/decision-model"
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
    ("S15 nothing stated", (None, None, None, None), "Refer"),
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def load() -> tuple[Path, Path, ET.Element]:
    project = rc.find_project(PROJECT_NAME)
    dmn_file, root = rc.load_rule(project)
    return project, dmn_file, root


def uipdm(root: ET.Element, name: str) -> list[ET.Element]:
    return list(root.iter(f"{{{UIPDM}}}{name}"))


def find_one(name: str) -> Path:
    found = sorted(p for p in Path(".").rglob(name) if "node_modules" not in p.parts)
    if not found:
        fail(f"no {name} written under the sandbox")
    return found[0]


def skill_script(name: str) -> Path:
    """The skill's own script: the plugin mount in CI, else this checkout."""
    for base in (os.environ.get("SKILLS_REPO_PATH"), str(HERE.parents[3])):
        if base and (Path(base) / "skills" / "uipath-rules" / "scripts" / name).is_file():
            return Path(base) / "skills" / "uipath-rules" / "scripts" / name
    fail(f"cannot find skills/uipath-rules/scripts/{name}")
    raise AssertionError


# ---- evaluating the table offline ------------------------------------------------------------------------------

def split_list(cell: str) -> list[str]:
    """Split a FEEL list of unary tests on the commas outside double quotes."""
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
    """A FEEL unary test as the engine runs it: a missing (null) input matches `-`, `null`, a list holding `null`, and a
    negated test such as `not(true)` or `not("A")` (checked on the local engine), but no plain comparison."""
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
        return bool(re.fullmatch(r"not\s*\(.*\)", cell))
    return rc.unary_test(cell, value)


def evaluate(table: ET.Element, inputs: dict) -> object:
    columns = rc.input_columns(table)
    out = rc.output_names(table).index(OUTPUT)
    hits = []
    for rule in table.findall("dmn:rule", rc.NS):
        cells = [e.findtext("dmn:text", default="", namespaces=rc.NS) or "" for e in rule.findall("dmn:inputEntry", rc.NS)]
        if len(cells) != len(columns):
            fail(f"a rule has {len(cells)} input entries for {len(columns)} input columns")
        if all(cell_matches(cell, inputs[column]) for cell, column in zip(cells, columns)):
            values = [e.findtext("dmn:text", default="", namespaces=rc.NS) or "" for e in rule.findall("dmn:outputEntry", rc.NS)]
            hits.append(rc.literal(values[out]))
    policy = table.get("hitPolicy", "UNIQUE")
    if policy not in ("FIRST", "UNIQUE", "ANY"):
        fail(f"hit policy {policy} is outside the single-result policies this check evaluates")
    if policy == "UNIQUE" and len(hits) > 1:
        fail(f"{inputs} matches {len(hits)} rows of a UNIQUE table")
    return hits[0] if hits else None


# ---- modes -----------------------------------------------------------------------------------------------------

def grade_profile() -> None:
    project, dmn_file, root = load()
    rc.check_input_data(root, INPUTS)
    outputs = rc.output_names(rc.table_of(root))
    if outputs != [OUTPUT]:
        fail(f"output columns are {outputs}, expected {[OUTPUT]}")
    rc.check_contract(project, dmn_file, root, INPUTS, {OUTPUT: "string"})
    bare = [e.get("name") for e in root.findall("dmn:inputData", rc.NS)
            if not (e.findtext("dmn:description", default="", namespaces=rc.NS) or "").strip()]
    if bare:
        fail(f"inputData without a <description> of what the caller supplies: {bare}")
    text = dmn_file.read_text(encoding="utf-8").lower()
    if any(word in text for word in ("receiptformat", "receipttype", "receiptpdf", "receipt_format")):
        fail("built an input from the permissive 'may submit receipts as a PDF or photo' sentence")
    print("OK: inputs, output, contract and input descriptions hold")


def grade_outcomes() -> None:
    _, _, root = load()
    table = rc.table_of(root)
    unknown = [c for c in rc.input_columns(table) if c not in INPUTS]
    if unknown:
        fail(f"input columns {unknown} are not among the inputs the prompt named")
    wrong = []
    for label, values, expected in SCENARIOS:
        actual = evaluate(table, dict(zip(INPUTS, values)))
        if actual != expected:
            wrong.append(f"{label}: returned {actual!r}, expected {expected!r}")
    if wrong:
        fail(f"{len(wrong)} of {len(SCENARIOS)} scenarios wrong:\n  " + "\n  ".join(wrong))
    print(f"OK: all {len(SCENARIOS)} scenarios match")


def load_tests() -> tuple[dict, list[dict]]:
    path = find_one("tests.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{path} is not JSON: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("base"), dict) or not isinstance(data.get("cases"), list):
        fail(f'{path} is not {{ "base": {{...}}, "cases": [...] }}')
    return data["base"], data["cases"]


def case_inputs(base: dict, case: dict) -> dict:
    inputs = {**base, **(case.get("inputs") or {})}
    for name in case.get("omit") or []:
        inputs.pop(name, None)
    return inputs


def grade_tests() -> None:
    _, _, root = load()
    base, cases = load_tests()
    if set(base) != set(INPUTS):
        fail(f"tests.json base names {sorted(base)}, expected every input {sorted(INPUTS)}")
    row_ids = {r.get("id") for r in rc.table_of(root).findall("dmn:rule", rc.NS)}
    problems = []
    for i, case in enumerate(cases):
        missing = [k for k in ("name", "rule", "page", "checks", "expected") if k not in case]
        if missing:
            problems.append(f"case {i} ({case.get('name')}) lacks {missing}")
        elif case["rule"] not in row_ids:
            problems.append(f"case {case['name']} names row {case['rule']!r}, which the table does not have")
    if problems:
        fail(f"{len(problems)} tests.json problems:\n  " + "\n  ".join(problems[:8]))
    covered = {c.get("expected") for c in cases}
    if not set(OUTCOMES) <= covered:
        fail(f"tests.json has no case for {sorted(set(OUTCOMES) - covered)}")
    if not any(c.get("omit") for c in cases):
        fail("tests.json has no missing-input case (a case with `omit`)")
    print(f"OK: tests.json has {len(cases)} cases covering every outcome and a missing input")


def grade_norefs() -> None:
    _, _, root = load()
    refs = uipdm(root, "sourceRefs")
    if refs:
        fail(f"{len(refs)} uipdm:sourceRefs written although no digitizer output (dom.json) was supplied")
    print("OK: no citations without the digitizer's output")


def sourcerefs(root: ET.Element) -> dict[str, list[tuple[str, str]]]:
    out = {}
    for rule in rc.table_of(root).findall("dmn:rule", rc.NS):
        out[rule.get("id")] = sorted((r.get("page"), r.get("box")) for r in rule.iter(f"{{{UIPDM}}}sourceRef"))
    return out


def grade_refs() -> None:
    _, dmn_file, root = load()
    cites = find_one("cites.json")
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / dmn_file.name
        shutil.copy(dmn_file, copy)
        done = subprocess.run(["node", str(skill_script("cite.mjs")), "--dmn", str(copy), "--cites", str(cites),
                               "--dom", str(DOM), "--write"], capture_output=True, text=True, timeout=60)
        if done.returncode != 0:
            fail(f"cite.mjs on the agent's cites.json exits {done.returncode}: {done.stdout[-1500:]}")
        rewritten = ET.parse(copy).getroot()
    if sourcerefs(rewritten) != sourcerefs(root):
        fail("the .dmn's sourceRefs differ from what cite.mjs writes from cites.json (boxes edited or written by hand, "
             "or cite.mjs not re-run after the last edit)")
    rows = sourcerefs(root)
    if sum(1 for refs in rows.values() if refs) < 4:
        fail(f"only {sum(1 for refs in rows.values() if refs)} rows carry sourceRefs; the policy states at least 6 rules")
    if any(w.get("conditionId") for w in uipdm(root, "qualityWarning")):
        fail("a uipdm:qualityWarning carries conditionId; the guide names the row in the text")
    check = subprocess.run(["node", str(skill_script("check-uipdm.mjs")), str(dmn_file)], capture_output=True, text=True, timeout=60)
    if check.returncode != 0:
        fail(f"check-uipdm.mjs: {(check.stdout or check.stderr)[-800:]}")
    print(f"OK: citations resolve and match cite.mjs on {len([r for r in rows.values() if r])} rows; uipdm elements valid")


def engine_outcome(project: Path, inputs: dict) -> object:
    done = subprocess.run(["uip", "rules", "debug", str(project), "--inputs", json.dumps(inputs), "--output", "json"],
                          capture_output=True, text=True, timeout=180)
    if done.returncode != 0:
        fail(f"rules debug exited {done.returncode} for {inputs}: {(done.stdout or done.stderr)[-800:]}")
    data = json.loads(done.stdout).get("Data") or {}
    for result in [data["result"]] if "result" in data else data.get("results") or []:
        for decision in result.get("decisions") or []:
            outputs = decision.get("outputs")
            if isinstance(outputs, dict) and OUTPUT in outputs:
                return outputs[OUTPUT]
    fail(f"rules debug returned no {OUTPUT} for {inputs}: {done.stdout[-800:]}")
    raise AssertionError


def grade_engine() -> None:
    project, _, _ = load()
    wrong = []
    for label, values, expected in SCENARIOS:
        inputs = {k: v for k, v in zip(INPUTS, values) if v is not None}
        if "serviceDays" not in inputs or "requestAmount" not in inputs:
            continue  # the missing-fact scenarios are graded offline by `outcomes`; one upload per case is enough here
        actual = engine_outcome(project, inputs)
        if actual != expected:
            wrong.append(f"{label}: engine returned {actual!r}, expected {expected!r}")
    if wrong:
        fail(f"{len(wrong)} scenarios wrong on the engine:\n  " + "\n  ".join(wrong))
    _, cases = load_tests()
    results_path = find_one("test-results.json")
    results = json.loads(results_path.read_text(encoding="utf-8"))
    if not isinstance(results, list):
        fail(f"{results_path} is not a list")
    by_name = {r.get("name"): r for r in results if isinstance(r, dict)}
    unrun = [c.get("name") for c in cases if c.get("name") not in by_name or "actual" not in by_name[c.get("name")]]
    if unrun:
        fail(f"{len(unrun)} tests.json cases have no recorded run in test-results.json: {unrun[:6]}")
    failing = [n for n, r in by_name.items() if r.get("pass") is not True or r.get("actual") != r.get("expected")]
    if failing:
        fail(f"test-results.json still has failing cases: {failing[:6]}")
    print(f"OK: the engine returns the policy's outcome, and all {len(cases)} tests.json cases ran and pass")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "outcomes"
    if mode == "validate":
        rc.run_validate(rc.find_project(PROJECT_NAME))
        print("OK: uip rules validate passes")
    elif mode in ("profile", "outcomes", "tests", "norefs", "refs", "engine"):
        {"profile": grade_profile, "outcomes": grade_outcomes, "tests": grade_tests, "norefs": grade_norefs,
         "refs": grade_refs, "engine": grade_engine}[mode]()
    else:
        fail(f"unknown mode {mode!r}")
