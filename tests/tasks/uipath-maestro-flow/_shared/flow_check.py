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
import math
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

# Variable ids the most recent :func:`run_debug` bound as INPUTS (via ``--inputs``
# / ``--attachment``). Stashed because the runtime returns every global — `in` and
# `out` alike — in one ``variables.globals`` dict with no direction marker, so
# this is the only exact way to tell a result from an echo of what we just fed
# in. Consumed by :func:`_declared_input_global_keys`; see the input-echo note on
# :func:`assert_outputs_contain`.
_LAST_DEBUG_INPUT_IDS: set[str] = set()

# Project dir :func:`run_debug` resolved for the most recent run. Stashed so the
# source-declared `direction:"in"` signal works automatically instead of needing
# every call site to opt in — and so the lookup is scoped to the project that
# actually ran, never a bare glob from an arbitrary CWD.
_LAST_DEBUG_PROJECT_DIR: str | None = None


# The CLI polls for `--timeout` seconds (default 600) before giving up, while
# `timeout` here caps one attempt at 180-840s. Without an explicit `--timeout`
# we SIGKILL the CLI mid-poll and keep nothing — no payload, no instanceId, no
# incidents. The headroom covers the phases `--timeout` does not bound (upload,
# provisioning, begin-session, create-instance), so the CLI always
# self-terminates first, with a parseable envelope.
_CLI_TIMEOUT_HEADROOM_SECONDS = 60
_MIN_CLI_TIMEOUT_SECONDS = 30

# The smallest remaining budget worth spending on another attempt. Below this a
# retry cannot even fund the CLI floor plus its headroom, so it would be killed
# mid-run and yield nothing to diagnose from.
_MIN_RETRY_BUDGET_SECONDS = _MIN_CLI_TIMEOUT_SECONDS + _CLI_TIMEOUT_HEADROOM_SECONDS

# What a check spends outside `run_debug`: interpreter start, the static
# `.flow` asserts, and solution teardown. The criterion `timeout:` in the task
# YAML must clear :func:`debug_budget` by at least this much — see
# test_criterion_budgets.py, which enforces it across every task. Public
# alongside `debug_budget`: the two halves of one contract.
CRITERION_MARGIN_SECONDS = 60

# `UIP_LOG_LEVEL`, not `UIPCLI_LOG_LEVEL` — the CLI never reads the latter. At
# `info` it narrates jobKey / instanceId / Studio Web URL to stderr, the only
# way to find the instance after a timeout.
_DEBUG_LOG_LEVEL = "info"

# Matched on the message: the CLI labels this path `Retry: RetryWillNotFix`,
# which is wrong for a poll timeout.
_DEBUG_POLL_TIMEOUT_MARKER = "debug polling timed out"

# A poll timeout burns a whole attempt for no new information, so it gets a
# tighter cap than `retries`, which still governs the cheap transients (a 5xx
# usually fails in seconds). Independent of the `retries` default: raising that
# does not buy more poll-timeout attempts.
_POLL_TIMEOUT_ATTEMPTS = 2

# `run_debug` defaults, named so `debug_budget` and the criterion guard cannot
# drift from the function they price. Two attempts, not three: a third
# full-length attempt has never paid for itself, and funding one would add
# `timeout` seconds to every criterion ceiling in the suite.
_DEFAULT_RETRIES_TIMEOUT = 240
_DEFAULT_RETRIES = 2
_DEFAULT_BACKOFF_SECONDS = 5.0

# A `uip maestro flow debug` run can die on a transient server-side error — a
# gateway timeout / 5xx while polling the debug instance, which the CLI reports
# as `Result:Failure`, `ErrorCode:server_error`, `Retry:RetryLater` (the CLI's
# own Instructions say "retry once before reporting"). This is orchestration
# infrastructure hiccuping mid-run, NOT the built flow being wrong: a single
# 504 on GET /debug-instances/<id>/element-executions failed a whole seeded
# check (customer-escalation-triage). Distinct from a real flow failure (a
# `finalStatus` that completed-with-fault, or wrong outputs), which must fail
# immediately. Retry ONLY on the transient markers below.
_DEBUG_RETRY_MARKERS = (
    '"retry": "retrylater"',
    '"errorcode": "server_error"',
    _DEBUG_POLL_TIMEOUT_MARKER,
)


def _output_blob(result: subprocess.CompletedProcess) -> str:
    """Both streams, lowercased, for case-insensitive marker matching."""
    return f"{result.stdout}\n{result.stderr}".lower()


def _is_transient_debug_error(result: subprocess.CompletedProcess) -> bool:
    """True iff a failed ``flow debug`` invocation looks like a transient
    server-side error (5xx / RetryLater / poll-budget expiry) worth retrying,
    rather than a real flow fault. Case-insensitive so CLI key casing can't
    slip past."""
    if result.returncode == 0:
        return False
    if any(marker in _output_blob(result) for marker in _DEBUG_RETRY_MARKERS):
        return True
    # Fall back to an explicit 5xx HttpStatus in the error Context.
    data = _parse_json(result.stdout)
    status = _get_ci(data or {}, "Context", default={})
    http = _get_ci(status if isinstance(status, dict) else {}, "HttpStatus")
    return isinstance(http, int) and 500 <= http < 600


def _is_poll_timeout(result: subprocess.CompletedProcess) -> bool:
    """True iff the CLI gave up on its own poll budget, rather than any other
    transient error — see :data:`_POLL_TIMEOUT_ATTEMPTS`."""
    return result.returncode != 0 and (
        _DEBUG_POLL_TIMEOUT_MARKER in _output_blob(result)
    )


