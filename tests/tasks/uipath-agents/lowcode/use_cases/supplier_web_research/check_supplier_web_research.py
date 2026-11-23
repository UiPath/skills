#!/usr/bin/env python3
"""Supplier web research — web-search researcher agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync. Inputs, checked structurally (names
     are the agent's choice): at least three inputs (supplier name, country,
     website), at least one required and at least two optional, every input
     templated. Which input plays which role is left to the LLM judge.
  2. An Integration Service tool on connector `uipath-uipath-airdk` (UiPath
     GenAI Activities) whose activity is Web Search, passing the Studio Web
     silent-drop rules, with the activity's array output kept under the
     literal `results[*]` key.
  3. The solution provisions a GenAI Activities connection resource.
  4. Output contract: companyOverview, recentNews (array), riskFlags (array
     of objects with at least three fields: type, description, source URL;
     which field holds the URL is left to the LLM judge), overallRisk enum
     {low, medium, high, unknown}, sources (array).
  Brownfield: the agent must be built inside the existing (fixture) project.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_existing_project,
    assert_autonomous,
    assert_connection_provisioned,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_integration_wiring,
    assert_project_id,
    assert_schema_sync,
    fail,
    is_integration_tool,
    load,
    require_resource,
    walk_properties,
)


def _inputs(in_schema: dict) -> dict:
    return {k: v for k, v in (in_schema.get("properties") or {}).items() if isinstance(v, dict)}


SOLUTION_DIR = Path(os.getcwd()) / "SupplierResearchSol"
AGENT_DIR = SOLUTION_DIR / "SupplierResearchAgent"
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "SupplierResearchSol" / "SupplierResearchAgent"
CONNECTOR = "uipath-uipath-airdk"


def check_web_search_tool() -> None:
    _, tool = require_resource(
        AGENT_DIR,
        is_integration_tool(CONNECTOR, lambda o: "websearch" in o.lower()),
        "GenAI Web Search IS tool",
    )
    assert_integration_wiring(tool)
    out_props = (tool.get("outputSchema") or {}).get("properties") or {}
    if "results[*]" not in out_props:
        fail(
            "Web Search tool outputSchema must keep the literal 'results[*]' key from the "
            f"activity metadata (Studio Web drops renamed keys); got {sorted(out_props)}"
        )
    print("OK: Web Search tool keeps the literal results[*] output key")


def check_inputs(in_schema: dict) -> list[str]:
    ins = _inputs(in_schema)
    if len(ins) < 3:
        fail(f"inputSchema must declare the supplier name, country and website (>=3 inputs), found {sorted(ins)}")
    required = [r for r in in_schema.get("required") or [] if r in ins]
    if not required or len(ins) - len(required) < 2:
        fail(f"the supplier name is required and country/website optional: expected >=1 required and >=2 optional inputs, required={required}")
    print(f"OK: inputs {sorted(ins)}; required {required}, the rest optional")
    return list(ins)


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "companyOverview": ["overview"],
            "recentNews": ["news"],
            "riskFlags": ["redFlags"],
            "overallRisk": ["riskLevel"],
            "sources": ["sourceUrls"],
        },
    )
    for name in ("recentNews", "riskFlags", "sources"):
        if f[name].get("type") != "array":
            fail(f"{name} must be an array, got {f[name]!r}")
    assert_enum(f["overallRisk"], "overallRisk", ["low", "medium", "high", "unknown"])
    flag_props = walk_properties({"type": "object", "properties": {"x": f["riskFlags"]}, "definitions": out_schema.get("definitions") or {}})
    if len(flag_props) < 3:
        fail(f"riskFlags items must carry a type, a description and a source URL (>=3 fields); found {sorted(flag_props)}")
    print(f"OK: list fields are arrays and each risk flag has {len(flag_props)} fields {sorted(flag_props)}")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_inputs_referenced(agent, check_inputs(in_schema))
    check_web_search_tool()
    assert_connection_provisioned(SOLUTION_DIR, CONNECTOR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
