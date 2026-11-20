from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
FLOW_TASKS = SHARED.parent
INVOICE_LOOKUP_REFERENCE = "multi_node/billing_invoice_lookup/BillingInvoiceLookup.reference.flow"
NATIVE_DISPUTE_REFERENCE = "multi_node/billing_dispute_resolution/BillingDisputeResolution.native.reference.flow"


def run_script(script: str, *args: Path | str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SHARED / script), *(str(arg) for arg in args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_server_side_filter_rejects_a_row_with_no_predicate(tmp_path: Path) -> None:
    """`rows: [{}]` is a non-empty list the serializer emits nothing from, so
    list non-emptiness is not the question."""
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    flow = _native_flow()
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_filters"] = {"logicalOperator": "AND", "rows": [{}], "groups": []}
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode != 0
    assert "no server-side filter" in result.stdout + result.stderr


def test_entity_read_shapes_match_the_structural_gates() -> None:
    """Two discriminators describe the same two shapes: this module's for the
    advisories, `flow_check.ENTITY_QUERY_HINTS` for the structural gates. A
    comment asking to "keep the two in step" is not a guard."""
    sys.path.insert(0, str(SHARED))
    import advisory_flow_utils
    import flow_check

    hints = flow_check.ENTITY_QUERY_HINTS
    assert len(hints) == 2, hints
    assert advisory_flow_utils.NATIVE_READ_TYPE in hints
    connector_type = advisory_flow_utils.CONNECTOR_READ_PREFIX + "query-entity-records"
    assert any(hint in connector_type for hint in hints), (hints, connector_type)


def test_preview_query_node_reads_the_tenant_entity() -> None:
    """Round-11 shape: the preview op ends in `-preview-` and names its entity in
    `queryParameters.tenantEntityName`, with no `pathParameters`."""
    sys.path.insert(0, str(SHARED))
    import advisory_flow_utils as utils

    prefix = utils.CONNECTOR_READ_PREFIX
    erp = {
        "id": "erpLookup",
        "type": prefix + "query-entity-records",
        "inputs": {"detail": {
            "endpoint": "/v2/{entityName}/qer",
            "pathParameters": {"entityName": "BillingDisputeERP"},
            "queryParameters": {"limit": 1},
        }},
    }
    crm = {
        "id": "crmLookup",
        "type": prefix + "query-entity-records-preview-",
        "inputs": {"detail": {
            "endpoint": "/v3/QueryEntityRecords/query",
            "bodyParameters": {},
            "queryParameters": {
                "entityScope": "tenant",
                "tenantEntityName": "BillingDisputeCRM",
                "limit": 1,
            },
        }},
    }
    write = {"id": "w", "type": prefix + "create-entity-record", "inputs": {}}

    shape, reads = utils.entity_reads([erp, crm, write])

    assert shape == utils.CONNECTOR_READ
    assert [node["id"] for node in reads] == ["erpLookup", "crmLookup"]
    assert [utils.entity_name(node, shape) for node in reads] == [
        "BillingDisputeERP",
        "BillingDisputeCRM",
    ]


def test_bindings_checker_accepts_a_valid_connection_pair(tmp_path: Path) -> None:
    flow = json.loads((FLOW_TASKS / INVOICE_LOOKUP_REFERENCE).read_text())
    cwd = _project(tmp_path, flow, CONNECTION_BINDINGS, "BillingInvoiceLookup")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "(connector)" in result.stdout


def _project(tmp_path: Path, flow: dict, bindings: dict, name: str) -> Path:
    """A generated-solution tree as the two billing checkers walk it: one flow
    and one bindings file under the cwd they are run from."""
    project = tmp_path / "proj"
    project.mkdir(parents=True, exist_ok=True)
    (project / f"{name}.flow").write_text(json.dumps(flow))
    (project / "bindings_v2.json").write_text(json.dumps(bindings))
    return tmp_path


def _native_flow() -> dict:
    return json.loads((FLOW_TASKS / NATIVE_DISPUTE_REFERENCE).read_text())


CONNECTION_BINDINGS = {
    "version": "2.0",
    "resources": [
        {
            "resource": "connection",
            "key": "data-fabric",
            "value": {
                "ConnectionId": {"defaultValue": "d61e5d0e-04af-4f93-95cc-151d81fa08dc"},
                "FolderKey": {"defaultValue": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c"},
            },
        }
    ],
}
# What a native build actually writes: resources for the IxP model, the API
# workflow and the context index, and no `connection` row at all. Named for what
# it lacks, because the connector cases below reuse it to mean "the row is gone".
NON_CONNECTION_BINDINGS = {
    "version": "2.0",
    "resources": [
        {"resource": "process", "key": "p", "value": {"name": {"defaultValue": "FinancialPostingFunction"}}}
    ],
}


def test_bindings_checker_accepts_a_native_build_with_no_connection(tmp_path: Path) -> None:
    """A flow whose only external calls are native reads has no Integration
    Service connection to bind, so `declares no bindings at all` is wrong there."""
    cwd = _project(tmp_path, _native_flow(), NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no connection to bind" in result.stdout


def test_bindings_checker_accepts_a_native_build_with_no_bindings_file(tmp_path: Path) -> None:
    """What an eval actually produced. A pure Data Fabric flow
    references no packaged resource, so the CLI writes no bindings file at all,
    and both native billing tasks died on `assert candidates` one line before the
    connection check could apply. The fixture that supplied an empty-of-
    connections file did not reproduce this: that shape never occurs."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / "BillingInvoiceLookup.flow").write_text(json.dumps(_native_flow()))

    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no bindings file, and no connector node that needs one" in result.stdout


def test_bindings_checker_requires_a_file_for_a_connector_build(tmp_path: Path) -> None:
    """The other half: a connector flow with no bindings file at all is the
    missing-connection regression, not a native build."""
    project = tmp_path / "proj"
    project.mkdir()
    flow = json.loads((FLOW_TASKS / INVOICE_LOOKUP_REFERENCE).read_text())
    (project / "BillingInvoiceLookup.flow").write_text(json.dumps(flow))

    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode != 0
    assert "carries a connector node that needs one" in result.stdout + result.stderr


def test_bindings_checker_fails_when_it_finds_no_flow(tmp_path: Path) -> None:
    """Relaxing the bindings-file requirement must not let a checker that ran in
    the wrong tree report success on an empty directory."""
    result = run_script("check_bindings_no_stubs.py", cwd=tmp_path)
    assert result.returncode != 0
    assert "neither a generated bindings file nor a .flow" in result.stdout + result.stderr


def test_bindings_checker_still_requires_one_for_a_connector_build(tmp_path: Path) -> None:
    """The regression the check exists for: a connector build that dropped its
    connection row deploys and faults with [102010]."""
    flow = json.loads((FLOW_TASKS / INVOICE_LOOKUP_REFERENCE).read_text())
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingInvoiceLookup")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode != 0
    assert "declares no bindings at all" in result.stdout + result.stderr


def test_bindings_checker_rejects_a_stub_connection_on_a_native_build(tmp_path: Path) -> None:
    """Zero connection rows is fine; a row that is there and wrong is not."""
    stub = json.loads(json.dumps(CONNECTION_BINDINGS))
    stub["resources"][0]["value"]["ConnectionId"]["defaultValue"] = "00000000-0000-0000-0000-000000000001"
    cwd = _project(tmp_path, _native_flow(), stub, "BillingDisputeResolution")

    result = run_script("check_bindings_no_stubs.py", cwd=cwd)
    assert result.returncode != 0
    assert "stub or empty bindings" in result.stdout + result.stderr


def test_server_side_filter_accepts_native_rows(tmp_path: Path) -> None:
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    cwd = _project(tmp_path, _native_flow(), NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_server_side_filter_rejects_an_empty_native_filter(tmp_path: Path) -> None:
    """The `_filters` container is always present, so its emptiness is what
    separates a server-side filter from fetching the entity whole."""
    checker = FLOW_TASKS / "multi_node/billing_invoice_lookup/check_server_side_filter.py"
    flow = _native_flow()
    for node in flow["nodes"]:
        config = (node.get("inputs") or {}).get("entityConfig")
        if config:
            config["_filters"] = {"logicalOperator": "AND", "rows": [], "groups": []}
    cwd = _project(tmp_path, flow, NON_CONNECTION_BINDINGS, "BillingDisputeResolution")

    result = subprocess.run(
        [sys.executable, str(checker)], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode != 0
    assert "no server-side filter" in result.stdout + result.stderr


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


def test_bindings_checker_prefers_solution_flow_over_root_scratch(tmp_path: Path) -> None:
    checker = FLOW_TASKS / "bindings" / "check_bindings.py"
    project = tmp_path / "BindingsMulti" / "BindingsMulti"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    good = {"nodes": [], "bindings": []}
    (project / "BindingsMulti.flow").write_text(json.dumps(good))
    (tmp_path / "BindingsMulti.flow").write_text(json.dumps({"nodes": []}))

    result = subprocess.run(
        [sys.executable, str(checker), "structure", "**/BindingsMulti*.flow"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert str(project.relative_to(tmp_path)) in result.stdout


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


def test_inline_agent_scoped_checks_preserve_artifact_outcomes(tmp_path: Path) -> None:
    agent = tmp_path / "agent-id" / "agent.json"
    agent.parent.mkdir()
    agent.write_text(json.dumps({"settings": {"model": "gpt-4.1"}}))

    exists = run_script(
        "check_inline_agent.py", "--check", "exists", "**/agent.json", cwd=tmp_path
    )
    model = run_script(
        "check_inline_agent.py", "--check", "model", "**/agent.json", cwd=tmp_path
    )

    assert exists.returncode == 0, exists.stdout + exists.stderr
    assert model.returncode == 0, model.stdout + model.stderr


def test_inline_agent_model_scope_rejects_scaffold_default(tmp_path: Path) -> None:
    agent = tmp_path / "agent-id" / "agent.json"
    agent.parent.mkdir()
    agent.write_text(json.dumps({"settings": {"model": "gpt-4o-2024-11-20"}}))

    result = run_script(
        "check_inline_agent.py", "--check", "model", "**/agent.json", cwd=tmp_path
    )

    assert result.returncode != 0
    assert "not overridden" in result.stdout
