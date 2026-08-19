#!/usr/bin/env python3
"""Grade Step 12.2 / Check 16 — a build carrying unresolved work must ship an issue log.

Regression guarded
------------------
The skill holds its issue list in the agent's reasoning for the whole build
(`plugins/logging/impl-json.md` § Setup) and dumps it exactly once at Step 12.1.
On a long build that in-memory list is the first casualty of context pressure,
and nothing downstream notices: Step 12 Checks 1-14 inspect `caseplan.json` and
its sidecars, never the log, and the Reporting clause *presumes* the file exists.

Observed 2026-08-13: a 52-minute build produced 8 stages, 39 tasks -- every one
of them a placeholder -- and 120 `<UNRESOLVED>` markers in tasks.md, emitted NO
`build-issues.md` at all, and still scored 1.0. The operator was handed 39
unwired resources with no record of which ones.

Predicate
---------
The build carries unresolved work when ANY of:
  1. tasks.md contains `<UNRESOLVED`
  2. any task in caseplan.json is a placeholder (`data: {}`)
  3. any wait-for-connector rule still carries the placeholder stub

If it does, tasks/build-issues.md must exist AND carry >= 1 issue entry.
A header-only or empty file fails: "I wrote a file" is not "I recorded the work".

Exit 0 = pass, 1 = fail. Run from the sandbox root.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_PARTS = {".venv", "node_modules", ".npm-prefix", "dist"}


def _iter(root: Path, name: str):
    for p in root.rglob(name):
        if SKIP_PARTS.isdisjoint(p.parts):
            yield p


def find_one(root: Path, name: str) -> Path | None:
    return next(_iter(root, name), None)


def walk_rules(case: dict):
    """Every rule across all four condition scopes."""
    for cond in (case.get("metadata") or {}).get("caseExitRules") or []:
        for grp in cond.get("rules") or []:
            yield from grp
    for node in case.get("nodes") or []:
        if node.get("type") != "case-management:Stage":
            continue
        data = node.get("data") or {}
        for key in ("entryConditions", "exitConditions"):
            for cond in data.get(key) or []:
                for grp in cond.get("rules") or []:
                    yield from grp
        for lane in data.get("tasks") or []:
            for task in lane:
                for cond in task.get("entryConditions") or []:
                    for grp in cond.get("rules") or []:
                        yield from grp


def placeholder_tasks(case: dict) -> list[str]:
    out = []
    for node in case.get("nodes") or []:
        if node.get("type") != "case-management:Stage":
            continue
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                if not (task.get("data") or {}):
                    out.append(task.get("displayName") or task.get("id") or "<unnamed>")
    return out


def stub_rules(case: dict) -> int:
    n = 0
    for rule in walk_rules(case):
        if rule.get("rule") != "wait-for-connector":
            continue
        ctx = (rule.get("uipath") or {}).get("context") or []
        vals = {e.get("name"): e.get("value") for e in ctx if isinstance(e, dict)}
        if vals.get("connectorKey") == "placeholder" or vals.get("operation") == "placeholder":
            n += 1
    return n


def has_issue_entries(text: str) -> bool:
    """A real entry, not just scaffolding.

    Accepts either the logging plugin's table rows or a bulleted/`##`-sectioned
    log. Rejects headers, the reconstruction NOTE, separators, and blank lines --
    an empty template must not pass as a record.
    """
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith(("NOTE:", "BLOCKED:")):
            continue
        if set(line) <= set("|-: "):        # markdown table separator
            continue
        # logging-plugin template scaffolding, e.g.
        #   **Case file:** caseplan.json | **Timestamp:** <ISO>
        if re.match(r"^\*\*(case file|timestamp)\s*:", line, re.IGNORECASE):
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or all(not c for c in cells):
                continue
            header_like = {"category", "severity", "step", "plugin", "message",
                           "errors", "warnings", "skipped", "issue", "detail"}
            if all(c.lower() in header_like for c in cells if c):
                continue
            return True
        if line.startswith(("- ", "* ", "1.")):
            return True
        return True
    return False


def main() -> int:
    root = Path.cwd()

    tasks_md = find_one(root, "tasks.md")
    unresolved = 0
    if tasks_md is not None:
        try:
            unresolved = len(re.findall(r"<UNRESOLVED", tasks_md.read_text()))
        except OSError:
            pass

    caseplan = find_one(root, "caseplan.json")
    placeholders: list[str] = []
    stubs = 0
    if caseplan is not None:
        try:
            case = json.loads(caseplan.read_text())
            placeholders = placeholder_tasks(case)
            stubs = stub_rules(case)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL: caseplan.json unreadable/unparseable: {exc}")
            return 1

    carries_unresolved = bool(unresolved or placeholders or stubs)

    print(f"unresolved markers in tasks.md : {unresolved}")
    print(f"placeholder tasks (data: {{}})   : {len(placeholders)}")
    print(f"surviving connector stubs      : {stubs}")

    issues = find_one(root, "build-issues.md")
    text = ""
    if issues is not None:
        try:
            text = issues.read_text()
        except OSError:
            text = ""

    if not carries_unresolved:
        print("\nPASS: build carries no unresolved work — issue log is optional.")
        return 0

    if issues is None:
        preview = ", ".join(placeholders[:5]) + ("…" if len(placeholders) > 5 else "")
        print(
            "\nFAIL: the build carries unresolved work but shipped NO tasks/build-issues.md.\n"
            f"  {len(placeholders)} placeholder task(s){': ' + preview if preview else ''}\n"
            f"  {unresolved} <UNRESOLVED> marker(s) in tasks.md\n"
            "  The operator receives unwired resources with no record of which ones.\n"
            "  Step 12.1 reconstructs the log from artifacts when the flush was skipped.\n"
            "  See implementation.md § Step 12.2 (Check 16)."
        )
        return 1

    if not has_issue_entries(text):
        print(
            f"\nFAIL: {issues.relative_to(root)} exists but carries no issue entries.\n"
            "  A header-only or empty log is not a record — Step 12.2 requires at least one entry\n"
            "  when the build carries unresolved work."
        )
        return 1

    # One marker, stamped by Step 12.1 § Recovery. The 12.2 form is accepted for
    # logs written before the recovery step was consolidated there.
    reconstructed = "reconstructed at Step 12.1" in text or "reconstructed at Step 12.2" in text
    note = "  (reconstructed log — severity/step attribution approximate)" if reconstructed else ""
    print(f"\nPASS: unresolved work is recorded in {issues.relative_to(root)}.{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
