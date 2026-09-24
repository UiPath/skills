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
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Collection, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"

# Absolute monotonic deadline capping every CLI subprocess. A task assigns


# `uip maestro bpmn debug` polls the instance at most this many times
# (pollDebugInstanceStatus maxPolls in the maestro tool).
CLI_MAX_POLLS = 300


class CheckFailure(RuntimeError):
    pass


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"




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


# Worst-case wall clock for one `run_debug` call, mirroring
# flow_check.debug_budget so test_criterion_budgets.py can hold both suites to
# the same arithmetic. BPMN's run_debug makes a single attempt with no backoff,
# so the budget is the call's own timeout; the retries/backoff parameters exist
# to keep the two signatures interchangeable if that changes.
# Headroom a criterion needs beyond the calls it makes, for process start and
# teardown. Mirrors flow_check.CRITERION_MARGIN_SECONDS; test_criterion_budgets
# enforces the pair.
CRITERION_MARGIN_SECONDS = 60

DEBUG_BUDGET_DEFAULT_TIMEOUT = 480


def debug_budget(
    timeout: int = DEBUG_BUDGET_DEFAULT_TIMEOUT,
    retries: int = 1,
    backoff_seconds: float = 0.0,
) -> int:
    attempts = max(1, retries)
    return timeout * attempts + math.ceil(backoff_seconds) * (attempts - 1)


def run_cli(
    arguments: list[str],
    *,
    timeout: int,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    effective_timeout: float = timeout
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
) -> dict[tuple[str, str, str], tuple[str, ...]]:
    """Index the element ids of every connector-bearing node, by
    (key, path, objectName).

    Scans all descendants rather than a fixed tag list: registry templates
    may emit a connector activity as sendTask, serviceTask, or a plain task,
    and the runtime correlates on the element id either way.

    Both route fields are carried: a connector can expose one operation under
    several objects whose paths differ only in spelling, so a caller matching
    on the path alone cannot say which of them it means.

    Returns ALL ids per key. Placing the same connector operation on more than
    one branch is a legitimate topology -- a Drive copy reached from two
    routes, say -- so the contract carries every id and the runtime assertions
    aggregate over them. An earlier version raised on the second occurrence,
    which forfeited the whole live criterion for a correct process.
    """

    connectors: dict[tuple[str, str, str], list[str]] = {}
    for node in process.iter():
        identifier = node.attrib.get("id")
        if not identifier:
            continue
        context = connector_context(node)
        connector_key = context.get("connectorKey", "")
        path = context.get("path", "")
        if not connector_key or not path:
            continue
        key = (connector_key, path, context.get("objectName", ""))
        connectors.setdefault(key, []).append(identifier)
    return {key: tuple(ids) for key, ids in connectors.items()}


def delete_target_is_absent(
    completed: subprocess.CompletedProcess[str],
    resource_kind: str,
    target_id: str,
) -> bool:
    detail = f"{completed.stdout}\n{completed.stderr}".casefold()
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

    absence_markers = ("404", "not found", "does not exist")
    if not any(marker in detail for marker in absence_markers):
        return False

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


def poll_interval_ms(timeout: int) -> int:
    """`--poll-interval` for a `bpmn debug` priced at `timeout` seconds.

    The CLI polls at most CLI_MAX_POLLS times, so the interval decides how
    long `bpmn debug` waits before giving up with its own poll-timeout
    envelope (ErrorCode "timeout", Data.lastStatus still "Running", no
    FinalStatus). A flat 500 ms capped that wait at 150 s and turned every
    longer run into "final status was None" (CI run 35503094182,
    jira_lifecycle and jira_search_triage), so the interval scales with the
    budget.

    80% of the budget, not ~97% (`CLI_MAX_POLLS - 10`): the CLI packs,
    publishes and starts the instance before its first poll, so an envelope
    sized at the full budget expires after run_cli's own SIGKILL and the
    ErrorCode == "timeout" branch in run_debug never runs. The remaining 20%
    pays for that startup and keeps the CLI's envelope — which names the
    instance and its last status — the thing that fires first.
    """
    return max(500, math.ceil(timeout * 1000 * 0.8 / CLI_MAX_POLLS))


