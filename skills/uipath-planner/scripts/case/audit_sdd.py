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


LAYERS_MD = Path(__file__).resolve().parent.parent.parent / "references" / "case" / "case-design-layers-guide.md"


def load_model_facts() -> tuple[dict, str | None]:
    """Parse the canonical tables in the case reference files (stdlib only).

    Reads the `### Task types` table (column 1 literals), the `### Lifecycle
    gates` table (legal WHEN rules per gate slot), and the `### Naming rules`
    fenced regex — all from case-design-layers-guide.md.

    Returns ``(facts, degraded)``. ``degraded`` is None on a clean parse and a
    reason string when the model checks could not be armed — a missing guide or a
    parse that came back empty. Never degrade silently: the caller turns the
    reason into a finding, so a renamed heading or a reshaped table fails loudly
    instead of no-op'ing the task-type enum, WHEN pairing, and naming checks.
    """
    try:
        text = LAYERS_MD.read_text(encoding="utf-8")
    except OSError:
        return {}, f"{LAYERS_MD.name} not found beside this script"

    def section(heading: str) -> str:
        match = re.search(rf"^### {re.escape(heading)}\s*$(.*?)(?=^#|\Z)", text, re.M | re.S)
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
    pattern = re.search(r"```\s*(\^[^\n`]+\$)\s*```", section("Naming rules"))
    facts["name_pattern"] = re.compile(pattern.group(1)) if pattern else None

    empty = [
        label for label, ok in (
            ("`### Task types` table", bool(facts["task_types"])),
            ("`### Lifecycle gates` table", bool(yes_when)),
            ("`### Naming rules` regex fence", facts["name_pattern"] is not None),
        ) if not ok
    ]
    if empty:
        return {}, (
            f"{LAYERS_MD.name} parsed but " + ", ".join(empty) + " came back empty — the heading was "
            "renamed or the table reshaped; the model checks are disarmed until it is restored"
        )
    return facts, None


def model_findings(text: str, facts: dict, carried_names: frozenset[str] = frozenset()) -> list[str]:
    """Checks driven by the canonical model tables: task-type enum, WHEN/Marks-Complete
    pairing legality, and display-name character rules. ``carried_names`` — stage/task
    display names present in the draft — are exempt from the minting charset (the naming
    contract preserves them verbatim); the ':' ban stays structural. ``facts`` comes
    from load_model_facts(); an empty dict means the caller already emitted the
    degradation finding, so skip these checks rather than assert on missing tables."""
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
        def name_finding(kind: str, name: str) -> str | None:
            name = name.strip()
            if ":" in name:
                return f"{kind} name {name!r} contains ':' — the structural ban; case-execution events are colon-delimited"
            if name in carried_names:
                return None  # read from the draft: preserved verbatim, minting charset does not apply
            if not name_pattern.fullmatch(name):
                return (
                    f"{ADVISORY}{kind} name {name!r} uses characters outside the safe display set in\n     case-design-layers-guide.md § Naming rules. Only ':' is known to break routing, so this does not\n     gate: prefer the safe set when MINTING a name, and keep a name the user or the source supplied"
                )
            return None

        for kind, name, _ in stage_blocks(text):
            finding = name_finding(kind.lower(), name)
            if finding:
                findings.append(finding)
        for match in re.finditer(r"^#{5} Task [S\d.]+: ([^\n]+)$", text, re.M):
            finding = name_finding("task", strip_id_suffix(match.group(1)))
            if finding:
                findings.append(finding)
    return findings



EXIT_TYPES_YES = {"exit-only", "return-to-origin", "wait-for-user"}
EXIT_TYPES_NO = {"exit-only", "wait-for-user"}
RECIPIENT_PREFIX = re.compile(r"^(Role|User|UserGroup|Email|Expression):")
FORBIDDEN_VOCAB = ["groupOperator", "savedFilterTrees", "io-binding", "auto-mint", "originalVar", "inputOutputs["]


