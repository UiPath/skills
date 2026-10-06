#!/usr/bin/env python3
"""Supplier web research — web-search researcher agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync; supplierName / country / website
     inputs templated (supplierName required).
  2. An Integration Service tool on connector `uipath-uipath-airdk` (UiPath
     GenAI Activities) whose activity is Web Search, passing the Studio Web
     silent-drop rules, with the activity's array output kept under the
     literal `results[*]` key.
  3. The solution provisions a GenAI Activities connection resource.
  4. Output contract: companyOverview, recentNews (array), riskFlags (array
     of objects carrying a source URL), overallRisk enum
     {low, medium, high, unknown}, sources (array).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_autonomous,
    assert_connection_provisioned,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_integration_wiring,
    assert_project_id,
    assert_schema_sync,
    fail,
    find_property,
    is_integration_tool,
    load,
    require_resource,
    walk_properties,
)

SOLUTION_DIR = Path(os.getcwd()) / "SupplierResearchSol"
AGENT_DIR = SOLUTION_DIR / "SupplierResearchAgent"
CONNECTOR = "uipath-uipath-airdk"
INPUTS = ["supplierName", "country", "website"]


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


def check_inputs(in_schema: dict) -> None:
    assert_has_fields(in_schema, "inputSchema", {f: [] for f in INPUTS})
    if "supplierName" not in (in_schema.get("required") or []):
        fail("supplierName must be a required input")
    print("OK: supplierName is required")


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
    if find_property(flag_props, "sourceUrl", "url", "source") is None:
        fail(f"riskFlags items must carry the source URL; item fields found: {sorted(flag_props)}")
    print("OK: list fields are arrays and each risk flag carries a source URL")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    check_inputs(in_schema)
    assert_inputs_referenced(agent, INPUTS)
    check_web_search_tool()
    assert_connection_provisioned(SOLUTION_DIR, CONNECTOR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
