#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent with NO eval-sets directory.

The baseline scaffold ships no evals/ — which is exactly the
MISSING_EVAL_DIR trigger (Glob finds no eval-sets/ at project root).
This inject explicitly asserts the absence so the test's premise is
self-documenting and robust if the baseline ever changes.
"""

import os
import shutil
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


def main() -> None:
    write_baseline_function_agent(ROOT)

    # Belt-and-suspenders: remove any eval dir the baseline might create
    # so MISSING_EVAL_DIR is guaranteed to be the injected condition.
    for candidate in ("eval-sets", "evals", "evaluations"):
        p = ROOT / candidate
        if p.exists():
            shutil.rmtree(p)

    print("Scaffolded CodedAgent with no eval-sets directory (MISSING_EVAL_DIR)")


if __name__ == "__main__":
    main()
