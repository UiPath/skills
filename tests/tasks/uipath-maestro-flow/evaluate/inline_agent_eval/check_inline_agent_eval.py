#!/usr/bin/env python3
"""Verify the inline-agent eval scaffold produced real artifacts on disk.

This task wires evaluation scaffolding against an INLINE agent node
(`uipath.agent.autonomous`), whose output is non-deterministic LLM text — so
the correct evaluator is an LLM judge, NOT the `exact-match` the deterministic
script-node eval tasks use. Beyond the `command_executed` matchers (which only
prove the agent ran the right shell command), assert the side effects:

  1. An inline agent.json exists under TriageEval/TriageEval/<uuid>/agent.json
     (the inline agent dir is a UUID, so glob it; skip generated
     .agent-builder/). Proves the eval target is a real inline agent.
  2. An evaluator JSON exists with evaluatorTypeId ==
     "uipath-llm-judge-output-semantic-similarity" (the `llm-judge-output`
     internal id) carrying a non-empty `model` — the right choice for a
     non-deterministic agent output, and the model the LLM gateway requires.
  3. An eval-set JSON exists with at least one data point in `evaluations[]`
     carrying non-empty `inputs` and an expected-output field.

These checks fail if the agent ran the commands but they errored, picked a
deterministic evaluator for the non-deterministic agent, or fabricated stdout
without producing real files. Reads only source files — no tenant calls.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

PROJECT = Path("TriageEval")
INLINE_AGENT_GLOB = "TriageEval/TriageEval/*/agent.json"
LLM_JUDGE_TYPE_ID = "uipath-llm-judge-output-semantic-similarity"


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        if "/.agent-builder/" in p.as_posix():
            continue
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def main() -> None:
    if not PROJECT.is_dir():
        sys.exit(f"FAIL: project directory {PROJECT} does not exist")

    # 1. Inline agent target exists.
    agent_paths = [p for p in glob.glob(INLINE_AGENT_GLOB) if "/.agent-builder/" not in p]
    if not agent_paths:
        sys.exit(f"FAIL: no inline agent.json matched {INLINE_AGENT_GLOB!r}")
    print(f"OK: inline agent at {sorted(agent_paths)[0]}")

    docs = _load_jsons(PROJECT)
    if not docs:
        sys.exit(f"FAIL: no JSON files found under {PROJECT}")

    # 2. LLM-judge evaluator (not a deterministic type) with a model set.
    evaluator = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict) and d.get("evaluatorTypeId") == LLM_JUDGE_TYPE_ID
        ),
        None,
    )
    if not evaluator:
        ids = sorted({d.get("evaluatorTypeId") for _, d in docs if isinstance(d, dict) and d.get("evaluatorTypeId")})
        sys.exit(
            f'FAIL: no evaluator JSON under {PROJECT}/ has '
            f'evaluatorTypeId="{LLM_JUDGE_TYPE_ID}" (llm-judge-output). '
            f"Found evaluator type ids: {ids}"
        )
    model = (evaluator[1].get("evaluatorConfig") or {}).get("model") or evaluator[1].get("model")
    if not model:
        sys.exit(f"FAIL: llm-judge evaluator {evaluator[0]} has no model set")
    print(f"OK: llm-judge-output evaluator {evaluator[0]} with model={model!r}")

    # 3. Eval set with at least one well-formed data point.
    set_match = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict) and isinstance(d.get("evaluations"), list) and d.get("evaluations")
        ),
        None,
    )
    if not set_match:
        sys.exit(f"FAIL: no eval-set JSON under {PROJECT}/ has a non-empty evaluations[] list")

    cases = set_match[1].get("evaluations") or []
    good = next(
        (
            c
            for c in cases
            if isinstance(c, dict) and c.get("inputs") and (c.get("expectedOutput") or c.get("expected"))
        ),
        None,
    )
    if not good:
        sys.exit(
            f"FAIL: eval set {set_match[0]} has no data point with both non-empty "
            f"inputs and an expectedOutput/expected field"
        )
    print(f"OK: eval set {set_match[0]} has data point {good.get('name')!r} with inputs + expected")


if __name__ == "__main__":
    main()
