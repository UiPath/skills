#!/usr/bin/env python3
"""Conversational appearance check (conversational anti-pattern 6).

Studio Web validates `agent.json` against the agents storage schema on load.
`appearance` must carry `welcomeTitle`, `welcomeDescription`, and
`startingPrompts`, and every starting prompt must be an object with string
`id`, `displayPrompt`, `actualPrompt`. A plain-string prompt array makes the
project unloadable ("Project storage is corrupted").

PASS requires ALL of:
  1. `appearance` is an object with string `welcomeTitle` and
     `welcomeDescription`, and `welcomeTitle` == "IT Help Desk"
  2. `startingPrompts` is a list of exactly three objects (no strings)
  3. every prompt has non-empty string `id`, `displayPrompt`, `actualPrompt`;
     ids are unique
  4. the display prompts are the three requested ones, in any order
  5. `displayMode`, when present, is a supported value
"""

import json
import os
import sys
from pathlib import Path

AGENT = Path(os.getcwd()) / "HelpDeskSol" / "HelpDeskBot" / "agent.json"

EXPECTED_PROMPTS = {"Reset my password", "Request a new laptop", "Check my ticket status"}
DISPLAY_MODES = {"FullTrace", "InputsAndOutputs", "ToolNameOnly"}
PROMPT_FIELDS = ("id", "displayPrompt", "actualPrompt")


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def main() -> None:
    appearance = load(AGENT).get("appearance")
    if not isinstance(appearance, dict):
        sys.exit(f"FAIL: appearance must be an object, got {appearance!r}")

    for field in ("welcomeTitle", "welcomeDescription"):
        if not isinstance(appearance.get(field), str):
            sys.exit(f"FAIL: appearance.{field} must be a string, got {appearance.get(field)!r}")
    if appearance["welcomeTitle"].strip() != "IT Help Desk":
        sys.exit(f'FAIL: welcomeTitle must be "IT Help Desk", got {appearance["welcomeTitle"]!r}')
    print("OK: welcomeTitle and welcomeDescription are strings")

    prompts = appearance.get("startingPrompts")
    if not isinstance(prompts, list) or len(prompts) != 3:
        sys.exit(f"FAIL: startingPrompts must be a list of 3 entries, got {prompts!r}")

    ids = set()
    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            sys.exit(f"FAIL: startingPrompts[{i}] must be an object, got {prompt!r}")
        for field in PROMPT_FIELDS:
            value = prompt.get(field)
            if not isinstance(value, str) or not value.strip():
                sys.exit(f"FAIL: startingPrompts[{i}].{field} must be a non-empty string, got {value!r}")
        ids.add(prompt["id"])
    if len(ids) != len(prompts):
        sys.exit("FAIL: startingPrompts ids must be unique")
    print("OK: every starting prompt is an object with id, displayPrompt, actualPrompt")

    shown = {p["displayPrompt"].strip() for p in prompts}
    if shown != EXPECTED_PROMPTS:
        sys.exit(f"FAIL: displayPrompts {sorted(shown)} != {sorted(EXPECTED_PROMPTS)}")
    print("OK: display prompts match the request")

    if "displayMode" in appearance:
        mode = appearance["displayMode"]
        if not isinstance(mode, str) or mode not in DISPLAY_MODES:
            sys.exit(f"FAIL: displayMode {mode!r} not in {sorted(DISPLAY_MODES)}")
    print("OK: displayMode absent or supported")

    print("PASS")


if __name__ == "__main__":
    main()
