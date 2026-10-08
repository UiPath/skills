#!/usr/bin/env python3
"""Checks a genome written by the uipath-genome skill, and its Source Map's step tables against the source export.

Usage:
  check-genome.py component <genome.md> [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
  check-genome.py process   <genome.md> [--profile core|strict] [--skills SKILL ...] [--expect TOKEN ...]
  check-genome.py tokens    <pattern>   --expect TOKEN ... [--min FRACTION] [--files N]
  component and process also take: [--shape transactional|stub [--flows N] [--unit TOKEN ...]]
                                   [--shape-checks gate|advisory]  advisory: Transactional Shape findings
                                   are graded by the strict profile only (a task that tests something else)
                                   [--processes <inventory.json> --recordsets <recordsets.json>]

The skill runs it with --profile strict after writing or editing a genome. For a genome extracted through the
framework migration pack it adds the two files the pack's `data` command writes, and execution runs it so at
migration preflight against the export it resolved. The genome tasks under tests/tasks/uipath-genome/ grade
with this file.

Profiles:
  core    the genome contract a smoke test gates on: level and preamble, every section, valid skill names,
          steps and criteria present, a Transactional Shape that is the stub or has flows that each name their
          unit of work, Source Map tokens, expected facts; in an extracted genome (one with a Source Map), a
          `### Steps` table with exactly one row per Workflow step.
  strict  core plus every mechanical format rule of genome-format-guide.md: behavioural wording (no
          code-level tokens), configuration question kind and default, bold step names, numbered acceptance
          criteria, the As-is table, exactly the outcome rows rule 4 allows, split options named by letter
          with only their Requires and Changes cells, complete for every unit and alternative unit, retry and
          consecutive-failure stop; step table cells holding references only.

Export check (--processes and --recordsets, both required together):
  --processes   a list of {"id", "name", "recordset" (name or null), "calls": [{"calleeId", "recordset"}]}
  --recordsets  a list of {"id", "name"}; an entry with "drives": false is provenance, never a data set
  In every step table: each source object is `Name` (id) with the id a process of that name, each data set
  `Name` (id) with the id a data set of that name, and every row names at least one source object. A library
  step's process that no built root reaches while a same-named copy is reachable is the wrong copy; a library
  workflow nothing in the genome calls is a NOTE. The check reads no prose and derives nothing.

<genome.md> and <pattern> may be a quoted glob ("*-genome.md"): the file name is the agent's choice, only the
-genome.md suffix is a contract. component and process need exactly one match; tokens searches every match,
case-sensitively, like a file_contains criterion.

Exit 0 when every check passes; exit 1 with one line per failure.
"""

import argparse
import json
import re
import sys
from pathlib import Path

