#!/usr/bin/env python3
"""C4 anti-pattern check — module-level UiPath* must be gone after the fix."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "legacy-classifier"
MAIN = ROOT / "main.py"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402


def main() -> None:
    if not MAIN.is_file():
        sys.exit(f"FAIL: missing {MAIN}")
    violations = find_module_level_llm_clients(MAIN)
    if violations:
        sys.exit(
            "FAIL: main.py still has module-level UiPath* construction — "
            "Critical Rule C4 violation. Move the LLM client into a node body. "
            + " | ".join(violations)
        )
    print("OK: main.py has no module-level UiPath* construction")
    text = MAIN.read_text(encoding="utf-8")
    # The graph variable must survive the refactor — it's what
    # `uip codedagent init` looks for via langgraph.json.
    if not re.search(r"^\s*graph\s*=\s*", text, re.M):
        sys.exit(
            "FAIL: main.py no longer exports a top-level `graph =` variable. "
            "Refactor must preserve the compiled graph export."
        )
    print("OK: top-level `graph` variable still exported")


if __name__ == "__main__":
    main()
