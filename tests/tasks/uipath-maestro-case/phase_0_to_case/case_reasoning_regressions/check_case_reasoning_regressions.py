#!/usr/bin/env python3
"""Check Phase 0 no-build output for case-reasoning regressions."""

from __future__ import annotations

import re
import sys
from pathlib import Path



def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


# Field keys whose values are reviewer prose, not authored rules. A plan that
# explains "no duplicate selected-tasks-completed(...) gate" is complying, not
# violating, so rule scans must never read these.
PROSE_KEYS = {"rationale", "decision", "note", "notes", "risk", "why", "description"}

# Field keys that carry an authored rule or its operands.
RULE_KEYS = {"entry-rule", "exit-rule", "rule-type", "rule", "when", "selected-tasks-ids"}

# Rule keys plus the guard expressions that gate them.
GATE_KEYS = RULE_KEYS | {"if", "condition", "condition-expression", "conditionexpression"}


def authored_rule_text(text: str) -> str:
    """Concatenated authored rule and guard values, excluding rationale prose.

    The compact no-build `tasks.md` shape writes plain `key: value` lines; the
    full-build T-entry contract writes `- key: value`. The leading bullet is
    therefore optional — requiring it made every rule scan read an empty string
    against compact output, so the gate assertions passed vacuously.
    """
    parts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        field = re.match(r"(?i)^[-*]?\s*([a-z][a-z0-9 _-]*):\s*(.*)$", stripped)
        if field:
            if field.group(1).strip().lower() in GATE_KEYS:
                parts.append(field.group(2))
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            parts += cells[:2]
    return "\n".join(parts)


def selected_task_operands(text: str) -> list[str]:
    """Operands of authored selected-tasks gates only.

    Reads structured `- <rule-key>: ...` field values and the WHEN (first) cell of
    markdown table rows, never rationale/description prose.
    """
    sources: list[str] = []
    operands: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        field = re.match(r"(?i)^[-*]?\s*([a-z][a-z0-9 _-]*):\s*(.*)$", stripped)
        if field:
            key = field.group(1).strip().lower()
            if key == "selected-tasks-ids":
                # Split field form: the value IS the operand list.
                operands.append(field.group(2))
            elif key in RULE_KEYS:
                sources.append(field.group(2))
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells:
                sources.append(cells[0])
    for source in sources:
        operands += re.findall(
            r"(?i)selected-tasks-(?:completed\s*\(|ids:)?\s*([^\n)]*)", source
        )
    return operands


def read_required(path: Path) -> str:
    if not path.is_file():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def sections_for(text: str, name: str) -> list[str]:
    # Terminate at the NEXT H2 of any kind, not just the next `## T<n>`. Plans group
    # entries under non-T headings such as `## Stage: Buyer Review`; stopping only at
    # `## T<n>` lets one entry swallow a whole stage block and its rules.
    pattern = rf"(?ims)^##\s+T\d+[^\n]*{re.escape(name)}[^\n]*\n.*?(?=^##\s|\Z)"
    return [m.group(0) for m in re.finditer(pattern, text)]


def require_section(text: str, name: str) -> str:
    sections = sections_for(text, name)
    if not sections:
        fail(f"missing tasks.md section for {name!r}")
    return "\n".join(sections)


def lane(section: str) -> str | None:
    """The task's declared task-set index, or None when the plan omits it.

    Compared as an opaque token, not parsed as an int. A non-numeric lane is a
    convention lapse the advisory format check reports; what *this* check grades
    is whether siblings land in the SAME set, which reads the same either way.
    """
    match = re.search(r"(?im)^[-*]?\s*lane:\s*(.+?)\s*$", section)
    return match.group(1).strip().lower() if match else None


def sdd_task_block(sdd: str, name: str) -> str:
    """The SDD's detail card for a task, else its summary-table row(s).

    Activation Mode appears in either place depending on how the SDD renders —
    `**Activation Mode:** x` in the per-task card, or a column in the stage's
    task table. Read both; requiring one shape grades formatting, not design.
    """
    card = re.search(
        rf"(?ims)^#{{3,6}}\s*Task\s[\d.]*:?\s*[^\n]*{re.escape(name)}[^\n]*\n.*?(?=^#{{1,6}}\s|\Z)",
        sdd,
    )
    if card:
        return card.group(0)
    rows = [ln for ln in sdd.splitlines() if ln.lstrip().startswith("|") and name.lower() in ln.lower()]
    return "\n".join(rows)


