#!/usr/bin/env python3
"""Verify simulation CRUD produced real artifacts on disk.

Beyond the `command_executed` matchers (which only prove the agent ran the
right shell command), confirm the simulations landed in the eval-set JSON and
that the remove actually mutated the file:

  1. An eval-set JSON exists under SimEval/ with name == "Sim Set" carrying a
     data point named "hello" in `evaluations[]`.
  2. That data point has a non-empty `simulations` array.
  3. The Llm simulation targeting `agent-lookup` is still present (add worked).
  4. The Static simulation targeting `connector-send-email` is gone (the
     `simulation remove` actually wrote back to disk, not just printed OK).

Fails if the agent ran the commands but they errored, or fabricated stdout
without producing/mutating real files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path("SimEval")
KEPT = "agent-lookup"
REMOVED = "connector-send-email"


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _component_ids(sim: dict) -> list[str]:
    """Collect any string field that could carry the targeted component id,
    tolerant of casing/key drift in the CLI's serialized shape."""
    keys = ("componentId", "component_id", "id", "componentID")
    return [str(sim[k]) for k in keys if isinstance(sim.get(k), str)]


def main() -> None:
    if not PROJECT.is_dir():
        sys.exit(f"FAIL: project directory {PROJECT} does not exist")

    docs = _load_jsons(PROJECT)
    if not docs:
        sys.exit(f"FAIL: no JSON files found under {PROJECT}")

    set_match = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict)
            and d.get("name") == "Sim Set"
            and isinstance(d.get("evaluations"), list)
        ),
        None,
    )
    if not set_match:
        sys.exit('FAIL: no eval-set JSON under SimEval/ has name="Sim Set"')

    cases = set_match[1].get("evaluations") or []
    hello = next(
        (c for c in cases if isinstance(c, dict) and c.get("name") == "hello"),
        None,
    )
    if not hello:
        sys.exit(
            f'FAIL: eval set "Sim Set" ({set_match[0]}) has no data point named '
            f'"hello". Got: {[c.get("name") for c in cases if isinstance(c, dict)]}'
        )

    sims = hello.get("simulations")
    if not isinstance(sims, list) or not sims:
        sys.exit(
            f'FAIL: data point "hello" ({set_match[0]}) has no non-empty '
            f'"simulations" array. Got: {sims!r}'
        )

    ids: list[str] = []
    for s in sims:
        if isinstance(s, dict):
            ids.extend(_component_ids(s))

    if KEPT not in ids:
        sys.exit(
            f'FAIL: Llm simulation "{KEPT}" not found in data point "hello" '
            f'simulations (add did not persist). Component ids present: {ids}'
        )
    if REMOVED in ids:
        sys.exit(
            f'FAIL: Static simulation "{REMOVED}" is still present — '
            f'`simulation remove` did not mutate the eval-set JSON. '
            f'Component ids present: {ids}'
        )

    print(
        f"OK: eval set {set_match[0]} data point 'hello' keeps '{KEPT}' and "
        f"dropped '{REMOVED}' (simulation add + remove persisted)"
    )


if __name__ == "__main__":
    main()
