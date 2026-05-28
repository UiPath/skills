#!/usr/bin/env python3
"""Scaffold a lowcode agent and inject LOWCODE_SCHEMA_DRIFT.

Adds an input property `drifted_field` to agent.json.inputSchema WITHOUT
updating entry-points.json. Studio Web uses entry-points.json as the
runtime contract, so the two files disagreeing is a deployment-breaker.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from lowcode_scaffold import write_baseline_lowcode_agent  # noqa: E402

SOLUTION = Path("ReviewSol")
FIELD = "drifted_field"


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)

    agent_path = project / "agent.json"
    d = json.loads(agent_path.read_text(encoding="utf-8"))
    schema = d["inputSchema"]
    schema["properties"][FIELD] = {
        "type": "string",
        "title": "Drifted Field",
        "description": (
            "Test fixture: in agent.json only, NOT entry-points.json — "
            "triggers LOWCODE_SCHEMA_DRIFT."
        ),
    }
    if FIELD not in schema.get("required", []):
        schema.setdefault("required", []).append(FIELD)
    agent_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"Injected {FIELD!r} into agent.json only — LOWCODE_SCHEMA_DRIFT")


if __name__ == "__main__":
    main()
