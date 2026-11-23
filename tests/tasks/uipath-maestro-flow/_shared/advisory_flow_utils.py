#!/usr/bin/env python3
"""Entity-read and agent-node helpers shared by the Flow graders."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

EXCLUDED_GENERATED_PARTS = {
    ".cli-stage",
    ".git",
    ".v1stage",
    "_lib",
    "_outputs",
    "example",
    "fixtures",
    "node_modules",
    "references",
    "v1stage",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def unwrap(value: Any) -> Any:
    if isinstance(value, dict):
        for key in ("expression", "source"):
            if key in value:
                return unwrap(value[key])
    return value


def load_flow(expected_name: str) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    """Load an explicit Flow path or find exactly one generated Flow by name."""
    if len(sys.argv) > 2:
        fail(f"usage: {Path(sys.argv[0]).name} [{expected_name}]")

    if len(sys.argv) == 2:
        path = Path(sys.argv[1])
        if not path.is_file():
            fail(f"Flow path does not name a file: {path}")
    else:
        cwd = Path.cwd()
        candidates = sorted(
            path
            for path in cwd.rglob(expected_name)
            if not EXCLUDED_GENERATED_PARTS.intersection(path.relative_to(cwd).parts)
        )
        if not candidates:
            # Studio Web names the main file `new.flow` inside a project named for the flow.
            candidates = sorted(
                path
                for path in cwd.rglob("new.flow")
                if path.parent.name == Path(expected_name).stem
                and not EXCLUDED_GENERATED_PARTS.intersection(path.relative_to(cwd).parts)
            )
        if len(candidates) != 1:
            fail(
                f"expected exactly one generated {expected_name}, found {len(candidates)}: "
                f"{[str(path) for path in candidates]}"
            )
        path = candidates[0]

    try:
        flow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read {path}: {error}")
    if not isinstance(flow, dict):
        fail(f"{path} is not a JSON object")
    nodes = flow.get("nodes")
    if not isinstance(nodes, list):
        fail(f"{path} has no nodes array")
    return path, flow, nodes


# ── entity reads: two shapes, tenant availability decides which ──────────────
# The `uipath-uipath-dataservice` connector activity and the native
# `core.datafabric.read` node both read entity records. The native flags default
# to off, so the connector is the working path until `registry get` proves
# otherwise; where the tenant does have them the native node is "the better
# build" (data-fabric/planning.md — Native node vs Data Service connector).
# `flow_check.ENTITY_QUERY_HINTS` gates the same two shapes for the non-advisory
# checkers; keep the two in step.
CONNECTOR_READ = "connector"
NATIVE_READ = "native"
CONNECTOR_NODE_PREFIX = "uipath.connector."
CONNECTOR_READ_PREFIX = f"{CONNECTOR_NODE_PREFIX}uipath-uipath-dataservice."
NATIVE_READ_TYPE = "core.datafabric.read"
# The connector operations that READ. The prefix above covers the whole Data
# Service family, writes included, and each native op has its own tenant flag
# (planning.md — Node types), so `read-entity` on with `create-entity` off is a
# real configuration: a native read beside a connector write. Only a connector
# READ alongside a native one is a flow with two sets of the same reads. Matched
# as a prefix: `query-entity-records-preview-` is the same read, and names its
# entity in `queryParameters.tenantEntityName` instead of `pathParameters`.
CONNECTOR_READ_OPS = (".query-entity-records", ".get-entity-record-by-id")


def _is_read_op(node_type: str) -> bool:
    operation = node_type[len(CONNECTOR_READ_PREFIX):]
    return f".{operation}".startswith(CONNECTOR_READ_OPS)


def entity_config(node: dict[str, Any]) -> dict[str, Any]:
    """The native read's single input container (data-fabric/impl.md)."""
    config = (node.get("inputs") or {}).get("entityConfig")
    return config if isinstance(config, dict) else {}


def read_detail(node: dict[str, Any]) -> dict[str, Any]:
    """The connector activity's `detail` envelope."""
    detail = (node.get("inputs") or {}).get("detail")
    return detail if isinstance(detail, dict) else {}


def entity_reads(nodes: Iterable[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Return ``(shape, reads)`` for the nodes that read entity records."""
    nodes = list(nodes)
    connector = [
        node for node in nodes
        if str(node.get("type") or "").startswith(CONNECTOR_READ_PREFIX)
        and _is_read_op(str(node.get("type") or ""))
    ]
    native = [node for node in nodes if str(node.get("type") or "") == NATIVE_READ_TYPE]
    if connector and native:
        fail(
            f"the flow mixes both entity-read shapes — connector "
            f"{[node.get('id') for node in connector]} and native "
            f"{[node.get('id') for node in native]}. Availability decides one shape per "
            f"flow; two means one set of reads was left behind"
        )
    return (NATIVE_READ, native) if native else (CONNECTOR_READ, connector)


def entity_name(node: dict[str, Any], shape: str) -> str:
    """The entity a read addresses. Fails naming the slot the name belongs in."""
    if shape == NATIVE_READ:
        config = entity_config(node)
        name = str(unwrap(config.get("entityName")) or "").strip()
        if not name:
            fail(
                f"read node {node.get('id')!r} sets no `inputs.entityConfig.entityName`; "
                f"entityConfig keys: {sorted(config)}"
            )
        return name

    detail = read_detail(node)
    path = {key: unwrap(value) for key, value in (detail.get("pathParameters") or {}).items()}
    query = {key: unwrap(value) for key, value in (detail.get("queryParameters") or {}).items()}
    if "entityName" not in path and str(query.get("tenantEntityName") or "").strip():
        return str(query["tenantEntityName"]).strip()
    if "entityName" not in path:
        fail(
            f"query node {node.get('id')!r} has pathParameters {sorted(path)}; `entityName` "
            f"belongs in the PATH slot — it is the {{entityName}} of /v2/{{entityName}}/qer. "
            f"queryParameters: {sorted(query)}"
        )
    return str(path["entityName"]).strip()


def native_filter_rows(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Root filter rows plus every nested group's rows (impl.md — Filters)."""

    def walk(block: Any) -> Iterable[dict[str, Any]]:
        if isinstance(block, list):  # the legacy bare-array form, still read
            yield from (row for row in block if isinstance(row, dict))
            return
        if not isinstance(block, dict):
            return
        yield from (row for row in (block.get("rows") or []) if isinstance(row, dict))
        for group in block.get("groups") or []:
            yield from walk(group)

    return list(walk(entity_config(node).get("_filters")))


