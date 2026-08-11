#!/usr/bin/env python3
"""Shared parsing helpers for the same-ground Flow advisory checkers."""

from __future__ import annotations

import json
import re
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
UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STUB_UUID = re.compile(r"^0{8}-0{4}-0{4}-0{4}-")
VAR_REF = re.compile(r"\$vars\.([A-Za-z_$][\w$]*)")
FILTER_REF = re.compile(r"\{([A-Za-z_$][\w$]*)\}")
FAILED_PORTS = {"error", "failed", "failure", "faulted"}
SKIPPED_VALUE_KEYS = {
    "configuration",
    "description",
    "displayName",
    "entryPointId",
    "label",
    "position",
    "size",
    "telemetryData",
    "uiPathActivityTypeId",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def unwrap(value: Any) -> Any:
    if isinstance(value, dict):
        for key in ("expression", "source"):
            if key in value:
                return unwrap(value[key])
    return value


def is_real_uuid(value: Any) -> bool:
    rendered = str(value or "").strip()
    return bool(UUID.fullmatch(rendered)) and not STUB_UUID.match(rendered)


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


def value_refs(value: Any) -> set[str]:
    return set(VAR_REF.findall(json.dumps(value, sort_keys=True)))


def node_dependencies(nodes: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    return {
        str(node.get("id")): value_refs(node.get("inputs") or {})
        for node in nodes
        if node.get("id")
    }


def source_depends_on(value: Any, producer: str, dependencies: dict[str, set[str]]) -> bool:
    """Follow exact `$vars.<node>` references through any number of reader nodes."""
    pending = list(value_refs(value))
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == producer:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(dependencies.get(current, ()))
    return False


def references_field(value: Any, field: str) -> bool:
    rendered = str(unwrap(value) or "")
    return bool(re.search(rf"(?:^|\.){re.escape(field)}(?:$|[^\w$])", rendered))


def query_references_input(detail: dict[str, Any], field: str) -> bool:
    """Accept direct `$vars` filters and v1's `{var_*}` + filterVariables form."""
    query = unwrap((detail.get("queryParameters") or {}).get("queryExpression"))
    rendered = str(query or "")
    if "$vars." in rendered and references_field(rendered, field):
        return True
    filter_variables = detail.get("filterVariables") or {}
    return any(
        placeholder in filter_variables and references_field(filter_variables[placeholder], field)
        for placeholder in FILTER_REF.findall(rendered)
    )


def successful_end_ids(
    nodes: Iterable[dict[str, Any]], edges: Iterable[dict[str, Any]], producer: str
) -> set[str]:
    """Return End nodes reachable from a producer without taking its failure port."""
    end_ids = {
        str(node.get("id"))
        for node in nodes
        if node.get("type") == "core.control.end" and node.get("id")
    }
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        source = str(edge.get("sourceNodeId") or "")
        target = str(edge.get("targetNodeId") or "")
        if not source or not target or edge.get("targetPort") == "loopBack":
            continue
        if source == producer and str(edge.get("sourcePort") or "").lower() in FAILED_PORTS:
            continue
        adjacency.setdefault(source, []).append(target)

    reached: set[str] = set()
    pending = [producer]
    while pending:
        current = pending.pop()
        for target in adjacency.get(current, ()):
            if target not in reached:
                reached.add(target)
                pending.append(target)
    return reached & end_ids


def end_bindings(
    nodes: Iterable[dict[str, Any]], end_ids: set[str], output_name: str
) -> list[Any]:
    return [
        (node.get("outputs") or {})[output_name]
        for node in nodes
        if str(node.get("id")) in end_ids and output_name in (node.get("outputs") or {})
    ]


def agent_prompt_text(flow_path: Path, agent: dict[str, Any]) -> str:
    """Read prompts stored on the Flow node and, when present, its agent sidecar."""
    inputs = agent.get("inputs") or {}
    prompts = [str(inputs.get(key) or "") for key in ("systemPrompt", "userPrompt")]
    source = str(inputs.get("source") or "").strip()
    if source:
        matches = sorted(flow_path.parent.rglob(f"{source}/agent.json"))
        if len(matches) == 1:
            try:
                sidecar = json.loads(matches[0].read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                fail(f"could not read inline-agent sidecar {matches[0]}: {error}")
            prompts.extend(str(message.get("content") or "") for message in sidecar.get("messages") or [])
    return " ".join(prompts)


def _authored_values(value: Any, key: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        value_type = str(value.get("type") or "")
        if value_type in {"jsExpression", "literal"} and "expression" in value:
            yield value_type, value.get("expression")
            return
        for child_key, child in value.items():
            if child_key not in SKIPPED_VALUE_KEYS:
                yield from _authored_values(child, child_key)
        return
    if isinstance(value, list):
        for child in value:
            yield from _authored_values(child, key)
        return
    yield ("expression" if key in {"expression", "queryExpression"} else "literal"), value


def carries_literal(flow: dict[str, Any], forbidden: str) -> bool:
    """Check authored inputs/defaults, excluding canvas, descriptions, and generated metadata."""
    roots: list[Any] = []
    for node in flow.get("nodes") or []:
        roots.append(node.get("inputs") or {})
        if node.get("type") == "core.control.end":
            roots.append(node.get("outputs") or {})
    roots.extend(
        variable.get("defaultValue")
        for variable in ((flow.get("variables") or {}).get("globals") or [])
        if "defaultValue" in variable
    )

    numeric = bool(re.fullmatch(r"[0-9][0-9,]*(?:\.[0-9]+)?", forbidden))
    token = re.compile(rf"(?<![\w-]){re.escape(forbidden)}(?![\w-])")
    quoted = re.compile(r"(['\"])(.*?)\1")
    for root in roots:
        for kind, value in _authored_values(root):
            rendered = str(value if value is not None else "").strip()
            if rendered == forbidden or rendered.strip("'\"") == forbidden:
                return True
            if kind != "expression" and not rendered.startswith("=js:") and "$vars." not in rendered:
                continue
            if any(match.group(2) == forbidden for match in quoted.finditer(rendered)):
                return True
            if numeric and token.search(rendered):
                return True
    return False


def connection_binding_values(flow: dict[str, Any]) -> list[tuple[str, list[Any]]]:
    """Read connection keys from either native Flow bindings schema."""
    bindings = flow.get("bindings")
    if isinstance(bindings, list):
        return [
            (
                str(binding.get("id") or index),
                [binding.get("resourceKey"), binding.get("default")],
            )
            for index, binding in enumerate(bindings)
            if str(binding.get("resource") or "").lower() == "connection"
        ]

    resources = flow.get("resources")
    if isinstance(resources, list):
        result: list[tuple[str, list[Any]]] = []
        for index, resource in enumerate(resources):
            if str(resource.get("resource") or "").lower() != "connection":
                continue
            defaults = [
                field.get("defaultValue")
                for field in (resource.get("value") or {}).values()
                if isinstance(field, dict) and "defaultValue" in field
            ]
            result.append((str(resource.get("key") or index), defaults))
        return result
    return []
