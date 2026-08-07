#!/usr/bin/env python3
"""Mechanical check on a case-design ``sdd.md`` (markdown only).

Case design (the uipath-planner Case Design Lane) stops at the approved
``sdd.md`` — no caseplan exists yet — so these checks parse the markdown
directly to confirm the SDD is sound enough to *deliver downstream* (the
build's planning pass trusts it verbatim). Domain sense is graded separately
by the ``llm_judge`` criterion; this script is the deterministic "rules and
mappings" half.

NOTE: this file is deliberately kept byte-identical between
``tests/tasks/uipath-maestro-case/_shared/`` and
``tests/tasks/uipath-planner/_shared/`` (per-suite _shared scoping; guarded by
``test_shared_twins.py``). Apply any change to both copies.

Checks (domain-agnostic):
  0. Template shape — the document is a full SDD template render, not a prose
     summary or build note.
  1. Mapping integrity — every ``=vars.<name>`` resolves to a §Case Variables row.
  2. Lineage closure  — every consumed variable is produced before use (In /
     Default / sourceTriggers / task Output ``-> name`` / button ``name = ...``).
  3. Task-type enum   — every task ``Type`` is one of the 9 legal types.
  4. Per-gate rule legality — each Entry / Completion / Exit / Case-exit rule is
     legal **for its gate**, with the correct Marks-Complete pairing.
  5. Conditions present — each stage section has Entry + Exit conditions, and the
     case can close (a ``required-stages-completed`` case-completion row exists).
  6. Return-lane semantics — every ``return-to-origin`` exit uses
     ``required-tasks-completed`` or ``wait-for-connector`` with
     ``Marks Stage Complete: Yes``, and every exception (secondary) stage that
     returns declares ``Interrupting: Yes`` (you can only return to a stage you
     interrupted).
  7. PO.Frontend name/SLA parity — stage/task/SLA/escalation names, uniqueness,
     duration bounds, conditional expressions, recipients, and at-risk fields.

Finds ``sdd.md`` under the current working directory.
"""

from __future__ import annotations

import glob
import re
import sys

TASK_TYPES = {
    "action", "agent", "rpa", "process", "api-workflow",
    "execute-connector-activity", "wait-for-connector", "wait-for-timer",
    "case-management",
}

# Legal rule types per gate (mirrors case-tool schema-helpers VALID_*_RULE_TYPES).
STAGE_ENTRY = {"case-entered", "selected-stage-completed", "selected-stage-exited",
               "wait-for-connector", "user-selected-stage", "sla-status-change"}
STAGE_COMPLETION = {"required-tasks-completed", "wait-for-connector"}   # Marks: Yes
STAGE_EXIT = {"selected-tasks-completed", "wait-for-connector"}          # Marks: No
TASK_ENTRY = {"current-stage-entered", "selected-tasks-completed",
              "wait-for-connector", "adhoc", "runs-sequentially",
              # the `start-task` SLA response; CLI-verified valid on task entry
              # (uip 1.198.0-preview.102). See skills/uipath-maestro-case/
              # references/sla-response-shapes.md section 3.
              "sla-status-change"}
CASE_COMPLETION = {"required-stages-completed", "wait-for-connector"}    # Marks: Yes
CASE_EXIT = {"selected-stage-completed", "selected-stage-exited",
             "wait-for-connector"}                                       # Marks: No
EXIT_TYPES = {"exit-only", "wait-for-user", "return-to-origin"}
RETURN_TO_ORIGIN_COMPLETION = {"required-tasks-completed", "wait-for-connector"}
KNOWN_RULES = STAGE_ENTRY | STAGE_COMPLETION | STAGE_EXIT | TASK_ENTRY | CASE_COMPLETION | CASE_EXIT
SUMMARY_ONLY_HEADINGS = {
    "Source", "Case Objective", "Actors And Systems", "Case Trigger", "Stages",
    "Business Rules", "Task Plan", "Resource Resolution", "Acceptance Scenarios",
}
INTEGRATION_HEADINGS = {
    "Integration Service Connectors", "API Workflows", "Agents", "Processes & RPA",
    "Child Cases", "External Agents",
}
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


def _find_sdd() -> str:
    matches = sorted(p for p in glob.glob("**/sdd.md", recursive=True) if "/.venv/" not in p)
    if not matches:
        sys.exit("FAIL: no sdd.md found under the current directory")
    return matches[0]


