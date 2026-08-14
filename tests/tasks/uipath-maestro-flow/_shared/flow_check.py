"""Shared helpers for uipath-maestro-flow e2e checks.

Runs ``uip maestro flow debug --output json`` and asserts:

1. ``finalStatus == "Completed"``.
2. For each required node-type hint, at least one ``elementExecution`` with
   status ``Completed`` has ``elementType`` or ``extensionType`` containing
   the hint (case-insensitive). This guards against an agent hardcoding the
   answer in a Script node instead of invoking the resource the test targets.
3. The declared output values (``globalVariables[].value`` +
   ``elements[].outputs``) satisfy the expected shape/content. We deliberately
   do NOT substring-search the full debug payload — that dump contains
   timestamps, GUIDs, and status strings whose digits/chars can falsely match
   tiny expected values (e.g. ``"3" in json.dumps(data)`` is almost always
   true whenever a debug run completes).

Payload key casing
------------------
Two distinct sources with two casings:

- The ``flow debug --output json`` RUNTIME payload uses **PascalCase** keys
  (``Data``, ``FinalStatus``, ``Variables``, ``Globals``, ``Elements``,
  ``Outputs``, and the file-attachment object's ``Id``/``FullName``/``MimeType``/
  ``Metadata``). Every runtime-payload read goes through :func:`_get_ci`, a
  case-insensitive accessor — so the conceptual camelCase key names used in this
  docstring resolve regardless of the CLI's serialization casing or any future
  normalization.
- The ``.flow`` SOURCE file uses **camelCase** keys (``variables``, ``globals``,
  ``direction``, ``type``, ``nodes``). Source readers (``read_flow_*_vars``,
  ``_iter_flow_nodes``, the node-type asserts) keep their literal camelCase keys
  — do NOT route them through :func:`_get_ci`.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence


# Raw stdout of the most recent ``uip maestro flow debug`` invocation, stashed by
# :func:`run_debug` so the output-assertion helpers can dump the FULL runtime
# response to stderr when they fail. This is the diagnostic channel for the
# chronic "debug Completes but Variables/Globals come back empty" flake
# (e.g. skill-flow-calculator 0.375): the captured stderr lands in
# ``task.json.success_criteria_results[].details``, so a failing eval preserves
# the exact payload (finalStatus, elementExecutions, globals, incidents) that the
# checker saw — which is otherwise ephemeral and unrecoverable post-run.
_LAST_DEBUG_RAW: str | None = None


# A `uip maestro flow debug` run can die on a transient server-side error — a
# gateway timeout / 5xx while polling the debug instance, which the CLI reports
# as `Result:Failure`, `ErrorCode:server_error`, `Retry:RetryLater` (the CLI's
# own Instructions say "retry once before reporting"). This is orchestration
# infrastructure hiccuping mid-run, NOT the built flow being wrong: a single
# 504 on GET /debug-instances/<id>/element-executions failed a whole seeded
# check (customer-escalation-triage). Distinct from a real flow failure (a
# `finalStatus` that completed-with-fault, or wrong outputs), which must fail
# immediately. Retry ONLY on the transient markers below.
_DEBUG_RETRY_MARKERS = ('"retry": "retrylater"', '"errorcode": "server_error"')


def _is_transient_debug_error(result: subprocess.CompletedProcess) -> bool:
    """True iff a failed ``flow debug`` invocation looks like a transient
    server-side error (5xx / RetryLater) worth retrying, rather than a real
    flow fault. Case-insensitive so CLI key casing can't slip past."""
    if result.returncode == 0:
        return False
    blob = f"{result.stdout}\n{result.stderr}".lower()
    if any(marker in blob for marker in _DEBUG_RETRY_MARKERS):
        return True
    # Fall back to an explicit 5xx HttpStatus in the error Context.
    data = _parse_json(result.stdout)
    status = _get_ci(data or {}, "Context", default={})
    http = _get_ci(status if isinstance(status, dict) else {}, "HttpStatus")
    return isinstance(http, int) and 500 <= http < 600


# ── Public helpers ──────────────────────────────────────────────────────────


