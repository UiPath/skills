"""The two contract-intake checkers accept what the product accepts and reject
what it never writes.

Every fixture is built here as a dict and written to tmp_path. None is committed
as a `.flow` file: the checkers glob `**/*.flow`, and this directory is part of
the reference tree an eval run can see.

The fixtures reproduce the shapes of four real artifacts (run archive, row
skill-flow-datafabric-native-contract-intake-pipeline):

- TYPED: the builder SDK's typed four-verb output (6.7.0 source, compiled after
  the SDK stops copying `model` onto Data Fabric nodes): flat `_filters` rows,
  `_sort`, instance `outputs` with the SDK's `{type: 'literal', ...}` source.
- V1: the 2026-09-23 v1 artifact: grouped `_filters`, no instance outputs.
- V2_0923: the 2026-09-23 v2 artifact (rawNode with hand-typed manifests):
  `_sortOptions` instead of `_sort`, instance `model`.
- V2_0918: the 2026-09-18 v2 artifact, which deleted `model` and
  `outputDefinition` from its definitions to satisfy the old rule.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CRUD = HERE / "check_datafabric_native_contract_intake_pipeline.py"
SHAPE = HERE / "check_native_node_shape.py"
FLOW_TASKS = HERE.parents[1]  # tests/tasks/uipath-maestro-flow

ENTITY = "ContractRegistry"
OUTPUT_DESC = {
    "core.datafabric.read": "Entity record queried by this node, or the matching records under \"results\"",
    "core.datafabric.create": "Entity record created by this node",
    "core.datafabric.update": "Entity record after the update",
}


def definition(node_type, version, *, model=True, sections=1, outputs=True):
    """A definitions[] entry reduced to what the checker reads, registry-shaped by default."""
    d = {
        "nodeType": node_type,
        "version": version,
        "runtimeConstraints": {"exclude": ["api-function"]},
        "form": {"id": "entity-properties", "sections": [{"id": f"s{i}"} for i in range(sections)]},
    }
    if model:
        d["model"] = {"type": "bpmn:Task"}
    if outputs and node_type in OUTPUT_DESC:
        d["outputDefinition"] = {"output": {
            "type": "jsonSchema", "description": OUTPUT_DESC[node_type], "source": "=response", "var": "output",
        }}
    return d


def sdk_outputs(node_type):
    """Instance outputs the builder SDK writes: the manifest's, with a wrapped source."""
    return {"output": {
        "type": "jsonSchema", "description": OUTPUT_DESC[node_type],
        "source": {"type": "literal", "expression": "=response", "fieldType": "string"}, "var": "output",
    }}


def node(node_id, node_type, version, config, *, outputs=False, model=False):
    n = {"id": node_id, "type": node_type, "typeVersion": version,
         "inputs": {"entityConfig": {"entityName": ENTITY, **config}}}
    if outputs and node_type in OUTPUT_DESC:
        n["outputs"] = sdk_outputs(node_type)
    if model:
        n["model"] = {"type": "bpmn:Task"}
    return n


def chain(nodes, defs):
    ids = ["start"] + [n["id"] for n in nodes]
    edges = [{"id": f"e{i}", "sourceNodeId": a, "sourcePort": "output", "targetNodeId": b, "targetPort": "input"}
             for i, (a, b) in enumerate(zip(ids, ids[1:]))]
    start = {"id": "start", "type": "core.trigger.manual", "typeVersion": "1.0", "inputs": {}}
    return {"nodes": [start, *nodes], "edges": edges, "definitions": defs}


def crud_nodes(*, versions, filters, sort_cfg, outputs=False, model=False, create_id="create"):
    """Create → Read(single, Id) → Read(multiple, title + sort) → Update(status) → Delete."""
    rid = f"=js:$vars.{create_id}.output.Id"
    c, r, u, d = (f"core.datafabric.{v}" for v in ("create", "read", "update", "delete"))
    kw = {"outputs": outputs, "model": model}
    return [
        node(create_id, c, versions["create"], {"fieldValues": [
            {"field": "contractTitle", "value": "Native Contract Intake"},
            {"field": "status", "value": "Draft"},
            {"field": "priority", "value": "7"},
        ]}, **kw),
        node("readById", r, versions["read"], {"resultMode": "single",
             "_filters": filters([{"field": "Id", "operator": "=", "value": rid}])}, **kw),
        node("readMany", r, versions["read"], {"resultMode": "multiple",
             "_filters": filters([{"field": "contractTitle", "operator": "=", "value": "Native Contract Intake"}]),
             **sort_cfg}, **kw),
        node("update", u, versions["update"], {"recordSource": "byId", "recordId": rid,
             "fieldUpdates": [{"field": "status", "value": "In Review"}]}, **kw),
        node("delete", d, versions["delete"], {"recordSource": "byId", "recordId": rid}, **kw),
    ]