def decision_routed_behaviors(text: str) -> list[str]:
    """`Behavior` prose from decision buttons that map a variable to a value.

    A decision task's `**Actions:**` table routes outcomes:

        | Button | Maps To                   | Behavior                       |
        | Reject | reviewDecision = "Reject" | ... the Application Rejected lane |

    A row whose `Maps To` carries an assignment is a deterministic route, so the
    lane it names cannot be keyed on `user-selected-stage` (a picker is for a lane
    a PERSON launches). Kept in code rather than in the template: the design
    lane's reading budget is saturated, and prose that was long enough to land
    this repair cost a passing task while prose short enough to be safe left the
    agent churning without producing an SDD.
    """
    out: list[str] = []
    for chunk in re.split(r"(?=\*\*Actions:\*\*)", text):
        if not chunk.startswith("**Actions:**"):
            continue
        for _, cells in table_rows(chunk):
            if len(cells) >= 3 and "=" in cells[1]:
                out.append(cells[2])
    return out


def section_slice(text: str, heading: str) -> str:
    """Body of a `### {heading}` section up to the next heading of any level."""
    match = re.search(rf"^### {re.escape(heading)}\s*$(.*?)(?=^#{{1,5}} |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def table_rows(chunk: str) -> list[tuple[int, list[str]]]:
    """(offset line index, cells) for pipe-table body rows in a chunk.

    Header detection is structural: a ruler row (`|---|...`) is skipped, and so is
    the row immediately preceding it — never a name list, which silently passes
    headers it does not know (e.g. `| T# | Trigger Type | ... |`)."""
    lines = chunk.splitlines()

    def is_ruler(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith("|"):
            return False
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        return bool(cells) and all(set(c) <= {"-", ":", " "} and c for c in cells)

    rows = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or is_ruler(line):
            continue
        if i + 1 < len(lines) and is_ruler(lines[i + 1]):
            continue  # header row
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells:
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



AMBIGUOUS_PERSONA = re.compile(r"^[A-Z][A-Za-z/ ]{2,40}\s+or\s+[A-Za-z][A-Za-z/ ]{2,40}$")
PERSONA_HEADER = re.compile(r"^(assignee|owner|performer|responsible|persona|role)s?$", re.I)


def ambiguous_personas(text: str) -> list[str]:
    """Persona cells naming two roles — an unresolved conditional, not an owner.

    A task runs as exactly one persona. "Underwriter or Credit Analyst" is a
    routing rule the author stated but never modelled: the reader cannot tell
    who owns the task, and no guard picks between them at run time.
    """
    found: list[str] = []
    cols: list[int] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            cols = None
            continue
        if re.match(r"^[\s\-:|]+$", stripped.strip("|")):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        header = [i for i, c in enumerate(cells) if PERSONA_HEADER.match(c)]
        if header:
            cols = header
            continue
        if cols:
            for i in cols:
                if i < len(cells) and AMBIGUOUS_PERSONA.match(cells[i]):
                    found.append(cells[i])
    return sorted(dict.fromkeys(found))

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
            findings.append(f"forbidden skill-internal term {token!r} in the SDD body (case-sdd-template.md § Validation footer)")

    has_wfu_exit = re.search(r"\bwait-for-user\b", text) is not None
    has_uss_entry = re.search(r"\buser-selected-stage\b", text) is not None
    if has_wfu_exit and not has_uss_entry:
        findings.append("wait-for-user exit with no user-selected-stage entry anywhere — validate fails with 'no possible stage options'")
    if has_uss_entry and not has_wfu_exit:
        findings.append("user-selected-stage entry with no wait-for-user exit anywhere — validate fails with 'will never be met'")

    for persona in ambiguous_personas(text):
        findings.append(
            f"task persona {persona!r} names two roles — a task runs as exactly one "
            "persona, so an either/or cell is a routing rule stated but not modelled: "
            "assign the role the case actually uses and put the condition in a guard, "
            "or split it into two guarded task variants"
        )

    routed = " || ".join(decision_routed_behaviors(text)).casefold()
    if routed:
        for kind, name, block in stage_blocks(text):
            if kind != "Secondary Stage" or "user-selected-stage" not in block:
                continue
            if name.casefold() in routed:
                findings.append(
                    f"stage {name!r} is entered by user-selected-stage but a decision button routes to it "
                    "— a picker rule cannot carry a deterministic route: key the entry on the decision "
                    '(selected-stage-completed("<origin>") + IF on the fact) and give the origin the '
                    "matching Marks Stage Complete: No diverting exit"
                )

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

    # FE-parity structural rules (PO.Frontend validation, design-expressible subset)
    entry_rows_all: list[tuple[str, str, list[str]]] = []  # (stage, WHEN cell, cells)
    for kind, stage_name, block in stage_blocks(text):
        entry = re.search(r"^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if entry:
            for _, cells in table_rows(entry.group(1)):
                entry_rows_all.append((stage_name, cells[0], cells))
                # self-reference: an entry selecting its own stage never fires
                for arg in re.findall(r"selected-stage-(?:completed|exited)\s*\(\s*[\"\u201c\u2018']([^\"\u201d\u2019']+)", cells[0]):
                    if strip_id_suffix(arg).strip() == stage_name:
                        findings.append(f"stage {stage_name!r}: entry condition references its own stage — it can never fire")
    if stage_blocks_exist := bool(list(stage_blocks(text))):
        if not any("case-entered" in when for _, when, _ in entry_rows_all):
            findings.append("no stage carries a `case-entered` entry row — the case has no start (first stage requires one)")

    # >=1 trigger row (FE: NO_TRIGGER_NODE)
    if not table_rows(section_slice(text, "Case Triggers")):
        findings.append("Case Triggers has no rows — a case needs at least one trigger (T02)")

    # SLA bounds + case-vs-stage duration (FE: SLA_BELOW_MIN/ABOVE_MAX_MINUTES, ROOT_SLA_LESS_THAN_NODES)
    UNIT_MIN = {"min": 1, "h": 60, "d": 1440, "w": 10080, "m": 43200}

    def sla_minutes(count: str, unit: str) -> int | None:
        try:
            return int(float(count)) * UNIT_MIN[unit.strip().strip("`")]
        except (ValueError, KeyError):
            return None

    case_minutes = None
    meta = section_slice(text, "Case Metadata")
    case_sla = re.search(r"^\|\s*Case-Level SLA\s*\|\s*(\d+(?:\.\d+)?)\s*(min|h|d|w|m)\b", meta, re.M)
    if case_sla:
        case_minutes = sla_minutes(case_sla.group(1), case_sla.group(2))
        if case_sla.group(2) == "min" and case_minutes is not None and not 15 <= case_minutes <= 1000:
            findings.append(f"Case-Level SLA {case_minutes} min is out of bounds — minute counts are bounded 15–1000")
    for kind, stage_name, block in stage_blocks(text):
        sla_sec = re.search(r"^#### Stage SLA\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if not sla_sec:
            continue
        for _, cells in table_rows(sla_sec.group(1)):
            if len(cells) < 2:
                continue
            minutes = sla_minutes(cells[0], cells[1])
            if minutes is None:
                continue
            if cells[1].strip("`") == "min" and not 15 <= minutes <= 1000:
                findings.append(f"stage {stage_name!r}: SLA {cells[0]} min out of bounds — minute counts are bounded 15–1000")
            if case_minutes is not None and minutes > case_minutes:
                findings.append(
                    f"stage {stage_name!r}: stage SLA ({cells[0]} {cells[1].strip('`')}) exceeds the case-level SLA — "
                    "the case would breach before the stage"
                )
            break

    # vacuous required-* (FE + validate: 'no required stage(s)/task(s) selected')
    required_stage = re.search(r"^\*\*Required for Case Completion:\*\*\s*Yes\b", text, re.M)
    if "required-stages-completed" in text and list(stage_blocks(text)) and not required_stage:
        findings.append(
            "required-stages-completed is used but no stage declares '**Required for Case Completion:** Yes' — "
            "validate fails with 'no required stage(s) selected'"
        )
    for kind, stage_name, block in stage_blocks(text):
        exit_sec = re.search(r"^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if not exit_sec or "required-tasks-completed" not in exit_sec.group(1):
            continue
        has_required_task = False
        for env in re.finditer(r"\*\*Task envelope\*\*(.*?)(?=^#{1,6} |\*\*Entry Condition:\*\*|\Z)", block, re.M | re.S):
            for _, cells in table_rows(env.group(1)):
                if cells and cells[0].strip("`") == "Yes":
                    has_required_task = True
        if not has_required_task and TASK_HEADING.search(block):
            findings.append(
                f"stage {stage_name!r}: required-tasks-completed completion but no task envelope declares Required: Yes — "
                "validate fails with 'no task(s) marked as required'"
            )

    # empty stage condition tables (FE: ENTRY/EXIT_CONDITION_MISSING) — an entry-less stage is unreachable
    for kind, stage_name, block in stage_blocks(text):
        entry_sec = re.search(r"^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if entry_sec and not table_rows(entry_sec.group(1)):
            findings.append(f"stage {stage_name!r}: Stage Entry Conditions has no rows — the stage can never activate")
        exit_sec = re.search(r"^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if exit_sec and not table_rows(exit_sec.group(1)):
            findings.append(f"stage {stage_name!r}: Stage Exit Conditions has no rows — the stage can never complete or exit")

    # entry-vs-case-exit overlap: case exit/completion evaluates BEFORE stage entry, so a stage
    # entry identical to a case-exit row leaves the stage permanently unreachable
    def norm_if(cell: str) -> str:
        cell = cell.strip().strip("`")
        return "" if cell in ("—", "-", "") else re.sub(r"\s+", "", cell)

    case_exit_rows = []
    for _, cells in table_rows(section_slice(text, "Case Exit Conditions")):
        sel = re.search(r"selected-stage-(completed|exited)\s*\(\s*[\"\u201c\u2018']([^\"\u201d\u2019']+)", cells[0])
        if sel and len(cells) >= 2:
            case_exit_rows.append((sel.group(1), strip_id_suffix(sel.group(2)).strip(), norm_if(cells[1])))
    if case_exit_rows:
        for stage_name, when, cells in entry_rows_all:
            sel = re.search(r"selected-stage-(completed|exited)\s*\(\s*[\"\u201c\u2018']([^\"\u201d\u2019']+)", when)
            if not sel or len(cells) < 2:
                continue
            key = (sel.group(1), strip_id_suffix(sel.group(2)).strip(), norm_if(cells[1]))
            if key in case_exit_rows:
                findings.append(
                    f"stage {stage_name!r}: entry condition matches a case-exit row (same rule, selector, IF) — "
                    "case exit takes precedence, leaving the stage permanently unreachable; differentiate the IF guards"
                )

    # exit-overrides-completion: within one stage, a guarded completion (Yes + IF) sharing its WHEN
    # with an unguarded exit (No, IF empty) never fires — exit evaluates first
    for kind, stage_name, block in stage_blocks(text):
        exit_sec = re.search(r"^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |\Z)", block, re.M | re.S)
        if not exit_sec:
            continue
        rows = []
        for _, cells in table_rows(exit_sec.group(1)):
            bare = [c.strip("`") for c in cells]
            marks = next((c for c in bare if c in ("Yes", "No")), None)
            if marks and len(cells) >= 2:
                rows.append((rule_name(cells[0]) or "", norm_if(cells[1]), marks))
        for when_y, if_y, marks_y in rows:
            if marks_y != "Yes" or not if_y:
                continue
            for when_n, if_n, marks_n in rows:
                if marks_n == "No" and when_n == when_y and not if_n:
                    findings.append(
                        f"stage {stage_name!r}: unguarded exit row shares WHEN {when_y!r} with a guarded completion — "
                        "the exit always fires first and the stage never completes; give the exit the inverse IF"
                    )

    # duplicate case-exit rows (FE: condition too similar)
    seen_exit_rows: set[tuple] = set()
    for _, cells in table_rows(section_slice(text, "Case Exit Conditions")):
        key = tuple(norm_if(c) if i == 1 else c.strip("`") for i, c in enumerate(cells[:4]))
        if key in seen_exit_rows:
            findings.append(f"duplicate case-exit row {cells[0]!r} — identical rules are ambiguous; differentiate or drop one")
        seen_exit_rows.add(key)

    # Selector existence: stage selectors name declared stages, task selectors declared tasks
    stage_names = {n.strip() for _, n, _ in stage_blocks(text)}
    task_names = {strip_id_suffix(m.group(3)).strip() for m in TASK_HEADING.finditer(text)}
    if stage_names:
        for line_no, line in enumerate(lines, 1):
            for call in re.finditer(r"selected-stage-(?:completed|exited)\s*\(([^)]*)\)", line):
                for arg in re.findall(r"[\"\u201c\u2018']([^\"\u201d\u2019']+)[\"\u201d\u2019']", call.group(1)):
                    if strip_id_suffix(arg).strip() not in stage_names:
                        findings.append(f"line {line_no}: stage selector references {arg!r} — no stage with that display name exists")
            for call in re.finditer(r"selected-tasks-completed\s*\(([^)]*)\)", line):
                for arg in re.findall(r"[\"\u201c\u2018']([^\"\u201d\u2019']+)[\"\u201d\u2019']", call.group(1)):
                    if task_names and strip_id_suffix(arg).strip() not in task_names:
                        findings.append(f"line {line_no}: task selector references {arg!r} — no task with that display name exists")

    # selected-tasks-completed scope: only non-adhoc tasks in the SAME stage (layers § Sequencing)
    for kind, stage_name, block in stage_blocks(text):
        own_tasks = {strip_id_suffix(m.group(3)).strip() for m in TASK_HEADING.finditer(block)}
        adhoc_tasks = set()
        tasks_in_block = list(TASK_HEADING.finditer(block))
        for index, task in enumerate(tasks_in_block):
            end = tasks_in_block[index + 1].start() if index + 1 < len(tasks_in_block) else len(block)
            tb = block[task.start():end]
            if re.search(r"^\*\*Activation Mode:\*\*\s*`?adhoc\b", tb, re.M):
                adhoc_tasks.add(strip_id_suffix(task.group(3)).strip())
        for call in re.finditer(r"selected-tasks-completed\s*\(([^)]*)\)", block):
            for arg in re.findall(r"[\"\u201c\u2018']([^\"\u201d\u2019']+)[\"\u201d\u2019']", call.group(1)):
                name = strip_id_suffix(arg).strip()
                if name in adhoc_tasks:
                    findings.append(f"stage {stage_name!r}: selected-tasks-completed selects adhoc task {name!r} — it selects only non-adhoc tasks")
                elif task_names and name in task_names and name not in own_tasks:
                    findings.append(f"stage {stage_name!r}: selected-tasks-completed selects {name!r} from another stage — it selects only tasks in the SAME stage")

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


# Findings carrying this prefix are printed but do not gate AUDIT OK. Reserved for rules whose
# violation is a display preference rather than a platform failure: gating on those costs full repair
# rounds and — worse for a display NAME — makes the agent rewrite the user's own domain vocabulary,
# which the lane's authoring policy forbids outright. Only rules with a known runtime consequence
# block (a ':' in a name breaks colon-delimited case-execution event routing; that one still gates).
ADVISORY = "[advisory] "


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

    carried: frozenset[str] = frozenset()
    if draft_path is not None and draft_path.is_file():
        draft_text = draft_path.read_text(encoding="utf-8")
        # Draft headings are pre-normalization — letter prefixes (Task R.2:) included.
        carried = frozenset(
            {name.strip() for _, name, _ in stage_blocks(draft_text)}
            | {strip_id_suffix(m.group(1)).strip() for m in re.finditer(r"^#{5} Task [A-Za-z0-9.]+: ([^\n]+)$", draft_text, re.M)}
        )
    facts, degraded = load_model_facts()
    if degraded:
        findings.append(f"model checks disarmed: {degraded}")
    findings.extend(lineage_findings(text))
    findings.extend(model_findings(text, facts, carried))
    findings.extend(contract_findings(text, facts or {"gate_rules": {}, "yes_when": set(), "no_when": set()}))

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


def emit_advisories(advisories: list[str]) -> None:
    """Suggestions, not gates — never repair-looped, never a reason to withhold the ready flip."""
    if not advisories:
        return
    print("\nADVISORY (does not gate AUDIT OK — fix only if you agree):", file=sys.stderr)
    for n, a in enumerate(advisories[:10], 1):
        print(f"  {n}. {a}", file=sys.stderr)
    if len(advisories) > 10:
        print(f"  … and {len(advisories) - 10} more", file=sys.stderr)


def main() -> None:
    args = [a for a in sys.argv[1:]]
    draft: Path | None = None
    if "--draft" in args:
        i = args.index("--draft")
        draft = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    all_findings = audit(Path(args[0]), draft)
    findings = [f for f in all_findings if not f.startswith(ADVISORY)]
    advisories = [f[len(ADVISORY):] for f in all_findings if f.startswith(ADVISORY)]
    if findings:
        shown = findings[:40]
        print("AUDIT FAIL — repair these, then re-run:", file=sys.stderr)
        for n, f in enumerate(shown, 1):
            print(f"  {n}. {f}", file=sys.stderr)
        if len(findings) > len(shown):
            print(f"  … and {len(findings) - len(shown)} more", file=sys.stderr)
        emit_advisories(advisories)
        sys.exit(1)
    print("AUDIT OK: sdd.md template shape is clean")
    emit_advisories(advisories)


if __name__ == "__main__":
    main()