def main() -> None:
    sdd = read_required(Path("sdd.md"))
    plan = read_required(Path("tasks/tasks.md"))
    combined = f"{sdd}\n{plan}"
    lower = combined.lower()

    SIBLINGS = ("Wait for Payment Confirmation", "Payment Deadline")

    # --- Design (sdd.md) -----------------------------------------------------
    # sdd.md is what Phase 0 produces and what Phase 1 reads as written, so the
    # activation-mode decision is graded there. The compact tasks.md shape has
    # proven unstable across agents/runs; grading design against it measures
    # plan formatting instead of case reasoning.
    for name in SIBLINGS:
        block = sdd_task_block(sdd, name)
        if not block:
            fail(f"sdd.md has no task entry for {name!r}")
        if not re.search(r"(?i)parallel-after-predecessor|race\s*branch", block):
            fail(
                f"sdd.md does not mark {name!r} parallel-after-predecessor or race "
                f"branch; both payment branches start together after Collect Fees"
            )
        if any("collect fees" in op.lower() for op in selected_task_operands(block)):
            fail(
                f"sdd.md gates {name!r} on selected-tasks-completed(\"Collect Fees\") "
                f"— siblings after one predecessor share a task set instead"
            )

    # --- Plan consistency (tasks.md), only where the plan expresses it -------
    # A plan that omits T-entries entirely is a format lapse, reported by the
    # advisory check rather than gated here; the design assertions above still
    # gate, so a narrative plan cannot skip grading.
    sections = {n: "\n".join(sections_for(plan, n)) for n in SIBLINGS}
    if all(sections.values()):
        lanes = {n: lane(s) for n, s in sections.items()}
        if all(lanes.values()) and len(set(lanes.values())) != 1:
            fail(
                f"payment confirmation and deadline are not in the same parallel task "
                f"set: lanes {lanes[SIBLINGS[0]]!r} vs {lanes[SIBLINGS[1]]!r}"
            )
        for name, section in sections.items():
            if "runs-sequentially" not in section.lower():
                fail(f"{name!r} does not use runs-sequentially for prior-set completion")
            if any("collect fees" in op.lower() for op in selected_task_operands(section)):
                fail(f"{name!r} duplicates the Collect Fees selected-task gate")

    generate_permit = "\n".join(sections_for(plan, "Generate Permit")) or sdd_task_block(
        sdd, "Generate Permit"
    )
    if any(
        "payment deadline" in operand.lower()
        for operand in selected_task_operands(generate_permit)
    ):
        fail("Generate Permit depends on the payment deadline branch")
    if "confirm" not in authored_rule_text(generate_permit).lower():
        fail("Generate Permit is not gated by successful payment confirmation")

    internal_notes = "\n".join(sections_for(plan, "Internal Notes")) or sdd_task_block(
        sdd, "Internal Notes"
    )
    if "selected-tasks-completed" in authored_rule_text(internal_notes).lower():
        fail("Internal Notes adhoc task is gated on a selected-task dependency")
    for operand in selected_task_operands(combined):
        if "internal notes" in operand.lower():
            fail("selected-tasks-completed references the adhoc Internal Notes task")

    # Scope to authored rules: the SDD's Design Rationale is *required* to explain
    # why a deterministic route avoids `user-selected-stage`, and naming the
    # anti-pattern in that explanation must not read as using it.
    combined_rules = authored_rule_text(combined).lower()
    if "user-selected-stage" in combined_rules and "wait-for-user" not in combined_rules:
        fail("user-selected-stage appears without an upstream wait-for-user exit")
    rejected = authored_rule_text(
        "\n".join(sections_for(plan, "Application Rejected"))
        or sdd_task_block(sdd, "Application Rejected")
    )
    if "user-selected-stage" in rejected.lower():
        fail("Application Rejected uses user-selected-stage for deterministic rejection")

    print("OK: case reasoning regression invariants are represented")


if __name__ == "__main__":
    main()