def flat(rows):
    return rows


def grouped(rows):
    return {"logicalOperator": "AND", "rows": rows, "groups": []}


def rows_only(rows):
    return {"rows": rows}


def defs_for(versions, **kw):
    return [definition(f"core.datafabric.{verb}", v, **kw) for verb, v in versions.items()
            if verb != "read"] + [definition("core.datafabric.read", versions["read"], **kw)]


SORT = {"_sort": {"field": "priority", "direction": "desc"}}
TYPED_V = {"create": "1.3", "read": "1.4", "update": "1.0", "delete": "1.3"}
PORTAL_V = {"create": "1.3", "read": "1.4", "update": "1.3", "delete": "1.3"}


def typed():
    return chain(crud_nodes(versions=TYPED_V, filters=flat, sort_cfg=SORT, outputs=True), defs_for(TYPED_V))


def v1_0923():
    return chain(
        crud_nodes(versions=PORTAL_V, filters=grouped,
                   sort_cfg={"_recordLimit": 100, "_skip": 0, **SORT}, create_id="createContract"),
        defs_for(PORTAL_V))


def v2_0923():
    return chain(
        crud_nodes(versions=PORTAL_V, filters=flat,
                   sort_cfg={"_sortOptions": [{"fieldName": "priority", "isDescending": True}]},
                   outputs=True, model=True),
        defs_for(PORTAL_V, sections=0))


def v2_0918():
    return chain(crud_nodes(versions=PORTAL_V, filters=rows_only, sort_cfg=SORT),
                 defs_for(PORTAL_V, model=False, outputs=False))