def run_debug(
    *,
    inputs: dict | None = None,
    attachments: dict[str, str] | None = None,
    timeout: int = 240,
    project_glob: str = "**/project.uiproj",
    retries: int = 3,
    backoff_seconds: float = 5.0,
) -> dict:
    """Locate the project, run ``uip maestro flow debug --output json``, and return the
    parsed ``Data`` payload. Exits on any step failing.

    Transient server-side errors (5xx / ``RetryLater`` while polling the debug
    instance — see :func:`_is_transient_debug_error`) are retried up to
    ``retries`` times with ``backoff_seconds`` between attempts. A real flow
    fault (non-transient failure, or a run that completes with the wrong
    ``finalStatus``) fails immediately without burning retries.

    ``attachments`` maps a file-typed input variable ``id`` to a local file path;
    each pair is passed as ``--attachment <id>=<path>`` (repeatable). The variable
    ``id`` must match a ``variables.globals[]`` entry with ``direction:"in"`` and
    ``type:"file"`` — see :func:`read_flow_file_input_vars`."""
    project_dir = _find_project(project_glob)
    cmd = ["uip", "maestro", "flow", "debug", project_dir, "--output", "json"]
    if inputs is not None:
        cmd.extend(["--inputs", json.dumps(inputs)])
    for var_id, local_path in (attachments or {}).items():
        cmd.extend(["--attachment", f"{var_id}={local_path}"])
    global _LAST_DEBUG_RAW
    for attempt in range(retries):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        _LAST_DEBUG_RAW = r.stdout
        if r.returncode == 0 or not _is_transient_debug_error(r):
            break
        if attempt + 1 < retries:
            time.sleep(backoff_seconds)
    if r.returncode != 0:
        _fail(f"flow debug exit {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}")
    data = _parse_json(r.stdout)
    if data is None:
        _fail(f"Could not parse JSON from flow debug\n{r.stdout}")
    payload = _get_ci(data, "Data") or {}
    status = _get_ci(payload, "finalStatus", "FinalStatus")
    if status != "Completed":
        _fail(f"Flow did not complete (finalStatus={status})\n{r.stdout}")
    return payload


def assert_flow_has_node_type(
    hints: Sequence[str], *, project_glob: str = "**/project.uiproj"
) -> None:
    """Require that every ``.flow`` file under the project has at least one
    node whose ``type`` contains each hint (case-insensitive, substring).

    Uses the UiPath-native node-type names from the flow source file
    (``core.action.http``, ``uipath.core.api-workflow.{key}``, etc.), which
    are stable and match the skill's own docs — unlike the BPMN-generic
    names ``flow debug`` emits on ``elementExecutions[].elementType``.

    Pairs with a runtime output assertion: the file check confirms the
    correct node *kind* was built; the output check confirms execution
    produced the expected result.
    """
    if not hints:
        return
    types_seen: set[str] = set()
    for node in _iter_flow_nodes(project_glob):
        t = node.get("type")
        if t:
            types_seen.add(t)
    for hint in hints:
        needle = hint.lower()
        if not any(needle in t.lower() for t in types_seen):
            _fail(
                f"No node matches type hint {hint!r}. "
                f"Node types seen: {sorted(types_seen)}"
            )


def assert_flow_has_any_node_type(
    hints: Sequence[str], *, project_glob: str = "**/project.uiproj"
) -> None:
    """Require that AT LEAST ONE hint matches some ``.flow`` node ``type``
    across the project (case-insensitive, substring — same semantics as
    :func:`assert_flow_has_node_type`, but any-of instead of all-of).

    Use this any-of matcher — rather than the AND-matcher
    :func:`assert_flow_has_node_type` — when a task accepts more than one
    legitimate node shape for the SAME step. The weather tasks are the
    canonical case: the open-meteo API call may be built either as a raw
    ``core.action.http`` node OR as the curated tenant connector
    ``uipath.connector.custom-codereval-openmeteoapis.getcurrentweather``,
    and the maestro-flow skill's node-selection ladder legitimately steers
    the agent to the connector when one is present. Pinning the AND-matcher
    to ``core.action.http`` rejects the connector shape even though it calls
    the very API the test targets.

    Pairs with a runtime output assertion: this file check confirms a node
    of one acceptable *kind* was built; the output check confirms execution
    produced the expected result.
    """
    if not hints:
        return
    types_seen: set[str] = set()
    for node in _iter_flow_nodes(project_glob):
        t = node.get("type")
        if t:
            types_seen.add(t)
    for hint in hints:
        needle = hint.lower()
        if any(needle in t.lower() for t in types_seen):
            return
    _fail(
        f"No node matches any type hint {list(hints)}. "
        f"Node types seen: {sorted(types_seen)}"
    )


