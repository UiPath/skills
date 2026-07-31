#!/usr/bin/env python3
"""Verify the inline-agent eval scaffold produced real artifacts on disk.

This task wires evaluation scaffolding against an INLINE agent node
(`uipath.agent.autonomous`), whose output is non-deterministic LLM text — so
the correct evaluator is an LLM judge, NOT the `exact-match` the deterministic
script-node eval tasks use. Beyond the `command_executed` matchers (which only
prove the agent ran the right shell command), assert the side effects:

  1. The eval target is a real embedded inline agent: TriageEval.flow carries
     a self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, UUID source — graded on the `.flow`,
     the source of truth; no sidecar is required or read) with typed
     `category`/`priority` output variables.
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

import json
import os
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_inline_wiring import (  # noqa: E402
    load_json,
    find_autonomous_agent_node,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_agent_output_vars,
)

PROJECT = Path("TriageEval")
FLOW_PATH = PROJECT / "TriageEval" / "TriageEval.flow"
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

    # 1. Inline agent target is embedded in the .flow (source of truth).
    flow = load_json(FLOW_PATH)
    node = find_autonomous_agent_node(flow)
    assert_embedded_agent(node)
    assert_prompt_tokens(node, require_vars_ref=True)
    assert_agent_output_vars(node, {"category": "string", "priority": "string"})
    print(f"OK: embedded inline agent node {node['id']!r} in {FLOW_PATH}")

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