def _as_text(raw: bytes | str | None) -> str:
    """Decode captured child output. ``subprocess.TimeoutExpired`` carries it as
    bytes even under ``text=True``, unlike ``CompletedProcess``."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


# ── Public helpers ──────────────────────────────────────────────────────────


def debug_budget(
    timeout: int = _DEFAULT_RETRIES_TIMEOUT,
    retries: int = _DEFAULT_RETRIES,
    backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS,
) -> int:
    """Worst-case wall clock for one :func:`run_debug` call.

    Sized on ``retries``, not on :data:`_POLL_TIMEOUT_ATTEMPTS`: the poll cap
    only binds the poll-timeout path, while a slow 5xx can still consume every
    attempt ``retries`` allows. Funding fewer than that would let the deadline
    cancel a retry the caller asked for. ``retries=1`` opts out and pays for one
    attempt. Rounds the backoff up, since this is an upper bound.

    Public so test_criterion_budgets.py can hold every task YAML to the same
    arithmetic instead of eyeballing it."""
    attempts = max(1, retries)
    return timeout * attempts + math.ceil(backoff_seconds) * (attempts - 1)


def run_debug(
    *,
    inputs: dict | None = None,
    attachments: dict[str, str] | None = None,
    timeout: int = _DEFAULT_RETRIES_TIMEOUT,
    budget: int | None = None,
    project_glob: str = "**/project.uiproj",
    retries: int = _DEFAULT_RETRIES,
    backoff_seconds: float = _DEFAULT_BACKOFF_SECONDS,
) -> dict:
    """Locate the project, run ``uip maestro flow debug --output json``, and return the
    parsed ``Data`` payload. Exits on any step failing.

    ``timeout`` caps ONE attempt; the CLI gets a strictly smaller ``--timeout``
    so an overrun ends with its own diagnosable envelope instead of a SIGKILL.
    ``budget`` is the wall-clock deadline for the whole call and defaults to
    :func:`debug_budget` — enough for the retry below, and never more. The two
    are separate because a task's flow needs the attempt it needs (an
    Orchestrator job is not a Script node), while the criterion has to bound
    the check as a whole. The deadline is what keeps a retry from running past
    the ``timeout:`` the task YAML granted and being SIGKILLed with no payload,
    no instanceId, and no CLI envelope to diagnose from.

    Transient server-side errors (5xx / ``RetryLater``, or the CLI's own
    poll-budget expiry — see :func:`_is_transient_debug_error`) are retried up
    to ``retries`` times with ``backoff_seconds`` between attempts; poll
    timeouts get :data:`_POLL_TIMEOUT_ATTEMPTS`, and any retry is skipped once
    the remaining budget drops below :data:`_MIN_RETRY_BUDGET_SECONDS`. A real
    flow fault (non-transient failure, or a run that completes with the wrong
    ``finalStatus``) fails immediately without burning retries.

    ``attachments`` maps a file-typed input variable ``id`` to a local file path;
    each pair is passed as ``--attachment <id>=<path>`` (repeatable). The variable
    ``id`` must match a ``variables.globals[]`` entry with ``direction:"in"`` and
    ``type:"file"`` — see :func:`read_flow_file_input_vars`."""
    project_dir = _find_project(project_glob)
    cmd = [
        "uip",
        "maestro",
        "flow",
        "debug",
        project_dir,
        "--output",
        "json",
    ]
    if inputs is not None:
        cmd.extend(["--inputs", json.dumps(inputs)])
    for var_id, local_path in (attachments or {}).items():
        cmd.extend(["--attachment", f"{var_id}={local_path}"])
    env = dict(os.environ)
    env.setdefault("UIP_LOG_LEVEL", _DEBUG_LOG_LEVEL)
    global _LAST_DEBUG_RAW, _LAST_DEBUG_INPUT_IDS, _LAST_DEBUG_PROJECT_DIR
    # Record what we bound as input, and where the project lives, so output
    # assertions can discount echoes of our own inputs.
    _LAST_DEBUG_INPUT_IDS = {str(k) for k in (inputs or {})} | {
        str(k) for k in (attachments or {})
    }
    _LAST_DEBUG_PROJECT_DIR = project_dir

    # One deadline for the whole call, so the retry can never push us past what
    # the criterion granted. An attempt gets `timeout`, or the remainder when
    # that is smaller.
    if budget is None:
        budget = debug_budget(timeout, retries, backoff_seconds)
    if budget < _MIN_RETRY_BUDGET_SECONDS:
        # Below this the subprocess cap lands under the CLI's own `--timeout`
        # floor, so we would SIGKILL it before it could self-terminate with a
        # parseable envelope — the #2776 bug, rebuilt from the other side.
        _fail(
            f"run_debug budget of {budget}s is below the {_MIN_RETRY_BUDGET_SECONDS}s "
            "floor (the CLI timeout minimum plus its headroom); raise `budget` or "
            "`timeout`"
        )
    deadline = time.monotonic() + budget
    out_of_budget = False

    for attempt in range(retries):
        attempt_cap = min(timeout, int(deadline - time.monotonic()))
        cli_timeout = max(
            _MIN_CLI_TIMEOUT_SECONDS, attempt_cap - _CLI_TIMEOUT_HEADROOM_SECONDS
        )
        try:
            r = subprocess.run(
                [*cmd, "--timeout", str(cli_timeout)],
                capture_output=True,
                text=True,
                timeout=attempt_cap,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            # The CLI's own --timeout never fired, so the stall is upstream of
            # polling. Keep the partial output rather than dying on a traceback.
            _LAST_DEBUG_RAW = _as_text(exc.stdout)
            _fail_with_capture(
                f"flow debug exceeded the {attempt_cap}s subprocess cap without returning "
                f"(CLI --timeout was {cli_timeout}s, so the stall is upstream of "
                "polling: solution upload, Studio Web debug provisioning, "
                "begin-session, or create-instance).\n"
                f"stdout: {_as_text(exc.stdout)}\nstderr: {_as_text(exc.stderr)}"
            )
        _LAST_DEBUG_RAW = r.stdout
        if r.returncode == 0 or not _is_transient_debug_error(r):
            break
        if _is_poll_timeout(r) and attempt + 1 >= _POLL_TIMEOUT_ATTEMPTS:
            break
        if attempt + 1 < retries:
            left = deadline - time.monotonic() - backoff_seconds
            if left < _MIN_RETRY_BUDGET_SECONDS:
                out_of_budget = True
                break
            time.sleep(backoff_seconds)

    if r.returncode != 0:
        spent = (
            f" (stopped after {attempt + 1} attempt(s): the remaining budget "
            "could not fund another)"
            if out_of_budget
            else ""
        )
        _fail(
            f"flow debug exit {r.returncode}{spent}\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )
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


def assert_loop_body_nodes_parented(
    *, project_glob: str = "**/project.uiproj"
) -> None:
    """Assert every node wired inside a loop body has ``parentId`` set to the
    loop's ID. Without ``parentId``, the runtime executes the node outside the
    loop context — per-iteration variables like ``currentItem`` are
    inaccessible and outputs come back null."""
    project_dir = _find_project(project_glob)
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        nodes_by_id = {n["id"]: n for n in flow.get("nodes") or []}
        edges = flow.get("edges") or []
        loops = [n for n in nodes_by_id.values() if n.get("type") == "core.logic.loop"]
        for loop_node in loops:
            loop_id = loop_node["id"]
            body_ids = _collect_loop_body_ids(loop_id, edges, nodes_by_id)
            for nid in body_ids:
                node = nodes_by_id[nid]
                actual_parent = node.get("parentId")
                if actual_parent != loop_id:
                    _fail(
                        f"Node {nid!r} is wired inside loop {loop_id!r} but "
                        f"{'has no parentId' if actual_parent is None else f'has parentId={actual_parent!r}'}. "
                        f"Add \"parentId\": \"{loop_id}\" to the node."
                    )


def _collect_loop_body_ids(
    loop_id: str, edges: list[dict], nodes_by_id: dict[str, dict]
) -> list[str]:
    """Walk edges from a loop's ``start`` port and collect reachable node IDs,
    stopping at the loop's ``continue`` and ``break`` ports."""
    outgoing: dict[str, list[tuple[str, str, str]]] = {}
    for e in edges:
        src = e.get("sourceNodeId", "")
        src_port = e.get("sourcePort", "")
        tgt = e.get("targetNodeId", "")
        tgt_port = e.get("targetPort", "")
        outgoing.setdefault(src, []).append((src_port, tgt, tgt_port))
    body: list[str] = []
    visited: set[str] = set()
    stack = [
        tgt
        for src_port, tgt, _ in outgoing.get(loop_id, [])
        if src_port == "start" and tgt != loop_id
    ]
    while stack:
        nid = stack.pop()
        if nid in visited or nid == loop_id:
            continue
        visited.add(nid)
        if nid not in nodes_by_id:
            continue
        body.append(nid)
        for _, tgt, tgt_port in outgoing.get(nid, []):
            if tgt == loop_id and tgt_port in ("continue", "break"):
                continue
            if tgt not in visited:
                stack.append(tgt)
    return body


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

    NOTE: ``variables.globals`` holds every global — ``in`` as well as ``out``
    — so this includes the flow's own INPUT values. That is deliberate for
    callers doing a "did the run produce anything at all" check, but it makes
    the set unsafe for grading a needle that is also an input. See
    :func:`assert_outputs_contain`, which subtracts the declared inputs.
    """
    return _global_leaves(payload)


def _global_leaves(payload: dict, *, skip_keys: Iterable[str] = ()) -> list[Any]:
    """Flattened global + element-output leaves, optionally skipping globals by
    key. ``skip_keys`` is how :func:`assert_outputs_contain` drops declared
    inputs; element outputs are never skipped (they are genuine node results)."""
    skip = {str(k).lower() for k in skip_keys}
    out: list[Any] = []
    variables = _get_ci(payload, "variables", "Variables") or {}
    for key, val in (_get_ci(variables, "globals", "Globals") or {}).items():
        if str(key).lower() in skip:
            continue
        out.extend(_leaves(val))
    for v in _get_ci(variables, "globalVariables", "GlobalVariables") or []:
        name = str(_get_ci(v, "id", "Id", "name", "Name") or "")
        if name.lower() in skip:
            continue
        value = _get_ci(v, "value", "Value")
        if value is not None:
            out.extend(_leaves(value))
    for e in _get_ci(variables, "elements", "Elements") or []:
        out.extend(_leaves(_get_ci(e, "outputs", "Outputs") or {}))
    return out


def _declared_input_global_keys(
    payload: dict, *, project_dir: str | None = None
) -> set[str]:
    """Return the ``variables.globals`` keys that hold INPUT values, not results.

    Three signals, unioned, because no single one is complete. All are cheap:
    none of them globs the filesystem, which matters because the module is
    imported from an arbitrary CWD (at a repo root, ``**/*.flow`` matches
    hundreds of unrelated flows through a ``plugins/`` symlink loop and would
    read whichever one sorted first).

    1. **Key shape.** A trigger-scoped input is keyed
       ``<triggerNodeId>.output.<varId>`` at runtime — e.g.
       ``start.output.inputDoc``. Outputs are keyed by bare id (``fileName``),
       so this shape is unambiguously an input.
    2. **What the checker itself bound.** :func:`run_debug` stashes the variable
       ids it passed via ``--inputs`` / ``--attachment``. Those are inputs by
       construction, and this is exact — no parsing, no guessing. It covers the
       plain (non-trigger) inputs that signal 1 cannot see.
    3. **Source declaration.** Reads the project's first ``.flow`` and collects
       ``variables.globals[].id`` where ``direction == "in"``. Catches inputs the
       checker never passed — an ``in`` global with a ``defaultValue`` still gets
       a runtime value and still echoes. The project defaults to the one
       :func:`run_debug` resolved, so this needs no per-call-site opt-in;
       ``project_dir`` overrides it for a caller holding a payload from
       elsewhere. Parse failures degrade to signals 1-2 rather than erroring.

    Why not read direction from the payload? The runtime does return a
    ``variables.globalDefinitions`` map, but it carries only ``name`` and
    ``type`` — no direction — so it cannot separate an input from an output::

        "globalDefinitions": {"start.output.inputDoc": {"name": "inputDoc", "type": "file"},
                              "fileName": {"name": "fileName", "type": "string"}}

    Verified against a live debug payload. It is useful only for mapping a
    trigger-scoped key back to its declared id, which the leaf split below
    already does.
    """
    variables = _get_ci(payload, "variables", "Variables") or {}
    keys = list((_get_ci(variables, "globals", "Globals") or {}).keys())
    keys += [
        str(_get_ci(v, "id", "Id", "name", "Name") or "")
        for v in _get_ci(variables, "globalVariables", "GlobalVariables") or []
    ]

    # Signal 1 — trigger-scoped key shape.
    inputs = {k for k in keys if re.match(r"^[^.]+\.output\.[^.]+$", str(k))}

    # Signals 2 and 3 — ids known to be inputs, matched to keys by exact name or
    # by the leaf of a `<trigger>.output.<id>` key.
    declared = {str(i).lower() for i in _LAST_DEBUG_INPUT_IDS}
    project_dir = project_dir or _LAST_DEBUG_PROJECT_DIR
    if project_dir:
        try:
            flows = sorted(
                glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
            )
            if flows:
                with open(flows[0]) as f:
                    flow = json.load(f)
                src = (
                    flow.get("variables")
                    or flow.get("workflow", {}).get("variables")
                    or {}
                )
                declared |= {
                    str(v["id"]).lower()
                    for v in (src.get("globals") or [])
                    if v.get("direction") == "in" and v.get("id")
                }
        except (OSError, ValueError, KeyError, TypeError):
            pass
    for k in keys:
        if str(k).lower() in declared or str(k).rsplit(".", 1)[-1].lower() in declared:
            inputs.add(k)
    return inputs


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
    payload: dict,
    needles: str | Sequence[str],
    *,
    require_all: bool = True,
    allow_input_echo: bool = False,
    project_dir: str | None = None,
) -> None:
    """Assert the stringified outputs contain the given needle(s), IGNORING the
    flow's own input values.

    ``require_all=True`` (default): every needle must appear.
    ``require_all=False``: at least one needle must appear.

    Input echoes do not count (MST — see below). ``variables.globals`` carries
    every global, ``in`` included, and :func:`_leaves` flattens nested objects —
    so a needle that is also an input is matched by the input's own value and
    the assertion becomes a tautology, passing regardless of what the flow
    computed. Observed live on the file-attachment task: binding
    ``--attachment inputDoc=<random>.txt`` puts the whole attachment object in
    ``globals``, so ``assert_outputs_contain(payload, "<random>.txt")`` passed a
    flow whose End node mapped the output to a hardcoded ``"sample-report.txt"``::

        {"start.output.inputDoc": {"ID": ..., "FullName": "evidence-<rand>.txt", ...},
         "fileName": "sample-report.txt"}

    Declared inputs are therefore subtracted before matching (see
    :func:`_declared_input_global_keys`). When a needle is absent from the
    outputs but WOULD have matched an input, the failure says so explicitly
    rather than reporting a bare "missing" — that case means the check was
    previously passing vacuously and the task needs a real output assertion,
    usually :func:`assert_named_output_contains`.

    Inputs this checker never passed are covered too — an ``in`` global with a
    ``defaultValue`` also echoes — by reading the project :func:`run_debug`
    resolved; ``project_dir`` overrides that. ``allow_input_echo=True``
    restores the old whole-payload behavior for the rare check that legitimately
    grades a round-trip; prefer naming the output variable instead, so the
    subtraction is never a reason to weaken an assertion elsewhere.
    """
    if isinstance(needles, str):
        needles = [needles]
    all_leaves = _stringify(collect_outputs(payload))
    if allow_input_echo:
        haystack = all_leaves
        input_keys: set[str] = set()
    else:
        input_keys = _declared_input_global_keys(payload, project_dir=project_dir)
        haystack = _stringify(_global_leaves(payload, skip_keys=input_keys))
    present = [n for n in needles if n.lower() in haystack]
    missing = [n for n in needles if n.lower() not in haystack]
    ok = len(missing) == 0 if require_all else len(present) > 0
    if not ok:
        mode = "all of" if require_all else "any of"
        echo_only = [n for n in missing if n.lower() in all_leaves]
        detail = ""
        if echo_only:
            detail = (
                f"\nINPUT ECHO: {echo_only} appear ONLY in the flow's input globals "
                f"{sorted(input_keys)}, not in its outputs. Before this guard existed "
                f"the match was satisfied by the input itself, so this check passed "
                f"vacuously. Grade the real output instead — "
                f"assert_named_output_contains(payload, '<outVarId>', ...)."
            )
        _fail_with_capture(
            f"Outputs missing {mode} {list(needles)}; present={present}; "
            f"missing={missing}\nOutputs: {haystack[:1000]}{detail}"
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


def normalized(value: Any, *, case_fold: bool = True) -> Any:
    """Normalize a scalar output for equality comparison: trim strings, coerce
    ``"true"``/``"false"`` to booleans, and (by default) fold case for enum-like
    values. Pass ``case_fold=False`` for OPAQUE identifiers (correlation ids,
    Jira keys) that must match exactly."""
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered if case_fold else text
    return value


def assert_named_equals(
    payload: dict, name: str, expected: Any, *, case_sensitive: bool = False
) -> None:
    """Assert a named ``out`` variable is present, non-empty, and equals
    ``expected``. Enum-like values compare case-insensitively; pass
    ``case_sensitive=True`` for opaque identifiers (caseKey, jiraIssueKey)."""
    actual = assert_output_nonempty(payload, name)
    if normalized(actual, case_fold=not case_sensitive) != normalized(
        expected, case_fold=not case_sensitive
    ):
        _fail(f"output {name!r}: expected {expected!r}, got {actual!r}")


_SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")


def _op_matches(hint: str, text: str) -> bool:
    """Separator- and case-insensitive operation match. A connector op is spelled
    hyphenated in a native node type (``…send-message-to-channel``) but with
    underscores (and a version suffix) in an HTTP-proxy endpoint path
    (``/send_message_to_channel_v2``). Fold both to letters-only so either shape
    of the same op matches."""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    return norm(hint) in norm(text)


def _is_connector_node(n: dict) -> bool:
    """True if ``n`` is ANY connector invocation — a native connector node, or a
    connector-authenticated ``core.action.http`` proxy (authentication=connector +
    a targetConnector/connectorKey + a bound connectionId). Connector-agnostic
    (no key/op filter): used to reject error handlers that merely route into
    another fallible connector, whichever form that connector takes."""
    t = str(n.get("type", ""))
    if "uipath.connector." in t:
        return True
    detail = (n.get("inputs") or {}).get("detail") or {}
    if not isinstance(detail, dict):
        return False
    body = detail.get("bodyParameters") or {}
    body = body if isinstance(body, dict) else {}
    target = body.get("targetConnector") or body.get("connectorKey")
    return bool(
        t.lower().startswith("core.action.http")
        and target
        and str(body.get("authentication") or "").lower() == "connector"
        and _non_empty_binding_value(detail.get("connectionId"))
    )


def _connector_node_ids(
    connector_key: str, project_glob: str, *, native_op_hint: str | None = None
) -> set:
    """Node ids that reach ``connector_key`` — a native connector node OR a
    connector-mode ``core.action.http`` proxy carrying real connector auth
    (authentication=connector + non-empty connectionId + connectionFolderKey),
    the same shapes :func:`assert_flow_uses_connector_target` accepts. Shared so
    the message check and the branch-routing check agree on what counts.

    ``native_op_hint`` pins the operation: when set, a node counts only if the
    hint (e.g. ``send-message-to-channel``) appears in its node type — so a Slack
    *read/search* activity that merely contains ``connector_key`` is not accepted
    as send/delivery evidence."""
    ids: set = set()
    for n in _iter_flow_nodes(project_glob):
        t = str(n.get("type", ""))
        if connector_key in t and (native_op_hint is None or _op_matches(native_op_hint, t)):
            ids.add(n.get("id"))
            continue
        detail = (n.get("inputs") or {}).get("detail") or {}
        if not isinstance(detail, dict):
            continue
        body = detail.get("bodyParameters") or {}
        body = body if isinstance(body, dict) else {}
        target = str((body.get("targetConnector") or body.get("connectorKey") or "")).lower()
        # For connector-mode HTTP proxies the operation lives in the endpoint, not
        # the node type; pin via a separator-insensitive match on the serialized
        # detail so a proxy to the documented /send_message_to_channel_v2 endpoint
        # is accepted while a proxy to a read endpoint is excluded.
        op_ok = native_op_hint is None or _op_matches(native_op_hint, json.dumps(detail))
        if (
            t.lower().startswith("core.action.http")
            and target == connector_key.lower()
            and str(body.get("authentication") or "").lower() == "connector"
            and _non_empty_binding_value(detail.get("connectionId"))
            and _non_empty_binding_value(detail.get("connectionFolderKey"))
            and op_ok
        ):
            ids.add(n.get("id"))
    return ids


def find_node_output_field(payload: dict, field: str, *, node_ids=None) -> "str | None":
    """Return the first non-empty string value of ``field`` found in a node's
    ``.output`` object (``globals["<id>.output"]``). Used to require an
    intermediate Script output (e.g. ``nextSteps``) that the flow computes but
    does not map to a named End ``out``. The field name is matched
    separator/case-insensitively (``next_steps`` matches ``nextSteps``).

    Pass ``node_ids`` to restrict the search to specific nodes (e.g. the executed
    classification Script) so an unrelated/cosmetic node can't supply the value."""
    gvars = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    if not isinstance(gvars, dict):
        return None
    allow = set(node_ids) if node_ids is not None else None
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    want = norm(field)
    for k, v in gvars.items():
        if not (isinstance(k, str) and k.endswith(".output") and isinstance(v, dict)):
            continue
        if allow is not None and k[: -len(".output")] not in allow:
            continue
        for kk, vv in v.items():
            if isinstance(kk, str) and norm(kk) == want and isinstance(vv, str) and vv.strip():
                return vv.strip()
    return None


_UNSET = object()


def find_node_output_value(payload: dict, field: str, *, node_ids=None) -> Any:
    """Like :func:`find_node_output_field` but returns the raw value of any type
    (bool, number, string) — the first non-None ``field`` found in a node's
    ``.output``. Returns ``None`` when absent. Use for intermediate classification
    outputs like ``engineeringNeeded`` (a boolean) that aren't mapped to a named
    End ``out``. Field name matched separator/case-insensitively.

    Pass ``node_ids`` to restrict the search to specific nodes (e.g. the executed
    classification Script) so an unrelated/cosmetic node can't supply the value."""
    gvars = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    if not isinstance(gvars, dict):
        return None
    allow = set(node_ids) if node_ids is not None else None
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    want = norm(field)
    for k, v in gvars.items():
        if not (isinstance(k, str) and k.endswith(".output") and isinstance(v, dict)):
            continue
        if allow is not None and k[: -len(".output")] not in allow:
            continue
        for kk, vv in v.items():
            if isinstance(kk, str) and norm(kk) == want and vv is not None:
                return vv
    return None


def assert_slack_message_posted(
    payload: dict,
    name: str,
    *,
    connector_key: str = "uipath-salesforce-slack",
    project_glob: str = "**/project.uiproj",
    expected_channel: str | None = None,
    must_contain: "str | list[str] | None" = None,
    must_contain_loose: "str | list[str] | None" = None,
    send_op: str = "send-message-to-channel",
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

    # A Slack SEND node (native send-message-to-channel, or a connector-mode HTTP
    # proxy to that op) — a read/search activity that returns a message object is
    # not delivery evidence, so it is excluded via send_op.
    slack_ids = _connector_node_ids(connector_key, project_glob, native_op_hint=send_op)
    if not slack_ids:
        _fail(f"no connected {connector_key} {send_op} node found in the flow")

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
        if must_contain or must_contain_loose:
            content = " ".join(str(x) for x in _leaves(matched_out) if isinstance(x, str))
        if must_contain:
            required = [must_contain] if isinstance(must_contain, str) else list(must_contain)
            missing = [s for s in required if s not in content]
            if missing:
                _fail_with_capture(
                    f"posted Slack message is missing required text {missing} — the "
                    "message must carry every required field (severity, correlationId, "
                    "next steps), not just some"
                )
        if must_contain_loose:
            loose = [must_contain_loose] if isinstance(must_contain_loose, str) else list(must_contain_loose)
            # Separator/case-insensitive: the escalationPath enum "unknown_customer"
            # matches a rendered "unknown customer" / "Unknown Customer" too.
            missing_loose = [s for s in loose if not _op_matches(s, content)]
            if missing_loose:
                _fail_with_capture(
                    f"posted Slack message is missing required field(s) {missing_loose} "
                    "(separator/case-insensitive) — e.g. the escalationPath"
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


def completed_node_ids_of_type(
    payload: dict, type_hint: str, *, project_glob: str = "**/project.uiproj"
) -> set:
    """Return ids of flow nodes whose ``type`` contains ``type_hint`` that have a
    ``Completed`` elementExecution in this run — the executed subset of that node
    type. Used to tie structural checks (e.g. Decision branch routing) to the node
    that actually ran, not merely one present in the source."""
    ids = {
        n.get("id")
        for n in _iter_flow_nodes(project_glob)
        if type_hint in str(n.get("type", ""))
    }
    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    return {
        _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId")
        for e in els
        if _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId") in ids
        and str(_get_ci(e, "status", "Status")).lower() == "completed"
    }


def assert_connector_error_handlers(
    connector_key: str,
    *,
    project_glob: str = "**/project.uiproj",
    native_op_hint: "str | None" = None,
) -> None:
    """Assert every matching connector node degrades gracefully on failure: its
    ``error`` port must route to a NON-connector handler (not a self-loop back to
    the failing node, and not another connector that can fault again) from which a
    terminating node (End, or a node with no outgoing edge) is reachable. A
    dangling error port, a self-loop, or an error edge into another connector all
    fail, so a flow that only appears to handle failures cannot get full credit."""
    from collections import defaultdict, deque

    flow = _load_flow(project_glob)
    edges = flow.get("edges") or []
    nodes = {n.get("id"): n for n in (flow.get("nodes") or [])}
    node_ids = {i for i in _connector_node_ids(connector_key, project_glob, native_op_hint=native_op_hint) if i}
    if not node_ids:
        _fail(f"no {connector_key} node found to check error handlers on")

    adj = defaultdict(list)
    for e in edges:
        adj[e.get("sourceNodeId")].append((str(e.get("sourcePort") or "").lower(), e.get("targetNodeId")))

    def is_connector(nid: str) -> bool:
        # Native connector OR a connector-authenticated HTTP proxy — an error edge
        # into either just invokes another fallible connector, not a real handler.
        return _is_connector_node(nodes.get(nid, {}) or {})

    # EVERY branch of the handler must degrade gracefully: connector-free, acyclic,
    # and terminating. A DFS with GRAY/BLACK coloring rejects (a) any connector on
    # the path (can fault again), and (b) any cycle — a back-edge to a GRAY node is
    # a loop that never completes. Returns True only when all reachable paths end at
    # a terminating node, so a fork to End + a non-connector cycle no longer passes.
    _GRAY, _BLACK = 1, 2

    def reaches_terminating(start: str) -> bool:
        color: dict = {}

        def dfs(n: str) -> bool:
            if is_connector(n):
                return False  # connector branch can fault → not graceful
            color[n] = _GRAY
            outs = [tgt for _, tgt in adj.get(n, []) if tgt]
            t = str(nodes.get(n, {}).get("type", "")).lower()
            if "end" in t or not outs:  # End node, or non-connector dead-end handler
                color[n] = _BLACK
                return True
            for tgt in outs:
                c = color.get(tgt, 0)
                if c == _GRAY:
                    return False  # back-edge → cycle: this branch never terminates
                if c == _BLACK:
                    continue  # already validated as gracefully terminating
                if not dfs(tgt):
                    return False
            color[n] = _BLACK
            return True

        return dfs(start)

    bad = []
    for sid in sorted(nid for nid in node_ids if nid):
        # Non-connector error targets, excluding a self-loop back to the send node.
        handlers = [
            t for p, t in adj.get(sid, [])
            if p == "error" and t and t != sid and not is_connector(t)
        ]
        if not handlers:
            bad.append((sid, "no non-connector error handler (dangling, self-loop, or into another connector)"))
        elif not any(reaches_terminating(h) for h in handlers):
            bad.append((sid, "error handler does not reach a terminating path"))
    if bad:
        _fail_with_capture(
            f"{connector_key} node(s) do not degrade gracefully on failure: {bad}"
        )


def assert_connector_send_identity(
    connector_key: str,
    *,
    expected: str = "user",
    param: str = "send_as",
    project_glob: str = "**/project.uiproj",
    native_op_hint: "str | None" = None,
) -> None:
    """Assert every matching connector send node carries the requested identity
    binding (``queryParameters.<param> == expected``, e.g. ``send_as == "user"``).
    A node that sends as the default bot instead of the prompt-required ``user``
    fails here even though its runtime response (ts/channel/content) looks the same."""
    send_ids = {i for i in _connector_node_ids(connector_key, project_glob, native_op_hint=native_op_hint) if i}
    if not send_ids:
        _fail(f"no {connector_key} send node found to check {param!r} on")
    bad = []
    for n in _iter_flow_nodes(project_glob):
        if n.get("id") not in send_ids:
            continue
        detail = (n.get("inputs") or {}).get("detail") or {}
        qp = detail.get("queryParameters") if isinstance(detail, dict) else None
        val = str((qp or {}).get(param, "")).strip().lower()
        if val != expected.strip().lower():
            bad.append((n.get("id"), val or None))
    if bad:
        _fail_with_capture(
            f"{connector_key} send node(s) do not set {param}={expected!r}: {bad}; "
            "the prompt requires sending as the requested identity"
        )


def node_output_leaves(payload: dict, node_ids) -> set:
    """String leaves of the given nodes' outputs (``globals["<id>.output"]``) —
    used to tie a flow output back to the connector node that actually produced
    it (e.g. a Jira key must appear in the executed Create Issue node's response)."""
    gvars = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    out: set = set()
    for nid in node_ids:
        v = gvars.get(f"{nid}.output") if isinstance(gvars, dict) else None
        for x in _leaves(v):
            if isinstance(x, str):
                out.add(x.strip())
    return out


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
    executed_decision_ids: "set | None" = None,
) -> None:
    """Assert some ``decision_type`` node has TWO distinct outgoing ports whose
    downstream reach separates ``branch_a_targets`` from ``branch_b_targets`` —
    i.e. the Decision itself routes to the two target groups (all A reachable from
    one port, all B from another, with no cross-contamination). Proves the two
    groups are the Decision's branches, not just nodes that happened to fire on
    different cases behind a cosmetic always-true Decision.

    When ``executed_decision_ids`` is given, only Decisions that actually executed
    in the run are considered candidates — so a second, unexecuted Decision that
    merely has the two source edges cannot satisfy the check while routing really
    happens through a cosmetic Decision elsewhere."""
    from collections import defaultdict, deque

    flow = _load_flow(project_glob)
    edges = flow.get("edges") or []
    nodes = flow.get("nodes") or []
    decisions = [n.get("id") for n in nodes if decision_type in str(n.get("type", ""))]
    if executed_decision_ids is not None:
        decisions = [d for d in decisions if d in executed_decision_ids]
        if not decisions:
            _fail_with_capture(
                f"no EXECUTED {decision_type!r} node in the run "
                f"(executed={sorted(i for i in executed_decision_ids if i)}); routing did "
                "not go through a Decision that actually ran"
            )
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


def assert_distinct_branch_ends(
    branch_a_nodes: set,
    branch_b_nodes: set,
    *,
    end_type: str = "core.control.end",
    project_glob: str = "**/project.uiproj",
) -> None:
    """Assert each branch reaches its OWN End node — the prompt's two-End-nodes
    requirement. From the ``branch_a``/``branch_b`` nodes (e.g. the escalation vs
    triage Slack sends) BFS downstream to reachable ``end_type`` nodes; require an
    End reachable from A but not B AND one reachable from B but not A. A flow that
    merges both branches into a single shared End (then conditionally maps the
    timestamp) fails here."""
    from collections import defaultdict, deque

    flow = _load_flow(project_glob)
    edges = flow.get("edges") or []
    nodes = flow.get("nodes") or []
    end_ids = {n.get("id") for n in nodes if end_type in str(n.get("type", ""))}
    adj = defaultdict(list)
    for e in edges:
        adj[e.get("sourceNodeId")].append(e.get("targetNodeId"))

    def reachable_ends(starts: set) -> set:
        seen: set = set()
        q = deque(s for s in starts if s)
        found: set = set()
        while q:
            n = q.popleft()
            if n in seen:
                continue
            seen.add(n)
            if n in end_ids:
                found.add(n)
            for t in adj.get(n, []):
                if t:
                    q.append(t)
        return found

    ends_a = reachable_ends(set(branch_a_nodes))
    ends_b = reachable_ends(set(branch_b_nodes))
    if not (ends_a - ends_b) or not (ends_b - ends_a):
        _fail_with_capture(
            "escalation and triage branches do not each reach their OWN End node "
            f"(escalation-reachable ends={sorted(ends_a)}, triage-reachable ends={sorted(ends_b)}); "
            "the prompt requires two branch-specific End nodes, not a single merged End"
        )


def completed_connector_node_ids(
    payload: dict,
    connector_key: str,
    *,
    project_glob: str = "**/project.uiproj",
    native_op_hint: "str | None" = None,
) -> set:
    """Return the ids of ``connector_key`` nodes with a ``Completed``
    elementExecution in this run — i.e. which connector node actually fired.
    Used to prove branch routing across cases (escalation vs triage must fire
    different nodes, not one dynamic node behind a cosmetic Decision).

    ``native_op_hint`` pins the operation so a connector-mode HTTP proxy (whose
    ``targetConnector`` is the bare key, with the op in the endpoint) is matched by
    op — pass ``connector_key`` as the bare key and the op separately."""
    ids = _connector_node_ids(connector_key, project_glob, native_op_hint=native_op_hint)
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


# A project whose ``.flow`` declares at most this many nodes is an abandoned
# `flow init` scaffold, not a build: init seeds a single trigger node.
_HUSK_MAX_NODES = 1


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

    Two Flow projects can also mean one build plus one abandoned scaffold —
    see :func:`_split_off_scaffold_husks`. Anything else stays a refusal.
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
        counts = [(p, _flow_node_count(os.path.dirname(p))) for p in flow_projects]
        selected, husks = _split_off_scaffold_husks(counts)
        if selected is not None:
            listed = ", ".join(_describe_candidate(p, n) for p, n in husks)
            print(f"note: ignoring {len(husks)} abandoned scaffold(s): {listed}")
            return os.path.dirname(selected)
        joined = "\n  - ".join(_describe_candidate(p, n) for p, n in counts)
        _fail(
            f"Multiple Flow projects match {pattern!r} — refusing to guess:\n  - {joined}"
        )
    return os.path.dirname(flow_projects[0])


def _split_off_scaffold_husks(
    counts: list[tuple[str, int | None]],
) -> tuple[str | None, list[tuple[str, int | None]]]:
    """Separate the one project carrying real work from abandoned init husks.

    `uip maestro flow init` run outside a solution auto-scaffolds a duplicate
    `<Project>Solution/` holding a trigger-only project (cli#2470). An agent that
    then rebuilds in the right solution leaves two `project.uiproj` files, one of
    which is dead weight — a configuration this checker used to refuse outright.

    Returns ``(selected, husks)`` only when exactly one candidate has a known
    node count above the husk ceiling and every other candidate has a known
    count at or below it. Any unknown count (missing / unreadable / malformed
    ``.flow``) makes the split ambiguous, so the caller keeps refusing.
    """
    substantive = [(p, n) for p, n in counts if n is None or n > _HUSK_MAX_NODES]
    husks = [(p, n) for p, n in counts if n is not None and n <= _HUSK_MAX_NODES]
    if len(substantive) != 1 or substantive[0][1] is None:
        return None, []
    return substantive[0][0], husks


def _flow_node_count(project_dir: str) -> int | None:
    """Total ``nodes`` declared across every ``.flow`` under ``project_dir``.

    ``None`` means unknown — no ``.flow``, or one that will not parse. Unknown is
    never read as a husk.
    """
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        return None
    total = 0
    for path in flows:
        try:
            with open(path, encoding="utf-8") as f:
                flow = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        nodes = flow.get("nodes") if isinstance(flow, dict) else None
        if not isinstance(nodes, list):
            return None
        total += len(nodes)
    return total


def _describe_candidate(project_uiproj: str, node_count: int | None) -> str:
    project_dir = os.path.dirname(project_uiproj)
    if node_count is None:
        return f"{project_dir} (node count unknown — .flow missing or unreadable)"
    return f"{project_dir} ({node_count} node{'' if node_count == 1 else 's'})"


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
