#!/usr/bin/env python3
"""Smoke check: a scaffolded inline (uipath.agent.autonomous) agent was raised
to a production bar, not left on the toy scaffold defaults.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/check_inline_agent.py <glob>

  <glob>  Shell-style glob for the inline agent.json. The inline agent dir is a
          UUID, so the path is not statically knowable — pass e.g.
          "EmailTriage/EmailTriage/*/agent.json". Defaults to
          "*/*/*/agent.json" if omitted.

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


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*/*/*/agent.json"
    paths = [p for p in glob.glob(pattern) if "/.agent-builder/" not in p]
    if not paths:
        print(f"FAIL: no inline agent.json matched {pattern!r}")
        return 1

    path = sorted(paths)[0]
    try:
        agent = json.load(open(path))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: could not read {path}: {e}")
        return 1

    errs = []

    model = (agent.get("settings") or {}).get("model", "")
    if not model:
        errs.append("settings.model is empty")
    elif model == SCAFFOLD_MODEL:
        errs.append(f"settings.model not overridden ({model})")

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
