#!/usr/bin/env python3
"""Checks for genome files produced by the uipath-genome skill.

Usage:
  genome_check.py component <genome.md> [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
  genome_check.py process   <genome.md> [--profile core|strict] --skills SKILL ... [--expect TOKEN ...]
  genome_check.py tokens    <pattern>   --expect TOKEN ... [--min FRACTION] [--files N]
  component and process also take: [--shape transactional|stub [--flows N] [--unit TOKEN ...]]
                                   [--shape-checks gate|advisory]  advisory: Transactional Shape findings
                                   are graded by the strict profile only (a task that tests something else)

Profiles:
  core    the genome contract a smoke test gates on: level and preamble, every section, valid
          skill names, steps and criteria present, a Transactional Shape that is the stub or has
          flows with a unit of work and split options, Source Map tokens, expected facts.
  strict  core plus every mechanical format rule of genome-format-guide.md: behavioural wording
          (no code-level tokens), configuration question kind and default, bold step names,
          the As-is table, exactly the outcome rows rule 4 allows, complete split options for
          every unit and alternative unit, retry and consecutive-failure stop.

<genome.md> and <pattern> may be a quoted glob ("*-genome.md"): the file name is the agent's
choice, only the -genome.md suffix is a contract. component and process need exactly one match;
tokens searches every match, case-sensitively, like a file_contains criterion.

Exit 0 when every check passes; exit 1 with one line per failure.
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
    "uipath-activity-migrator", "uipath-knowledge-bundles",
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
OUTCOME_ROWS = {"Success", "Business exception", "System exception", "Postponed"}
SPLIT_OPTIONS = {"A", "B", "C"}
STUB = "Not transactional"
# format guide § Transactional Shape rule 9: a flow with one side outside the genome names it instead of the table
EXTERNAL_SIDE = re.compile(r"Split options:(?:\*\*)? none\s*[—–-]+\s*the (consumer|producer) is outside this genome", re.I)


class Report:
    """Collects findings; a strict finding is dropped under the core profile."""

    def __init__(self, profile: str, shape_gates: bool = True):
        self.profile = profile
        self.shape_gates = shape_gates  # --shape-checks advisory: Transactional Shape findings count as strict
        self.errors: list[str] = []

    def shape(self, message: str) -> None:
        (self.core if self.shape_gates else self.strict)(message)

    def core(self, message: str) -> None:
        self.errors.append(message)

    def strict(self, message: str) -> None:
        if self.profile == "strict":
            self.errors.append(message)


# --- markdown helpers --------------------------------------------------------------------------

def h2_positions(text: str) -> dict[str, int]:
    return {m.group(1).strip(): m.start() for m in re.finditer(r"^## (.+)$", text, re.M)}


def section_body(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def body_without_source_map(text: str) -> str:
    return re.split(r"^## Source Map\s*$", text, maxsplit=1, flags=re.M)[0]


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
    """(name, body) per '### Flow N' block of the Transactional Shape."""
    parts = re.split(r"^(### Flow\b.*)$", ts, flags=re.M)
    return [(parts[i].lstrip("# ").split(":")[0].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


# --- checks shared by both levels ---------------------------------------------------------------

def check_common(text: str, level: str, sections: list[str], r: Report, min_criteria: int) -> None:
    if f"UIPATH-AUTOMATION-GENOME: {level}" not in text:
        r.core(f"missing preamble comment 'UIPATH-AUTOMATION-GENOME: {level}'")
    if "This is a UiPath automation blueprint" not in text:
        r.core("missing blueprint blockquote")
    pos = h2_positions(text)
    for s in sections:
        if s not in pos:
            r.core(f"missing section '## {s}'")
    for name in RETIRED_SKILLS:
        if name in text:
            r.core(f"retired skill name '{name}' present")
    # skill names are read where a genome names skills; elsewhere `uipath-…` is also an Integration
    # Service connector key (`uipath-slack`, `uipath-salesforce-sfdc`), not a skill
    for heading in ("Build With", "Components"):
        for name in sorted(set(re.findall(r"`(uipath-[a-z-]+)`", section_body(text, heading)))):
            if name not in VALID_SKILLS | OPERATE_SKILLS | {"uipath-genome"}:
                r.core(f"unknown skill name '{name}' in {heading}")
    for heading in ("Build With", "Components"):
        for name in sorted(set(re.findall(r"`(uipath-[a-z-]+)`", section_body(text, heading)))):
            if name in OPERATE_SKILLS:
                r.core(f"operate-only skill '{name}' in {heading}; it belongs under Platform Dependencies")
    criteria = [l for l in section_body(text, "Acceptance Criteria").splitlines() if re.match(r"- \[[ x]\] ", l)]
    if len(criteria) < min_criteria:
        r.core(f"acceptance criteria: {len(criteria)} found, expected >= {min_criteria}")
    for line in criteria:
        if re.search(r"completes successfully|handles errors properly", line, re.I):
            r.core(f"generic acceptance criterion: {line.strip()}")

    body = body_without_source_map(text)
    for tok in BANNED_BODY_TOKENS:
        if tok in body:
            r.strict(f"code-level token '{tok}' in the genome body (outside Source Map)")
    for num, question in re.findall(r"^(\d+)\. (.*)$", section_body(text, "Configuration Questions"), re.M):
        if not re.search(r"\((setting|constant); default:", question):
            r.strict(f"configuration question {num} does not name its kind and default as '(setting; default: …)' or '(constant; default: …)'")


def check_transactional(text: str, level: str, r: Report) -> None:
    """Transactional Shape: the stub, or flow blocks the format guide describes."""
    ts = section_body(text, "Transactional Shape")
    if not ts.strip() or ts.strip().startswith(STUB):
        return
    if "**Recommendation:**" in ts or re.search(r"^\|\s*(Producer|Consumer)\s*\|", ts, re.M):
        r.strict("Transactional Shape carries a verdict (Recommendation line or Producer/Consumer mode table)")
    flows = flow_blocks(ts)
    if not flows:
        r.shape("Transactional Shape is neither the stub nor '### Flow N' blocks")
        return
    in_process = level == "component" and "Part of:" in text
    if not in_process and "**Flows:**" not in ts:
        r.strict("Transactional Shape has no 'Flows:' line")
    if re.search(r"\{[a-z][^}]*\}", ts):
        r.strict("Transactional Shape leaves a template placeholder unfilled")
    for name, body in flows:
        if in_process:
            if "**Role:**" not in body:
                r.shape(f"Transactional Shape {name}: a component inside a process has no 'Role:' line")
            if "per the process genome" not in body:
                r.strict(f"Transactional Shape {name}: does not point to the process genome's split options")
            continue
        if "**Unit of work:**" not in body:
            r.shape(f"Transactional Shape {name}: no 'Unit of work' line")
        external = EXTERNAL_SIDE.search(body)
        split = table_rows(body, "| Unit of work | Option |")
        if not external and not split:
            r.shape(f"Transactional Shape {name}: no Split options table and no 'outside this genome' line")
        if "| Aspect | As-is |" not in body:
            r.strict(f"Transactional Shape {name}: no As-is table")
        consumer_outside = bool(external and external.group(1).lower() == "consumer")
        if not consumer_outside:
            rows = [row[0] for row in table_rows(body, "| Outcome |") if row]
            for needed in ("Success", "Business exception", "System exception"):
                if needed not in rows:
                    r.strict(f"Transactional Shape {name}: no '{needed}' outcome row")
            for extra in [x for x in rows if x not in OUTCOME_ROWS]:
                r.strict(f"Transactional Shape {name}: outcome row '{extra}' — a source's own results map to Success or a Business exception")
            # an RPA consumer owes the item retry and the consecutive-failure stop; a flow whose items a
            # coordinator's trigger takes one per instance has no consumer loop (format guide rule 9)
            if "No RPA consumer" not in body and (
                    not re.search(r"retr(y|ie)", body, re.I) or not re.search(r"consecutive|stops? after \d", body, re.I)):
                r.strict(f"Transactional Shape {name}: outcomes do not state the item retry and the consecutive-failure stop")
        if external:
            continue
        units: dict[str, set[str]] = {}
        for row in split:
            m = re.match(r"([ABC])\b", row[1]) if len(row) >= 2 else None
            if m:
                units.setdefault(row[0], set()).add(m.group(1))
        for unit, opts in units.items():
            if opts != SPLIT_OPTIONS:
                r.strict(f"Transactional Shape {name}: unit '{unit}' lacks option(s) {sorted(SPLIT_OPTIONS - opts)}")
        alt = next((l for l in body.splitlines() if l.startswith("**Alternative units of work:**")), "")
        if alt and not re.search(r":\*\*\s*none\b", alt, re.I) and len(units) < 2:
            r.strict(f"Transactional Shape {name}: alternative units of work named but split options cover only one unit")
        header = next((l for l in body.splitlines() if l.strip().startswith("| Unit of work | Option |")), "")
        cols = [c.strip().lower() for c in header.strip().strip("|").split("|")]
        if "requires" not in cols or "changes against as-is" not in cols:
            r.strict(f"Transactional Shape {name}: Split options table has no Requires and Changes against as-is columns")
            continue
        ir, ic = cols.index("requires"), cols.index("changes against as-is")
        for row in split:
            if len(row) > max(ir, ic) and row[1][:1] in SPLIT_OPTIONS:
                if not row[ir] or not row[ic]:
                    r.strict(f"Transactional Shape {name}: option {row[1][:1]} of '{row[0]}' has an empty Requires or Changes cell")
                if re.search(r"\b(recommended|best option|preferred)\b", row[ir] + " " + row[ic], re.I):
                    r.strict(f"Transactional Shape {name}: option {row[1][:1]} of '{row[0]}' ranks the options")


def check_shape_assertion(text: str, shape: str, flows: int | None, units: list[str], r: Report) -> None:
    """--shape: what the Transactional Shape of this genome must describe."""
    ts = section_body(text, "Transactional Shape")
    stub = ts.strip().startswith(STUB)
    if shape == "stub":
        if not stub:
            r.core("Transactional Shape: expected the 'Not transactional' stub")
        return
    if stub:
        r.core("Transactional Shape: expected flow blocks, found the stub")
        return
    blocks = flow_blocks(ts)
    if flows is not None and len(blocks) != flows:
        r.core(f"Transactional Shape: {len(blocks)} flow block(s), expected {flows}")
    unit_lines = " ".join(l for l in ts.splitlines() if l.startswith("**Unit of work:**")).lower()
    for tok in units:
        if tok.lower() not in unit_lines:
            r.core(f"Transactional Shape: no 'Unit of work' line names '{tok}'")


# --- levels -------------------------------------------------------------------------------------

def check_component(path: Path, a: argparse.Namespace, part_of: bool, shape: bool = True) -> list[str]:
    text = path.read_text(encoding="utf-8")
    r = Report(a.profile, a.shape_checks == "gate")
    check_common(text, "component", COMPONENT_SECTIONS, r, a.min_criteria)
    pos = h2_positions(text)
    if "Build With" in pos and "Workflow" in pos and pos["Build With"] > pos["Workflow"]:
        r.core("Build With must precede Workflow")
    if not re.search(r"`uipath-[a-z-]+`", section_body(text, "Build With")):
        r.core("Build With names no skill")
    workflow = section_body(text, "Workflow")
    if len(re.findall(r"^\d+\. ", workflow, re.M)) < a.min_steps:
        r.core(f"workflow: fewer than {a.min_steps} numbered steps")
    elif len(re.findall(r"^\d+\. \*\*", workflow, re.M)) < a.min_steps:
        r.strict(f"workflow: fewer than {a.min_steps} steps in the '1. **Step name**' form the step map keys on")
    cq = section_body(text, "Configuration Questions")
    questions = re.findall(r"^\d+\. ", cq, re.M)
    if not questions and "no additional configuration needed" not in cq:
        r.core("Configuration Questions: neither questions nor the stub line")
    if questions and len(questions) < a.min_questions:
        r.strict(f"configuration questions: {len(questions)} found, expected >= {a.min_questions}")
    if a.source_map:
        sm = section_body(text, "Source Map")
        if not sm.strip():
            r.core("missing or empty '## Source Map' section")
        for tok in a.source_map:
            if tok not in sm:
                r.core(f"Source Map does not mention '{tok}'")
    if part_of and "Part of:" not in text:
        r.core("component inside a process genome lacks the 'Part of:' line")
    check_transactional(text, "component", r)
    if a.shape and shape:
        check_shape_assertion(text, a.shape, a.flows, a.unit, r)
    for tok in a.expect:
        if tok.lower() not in text.lower():
            r.core(f"expected token '{tok}' not found")
    return [f"{path.name}: {e}" for e in r.errors]


def check_process(path: Path, a: argparse.Namespace) -> list[str]:
    text = path.read_text(encoding="utf-8")
    r = Report(a.profile, a.shape_checks == "gate")
    check_common(text, "process", PROCESS_SECTIONS, r, a.min_criteria)
    pos = h2_positions(text)
    if "Components" in pos and "Process Map" in pos and pos["Components"] > pos["Process Map"]:
        r.core("Components must precede Process Map")
    comp = section_body(text, "Components")
    if len([l for l in comp.splitlines() if l.startswith("|") and "`uipath-" in l]) < 2:
        r.core("Components table: fewer than 2 rows naming a skill")
    for s in a.skills:
        if f"`{s}`" not in comp:
            r.core(f"Components table lacks skill '{s}'")
    for row in table_rows(comp, "| #"):
        if len(row) > 2 and re.search(r"\b(dispatcher|performer)\b", row[2], re.I):
            r.strict(f"Components: role word in the Type cell of '{row[1]}' — it reads the component type only")
    links = re.findall(r"\]\(([^)]+-genome\.md)\)", comp)
    if not links:
        r.core("Components table links no component genome")
    component_errors: list[str] = []
    for link in links:
        target = (path.parent / link).resolve()
        if not target.exists():
            r.core(f"linked component genome missing on disk: {link}")
        else:
            component_errors.extend(check_component(target, argparse.Namespace(**{**vars(a), "expect": [], "source_map": []}), part_of=True, shape=False))
    handoffs = [l for l in section_body(text, "Handoffs").splitlines() if l.startswith("|")]
    if len(handoffs) < 4:  # header + separator + >= 2 rows
        r.core(f"Handoffs table: {max(0, len(handoffs) - 2)} rows, expected >= 2")
    check_transactional(text, "process", r)
    if a.shape:
        check_shape_assertion(text, a.shape, a.flows, a.unit, r)
    for tok in a.expect:
        if tok.lower() not in text.lower():
            r.core(f"expected token '{tok}' not found")
    return [f"{path.name}: {e}" for e in r.errors] + component_errors


def check_tokens(paths: list[Path], tokens: list[str], minimum: float, files: int | None) -> list[str]:
    errors: list[str] = []
    if files is not None and len(paths) != files:
        errors.append(f"{len(paths)} file(s) match, expected {files}: {', '.join(p.as_posix() for p in paths) or 'none'}")
    text = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    missing = [t for t in tokens if t not in text]
    if tokens and (len(tokens) - len(missing)) / len(tokens) < minimum:
        errors.append(f"{len(tokens) - len(missing)}/{len(tokens)} tokens found, expected >= {minimum:.0%}; missing: {', '.join(missing)}")
    return errors


def resolve(pattern: str) -> list[Path]:
    path = Path(pattern)
    if path.exists() or not any(c in pattern for c in "*?["):
        return [path] if path.exists() else []
    return sorted(Path(".").glob(pattern))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("level", choices=["component", "process", "tokens"])
    ap.add_argument("genome")
    ap.add_argument("--profile", choices=["core", "strict"], default="core")
    ap.add_argument("--expect", nargs="*", default=[])
    ap.add_argument("--source-map", nargs="*", default=[])
    ap.add_argument("--skills", nargs="*", default=[])
    ap.add_argument("--shape", choices=["transactional", "stub"], default=None)
    ap.add_argument("--shape-checks", choices=["gate", "advisory"], default="gate")
    ap.add_argument("--flows", type=int, default=None)
    ap.add_argument("--unit", nargs="*", default=[])
    ap.add_argument("--min-steps", type=int, default=5, help="format guide: 3 simple, 5 medium, 8 complex")
    ap.add_argument("--min-criteria", type=int, default=5, help="format guide: 3 simple, 5 medium, 7 complex")
    ap.add_argument("--min-questions", type=int, default=3, help="strict: minimum configuration questions when any are asked")
    ap.add_argument("--min", type=float, default=1.0, help="tokens: fraction of --expect tokens that must be found")
    ap.add_argument("--files", type=int, default=None, help="tokens: exact number of files the pattern must match")
    a = ap.parse_args(argv)

    paths = resolve(a.genome)
    if a.level == "tokens":
        errors = ([f"no file matches {a.genome}"] if not paths else []) + check_tokens(paths, a.expect, a.min, a.files)
    elif len(paths) != 1:
        errors = [f"expected exactly one file matching {a.genome}, found {len(paths)}: {', '.join(p.as_posix() for p in paths) or 'none'}"]
    elif a.level == "component":
        errors = check_component(paths[0], a, part_of=False)
    else:
        errors = check_process(paths[0], a)
    for e in errors:
        print(f"FAIL: {e}")
    if not errors:
        print(f"OK ({a.profile if a.level != 'tokens' else 'tokens'}): {', '.join(p.as_posix() for p in paths)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