def _rule_token(cell: str) -> str | None:
    """Leading rule keyword from a WHEN cell (``case-entered``, ``adhoc``, …)."""
    m = re.match(r"`?\s*([a-z][a-z]+(?:-[a-z]+)*)", cell.strip())
    return m.group(1) if m else None


def _return_to_origin_pairing_issue(
    rule: str, marks_complete: bool, where: str
) -> str | None:
    """Return an error unless a return lane uses a supported completing trigger."""
    if marks_complete and rule in RETURN_TO_ORIGIN_COMPLETION:
        return None
    return (
        "rule: return-to-origin requires 'required-tasks-completed' or "
        f"'wait-for-connector' with Marks=Yes ({where})"
    )


def _has_heading(text: str, heading: str) -> bool:
    return re.search(rf"^{re.escape(heading)}\s*$", text, re.M) is not None


def _sdd_template_shape_issues(text: str, source: str = "sdd.md") -> list[str]:
    """Require the full SDD template shape, not a compact design summary."""
    issues: list[str] = []
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first.startswith("# SDD — "):
        issues.append(f"template: first heading must be '# SDD — {{Case Name}}' at {source}")

    required_headings = [
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
    for heading in required_headings:
        if not _has_heading(text, heading):
            issues.append(f"template: missing required heading {heading!r} in {source}")

    for heading in sorted(SUMMARY_ONLY_HEADINGS):
        if _has_heading(text, f"## {heading}"):
            issues.append(f"template: summary-only heading '## {heading}' is not a template SDD")

    if re.search(r"(?im)^(Source|Build mode|Output folder)\s*:", text):
        issues.append(f"template: source/build narration belongs in chat, not {source}")
    if re.search(r"(?i)generated from (the )?(requirements|source) file", text):
        issues.append(f"template: generation-source narration belongs in chat, not {source}")

    stage_matches = list(
        re.finditer(r"^###\s+(Stage\s+\d+|Secondary Stage):\s*(.+?)\s*$", text, re.M)
    )
    if not stage_matches:
        issues.append(f"template: no Stage/Secondary Stage detail blocks found in {source}")
    section3 = re.search(r"^## Section 3: Personas & App Views\s*$", text, re.M)
    doc_end = section3.start() if section3 else len(text)

    for index, match in enumerate(stage_matches):
        end = stage_matches[index + 1].start() if index + 1 < len(stage_matches) else doc_end
        block = text[match.start():end]
        stage_name = match.group(2).strip()
        for marker in (
            "**Type:**",
            "**Design Rationale:**",
            "#### Stage Entry Conditions",
            "#### Stage Exit Conditions",
            "#### Tasks",
        ):
            if marker not in block:
                issues.append(f"template: stage {stage_name!r} missing {marker!r} in {source}")

        task_matches = list(re.finditer(r"^#####\s+Task\s+(?:S)?\d+\.\d+:\s*(.+?)\s*$", block, re.M))
        if not task_matches:
            issues.append(f"template: stage {stage_name!r} has no task detail blocks in {source}")
            continue
        for task_index, task_match in enumerate(task_matches):
            task_end = (
                task_matches[task_index + 1].start()
                if task_index + 1 < len(task_matches)
                else len(block)
            )
            task_block = block[task_match.start():task_end]
            task_name = task_match.group(1).strip()
            for marker in (
                "**Type:**",
                "**Activation Mode:**",
                "**Design Rationale:**",
                "**Entry Condition:**",
                "**Task envelope**",
            ):
                if marker not in task_block:
                    issues.append(f"template: task {task_name!r} missing {marker!r} in {source}")
            task_type = re.search(r"^\*\*Type:\*\*\s*`?([a-z-]+)", task_block, re.M)
            if task_type:
                markers = TASK_DETAIL_MARKERS.get(task_type.group(1))
                if markers and not any(marker in task_block for marker in markers):
                    issues.append(
                        f"template: task {task_name!r} missing type detail block {markers[0]!r} "
                        f"in {source}"
                    )

    if _has_heading(text, "## Section 4: Integrations"):
        has_family_heading = any(_has_heading(text, f"### {heading}") for heading in INTEGRATION_HEADINGS)
        if not has_family_heading and "> None." not in text:
            issues.append(f"template: Section 4 needs integration family headings or '> None.' in {source}")

    return issues


def _sdd_frontend_issues(text: str, source: str = "sdd.md") -> list[str]:
    """Mirror the deterministic stage/task/SLA checks performed by PO.Frontend."""
    issues: list[str] = []
    stage_names: list[str] = []
    in_stage_sla = False
    in_variable_sla = False
    stage_variable_sla = False
    variable_sla_names: set[str] = set()

    def check_duration(count_text: str, unit_text: str, line_no: int) -> None:
        try:
            count = float(count_text.strip())
        except ValueError:
            return
        unit = unit_text.strip().lower()
        if count <= 0:
            issues.append(f"sla: count must be positive at {source}:{line_no}")
        if unit == "min" and not 15 <= count <= 1000:
            issues.append(f"sla: minute count must be between 15 and 1000 at {source}:{line_no}")

    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped == "#### Stage SLA":
            in_stage_sla = True
            in_variable_sla = False
            stage_variable_sla = False
        elif stripped == "### Variable SLA Rules":
            in_variable_sla = True
            in_stage_sla = False
            stage_variable_sla = False
            variable_sla_names = set()
        elif stripped == "##### Stage Variable SLA Rules":
            in_variable_sla = True
            in_stage_sla = False
            stage_variable_sla = True
            variable_sla_names = set()
        elif stripped.startswith("#"):
            in_stage_sla = False
            in_variable_sla = False
            stage_variable_sla = False

        case_sla = re.match(r"^\|\s*Case-Level SLA\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s+([A-Za-z]+)", line, re.I)
        if case_sla:
            check_duration(case_sla.group(1), case_sla.group(2), line_no)

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if in_stage_sla and len(cells) >= 2 and re.fullmatch(r"\d+(?:\.\d+)?", cells[0]):
            check_duration(cells[0], cells[1], line_no)
        if in_variable_sla and len(cells) >= 3 and re.fullmatch(r"\d+(?:\.\d+)?", cells[1]):
            check_duration(cells[1], cells[2], line_no)
            expression = cells[0].strip().strip("\"'")
            if not expression or expression in {"—", "-"}:
                issues.append(
                    f"sla: conditional rule requires an expression at "
                    f"{source}:{line_no}"
                )
            if stage_variable_sla:
                display = cells[3].strip().strip("\"'") if len(cells) >= 4 else ""
                if not display or display in {"—", "-"}:
                    issues.append(
                        f"naming: SLA title is missing at {source}:{line_no}"
                    )
                elif display in variable_sla_names:
                    issues.append(
                        f"naming: duplicate SLA title {display!r} at "
                        f"{source}:{line_no}"
                    )
                else:
                    variable_sla_names.add(display)
                if ":" in display:
                    issues.append(
                        f"naming: SLA title contains ':' at {source}:{line_no}"
                    )

        stage = re.match(r"###\s+(Stage \d+|Exception Stage|Secondary Stage):\s*(.*)", line.strip())
        if stage:
            # The first colon belongs to the SDD heading grammar. Any later colon
            # is part of the authored stage label and would make FE/SDD parsing
            # ambiguous.
            label = re.sub(r"\s*\([^)]*\)\s*$", "", stage.group(2)).strip()
            if not label:
                issues.append(f"naming: stage name is missing at {source}:{line_no}")
            else:
                stage_names.append(label)
            if ":" in label:
                issues.append(f"naming: stage name contains ':' at {source}:{line_no}: {label!r}")

        task = re.match(r"#####\s+Task\s+[\d.]+:\s*(.+)", line.strip())
        if task:
            label = re.sub(r"\s*\([^)]*\)\s*$", "", task.group(1)).strip()
            if ":" in label:
                issues.append(f"naming: task name contains ':' at {source}:{line_no}: {label!r}")

        # SDDs may expose an explicit SLA title, while Phase 1 carries the same
        # value as tasks.md `display-name` on an SLA escalation T-entry.
        sla_title = re.match(r"^\|\s*SLA Title\s*\|\s*([^|]*)\|", line, re.I)
        if sla_title:
            value = sla_title.group(1).strip()
            if not value or value in {"—", "-"}:
                issues.append(f"naming: SLA title is missing at {source}:{line_no}")
            if ":" in value:
                issues.append(f"naming: SLA title contains ':' at {source}:{line_no}")

    duplicates = sorted({name for name in stage_names if stage_names.count(name) > 1})
    for name in duplicates:
        issues.append(f"naming: duplicate stage name {name!r} in {source}")
    return issues


def _colon_issues(text: str, source: str = "sdd.md") -> list[str]:
    """Backward-compatible focused helper used by older checker unit tests."""
    return [issue for issue in _sdd_frontend_issues(text, source) if "contains ':'" in issue]


def _parse_value(value: str) -> str:
    value = value.strip().strip('"\'')
    return "" if value in {"", "—", "-"} else value


def _tasks_frontend_issues(text: str, source: str) -> list[str]:
    """Validate SLA T-entries using the same name/value invariants as FE."""
    issues: list[str] = []
    blocks = re.split(r"(?=^##\s+T\d+\b)", text, flags=re.M)
    rule_names: dict[str, set[str]] = {}
    escalation_names: dict[str, set[str]] = {}
    for block in blocks:
        header = re.match(r"##\s+T\d+[^\n]*", block)
        if not header:
            continue
        header_text = header.group(0)
        is_escalation = bool(re.search(r"Add escalation rule for", header_text, re.I))
        is_sla_entry = is_escalation or bool(
            re.search(r"Set default SLA for|Add conditional SLA rule for", header_text, re.I)
        )
        if not is_sla_entry:
            continue
        target_match = re.search(r"^\s*-\s*target:\s*[\"']?([^\"'\n]+)", block, re.M | re.I)
        target = (target_match.group(1).strip() if target_match else "root")
        display_match = re.search(r"^\s*-\s*display-name:\s*(.*?)\s*$", block, re.M | re.I)
        display = _parse_value(display_match.group(1)) if display_match else ""
        names = escalation_names if is_escalation else rule_names
        names.setdefault(target, set())
        if not display:
            issues.append(f"naming: {'escalation' if is_escalation else 'SLA'} title is missing at {source}")
        elif display in names[target]:
            issues.append(f"naming: duplicate {'escalation' if is_escalation else 'SLA'} title {display!r} at {source}")
        else:
            names[target].add(display)
        if ":" in display:
            issues.append(f"naming: {'escalation' if is_escalation else 'SLA'} title contains ':' at {source}")

        count_match = re.search(r"^\s*-\s*count:\s*([0-9]+(?:\.[0-9]+)?)\s*$", block, re.M | re.I)
        unit_match = re.search(r"^\s*-\s*unit:\s*(\S+)\s*$", block, re.M | re.I)
        if count_match:
            count = float(count_match.group(1))
            unit = unit_match.group(1).strip().lower() if unit_match else ""
            if count <= 0:
                issues.append(f"sla: count must be positive at {source}")
            if unit == "min" and not 15 <= count <= 1000:
                issues.append(f"sla: minute count must be between 15 and 1000 at {source}")

        if re.search(r"conditional SLA rule", header_text, re.I):
            condition = re.search(r"^\s*-\s*(?:condition|expression):\s*(.*?)\s*$", block, re.M | re.I)
            if not condition or not _parse_value(condition.group(1)):
                issues.append(f"sla: conditional rule requires an expression at {source}")

        if is_escalation:
            recipients = re.findall(r"^\s*-\s+(?:User|UserGroup):\s*.+$", block, re.M)
            if not recipients:
                issues.append(f"sla: escalation requires at least one recipient at {source}")
            if re.search(r"^\s*-\s*trigger-type:\s*at-risk\s*$", block, re.M | re.I):
                if not re.search(r"^\s*-\s*at-risk-percentage:\s*\S+", block, re.M | re.I):
                    issues.append(f"sla: at-risk escalation requires at-risk-percentage at {source}")
    return issues


def main() -> None:
    path = _find_sdd()
    text = open(path, encoding="utf-8").read()
    issues: list[str] = []
    issues.extend(_sdd_template_shape_issues(text, path))
    issues.extend(_sdd_frontend_issues(text, path))

    # When Phase 1 has already generated tasks.md next to the SDD, validate its
    # SLA and escalation T-entries before JSON emission.
    tasks_path = glob.glob("**/tasks/tasks.md", recursive=True)
    for candidate in sorted(tasks_path):
        tasks_text = open(candidate, encoding="utf-8").read()
        issues.extend(_tasks_frontend_issues(tasks_text, candidate))

    # --- §Case Variables: | name | In/Out/Variable | type | srcTrig | srcFld | default | desc |
    declared: set[str] = set()
    category: dict[str, str] = {}
    src_trig: dict[str, str] = {}
    default: dict[str, str] = {}
    for name, cat, st, d in re.findall(
        r"^\|\s*([A-Za-z]\w*)\s*\|\s*(In|Out|Variable)\s*\|"
        r"\s*[^|]*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|",
        text, re.M,
    ):
        declared.add(name)
        category[name] = cat
        src_trig[name] = st.strip()
        default[name] = d.strip()
    if not declared:
        sys.exit("FAIL: no §Case Variables table found")

    refs = set(re.findall(r"=vars\.([A-Za-z]\w*)", text)) - {"X"}

    # 1. mapping integrity
    unresolved = sorted(r for r in refs if r not in declared)
    if unresolved:
        issues.append(f"mapping: {len(unresolved)} =vars not declared: {', '.join(unresolved)}")

    # 2. lineage closure
    produced = set(re.findall(r"->\s*([A-Za-z]\w*)", text)) | set(
        re.findall(r"\b([A-Za-z]\w*)\s*=\s*(?!=)", text)
    )
    open_lineage = sorted(
        r for r in refs
        if r in declared and category.get(r) != "In"
        and not default.get(r) and not src_trig.get(r) and r not in produced
    )
    if open_lineage:
        issues.append(
            f"lineage: {len(open_lineage)} variable(s) consumed but never produced: "
            + ", ".join(open_lineage)
        )

    # 3. task-type enum
    # Per-stage **Type:** is always "Stage" post-consolidation; "ExceptionStage"
    # stays whitelisted for back-compat with un-migrated SDDs. Task rows carry the
    # 9 legal task types. The new **Stage Kind:** field is matched separately below.
    bad_types = sorted(
        {t for t in re.findall(r"^\*\*Type:\*\*\s*(\S+)", text, re.M)
         if t not in ("Stage", "ExceptionStage") and t not in TASK_TYPES}
    )
    if bad_types:
        issues.append(f"task-type: invalid type(s): {', '.join(bad_types)}")

    # 3b. **Stage Kind:** enum — optional field; when present must be primary|secondary.
    bad_kinds = sorted(
        {k for k in re.findall(r"^\*\*Stage Kind:\*\*\s*(\S+)", text, re.M)
         if k not in ("primary", "secondary")}
    )
    if bad_kinds:
        issues.append(f"stage-kind: invalid Stage Kind value(s): {', '.join(bad_kinds)}")

    # 4 + 5. per-gate rule legality + entry/exit presence (context-tracking walk)
    gate = cur_stage = None
    has_entry: dict[str, bool] = {}
    has_exit: dict[str, bool] = {}
    is_exc: dict[str, bool] = {}
    interrupting: dict[str, str] = {}
    exit_types: dict[str, set[str]] = {}
    marks_idx: int | None = None
    et_idx: int | None = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"###\s+(Stage \d+|Exception Stage|Secondary Stage):\s*(.*)", s)
        if m:
            cur_stage = re.sub(r"\(.*", "", m.group(2)).strip()
            has_entry.setdefault(cur_stage, False)
            has_exit.setdefault(cur_stage, False)
            # "Secondary Stage" is the v22 heading; "Exception Stage" kept for back-compat
            is_exc[cur_stage] = m.group(1) in ("Exception Stage", "Secondary Stage")
            exit_types.setdefault(cur_stage, set())
            gate = None
            continue
        mk = re.match(r"\*\*Stage Kind:\*\*\s*`?(\w+)", s)
        if mk and cur_stage and mk.group(1).lower() == "secondary":
            # **Stage Kind:** secondary is the authoritative discriminator (it maps to
            # data.stageType); flag the stage as secondary regardless of heading form.
            is_exc[cur_stage] = True
            continue
        if s.startswith("### Case Exit Conditions"):
            gate = "case-exit"; continue
        if s.startswith("####") and "Entry Conditions" in s:
            gate = "stage-entry"
            if cur_stage:
                has_entry[cur_stage] = True
            continue
        if s.startswith("####") and "Exit Conditions" in s:
            gate = "stage-exit"
            if cur_stage:
                has_exit[cur_stage] = True
            continue
        if s.startswith("**Entry Condition"):
            gate = "task-entry"; continue
        im = re.match(r"\*\*Interrupting:\*\*\s*(Yes|No)", s)
        if im:
            if cur_stage:
                interrupting[cur_stage] = im.group(1)
            gate = None; continue
        if s.startswith("#") or s == "---" or s.startswith("**"):
            gate = None; continue
        if not (gate and s.startswith("|")):
            continue
        cells = [c.strip() for c in s.strip().strip("|").split("|")]
        if not cells:
            continue
        # Header row: capture Marks-Complete / Exit-Type column positions by name
        # (robust to the trailing "Display Name" column the template adds).
        if cells[0] == "WHEN":
            hdr = [c.lower() for c in cells]
            marks_idx = next((i for i, h in enumerate(hdr) if h.startswith("marks")), None)
            et_idx = next((i for i, h in enumerate(hdr) if "exit type" in h), None)
            continue
        if cells[0] == "" or set(cells[0]) <= set("-: "):
            continue
        rule = _rule_token(cells[0])
        if rule is None:
            continue
        where = f"{cur_stage or 'case'}"
        if rule not in KNOWN_RULES:
            issues.append(f"rule: unknown/invalid rule type {rule!r} at {where} {gate}")
            continue
        if gate == "stage-entry" and rule not in STAGE_ENTRY:
            issues.append(f"rule: {rule!r} is not a legal stage-entry rule ({where})")
        elif gate == "task-entry" and rule not in TASK_ENTRY:
            issues.append(f"rule: {rule!r} is not a legal task-entry rule ({where})")
        elif gate in ("stage-exit", "case-exit"):
            # Resolve Marks-Complete by header index; fall back to last cell.
            marks_cell = cells[marks_idx] if (marks_idx is not None and marks_idx < len(cells)) else cells[-1]
            marks = marks_cell.lower()
            yes = marks.startswith("yes")
            legal = (STAGE_COMPLETION if gate == "stage-exit" else CASE_COMPLETION) if yes \
                else (STAGE_EXIT if gate == "stage-exit" else CASE_EXIT)
            kind = "completion (Marks=Yes)" if yes else "exit (Marks=No)"
            if rule not in legal:
                issues.append(f"rule: {rule!r} is not legal for {gate} {kind} ({where})")
            if gate == "stage-exit":
                # Resolve Exit-Type by header index; fall back to second-to-last.
                et = cells[et_idx] if (et_idx is not None and et_idx < len(cells)) \
                    else (cells[-2] if len(cells) >= 4 else None)
                if et is not None:
                    if cur_stage:
                        exit_types.setdefault(cur_stage, set()).add(et)
                    if et and et not in EXIT_TYPES:
                        issues.append(f"rule: invalid exit-type {et!r} at {where}")
                    if et == "return-to-origin":
                        pairing_issue = _return_to_origin_pairing_issue(rule, yes, where)
                        if pairing_issue:
                            issues.append(pairing_issue)

    missing = sorted(
        st for st in has_entry
        if not has_entry.get(st) or not has_exit.get(st)
    )
    if missing:
        issues.append(
            "conditions: stage(s) missing Entry and/or Exit conditions: "
            + ", ".join(missing)
        )

    # 6. interrupting semantics for exception/secondary stages
    for st, exc in is_exc.items():
        if not exc:
            continue
        if interrupting.get(st) is None:
            issues.append(f"interrupting: exception stage {st!r} has no **Interrupting:** flag")
        if "return-to-origin" in exit_types.get(st, set()) and interrupting.get(st) != "Yes":
            issues.append(
                f"interrupting: {st!r} exits 'return-to-origin' but is not Interrupting: Yes "
                "(a lane that returns to its origin must interrupt the stage it returns to)"
            )

    if "required-stages-completed" not in text:
        issues.append("conditions: no required-stages-completed case-completion row (case cannot close)")

    stage_sections = re.findall(r"^###\s+(?:Stage \d+|Exception Stage|Secondary Stage):", text, re.M)
    if len(stage_sections) < 3:
        issues.append(f"conditions: expected several stage sections; found {len(stage_sections)}")

    if issues:
        sys.exit("FAIL: sdd.md mechanical check\n  - " + "\n  - ".join(issues))

    print(
        f"OK: sdd.md mechanically sound — {len(declared)} variables, {len(refs)} =vars "
        f"references all resolve, lineage closes, task types valid, "
        f"{len(stage_sections)} stages with legal entry/exit conditions, case can close"
    )


if __name__ == "__main__":
    main()
