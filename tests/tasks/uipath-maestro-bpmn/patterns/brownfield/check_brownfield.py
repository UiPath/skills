#!/usr/bin/env python3
"""Assert a pattern was inserted into a running process, not bolted alongside it.

Three things the composing guide promises, in order of how easy they are to get
wrong: reuse the variable the process already holds rather than declaring a
duplicate; add only the part that is missing rather than a second scoring step;
leave everything untouched that the edit did not target.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    elements,
    fail,
    load_bpmn,
)

BPMN = "ClaimsIntake.bpmn"
PRESERVED_IDS = {
    "Start_1",
    "Task_Score",
    "Task_Settle",
    "End_1",
    "Var_ClaimId",
    "Var_ConfidenceScore",
    "Var_SettlementResult",
}
SCORE_WORDS = re.compile(r"\b(score|scoring|confidence|classif)", re.I)


def main() -> None:
    root = load_bpmn(BPMN)
    raw = Path(BPMN).read_text(encoding="utf-8")

    # 1. Nothing the edit did not target was disturbed.
    for ident in sorted(PRESERVED_IDS):
        if f'"{ident}"' not in raw:
            fail(f"pre-existing id {ident} is gone — the file was regenerated, not edited")
    if "preserve-only-do-not-touch" not in raw:
        fail("preserve-only caseManagement payload was dropped")
    if "migrationVersion" not in raw:
        fail("uipath:migrationVersion was dropped")

    # 2. A gate and a human review step were added.
    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway — nothing routes low-confidence claims away from auto-settle")
    if not elements(root, "userTask"):
        fail("no userTask — there is no human in the loop")

    # 3. The gate reads the score the process already produces, rather than a
    #    duplicate declared alongside it.
    conditions = [
        (c.text or "") for c in root.findall(f".//{{{BPMN_NS}}}conditionExpression")
    ]
    if not conditions:
        fail("no conditionExpression on any gateway")
    if not any("Var_ConfidenceScore" in c for c in conditions):
        fail(
            "no gateway condition reads Var_ConfidenceScore — the existing score "
            f"variable was not reused (conditions seen: {conditions})"
        )

    # 4. No second scoring step. The fixture ships exactly one node whose name
    #    is about scoring; inserting the pattern whole would add another.
    named_scorers = [
        e
        for kind in ("scriptTask", "serviceTask", "businessRuleTask")
        for e in elements(root, kind)
        if SCORE_WORDS.search(e.attrib.get("name", ""))
    ]
    if len(named_scorers) > 1:
        names = [e.attrib.get("name") for e in named_scorers]
        fail(f"more than one scoring step present {names} — existing work was duplicated")

    # 5. Variables were extended, not replaced.
    declared = {
        v.attrib.get("id")
        for tag in ("inputOutput", "input", "output")
        for v in root.findall(f".//{{{UIPATH_NS}}}{tag}")
    }
    for ident in ("Var_ClaimId", "Var_ConfidenceScore", "Var_SettlementResult"):
        if ident not in declared:
            fail(f"variable {ident} no longer declared")

    # 6. Still importable.
    if not root.findall(".//{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the edited file will not import")

    print(
        f"PASS: {len(gateways)} gateway(s) and a review task inserted, "
        f"bound to the existing score variable, {len(PRESERVED_IDS)} pre-existing ids intact"
    )


if __name__ == "__main__":
    main()
