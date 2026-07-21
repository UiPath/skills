#!/usr/bin/env python3
"""Verify the BPMN skill's SDD routing and handoff contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "skills/uipath-maestro-bpmn/SKILL.md"
TEMPLATE = ROOT / "skills/uipath-maestro-bpmn/assets/templates/sdd-template.md"
RULES = ROOT / "skills/uipath-maestro-bpmn/references/sdd-generation-rules.md"
INTERVIEW = ROOT / "skills/uipath-maestro-bpmn/references/phase-0-interview.md"
INTAKE = ROOT / "skills/uipath-maestro-bpmn/references/sdd-input.md"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_required(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required skill-owned file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require_text(label: str, text: str, *phrases: str) -> None:
    normalized_text = " ".join(text.lower().split())
    missing = [
        phrase
        for phrase in phrases
        if " ".join(phrase.lower().split()) not in normalized_text
    ]
    if missing:
        fail(f"{label} is missing required contract text: {', '.join(missing)}")


def require_order(label: str, text: str, *phrases: str) -> None:
    cursor = 0
    for phrase in phrases:
        found = text.lower().find(phrase.lower(), cursor)
        if found < 0:
            fail(f"{label} does not preserve required order: {' -> '.join(phrases)}")
        cursor = found + len(phrase)


def main() -> int:
    skill = read_required(SKILL)
    template = read_required(TEMPLATE)
    rules = read_required(RULES)
    interview = read_required(INTERVIEW)
    intake = read_required(INTAKE)

    require_text(
        "SKILL.md input routing",
        skill,
        "Existing `.bpmn`",
        "surgical edit",
        "Supplied `sdd.md`",
        "skip Phase 0",
        "No `sdd.md`",
        "Phase 0",
        "explicit direct-authoring",
        "direct prose-to-BPMN",
    )
    require_order(
        "SKILL.md input routing",
        skill,
        "Existing `.bpmn`",
        "Supplied `sdd.md`",
        "Prose with an explicit direct-authoring request",
        "No `sdd.md`",
    )
    require_text(
        "SKILL.md frontmatter activation",
        skill.split("---", 2)[1],
        "SDD",
        "Phase 0",
    )
    require_text(
        "SKILL.md supplied-SDD connection refresh",
        skill,
        "supplied-SDD",
        "uip is connections list --all-folders",
        "exactly once",
        "Discovery does not authorize usage",
    )
    require_text(
        "SKILL.md unresolved-resource policy",
        skill,
        "required unresolved resource",
        "blocks executable BPMN",
        "does not block SDD review",
    )
    require_text(
        "SKILL.md supplied-SDD package contract",
        skill,
        "project.uiproj",
        "bindings_v2.json",
        "entry-points.json",
        "operate.json",
        "package-descriptor.json",
        "references/shared/project-layout.md",
    )
    require_text(
        "SKILL.md reference navigation",
        skill,
        "assets/templates/sdd-template.md",
        "references/sdd-generation-rules.md",
        "references/phase-0-interview.md",
        "references/sdd-input.md",
    )

    require_text(
        "Phase 0 interview",
        interview,
        "sdd.draft.md",
        "explicit approval",
        "AskUserQuestion",
        "sdd.md",
        "before registry",
    )
    require_order(
        "Phase 0 interview",
        interview,
        "Listen",
        "Sketch",
        "Ask",
        "Resolve",
        "Approve",
    )

    require_text(
        "SDD semantic intake",
        intake,
        "skip Phase 0",
        "process identity",
        "nodes",
        "flows",
        "conditions",
        "variables",
        "events",
        "subprocess",
        "loop",
        "resource intent",
        "graph completeness",
        "before registry",
        "registry",
        "Inventory membership is not permission",
        "BPMNDI",
        "validator",
        "project.uiproj",
        "bindings_v2.json",
        "entry-points.json",
        "operate.json",
        "package-descriptor.json",
        "uip is connections list --all-folders",
        "exactly once",
    )
    require_text(
        "SDD generation rules",
        rules,
        "stable logical IDs",
        "graph integrity",
        "data lineage",
        "default flow is unconditional",
        "flow ID is the consumer",
        "unresolved",
        "does not include registry XML",
        "does not include BPMNDI",
    )

    for forbidden in ("uipath:", "<bpmn:", "bpmndi"):
        if forbidden in template.lower():
            fail(f"SDD template must not contain {forbidden!r}")

    print("OK: BPMN SDD routing, Phase 0, intake, and handoff contract is present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