def assert_flow_has_api_node_targeting(
    service_hints: Sequence[str], *, project_glob: str = "**/project.uiproj"
) -> None:
    """Require an API-capable node that actually targets one of the services.

    An API-capable node is one whose ``type`` contains ``core.action.http`` or
    ``uipath.connector``; it targets the service when ANY ``service_hints``
    entry appears anywhere in the node's JSON (case-insensitive substring) —
    the connector key in the node type, the URL of a manual HTTP node, or the
    ``targetConnector`` in a connector-proxy HTTP node's detail.

    Use this instead of a bare type hint when the flow legitimately contains
    OTHER nodes of the same generic type: e.g. in the Slack weather pipeline a
    Slack connector-proxy ``core.action.http.v2`` node would satisfy a plain
    ``core.action.http`` hint, letting a flow with no weather node at all pass
    the structural gate. Scoping the content match to API-capable node types
    keeps a Script node that merely mentions the service from counting.
    """
    if not service_hints:
        return
    needles = [hint.lower() for hint in service_hints]
    api_types_seen: set[str] = set()
    for node in _iter_flow_nodes(project_glob):
        t = str(node.get("type") or "")
        t_lower = t.lower()
        if "core.action.http" not in t_lower and "uipath.connector" not in t_lower:
            continue
        api_types_seen.add(t)
        blob = json.dumps(node).lower()
        if any(needle in blob for needle in needles):
            return
    _fail(
        f"No core.action.http/uipath.connector node targets any of {list(service_hints)}. "
        f"API-capable node types seen: {sorted(api_types_seen)}"
    )


def assert_flow_has_exact_node_type(
    types: Sequence[str], *, project_glob: str = "**/project.uiproj"
) -> None:
    """Require that the project has, for EACH type in ``types``, at least one
    ``.flow`` node whose ``type`` equals it EXACTLY (``==``).

    This is the strict counterpart to :func:`assert_flow_has_node_type`, which
    matches by case-insensitive SUBSTRING. Use the exact helper when a family of
    node types shares a common prefix and the task requires one specific member:
    e.g. the generic chained ``core.action.transform`` node must be pinned so the
    standalone variants ``core.action.transform.filter`` / ``.map`` / ``.group-by``
    are REJECTED (the substring helper would accept all four).

    On failure, exits listing the node types actually seen.
    """
    if not types:
        return
    types_seen: set[str] = set()
    for node in _iter_flow_nodes(project_glob):
        t = node.get("type")
        if t:
            types_seen.add(t)
    for wanted in types:
        if wanted not in types_seen:
            _fail(
                f"No node has exact type {wanted!r}. "
                f"Node types seen: {sorted(types_seen)}"
            )


def assert_flow_uses_connector_target(
    connector_key: str, *, project_glob: str = "**/project.uiproj"
) -> None:
    """Require a native connector node or HTTP proxy node targeting connector_key.

    Some connector-backed flows are authored as ``core.action.http.v2`` nodes
    with ``bodyParameters.authentication = "connector"`` and a
    ``targetConnector`` rather than as ``uipath.connector.*`` node types.
    Treat that as connector usage only when a real connection id and folder key
    are also present, so a manual HTTP request cannot satisfy connector tests.
    """
    expected = connector_key.lower()
    seen: list[str] = []

    for node in _iter_flow_nodes(project_glob):
        node_type = str(node.get("type") or "")
        node_type_lower = node_type.lower()
        seen.append(node_type)

        if "uipath.connector" in node_type_lower and expected in node_type_lower:
            return

        detail = (node.get("inputs") or {}).get("detail") or {}
        if not isinstance(detail, dict):
            continue
        body = detail.get("bodyParameters") or {}
        if not isinstance(body, dict):
            continue

        target = str(body.get("targetConnector") or body.get("connectorKey") or "")
        authentication = str(body.get("authentication") or "")
        connection_id = detail.get("connectionId")
        folder_key = detail.get("connectionFolderKey")
        if (
            node_type_lower.startswith("core.action.http")
            and target.lower() == expected
            and authentication.lower() == "connector"
            and _non_empty_binding_value(connection_id)
            and _non_empty_binding_value(folder_key)
        ):
            return

    _fail(
        f"No node uses connector target {connector_key!r}. "
        f"Node types seen: {sorted(set(seen))}"
    )


