#!/usr/bin/env python3
"""Verify BPMN Phase 0 promotes an approved semantic SDD and stops."""

from __future__ import annotations

import re
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(pattern: str, text: str, label: str) -> None:
    if not re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE):
        fail(f"approved sdd.md is missing {label}")


def main() -> int:
    sdd = Path("sdd.md")
    if not sdd.is_file():
        fail("Phase 0 did not promote the approved draft to sdd.md")
    draft = Path("sdd.draft.md")
    if draft.exists() and draft.read_bytes() != sdd.read_bytes():
        fail("approved sdd.md is not the exact reviewed draft content")
    if list(Path(".").rglob("*.bpmn")):
        fail("Phase 0 ran ahead into BPMN authoring")

    text = sdd.read_text(encoding="utf-8")
    for heading in (
        "Process identity",
        "Participants and triggers",
        "Process graph",
        "Data and variables",
        "Resource intent",
        "Implementation readiness",
    ):
        require(rf"^##\s+\d*\.?\s*{re.escape(heading)}", text, heading)

    for concept in (
        "start event",
        "script task",
        "exclusive gateway",
        "user task",
        "end event",
        "applicationId",
        "requestedAmount",
        "validationStatus",
        "eligibilityDecision",
        "reviewOutcome",
    ):
        require(re.escape(concept), text, concept)

    require(r"valid.*eligible.*underwriter", text, "valid/eligible review route")
    require(r"invalid.*reject|reject.*invalid", text, "invalid rejection route")
    require(r"ineligible.*reject|reject.*ineligible", text, "ineligible rejection route")
    require(r"reviewOutcome.*approv", text, "underwriter approval condition")
    require(r"reviewOutcome.*reject", text, "underwriter rejection condition")
    require(r"UNRESOLVED", text, "unresolved human-task resource intent")
    require(r"Blocked|Reviewable", text, "honest implementation readiness")

    if re.search(r"<uipath:|<bpmn:|bpmndi:", text, flags=re.IGNORECASE):
        fail("semantic SDD contains executable registry XML or BPMNDI")

    print("OK: BPMN Phase 0 promoted an approved semantic SDD and stopped before implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
