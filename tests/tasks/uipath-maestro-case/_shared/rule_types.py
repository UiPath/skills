#!/usr/bin/env python3
"""The case condition rule types per slot, as the CLI declares them (MST-16782).

`uip maestro case rule-types list --output json` is the declaration: for each
condition slot (`Scope`), the rule types it can hold, whether it marks the
stage or case complete, and whether `case validate` checks it. `rule_types.json`
beside this file is a snapshot of that command's `Data`;
scripts/refresh-cli-declarations.py refreshes it nightly.

The declaration says what a slot CAN hold. The skills may author a subset: the
planner deliberately keeps `selected-*` off completion slots. So the copies are
held to it one way (`test_rule_types.py`): never a rule the slot cannot hold.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "rule_types.json"
GUIDE = HERE.parents[3] / "skills" / "uipath-planner" / "references" / "case" / "case-design-layers-guide.md"

# The layers guide's § Lifecycle gates row label for each declared scope.
GUIDE_ROWS = {
    "Task entry": "task-entry",
    "Stage entry": "stage-entry",
    "Stage exit": "stage-exit",
    "Stage completion": "stage-completion",
    "Case exit": "case-exit",
    "Case completion": "case-completion",
}
COMMAND = ["uip", "maestro", "case", "rule-types", "list", "--output", "json"]


def load() -> dict:
    return json.loads(SNAPSHOT.read_text())["Data"]


def scopes(data: dict) -> dict:
    """The whole declaration, one list per slot so a drift report names the rule that moved.

    Every field constrains a copy and none is volatile, so the flags ride along
    as entries: `MarksComplete=true`, `Validated=false`.
    """
    out = {}
    for s in data["Scopes"]:
        flags = [f"{key}={str(s[key]).lower()}" for key in ("MarksComplete", "Validated") if key in s]
        out[s["Scope"]] = sorted(r["Type"] for r in s["RuleTypes"]) + flags
    out["Unscoped"] = sorted(r["Type"] for r in data["Unscoped"])
    return out


def by_scope(data: dict | None = None) -> dict[str, set[str]]:
    return {s["Scope"]: {r["Type"] for r in s["RuleTypes"]} for s in (data or load())["Scopes"]}


def marks_complete(data: dict | None = None) -> dict[str, bool | None]:
    return {s["Scope"]: s.get("MarksComplete") for s in (data or load())["Scopes"]}


def from_cli() -> dict | None:
    """The command's `Data`, or None when the installed CLI has no such command."""
    try:
        result = subprocess.run(COMMAND, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    start = result.stdout.find("{")
    if result.returncode != 0 or start < 0:
        return None
    try:
        payload = json.loads(result.stdout[start:])
    except json.JSONDecodeError:
        return None
    if payload.get("Code") != "RuleTypeList":
        return None
    return payload["Data"]


def lifecycle_rows() -> dict[str, tuple[str, set[str]]]:
    """§ Lifecycle gates as {row label: (Marks complete cell, legal WHEN rules)}."""
    text = GUIDE.read_text()
    start = text.find("### Lifecycle gates")
    assert start >= 0, "the layers guide has no '### Lifecycle gates' heading"
    end = text.find("\n### ", start + 1)
    section = text[start:] if end < 0 else text[start:end]
    rows = {}
    for gate, marks, rules in re.findall(r"^\| ([A-Z][a-z]+ [a-z]+) \| (\S+) \| (.+) \|$", section, re.M):
        rows[gate] = (marks, set(re.findall(r"`([a-z-]+)`", rules)))
    return rows


def unused(data: dict | None = None) -> list[str]:
    """One line per rule a slot can hold that the guide does not allow: a drift-PR note, never a failure.

    One line per (slot, rule), so the refresh can report only the pairs that are new.
    """
    rows = lifecycle_rows()
    declared = by_scope(data)
    return [
        f"- `{scope}` can also hold `{rule}`; § Lifecycle gates '{gate}' does not allow it"
        for gate, scope in GUIDE_ROWS.items()
        for rule in sorted(declared.get(scope, set()) - rows[gate][1])
    ]
