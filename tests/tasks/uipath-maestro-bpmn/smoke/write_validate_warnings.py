#!/usr/bin/env python3
"""Write the warnings `uip maestro bpmn validate` reports on the built process.

The final `.bpmn` is what the agent shipped, so every warning listed is one it
kept. The next criterion, a judge, reads the file and checks the final
report names each one on `Assumed:` or `Unverified:`.

Usage: write_validate_warnings.py <output file>
Always exits 0: this criterion only records; the judge grades.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.validate_bpmn import _bpmn_files  # noqa: E402

TIMEOUT_SECONDS = 60
NO_WARNINGS = "none"


def warnings_of(path: Path) -> str:
    proc = subprocess.run(
        ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    try:
        data = json.loads(proc.stdout).get("Data") or {}
    except json.JSONDecodeError:
        return ""
    return str(data.get("Warnings") or "").strip()


def main() -> int:
    out = Path(sys.argv[1])
    found = []
    for path in _bpmn_files():
        text = warnings_of(path)
        if text:
            found.append(f"{path.name}:\n{text}")
    out.write_text("\n\n".join(found) or NO_WARNINGS, encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