def collect_outputs(payload: dict) -> list[Any]:
    """Return the declared output values — global variables and per-element
    outputs only. Excludes metadata (IDs, timestamps, status strings).
    Nested dicts/lists are flattened to leaf values so callers can match
    scalars regardless of how the agent wrapped them (e.g. ``{"product": 391}``
    yields ``391``, not the enclosing dict).

    ``variables.globals`` is where End-node output expressions land at
    runtime (as a name→value dict). ``variables.globalVariables`` is the
    SDK-typed array shape; in practice the runtime populates the dict form.
    Both are walked to be safe.
    """
    out: list[Any] = []
    variables = _get_ci(payload, "variables", "Variables") or {}
    for val in (_get_ci(variables, "globals", "Globals") or {}).values():
        out.extend(_leaves(val))
    for v in _get_ci(variables, "globalVariables", "GlobalVariables") or []:
        value = _get_ci(v, "value", "Value")
        if value is not None:
            out.extend(_leaves(value))
    for e in _get_ci(variables, "elements", "Elements") or []:
        out.extend(_leaves(_get_ci(e, "outputs", "Outputs") or {}))
    return out


def _leaves(v: Any):
    if isinstance(v, dict):
        for nested in v.values():
            yield from _leaves(nested)
    elif isinstance(v, (list, tuple)):
        for item in v:
            yield from _leaves(item)
    else:
        yield v


def assert_outputs_contain(
    payload: dict, needles: str | Sequence[str], *, require_all: bool = True
) -> None:
    """Assert the stringified outputs contain the given needle(s).

    ``require_all=True`` (default): every needle must appear.
    ``require_all=False``: at least one needle must appear.
    """
    if isinstance(needles, str):
        needles = [needles]
    haystack = _stringify(collect_outputs(payload))
    present = [n for n in needles if n.lower() in haystack]
    missing = [n for n in needles if n.lower() not in haystack]
    ok = len(missing) == 0 if require_all else len(present) > 0
    if not ok:
        mode = "all of" if require_all else "any of"
        _fail_with_capture(
            f"Outputs missing {mode} {list(needles)}; present={present}; "
            f"missing={missing}\nOutputs: {haystack[:1000]}"
        )


def get_last_debug_raw() -> str | None:
    """Return the raw stdout of the most recent ``run_debug`` call (the full
    ``uip maestro flow debug`` JSON envelope), or ``None`` if none ran yet.
    Useful for persisting the execution trace for post-run inspection."""
    return _LAST_DEBUG_RAW


def assert_output_nonempty(payload: dict, name: str) -> Any:
    """Assert a named output global (e.g. an End-node-mapped ``out`` variable)
    is present and non-empty, and return its value.

    Looks the variable up by name in the runtime payload's ``variables.globals``
    dict and ``variables.globalVariables`` array (both casings). "Non-empty"
    means: present, not ``None``, and — once stringified — not whitespace-only
    (so ``""``, ``"   "``, ``{}``, ``[]`` all fail)."""
    variables = _get_ci(payload, "variables", "Variables") or {}
    globals_dict = _get_ci(variables, "globals", "Globals") or {}
    value = _get_ci(globals_dict, name)
    if value is None:
        for v in _get_ci(variables, "globalVariables", "GlobalVariables") or []:
            if str(_get_ci(v, "id", "Id", "name", "Name") or "").lower() == name.lower():
                value = _get_ci(v, "value", "Value")
                break
    text = "".join(str(v) for v in _leaves(value) if v is not None).strip()
    if not text:
        present = list(globals_dict.keys())
        _fail_with_capture(
            f"Output {name!r} is missing or empty; present globals={present}\n"
            f"value={value!r}"
        )
    return value


def assert_named_output_contains(
    payload: dict,
    name: str,
    needles: str | Sequence[str],
    *,
    require_all: bool = True,
) -> str:
    """Assert a NAMED output global is present, non-empty, and contains the
    needle(s). Returns the stringified value.

    Unlike :func:`assert_outputs_contain` — which flattens the WHOLE payload and
    so matches trigger-input echoes (e.g. an ``invoiceNumber`` input global makes
    the invoice string "present" even when the agent never drafted it) — this
    scopes the match to one declared output global, the value a downstream
    consumer actually receives. Use it to grade that an agent's drafted text
    landed in the mapped flow output, not merely that a string appears somewhere
    in the debug dump.
    """
    value = assert_output_nonempty(payload, name)  # fails if missing/empty
    haystack = _stringify(_leaves(value))
    if isinstance(needles, str):
        needles = [needles]
    present = [n for n in needles if n.lower() in haystack]
    missing = [n for n in needles if n.lower() not in haystack]
    ok = len(missing) == 0 if require_all else len(present) > 0
    if not ok:
        mode = "all of" if require_all else "any of"
        _fail_with_capture(
            f"Output {name!r} missing {mode} {list(needles)}; present={present}; "
            f"missing={missing}\n{name}={haystack[:1000]}"
        )
    return haystack


