#!/usr/bin/env python3
"""Shared helpers for live Maestro BPMN evaluations.

Plays the role `uipath-maestro-flow/_shared/flow_check.py` plays for the flow
suite: the CLI-surface plumbing every live BPMN grader needs, so a task
checker holds only its own contract. Extracted after the same helpers had been
written three times — here, in the escalation grader, and privately inside
`debug/live_debug_e2e/check_live_debug.py`.

Cannot reuse `flow_check.py` itself: the CLI surface differs. `uip maestro
flow debug` returns variables inline and addresses outputs by name, whereas
`uip maestro bpmn debug` returns an instance id whose evidence must be fetched
via `debug-instance variables-all` and `debug-instance incidents`, with
scopes keyed by ParentElementId and variables addressed by id.

Standard library only: the CI job for this suite installs pytest and nothing
else (.github/workflows/test-helpers.yml).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"

# Absolute monotonic deadline capping every CLI subprocess. A task assigns
# `bpmn_live.ACTIVE_CLI_DEADLINE` while it owns live resources so a hung call
# cannot eat the window before coder_eval SIGKILLs the grader; None disables
# capping and leaves each call to its own timeout.
ACTIVE_CLI_DEADLINE: float | None = None


class CheckFailure(RuntimeError):
    pass


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_identifier(value: object) -> str:
    """Loose id key used only as a fallback after an exact match fails.

    The runtime has been observed to re-case and re-punctuate variable ids
    between the BPMN source and the PIMS globals map, so lookups fall back to
    this form. It is intentionally lossy — `caseKey` and `case_key` collapse
    to the same key — so every caller must try the exact id first and treat a
    fallback hit that is ambiguous as a failure rather than a match.
    """

    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def resolve_runtime_key(
    mapping: dict[str, Any],
    identifier: str,
    label: str,
) -> Any:
    """Read `identifier` out of a runtime map, exactly where possible."""

    if identifier in mapping:
        return mapping[identifier]
    wanted = normalized_identifier(identifier)
    matches = [
        key for key in mapping if normalized_identifier(key) == wanted
    ]
    if not matches:
        raise CheckFailure(
            f"runtime map is missing {identifier!r} ({label})"
        )
    if len(matches) > 1:
        raise CheckFailure(
            f"{identifier!r} ({label}) matches multiple runtime ids "
            f"{sorted(matches)}; ids must be distinct beyond casing and "
            "punctuation so the graded value is unambiguous"
        )
    return mapping[matches[0]]


def get_ci(value: Any, key: str, default: Any = None) -> Any:
    if not isinstance(value, dict):
        return default
    wanted = key.casefold()
    for candidate, item in value.items():
        if str(candidate).casefold() == wanted:
            return item
    return default


def parse_json_output(text: str, label: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    raise CheckFailure(f"{label} returned invalid JSON: {stripped[:1200]}")


def exact_type(value: Any, declared_type: str) -> bool:
    if declared_type == "string":
        return type(value) is str
    if declared_type == "boolean":
        return type(value) is bool
    if declared_type == "integer":
        return type(value) is int
    if declared_type == "number":
        return type(value) in (int, float)
    if declared_type == "array":
        return type(value) is list
    if declared_type == "object":
        return type(value) is dict
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(
    arguments: list[str],
    *,
    timeout: int,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    effective_timeout: float = timeout
    # Module-level, assigned by the owning task; see ACTIVE_CLI_DEADLINE above.
    if ACTIVE_CLI_DEADLINE is not None:
        remaining = ACTIVE_CLI_DEADLINE - time.monotonic()
        if remaining <= 0:
            raise CheckFailure(
                "live Alpha operation deadline reached before running "
                f"{' '.join(arguments[:5])}"
            )
        effective_timeout = min(effective_timeout, remaining)
    command = [*arguments, "--output", "json"]
    if log_file is not None:
        command.extend(["--log-file", str(log_file)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=effective_timeout,
    )


def payload_data(
    completed: subprocess.CompletedProcess[str],
    label: str,
    *,
    require_success: bool = True,
) -> tuple[Any, Any]:
    payload = parse_json_output(
        completed.stdout or completed.stderr,
        label,
    )
    if require_success and (
        completed.returncode != 0
        or str(get_ci(payload, "Result", "")).casefold() != "success"
    ):
        message = get_ci(payload, "Message", "")
        instructions = get_ci(payload, "Instructions", "")
        raise CheckFailure(
            f"{label} failed (exit {completed.returncode}): "
            f"{message} {instructions}".strip()
        )
    return payload, get_ci(payload, "Data")


def tail_log(path: Path, limit: int = 5000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[-limit:]


def incident_records(incidents_data: Any) -> list[Any] | None:
    """Normalise `debug-instance incidents` into a list of records.

    The CLI has returned both a bare list and a paged `{"Items": [...]}`
    envelope for this endpoint; either is accepted so a shape change does not
    read as a scenario failure. Returns None when the payload is neither.
    """

    if isinstance(incidents_data, list):
        return incidents_data
    for key in ("Items", "Incidents", "Results", "Value"):
        items = get_ci(incidents_data, key)
        if isinstance(items, list):
            return items
    if isinstance(incidents_data, dict) and not incidents_data:
        return []
    return None


def root_scope(variables_data: Any) -> dict[str, Any]:
    scopes = get_ci(variables_data, "Variables", [])
    roots = [
        scope
        for scope in scopes
        if get_ci(scope, "ParentElementId") is None
    ]
    if len(roots) != 1:
        raise CheckFailure(
            f"variables-all returned {len(roots)} root scopes, expected one"
        )
    return roots[0]


def element_output_records(
    variables_data: Any,
    element_ids: str | tuple[str, ...],
) -> list[Any]:
    """Collect Outputs for one element id, or across several equivalent ids."""

    if isinstance(element_ids, str):
        element_ids = (element_ids,)
    wanted = set(element_ids)
    return _element_output_records(variables_data, wanted)


def _element_output_records(
    variables_data: Any,
    wanted: set[str],
) -> list[Any]:
    records: list[Any] = []
    scopes = get_ci(variables_data, "Variables", [])
    if not isinstance(scopes, list):
        return records
    for scope in scopes:
        for element in get_ci(scope, "Elements", []):
            if get_ci(element, "ElementId") in wanted:
                records.append(get_ci(element, "Outputs", {}))
    return records


def runtime_variable_values(
    variables_data: Any,
    variable_id: str,
) -> list[Any]:
    values: list[Any] = []
    wanted = normalized_identifier(variable_id)
    scopes = get_ci(variables_data, "Variables", [])
    if not isinstance(scopes, list):
        return values
    for scope in scopes:
        globals_map = get_ci(scope, "Globals", {})
        if not isinstance(globals_map, dict):
            continue
        for key, value in globals_map.items():
            if normalized_identifier(key) == wanted:
                values.append(value)
    return values


def connector_response_values(outputs: list[Any], name: str) -> list[Any]:
    """Read only top-level response fields, never same-named nested metadata."""
    values: list[Any] = []
    for output in outputs:
        response = get_ci(output, "response")
        if isinstance(response, dict):
            value = get_ci(response, name)
            if value is not None:
                values.append(value)
    return values


def connector_context(element: ET.Element) -> dict[str, str]:
    activity = element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )
    if activity is None:
        return {}
    return {
        item.attrib["name"]: item.attrib.get("value", "")
        for item in activity.findall(
            f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'input')}"
        )
        if item.attrib.get("name")
    }


def index_runtime_connectors(
    process: ET.Element,
) -> dict[tuple[str, str], tuple[str, ...]]:
    """Index the element ids of every connector-bearing node, by (key, path).

    Scans all descendants rather than a fixed tag list: registry templates
    may emit a connector activity as sendTask, serviceTask, or a plain task,
    and the runtime correlates on the element id either way.

    Returns ALL ids per key. Placing the same connector operation on more than
    one branch is a legitimate topology -- a Drive copy reached from two
    routes, say -- so the contract carries every id and the runtime assertions
    aggregate over them. An earlier version raised on the second occurrence,
    which forfeited the whole live criterion for a correct process.
    """

    connectors: dict[tuple[str, str], list[str]] = {}
    for node in process.iter():
        identifier = node.attrib.get("id")
        if not identifier:
            continue
        context = connector_context(node)
        key = (context.get("connectorKey", ""), context.get("path", ""))
        if not all(key):
            continue
        connectors.setdefault(key, []).append(identifier)
    return {key: tuple(ids) for key, ids in connectors.items()}


def delete_target_is_absent(
    completed: subprocess.CompletedProcess[str],
    resource_kind: str,
    target_id: str,
) -> bool:
    detail = f"{completed.stdout}\n{completed.stderr}".casefold()
    absence_markers = ("404", "not found", "does not exist")
    if not any(marker in detail for marker in absence_markers):
        return False
    resource_markers = {
        "solution": ("solution not found", "solution does not exist"),
        "slack message": (
            "message_not_found",
            "message not found",
            "message does not exist",
        ),
        "drive file": ("file not found", "file does not exist"),
        "jira issue": ("issue not found", "issue does not exist"),
    }
    if any(
        marker in detail
        for marker in resource_markers.get(resource_kind, ())
    ):
        return True

    labels = {
        "solution": "solution",
        "slack message": "message",
        "drive file": "file",
        "jira issue": "issue",
    }
    label = labels.get(resource_kind)
    if label is None:
        return False
    # An echoed target ID elsewhere in a generic 404 (for example an OAuth
    # connection failure followed by a request path) is not deletion proof.
    # Trust only a resource phrase that names the exact target before saying
    # that target is absent.
    return (
        re.search(
            rf"\b{re.escape(label)}\b[^\r\n]{{0,120}}"
            rf"{re.escape(target_id.casefold())}[^\r\n]{{0,120}}"
            r"(?:not found|does not exist|404)",
            detail,
        )
        is not None
    )

