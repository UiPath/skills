#!/usr/bin/env python3
"""Mechanical check on a Phase-0 ``sdd.md`` (markdown only).

Phase 0 stops at the approved ``sdd.md`` — no caseplan exists yet — so these
checks parse the markdown directly to confirm the SDD is sound enough to
*deliver downstream* (Phase 1 trusts it verbatim). Domain sense is graded
separately by the ``llm_judge`` criterion; this script is the deterministic
"rules and mappings" half.

Checks (domain-agnostic):
  1. Mapping integrity — every ``=vars.<name>`` resolves to a §Case Variables row.
  2. Lineage closure  — every consumed variable is produced before use (In /
     Default / sourceTriggers / task Output ``-> name`` / button ``name = ...``).
  3. Task-type enum   — every task ``Type`` is one of the 9 legal types.
  4. Per-gate rule legality — each Entry / Completion / Exit / Case-exit rule is
     legal **for its gate**, with the correct Marks-Complete pairing.
  5. Conditions present — each stage section has Entry + Exit conditions, and the
     case can close (a ``required-stages-completed`` case-completion row exists).
  6. Interrupting semantics — every exception (secondary) stage declares an
     Interrupting flag, and any lane that returns to its origin
     (``return-to-origin`` exit) is marked ``Interrupting: Yes`` (you can only
     return to a stage you interrupted).

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
               "wait-for-connector", "user-selected-stage"}
STAGE_COMPLETION = {"required-tasks-completed", "wait-for-connector"}   # Marks: Yes
STAGE_EXIT = {"selected-tasks-completed", "wait-for-connector"}          # Marks: No
TASK_ENTRY = {"current-stage-entered", "selected-tasks-completed",
              "wait-for-connector", "adhoc", "runs-sequentially"}
CASE_COMPLETION = {"required-stages-completed", "wait-for-connector"}    # Marks: Yes
CASE_EXIT = {"selected-stage-completed", "selected-stage-exited",
             "wait-for-connector"}                                       # Marks: No
EXIT_TYPES = {"exit-only", "wait-for-user", "return-to-origin"}
KNOWN_RULES = STAGE_ENTRY | STAGE_COMPLETION | STAGE_EXIT | TASK_ENTRY | CASE_COMPLETION | CASE_EXIT


def _find_sdd() -> str:
    matches = sorted(p for p in glob.glob("**/sdd.md", recursive=True) if "/.venv/" not in p)
    if not matches:
        sys.exit("FAIL: no sdd.md found under the current directory")
    return matches[0]


def _rule_token(cell: str) -> str | None:
    """Leading rule keyword from a WHEN cell (``case-entered``, ``adhoc``, …)."""
    m = re.match(r"`?\s*([a-z][a-z]+(?:-[a-z]+)*)", cell.strip())
    return m.group(1) if m else None


def main() -> None:
    path = _find_sdd()
    text = open(path, encoding="utf-8").read()
    issues: list[str] = []

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

    refs = set(re.findall(r"=vars\.([A-Za-z]\w*)", text))

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
    bad_types = sorted(
        {t for t in re.findall(r"^\*\*Type:\*\*\s*(\S+)", text, re.M)
         if t not in ("Stage", "ExceptionStage") and t not in TASK_TYPES}
    )
    if bad_types:
        issues.append(f"task-type: invalid type(s): {', '.join(bad_types)}")

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
        m = re.match(r"###\s+(Stage \d+|Exception Stage):\s*(.+)", s)
        if m:
            cur_stage = re.sub(r"\(.*", "", m.group(2)).strip()
            has_entry.setdefault(cur_stage, False)
            has_exit.setdefault(cur_stage, False)
            is_exc[cur_stage] = m.group(1) == "Exception Stage"
            exit_types.setdefault(cur_stage, set())
            gate = None
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

    stage_sections = re.findall(r"^###\s+(?:Stage \d+|Exception Stage):", text, re.M)
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