def run(checker: Path, flow: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    (tmp_path / "Flow.flow").write_text(json.dumps(flow))
    return subprocess.run([sys.executable, str(checker)], cwd=tmp_path, capture_output=True, text=True)


def assert_clean_fail(result: subprocess.CompletedProcess) -> str:
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "Traceback" not in out, out
    assert "FAIL:" in out, out
    return out


# ── product-accepted shapes pass ────────────────────────────────────────────


def test_typed_sdk_flow_passes_both(tmp_path: Path) -> None:
    for checker in (CRUD, SHAPE):
        result = run(checker, typed(), tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr


def test_v1_grouped_filters_flow_passes_both(tmp_path: Path) -> None:
    for checker in (CRUD, SHAPE):
        result = run(checker, v1_0923(), tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr


def test_canvas_spelled_output_source_passes(tmp_path: Path) -> None:
    """The canvas keeps the manifest's plain `'=response'` string."""
    flow = typed()
    for n in flow["nodes"]:
        if "outputs" in n:
            n["outputs"]["output"]["source"] = "=response"
    assert run(SHAPE, flow, tmp_path).returncode == 0


# ── the CRUD checker ────────────────────────────────────────────────────────


def test_sort_options_is_named_not_a_traceback(tmp_path: Path) -> None:
    out = assert_clean_fail(run(CRUD, v2_0923(), tmp_path))
    assert "no multi-record read with priority DESC sort" in out
    assert "`_sortOptions`" in out
    assert "`_sort: {field, direction}`" in out


def test_string_filters_fail_cleanly(tmp_path: Path) -> None:
    flow = typed()
    for n in flow["nodes"]:
        cfg = n["inputs"].get("entityConfig", {})
        if "_filters" in cfg:
            cfg["_filters"] = "Id = x"
    out = assert_clean_fail(run(CRUD, flow, tmp_path))
    assert "no Id filter" in out


def test_id_filter_only_in_a_nested_group_is_found(tmp_path: Path) -> None:
    """The grouped form nests: `groups[].rows` rows count like root rows."""
    flow = typed()
    for n in flow["nodes"]:
        cfg = n["inputs"].get("entityConfig", {})
        if "_filters" in cfg:
            cfg["_filters"] = {"logicalOperator": "AND", "rows": [],
                               "groups": [{"logicalOperator": "AND", "rows": cfg["_filters"], "groups": []}]}
    result = run(CRUD, flow, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_single_read_without_result_mode_counts_as_single(tmp_path: Path) -> None:
    """Read 1.0 writes no resultMode; the platform reads that as single."""
    flow = typed()
    read_one = next(n for n in flow["nodes"] if n["id"] == "readById")
    read_one["typeVersion"] = "1.0"
    del read_one["inputs"]["entityConfig"]["resultMode"]
    flow["definitions"].append(definition("core.datafabric.read", "1.0"))
    for checker in (CRUD, SHAPE):
        result = run(checker, flow, tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr


def test_non_dict_sort_fails_cleanly(tmp_path: Path) -> None:
    flow = typed()
    for n in flow["nodes"]:
        cfg = n["inputs"].get("entityConfig", {})
        if "_sort" in cfg:
            cfg["_sort"] = "priority desc"
    assert "priority DESC" in assert_clean_fail(run(CRUD, flow, tmp_path))


# ── the node-shape checker ──────────────────────────────────────────────────


def test_instance_model_still_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["nodes"][1]["model"] = {"type": "bpmn:Task"}
    out = assert_clean_fail(run(SHAPE, flow, tmp_path))
    assert "carries an instance `model` block" in out


def test_sdk_670_shape_fails_only_on_the_instance_model(tmp_path: Path) -> None:
    """SDK 6.7.0 as shipped: the typed shape plus a model copied onto every node.

    Only the model lines fail. The definitions (registry copies) and the
    outputs (the manifest's) pass, so the row turns green as soon as the SDK
    stops copying `model`, with no second checker change.
    """
    flow = chain(crud_nodes(versions=TYPED_V, filters=flat, sort_cfg=SORT, outputs=True, model=True),
                 defs_for(TYPED_V))
    out = assert_clean_fail(run(SHAPE, flow, tmp_path))
    fails = [line for line in out.splitlines() if "FAIL" in line or "carries" in line]
    assert fails, out
    assert all("instance `model` block" in line for line in fails if "node " in line), out
    assert out.count("instance `model` block") == 5, out
    assert "definitions[]" not in out and "outputs" not in out, out
    assert run(CRUD, flow, tmp_path).returncode == 0


def test_service_task_definition_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["definitions"][0]["model"]["type"] = "bpmn:ServiceTask"
    assert "expected 'bpmn:Task'" in assert_clean_fail(run(SHAPE, flow, tmp_path))


def test_definition_without_api_function_exclude_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["definitions"][0]["runtimeConstraints"] = {"exclude": []}
    assert "lacks 'api-function'" in assert_clean_fail(run(SHAPE, flow, tmp_path))


def test_extra_instance_output_key_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["nodes"][1]["outputs"]["record"] = {"type": "object", "var": "record"}
    out = assert_clean_fail(run(SHAPE, flow, tmp_path))
    assert "['record']" in out


def test_instance_output_var_mismatch_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["nodes"][1]["outputs"]["output"]["var"] = "result"
    assert "outputs.output.var" in assert_clean_fail(run(SHAPE, flow, tmp_path))


def test_delete_with_outputs_fails(tmp_path: Path) -> None:
    flow = typed()
    delete = next(n for n in flow["nodes"] if n["type"] == "core.datafabric.delete")
    delete["outputs"] = sdk_outputs("core.datafabric.create")
    assert "declares no output" in assert_clean_fail(run(SHAPE, flow, tmp_path))


def test_definitions_without_form_pass(tmp_path: Path) -> None:
    """Two scored v1 runs (nightly 2026-09-21, adhoc 2026-09-22 v1) wrote
    definitions with `model`, `outputDefinition` and `runtimeConstraints` but no
    `form`. The canvas falls back to the registry's form (conversion.ts:196), so
    a missing or empty form is not a defect."""
    flow = typed()
    for d in flow["definitions"]:
        d.pop("form", None)
    flow["definitions"][1]["form"] = {"id": "entity-properties", "sections": []}
    result = run(SHAPE, flow, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_0923_rawnode_manifests_fail(tmp_path: Path) -> None:
    out = assert_clean_fail(run(SHAPE, v2_0923(), tmp_path))
    assert "carries an instance `model` block" in out


def test_v2_0918_stripped_definitions_fail(tmp_path: Path) -> None:
    """Passed the old rule: it deleted `model`/`outputDefinition` from definitions[]."""
    out = assert_clean_fail(run(SHAPE, v2_0918(), tmp_path))
    assert "model.type is None" in out
    assert "outputDefinition is missing" in out


def test_error_port_edge_fails(tmp_path: Path) -> None:
    flow = typed()
    flow["edges"].append({"id": "err", "sourceNodeId": "update", "sourcePort": "error",
                          "targetNodeId": "delete", "targetPort": "input"})
    assert "sourcePort: \"error\"" in assert_clean_fail(run(SHAPE, flow, tmp_path))


# ── one filter walker ───────────────────────────────────────────────────────


def test_no_checker_parses_filters_outside_shared() -> None:
    """`_filters` has two product shapes; only `_shared.native_filter_rows` reads both.

    A checker that re-implements the parse is how a flat row list crashed
    this row's grading with a traceback.
    """
    access = re.compile(r"""\.get\(\s*["']_filters["']|\[\s*["']_filters["']\s*\]""")
    offenders = [
        str(p.relative_to(FLOW_TASKS))
        for p in FLOW_TASKS.rglob("check_*.py")
        if "_shared" not in p.parts and access.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == [], offenders