VALID_SKILLS = {
    "uipath-rpa", "uipath-maestro-flow", "uipath-maestro-bpmn", "uipath-maestro-case",
    "uipath-agents", "uipath-functions", "uipath-api-workflow", "uipath-coded-apps",
    "uipath-connector-builder", "uipath-ixp", "uipath-process-mining", "uipath-mcp-servers",
    "uipath-solution", "uipath-human-in-the-loop", "uipath-rules",
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
# format guide § Population Matrix: minimum Workflow steps and Acceptance Criteria per complexity.
# core gates only on the floor every genome meets (the simple minimum); the per-complexity minimum is strict.
CORE_FLOOR = 3
MIN_STEPS_BY_COMPLEXITY = {"simple": 3, "medium": 5, "complex": 8}
MIN_CRITERIA_BY_COMPLEXITY = {"simple": 3, "medium": 5, "complex": 7}
SPLIT_OPTIONS = {"A", "B", "C"}
SPLIT_COLUMNS = ["unit of work", "option", "requires", "changes against as-is"]
STUB = "Not transactional"
# format guide § Transactional Shape rule 9: a flow with one side outside the genome names it instead of the table
EXTERNAL_SIDE = re.compile(r"Split options:(?:\*\*)? none\s*[—–-]+\s*the (consumer|producer) is outside this genome", re.I)
# format guide § Source Map: the step table
STEPS_COLUMNS = ["step", "source objects", "data sets", "captures", "notes"]
REFERENCE = re.compile(r"`([^`]+)`(?:\s*\(((?:[^()`]|`[^`]*`)*)\))?")  # `Name`, `Name` (id), `Name` (id, locator)


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


def section_pos(pos: dict[str, int], name: str) -> int | None:
    """Position of the first heading that starts with name, any case ('Error Handling and Recovery'
    counts as 'Error Handling'). The exact heading is a format rule, graded by strict."""
    return next((p for h, p in pos.items() if h.lower().startswith(name.lower())), None)


def section_body(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\b[^\n]*$(.*?)(?=^## |\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else ""


def complexity_of(text: str) -> str | None:
    m = re.search(r"\b(simple|medium|complex)\b", section_body(text, "Complexity"), re.I)
    return m.group(1).lower() if m else None


def body_without_source_map(text: str) -> str:
    return re.split(r"^## Source Map\s*$", text, maxsplit=1, flags=re.M)[0]


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def table_rows(block: str, header_start: str) -> list[list[str]]:
    """Data rows of the first markdown table in block whose header row starts with header_start."""
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header_start):
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append(cells(row))
            return rows
    return []


def flow_blocks(ts: str) -> list[tuple[str, str]]:
    """(name, body) per '### Flow N' block of the Transactional Shape."""
    parts = re.split(r"^(### Flow\b.*)$", ts, flags=re.M)
    return [(parts[i].lstrip("# ").split(":")[0].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def workflow_steps(text: str) -> list[str]:
    """The numbers of the Workflow's top-level steps, in order."""
    return re.findall(r"^(\d+)\.\s", section_body(text, "Workflow"), re.M)


def steps_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    """(header cells, rows) of the Source Map's `### Steps` table; None when the Source Map has none."""
    m = re.search(r"^### Steps\s*$(.*?)(?=^#{2,3} |\Z)", section_body(text, "Source Map"), re.M | re.S)
    if not m:
        return None
    header = next((l for l in m.group(1).splitlines() if l.strip().startswith("|")), "")
    return [c.lower() for c in cells(header)], table_rows(m.group(1), header.strip()) if header else []


def split_references(cell: str) -> list[str]:
    """The parts of a step table cell, split on '; ' outside backticks and parentheses."""
    parts, part, tick, depth = [], "", False, 0
    for ch in cell:
        if ch == "`":
            tick = not tick
        elif not tick and ch in "()":
            depth = depth + 1 if ch == "(" else max(0, depth - 1)
        if ch == ";" and not tick and depth == 0:
            parts.append(part)
            part = ""
        else:
            part += ch
    return [p.strip() for p in parts + [part] if p.strip()]


def references(cell: str) -> tuple[list[tuple[str, str | None]], list[str]]:
    """((name, id or None) per reference, the parts that are no reference) of a step table cell; `none` is empty."""
    if cell.strip().lower() == "none":
        return [], []
    refs, prose = [], []
    for part in split_references(cell):
        m = REFERENCE.fullmatch(part)
        if not m:
            prose.append(part)
            continue
        ident = (m.group(2) or "").partition(",")[0].strip()
        refs.append((m.group(1), ident or None))
    return refs, prose


# --- checks shared by both levels ---------------------------------------------------------------

def check_common(text: str, level: str, sections: list[str], r: Report, min_criteria: int) -> None:
    if not re.search(rf"UIPATH-AUTOMATION-GENOME:\s*{level}", text, re.I):
        r.core(f"missing preamble comment 'UIPATH-AUTOMATION-GENOME: {level}'")
    elif f"UIPATH-AUTOMATION-GENOME: {level}" not in text:
        r.strict(f"preamble comment not written exactly 'UIPATH-AUTOMATION-GENOME: {level}'")
    if not re.search(r"UiPath automation blueprint", text, re.I):
        r.core("missing blueprint blockquote")
    elif "This is a UiPath automation blueprint" not in text:
        r.strict("blueprint blockquote not written as the template words it")
    # format guide rule 5: the preamble routes the agent to uipath-genome, not to the Build With skills
    comment = re.search(r"<!--\s*UIPATH-AUTOMATION-GENOME.*?-->", text, re.S | re.I)
    if comment and "uipath-genome" not in comment.group(0):
        r.strict("preamble comment does not name uipath-genome as the skill that builds the genome")
    blockquote = re.search(r"^>.*UiPath automation blueprint.*$", text, re.M | re.I)
    if blockquote and "uipath-genome" not in blockquote.group(0):
        r.strict("blueprint blockquote does not name uipath-genome as the skill that builds the genome")
    pos = h2_positions(text)
    for s in sections:
        if section_pos(pos, s) is None:
            r.core(f"missing section '## {s}'")
        elif s not in pos:
            r.strict(f"section '## {s}' present under a longer or differently cased heading")
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
                # skill-mapping guide rule 2; advisory: a platform row in Build With does no harm — the
                # resources still reach the target through the solution and the open-items files
                r.strict(f"operate-only skill '{name}' in {heading}; it belongs under Platform Dependencies")
    # a criterion is a list item in any form: '- ', '- [ ] ', '* ' or '1. '; the format guide numbers them
    criteria = [l for l in section_body(text, "Acceptance Criteria").splitlines() if re.match(r"([-*]|\d+\.) \S", l)]
    if len(criteria) < CORE_FLOOR:
        r.core(f"acceptance criteria: {len(criteria)} found, expected >= {CORE_FLOOR}")
    elif len(criteria) < min_criteria:
        r.strict(f"acceptance criteria: {len(criteria)} found, expected >= {min_criteria} for the stated complexity")
    if any(not re.match(r"\d+\. ", l) for l in criteria):
        r.strict("acceptance criteria are not numbered ('1. …'), so a report cannot cite them by number")
    for line in criteria:
        if re.search(r"completes successfully|handles errors properly", line, re.I):
            r.core(f"generic acceptance criterion: {line.strip()}")

    body = body_without_source_map(text)
    for tok in BANNED_BODY_TOKENS:
        # a prefix token counts at the start of a word only: `in_Folder`, never "login_page" or "layout_name"
        if (re.search(rf"\b{re.escape(tok)}\w", body) if tok.endswith("_") else tok in body):
            r.strict(f"code-level token '{tok}' in the genome body (outside Source Map)")
    for num, question in re.findall(r"^(\d+)\. (.*)$", section_body(text, "Configuration Questions"), re.M):
        pointer = "?" not in question and re.search(r"Configuration Question \d+", question)  # a question the process genome asks
        if not pointer and not re.search(r"\((setting|constant); default:", question):
            r.strict(f"configuration question {num} does not name its kind and default as '(setting; default: …)' or '(constant; default: …)'")


def effective_flows(ts: str) -> tuple[list[tuple[str, str]], bool]:
    """(flows, headed): the '### Flow N' blocks, or — when there is no such heading but the section names a
    unit of work — the whole section as one flow. The heading is a format rule; the unit of work is the contract."""
    blocks = flow_blocks(ts)
    if blocks:
        return blocks, True
    if re.search(r"unit of work", ts, re.I):
        return [("Flow 1", ts)], False
    return [], False


def check_transactional(text: str, level: str, r: Report, part_of: bool = False) -> None:
    """Transactional Shape: the stub, or flow blocks the format guide describes."""
    ts = section_body(text, "Transactional Shape")
    if not ts.strip() or ts.strip().startswith(STUB):
        return
    if "**Recommendation:**" in ts or re.search(r"^\|\s*(Producer|Consumer)\s*\|", ts, re.M):
        r.strict("Transactional Shape carries a verdict (Recommendation line or Producer/Consumer mode table)")
    flows, headed = effective_flows(ts)
    if not flows:
        r.shape("Transactional Shape is neither the stub nor flows naming their unit of work")
        return
    if not headed:
        r.strict("Transactional Shape describes its flow without '### Flow N' headings")
    # a component reached through a process genome's links is inside it, with or without its 'Part of:' line
    in_process = level == "component" and (part_of or "Part of:" in text)
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
        if not re.search(r"unit of work", body, re.I):
            r.shape(f"Transactional Shape {name}: names no unit of work")
        elif "**Unit of work:**" not in body:
            r.strict(f"Transactional Shape {name}: no '**Unit of work:**' line")
        external = EXTERNAL_SIDE.search(body)
        split = table_rows(body, "| Unit of work | Option |")
        if not external and not split:
            r.strict(f"Transactional Shape {name}: no Split options table and no 'outside this genome' line")
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
            # the consumer owes the item retry and the consecutive-failure stop (format guide rule 4)
            if not re.search(r"retr(y|ie)", body, re.I) or not re.search(r"consecutive|stops? after \d", body, re.I):
                r.strict(f"Transactional Shape {name}: outcomes do not state the item retry and the consecutive-failure stop")
        if external:
            continue
        units: dict[str, set[str]] = {}
        for row in split:
            m = re.match(r"([ABC])\b", row[1]) if len(row) >= 2 else None
            if m:
                units.setdefault(row[0], set()).add(m.group(1))
            if len(row) >= 2 and row[1].strip() not in SPLIT_OPTIONS:
                r.strict(f"Transactional Shape {name}: option cell '{row[1]}' of '{row[0]}' holds more than its letter — the format guide defines A, B and C")
        for unit, opts in units.items():
            if opts != SPLIT_OPTIONS:
                r.strict(f"Transactional Shape {name}: unit '{unit}' lacks option(s) {sorted(SPLIT_OPTIONS - opts)}")
        alt = next((l for l in body.splitlines() if l.startswith("**Alternative units of work:**")), "")
        if alt and not re.search(r":\*\*\s*none\b", alt, re.I) and len(units) < 2:
            r.strict(f"Transactional Shape {name}: alternative units of work named but split options cover only one unit")
        header = next((l for l in body.splitlines() if l.strip().startswith("| Unit of work | Option |")), "")
        cols = [c.lower() for c in cells(header)]
        if "requires" not in cols or "changes against as-is" not in cols:
            r.strict(f"Transactional Shape {name}: Split options table has no Requires and Changes against as-is columns")
            continue
        if cols != SPLIT_COLUMNS:
            r.strict(f"Transactional Shape {name}: Split options columns are {cols}, expected Unit of work, Option, Requires, Changes against as-is")
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
    blocks, _ = effective_flows(ts)
    if not blocks:
        r.core("Transactional Shape: expected flows naming their unit of work, found none")
        return
    if flows is not None and len(blocks) != flows:
        r.core(f"Transactional Shape: {len(blocks)} flow(s), expected {flows}")
    # the primary unit's line only: never the alternatives line or a table header, and whole words ('row', not 'throw')
    unit_lines = " ".join(l for l in ts.splitlines() if re.match(r"[*_\s>-]*unit of work\b", l, re.I))
    for tok in units:
        if not re.search(rf"\b{re.escape(tok)}s?\b", unit_lines, re.I):
            r.core(f"Transactional Shape: no 'Unit of work' line names '{tok}'")


def check_steps_table(text: str, r: Report) -> None:
    """An extracted genome's step table: one row per Workflow step (core), reference-only cells (strict)."""
    if not section_body(text, "Source Map").strip():
        return
    table = steps_table(text)
    if table is None:
        r.core("Source Map has no '### Steps' table pairing each Workflow step with its source objects")
        return
    header, rows = table
    if header != STEPS_COLUMNS:
        r.strict(f"step table columns are {header}, expected Step, Source objects, Data sets, Captures, Notes")
    steps = workflow_steps(text)
    keys = [row[0] for row in rows]
    for step in steps:
        if keys.count(step) != 1:
            r.core(f"step table: Workflow step {step} has {keys.count(step)} rows, expected exactly one")
    for key in sorted(set(keys) - set(steps), key=lambda k: (len(k), k)):
        r.core(f"step table: row '{key}' names no Workflow step — key a row by the step's number only")
    for row in rows:
        row = row + [""] * (len(STEPS_COLUMNS) - len(row))
        sources, prose = references(row[1])
        if not sources:
            r.strict(f"step table, step {row[0]}: no source object")
        data, data_prose = references(row[2])
        for part in prose + data_prose:
            r.strict(f"step table, step {row[0]}: '{part[:60]}' is not a reference — move it to Notes")
        if not data and row[2].strip().lower() != "none":
            r.strict(f"step table, step {row[0]}: Data sets is empty — write 'none' when the step reads no data set")
        if not re.fullmatch(r"\d+", row[3]):
            r.strict(f"step table, step {row[0]}: Captures '{row[3]}' is not a count")


# --- levels -------------------------------------------------------------------------------------

def component_links(path: Path, text: str) -> list[tuple[str, Path, bool]]:
    """(link, component genome path, is a library) per row of a process genome's Components table."""
    out = []
    for row in table_rows(section_body(text, "Components"), "| #"):
        m = re.search(r"\]\(([^)]+-genome\.md)\)", " | ".join(row))
        if m:
            out.append((m.group(1), (path.parent / m.group(1)).resolve(),
                        len(row) > 2 and bool(re.search(r"\blibrary\b", row[2], re.I))))
    return out


def check_component(path: Path, a: argparse.Namespace, part_of: bool, shape: bool = True, library: bool = False) -> list[str]:
    text = path.read_text(encoding="utf-8")
    # a library is named so in its process genome's Components table, or in its own Transactional Shape stub
    library = library or bool(re.search(r"^Not transactional:[^\n]*\blibrar(y|ies)\b", section_body(text, "Transactional Shape").strip(), re.I))
    r = Report(a.profile, a.shape_checks == "gate")
    level = complexity_of(text)
    min_steps = MIN_STEPS_BY_COMPLEXITY.get(level, a.min_steps)
    check_common(text, "component", COMPONENT_SECTIONS, r, MIN_CRITERIA_BY_COMPLEXITY.get(level, a.min_criteria))
    pos = h2_positions(text)
    bw, wf = section_pos(pos, "Build With"), section_pos(pos, "Workflow")
    if bw is not None and wf is not None and bw > wf:
        r.core("Build With must precede Workflow")
    if not re.search(r"uipath-[a-z-]+", section_body(text, "Build With")):
        r.core("Build With names no skill")
    workflow = section_body(text, "Workflow")
    steps = len(re.findall(r"^(?:\d+\.|[-*]) \S", workflow, re.M))  # top-level numbered or bulleted steps
    # a test component's steps are its cases and a library's its public workflows (format guide § Population Matrix)
    exempt = library or bool(re.search(r"^\d+\. \*\*Test case:", workflow, re.M))
    if steps < CORE_FLOOR and not exempt:
        r.core(f"workflow: {steps} numbered steps, expected >= {CORE_FLOOR}")
    elif steps < min_steps and not exempt:
        r.strict(f"workflow: {steps} numbered steps, expected >= {min_steps} for complexity {level or 'not stated'}")
    if len(re.findall(r"^\d+\. \*\*", workflow, re.M)) < min(steps, min_steps):
        r.strict("workflow: steps not all in the '1. **Step name**' form")
    cq = section_body(text, "Configuration Questions")
    questions = re.findall(r"^\d+\. ", cq, re.M)
    if not cq.strip():
        r.core("Configuration Questions section is empty")
    elif not questions and "no configuration needed" not in cq:
        r.strict("Configuration Questions: neither a numbered list of questions nor the stub line")
    if a.source_map:
        sm = section_body(text, "Source Map")
        if not sm.strip():
            r.core("missing or empty '## Source Map' section")
        for tok in a.source_map:
            if tok not in sm:
                r.core(f"Source Map does not mention '{tok}'")
    check_steps_table(text, r)
    if part_of and "Part of:" not in text:
        r.strict("component inside a process genome lacks the 'Part of:' line")
    check_transactional(text, "component", r, part_of)
    if a.shape and shape:
        check_shape_assertion(text, a.shape, a.flows, a.unit, r)
    for tok in a.expect:
        if tok.lower() not in text.lower():
            r.core(f"expected token '{tok}' not found")
    return [f"{path.name}: {e}" for e in r.errors]


def check_process(path: Path, a: argparse.Namespace) -> list[str]:
    text = path.read_text(encoding="utf-8")
    r = Report(a.profile, a.shape_checks == "gate")
    check_common(text, "process", PROCESS_SECTIONS, r, MIN_CRITERIA_BY_COMPLEXITY.get(complexity_of(text), a.min_criteria))
    pos = h2_positions(text)
    cp, pm = section_pos(pos, "Components"), section_pos(pos, "Process Map")
    if cp is not None and pm is not None and cp > pm:
        r.core("Components must precede Process Map")
    comp = section_body(text, "Components")
    if len([l for l in comp.splitlines() if l.startswith("|") and "uipath-" in l]) < 2:
        r.core("Components table: fewer than 2 rows naming a skill")
    for s in a.skills:
        if not re.search(rf"\b{re.escape(s)}\b", comp):
            r.core(f"Components table lacks skill '{s}'")
    for row in table_rows(comp, "| #"):
        if len(row) > 2 and re.search(r"\b(dispatcher|performer)\b", row[2], re.I):
            r.strict(f"Components: role word in the Type cell of '{row[1]}' — it reads the component type only")
    links = component_links(path, text)
    if not links:
        r.core("Components table links no component genome")
    component_errors: list[str] = []
    for link, target, is_library in links:
        if not target.exists():
            r.core(f"linked component genome missing on disk: {link}")
        else:
            component_errors.extend(check_component(target, argparse.Namespace(**{**vars(a), "expect": [], "source_map": []}),
                                                    part_of=True, shape=False, library=is_library))
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


def check_export(genomes: list[tuple[Path, bool]], processes: list[dict], recordsets: list[dict]) -> tuple[list[str], list[str]]:
    """(failures, notes) of every step table against the export's inventory. Ids are compared as text."""
    by_id = {str(p["id"]): p for p in processes}
    by_name: dict[str, list[dict]] = {}
    for p in processes:
        by_name.setdefault(p["name"].lower(), []).append(p)
    data = {str(d["id"]): d for d in recordsets}
    errors, notes, used = [], [], []
    for path, is_library in genomes:
        table = steps_table(path.read_text(encoding="utf-8")) if path.exists() else None
        for row in (table[1] if table else []):
            row = row + [""] * (len(STEPS_COLUMNS) - len(row))
            where = f"{path.name} step {row[0]}"
            sources, _ = references(row[1])
            if not sources:
                errors.append(f"{where}: no source object")
            for name, ident in sources:
                p = by_id.get(ident or "")
                if ident is None:
                    errors.append(f"{where}: `{name}` has no id — cite it as `Name` (id)")
                elif p is None:
                    hint = " — it is a data set: move it to Data sets" if ident in data else ""
                    errors.append(f"{where}: `{name}` ({ident}) is no process of the export{hint}")
                elif p["name"].lower() != name.lower():
                    errors.append(f"{where}: id {ident} is `{p['name']}`, the row says `{name}`")
                else:
                    used.append((where, is_library, p))
            for name, ident in references(row[2])[0]:
                d = data.get(ident or "")
                if ident is None:
                    errors.append(f"{where}: data set `{name}` has no id — cite it as `Name` (id)")
                elif d is None:
                    hint = " — it is a process: move it to Source objects" if ident in by_id else ""
                    errors.append(f"{where}: data set `{name}` ({ident}) is no data set of the export{hint}")
                elif d.get("drives", True) is False:
                    errors.append(f"{where}: `{name}` ({ident}) drives nothing (a file the step writes, a URL) — name it in Notes")
                elif d["name"].lower() != name.lower() and not d["name"].lower().endswith("::" + name.lower()):
                    errors.append(f"{where}: data set id {ident} is `{d['name']}`, the row says `{name}`")
    # the built roots: every process a non-library step was built from, and what they call
    scope = {str(p["id"]) for _, lib, p in used if not lib} or set(by_id)
    frontier = list(scope)
    while frontier:
        for c in (by_id.get(frontier.pop()) or {}).get("calls", []):
            callee = str(c.get("calleeId"))
            if callee not in scope:
                scope.add(callee)
                frontier.append(callee)
    for where, lib, p in used:
        if lib and str(p["id"]) not in scope:
            twins = [str(q["id"]) for q in by_name.get(p["name"].lower(), []) if str(q["id"]) in scope]
            if twins:
                errors.append(f"{where}: `{p['name']}` ({p['id']}) is not reachable from the built roots; the copy they run is {', '.join(twins)}")
            else:
                notes.append(f"{where}: `{p['name']}` ({p['id']}) is a library workflow no built component calls")
    return errors, notes


def resolve(pattern: str) -> list[Path]:
    path = Path(pattern)
    if path.exists() or not any(c in pattern for c in "*?["):
        return [path] if path.exists() else []
    return sorted(Path(".").glob(pattern))


def check_tokens(paths: list[Path], tokens: list[str], minimum: float, files: int | None) -> list[str]:
    errors: list[str] = []
    if files is not None and len(paths) != files:
        errors.append(f"{len(paths)} file(s) match, expected {files}: {', '.join(p.as_posix() for p in paths) or 'none'}")
    text = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    missing = [t for t in tokens if t not in text]
    if tokens and (len(tokens) - len(missing)) / len(tokens) < minimum:
        errors.append(f"{len(tokens) - len(missing)}/{len(tokens)} tokens found, expected >= {minimum:.0%}; missing: {', '.join(missing)}")
    return errors


def load_inventory(path: str, what: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, dict) and "id" in x and "name" in x for x in data):
        sys.exit(f"FAIL: {path}: the {what} is a list of objects with 'id' and 'name' (regenerate it with the source guide's script)")
    return data


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
    ap.add_argument("--min", type=float, default=1.0, help="tokens: fraction of --expect tokens that must be found")
    ap.add_argument("--files", type=int, default=None, help="tokens: exact number of files the pattern must match")
    ap.add_argument("--processes", help="process inventory JSON the framework script derived from the export")
    ap.add_argument("--recordsets", help="recordset list JSON from the same script")
    a = ap.parse_args(argv)
    if bool(a.processes) != bool(a.recordsets):
        ap.error("--processes and --recordsets go together")

    paths = resolve(a.genome)
    notes: list[str] = []
    if a.level == "tokens":
        errors = ([f"no file matches {a.genome}"] if not paths else []) + check_tokens(paths, a.expect, a.min, a.files)
    elif len(paths) != 1:
        errors = [f"expected exactly one file matching {a.genome}, found {len(paths)}: {', '.join(p.as_posix() for p in paths) or 'none'}"]
    else:
        errors = (check_component(paths[0], a, part_of=False) if a.level == "component" else check_process(paths[0], a))
        if a.processes:
            text = paths[0].read_text(encoding="utf-8")
            genomes = ([(target, lib) for _, target, lib in component_links(paths[0], text)]
                       if a.level == "process" else [(paths[0], False)])
            export_errors, notes = check_export(genomes, load_inventory(a.processes, "process inventory"),
                                                load_inventory(a.recordsets, "recordset list"))
            errors += export_errors
    for e in errors:
        print(f"FAIL: {e}")
    for n in notes:
        print(f"NOTE: {n}")
    if not errors:
        print(f"OK ({a.profile if a.level != 'tokens' else 'tokens'}): {', '.join(p.as_posix() for p in paths)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
