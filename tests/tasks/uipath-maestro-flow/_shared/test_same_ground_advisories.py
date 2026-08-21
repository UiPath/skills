from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent
FLOW_TASKS = SHARED.parent
REFERENCE_CASES = {
    "advisory_billing_invoice_lookup.py": (
        "multi_node/billing_invoice_lookup/BillingInvoiceLookup.reference.flow"
    ),
    "advisory_billing_discrepancy_detector.py": (
        "multi_node/billing_discrepancy_detector/BillingDiscrepancyDetector.reference.flow"
    ),
    "advisory_billing_dispute_analyst.py": (
        "multi_node/billing_dispute_analyst/BillingDisputeAnalyst.reference.flow"
    ),
    "advisory_billing_resolution_writer.py": (
        "multi_node/billing_resolution_writer/BillingResolutionWriter.reference.flow"
    ),
    "advisory_billing_dispute_resolution.py": (
        "multi_node/billing_dispute_resolution/BillingDisputeResolution.reference.flow"
    ),
}


def run_script(script: str, *args: Path | str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SHARED / script), *(str(arg) for arg in args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(("script", "relative_flow"), REFERENCE_CASES.items())
def test_advisories_accept_repo_reference_flows(script: str, relative_flow: str) -> None:
    result = run_script(script, FLOW_TASKS / relative_flow)
    assert result.returncode == 0, result.stdout + result.stderr


def test_literal_scan_ignores_canvas_descriptions_and_uuid_segments(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_discrepancy_detector.py"]
    flow = json.loads(source.read_text())
    flow["nodes"][0]["position"] = {"x": 1610, "y": 4200}
    flow["nodes"][0]["description"] = "Enterprise-tier customers"
    for node in flow["nodes"]:
        detail = (node.get("inputs") or {}).get("detail")
        if detail:
            detail["connectionId"] = "3f2a91cc-1610-4b7e-a111-123456789abc"
    target = tmp_path / "BillingDiscrepancyDetector.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_discrepancy_detector.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_multi_end_error_binding_does_not_override_success_binding(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_resolution_writer.py"]
    flow = json.loads(source.read_text())
    flow["nodes"].append(
        {
            "id": "errorEnd",
            "type": "core.control.end",
            "outputs": {"emailSubject": "failed", "emailBody": "failed"},
        }
    )
    flow["edges"].append(
        {
            "sourceNodeId": "resolutionWriter",
            "sourcePort": "error",
            "targetNodeId": "errorEnd",
            "targetPort": "input",
        }
    )
    target = tmp_path / "BillingResolutionWriter.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_resolution_writer.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_output_provenance_follows_multiple_reader_hops(tmp_path: Path) -> None:
    source = FLOW_TASKS / REFERENCE_CASES["advisory_billing_invoice_lookup.py"]
    flow = json.loads(source.read_text())
    end = next(node for node in flow["nodes"] if node.get("type") == "core.control.end")
    flow["nodes"].extend(
        [
            {"id": "format1", "type": "core.action.script", "inputs": {"value": "$vars.erpQuery.output"}},
            {"id": "format2", "type": "core.action.script", "inputs": {"value": "$vars.format1.output"}},
        ]
    )
    for output in end["outputs"].values():
        output["source"] = {
            "type": "jsExpression",
            "expression": "$vars.format2.output.value",
            "fieldType": "string",
        }
    flow["edges"] = [
        edge
        for edge in flow["edges"]
        if not (edge.get("sourceNodeId") == "erpQuery" and edge.get("targetNodeId") == end["id"])
    ]
    flow["edges"].extend(
        [
            {"sourceNodeId": "erpQuery", "sourcePort": "success", "targetNodeId": "format1"},
            {"sourceNodeId": "format1", "sourcePort": "success", "targetNodeId": "format2"},
            {"sourceNodeId": "format2", "sourcePort": "success", "targetNodeId": end["id"]},
        ]
    )
    target = tmp_path / "BillingInvoiceLookup.flow"
    target.write_text(json.dumps(flow))

    result = run_script("advisory_billing_invoice_lookup.py", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_bindings_checker_uses_relative_exclusions_and_rejects_any_bad_key(tmp_path: Path) -> None:
    cwd = tmp_path / "sdk"
    project = cwd / "project"
    project.mkdir(parents=True)
    bindings = project / "bindings.json"
    bindings.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "id": "connection",
                        "resource": "connection",
                        "resourceKey": "DataFabricConn",
                        "default": "00000000-0000-0000-0000-000000000001",
                    }
                ]
            }
        )
    )
    bad = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert bad.returncode != 0
    assert "connection" in bad.stdout + bad.stderr

    bindings.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "id": "connection",
                        "resource": "connection",
                        "resourceKey": "d61e5d0e-04af-4f93-95cc-151d81fa08dc",
                        "default": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c",
                    }
                ]
            }
        )
    )
    good = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert good.returncode == 0, good.stdout + good.stderr


def test_bindings_checker_accepts_v2_symbolic_key_with_real_values(tmp_path: Path) -> None:
    bindings = tmp_path / "bindings_v2.json"
    bindings.write_text(
        json.dumps(
            {
                "resources": [
                    {
                        "resource": "connection",
                        "key": "data-fabric",
                        "value": {
                            "ConnectionId": {"defaultValue": "d61e5d0e-04af-4f93-95cc-151d81fa08dc"},
                            "FolderKey": {"defaultValue": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c"},
                        },
                    }
                ]
            }
        )
    )
    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_inline_agent_ignores_staging_trees(tmp_path: Path) -> None:
    valid = {
        "settings": {"model": "gpt-4.1"},
        "messages": [{"role": "system", "content": "A sufficiently detailed production system prompt for this agent."}],
        "outputSchema": {"properties": {"result": {"type": "string"}}},
    }
    real = tmp_path / "Solution" / "Flow" / "agent-id" / "agent.json"
    real.parent.mkdir(parents=True)
    real.write_text(json.dumps(valid))
    for stale_root in (tmp_path / ".agent-builder", tmp_path / "_outputs"):
        stale_root.mkdir()
        (stale_root / "agent.json").write_text("{}")

    result = run_script("check_inline_agent.py", "**/agent.json", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Solution" in result.stdout
