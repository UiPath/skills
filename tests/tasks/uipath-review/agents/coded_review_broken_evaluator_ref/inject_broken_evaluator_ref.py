#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject EVAL_BROKEN_EVALUATOR_REF.

Creates an eval set whose `evaluatorRefs` lists `ghost-evaluator-id`,
while evaluations/evaluators/ only configures a different id. The
dangling reference is the rule trigger.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from coded_scaffold import write_baseline_function_agent  # noqa: E402

ROOT = Path("CodedAgent")
GHOST_ID = "ghost-evaluator-id"
REAL_ID = "real-evaluator-id"


def main() -> None:
    write_baseline_function_agent(ROOT)

    eval_sets = ROOT / "evaluations" / "eval-sets"
    evaluators = ROOT / "evaluations" / "evaluators"
    eval_sets.mkdir(parents=True, exist_ok=True)
    evaluators.mkdir(parents=True, exist_ok=True)

    # Eval set references GHOST_ID (which has no config).
    (eval_sets / "default.json").write_text(
        json.dumps(
            {
                "fileName": "default.json",
                "id": "eval-set-default",
                "name": "Default Evaluation Set",
                "evaluatorRefs": [GHOST_ID],
                "evaluations": [
                    {
                        "id": "test-echo",
                        "inputs": {"message": "hello"},
                        "expectedOutput": "hello",
                        "expectedAgentBehavior": "Echo the message back unchanged.",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Only REAL_ID is configured — GHOST_ID dangles.
    (evaluators / "real.json").write_text(
        json.dumps(
            {
                "fileName": "real.json",
                "id": REAL_ID,
                "name": "Exact Match",
                "type": "uipath-exact-match",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Scaffolded CodedAgent + eval set referencing {GHOST_ID!r} "
        f"(configured: {REAL_ID!r}) — EVAL_BROKEN_EVALUATOR_REF"
    )


if __name__ == "__main__":
    main()
