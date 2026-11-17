#!/usr/bin/env python3
"""Grading for the one-shot rules-extraction task.

The agent picks the one-shot level and the pipeline returns a DMN that one-shot.mjs
writes into the BusinessRules project named ReimbursementRules. The pipeline's DMN is a graph of
decisions, not one table, so the outcome check in policy_check.py does not apply; these modes
check what the one-shot path must leave behind:

  pipeline  the project's one .dmn is the pipeline's (exporter attribute), not hand-built.
  declared  the pipeline declared at least one input, and policy_decision's allowedAnswers
            are exactly the outcomes the prompt named.
  refs      the DMN carries uipdm:sourceRef elements with a page and a box and no quote
            (the pipeline cites boxes; resolve-refs.mjs is not part of this path).

Stdlib ElementTree only; the DMN comes from the pipeline under test.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_check as rc  # noqa: E402

PROJECT_NAME = "ReimbursementRules"
OUTCOMES = {"Approve", "Deny", "Refer"}
EXPORTER = "uipath-idp-rules-extraction"
DMN = "{https://www.omg.org/spec/DMN/20230324/MODEL/}"
UIPDM = "{http://uipath.com/schema/1.0/dmn-ext/decision-model}"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def load_root(project: Path) -> ET.Element:
    dmn_files = list(project.glob("*.dmn"))
    if len(dmn_files) != 1:
        fail(f"expected exactly one .dmn in {project}/, found {len(dmn_files)}")
    text = dmn_files[0].read_text(encoding="utf-8")
    if "<!--" in text:
        fail(f"{dmn_files[0]} carries an XML comment")
    return ET.fromstring(text)


def top_decision(root: ET.Element) -> ET.Element:
    for decision in root.findall(f"{DMN}decision"):
        if decision.get("name") == "policy_decision":
            return decision
    fail("no top-level policy_decision in the project's .dmn")
    raise AssertionError


def grade_pipeline(root: ET.Element) -> None:
    if root.get("exporter") != EXPORTER:
        fail(f"the .dmn is not the pipeline's output (exporter={root.get('exporter')!r})")
    top_decision(root)
    print("OK: the .dmn is the pipeline's and has a top-level policy_decision")


def grade_declared(root: ET.Element) -> None:
    inputs = [e.get("name") for e in root.findall(f"{DMN}inputData")]
    if not inputs:
        fail("the pipeline declared no inputData")
    allowed = top_decision(root).find(f"{DMN}allowedAnswers")
    answers = set(re.findall(r'"([^"]*)"', (allowed.text or "") if allowed is not None else ""))
    if answers != OUTCOMES:
        fail(f"policy_decision allowedAnswers are {sorted(answers)}, expected {sorted(OUTCOMES)}")
    print(f"OK: {len(inputs)} inputs declared and the outcomes are exactly {sorted(OUTCOMES)}")


def grade_refs(root: ET.Element) -> None:
    refs = list(root.iter(f"{UIPDM}sourceRef"))
    if not refs:
        fail("no uipdm:sourceRef in the .dmn")
    for ref in refs:
        if not ref.get("page") or not ref.get("box"):
            fail(f"a sourceRef lacks a page or a box: {ref.attrib}")
        if ref.get("quote"):
            fail("a sourceRef carries a quote; the pipeline cites boxes only")
    print(f"OK: {len(refs)} sourceRef elements with a page and a box, no quote")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pipeline"
    modes = {"pipeline": grade_pipeline, "declared": grade_declared, "refs": grade_refs}
    if mode not in modes:
        fail(f"unknown mode {mode!r}")
    modes[mode](load_root(rc.find_project(PROJECT_NAME)))
