#!/usr/bin/env python3
"""Check Phase 0 no-build output for case-reasoning regressions."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def read_required(path: Path) -> str:
    if not path.is_file():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def sections_for(text: str, name: str) -> list[str]:
    pattern = rf"(?ims)^##\s+T\d+[^\n]*{re.escape(name)}[^\n]*\n.*?(?=^##\s+T\d+|\Z)"
    return [m.group(0) for m in re.finditer(pattern, text)]


def require_section(text: str, name: str) -> str:
    sections = sections_for(text, name)
    if not sections:
        fail(f"missing tasks.md section for {name!r}")
    return "\n".join(sections)


def has_near(text: str, left: str, right: str, distance: int = 500) -> bool:
    return re.search(
        rf"{re.escape(left)}.{{0,{distance}}}{re.escape(right)}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ) is not None


def lane(section: str, name: str) -> int:
    match = re.search(r"(?im)^-\s*lane:\s*(\d+)\b", section)
    if not match:
        fail(f"missing lane/task-set index for {name!r}")
    return int(match.group(1))


def assert_no_bare_sla_status_change(plan: str) -> None:
    for match in re.finditer(r"(?ims)^##\s+T\d+[^\n]*\n.*?(?=^##\s+T\d+|\Z)", plan):
        section = match.group(0)
        if "sla-status-change" not in section:
            continue
        lower = section.lower()
        missing = [
            key
            for key in ("sla-target", "sla-display-name", "escalation-display-name")
            if key not in lower
        ]
        if missing:
            fail(f"bare sla-status-change missing {missing}: {section[:180]!r}")


def main() -> None:
    sdd = read_required(Path("sdd.md"))
    plan = read_required(Path("tasks/tasks.md"))
    combined = f"{sdd}\n{plan}"
    lower = combined.lower()

    if "sla response map" not in lower:
        fail("missing SLA Response Map")
    if "task-set map" not in lower and "task set map" not in lower:
        fail("missing Task-Set Map")
    if "rule firing map" not in lower:
        fail("missing Rule Firing Map")
    if "re-entry loop map" not in lower and "reentry loop map" not in lower:
        fail("missing Re-entry Loop Map")

    stage_sla_lines = [
        line
        for line in sdd.splitlines()
        if "issuing permit sla" in line.lower() and "breach" in line.lower()
    ]
    if not stage_sla_lines:
        fail("missing breached Issuing Permit SLA response row")
    if not any(
        " no " in f" {line.lower()} "
        or "non-interrupt" in line.lower()
        or "notify" in line.lower()
        for line in stage_sla_lines
    ):
        fail("Issuing Permit SLA breach is not explicitly non-interrupting/notify-only")

    bad_stage_interrupt = re.search(
        r"(?is)issuing the permit.{0,900}sla-status-change.{0,500}issuing permit sla.{0,300}interrupting.{0,80}yes",
        combined,
    )
    if bad_stage_interrupt:
        fail("stage SLA is modeled as an interrupting same-stage entry")

    payment_wait = require_section(plan, "Wait for Payment Confirmation")
    payment_deadline = require_section(plan, "Payment Deadline")
    if lane(payment_wait, "Wait for Payment Confirmation") != lane(
        payment_deadline, "Payment Deadline"
    ):
        fail("payment confirmation and deadline are not in the same parallel task set")
    for name, section in (
        ("Wait for Payment Confirmation", payment_wait),
        ("Payment Deadline", payment_deadline),
    ):
        if "parallel-after-predecessor" not in section.lower():
            fail(f"{name!r} is not marked parallel-after-predecessor")
        if "runs-sequentially" not in section.lower():
            fail(f"{name!r} does not use runs-sequentially for prior-set completion")
        if "selected-tasks-completed" in section.lower() and "collect fees" in section.lower():
            fail(f"{name!r} duplicates the Collect Fees selected-task gate")

    generate_permit = require_section(plan, "Generate Permit")
    if "payment deadline" in generate_permit.lower():
        fail("Generate Permit depends on the payment deadline branch")
    if not has_near(generate_permit, "Payment Confirmation", "condition", 1200) and not has_near(
        generate_permit, "payment", "confirmed", 1200
    ):
        fail("Generate Permit is not gated by successful payment confirmation")

    internal_notes = "\n".join(sections_for(plan, "Internal Notes"))
    if internal_notes and "selected-tasks-completed" in internal_notes.lower():
        fail("Internal Notes adhoc task is used as a selected-task dependency")
    if has_near(combined, "selected-tasks-completed", "Internal Notes", 500):
        fail("selected-tasks-completed references the adhoc Internal Notes task")

    if "user-selected-stage" in lower and "wait-for-user" not in lower:
        fail("user-selected-stage appears without an upstream wait-for-user exit")
    if has_near(combined, "Application Rejected", "user-selected-stage", 800):
        fail("Application Rejected uses user-selected-stage for deterministic rejection")

    assert_no_bare_sla_status_change(plan)

    buyer_request = require_section(plan, "Send Buyer Review Request")
    buyer_decision = require_section(plan, "Buyer Decision")
    for name, section in (
        ("Send Buyer Review Request", buyer_request),
        ("Buyer Decision", buyer_decision),
    ):
        if not re.search(r"(?im)^-\s*runOnlyOnce:\s*false\b", section):
            fail(f"{name!r} must rerun after SendBack correction")
    if "buyerdecision" not in re.sub(r"[^a-z0-9]", "", combined.lower()):
        fail("buyerDecision state is missing")
    if not re.search(r"(?is)buyer\s*decision|buyerdecision", combined):
        fail("Buyer Decision routing fact is missing")
    normalized_window = re.sub(r"[^a-z0-9]+", " ", combined.lower())
    if not (
        re.search(r"(?is)buyer\s*decision.{0,800}(pending|reset|attempt)", combined)
        or re.search(r"(?is)(pending|reset|attempt).{0,800}buyer\s*decision", combined)
        or re.search(r"\bbuyerdecision\b.{0,800}\b(pending|reset|attempt)\b", normalized_window)
        or re.search(r"\b(pending|reset|attempt)\b.{0,800}\bbuyerdecision\b", normalized_window)
    ):
        fail("buyerDecision is not reset or attempt-scoped for re-entry")

    unsafe_names = [
        "Issuing the Permit: Payment.",
        "Case.Reasoning",
        "Buyer Review:",
    ]
    for unsafe in unsafe_names:
        if unsafe in combined:
            fail(f"unsafe display name was preserved verbatim: {unsafe!r}")

    print("OK: case reasoning regression invariants are represented")


if __name__ == "__main__":
    main()
