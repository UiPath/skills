"""Helpers the draft-mode graders share: find the plan, read it, tell blank boxes from built tasks."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_check import find_caseplan, find_stages, find_triggers  # noqa: E402

KIND_SUFFIX = re.compile(r"\s\[[^\[\]]+\](?=\s*(?:→|->|$))")
BOX_LABEL = re.compile(r"\S(?:.*?\S)? \[[A-Z][^\[\]]*\](?:\s*(?:→|->)\s*\S.*)?")


def fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def load_plan() -> tuple[str, dict]:
    path = find_caseplan()
    with open(path, encoding="utf-8") as fh:
        return path, json.load(fh)


def stages(doc: dict) -> list[dict]:
    return find_stages(doc, include_exception=True)


def stage_label(stage: dict) -> str:
    return (stage.get("data") or {}).get("label") or ""


def tasks(doc: dict) -> list[tuple[str, dict]]:
    """Every task with its stage's label, stage by stage in plan order."""
    found = []
    for stage in stages(doc):
        for lane in (stage.get("data") or {}).get("tasks") or []:
            for task in lane if isinstance(lane, list) else [lane]:
                if isinstance(task, dict):
                    found.append((stage_label(stage), task))
    return found


def is_blank(task: dict) -> bool:
    """A skeleton box: `unresolved('<kind>')` compiles to an empty `data` block."""
    return not task.get("data")


def label_of(task: dict) -> str:
    return task.get("displayName") or ""


def trigger_kinds(doc: dict) -> list[str]:
    """`manual`, `timer` or the trigger's own service type, one per trigger."""
    kinds = []
    for node in find_triggers(doc):
        service = str(((node.get("data") or {}).get("inputs") or {}).get("serviceType") or "None")
        kinds.append("manual" if service == "None" else service.lower())
    return kinds


def validate(path: str) -> int:
    """`uip maestro case validate --strict` must report Valid; a skeleton's warnings are expected."""
    try:
        run = subprocess.run(
            ["uip", "maestro", "case", "validate", path, "--strict", "--output", "json"],
            capture_output=True, text=True, timeout=150,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return fail(f"uip maestro case validate did not run: {err}")
    start = run.stdout.find("{")
    try:
        status = (json.loads(run.stdout[start:]).get("Data") or {}).get("Status") if start >= 0 else None
    except json.JSONDecodeError:
        status = None
    if run.returncode != 0 or status != "Valid":
        return fail(f"validate --strict exit {run.returncode}, status {status!r}\n{run.stdout[-2000:]}\n{run.stderr[-1000:]}")
    print(f"OK: {path} validates (strict)")
    return 0