def assert_output_int_in_range(payload: dict, lo: int, hi: int) -> int:
    """Assert at least one integer in [lo, hi] appears in the outputs, and
    return the first match. Extracts integers from output values only, not
    from the full debug payload."""
    haystack = _stringify(collect_outputs(payload))
    hits = [int(m) for m in re.findall(r"-?\d+", haystack) if lo <= int(m) <= hi]
    if not hits:
        _fail_with_capture(
            f"No integer in [{lo}, {hi}] found in outputs\nOutputs: {haystack[:1000]}"
        )
    return hits[0]


def assert_output_value(payload: dict, expected: Any) -> None:
    """Assert that some declared output equals ``expected``. For numerics this
    is strict equality against a numeric leaf; for strings it is case-insensitive
    substring. Deliberately does NOT regex-search for integers inside string
    leaves — error dumps (e.g., HTTP response bodies with ETag hashes like
    ``W/"20-da39a3ee5e6b4b0d..."``) embed isolated digits between non-digit
    characters and would spuriously match small expected ints like 6 or 3."""
    outs = collect_outputs(payload)
    for v in outs:
        if v == expected:
            return
        if isinstance(expected, str) and isinstance(v, str):
            if expected.lower() in v.lower():
                return
    _fail_with_capture(
        f"No output equals expected {expected!r}\nOutputs: {_stringify(outs)[:1000]}"
    )


def normalized(value: Any) -> Any:
    """Normalize a scalar output for equality comparison: trim strings, fold
    case, and coerce the literal strings ``"true"``/``"false"`` to booleans.
    Shared so per-task checkers don't each re-declare it."""
    if isinstance(value, str):
        lowered = value.strip().casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered
    return value


def assert_named_equals(payload: dict, name: str, expected: Any) -> None:
    """Assert a named ``out`` variable is present, non-empty, and (after
    :func:`normalized`) equals ``expected``. Shared across the escalation
    checkers so the compare/normalize logic lives in one place."""
    actual = assert_output_nonempty(payload, name)
    if normalized(actual) != normalized(expected):
        _fail(f"output {name!r}: expected {expected!r}, got {actual!r}")


_SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")


def _connector_node_ids(connector_key: str, project_glob: str) -> set:
    """Node ids that reach ``connector_key`` — a native connector node OR a
    connector-mode ``core.action.http`` proxy carrying real connector auth
    (authentication=connector + non-empty connectionId + connectionFolderKey),
    the same shapes :func:`assert_flow_uses_connector_target` accepts. Shared so
    the message check and the branch-routing check agree on what counts."""
    ids: set = set()
    for n in _iter_flow_nodes(project_glob):
        t = str(n.get("type", ""))
        if connector_key in t:
            ids.add(n.get("id"))
            continue
        detail = (n.get("inputs") or {}).get("detail") or {}
        if not isinstance(detail, dict):
            continue
        body = detail.get("bodyParameters") or {}
        body = body if isinstance(body, dict) else {}
        target = str((body.get("targetConnector") or body.get("connectorKey") or "")).lower()
        if (
            t.lower().startswith("core.action.http")
            and target == connector_key.lower()
            and str(body.get("authentication") or "").lower() == "connector"
            and _non_empty_binding_value(detail.get("connectionId"))
            and _non_empty_binding_value(detail.get("connectionFolderKey"))
        ):
            ids.add(n.get("id"))
    return ids


