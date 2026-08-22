#!/usr/bin/env python3
"""Verify simulation CRUD produced real artifacts on disk.

Confirm the simulations landed in the eval-set JSON and that the remove
actually mutated the file:

  1. An eval-set JSON exists somewhere in the sandbox with name == "Sim Set",
     carrying a data point named "hello" in `evaluations[]`.
  2. That data point has a non-empty `simulations` array.
  3. The Llm simulation targeting `agent-lookup` is still present (add worked).
  4. The Static simulation targeting `connector-send-email` is gone (the
     `simulation remove` actually wrote back to disk, not just printed OK).

Pass ``--check`` to grade one persisted outcome, or omit it for the original
combined add/remove check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KEPT = "agent-lookup"
REMOVED = "connector-send-email"


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            out.append((p, value))
    return out


def _component_ids(sim: dict) -> list[str]:
    """Collect any string field that could carry the targeted component id,
    tolerant of casing/key drift in the CLI's serialized shape."""
    keys = ("componentId", "component_id", "id", "componentID")
    return [str(sim[k]) for k in keys if isinstance(sim.get(k), str)]


def _find_eval_set(docs: list[tuple[Path, dict]]) -> tuple[Path, dict]:
    match = next(
        (
            (path, doc)
            for path, doc in docs
            if doc.get("name") == "Sim Set" and isinstance(doc.get("evaluations"), list)
        ),
        None,
    )
    if match is None:
        sys.exit('FAIL: no eval-set JSON has name="Sim Set"')
    return match


def _find_data_point(eval_set: tuple[Path, dict]) -> dict:
    cases = eval_set[1].get("evaluations") or []
    hello = next(
        (
            case
            for case in cases
            if isinstance(case, dict) and case.get("name") == "hello"
        ),
        None,
    )
    if hello is None:
        sys.exit(
            f'FAIL: eval set "Sim Set" ({eval_set[0]}) has no data point named '
            f'"hello". Got: {[c.get("name") for c in cases if isinstance(c, dict)]}'
        )
    return hello


def _simulations(data_point: dict, set_path: Path) -> list[dict]:
    simulations = data_point.get("simulations")
    if not isinstance(simulations, list) or not simulations:
        sys.exit(
            f'FAIL: data point "hello" ({set_path}) has no non-empty '
            f'"simulations" array. Got: {simulations!r}'
        )
    return [sim for sim in simulations if isinstance(sim, dict)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        choices=("eval-set", "data-point", "llm-simulation", "static-absent"),
    )
    check = parser.parse_args().check

    docs = _load_jsons(Path("."))
    if not docs:
        sys.exit("FAIL: no JSON files found under the sandbox")

    set_match = _find_eval_set(docs)
    if check == "eval-set":
        print(f"OK: Sim Set eval set at {set_match[0]}")
        return

    hello = _find_data_point(set_match)
    if check == "data-point":
        if not hello.get("inputs"):
            sys.exit('FAIL: data point "hello" has empty inputs')
        if not (hello.get("expectedOutput") or hello.get("expected")):
            sys.exit('FAIL: data point "hello" has no expectedOutput / expected field')
        print(
            f"OK: eval set {set_match[0]} contains data point 'hello' with inputs + expected"
        )
        return

    sims = _simulations(hello, set_match[0])

    ids: list[str] = []
    for s in sims:
        if isinstance(s, dict):
            ids.extend(_component_ids(s))

    if check == "llm-simulation":
        llm = next(
            (
                sim
                for sim in sims
                if KEPT in _component_ids(sim)
                and sim.get("simulationStrategy") == "Llm"
                and sim.get("outputSchema")
            ),
            None,
        )
        if llm is None:
            sys.exit(
                f'FAIL: no Llm simulation for "{KEPT}" has an explicit outputSchema'
            )
        print(f"OK: Llm simulation {KEPT!r} persists with an output schema")
        return

    if check == "static-absent":
        if REMOVED in ids:
            sys.exit(f'FAIL: Static simulation "{REMOVED}" is still present')
        print(f"OK: removed simulation {REMOVED!r} is absent")
        return

    if KEPT not in ids:
        sys.exit(
            f'FAIL: Llm simulation "{KEPT}" not found in data point "hello" '
            f"simulations (add did not persist). Component ids present: {ids}"
        )
    if REMOVED in ids:
        sys.exit(
            f'FAIL: Static simulation "{REMOVED}" is still present — '
            f"`simulation remove` did not mutate the eval-set JSON. "
            f"Component ids present: {ids}"
        )

    print(
        f"OK: eval set {set_match[0]} data point 'hello' keeps '{KEPT}' and "
        f"dropped '{REMOVED}' (simulation add + remove persisted)"
    )


if __name__ == "__main__":
    main()
