#!/usr/bin/env python3
"""Write the warnings `uip maestro bpmn validate` reports on the built process.

The final `.bpmn` is what the agent shipped, so every warning listed is one it
kept. The next criterion, a judge, reads the file and checks the final
report names each one on `Assumed:` or `Unverified:`.

The file holds `none`, the warnings, or a first line starting with `unknown`
when a warning list could not be read; the judge scores `unknown` 0.

Usage: write_validate_warnings.py <output file>
Exits 0 whenever the file is written: this criterion only records.
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
UNKNOWN = "unknown"
WARNING_LINE = "[warning]"


class Unreadable(Exception):
    pass


def warnings_of(path: Path) -> str:
    try:
        proc = subprocess.run(
            ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unreadable(f"validate did not run: {exc}") from exc

    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise Unreadable(f"validate printed no JSON (exit {proc.returncode})") from exc

    data = out.get("Data") or {}
    if "Warnings" in data or out.get("Result") == "Success":
        return str(data.get("Warnings") or "").strip()

    instructions = out.get("Instructions")
    if not isinstance(instructions, str):
        raise Unreadable(f"validate failed with no Instructions (exit {proc.returncode})")
    return "\n".join(line for line in instructions.splitlines() if WARNING_LINE in line).strip()


def main() -> int:
    out = Path(sys.argv[1])
    found, unknown = [], []
    for path in _bpmn_files():
        try:
            text = warnings_of(path)
        except Unreadable as exc:
            unknown.append(f"{path.name}: {exc}")
            continue
        if text:
            found.append(f"{path.name}:\n{text}")

    parts = [f"{UNKNOWN}: " + "; ".join(unknown)] if unknown else []
    parts += found
    out.write_text("\n\n".join(parts) or NO_WARNINGS, encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