def _as_text(raw: bytes | str | None) -> str:
    """Decode captured child output.

    ``subprocess.TimeoutExpired`` carries it as bytes even under ``text=True``,
    unlike ``CompletedProcess``.
    """
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", "replace")
    return raw


def _write_debug_log(log_file, text: str) -> None:
    """Persist the debug CLI's combined output, best effort.

    `log_file` is evidence for a human reading a failed run, never something a
    check asserts on, so a filesystem error here must not turn a real verdict
    into a crash.
    """
    if log_file is None:
        return
    path = Path(log_file)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError:
        pass


def run_debug(
    project_dir,
    inputs: dict,
    log_file,
    *,
    timeout: int = DEBUG_BUDGET_DEFAULT_TIMEOUT,
) -> tuple:
    """Run one `uip maestro bpmn debug`; return (debug_data, instance_id).

    Lives here rather than in a task checker so test_criterion_budgets.py can
    price it, the same way flow_check.run_debug is priced in the flow suite.
    """

    poll_ms = poll_interval_ms(timeout)
    try:
        completed = run_cli(
            [
                "uip",
                "maestro",
                "bpmn",
                "debug",
                str(project_dir),
                "--poll-interval",
                str(poll_ms),
                "--inputs",
                json.dumps(inputs, separators=(",", ":")),
            ],
            timeout=timeout,
            # Not passed through as the CLI's own --log-file: the CLI buffers
            # that file and a SIGKILL on timeout leaves it empty (run
            # 35524004307). The poll log (instance id, per-poll status) is
            # streamed to stderr instead, survives on the TimeoutExpired
            # exception, and is written to `log_file` from here.
            log_file=None,
        )
    except subprocess.TimeoutExpired as exc:
        out, err = _as_text(exc.stdout), _as_text(exc.stderr)
        _write_debug_log(log_file, out + err)
        partial = err or out
        raise CheckFailure(
            f"bpmn debug did not reach a terminal status within the {timeout}s budget "
            f"(the instance is still running or stuck); CLI log tail: {partial[-3000:]}"
        ) from None
    _write_debug_log(log_file, (completed.stdout or "") + (completed.stderr or ""))
    payload = parse_json_output(completed.stdout or completed.stderr, "debug")
    debug_data = get_ci(payload, "Data", {})
    if str(get_ci(payload, "ErrorCode", "")).casefold() == "timeout":
        raise CheckFailure(
            "bpmn debug stopped waiting before the run reached a terminal status: "
            f"instance {get_ci(debug_data, 'instanceId')!r} was still "
            f"{get_ci(debug_data, 'lastStatus')!r} after "
            f"{get_ci(debug_data, 'timeoutSeconds')!r}s"
        )
    instance_id = get_ci(debug_data, "InstanceId")
    if not isinstance(instance_id, str) or not instance_id:
        raise CheckFailure(
            f"debug returned no instance id (exit {completed.returncode}): "
            f"{get_ci(payload, 'Message', '')} {get_ci(payload, 'Instructions', '')}".strip()
            + f"; stderr tail: {(completed.stderr or '')[-1500:]}"
        )
    return debug_data, instance_id


SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120

COMPLETED_STATUSES = frozenset({"Completed", "Successful"})


def import_exact(bpmn_path: Path, project_dir: Path, solution_dir: Path) -> Path:
    """Import the submitted project into a fresh solution and return the
    imported project directory, failing if the imported .bpmn bytes differ."""

    original_hash = sha256(bpmn_path)
    solution_dir.parent.mkdir(parents=True, exist_ok=True)
    initialized = run_cli(
        ["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT
    )
    payload_data(initialized, "initialize ephemeral solution")

    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        raise CheckFailure(
            f"solution init produced {len(solution_files)} .uipx files in "
            f"{solution_dir}, expected exactly one"
        )

    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(project_dir.resolve()),
            "--solutionFile",
            str(solution_files[0]),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")

    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / bpmn_path.name) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")
    return imported_project


