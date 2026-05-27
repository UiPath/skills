#!/usr/bin/env python3
"""Inject MISSING_OUTPUT_SCHEMA violation: strip
entry-points.json.entryPoints[0].output.properties to {}. The catalog
rule fires when the runtime output contract has no properties, leaving
downstream consumers nothing to bind to.

agent-builder layout: entry-points.json is the runtime contract.
We also strip agent.json.outputSchema.properties so the two files
remain in sync (avoids accidentally triggering LOWCODE_SCHEMA_DRIFT
alongside this rule).
"""

import json
from pathlib import Path

AGENT_JSON = Path("ReviewSol/SampleAgent/agent.json")
ENTRY_POINTS = Path("ReviewSol/SampleAgent/entry-points.json")


def main() -> None:
    # Strip entry-points.json output.properties to {}
    ep = json.loads(ENTRY_POINTS.read_text())
    entries = ep.get("entryPoints") or []
    if not entries:
        raise SystemExit("Pre-condition: entry-points.json.entryPoints is empty")
    output = entries[0].setdefault("output", {"type": "object", "properties": {}})
    output["properties"] = {}
    if "required" in output:
        output["required"] = []
    ENTRY_POINTS.write_text(json.dumps(ep, indent=2))

    # Mirror in agent.json so the two files stay in sync (the test is
    # targeting MISSING_OUTPUT_SCHEMA, not LOWCODE_SCHEMA_DRIFT).
    agent = json.loads(AGENT_JSON.read_text())
    out_schema = agent.setdefault(
        "outputSchema", {"type": "object", "properties": {}}
    )
    out_schema["properties"] = {}
    if "required" in out_schema:
        out_schema["required"] = []
    AGENT_JSON.write_text(json.dumps(agent, indent=2))

    print(
        "Stripped outputSchema.properties to {} in both agent.json and "
        "entry-points.json — triggers MISSING_OUTPUT_SCHEMA"
    )


if __name__ == "__main__":
    main()
