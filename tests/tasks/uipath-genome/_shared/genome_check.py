#!/usr/bin/env python3
"""Structural checks for genome files produced by the uipath-genome skill.

Usage:
  genome_check.py component <genome.md> [--expect TOKEN ...] [--source-map TOKEN ...] [--part-of]
  genome_check.py process   <genome.md> --components <dir> --skills SKILL ... [--expect TOKEN ...]
  … [--shape transactional|stub [--flows N] [--unit TOKEN ...]]   asserts what the Transactional Shape describes

Exit 0 when every check passes; exit 1 with one diagnostic line per failure.
"""

import argparse
import re
import sys
from pathlib import Path

VALID_SKILLS = {
    "uipath-rpa", "uipath-maestro-flow", "uipath-maestro-bpmn", "uipath-maestro-case",
    "uipath-agents", "uipath-functions", "uipath-api-workflow", "uipath-coded-apps",
    "uipath-connector-builder", "uipath-ixp", "uipath-process-mining", "uipath-mcp-servers",
    "uipath-solution", "uipath-human-in-the-loop",
}
OPERATE_SKILLS = {  # allowed in Platform Dependencies / Deployment, never in Build With or Components
    "uipath-platform", "uipath-tasks", "uipath-test", "uipath-admin", "uipath-insights",
    "uipath-troubleshoot", "uipath-governance", "uipath-review", "uipath-planner", "uipath-aops",
    "uipath-automationhub", "uipath-automation-discovery", "uipath-feedback",
}
RETIRED_SKILLS = {"uipath-rpa-workflows", "uipath-coded-workflows", "uipath-coded-agents"}

COMPONENT_SECTIONS = [
    "Overview", "Target Applications", "Build With", "Platform Dependencies", "Interface",
    "Configuration Questions", "Workflow", "Business Rules", "Error Handling",
    "Transactional Shape", "Acceptance Criteria", "Complexity", "Tags",
]
PROCESS_SECTIONS = [
    "Overview", "Actors and Systems", "Components", "Process Map", "Handoffs",
    "Platform Dependencies", "Configuration Questions", "Business Rules",
    "Error Handling and Recovery", "Transactional Shape", "Acceptance Criteria", "Deployment",
    "Complexity", "Tags",
]

# Code-level tokens that must not appear in the genome body (Source Map excluded).
BANNED_BODY_TOKENS = [
    "InvokeWorkflowFile", "RetryScope", "TryCatch", "ReadRange", "AppendRange", "WriteRange",
    "GetIMAPMailMessages", "SaveAttachments", "AddQueueItem", "ReadPDFText", "LogMessage",
    "AndAlso", "OrElse", "dt_", "in_", "out_", ".xaml", "core.action", "core.logic",
    "uipath.core.", "activityType", "JsInvoke",
]


def h2_positions(text: str) -> dict[str, int]:
    return {m.group(1).strip(): m.start() for m in re.finditer(r"^## (.+)$", text, re.M)}


