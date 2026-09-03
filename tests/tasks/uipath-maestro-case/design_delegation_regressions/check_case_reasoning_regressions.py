#!/usr/bin/env python3
"""Check the design-only SDD for case-reasoning regressions."""

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

    SDD detail cards write `**Key:** value` lines and WHEN/IF condition tables;
    the leading bullet is optional so both shapes read the same.
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

    SIBLINGS = ("Wait for Payment Confirmation", "Payment Deadline")

    # sdd.md is the design AND the build plan — Phase 2 writes caseplan.json from
    # it directly — so every activation-mode decision is graded here.
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

    generate_permit = sdd_task_block(sdd, "Generate Permit")
    if any(
        "payment deadline" in operand.lower()
        for operand in selected_task_operands(generate_permit)
    ):
        fail("Generate Permit depends on the payment deadline branch")
    if "confirm" not in authored_rule_text(generate_permit).lower():
        fail("Generate Permit is not gated by successful payment confirmation")

    internal_notes = sdd_task_block(sdd, "Internal Notes")
    if "selected-tasks-completed" in authored_rule_text(internal_notes).lower():
        fail("Internal Notes adhoc task is gated on a selected-task dependency")
    for operand in selected_task_operands(sdd):
        if "internal notes" in operand.lower():
            fail("selected-tasks-completed references the adhoc Internal Notes task")

    # Scope to authored rules: the SDD's Design Rationale is *required* to explain
    # why a deterministic route avoids `user-selected-stage`, and naming the
    # anti-pattern in that explanation must not read as using it.
    sdd_rules = authored_rule_text(sdd).lower()
    if "user-selected-stage" in sdd_rules and "wait-for-user" not in sdd_rules:
        fail("user-selected-stage appears without an upstream wait-for-user exit")
    rejected = authored_rule_text(sdd_task_block(sdd, "Application Rejected"))
    if "user-selected-stage" in rejected.lower():
        fail("Application Rejected uses user-selected-stage for deterministic rejection")

    print("OK: case reasoning regression invariants are represented")


if __name__ == "__main__":
    main()
