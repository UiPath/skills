#!/usr/bin/env python3
"""Run SlackChannelDescription flow and verify output contains the Bellevue office address."""

import glob
import json
import os
import subprocess
import sys

ADDRESS_FRAGMENTS = [
    "700 Bellevue Way NE",
    "Suite 2000",
    "Bellevue",
    "WA 98004",
]


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

    output_text = json.dumps(data).lower()
    missing = [f for f in ADDRESS_FRAGMENTS if f.lower() not in output_text]
    if missing:
        sys.exit(f"FAIL: Output missing address fragments: {missing}\n{r.stdout[:1000]}")

    print("OK: Channel description contains Bellevue office address")


if __name__ == "__main__":
    main()
