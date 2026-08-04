#!/usr/bin/env python3
"""Low-code eval run check (cloud lifecycle).

Confirms the agent exported a results artifact from a completed eval run.
`uip agent eval run results --export-format json` writes
`eval-results-{timestamp}.json`; the prompt also asks for results saved to
the project dir, so this globs broadly and accepts any `eval-results*.json`
under the working tree.

Because the run executes in the cloud against a live tenant, per-case
scores are not deterministic — this grades that a results artifact was
produced and carries a recognizable eval-results shape, not specific
scores. The command_executed criteria in the YAML grade the lifecycle
verbs (upload, eval run start --wait, results).

Recognized signals (any one): a top-level/`Data` `Code` of `AgentEvalRun*`,
or any of the documented result keys (`Results`, `evaluationSetResults`,
`EvalSetRunId`, `EvaluatorScores`, `TestCase`).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

RESULT_KEYS = {
    "Results",
    "evaluationSetResults",
    "EvalSetRunId",
    "EvaluatorScores",
    "TestCase",
    "Score",
}


def _walk_keys(obj, found: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in RESULT_KEYS:
                found.add(k)
            _walk_keys(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _walk_keys(item, found)


def main() -> None:
    candidates = sorted(ROOT.rglob("eval-results*.json"))
    if not candidates:
        sys.exit(
            "FAIL: no exported results artifact found (looked for "
            "eval-results*.json under the working tree). Expected the agent "
            "to export results from `uip agent eval run results --export-format json`."
        )

    for path in candidates:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not doc:
            continue

        rel = path.relative_to(ROOT)
        code = ""
        if isinstance(doc, dict):
            code = str(doc.get("Code") or (doc.get("Data") or {}).get("Code") or "")
        if code.startswith("AgentEvalRun"):
            print(f"OK: {rel} is a valid eval-results artifact (Code={code})")
            return

        found: set[str] = set()
        _walk_keys(doc, found)
        if found:
            print(
                f"OK: {rel} is a valid eval-results artifact "
                f"(keys: {sorted(found)})"
            )
            return

    sys.exit(
        "FAIL: found eval-results*.json file(s) but none were valid, non-empty "
        "JSON carrying an eval-results shape (Code AgentEvalRun* or a results "
        f"key {sorted(RESULT_KEYS)}). Candidates: "
        f"{[str(p.relative_to(ROOT)) for p in candidates]}"
    )


if __name__ == "__main__":
    main()
