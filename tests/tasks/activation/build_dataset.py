#!/usr/bin/env python3
"""Merge per-skill positives + shared negatives → dataset.jsonl for coder-eval.

HACK: This script exists because coder_eval's `dataset.path` only accepts a
single JSONL file. The proper fix is to extend the framework's Dataset model
to accept `dataset.paths: [...]` (with optional per-path label injection) so
the YAML can reference both source files directly. Until then, this script
materializes a merged file and the activation.yaml points at it. See the
chat thread that introduced this comment for context.

Each row in `<skill>.jsonl` is a positive for that skill (should_trigger=yes).
Each row in `negative.jsonl` is a shared negative (should_trigger=no for any
skill). Cross-skill confusion: a row in skill A's file is also a negative
when scoring skill B (not yet exercised — only one skill so far).

Usage:
    uv run python build_dataset.py --skill uipath-maestro-flow
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, help="skill name (file stem of <skill>.jsonl)")
    parser.add_argument("--out", default=str(_DIR / "dataset.jsonl"))
    args = parser.parse_args()

    skill_path = _DIR / f"{args.skill}.jsonl"
    if not skill_path.exists():
        raise SystemExit(f"missing positives file: {skill_path}")

    positives = _read_jsonl(skill_path)
    negatives = _read_jsonl(_DIR / "negative.jsonl")

    # Cross-skill negatives: every other <skill>.jsonl file in this directory.
    # Each such row is a negative when scoring `args.skill`.
    cross: list[dict] = []
    for other in sorted(_DIR.glob("*.jsonl")):
        if other.name in {f"{args.skill}.jsonl", "negative.jsonl", "dataset.jsonl"}:
            continue
        for row in _read_jsonl(other):
            cross.append({**row, "expected_skill": other.stem})

    out_rows: list[dict] = []
    for row in positives:
        out_rows.append({**row, "should_trigger": "yes", "expected_skill": args.skill})
    for row in negatives:
        out_rows.append({**row, "should_trigger": "no", "expected_skill": None})
    for row in cross:
        out_rows.append({**row, "should_trigger": "no"})

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    yes = sum(1 for r in out_rows if r["should_trigger"] == "yes")
    no = len(out_rows) - yes
    print(f"Wrote {len(out_rows)} rows to {out_path} (yes={yes}, no={no}; cross-skill={len(cross)})")


if __name__ == "__main__":
    main()
