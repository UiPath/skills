#!/usr/bin/env python3
"""Structural checks for genome files produced by the uipath-genome skill.

Usage:
  genome_check.py component <genome.md> [--expect TOKEN ...] [--source-map TOKEN ...] [--part-of]
  genome_check.py process   <genome.md> --components <dir> --skills SKILL ... [--expect TOKEN ...]
  … [--shape applied|declined|stub [--mode queue|direct]]   asserts the Transactional Shape verdict

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


MIN_STEPS = 5
MIN_CRITERIA = 5
MIN_QUESTIONS = 3
SHAPE: str | None = None   # --shape: assert the Transactional Shape verdict of the genome given on the command line
MODE: str | None = None    # --mode: with --shape applied, the mode the Consumer row must name


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
    ts = section_body(text, "Transactional Shape")
    ts_stub = ts.strip().startswith("Not transactional")
    if ts_stub and "**Recommendation:**" in ts:
        errors.append("Transactional Shape: the stub carries a Recommendation line")
    if ts and not ts_stub:
        if "**Recommendation:**" not in ts:
            errors.append("Transactional Shape: no Recommendation line and not the stub")
        if "| Producer |" not in ts and "| Consumer |" not in ts:
            errors.append("Transactional Shape: neither a Producer nor a Consumer table")
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


def check_shape(text: str, shape: str, mode: str | None, standalone: bool) -> list[str]:
    """Assert the Transactional Shape's verdict (--shape) and, when applied, its mode and seam."""
    errors: list[str] = []
    ts = section_body(text, "Transactional Shape")
    rec = next((l for l in ts.splitlines() if l.startswith("**Recommendation:**")), "")
    if shape == "stub":
        if not ts.strip().startswith("Not transactional"):
            errors.append("Transactional Shape: expected the 'Not transactional' stub")
        return errors
    if shape == "declined":
        if not re.search(r"Not recommended|— not applied", rec):
            errors.append("Transactional Shape: Recommendation is not the 'Not recommended' verdict")
        return errors
    if not re.search(r"\bApply\b|— applied", rec):
        errors.append("Transactional Shape: Recommendation is not the 'Apply' verdict")
    consumer_rows = [l for l in ts.splitlines() if l.startswith("|") and "Consumer" not in l and "---" not in l
                     and re.search(r"\|\s*(queue|direct)\b", l)]
    if not consumer_rows:
        errors.append("Transactional Shape: no Consumer row with a queue/direct Mode cell")
    elif mode and not any(re.search(rf"\|\s*{mode}\b[^|]*(—|-)[^|]*\|", l) for l in consumer_rows):
        errors.append(f"Transactional Shape: no Consumer row whose Mode cell reads '{mode} — <reason>'")
    if not re.search(r"retr(y|ie)", ts, re.I) or not re.search(r"consecutive", ts, re.I):
        errors.append("Transactional Shape: outcomes do not state the per-item retry and the consecutive-failure stop")
    if re.search(r"\{[a-z][^}]*\}", ts):
        errors.append("Transactional Shape: unfilled template placeholder left in the section")
    if standalone and not re.search(r"\bperformer\b", section_body(text, "Overview"), re.I):
        errors.append("Transactional Shape applied on a standalone component, but the Overview names no 'performer'")
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
        errors.extend(check_shape(text, SHAPE, MODE, standalone="Part of:" not in text))
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
        errors.extend(check_shape(text, SHAPE, MODE, standalone=False))
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
    global MIN_STEPS, MIN_CRITERIA, MIN_QUESTIONS, SHAPE, MODE
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
    ap.add_argument("--shape", choices=["applied", "declined", "stub"], default=None,
                    help="assert the Transactional Shape verdict of the given genome (components linked from a process are not checked)")
    ap.add_argument("--mode", choices=["queue", "direct"], default=None,
                    help="with --shape applied: the mode the Consumer row's Mode cell must name, with its reason")
    args = ap.parse_args()
    MIN_STEPS, MIN_CRITERIA, MIN_QUESTIONS = args.min_steps, args.min_criteria, args.min_questions
    SHAPE, MODE = args.shape, args.mode

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
