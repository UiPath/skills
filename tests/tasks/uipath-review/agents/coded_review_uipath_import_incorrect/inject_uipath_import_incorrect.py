#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject UIPATH_IMPORT_INCORRECT.

Adds `from uipath import UiPath` at module top (correct form is
`from uipath.platform import UiPath`). Detected by Grep
'^from uipath import UiPath\\b'.
"""

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
BAD_IMPORT = "from uipath import UiPath\n"


def main() -> None:
    write_baseline_function_agent(ROOT)

    main_py = ROOT / "main.py"
    text = main_py.read_text(encoding="utf-8")
    # Prepend the incorrect import as the first line.
    text = BAD_IMPORT + text
    main_py.write_text(text, encoding="utf-8")
    print("Scaffolded CodedAgent + injected incorrect `from uipath import UiPath`")


if __name__ == "__main__":
    main()
