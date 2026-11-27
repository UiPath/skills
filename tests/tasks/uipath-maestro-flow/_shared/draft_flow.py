"""Helpers the draft-mode graders share: find the Flow, read it, tell mock nodes from real ones."""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_flow  # noqa: E402
from flow_check import find_flow_file  # noqa: E402

MOCK = "core.logic.mock"
DECISION = "core.logic.decision"
SWITCH = "core.logic.switch"
LOOP = "core.logic.loop"
CONTROL_TYPES = frozenset({
    DECISION,
    SWITCH,
    LOOP,
    "core.logic.merge",
    "core.logic.terminate",
    "core.control.end",
    "stickyNote",
})
KIND_SUFFIX = re.compile(r"\s\[[^\[\]]+\](?=\s*(?:→|->|$))")


def fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def load_flow() -> tuple[str, dict]:
    path = find_flow_file()
    with open(path, encoding="utf-8") as fh:
        return path, json.load(fh)


def label_of(node: dict) -> str:
    return (node.get("display") or {}).get("label") or ""


def is_trigger(node: dict) -> bool:
    return str(node.get("type", "")).startswith("core.trigger.")


def action_nodes(doc: dict) -> list[dict]:
    """Nodes that do work: everything but triggers and control flow."""
    return [
        n for n in doc.get("nodes") or []
        if not is_trigger(n) and n.get("type") not in CONTROL_TYPES
    ]


def validate(path: str) -> int:
    return validate_flow.main([path])