@dataclass(frozen=True)
class DebugEvidence:
    variables: Any
    variables_text: str
    incidents: list[Any] | None
    incidents_raw: Any


def fetch_variables(instance_id: str) -> tuple[Any, str]:
    """`debug-instance variables-all`: (data, raw stdout)."""

    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")
    return variables_data, variables.stdout or ""


def fetch_incidents(instance_id: str) -> tuple[list[Any] | None, Any]:
    """`debug-instance incidents`: (records, raw data)."""

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    return incident_records(incidents_data), incidents_data


def debug_evidence(instance_id: str) -> DebugEvidence:
    """Variables then incidents. A grader with side effects calls the two
    fetches itself, journaling between them."""

    variables_data, variables_text = fetch_variables(instance_id)
    incidents, incidents_data = fetch_incidents(instance_id)
    return DebugEvidence(variables_data, variables_text, incidents, incidents_data)


def require_clean_run(debug_data: Any, evidence: DebugEvidence) -> str:
    """Raise unless the run completed with no incidents; return FinalStatus."""

    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in COMPLETED_STATUSES:
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if evidence.incidents:
            detail.append(f"incidents: {json.dumps(evidence.incidents)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )

    if evidence.incidents is None:
        raise CheckFailure(
            f"incidents response has an unknown shape: {evidence.incidents_raw!r}"
        )
    if evidence.incidents:
        raise CheckFailure(f"unexpected incidents: {evidence.incidents}")

    print(f"OK: bpmn debug completed (FinalStatus={final_status}, no incidents)")
    return final_status


def value_leaves(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from value_leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from value_leaves(item)
    elif value is not None:
        yield value


def output_leaves(
    variables_data: Any,
    skip: Collection[str] = (),
    *,
    elements: Collection[str] | None = None,
) -> list[Any]:
    """Leaves of the root Globals and the elements' Outputs, minus the globals
    and elements named in `skip` (see :func:`input_echo_ids`). `elements`
    limits the Outputs to those element ids; None reads every element."""

    skipped = {normalized_identifier(name) for name in skip}
    wanted = None if elements is None else {normalized_identifier(e) for e in elements}
    globals_ = get_ci(root_scope(variables_data), "Globals", {}) or {}
    leaves: list[Any] = []
    if isinstance(globals_, dict):
        for name, value in globals_.items():
            if normalized_identifier(name) in skipped:
                continue
            leaves.extend(value_leaves(value))

    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            element_id = normalized_identifier(get_ci(element, "ElementId"))
            if element_id in skipped or (wanted is not None and element_id not in wanted):
                continue
            leaves.extend(value_leaves(get_ci(element, "Outputs", {})))
    return leaves


def output_haystack(variables_data: Any, skip: Collection[str] = ()) -> str:
    return "\n".join(str(v) for v in output_leaves(variables_data, skip)).lower()


def input_echo_ids(process: ET.Element) -> set[str]:
    """Where a process input shows up unchanged in variables-all: the
    `uipath:input` ids and names, the variables a start event copies them
    into verbatim, and the start events themselves.

        <uipath:input id="input_Var_Amount" name="Amount" elementId="Start_1"/>
        <uipath:output var="Var_Amount" source="=vars.input_Var_Amount"/>  # on Start_1
        -> {"input_Var_Amount", "Amount", "Var_Amount", "Start_1"}
    """

    ids: set[str] = set()
    for variables in process.iter(q(UIPATH_NS, "variables")):
        for node in variables.iter(q(UIPATH_NS, "input")):
            ids.update(v for v in (node.attrib.get("id"), node.attrib.get("name")) if v)

    copies = {f"=vars.{identifier}" for identifier in ids}
    for start in process.iter(q(BPMN_NS, "startEvent")):
        if start.attrib.get("id"):
            ids.add(start.attrib["id"])
        for mapping in start.iter(q(UIPATH_NS, "output")):
            if (mapping.attrib.get("source") or "").strip() in copies and mapping.attrib.get("var"):
                ids.add(mapping.attrib["var"])
    return ids
