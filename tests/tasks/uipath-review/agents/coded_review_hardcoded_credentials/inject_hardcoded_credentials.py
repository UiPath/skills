#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject HARDCODED_CREDENTIALS.

The injected line matches both Grep patterns in the catalog rule:
  (api_key|secret|password|token|credential)\\s*=\\s*["'][^"']{8,}["']
  sk-[A-Za-z0-9]{20,}
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


def main() -> None:
    write_baseline_function_agent(ROOT)

    main_py = ROOT / "main.py"
    text = main_py.read_text(encoding="utf-8")
    needle = '    """Process the input message and return a result."""\n'
    secret_line = (
        '    api_key = "sk-abcdefghijklmnopqrstuvwxyz123456"  '
        "# test fixture: hardcoded secret\n"
    )
    if needle not in text:
        raise SystemExit("Pre-condition: baseline main.py docstring not found")
    text = text.replace(needle, needle + secret_line, 1)
    main_py.write_text(text, encoding="utf-8")
    print("Scaffolded CodedAgent + injected hardcoded api_key in main.py")


if __name__ == "__main__":
    main()