def assert_slack_message_posted(
    payload: dict,
    name: str,
    *,
    connector_key: str = "uipath-salesforce-slack",
    project_glob: str = "**/project.uiproj",
    expected_channel: str | None = None,
    must_contain: str | None = None,
) -> str:
    """Assert a Slack message was actually sent in this debug run.

    Two independent gates, so a flow can't fake delivery:

    1. **Shape** — the named output is a Slack message ``ts``
       (``\\d{9,11}\\.\\d{4,6}``, e.g. ``1786647595.771239``), rejecting a
       hard-coded placeholder like ``"ok"`` / ``"sent"`` / ``"1"``.
    2. **Trace** — at least one ``connector_key`` node in the flow has a
       ``Completed`` ``elementExecution`` in the debug payload. A disconnected
       or unexecuted connector node produces no such record, so a constant ``ts``
       mapped past an idle node fails here. This is the "confirm the timestamp
       came from an executed connector send" check.

    Returns the ts."""
    value = assert_output_nonempty(payload, name)
    text = str(value).strip()
    if not _SLACK_TS_RE.match(text):
        _fail(
            f"output {name!r}={text!r} is not a Slack message ts (expected "
            r"\d{9,11}\.\d{4,6}); the flow did not actually post to Slack"
        )

    # Native connector node OR a connector-mode HTTP proxy carrying real auth.
    slack_ids = _connector_node_ids(connector_key, project_glob)
    if not slack_ids:
        _fail(f"no connected {connector_key} node found in the flow")

    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    completed = [
        e
        for e in els
        if _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId") in slack_ids
        and str(_get_ci(e, "status", "Status")).lower() == "completed"
    ]
    if not completed:
        _fail_with_capture(
            f"no {connector_key} node completed in the debug trace "
            f"(slack nodes {sorted(i for i in slack_ids if i)}); ts {text} did "
            "not come from an executed Slack send"
        )

    # Tie the mapped ts to an executed Slack node's OWN response. The runtime
    # surfaces each node's output at globals["<nodeId>.output"]; a real send's
    # response carries its ``ts``. If any executed Slack node exposes a ts, the
    # mapped slackMessageId must be one of them — so executing a Slack node while
    # mapping a different hard-coded ts is rejected.
    gvars = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    matched_out = None
    for e in completed:
        nid = _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId")
        out = gvars.get(f"{nid}.output") if isinstance(gvars, dict) else None
        if not isinstance(out, (dict, list)):
            continue
        ts_leaves = {
            str(x).strip()
            for x in _leaves(out)
            if isinstance(x, str) and _SLACK_TS_RE.match(str(x).strip())
        }
        if text in ts_leaves:
            matched_out = out
            break
    # A real send's response always carries its ts; require the mapped
    # slackMessageId to be that response's ts. If no executed Slack node's output
    # exposes this exact ts, the value was not produced by the executed send.
    if matched_out is None:
        _fail_with_capture(
            f"slackMessageId {text} does not match any executed Slack node's response "
            "ts; the mapped ts was not produced by the executed send"
        )

    # Channel + content of the actual send (from the connector's own echoed
    # response), so posting a generic message or to the wrong channel is rejected.
    if matched_out is not None:
        if expected_channel:
            posted = str(_get_ci(matched_out, "channel", "Channel") or "")
            if posted != expected_channel:
                _fail_with_capture(
                    f"Slack message posted to channel {posted!r}, expected {expected_channel!r}"
                )
        if must_contain:
            content = " ".join(str(x) for x in _leaves(matched_out) if isinstance(x, str))
            if must_contain not in content:
                _fail_with_capture(
                    f"posted Slack message does not contain {must_contain!r} — wrong content"
                )
    return text


def assert_node_type_executed(
    payload: dict, type_hint: str, *, project_glob: str = "**/project.uiproj"
) -> None:
    """Assert at least one flow node whose ``type`` contains ``type_hint`` has a
    ``Completed`` ``elementExecution`` in this debug run — i.e. the node type is
    actually on the executed path, not merely present-but-disconnected in the
    source. Complements :func:`assert_flow_has_node_type` (source-only)."""
    ids = {
        n.get("id")
        for n in _iter_flow_nodes(project_glob)
        if type_hint in str(n.get("type", ""))
    }
    if not ids:
        _fail(f"no node of type {type_hint!r} in the flow")
    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    if not any(
        _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId") in ids
        and str(_get_ci(e, "status", "Status")).lower() == "completed"
        for e in els
    ):
        _fail_with_capture(
            f"no {type_hint!r} node executed in the debug trace (nodes {sorted(i for i in ids if i)}); "
            "it is present in the source but not on the executed path"
        )


def _load_flow(project_glob: str) -> dict:
    """Load the single .flow next to the matched project.uiproj."""
    proj = _find_project(project_glob)
    flows = glob.glob(os.path.join(proj, "*.flow"))
    if not flows:
        _fail(f"no .flow file under {proj}")
    return json.loads(open(flows[0], encoding="utf-8").read())


