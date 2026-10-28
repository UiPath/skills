#!/usr/bin/env python3
"""Diagnose check: trajectory-evaluator-on-plain-StateGraph trap.

Quickstart Step 7 documents that
`uipath-llm-judge-trajectory-similarity` scores 0.0 on plain
`StateGraph` agents because `AgentRunHistory` is empty. The skill
proposes two valid fixes:

  Fix A — swap the evaluator for one that matches the user's stated
  need: "a simple 'did the right keyword end up in the output'
  check." That's `ContainsEvaluator`
  (`evaluatorTypeId: "uipath-contains"`). Other output-based
  evaluators don't fit the user's described semantics.

  Fix B — add `@traced()` decorator (from `uipath.tracing`) to the
  graph entrypoint so AgentRunHistory spans actually populate.
  Heuristic signal: `main.py` now imports from `uipath.tracing` and
  applies `@traced()` to the agent function.

Either fix is acceptable; both is fine. The check fails only if
NEITHER signal is present — that means the agent walked away with
the trap still in place, or applied a fix that doesn't match what
the user asked for.

Beyond the fix, the check also verifies:
  - the seeded `main.py` was preserved (the routing logic that
    was working should not have been rewritten),
  - `evaluatorRefs` and the eval set's per-case `evaluationCriterias`
    were updated consistently if the evaluator id changed (Fix A),
    so the eval set still parses.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("ticket-router")

CONTAINS_TYPE = "uipath-contains"

UIPATH_TRACING_HINTS = (
    "uipath.tracing",
    "from uipath.tracing import",
    "@traced(",
    "@traced()",
)


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_main_preserved() -> None:
    """The seed main.py routes deterministically. Allow edits but the
    routing-by-keywords logic must survive — Fix A doesn't touch
    main.py; Fix B only adds tracing instrumentation."""
    text = _read_text(ROOT / "main.py")
    for needle in ("StateGraph", "graph = builder.compile()"):
        if needle not in text:
            sys.exit(
                f"FAIL: main.py lost the structural piece `{needle}` — the "
                "diagnose flow should not rewrite the working agent."
            )
    if "invoice" not in text and "billing" not in text:
        sys.exit(
            "FAIL: main.py no longer contains the routing keywords from "
            "the seed; the agent appears to have been rewritten instead "
            "of fixed."
        )
    print("OK: main.py retains the working routing logic from the seed")


def detect_fix_a() -> bool:
    """Fix A — `ContainsEvaluator` wired in.

    Per the user's stated need ("did the right keyword end up in the
    output"), the matching evaluator type is `uipath-contains`. Other
    evaluator types don't capture that exact semantics. If `Fix A` is
    applied, it must be `ContainsEvaluator` AND the eval set must
    reference it consistently.
    """
    evals_dir = ROOT / "evaluations" / "evaluators"
    if not evals_dir.is_dir():
        return False
    contains_ids: list[str] = []
    for path in sorted(evals_dir.glob("*.json")):
        doc = _load_json(path)
        if doc.get("evaluatorTypeId") == CONTAINS_TYPE:
            contains_ids.append(doc.get("id") or path.stem)
    if not contains_ids:
        return False

    eval_sets_dir = ROOT / "evaluations" / "eval-sets"
    refs_match = False
    for path in sorted(eval_sets_dir.glob("*.json")):
        doc = _load_json(path)
        refs = set(doc.get("evaluatorRefs") or [])
        if refs & set(contains_ids):
            refs_match = True
            for case in doc.get("evaluations") or []:
                keys = set((case.get("evaluationCriterias") or {}).keys())
                if not (keys & set(contains_ids)):
                    sys.exit(
                        f'FAIL: eval-set case `{case.get("id")}` does not key '
                        f'its evaluationCriterias on the ContainsEvaluator '
                        f'id(s) {contains_ids}. Got keys: {sorted(keys)}'
                    )
    if not refs_match:
        sys.exit(
            f"FAIL: a ContainsEvaluator was authored ({contains_ids}) but "
            f"no eval-set's `evaluatorRefs` points at it — Fix A is "
            f"half-applied."
        )
    print(f"OK: Fix A detected — ContainsEvaluator wired (ids: {contains_ids})")
    return True


def detect_fix_b() -> bool:
    """Fix B — main.py adds @traced() decorator from uipath.tracing to
    populate AgentRunHistory."""
    text = _read_text(ROOT / "main.py")
    has_traced = any(hint in text for hint in UIPATH_TRACING_HINTS)
    if not has_traced:
        return False
    print("OK: Fix B detected — @traced() decorator from uipath.tracing wired into main.py")
    return True


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_main_preserved()
    fix_a = detect_fix_a()
    fix_b = detect_fix_b()
    if not (fix_a or fix_b):
        sys.exit(
            "FAIL: neither documented fix was applied. The trajectory "
            "evaluator on a plain StateGraph still scores 0.0 because "
            "AgentRunHistory is empty. Expected one of: (A) replace the "
            "evaluator with `ContainsEvaluator` (the user's stated need "
            "was a keyword-in-output check), or (B) add the `@traced()` "
            "decorator from `uipath.tracing` to main.py."
        )


if __name__ == "__main__":
    main()
