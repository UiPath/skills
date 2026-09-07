#!/usr/bin/env python3
"""Verify the local-CRUD smoke produced real artifacts on disk.

Checks the persisted outcomes of local evaluation operations:

  1. An evaluator JSON file exists somewhere in the sandbox with
     name == "greeting-match" and evaluatorTypeId == "uipath-exact-match".
  2. An eval-set JSON file exists with name == "Smoke Set", carrying at
     least one data point in `evaluations[]` whose name == "hello" with
     non-empty `inputs` and `expectedOutput`.

Use ``--check`` to grade one operation's persisted outcome, or omit it for
the final combined check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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


def _find_evaluator(docs: list[tuple[Path, dict]]) -> tuple[Path, dict]:
    match = next(
        (
            (path, doc)
            for path, doc in docs
            if doc.get("name") == "greeting-match"
            and doc.get("evaluatorTypeId") == "uipath-exact-match"
        ),
        None,
    )
    if match is None:
        sys.exit(
            'FAIL: no evaluator JSON has name="greeting-match" '
            'and evaluatorTypeId="uipath-exact-match"'
        )
    print(f"OK: evaluator file {match[0]} matches")
    return match


def _find_eval_set(docs: list[tuple[Path, dict]]) -> tuple[Path, dict]:
    match = next(
        (
            (path, doc)
            for path, doc in docs
            if doc.get("name") == "Smoke Set"
            and isinstance(doc.get("evaluations"), list)
        ),
        None,
    )
    if match is None:
        sys.exit('FAIL: no eval-set JSON has name="Smoke Set"')
    print(f"OK: eval-set file {match[0]} matches")
    return match


def _find_data_point(eval_set: tuple[Path, dict]) -> None:
    cases = eval_set[1].get("evaluations") or []
    hello = next(
        (
            case
            for case in cases
            if isinstance(case, dict) and case.get("name") == "hello"
        ),
        None,
    )
    if not hello:
        sys.exit(
            f'FAIL: eval set "Smoke Set" ({eval_set[0]}) has no data point '
            f'named "hello". Got: {[c.get("name") for c in cases if isinstance(c, dict)]}'
        )
    if not hello.get("inputs"):
        sys.exit('FAIL: data point "hello" has empty inputs')
    if not (hello.get("expectedOutput") or hello.get("expected")):
        sys.exit('FAIL: data point "hello" has no expectedOutput / expected field')
    print(
        f"OK: eval set {eval_set[0]} contains data point 'hello' with inputs + expected"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("evaluator", "eval-set", "data-point"))
    check = parser.parse_args().check

    docs = _load_jsons(Path("."))
    if not docs:
        sys.exit("FAIL: no JSON files found under the sandbox")

    if check in (None, "evaluator"):
        _find_evaluator(docs)
    eval_set = None
    if check in (None, "eval-set", "data-point"):
        eval_set = _find_eval_set(docs)
    if check in (None, "data-point"):
        _find_data_point(eval_set)


if __name__ == "__main__":
    main()