def assert_decision_branches_reach(
    branch_a_targets: set,
    branch_b_targets: set,
    *,
    decision_type: str = "core.logic.decision",
    project_glob: str = "**/project.uiproj",
) -> None:
    """Assert some ``decision_type`` node has TWO distinct outgoing ports whose
    downstream reach separates ``branch_a_targets`` from ``branch_b_targets`` —
    i.e. the Decision itself routes to the two target groups (all A reachable from
    one port, all B from another, with no cross-contamination). Proves the two
    groups are the Decision's branches, not just nodes that happened to fire on
    different cases behind a cosmetic always-true Decision."""
    from collections import defaultdict, deque

    flow = _load_flow(project_glob)
    edges = flow.get("edges") or []
    nodes = flow.get("nodes") or []
    decisions = [n.get("id") for n in nodes if decision_type in str(n.get("type", ""))]
    if not decisions:
        _fail(f"no {decision_type!r} node in the flow")

    adj = defaultdict(list)
    for e in edges:
        adj[e.get("sourceNodeId")].append((e.get("sourcePort"), e.get("targetNodeId")))

    def reach(start: str) -> set:
        seen: set = set()
        q = deque([start])
        while q:
            n = q.popleft()
            if n in seen:
                continue
            seen.add(n)
            for _, t in adj.get(n, []):
                q.append(t)
        return seen

    a, b = set(branch_a_targets), set(branch_b_targets)
    for d in decisions:
        port_reach = defaultdict(set)
        for port, tgt in adj.get(d, []):
            port_reach[port].update(reach(tgt))
        for pa, ra in port_reach.items():
            if not a <= ra:
                continue
            for pb, rb in port_reach.items():
                if pb != pa and b <= rb and not (a & rb) and not (b & ra):
                    return  # clean two-branch separation via this Decision
    _fail_with_capture(
        f"no {decision_type!r} routes {sorted(a)} and {sorted(b)} through separate "
        "branches; the distinct Slack nodes are not the Decision's two outgoing paths"
    )


def completed_connector_node_ids(
    payload: dict, connector_key: str, *, project_glob: str = "**/project.uiproj"
) -> set:
    """Return the ids of ``connector_key`` nodes with a ``Completed``
    elementExecution in this run — i.e. which connector node actually fired.
    Used to prove branch routing across cases (escalation vs triage must fire
    different nodes, not one dynamic node behind a cosmetic Decision)."""
    ids = _connector_node_ids(connector_key, project_glob)
    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    return {
        _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId")
        for e in els
        if _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId") in ids
        and str(_get_ci(e, "status", "Status")).lower() == "completed"
    }


def read_flow_input_vars(project_dir: str) -> list[str]:
    """Return the ordered list of input variable IDs declared on the first
    ``.flow`` file in ``project_dir``."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        _fail(f"No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    variables = flow.get("variables") or flow.get("workflow", {}).get("variables") or {}
    return [
        v["id"]
        for v in (variables.get("globals") or [])
        if v.get("direction") in ("in", "inout")
    ]


def read_flow_file_input_vars(project_dir: str) -> list[str]:
    """Return the ordered list of file-typed input variable IDs (``direction:"in"``,
    ``type:"file"``) declared on the first ``.flow`` file in ``project_dir``. These
    are the ids eligible for ``uip maestro flow debug --attachment <id>=<path>``."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        _fail(f"No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    variables = flow.get("variables") or flow.get("workflow", {}).get("variables") or {}
    return [
        v["id"]
        for v in (variables.get("globals") or [])
        if v.get("direction") == "in" and v.get("type") == "file"
    ]


def find_project_dir(pattern: str = "**/project.uiproj") -> str:
    return _find_project(pattern)


# ── Internals ───────────────────────────────────────────────────────────────


def _parse_json(stdout: str) -> dict | None:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        for i, line in enumerate(stdout.split("\n")):
            if line.strip().startswith("{"):
                try:
                    return json.loads("\n".join(stdout.split("\n")[i:]))
                except json.JSONDecodeError:
                    continue
    return None


def _get_ci(mapping: Any, *candidate_keys: str, default: Any = None) -> Any:
    """Case-insensitively read the first present candidate key from ``mapping``.

    The ``uip maestro flow debug --output json`` runtime payload uses PascalCase
    keys (``FinalStatus``, ``Variables``, ``Globals``, ``Elements``, ``Outputs``)
    while this module's docstring and the ``.flow`` source files use camelCase.
    Reading the runtime payload through this accessor tolerates either casing and
    any future CLI normalization. Use it ONLY for the debug RUNTIME payload — NOT
    for ``.flow`` SOURCE readers, whose camelCase keys are stable and intentional.

    Candidates are tried in order; the first whose lowercased form matches a key
    in ``mapping`` (also lowercased) wins. Returns ``default`` if ``mapping`` is
    not a dict or no candidate matches.
    """
    if not isinstance(mapping, dict):
        return default
    lowered = {k.lower(): k for k in mapping.keys() if isinstance(k, str)}
    for candidate in candidate_keys:
        actual = lowered.get(candidate.lower())
        if actual is not None:
            return mapping[actual]
    return default


def _iter_flow_nodes(project_glob: str):
    project_dir = _find_project(project_glob)
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        yield from flow.get("nodes") or []


def _non_empty_binding_value(value: Any) -> bool:
    return (
        isinstance(value, str) and bool(value.strip()) and value != "ImplicitConnection"
    )


