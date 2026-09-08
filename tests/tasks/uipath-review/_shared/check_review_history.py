#!/usr/bin/env python3
"""Verify Step 6 recorded the final grade in CLI-owned review-history.json.

The review skill's Step 6 (SKILL.md; detailed in
`references/agents/agent-grading-rubric.md`) has the reviewer run, per low-code
agent project after the report:

    uip agent review-history add <GRADE> "<PROJECT_DIR>" --errors <N> --warnings <N> --output json

which appends `{grade, runAt, errors, warnings}` to
`<PROJECT_DIR>/review-history.json`. This checker grades the OUTCOME (the file
the CLI wrote) rather than command telemetry, for the reasons documented in
`check_review_cli_provenance.py`: batched shell scripts make `command_executed`
criteria blind to both the call and its exit code.

The recorded grade must equal the report's `**Final grade: <A-F>**` footer --
Step 6 persists the Step 4.5 final grade, not some other letter.

Step 6's own failure contract ("state that the grade was not recorded and
stop") is spoken to the user after the report is saved, so it leaves no
artifact this checker can read. When review-history.json is missing, ground
truth comes from probing the CLI itself: a `uip` that does not know the
`agent review-history` verb makes recording impossible (WARN + PASS -- same
environment caveat as the provenance checker: agent and checker can resolve
different `uip` binaries), while a `uip` that does know it means Step 6 was
skipped (FAIL).

Exit 0 on PASS; sys.exit(str) on failure.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from report_evidence import cli_identity

FINAL_GRADE = re.compile(r"(?m)^\*\*Final grade: ([ABCDF])\*\*\Z")
GRADES = frozenset("ABCDF")


def _verb_available(uip: str) -> tuple[bool, str]:
    """Probe whether this `uip` knows `agent review-history`."""
    try:
        proc = subprocess.run(
            [uip, "agent", "review-history", "--help"],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        return False, f"{uip} not on PATH"
    except subprocess.SubprocessError as error:
        return False, f"probe failed: {error}"
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-200:]
        return False, f"exit {proc.returncode}: {tail}"
    return True, ""


def _int_field(entry: dict, key: str) -> int:
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        sys.exit(f"FAIL: review-history entry `{key}` must be a non-negative integer, got {value!r}")
    return value


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="ReviewSol/SampleAgent")
    ap.add_argument("--report", default="_review_report.md")
    args = ap.parse_args()

    report_path = Path(os.getcwd()) / args.report
    if not report_path.is_file():
        sys.exit(f"FAIL: {report_path} not found")
    report = report_path.read_text(encoding="utf-8", errors="replace")
    footer = FINAL_GRADE.search(report.rstrip())
    if not footer:
        sys.exit(
            "FAIL: report does not end with '**Final grade: <A-F>**' -- without it there "
            "is no ground truth for the grade Step 6 must record."
        )
    final_grade = footer.group(1)

    history_path = Path(os.getcwd()) / args.project / "review-history.json"
    if not history_path.is_file():
        uip = os.environ.get("UIP", "uip")
        print(f"Checker resolved `{uip}` -> {cli_identity(uip)}")
        available, why = _verb_available(uip)
        if available:
            sys.exit(
                f"FAIL: {history_path} does not exist, but `{uip} agent review-history` is "
                "available -- Step 6 (record the agent grade) was skipped."
            )
        print(
            f"WARN: {history_path} does not exist and `{uip} agent review-history` is "
            f"unavailable ({why}) -- recording was impossible in this environment, so Step 6 "
            "cannot be graded. If the agent resolved a different `uip`, compare `which -a uip`."
        )
        print("PASS")
        return

    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"FAIL: {history_path} is not valid JSON: {error}")
    if not isinstance(history, list) or not history:
        sys.exit(f"FAIL: {history_path} must be a non-empty JSON array of review entries")
    entry = history[-1]
    if not isinstance(entry, dict):
        sys.exit(f"FAIL: last review-history entry must be a JSON object, got {entry!r}")

    grade = entry.get("grade")
    if grade not in GRADES:
        sys.exit(f"FAIL: last review-history entry has invalid grade {grade!r}")
    if grade != final_grade:
        sys.exit(
            f"FAIL: recorded grade {grade} does not match the report's final grade "
            f"{final_grade} -- Step 6 must persist the Step 4.5 final grade."
        )
    errors = _int_field(entry, "errors")
    warnings = _int_field(entry, "warnings")
    run_at = entry.get("runAt")
    if not isinstance(run_at, str) or not run_at.strip():
        sys.exit(f"FAIL: last review-history entry has no `runAt` timestamp, got {run_at!r}")

    print(
        f"OK: {history_path} records grade {grade} (errors={errors}, warnings={warnings}, "
        f"runAt={run_at}), matching the report's final grade."
    )
    print("PASS")


if __name__ == "__main__":
    main()
