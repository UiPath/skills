#!/usr/bin/env python3
"""The Flow's conversation trigger carries the source agent's appearance.

    python3 $REFERENCE_DIR/conversational_port_appearance/check_port_appearance.py

Offline: reads the fixture `LibraryDeskAgent/agent.json` and the generated
`.flow`. PASS requires a `core.trigger.conversation` node past 1.0 whose
`inputs.appearance` has the agent's welcome title and description,
`personalWorkspaceConnectionsOnly: false` (the agent sets it; the trigger
default is `true`), and the agent's starting prompts, each with the same
`displayPrompt` and `actualPrompt` and a non-empty `id`. Order and ids are not
graded: compile mints ids when they are left out.
Exit 0 on pass; exit 1 with a `FAIL:` line.
"""

from __future__ import annotations

import json
import os
import sys

_TASK_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if os.path.isdir(os.path.join(_TASK_ROOT, "_shared")):
    sys.path.insert(0, _TASK_ROOT)
else:
    sys.exit("FAIL: cannot locate the _shared helpers at " + os.path.normpath(_TASK_ROOT))
from _shared.flow_check import find_flow_files  # noqa: E402

CONV_TRIGGER = "core.trigger.conversation"
NO_APPEARANCE_VERSION = "1.0"
AGENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture", "LibraryDeskAgent", "agent.json")


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        sys.exit(f"FAIL: could not read {path}: {err}")


def _trigger() -> dict:
    seen: list[str] = []
    for path in find_flow_files():
        for node in _load(path).get("nodes") or []:
            if node.get("type") == CONV_TRIGGER:
                print(f"Reading {path}")
                return node
            seen.append(str(node.get("type")))
    sys.exit(f"FAIL: no {CONV_TRIGGER} node in the generated flow; node types seen: {sorted(set(seen))}")


def main() -> int:
    expected = _load(AGENT)["appearance"]
    node = _trigger()

    version = str(node.get("typeVersion") or node.get("version") or "")
    if version.split(".")[:2] == NO_APPEARANCE_VERSION.split("."):
        return _fail(f"conversation trigger is at {version}, which has no appearance")

    appearance = (node.get("inputs") or {}).get("appearance")
    if not isinstance(appearance, dict):
        return _fail(f"conversation trigger has no inputs.appearance: {node.get('inputs')!r}")

    for key in ("welcomeTitle", "welcomeDescription", "personalWorkspaceConnectionsOnly"):
        if appearance.get(key) != expected[key]:
            return _fail(f"appearance.{key} is {appearance.get(key)!r}, expected {expected[key]!r}")

    prompts = appearance.get("startingPrompts")
    if not isinstance(prompts, list) or not all(isinstance(p, dict) for p in prompts):
        return _fail(f"appearance.startingPrompts is not a list of objects: {prompts!r}")
    for p in prompts:
        if not isinstance(p.get("id"), str) or not p["id"]:
            return _fail(f"starting prompt has no id: {p!r}")
    got = sorted((p.get("displayPrompt"), p.get("actualPrompt")) for p in prompts)
    want = sorted((p["displayPrompt"], p["actualPrompt"]) for p in expected["startingPrompts"])
    if got != want:
        return _fail(f"starting prompts (displayPrompt, actualPrompt) are {got}, expected {want}")

    print("PASS: conversation trigger carries the agent's appearance")
    return 0


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
