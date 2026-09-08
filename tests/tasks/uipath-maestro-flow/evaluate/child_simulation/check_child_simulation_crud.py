#!/usr/bin/env python3
"""Verify child simulation CRUD produced real artifacts on disk.

Beyond the `command_executed` matchers (which only prove the agent ran the
right shell command), confirm that:

  1. An eval-set JSON exists under ChildSimEval/ with name == "Agent Tools"
     carrying a data point named "search-test" in `evaluations[]`.
  2. That data point has a `simulations` array with a parent entry whose
     componentId is "agent-1" (auto-created by --parent).
  3. The parent has a `childSimulations` array.
  4. The Static child simulation "Web_Search" is present (add worked).
  5. The Llm child simulation "Send_Email" is gone (remove worked).
  6. The parent simulation's componentType is "agent" and simulationStrategy
     is "Llm" (auto-creation defaults).

Fails if the agent ran the commands but they errored, or fabricated stdout
without producing/mutating real files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path("ChildSimEval")
KEPT_CHILD = "Web_Search"
REMOVED_CHILD = "Send_Email"
PARENT_ID = "agent-1"


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _component_ids(sims: list) -> list[str]:
    """Extract componentId from a list of simulation dicts."""
    ids: list[str] = []
    for s in sims:
        if isinstance(s, dict):
            cid = s.get("componentId") or s.get("component_id") or s.get("id")
            if isinstance(cid, str):
                ids.append(cid)
    return ids


def main() -> None:
    if not PROJECT.is_dir():
        sys.exit(f"FAIL: project directory {PROJECT} does not exist")

    docs = _load_jsons(PROJECT)
    if not docs:
        sys.exit(f"FAIL: no JSON files found under {PROJECT}")

    # 1. Find eval set "Agent Tools"
    set_match = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict)
            and d.get("name") == "Agent Tools"
            and isinstance(d.get("evaluations"), list)
        ),
        None,
    )
    if not set_match:
        names = [d.get("name") for _, d in docs if isinstance(d, dict) and d.get("name")]
        sys.exit(
            f'FAIL: no eval-set JSON under {PROJECT}/ has name="Agent Tools". '
            f"Found names: {names}"
        )

    # 2. Find data point "search-test"
    cases = set_match[1].get("evaluations") or []
    dp = next(
        (c for c in cases if isinstance(c, dict) and c.get("name") == "search-test"),
        None,
    )
    if not dp:
        sys.exit(
            f'FAIL: eval set "Agent Tools" ({set_match[0]}) has no data point '
            f'named "search-test". Got: {[c.get("name") for c in cases if isinstance(c, dict)]}'
        )

    # 3. Find parent simulation "agent-1"
    sims = dp.get("simulations")
    if not isinstance(sims, list) or not sims:
        sys.exit(
            f'FAIL: data point "search-test" has no simulations array. Got: {sims!r}'
        )

    parent_ids = _component_ids(sims)
    parent = next(
        (s for s in sims if isinstance(s, dict) and s.get("componentId") == PARENT_ID),
        None,
    )
    if not parent:
        sys.exit(
            f'FAIL: no parent simulation with componentId="{PARENT_ID}" found. '
            f"Component ids present: {parent_ids}"
        )

    # 4. Verify auto-creation defaults
    parent_type = parent.get("componentType")
    parent_strategy = parent.get("simulationStrategy")
    if parent_type != "agent":
        sys.exit(
            f'FAIL: parent simulation componentType should be "agent", '
            f'got "{parent_type}"'
        )
    if parent_strategy != "Llm":
        sys.exit(
            f'FAIL: auto-created parent simulationStrategy should be "Llm", '
            f'got "{parent_strategy}"'
        )
    print(f"OK: parent simulation {PARENT_ID} auto-created (type=agent, strategy=Llm)")

    # 5. Check child simulations
    children = parent.get("childSimulations")
    if not isinstance(children, list):
        sys.exit(
            f'FAIL: parent "{PARENT_ID}" has no childSimulations array. '
            f"Got: {children!r}"
        )

    child_ids = _component_ids(children)

    if KEPT_CHILD not in child_ids:
        sys.exit(
            f'FAIL: child simulation "{KEPT_CHILD}" not found in parent '
            f'"{PARENT_ID}" childSimulations (add did not persist). '
            f"Child ids present: {child_ids}"
        )

    if REMOVED_CHILD in child_ids:
        sys.exit(
            f'FAIL: child simulation "{REMOVED_CHILD}" is still present — '
            f"`simulation remove --parent` did not mutate the eval-set JSON. "
            f"Child ids present: {child_ids}"
        )

    print(
        f"OK: parent '{PARENT_ID}' keeps child '{KEPT_CHILD}' and "
        f"dropped child '{REMOVED_CHILD}' (child simulation add + remove persisted)"
    )


if __name__ == "__main__":
    main()
