#!/usr/bin/env python3
"""Verify the inline-agent eval scaffold produced real artifacts on disk.

This task wires evaluation scaffolding against an INLINE agent node
(`uipath.agent.autonomous`), whose output is non-deterministic LLM text — so
the correct evaluator is an LLM judge, NOT the `exact-match` the deterministic
script-node eval tasks use. The checks assert these persisted side effects:

  1. An inline agent.json exists somewhere in the sandbox (skip generated
     .agent-builder/ intermediates). Proves the eval target is a real inline
     agent.
  2. An evaluator JSON exists with evaluatorTypeId ==
     "uipath-llm-judge-output-semantic-similarity" (the `llm-judge-output`
     internal id) carrying a non-empty `model` — the right choice for a
     non-deterministic agent output, and the model the LLM gateway requires.
  3. An eval-set JSON exists with at least one data point in `evaluations[]`
     carrying non-empty `inputs` and an expected-output field.

Pass ``--check`` to grade one persisted outcome, or omit it for the original
combined scaffold check. Reads only source files — no tenant calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LLM_JUDGE_TYPE_ID = "uipath-llm-judge-output-semantic-similarity"
DETERMINISTIC_TYPE_IDS = {"uipath-exact-match", "uipath-contains"}


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        if "/.agent-builder/" in p.as_posix():
            continue
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            out.append((p, value))
    return out


def _check_inline_agent() -> None:
    agent_paths = [
        path
        for path in Path(".").rglob("agent.json")
        if "/.agent-builder/" not in path.as_posix()
    ]
    if not agent_paths:
        sys.exit("FAIL: no inline agent.json found in the sandbox")
    print(f"OK: inline agent at {sorted(agent_paths)[0]}")


def _check_evaluator(docs: list[tuple[Path, dict]]) -> None:
    evaluator = next(
        ((p, d) for p, d in docs if d.get("evaluatorTypeId") == LLM_JUDGE_TYPE_ID),
        None,
    )
    if not evaluator:
        ids = sorted(
            {
                doc.get("evaluatorTypeId")
                for _, doc in docs
                if doc.get("evaluatorTypeId")
            }
        )
        sys.exit(
            "FAIL: no evaluator JSON has "
            f'evaluatorTypeId="{LLM_JUDGE_TYPE_ID}" (llm-judge-output). '
            f"Found evaluator type ids: {ids}"
        )
    model = (evaluator[1].get("evaluatorConfig") or {}).get("model") or evaluator[
        1
    ].get("model")
    if not model:
        sys.exit(f"FAIL: llm-judge evaluator {evaluator[0]} has no model set")
    print(f"OK: llm-judge-output evaluator {evaluator[0]} with model={model!r}")


def _check_no_deterministic(docs: list[tuple[Path, dict]]) -> None:
    matches = [
        (path, doc.get("evaluatorTypeId"))
        for path, doc in docs
        if doc.get("evaluatorTypeId") in DETERMINISTIC_TYPE_IDS
    ]
    if matches:
        sys.exit(f"FAIL: deterministic evaluator artifacts found: {matches}")
    print("OK: no exact-match or contains evaluator artifact exists")


def _find_eval_set(docs: list[tuple[Path, dict]]) -> tuple[Path, dict]:
    set_match = next(
        (
            (path, doc)
            for path, doc in docs
            if doc.get("name") == "Triage Cases"
            and isinstance(doc.get("evaluations"), list)
        ),
        None,
    )
    if not set_match:
        sys.exit('FAIL: no eval-set JSON has name="Triage Cases"')
    return set_match


def _check_eval_set(docs: list[tuple[Path, dict]]) -> None:
    set_match = _find_eval_set(docs)
    print(f"OK: Triage Cases eval set at {set_match[0]}")


def _check_evaluator_refs(docs: list[tuple[Path, dict]]) -> None:
    set_path, eval_set = _find_eval_set(docs)
    refs = eval_set.get("evaluatorRefs")
    if not isinstance(refs, list) or not refs:
        sys.exit(f"FAIL: eval set {set_path} has no evaluatorRefs")
    if "triage-judge" in refs:
        sys.exit(f"FAIL: eval set {set_path} uses display name 'triage-judge' as a ref")
    print(f"OK: eval set {set_path} uses generated evaluator refs: {refs}")


def _check_data_point(docs: list[tuple[Path, dict]]) -> None:
    set_match = _find_eval_set(docs)

    cases = set_match[1].get("evaluations") or []
    good = next(
        (
            c
            for c in cases
            if isinstance(c, dict)
            and c.get("inputs")
            and (c.get("expectedOutput") or c.get("expected"))
        ),
        None,
    )
    if not good:
        sys.exit(
            f"FAIL: eval set {set_match[0]} has no data point with both non-empty "
            f"inputs and an expectedOutput/expected field"
        )
    print(
        f"OK: eval set {set_match[0]} has data point {good.get('name')!r} with inputs + expected"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        choices=(
            "inline-agent",
            "evaluator",
            "no-deterministic",
            "eval-set",
            "evaluator-refs",
            "data-point",
        ),
    )
    check = parser.parse_args().check
    docs = _load_jsons(Path("."))

    if check in (None, "inline-agent"):
        _check_inline_agent()
    if check in (None, "evaluator"):
        _check_evaluator(docs)
    if check == "no-deterministic":
        _check_no_deterministic(docs)
    if check == "eval-set":
        _check_eval_set(docs)
    if check == "evaluator-refs":
        _check_evaluator_refs(docs)
    if check in (None, "data-point"):
        _check_data_point(docs)


if __name__ == "__main__":
    main()