def section_body(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def body_without_source_map(text: str) -> str:
    return re.split(r"^## Source Map\s*$", text, maxsplit=1, flags=re.M)[0]


SPLIT_OPTIONS = {"A", "B", "C"}  # A one process, no queue; B producer and consumer processes; C one process with a queue
MIN_STEPS = 5
MIN_CRITERIA = 5
MIN_QUESTIONS = 3
SHAPE: str | None = None        # --shape: transactional | stub, for the genome given on the command line
FLOWS: int | None = None        # --flows: with --shape transactional, the number of ### Flow blocks expected
UNITS: list[str] = []           # --unit: tokens each expected in some "**Unit of work:**" line


def common_checks(text: str, level: str, sections: list[str]) -> list[str]:
    errors: list[str] = []
    if f"UIPATH-AUTOMATION-GENOME: {level}" not in text:
        errors.append(f"missing preamble comment 'UIPATH-AUTOMATION-GENOME: {level}'")
    if "This is a UiPath automation blueprint" not in text:
        errors.append("missing blueprint blockquote")
    pos = h2_positions(text)
    for s in sections:
        if s not in pos:
            errors.append(f"missing section '## {s}'")
    body = body_without_source_map(text)
    for tok in BANNED_BODY_TOKENS:
        if tok in body:
            errors.append(f"code-level token '{tok}' in genome body (outside Source Map)")
    for name in RETIRED_SKILLS:
        if name in text:
            errors.append(f"retired skill name '{name}' present")
    for name in set(re.findall(r"`(uipath-[a-z-]+)`", text)):
        if name not in VALID_SKILLS and name not in OPERATE_SKILLS and name != "uipath-genome":
            errors.append(f"unknown skill name '{name}' referenced")
    for heading in ("Build With", "Components"):
        for name in set(re.findall(r"`(uipath-[a-z-]+)`", section_body(text, heading))):
            if name in OPERATE_SKILLS:
                errors.append(f"operate-only skill '{name}' used in {heading}; it belongs under Platform Dependencies")
    errors.extend(shape_structure(text, level))
    criteria = re.findall(r"^- \[[ x]\] ", section_body(text, "Acceptance Criteria"), re.M)
    if len(criteria) < MIN_CRITERIA:
        errors.append(f"acceptance criteria: {len(criteria)} found, expected >= {MIN_CRITERIA}")
    for line in criteria_lines(text):
        low = line.lower()
        if "completes successfully" in low or "handles errors properly" in low:
            errors.append(f"generic acceptance criterion: {line.strip()}")
    return errors


def criteria_lines(text: str) -> list[str]:
    return [l for l in section_body(text, "Acceptance Criteria").splitlines() if l.startswith("- [")]


def table_rows(block: str, header_start: str) -> list[list[str]]:
    """Data rows of the first markdown table in block whose header row starts with header_start."""
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header_start):
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append([c.strip() for c in row.strip().strip("|").split("|")])
            return rows
    return []


