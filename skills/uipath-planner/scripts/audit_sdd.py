#!/usr/bin/env python3
"""Deterministic template-shape audit for a planner-authored Case Management SDD.

Usage:
    python3 audit_sdd.py <sdd.md> [--draft <sdd.draft.md>]

Read-only. Exit 0 = shape-clean. Exit 1 = numbered findings on stderr; repair
the document with Write/Edit and re-run until clean. `--draft` additionally
verifies the finalized document preserves the draft's ordered stage/task
inventory and every draft `=js:` expression.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## Document History",
    "## Planner Handoff",
    "## Table of Contents",
    "## Section 1: Case Definition",
    "### Case Metadata",
    "### Case Triggers",
    "### Case Exit Conditions",
    "### Case Variables",
    "## Section 2: Stages & Tasks",
    "## Section 3: Personas & App Views",
    "### Personas",
    "### Process App Views",
    "## Section 4: Integrations",
]

SUMMARY_ONLY_HEADINGS = [
    "Source", "Case Objective", "Actors And Systems", "Case Trigger", "Stages",
    "Business Rules", "Task Plan", "Resource Resolution", "Acceptance Scenarios",
]

STAGE_MARKERS = [
    "**Type:**",
    "**Design Rationale:**",
    "#### Stage Entry Conditions",
    "#### Stage Exit Conditions",
    "#### Tasks",
]

TASK_MARKERS = [
    "**Type:**",
    "**Activation Mode:**",
    "**Design Rationale:**",
    "**Entry Condition:**",
    "**Task envelope**",
]

# task type -> (detail-block heading, alternate literal markers)
TASK_DETAIL_MARKERS = {
    "action": ("Action Task Detail", "**HITL Implementation:**"),
    "wait-for-connector": ("Connector Task Detail", "**Connector:**", "**Trigger / Event:**"),
    "execute-connector-activity": ("Connector Task Detail", "**Connector:**", "**Resolved Resource:**"),
    "wait-for-timer": ("Timer Task Detail", "**Timer Configuration:**", "**Duration:**", "**Timer:**"),
    "case-management": ("Child Case Task Detail", "**Child Case:**"),
    "process": ("Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"),
    "agent": ("Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"),
    "rpa": ("Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"),
    "api-workflow": ("Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"),
}

CASE_VARIABLES_HEADER = "| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |"

STAGE_HEADING = re.compile(r"^###\s+(Stage\s+\d+|Secondary Stage):\s*(.+?)\s*$", re.M)
TASK_HEADING = re.compile(r"^#####\s+Task\s+(S?\d+|[A-Z]{1,4})\.(\d+):\s*(.+?)\s*$", re.M)
LETTERED_TASK = re.compile(r"^#####\s+Task\s+[A-RT-Z]+[A-Z]*\.\d", re.M)


def strip_id_suffix(name: str) -> str:
    return re.sub(r"\s*\(`[^`]*`\)\s*$", "", name).strip()


def stage_blocks(text: str):
    """Yield (kind, display name, block text) for each stage heading."""
    matches = list(STAGE_HEADING.finditer(text))
    section3 = re.search(r"^## Section 3: Personas & App Views\s*$", text, re.M)
    doc_end = section3.start() if section3 else len(text)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else doc_end
        yield match.group(1), strip_id_suffix(match.group(2)), text[match.start():end]


def inventory(text: str):
    """Ordered (stage, task) names, id suffixes stripped."""
    entries = []
    for _, stage_name, block in stage_blocks(text):
        for task in TASK_HEADING.finditer(block):
            entries.append((stage_name, strip_id_suffix(task.group(3))))
    return entries


def js_expressions(text: str):
    return {re.sub(r"\s+", " ", m.group(0)).strip() for m in re.finditer(r"=js:[^|\n]+", text)}


HIGH_WORDS = r"over|above|at\s+least|more\s+than|greater\s+than|in\s+excess\s+of|exceed(?:s|ing)?"
LOW_WORDS = r"under|below|at\s+most|less\s+than"
COMPARATOR_THRESHOLD = re.compile(
    rf"(>=|<=|>|<|≥|≤|\b(?:{HIGH_WORDS}|{LOW_WORDS})\b)\s*"
    r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*([mk])?\b",
    re.IGNORECASE,
)
EXECUTABLE_LINE = re.compile(r"=js:|vars\.|\bowner\b|\brecipient\b|Role:", re.IGNORECASE)
PROSE_MARKER = re.compile(r"^\*\*(Design Rationale|Description):\*\*", re.M)


def comparator_direction(token: str) -> str:
    token = token.casefold().strip()
    if token in (">", ">=", "≥") or re.fullmatch(HIGH_WORDS, token):
        return "high"
    return "low"


def threshold_variants(number: str, suffix: str | None) -> list[str]:
    """Spellings of one currency threshold: '5' + 'M' -> 5M, 5 million, 5000000, 5,000,000.

    The bare short numeral ('5') is deliberately excluded — it would match any
    digit in an executable line and make the check vacuous.
    """
    bare = number.replace(",", "")
    if suffix:
        factor = 1_000_000 if suffix.lower() == "m" else 1_000
        word = "million" if suffix.lower() == "m" else "thousand"
        variants = [f"{bare}{suffix.lower()}", f"{bare} {word}"]
        if "." not in bare:
            expanded = str(int(bare) * factor)
            variants += [expanded, f"{int(expanded):,}"]
        return variants
    variants = [bare]
    if "." not in bare:
        variants.append(f"{int(bare):,}")
    return variants


def unencoded_thresholds(draft: str, final: str) -> list[str]:
    """Draft comparator-currency thresholds with no executable encoding in the final.

    A threshold counts as encoded when some final line mentions one of its
    spellings AND carries an executable signal (`=js:` / `vars.` / owner /
    recipient / `Role:`). Prose repetition alone is not an encoding.
    """
    findings = []
    seen: set[tuple[str, str]] = set()
    # Rationale/Description prose never counts as an encoding — the guard must
    # live in an executable table cell (owner/recipient/WHEN/IF/Inputs).
    executable_lines = [
        line for line in final.splitlines()
        if EXECUTABLE_LINE.search(line) and not PROSE_MARKER.match(line.strip())
    ]
    for match in COMPARATOR_THRESHOLD.finditer(draft):
        direction = comparator_direction(match.group(1))
        variants = threshold_variants(match.group(2), match.group(3))
        key = (variants[-1], direction)
        if key in seen:
            continue
        seen.add(key)
        needles = [re.compile(rf"(?<![\w.]){re.escape(v)}(?!\w)", re.IGNORECASE) for v in variants]
        covered = False
        for line in executable_lines:
            if not any(n.search(line) for n in needles):
                continue
            ternary = "?" in line and ":" in line.split("?", 1)[-1]
            line_dirs = {comparator_direction(t.group(1)) for t in re.finditer(
                rf"(>=|<=|>|<|≥|≤|\b(?:{HIGH_WORDS}|{LOW_WORDS})\b)", line, re.IGNORECASE)}
            if ternary or direction in line_dirs:
                covered = True
                break
        if not covered:
            findings.append(
                f"draft threshold policy {match.group(0).strip()!r} has no {direction}-side executable encoding — "
                f"add the guard to an owner/recipient/WHEN/IF cell (fast-path step 9), e.g. "
                f"`=js:vars.<attr> > <threshold> ? \"Role:<ExceptionRole>\" : \"Role:<DefaultRole>\"`; "
                f"Rationale/Description prose does not count"
            )
    return findings


VARIABLE_ROW = re.compile(
    r"^\|\s*([A-Za-z]\w*)\s*\|\s*(In|Out|Variable)\s*\|"
    r"\s*[^|]*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|",
    re.M,
)


def lineage_findings(text: str) -> list[str]:
    """Mirror sdd_check's mapping + lineage closure: every consumed variable is
    declared and produced (-> output, `X =` assignment, Default, or trigger-sourced)."""
    findings: list[str] = []
    category: dict[str, str] = {}
    src_trig: dict[str, str] = {}
    default: dict[str, str] = {}
    for name, cat, st, d in VARIABLE_ROW.findall(text):
        category[name] = cat
        src_trig[name] = st.strip()
        default[name] = d.strip()
    if not category:
        return findings  # template checks already flag a missing table
    refs = set(re.findall(r"=vars\.([A-Za-z]\w*)", text)) - {"X"}
    undeclared = sorted(r for r in refs if r not in category)
    if undeclared:
        findings.append(f"{len(undeclared)} =vars consumed but not declared in Case Variables: {', '.join(undeclared)}")
    produced = set(re.findall(r"->\s*([A-Za-z]\w*)", text)) | set(
        re.findall(r"\b([A-Za-z]\w*)\s*=\s*(?!=)", text)
    )
    open_lineage = sorted(
        r for r in refs
        if r in category and category.get(r) != "In"
        and not default.get(r) and not src_trig.get(r) and r not in produced
    )
    for name in open_lineage:
        findings.append(
            f"variable {name!r} is consumed but never produced — keep its producer output row "
            f"(`-> {name}`), assignment, Default, or trigger source"
        )
    return findings


_REFS = Path(__file__).resolve().parent.parent / "references"
LAYERS_MD = _REFS / "case-design-layers-guide.md"
SPEC_MD = _REFS / "case-sdd-spec.md"


def load_model_facts() -> dict:
    """Parse the canonical tables in the case reference files (stdlib only).

    Reads the `### Task types` table (column 1 literals) and the `### Lifecycle
    gates` table (legal WHEN rules per Marks-complete value) from
    case-design-layers-guide.md, and the `### Naming rules` fenced regex from
    case-sdd-spec.md. Returns {} when the layers guide is absent so the shape
    audit still runs.
    """
    try:
        text = LAYERS_MD.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        spec_text = SPEC_MD.read_text(encoding="utf-8")
    except OSError:
        spec_text = ""

    def section(heading: str, source: str = None) -> str:
        match = re.search(
            rf"^### {re.escape(heading)}\s*$(.*?)(?=^#|\Z)",
            source if source is not None else text,
            re.M | re.S,
        )
        return match.group(1) if match else ""

    facts: dict = {}
    facts["task_types"] = set(re.findall(r"^\|\s*`([a-z][a-z-]+)`\s*\|", section("Task types"), re.M))
    yes_when: set[str] = set()
    no_when: set[str] = set()
    gate_rules: dict[str, set[str]] = {}
    for row in re.finditer(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|", section("Lifecycle gates"), re.M):
        gate, marks = row.group(1).strip(), row.group(2).strip()
        rules = set(re.findall(r"`([a-z][a-z-]+)`", row.group(3)))
        if not rules:
            continue
        gate_rules[gate] = rules
        if marks == "Yes":
            yes_when.update(rules)
        elif marks == "No":
            no_when.update(rules)
    facts["yes_when"], facts["no_when"] = yes_when, no_when
    facts["gate_rules"] = gate_rules
    pattern = re.search(r"```\s*(\^[^\n`]+\$)\s*```", section("Naming rules", spec_text))
    facts["name_pattern"] = re.compile(pattern.group(1)) if pattern else None
    if not facts["task_types"] or not yes_when:
        return {}
    return facts


def model_findings(text: str) -> list[str]:
    """Checks driven by the canonical model tables: task-type enum, WHEN/Marks-Complete
    pairing legality, and display-name character rules."""
    facts = load_model_facts()
    if not facts:
        return []
    findings: list[str] = []

    for match in re.finditer(r"^\*\*Type:\*\*\s*`?([a-z][a-z-]+)`?\s*$", text, re.M):
        if match.group(1) not in facts["task_types"]:
            findings.append(
                f"task type {match.group(1)!r} outside the closed enum (case-design-layers-guide.md § Task types): "
                + ", ".join(sorted(facts["task_types"]))
            )

    # WHEN x Marks-Complete pairing applies only inside tables whose header carries a
    # 'Marks ... Complete' column — entry tables put Yes/No in their Interrupting column,
    # and reading that cell as Marks-Complete false-flags legal entry rows.
    known_rules = facts["yes_when"] | facts["no_when"]
    lines = text.splitlines()
    marks_col: int | None = None
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            marks_col = None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if any(re.fullmatch(r"Marks (Stage|Case) Complete", c) for c in cells):
            marks_col = next(i for i, c in enumerate(cells) if c.startswith("Marks "))
            continue
        if marks_col is None or len(cells) <= marks_col or set(cells[0]) <= {"-", ":", " "}:
            continue
        when = re.match(r"`?([a-z][a-z-]+)", cells[0])
        marks = cells[marks_col] if cells[marks_col] in ("Yes", "No") else None
        if not when or marks is None or when.group(1) not in known_rules:
            continue
        legal = facts["yes_when"] if marks == "Yes" else facts["no_when"]
        if when.group(1) not in legal:
            findings.append(
                f"line {line_no}: WHEN {when.group(1)!r} with Marks Complete {marks!r} is an illegal "
                "pair (case-design-layers-guide.md § Lifecycle gates)"
            )

    name_pattern = facts.get("name_pattern")
    if name_pattern:
        for kind, name, _ in stage_blocks(text):
            if not name_pattern.fullmatch(name.strip()):
                findings.append(f"{kind.lower()} name {name!r} breaks case-sdd-spec.md § Naming rules")
        for match in re.finditer(r"^#{5} Task [S\d.]+: ([^\n]+)$", text, re.M):
            candidate = strip_id_suffix(match.group(1)).strip()
            if not name_pattern.fullmatch(candidate):
                findings.append(f"task name {candidate!r} breaks case-sdd-spec.md § Naming rules")
    return findings



EXIT_TYPES_YES = {"exit-only", "return-to-origin", "wait-for-user"}
EXIT_TYPES_NO = {"exit-only", "wait-for-user"}
RECIPIENT_PREFIX = re.compile(r"^(Role|User|UserGroup|Email|Expression):")
FORBIDDEN_VOCAB = ["groupOperator", "savedFilterTrees", "io-binding", "auto-mint", "originalVar", "inputOutputs["]


def section_slice(text: str, heading: str) -> str:
    """Body of a `### {heading}` section up to the next heading of any level."""
    match = re.search(rf"^### {re.escape(heading)}\s*$(.*?)(?=^#{{1,5}} |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def table_rows(chunk: str) -> list[tuple[int, list[str]]]:
    """(offset line index, cells) for pipe-table body rows in a chunk (header + ruler skipped)."""
    rows = []
    for i, line in enumerate(chunk.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or set(cells[0]) <= {"-", ":", " "} or cells[0] in ("WHEN", "Name", "Button", "Threshold", "SLA"):
            continue
        rows.append((i, cells))
    return rows


def rule_name(cell: str) -> str | None:
    match = re.match(r"`?([a-z][a-z-]+)", cell.strip())
    return match.group(1) if match else None


def declared_sla_titles(text: str) -> dict[str, set[str]]:
    """SLA titles per target: 'root' from the §1.1 metadata row; each stage from its
    `**SLA Title:**` lines. Casefolded keys and titles."""
    titles: dict[str, set[str]] = {}
    meta = section_slice(text, "Case Metadata")
    row = re.search(r"^\|\s*SLA Title\s*\|\s*([^|]+?)\s*\|", meta, re.M)
    if row and row.group(1).strip() not in ("—", ""):
        titles["root"] = {row.group(1).strip()}
    for _, stage_name, block in stage_blocks(text):
        found = {m.group(1).strip() for m in re.finditer(r"^\*\*SLA Title:\*\*\s*([^\n<]+)", block, re.M)}
        if found:
            titles[stage_name.casefold()] = found
    return titles


def contract_findings(text: str, facts: dict) -> list[str]:
    """Deterministic contract checks beyond template shape: gate-slot WHEN legality,
    exit-type pairing, SLA title closure, uniqueness, recipients, buttons, Out producers,
    completion row, wait-for-user pairing, markers, vocabulary."""
    findings: list[str] = []
    lines = text.splitlines()

    if "<!-- planner-handoff:v1 -->" not in text:
        findings.append("missing '<!-- planner-handoff:v1 -->' marker (Planner Handoff scaffold)")
    if "`<UNRESOLVED>`" in text:
        findings.append("backtick-wrapped `<UNRESOLVED>` — the marker renders as plain text, exactly <UNRESOLVED>")
    for token in FORBIDDEN_VOCAB:
        if token in text:
            findings.append(f"forbidden skill-internal term {token!r} in the SDD body (case-sdd-spec.md § Markers & vocabulary)")

    has_wfu_exit = re.search(r"\bwait-for-user\b", text) is not None
    has_uss_entry = re.search(r"\buser-selected-stage\b", text) is not None
    if has_wfu_exit and not has_uss_entry:
        findings.append("wait-for-user exit with no user-selected-stage entry anywhere — validate fails with 'no possible stage options'")
    if has_uss_entry and not has_wfu_exit:
        findings.append("user-selected-stage entry with no wait-for-user exit anywhere — validate fails with 'will never be met'")

    # Case Exit Conditions: >= 1 completing row
    case_exit = section_slice(text, "Case Exit Conditions")
    if case_exit and not any("Yes" in cells for _, cells in table_rows(case_exit)):
        findings.append("Case Exit Conditions has no 'Marks Case Complete: Yes' row — the case can never complete")
    if "return-to-origin" in case_exit:
        findings.append("return-to-origin in Case Exit Conditions — it is a stage-completion exit type only")

    # Case Variables: Out rows need a producer or Default
    produced = set(re.findall(r"->\s*([A-Za-z]\w*)", text)) | set(re.findall(r"\b([A-Za-z]\w*)\s*=\s*(?!=)", text))
    for name, cat, _, default in VARIABLE_ROW.findall(text):
        if cat == "Out" and not default and name not in produced:
            findings.append(f"Out variable {name!r} has no Default and no producing Outputs row (`-> {name}` / `{name} = ...`)")

    # Uniqueness: stage labels and task display names, case-wide
    seen_stages: set[str] = set()
    seen_tasks: dict[str, str] = {}
    for _, stage_name, block in stage_blocks(text):
        key = stage_name.strip()
        if key in seen_stages:
            findings.append(f"duplicate stage label {key!r} — stage labels are unique across the case")
        seen_stages.add(key)
        for task in TASK_HEADING.finditer(block):
            task_name = strip_id_suffix(task.group(3)).strip()
            if task_name in seen_tasks and seen_tasks[task_name] != stage_name + task.group(0):
                findings.append(f"duplicate task display name {task_name!r} — task names are unique across the whole case")
            seen_tasks.setdefault(task_name, stage_name + task.group(0))

    gate_rules = facts.get("gate_rules", {})
    stage_entry_legal = gate_rules.get("Stage entry", set())
    task_entry_legal = gate_rules.get("Task entry", set())
    sla_titles = declared_sla_titles(text)

    for kind, stage_name, block in stage_blocks(text):
        # Stage entry WHEN legality
        entry = re.search(r"^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |\*\*Task envelope\*\*|\Z)", block, re.M | re.S)
        if entry and stage_entry_legal:
            for _, cells in table_rows(entry.group(1)):
                rule = rule_name(cells[0])
                if rule and rule not in stage_entry_legal and (rule in facts["yes_when"] | facts["no_when"] | task_entry_legal | {"case-entered", "adhoc", "runs-sequentially", "current-stage-entered"}):
                    findings.append(f"stage {stage_name!r}: entry WHEN {rule!r} is not a legal stage-entry rule (case-design-layers-guide.md § Lifecycle gates)")
        # Stage exit rows: Exit Type x Marks Stage Complete legality
        exit_sec = re.search(r"^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if exit_sec:
            for _, cells in table_rows(exit_sec.group(1)):
                bare = [c.strip("`") for c in cells]
                etype = next((c for c in bare if c in EXIT_TYPES_YES), None)
                marks = next((c for c in bare if c in ("Yes", "No")), None)
                if etype and marks:
                    legal = EXIT_TYPES_YES if marks == "Yes" else EXIT_TYPES_NO
                    if etype not in legal:
                        findings.append(
                            f"stage {stage_name!r}: exit type {etype!r} with Marks Stage Complete {marks!r} is illegal — "
                            f"legal for {marks}: {', '.join(sorted(legal))}"
                        )
        # Task entry WHEN legality + Buttons Maps To
        tasks = list(TASK_HEADING.finditer(block))
        for index, task in enumerate(tasks):
            end = tasks[index + 1].start() if index + 1 < len(tasks) else len(block)
            task_block = block[task.start():end]
            task_name = strip_id_suffix(task.group(3))
            entry_tbl = re.search(r"\*\*Entry Condition:\*\*(.*?)(?=\*\*Task envelope\*\*|\Z)", task_block, re.S)
            if entry_tbl and not table_rows(entry_tbl.group(1)):
                findings.append(
                    f"task {task_name!r}: Entry Condition has no table rows — an executable gate collapsed "
                    "into prose drops out of the planning handoff (and a task with no entry never starts)"
                )
            if entry_tbl and task_entry_legal:
                for _, cells in table_rows(entry_tbl.group(1)):
                    rule = rule_name(cells[0])
                    if rule and rule not in task_entry_legal and (rule in facts["yes_when"] | facts["no_when"] | stage_entry_legal):
                        findings.append(f"task {task_name!r}: entry WHEN {rule!r} is not a legal task-entry rule (case-design-layers-guide.md § Lifecycle gates)")
            recipient = re.search(r"^\*\*Recipient:\*\*\s*([^\n]+)", task_block, re.M)
            if recipient:
                value = recipient.group(1).strip().strip("`")
                if value not in ("—", "<UNRESOLVED>") and not RECIPIENT_PREFIX.match(value) and not value.startswith("="):
                    findings.append(f"task {task_name!r}: Recipient {value!r} lacks a typed prefix (Role:/User:/UserGroup:/Email:/Expression:)")

    # Buttons Maps To LHS: a §1.5 name, taskOutcome, or the task's own output
    # (read downstream via a direct producer reference). Flag only true orphans —
    # an identifier that never occurs outside Buttons tables is a typo or dead route.
    declared_vars = {name for name, _, _, _ in VARIABLE_ROW.findall(text)} | {"taskOutcome"}
    button_spans = [m.span(1) for m in re.finditer(r"^\|\s*Button\s*\|\s*Maps To\s*\|[^\n]*$(.*?)(?=^[^|]|\Z)", text, re.M | re.S)]
    outside = "".join(
        text[(button_spans[i - 1][1] if i else 0):start] for i, (start, _) in enumerate(button_spans)
    ) + (text[button_spans[-1][1]:] if button_spans else text)
    for start, end in button_spans:
        for _, cells in table_rows(text[start:end]):
            if len(cells) < 2:
                continue
            target = re.match(r"`?([A-Za-z]\w*)", cells[1])
            if not target:
                continue
            lhs = target.group(1)
            if lhs in declared_vars:
                continue
            if not re.search(rf"\b{re.escape(lhs)}\b", outside):
                findings.append(
                    f"button {cells[0]!r} maps to {lhs!r}, which is never declared, extracted, or read anywhere else — "
                    "a typo or a dead decision route"
                )

    # sla-status-change SLA-title closure (target validity is checked in audit())
    if sla_titles:
        for line_no, line in enumerate(lines, 1):
            for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", line, re.I):
                args = re.findall(r"[\"\u201c\u2018']([^\"\u201d\u2019']+)[\"\u201d\u2019']", call.group(1))
                if len(args) < 2:
                    continue
                target = args[0].strip().casefold()
                declared = sla_titles.get(target)
                if declared is not None and args[1].strip().casefold() not in {t.casefold() for t in declared}:
                    findings.append(
                        f"line {line_no}: sla-status-change references SLA title {args[1]!r} but target {args[0]!r} declares: "
                        + ", ".join(sorted(declared))
                    )
    return findings


def audit(sdd_path: Path, draft_path: Path | None) -> list[str]:
    findings: list[str] = []
    text = sdd_path.read_text(encoding="utf-8")

    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first.startswith("# SDD — "):
        findings.append("first heading must be '# SDD — {Case Name}'")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
            findings.append(f"missing required heading {heading!r}")
    for heading in SUMMARY_ONLY_HEADINGS:
        if re.search(rf"^## {re.escape(heading)}\s*$", text, re.M):
            findings.append(f"summary-only heading '## {heading}' — render the full template instead")

    if CASE_VARIABLES_HEADER not in text:
        findings.append(f"Case Variables table must use the literal header {CASE_VARIABLES_HEADER!r}")
    if LETTERED_TASK.search(text):
        findings.append("lettered task prefixes (Task R.1 / W.1 / CC.1 / ESC.1) — renumber as Task S{K}.{M}")
    for line_no, line in enumerate(text.splitlines(), 1):
        if re.search(r"\\n\s*(?:\*\*|#|\|)", line):
            findings.append(
                f"line {line_no}: literal \\n escape corrupts the document structure — rewrite the block with real newlines"
            )

    stages = list(stage_blocks(text))
    if not stages:
        findings.append("no '### Stage {N}:' / '### Secondary Stage:' blocks found")
    for kind, stage_name, block in stages:
        for marker in STAGE_MARKERS:
            if marker not in block:
                findings.append(f"stage {stage_name!r} missing {marker!r}")
        stage_type = re.search(r"^\*\*Type:\*\*\s*([^\n]+)", block, re.M)
        if stage_type and stage_type.group(1).strip() not in ("Stage", "ExceptionStage"):
            findings.append(
                f"stage {stage_name!r} has '**Type:** {stage_type.group(1).strip()}' — the stage Type literal is 'Stage'; "
                "secondary-ness lives in the heading, '**Stage Kind:** secondary', and '**Interrupting:**'"
            )
        if kind == "Secondary Stage" and not re.search(r"^\*\*Interrupting:\*\*\s*(Yes|No)\b", block, re.M):
            findings.append(f"secondary stage {stage_name!r} missing explicit '**Interrupting:** Yes' or 'No'")
        if kind == "Secondary Stage" and "return-to-origin" in block and not re.search(
            r"^\*\*Interrupting:\*\*\s*Yes\b", block, re.M
        ):
            findings.append(
                f"secondary stage {stage_name!r} exits return-to-origin but does not declare '**Interrupting:** Yes'"
            )

        tasks = list(TASK_HEADING.finditer(block))
        if not tasks:
            findings.append(f"stage {stage_name!r} has no '##### Task' detail blocks — every task in its Tasks table needs one")
            continue
        for index, task in enumerate(tasks):
            end = tasks[index + 1].start() if index + 1 < len(tasks) else len(block)
            task_block = block[task.start():end]
            task_name = strip_id_suffix(task.group(3))
            for marker in TASK_MARKERS:
                if marker not in task_block:
                    findings.append(f"task {task_name!r} missing {marker!r}")
            type_match = re.search(r"^\*\*Type:\*\*\s*`?([a-z-]+)", task_block, re.M)
            if type_match:
                markers = TASK_DETAIL_MARKERS.get(type_match.group(1))
                if markers and not any(marker in task_block for marker in markers):
                    findings.append(f"task {task_name!r} (type {type_match.group(1)}) missing type detail block {markers[0]!r}")

    # sla-status-change arg shape: 2 quoted args (breach) or 3 (at-risk), and the
    # target must resolve: the literal 'root' or a declared stage display name.
    valid_targets = {"root"} | {name.casefold() for _, name, _ in stage_blocks(text)}
    for line_no, line in enumerate(text.splitlines(), 1):
        for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", line, re.I):
            args = re.findall(r"[\"“‘']([^\"”’']+)[\"”’']", call.group(1))
            if args and len(args) not in (2, 3):
                findings.append(
                    f"line {line_no}: sla-status-change takes (\"<SLA target>\",\"<SLA Title>\") "
                    f"or (...,\"<At-Risk Escalation Display Name>\"); got {len(args)} args"
                )
            if args and valid_targets and args[0].strip().casefold() not in valid_targets:
                findings.append(
                    f"line {line_no}: sla-status-change target {args[0]!r} is neither the literal 'root' (case-level) "
                    f"nor a stage declared in this SDD — never the case name or a synonym"
                )

    findings.extend(lineage_findings(text))
    findings.extend(model_findings(text))
    findings.extend(contract_findings(text, load_model_facts() or {"gate_rules": {}, "yes_when": set(), "no_when": set()}))

    draft_findings: list[str] = []
    if draft_path is not None:
        if not draft_path.is_file():
            draft_findings.append(f"{draft_path} is gone — never delete or rename the draft; finalize renders a new sdd.md beside it")
        else:
            draft = draft_path.read_text(encoding="utf-8")
            draft_inv, final_inv = inventory(draft), inventory(text)
            if draft_inv != final_inv:
                missing = [f"{s} / {t}" for s, t in draft_inv if (s, t) not in final_inv]
                added = [f"{s} / {t}" for s, t in final_inv if (s, t) not in draft_inv]
                detail = "; ".join(
                    part for part in (
                        f"missing: {', '.join(missing[:8])}" if missing else "",
                        f"added/renamed: {', '.join(added[:8])}" if added else "",
                        "order changed" if not missing and not added else "",
                    ) if part
                )
                draft_findings.append(
                    f"stage/task inventory differs from draft (draft={len(draft_inv)}, final={len(final_inv)}) — {detail}"
                )
            lost = sorted(js_expressions(draft) - js_expressions(text))
            for expression in lost[:10]:
                draft_findings.append(f"draft policy expression lost: {expression}")
            draft_findings.extend(unencoded_thresholds(draft, text))

    findings = draft_findings + findings
    return findings


def main() -> None:
    args = [a for a in sys.argv[1:]]
    draft: Path | None = None
    if "--draft" in args:
        i = args.index("--draft")
        draft = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    findings = audit(Path(args[0]), draft)
    if findings:
        shown = findings[:40]
        print("AUDIT FAIL — repair these, then re-run:", file=sys.stderr)
        for n, f in enumerate(shown, 1):
            print(f"  {n}. {f}", file=sys.stderr)
        if len(findings) > len(shown):
            print(f"  … and {len(findings) - len(shown)} more", file=sys.stderr)
        sys.exit(1)
    print("AUDIT OK: sdd.md template shape is clean")


if __name__ == "__main__":
    main()
