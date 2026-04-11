#!/usr/bin/env python3
"""Run DiceRoller flow and verify output contains a valid dice roll (1-6)."""

import glob
import json
import os
import re
import subprocess
import sys


def parse_json(stdout):
    """Parse JSON from stdout, skipping any non-JSON prefix lines from uip."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        for i, line in enumerate(stdout.split("\n")):
            if line.strip().startswith("{"):
                try:
                    return json.loads("\n".join(stdout.split("\n")[i:]))
                except json.JSONDecodeError:
                    continue
    return None


def main():
    projects = glob.glob("**/project.uiproj", recursive=True)
    if not projects:
        sys.exit("FAIL: No project.uiproj found")

    project_dir = os.path.dirname(projects[0])
    r = subprocess.run(
        ["uip", "flow", "debug", project_dir, "--output", "json"],
        capture_output=True, text=True, timeout=90,
    )
    if r.returncode != 0:
        sys.exit(f"FAIL: flow debug exit {r.returncode}\n{r.stderr[:500]}")

    data = parse_json(r.stdout)
    if data is None:
        sys.exit(f"FAIL: Could not parse JSON\n{r.stdout[:500]}")
    if (data.get("Data") or {}).get("finalStatus") != "Completed":
        sys.exit(f"FAIL: Flow did not complete\n{r.stdout[:1000]}")

    # Look for any integer 1-6 in the output (valid dice roll)
    output_str = json.dumps(data)
    rolls = [int(m) for m in re.findall(r'\b([1-6])\b', output_str)]
    if not rolls:
        sys.exit(f"FAIL: No dice value (1-6) in output\n{r.stdout[:1000]}")

    print(f"OK: Flow completed, found dice roll = {rolls[0]}")


if __name__ == "__main__":
    main()