def flow_blocks(ts: str) -> list[tuple[str, str]]:
    """(heading, body) per '### Flow N' block of the Transactional Shape."""
    parts = re.split(r"^(### Flow\b.*)$", ts, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def shape_structure(text: str, level: str) -> list[str]:
    """Structure the format guide requires of every Transactional Shape (no verdict; flows; per-unit split options)."""
    errors: list[str] = []
    ts = section_body(text, "Transactional Shape")
    if not ts.strip():
        return errors
    stub = ts.strip().startswith("Not transactional")
    if "**Recommendation:**" in ts or re.search(r"^\|\s*(Producer|Consumer)\s*\|", ts, re.M):
        errors.append("Transactional Shape: carries a verdict (Recommendation line or Producer/Consumer mode tables) — describe, never decide")
    if level == "process":
        for row in table_rows(section_body(text, "Components"), "| #"):
            if len(row) > 2 and re.search(r"\b(dispatcher|performer)\b", row[2], re.I):
                errors.append(f"Components: role word in the Type cell of '{row[1]}' — it reads the component type only")
    if stub:
        return errors
    flows = flow_blocks(ts)
    if not flows:
        errors.append("Transactional Shape: no '### Flow N' block and not the stub")
        return errors
    in_process = level == "component" and "Part of:" in text
    if not in_process and "**Flows:**" not in ts:
        errors.append("Transactional Shape: no 'Flows:' line")
    for heading, body in flows:
        name = heading.lstrip("# ").split(":")[0].strip()
        if in_process:
            if "**Role:**" not in body:
                errors.append(f"Transactional Shape {name}: component inside a process has no 'Role:' line")
            if "per the process genome" not in body:
                errors.append(f"Transactional Shape {name}: component inside a process does not point to the process genome's split options")
            continue
        for token, what in (("**Unit of work:**", "Unit of work line"), ("| Aspect | As-is |", "As-is table"),
                            ("| Success |", "Success outcome"), ("| Business exception |", "Business exception outcome"),
                            ("| System exception |", "System exception outcome")):
            if token not in body:
                errors.append(f"Transactional Shape {name}: missing {what}")
        split = table_rows(body, "| Unit of work | Option |")
        if not split:
            errors.append(f"Transactional Shape {name}: no Split options table keyed by unit of work")
            continue
        units: dict[str, set[str]] = {}
        for row in split:
            if len(row) >= 2:
                m = re.match(r"([ABC])\b", row[1])
                if m:
                    units.setdefault(row[0], set()).add(m.group(1))
        for unit, opts in units.items():
            if opts != SPLIT_OPTIONS:
                errors.append(f"Transactional Shape {name}: unit '{unit}' lacks option(s) {sorted(SPLIT_OPTIONS - opts)}")
        alt = next((l for l in body.splitlines() if l.startswith("**Alternative units of work:**")), "")
        if alt and not re.search(r":\*\*\s*none\b", alt, re.I) and len(units) < 2:
            errors.append(f"Transactional Shape {name}: alternative units of work named but split options cover only one unit")
        header = next((l for l in body.splitlines() if l.strip().startswith("| Unit of work | Option |")), "")
        cols = [c.strip().lower() for c in header.strip().strip("|").split("|")]
        if "requires" not in cols or "changes against as-is" not in cols:
            errors.append(f"Transactional Shape {name}: Split options table has no Requires and Changes against as-is columns")
        elif "pros" in cols or "cons" in cols:
            errors.append(f"Transactional Shape {name}: Split options table carries Pros / Cons columns")
        else:
            ir, ic = cols.index("requires"), cols.index("changes against as-is")
            for row in split:
                if len(row) > max(ir, ic) and row[1][:1] in SPLIT_OPTIONS:
                    if not row[ir] or not row[ic]:
                        errors.append(f"Transactional Shape {name}: option {row[1][:1]} of '{row[0]}' has an empty Requires or Changes cell")
                    if re.search(r"\b(recommended|best option|preferred)\b", row[ir] + " " + row[ic], re.I):
                        errors.append(f"Transactional Shape {name}: option {row[1][:1]} of '{row[0]}' ranks the options")
    return errors


def check_shape(text: str, shape: str, flows: int | None, units: list[str]) -> list[str]:
    """Assert what the Transactional Shape of the genome given on the command line describes (--shape)."""
    errors: list[str] = []
    ts = section_body(text, "Transactional Shape")
    stub = ts.strip().startswith("Not transactional")
    if shape == "stub":
        if not stub:
            errors.append("Transactional Shape: expected the 'Not transactional' stub")
        return errors
    if stub:
        errors.append("Transactional Shape: expected flow blocks, found the stub")
        return errors
    blocks = flow_blocks(ts)
    if flows is not None and len(blocks) != flows:
        errors.append(f"Transactional Shape: {len(blocks)} flow block(s), expected {flows}")
    unit_lines = " ".join(l for l in ts.splitlines() if l.startswith("**Unit of work:**")).lower()
    for tok in units:
        if tok.lower() not in unit_lines:
            errors.append(f"Transactional Shape: no Unit of work line names '{tok}'")
    for heading, body in blocks:  # an RPA consumer owes the per-item retry and the consecutive-failure stop
        if "No RPA consumer" in body:
            continue
        if not re.search(r"retr(y|ie)", body, re.I) or not re.search(r"consecutive", body, re.I):
            errors.append(f"Transactional Shape {heading.lstrip('# ').split(':')[0]}: outcomes do not state the per-item retry and the consecutive-failure stop")
    if re.search(r"\{[a-z][^}]*\}", ts):
        errors.append("Transactional Shape: unfilled template placeholder left in the section")
    return errors


def check_component(path: Path, expect: list[str], source_map: list[str], part_of: bool,
                    shape_check: bool = True) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = common_checks(text, "component", COMPONENT_SECTIONS)
    pos = h2_positions(text)
    if "Build With" in pos and "Workflow" in pos and pos["Build With"] > pos["Workflow"]:
        errors.append("Build With must precede Workflow")
    bw = section_body(text, "Build With")
    if not re.search(r"`uipath-[a-z-]+`", bw):
        errors.append("Build With has no skill reference")
    steps = re.findall(r"^\d+\. \*\*", section_body(text, "Workflow"), re.M)
    if len(steps) < MIN_STEPS:
        errors.append(f"workflow: {len(steps)} numbered bold steps, expected >= {MIN_STEPS}")
    cq = section_body(text, "Configuration Questions")
    questions = re.findall(r"^\d+\. ", cq, re.M)
    if len(questions) < MIN_QUESTIONS:
        errors.append(f"configuration questions: {len(questions)} found, expected >= {MIN_QUESTIONS}")
    if questions and "(default:" not in cq:
        errors.append("configuration questions carry no '(default: …)' values")
    if source_map:
        sm = section_body(text, "Source Map")
        if not sm.strip():
            errors.append("missing or empty '## Source Map' section")
        for tok in source_map:
            if tok not in sm:
                errors.append(f"Source Map does not mention '{tok}'")
    if part_of and "Part of:" not in text:
        errors.append("component inside a process genome lacks the 'Part of:' line")
    if SHAPE and shape_check:
        errors.extend(check_shape(text, SHAPE, FLOWS, UNITS))
    for tok in expect:
        if tok.lower() not in text.lower():
            errors.append(f"expected token '{tok}' not found")
    return [f"{path.name}: {e}" for e in errors]


def check_process(path: Path, components_dir: Path, skills: list[str], expect: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = common_checks(text, "process", PROCESS_SECTIONS)
    pos = h2_positions(text)
    if "Components" in pos and "Process Map" in pos and pos["Components"] > pos["Process Map"]:
        errors.append("Components must precede Process Map")
    comp = section_body(text, "Components")
    rows = [l for l in comp.splitlines() if l.startswith("|") and "`uipath-" in l]
    if len(rows) < 2:
        errors.append(f"components table: {len(rows)} skill rows, expected >= 2")
    for s in skills:
        if f"`{s}`" not in comp:
            errors.append(f"components table lacks skill '{s}'")
    links = re.findall(r"\]\(([^)]+-genome\.md)\)", comp)
    if not links:
        errors.append("components table has no links to component genome files")
    component_errors: list[str] = []
    for link in links:
        target = (path.parent / link).resolve()
        if not target.exists():
            errors.append(f"linked component genome missing on disk: {link}")
        else:
            component_errors.extend(check_component(target, [], [], part_of=True, shape_check=False))
    if SHAPE:
        errors.extend(check_shape(text, SHAPE, FLOWS, UNITS))
    handoffs = [l for l in section_body(text, "Handoffs").splitlines() if l.startswith("|")]
    if len(handoffs) < 4:  # header + separator + >= 2 rows
        errors.append(f"handoffs table: {max(0, len(handoffs) - 2)} rows, expected >= 2")
    if not components_dir.exists():
        errors.append(f"components directory missing: {components_dir}")
    for tok in expect:
        if tok.lower() not in text.lower():
            errors.append(f"expected token '{tok}' not found")
    return [f"{path.name}: {e}" for e in errors] + component_errors


def main() -> int:
    global MIN_STEPS, MIN_CRITERIA, MIN_QUESTIONS, SHAPE, FLOWS, UNITS
    ap = argparse.ArgumentParser()
    ap.add_argument("level", choices=["component", "process"])
    ap.add_argument("genome")
    ap.add_argument("--expect", nargs="*", default=[])
    ap.add_argument("--source-map", nargs="*", default=[])
    ap.add_argument("--part-of", action="store_true")
    ap.add_argument("--components", default=None)
    ap.add_argument("--skills", nargs="*", default=[])
    ap.add_argument("--min-steps", type=int, default=MIN_STEPS,
                    help="minimum numbered Workflow steps per component (format guide: 3 simple, 5 medium, 8 complex)")
    ap.add_argument("--min-criteria", type=int, default=MIN_CRITERIA,
                    help="minimum acceptance criteria (format guide: 3 simple, 5 medium, 7 complex)")
    ap.add_argument("--min-questions", type=int, default=MIN_QUESTIONS,
                    help="minimum configuration questions (format guide: stub allowed for simple, 3 medium, 5 complex)")
    ap.add_argument("--shape", choices=["transactional", "stub"], default=None,
                    help="assert the Transactional Shape of the given genome: flow blocks, or the stub (components linked from a process are checked for structure only)")
    ap.add_argument("--flows", type=int, default=None,
                    help="with --shape transactional: the number of '### Flow N' blocks expected")
    ap.add_argument("--unit", nargs="*", default=[],
                    help="with --shape transactional: tokens each expected in some 'Unit of work' line")
    args = ap.parse_args()
    MIN_STEPS, MIN_CRITERIA, MIN_QUESTIONS = args.min_steps, args.min_criteria, args.min_questions
    SHAPE, FLOWS, UNITS = args.shape, args.flows, args.unit

    path = Path(args.genome)
    if not path.exists():
        print(f"FAIL: {path} does not exist")
        return 1
    if args.level == "component":
        errors = check_component(path, args.expect, args.source_map, args.part_of)
    else:
        comp_dir = Path(args.components) if args.components else path.with_suffix("")
        errors = check_process(path, comp_dir, args.skills, args.expect)
    for e in errors:
        print(f"FAIL: {e}")
    if not errors:
        print(f"OK: {path}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