def _find_project(pattern: str) -> str:
    """Locate the *Flow* project directory matching ``pattern``.

    Tasks that legitimately ship multi-project solutions (a Flow project
    plus a sibling agent / sub-flow / RPA project — see e.g. coded_agent,
    lowcode_agent) produce more than one ``project.uiproj`` under the
    solution root. The Flow project is the one with
    ``"ProjectType": "Flow"`` in its manifest; sibling resource projects
    declare ``"ProjectType": "Agent"`` / ``"Coded"`` / ``"Process"``.
    Filtering by manifest avoids a 1-of-N glob collision the symptom of
    MST-9734.
    """
    candidates = sorted(glob.glob(pattern, recursive=True))
    if not candidates:
        _fail(f"No project.uiproj found matching {pattern}")
    flow_projects = [p for p in candidates if _is_flow_project(p)]
    if not flow_projects:
        joined = "\n  - ".join(candidates)
        _fail(
            f"No Flow project.uiproj found matching {pattern} — "
            f'candidates exist but none declare ProjectType="Flow":\n  - {joined}'
        )
    if len(flow_projects) > 1:
        joined = "\n  - ".join(flow_projects)
        _fail(
            f"Multiple Flow projects match {pattern!r} — refusing to guess:\n  - {joined}"
        )
    return os.path.dirname(flow_projects[0])


def _is_flow_project(path: str) -> bool:
    """Return True iff ``path`` is a ``project.uiproj`` declaring a Flow project.

    Returns False (rather than raising) for unreadable / malformed manifests
    so a single bad sibling cannot mask a legitimate Flow project.
    """
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("ProjectType") == "Flow"


def _stringify(values: Iterable[Any]) -> str:
    return json.dumps(list(values), default=str).lower()


def _dump_debug_capture(context: str = "") -> None:
    """Emit the most recent raw ``flow debug`` response to stderr for diagnosis.

    Called on output-assertion failures so the captured criterion output preserves
    the full runtime payload — the only way to inspect the chronic
    "Completed-but-empty-Variables" flake after the (ephemeral) debug run is gone.
    Best-effort and side-effect-free: never raises, so it cannot mask the real
    assertion failure that follows.
    """
    raw = _LAST_DEBUG_RAW
    if not raw:
        return
    tag = f" ({context})" if context else ""
    lines = [f"=== FLOW_DEBUG_RAW_CAPTURE BEGIN{tag} ==="]
    try:
        # Parse via the tolerant helper, not bare json.loads: the CLI may emit a
        # banner/warning before the JSON (the reason run_debug uses _parse_json),
        # and a plain json.loads would drop the whole structured summary to
        # "<unparsable>" even though the run produced a valid payload.
        parsed = _parse_json(raw)
        if parsed is None:
            raise ValueError("no JSON object found in debug stdout")
        data = _get_ci(parsed, "Data") or {}
        variables = _get_ci(data, "variables", "Variables") or {}
        summary = {
            "finalStatus": _get_ci(data, "finalStatus", "FinalStatus"),
            "globals": _get_ci(variables, "globals", "Globals"),
            "globalVariables": _get_ci(variables, "globalVariables", "GlobalVariables"),
            "elementOutputs": [
                {
                    "id": _get_ci(e, "elementId", "ElementId", "id", "Id"),
                    "outputs": _get_ci(e, "outputs", "Outputs"),
                }
                for e in (_get_ci(variables, "elements", "Elements") or [])
            ],
            "elementExecutions": [
                {
                    "id": _get_ci(x, "elementId", "ElementId", "id", "Id"),
                    "type": _get_ci(x, "elementType", "ElementType", "extensionType"),
                    "status": _get_ci(x, "status", "Status"),
                }
                for x in (_get_ci(data, "elementExecutions", "ElementExecutions") or [])
            ],
            "incidents": _get_ci(data, "incidents", "Incidents"),
        }
        lines.append("SUMMARY: " + json.dumps(summary, default=str))
    except Exception as exc:  # noqa: BLE001 — diagnostics must never mask the real failure
        lines.append(f"SUMMARY: <unparsable: {exc!r}>")
    lines.append("RAW: " + raw.strip())
    lines.append("=== FLOW_DEBUG_RAW_CAPTURE END ===")
    print("\n".join(lines), file=sys.stderr)


def _fail_with_capture(msg: str):
    """Dump the raw debug payload (diagnostics) then fail with ``msg``."""
    _dump_debug_capture(msg.split("\n", 1)[0])
    _fail(msg)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")
