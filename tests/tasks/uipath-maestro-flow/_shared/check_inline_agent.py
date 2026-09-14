#!/usr/bin/env python3
"""Smoke check: a scaffolded inline (uipath.agent.autonomous) agent was raised
to a production bar, not left on the toy scaffold defaults.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/check_inline_agent.py [--check <scope>] [<glob>]

  <glob>  Shell-style glob for the inline agent.json. The inline agent dir is a
          UUID, so the path is not statically knowable — pass e.g.
          "EmailTriage/EmailTriage/*/agent.json". Defaults to
          "**/agent.json" if omitted.
  <scope> One of ``exists``, ``model``, or ``quality`` (the default).

Asserts, on the first matching agent.json (excluding generated .agent-builder/):
  1. settings.model is set and is NOT the stale scaffold default gpt-4o-2024-11-20.
  2. The system message is a real prompt — not empty, not a known placeholder,
     and at least 40 chars.
  3. outputSchema declares at least one typed field beyond a bare `content` string.

Exit 0 on pass; exit 1 with a "FAIL: ..." line naming every failing property.
Reads only the source agent.json — no tenant calls, no agent self-reports.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

SCAFFOLD_MODEL = "gpt-4o-2024-11-20"

# Lowercased, stripped placeholder prompts shipped by scaffolds / docs examples.
PLACEHOLDER_PROMPTS = {
    "",
    "you are an agentic assistant.",
    "you are an assistant.",
    "triage the inbound email.",
    "you are a classifier.",
    "what is the current date?",
}
MIN_PROMPT_LEN = 40
EXCLUDED_PARTS = {
    ".agent-builder",
    ".cli-stage",
    ".v1stage",
    "_lib",
    "_outputs",
    "example",
    "fixtures",
    "node_modules",
    "reference_agents",
    "references",
    "v1stage",
}


def _parse_args() -> tuple[str, str]:
    args = sys.argv[1:]
    scope = "quality"
    if args[:1] == ["--check"]:
        if len(args) < 2 or args[1] not in {"exists", "model", "quality"}:
            print("FAIL: --check must be one of exists, model, or quality")
            raise SystemExit(1)
        scope = args[1]
        args = args[2:]
    if len(args) > 1:
        print("FAIL: expected at most one agent.json glob")
        raise SystemExit(1)
    return scope, args[0] if args else "**/agent.json"


def main() -> int:
    scope, pattern = _parse_args()
    paths = [
        path
        for path in glob.glob(pattern, recursive=True)
        if not EXCLUDED_PARTS.intersection(Path(path).parts)
    ]
    if not paths:
        print(f"FAIL: no inline agent.json matched {pattern!r}")
        return 1

    path = min(paths)
    if scope == "exists":
        print(f"OK ({path}): inline agent sidecar exists")
        return 0

    try:
        with open(path) as source:
            agent = json.load(source)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: could not read {path}: {e}")
        return 1

    errs = []

    model = (agent.get("settings") or {}).get("model", "")
    if not model:
        errs.append("settings.model is empty")
    elif model == SCAFFOLD_MODEL:
        errs.append(f"settings.model not overridden ({model})")

    if scope == "model":
        if errs:
            print(f"FAIL ({path}): " + "; ".join(errs))
            return 1
        print(f"OK ({path}): model={model}")
        return 0

    sys_msgs = [m.get("content", "") for m in agent.get("messages", []) if m.get("role") == "system"]
    prompt = (sys_msgs[0] if sys_msgs else "").strip()
    if prompt.lower() in PLACEHOLDER_PROMPTS or len(prompt) < MIN_PROMPT_LEN:
        errs.append(f"system prompt looks like a placeholder: {prompt[:60]!r}")

    props = ((agent.get("outputSchema") or {}).get("properties") or {})
    typed = [k for k in props if k != "content"]
    if not typed:
        errs.append(f"outputSchema has no typed field beyond 'content': {list(props)}")

    if errs:
        print(f"FAIL ({path}): " + "; ".join(errs))
        return 1

    print(f"OK ({path}): model={model} promptlen={len(prompt)} fields={list(props)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
