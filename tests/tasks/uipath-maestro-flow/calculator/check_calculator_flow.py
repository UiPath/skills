#!/usr/bin/env python3
"""Run Calculator flow with injected inputs (17, 23) and verify output contains 391."""

import glob
import json
import os
import subprocess
import sys

INPUT_A = 17
INPUT_B = 23
EXPECTED = INPUT_A * INPUT_B  # 391


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

    # Discover input variable names from the .flow file
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit("FAIL: No .flow file found")

    with open(flows[0]) as f:
        flow = json.load(f)

    variables = flow.get("variables", {}) or flow.get("workflow", {}).get("variables", {})
    in_vars = [v["id"] for v in variables.get("globals", []) if v.get("direction") in ("in", "inout")]
    if len(in_vars) < 2:
        sys.exit(f"FAIL: Expected 2+ input variables, found {len(in_vars)}")

    inputs_json = json.dumps({in_vars[0]: INPUT_A, in_vars[1]: INPUT_B})
    print(f"Injecting inputs: {inputs_json}")

    r = subprocess.run(
        ["uip", "flow", "debug", project_dir, "--inputs", inputs_json, "--output", "json"],
        capture_output=True, text=True, timeout=90,
    )
    if r.returncode != 0:
        sys.exit(f"FAIL: flow debug exit {r.returncode}\n{r.stderr[:500]}")

    data = parse_json(r.stdout)
    if data is None:
        sys.exit(f"FAIL: Could not parse JSON\n{r.stdout[:500]}")
    if (data.get("Data") or {}).get("finalStatus") != "Completed":
        sys.exit(f"FAIL: Flow did not complete\n{r.stdout[:1000]}")

    if str(EXPECTED) not in json.dumps(data):
        sys.exit(f"FAIL: Output missing {EXPECTED} ({INPUT_A} * {INPUT_B})\n{r.stdout[:1000]}")

    print(f"OK: Flow completed, output contains {EXPECTED}")


if __name__ == "__main__":
    main()
