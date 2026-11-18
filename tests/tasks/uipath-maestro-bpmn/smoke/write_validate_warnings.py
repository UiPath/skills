#!/usr/bin/env python3
"""Write the warnings `uip maestro bpmn validate` reports on the built process.

The final `.bpmn` is what the agent shipped, so every warning listed is one it
kept. The next criterion, a judge, reads the file and checks the final
report names each one on `Needs:`, `Assumed:` or `Unverified:`.

The file holds `none`, the warnings, or a first line starting with `unknown`
when a warning list could not be read; the judge scores `unknown` 0.
`[(xml)] unknown attribute` lines are left out: the skill tells the agent
to ignore that parser note on compiled output.

Usage: write_validate_warnings.py <output file>
Exits 0 whenever the file is written: this criterion only records.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.validate_bpmn import _bpmn_files  # noqa: E402

BUDGET_SECONDS = 170
NO_WARNINGS = "none"
UNKNOWN = "unknown"
WARNING_LINE = "[warning]"
PARSER_NOTE = "[(xml)] unknown attribute"
# A failed validate lists warnings only once its rules ran: a thrown error or an
# XML parse failure stops it earlier, and its Instructions hold no warning list.
RULES_RAN = re.compile(r"^Found \d+ error\(s\):")
PARSE_LEVEL = ("[(xml)]", "BPMN_PARSE_ERROR", "XML_NOT_WELL_FORMED")


class Unreadable(Exception):
    pass


def _kept(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("-")]
    return "\n".join(line for line in lines if PARSER_NOTE not in line)


def warnings_of(path: Path, timeout: float) -> str:
    try:
        proc = subprocess.run(
            ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
            capture_output=True,
            text=True,
            timeout=max(1, timeout),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unreadable(f"validate did not run: {exc}") from exc

    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise Unreadable(f"validate printed no JSON (exit {proc.returncode})") from exc

    data = out.get("Data") or {}
    if "Warnings" in data or out.get("Result") == "Success":
        return _kept(str(data.get("Warnings") or ""))

    instructions = out.get("Instructions")
    if not isinstance(instructions, str) or not RULES_RAN.match(instructions.strip()):
        raise Unreadable(f"validate stopped before its warning rules ran (exit {proc.returncode})")
    lines = instructions.splitlines()
    if any("[error]" in line and any(p in line for p in PARSE_LEVEL) for line in lines):
        raise Unreadable("validate could not parse the file")
    return _kept("\n".join(line for line in lines if WARNING_LINE in line))


def main() -> int:
    out = Path(sys.argv[1])
    deadline = time.monotonic() + BUDGET_SECONDS
    files = _bpmn_files()
    found = []
    unknown = [] if files else ["no .bpmn file found"]
    for path in files:
        try:
            text = warnings_of(path, deadline - time.monotonic())
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
