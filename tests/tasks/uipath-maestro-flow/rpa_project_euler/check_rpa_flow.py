#!/usr/bin/env python3
"""Run ProjectEulerTitle flow and verify output contains 'prime square remainders'."""

import glob
import json
import os
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
        capture_output=True, text=True, timeout=240,
    )
    if r.returncode != 0:
        sys.exit(f"FAIL: flow debug exit {r.returncode}\n{r.stderr[:500]}")

    data = parse_json(r.stdout)
    if data is None:
        sys.exit(f"FAIL: Could not parse JSON\n{r.stdout[:500]}")
    if (data.get("Data") or {}).get("finalStatus") != "Completed":
        sys.exit(f"FAIL: Flow did not complete\n{r.stdout[:1000]}")

    if "prime square remainders" not in json.dumps(data).lower():
        sys.exit(f"FAIL: Output missing 'prime square remainders'\n{r.stdout[:1000]}")

    print("OK: Flow completed, output contains 'prime square remainders'")


if __name__ == "__main__":
    main()
