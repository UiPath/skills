"""Shared helpers for uipath-maestro-case single-node e2e checks.

Locates the generated `caseplan.json`, runs ``uip maestro case validate``,
and asserts that a task of the expected ``type`` exists somewhere in the
case definition. ``case-management`` tasks are allowed to land as skeletons
(empty ``data``) when the referenced sub-case isn't published on the tenant
— the test only cares that the task ``type`` was written correctly.

For tasks whose referenced resource is published on the tenant (e.g. the
RPA / Agent / API-workflow single-node tests), this module also provides
``run_debug``: runs ``uip solution resource refresh`` then
``uip maestro case debug`` and returns the parsed JSON payload so callers
can assert on declared output values. Mirrors the uipath-maestro-flow
``flow_check.run_debug`` shape.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence


def find_caseplan(pattern: str = "**/caseplan.json") -> str:
    matches = sorted(
        p for p in glob.glob(pattern, recursive=True) if "/.venv/" not in p
    )
    if not matches:
        _fail(f"No caseplan.json found matching {pattern}")
    if len(matches) > 1:
        joined = "\n  - ".join(matches)
        _fail(f"Multiple caseplan.json files match {pattern!r}:\n  - {joined}")
    return matches[0]


def read_caseplan(path: str | None = None) -> dict:
    p = path or find_caseplan()
    with open(p) as f:
        return json.load(f)


def iter_tasks(plan: dict):
    """Yield every task dict from every Stage / ExceptionStage node.

    Tolerates a mis-nested FLAT ``data.tasks`` (``Task[]`` instead of the schema's
    ``Task[][]`` lanes) so callers don't crash on it — use ``assert_tasks_nested``
    to reject that shape explicitly.
    """
    for node in plan.get("nodes") or []:
        node_type = node.get("type") or ""
        if not node_type.endswith("Stage") and "Stage" not in node_type:
            continue
        lanes = ((node.get("data") or {}).get("tasks")) or []
        for lane in lanes:
            if isinstance(lane, dict):  # flat (mis-nested) task — yield directly
                yield lane
            elif isinstance(lane, list):
                for task in lane:
                    if isinstance(task, dict):
                        yield task


def assert_tasks_nested(plan: dict) -> None:
    """Fail unless every stage's ``data.tasks`` is a 2D ``Task[][]`` (lanes).

    A FLAT ``Task[]`` (a task object where a lane array is expected) silently
    passes ``uip maestro case validate`` — the CLI reads each task dict as an
    empty lane, so it reports 0 tasks / 0 warnings — yet it is not a buildable
    case plan. Reject it explicitly so the test can't false-pass.
    """
    bad = []
    for node in plan.get("nodes") or []:
        if "Stage" not in (node.get("type") or ""):
            continue
        tasks = (node.get("data") or {}).get("tasks") or []
        for i, lane in enumerate(tasks):
            if not isinstance(lane, list):
                label = (node.get("data") or {}).get("label") or node.get("id")
                bad.append(f"{label} (tasks[{i}] is {type(lane).__name__}, not a lane)")
                break
    if bad:
        sys.exit(
            "FAIL: data.tasks must be a 2D array Task[][] (outer=lanes, "
            "inner=tasks); these stages have a FLAT tasks array: "
            + "; ".join(bad)
            + ". A flat tasks array silently passes `validate` with 0 tasks "
            "detected and is not a buildable case plan."
        )


def find_tasks_of_type(plan: dict, task_type: str) -> list[dict]:
    return [t for t in iter_tasks(plan) if t.get("type") == task_type]


def assert_validate_passes(caseplan_path: str, *, timeout: int = 60) -> None:
    cmd = ["uip", "maestro", "case", "validate", caseplan_path, "--output", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        _fail(
            f"uip maestro case validate exit {r.returncode}\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )


def assert_task_type_present(task_type: str, *, caseplan_path: str | None = None) -> dict:
    plan = read_caseplan(caseplan_path)
    matches = find_tasks_of_type(plan, task_type)
    if not matches:
        types_seen = sorted({t.get("type", "?") for t in iter_tasks(plan)})
        _fail(
            f"No task with type={task_type!r} found in caseplan. "
            f"Task types seen: {types_seen}"
        )
    return matches[0]


def task_is_skeleton(task: dict) -> bool:
    """True when the task's resource hasn't been wired into ``data``.

    v20 caseplan markers for a populated task:
    - ``execute-connector-activity`` / ``wait-for-connector``: ``data.typeId`` AND ``data.connectionId``
    - ``action``: ``data.inputs`` present (bare ``taskTitle`` / ``priority`` is still skeleton-equivalent)
    - everything else (``process`` / ``agent`` / ``rpa`` / ``api-workflow`` / ``case-management``):
      ``data.name`` AND ``data.folderPath`` (both as ``=bindings.<id>`` refs)
    """
    data = task.get("data") or {}
    if not data:
        return True
    task_type = task.get("type")
    if task_type in {"execute-connector-activity", "wait-for-connector"}:
        return not (data.get("typeId") and data.get("connectionId"))
    if task_type == "action":
        return "inputs" not in data
    return not (data.get("name") and data.get("folderPath"))


# ── Schema-aware structural helpers ─────────────────────────────────────────
#
# v19 wraps case-level metadata under a `root` node; v20 hoists it to the
# top-level + a `metadata` block. Node and edge internals are identical.


def _is_v20(plan: dict) -> bool:
    """Return True if ``plan`` is v20 schema (top-level metadata)."""
    if not isinstance(plan, dict):
        return False
    version = plan.get("version") or ""
    if isinstance(version, str) and version.startswith("20"):
        return True
    return "metadata" in plan and isinstance(plan.get("metadata"), dict)


def assert_count(actual: int, expected: int, what: str) -> None:
    if actual != expected:
        _fail(f"expected {expected} {what}, got {actual}")


def iter_nodes_of_type(plan: dict, node_type: str):
    for node in plan.get("nodes") or []:
        if node.get("type") == node_type:
            yield node


def find_stages(plan: dict, *, include_exception: bool = False) -> list[dict]:
    types = {"case-management:Stage"}
    if include_exception:
        types.add("case-management:ExceptionStage")
    return [n for n in plan.get("nodes") or [] if n.get("type") in types]


def find_triggers(plan: dict) -> list[dict]:
    return list(iter_nodes_of_type(plan, "case-management:Trigger"))


def find_node_by_label(plan: dict, label: str) -> dict:
    for node in plan.get("nodes") or []:
        if (node.get("data") or {}).get("label") == label:
            return node
    labels = [(n.get("data") or {}).get("label") for n in plan.get("nodes") or []]
    _fail(f"no node with data.label={label!r}; available labels: {labels}")


def find_edges(
    plan: dict, *, source: str | None = None, target: str | None = None
) -> list[dict]:
    out: list[dict] = []
    for edge in plan.get("edges") or []:
        if source is not None and edge.get("source") != source:
            continue
        if target is not None and edge.get("target") != target:
            continue
        out.append(edge)
    return out


def edge_labels_from(plan: dict, source_id: str) -> list[str]:
    return [
        (e.get("data") or {}).get("label") or ""
        for e in find_edges(plan, source=source_id)
    ]


def first_rule_of_condition(cond: dict | None) -> dict | None:
    """Return the first rule of a DNF condition: ``cond.rules[0][0]``."""
    if not cond:
        return None
    rules = cond.get("rules") or []
    if not rules:
        return None
    first_group = rules[0] or []
    if not first_group:
        return None
    return first_group[0]


def iter_stage_entry_conditions(node: dict):
    for cond in (node.get("data") or {}).get("entryConditions") or []:
        yield cond


def iter_stage_exit_conditions(node: dict):
    for cond in (node.get("data") or {}).get("exitConditions") or []:
        yield cond


def get_variables(plan: dict) -> dict:
    """Return ``{inputs, outputs, inputOutputs}`` — top-level in v20, ``root.data.uipath.variables`` in v19."""
    if _is_v20(plan):
        return plan.get("variables") or {}
    root = get_root(plan)
    return ((root.get("data") or {}).get("uipath") or {}).get("variables") or {}


def get_bindings(plan: dict) -> list[dict]:
    if _is_v20(plan):
        return plan.get("bindings") or []
    root = get_root(plan)
    return ((root.get("data") or {}).get("uipath") or {}).get("bindings") or []


def get_case_exit_conditions(plan: dict) -> list[dict]:
    """v19 ``root.caseExitConditions`` / v20 ``metadata.caseExitRules`` — field rename, identical shape."""
    if _is_v20(plan):
        return (plan.get("metadata") or {}).get("caseExitRules") or []
    root = get_root(plan)
    return root.get("caseExitConditions") or []


def get_sla_rules(target: dict) -> list[dict]:
    """Return ``slaRules[]`` from a plan (case-level) or a stage node.

    Case-level in v20 lives under ``metadata.slaRules``; v19 under
    ``root.data.slaRules``. Stage-level lives under ``node.data.slaRules``
    in both schemas.
    """
    if "nodes" in target and isinstance(target.get("nodes"), list):
        if _is_v20(target):
            return (target.get("metadata") or {}).get("slaRules") or []
        root = get_root(target)
        return ((root.get("data") or {}).get("slaRules")) or []
    return ((target.get("data") or {}).get("slaRules")) or []


def get_default_sla(target: dict) -> dict | None:
    rules = get_sla_rules(target)
    if not rules:
        return None
    last = rules[-1]
    return last if (last or {}).get("expression") == "=js:true" else None


def get_root(plan: dict) -> dict:
    """Return root-equivalent dict.

    v19: returns the actual ``case-management:root`` node from ``plan.root``
    (or ``plan.nodes`` if embedded). v20: synthesizes a v19-shaped dict so
    legacy paths like ``root.data.uipath.variables`` still resolve.
    """
    if _is_v20(plan):
        metadata = plan.get("metadata") or {}
        synthesized: dict = {
            "id": plan.get("id"),
            "name": plan.get("name"),
            "description": plan.get("description"),
            "version": plan.get("version"),
            "type": "case-management:root",
            "data": {
                "slaRules": metadata.get("slaRules") or [],
                "intsvcActivityConfig": metadata.get("intsvcActivityConfig"),
                "uipath": {
                    "bindings": plan.get("bindings") or [],
                    "variables": plan.get("variables") or {},
                },
            },
            "caseExitConditions": metadata.get("caseExitRules") or [],
        }
        for k, v in metadata.items():
            if k not in {"slaRules", "intsvcActivityConfig", "caseExitRules"}:
                synthesized.setdefault(k, v)
        return synthesized
    if isinstance(plan.get("root"), dict):
        return plan["root"]
    for node in plan.get("nodes") or []:
        if node.get("type") == "case-management:root":
            return node
    _fail("no root found in caseplan (neither v19 root node nor v20 metadata)")


def _stringify(v: Any) -> str:
    return json.dumps(v, default=str)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


# ── Debug helpers ───────────────────────────────────────────────────────────


def find_project_dir(pattern: str = "**/project.uiproj") -> str:
    """Return the directory holding the Case `project.uiproj`. Filters by
    ``ProjectType`` so a sibling Agent / RPA / Coded project in the same
    solution does not collide with the Case project we want to debug.
    """
    candidates = sorted(
        p for p in glob.glob(pattern, recursive=True) if "/.venv/" not in p
    )
    if not candidates:
        _fail(f"No project.uiproj found matching {pattern}")
    case_projects = [p for p in candidates if _is_case_project(p)]
    if not case_projects:
        joined = "\n  - ".join(candidates)
        _fail(
            f"No Case project.uiproj found matching {pattern} — "
            f"candidates exist but none declare ProjectType=\"CaseManagement\":"
            f"\n  - {joined}"
        )
    if len(case_projects) > 1:
        joined = "\n  - ".join(case_projects)
        _fail(
            f"Multiple Case projects match {pattern!r} — refusing to guess:"
            f"\n  - {joined}"
        )
    return os.path.dirname(case_projects[0])


def find_solution_dir(pattern: str = "**/*.uipx") -> str:
    """Return the directory holding the ``*.uipx`` solution manifest.
    Used as ``--solution-folder`` for ``uip solution resource refresh``.
    """
    matches = sorted(
        p for p in glob.glob(pattern, recursive=True) if "/.venv/" not in p
    )
    if not matches:
        _fail(f"No solution manifest found matching {pattern}")
    if len(matches) > 1:
        joined = "\n  - ".join(matches)
        _fail(f"Multiple solution manifests match {pattern!r}:\n  - {joined}")
    return os.path.dirname(matches[0])


def run_debug(
    *,
    timeout: int = 540,
    project_glob: str = "**/project.uiproj",
    solution_glob: str = "**/*.uipx",
    refresh_timeout: int = 120,
) -> dict:
    """Locate the case project, refresh solution resources, run
    ``uip maestro case debug --output json``, and return the parsed
    ``Data`` payload. Exits on any step failing or ``finalStatus`` not
    being ``Completed``.

    Resource refresh is mandatory per the maestro-case skill: without it
    Studio Web cannot resolve connector resources and the debug call
    surfaces a "Resource is not configured" warning instead of running.
    """
    payload = start_debug(
        timeout=timeout,
        project_glob=project_glob,
        solution_glob=solution_glob,
        refresh_timeout=refresh_timeout,
    )
    status = (payload or {}).get("finalStatus")
    if status != "Completed" and status != "Successful":
        _fail(f"Case did not complete (finalStatus={status})\nPayload: {json.dumps(payload, default=str)[:2000]}")
    return payload


def start_debug(
    *,
    timeout: int = 540,
    project_glob: str = "**/project.uiproj",
    solution_glob: str = "**/*.uipx",
    refresh_timeout: int = 120,
) -> dict:
    """Like ``run_debug`` but does NOT require ``finalStatus == Completed``.

    Use for multi-stage cases whose tasks intentionally suspend (wait-for-timer,
    wait-for-connector, wait-for-user, SLA) and therefore never reach a
    Completed status in a single debug run. Returns the parsed ``Data``
    payload so callers can assert structural debug progress.

    Exits if the debug command fails to launch / does not return parseable
    JSON. A non-Completed ``finalStatus`` is NOT a failure here.
    """
    project_dir = find_project_dir(project_glob)
    solution_dir = find_solution_dir(solution_glob)

    refresh_cmd = [
        "uip", "solution", "resource", "refresh",
        "--solution-folder", solution_dir,
        "--output", "json",
    ]
    r = subprocess.run(refresh_cmd, capture_output=True, text=True, timeout=refresh_timeout)
    if r.returncode != 0:
        _fail(
            f"solution resource refresh exit {r.returncode}\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )

    debug_cmd = [
        "uip", "maestro", "case", "debug", project_dir,
        "--log-level", "debug", "--output", "json",
    ]
    r = subprocess.run(debug_cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        _fail(
            f"case debug exit {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}"
        )
    data = _parse_json(r.stdout)
    if data is None:
        _fail(f"Could not parse JSON from case debug\n{r.stdout}")
    payload = data.get("Data") if isinstance(data, dict) and "Data" in data else data
    if not isinstance(payload, dict):
        _fail(f"case debug payload is not a JSON object: {type(payload).__name__}\n{r.stdout[:1000]}")
    return payload


def payload_contains(
    payload: dict, *needles: str, require_all: bool = True
) -> None:
    """Assert that each needle appears (case-insensitive) somewhere in the
    stringified debug payload. Use this for structure-agnostic checks that a
    given stage / task / variable was referenced by the debug run.
    """
    haystack = json.dumps(payload, default=str).lower()
    missing = [n for n in needles if n.lower() not in haystack]
    if require_all and missing:
        _fail(
            f"debug payload missing references: {missing}\n"
            f"Payload (first 2000 chars): {haystack[:2000]}"
        )
    if not require_all and len(missing) == len(needles):
        _fail(
            f"debug payload missing all of: {list(needles)}\n"
            f"Payload (first 2000 chars): {haystack[:2000]}"
        )


# Keys that hold runtime metadata, not task outputs. Excluded from
# output extraction so GUID / timestamp / status digits do not falsely
# match small expected values (e.g. an integer in [0, 120] would match
# any 1-3 digit chunk of an instanceId UUID).
_METADATA_KEYS = frozenset({
    "jobKey", "instanceId", "runId", "solutionId", "finalStatus",
    "status", "studioWebUrl", "createdAt", "startedAt", "endedAt",
    "elementId", "id", "uniqueId", "projectId", "tenantId", "folderId",
    "uipathActivityTypeId", "taskTypeId", "elementInstanceId",
    "timestamp", "occurredAt",
})


def collect_outputs(payload: dict) -> list[Any]:
    """Return the declared output values from a case debug payload.

    The case runtime exposes outputs under a few paths depending on
    schema version — we walk all of them and ignore well-known metadata
    keys. Nested dicts/lists are flattened to leaf values.
    """
    out: list[Any] = []

    variables = payload.get("variables") or {}
    for val in (variables.get("globals") or {}).values():
        out.extend(_leaves(val))
    for v in variables.get("globalVariables") or []:
        if isinstance(v, dict) and "value" in v:
            out.extend(_leaves(v.get("value")))
    for section in ("outputs", "inputOutputs"):
        for v in variables.get(section) or []:
            if isinstance(v, dict) and "value" in v:
                out.extend(_leaves(v.get("value")))

    for task in _iter_runtime_tasks(payload):
        for out_var in task.get("outputs") or []:
            if isinstance(out_var, dict) and "value" in out_var:
                out.extend(_leaves(out_var.get("value")))

    return out


def _iter_runtime_tasks(payload: dict):
    """Yield runtime task execution dicts from anywhere in the payload.

    Case debug nests task executions under stage / lane structures. We
    walk defensively so changes to the runtime shape don't silently
    break the output extraction.
    """
    seen_ids: set[int] = set()
    stack: list[Any] = [payload]
    while stack:
        node = stack.pop()
        if id(node) in seen_ids:
            continue
        seen_ids.add(id(node))
        if isinstance(node, dict):
            if "outputs" in node and (
                "displayName" in node or "taskTypeId" in node or "type" in node
            ):
                yield node
            stack.extend(node.values())
        elif isinstance(node, (list, tuple)):
            stack.extend(node)


def _leaves(v: Any):
    if isinstance(v, dict):
        for k, nested in v.items():
            if k in _METADATA_KEYS:
                continue
            yield from _leaves(nested)
    elif isinstance(v, (list, tuple)):
        for item in v:
            yield from _leaves(item)
    else:
        yield v


def assert_outputs_contain(
    payload: dict, needles: str | Sequence[str], *, require_all: bool = True
) -> None:
    """Assert the stringified outputs contain the given needle(s)."""
    if isinstance(needles, str):
        needles = [needles]
    haystack = _stringify_leaves(collect_outputs(payload))
    present = [n for n in needles if n.lower() in haystack]
    missing = [n for n in needles if n.lower() not in haystack]
    ok = len(missing) == 0 if require_all else len(present) > 0
    if not ok:
        mode = "all of" if require_all else "any of"
        _fail(
            f"Outputs missing {mode} {list(needles)}; present={present}; "
            f"missing={missing}\nOutputs: {haystack[:1000]}"
        )


def assert_output_int_in_range(payload: dict, lo: int, hi: int) -> int:
    """Assert at least one integer in [lo, hi] appears in the outputs.

    Pulls integers from output values only (metadata keys excluded by
    ``collect_outputs``), so GUIDs in jobKey / instanceId can't satisfy
    the range.
    """
    haystack = _stringify_leaves(collect_outputs(payload))
    hits = [int(m) for m in re.findall(r"-?\d+", haystack) if lo <= int(m) <= hi]
    if not hits:
        _fail(
            f"No integer in [{lo}, {hi}] found in outputs\n"
            f"Outputs: {haystack[:1000]}"
        )
    return hits[0]


def _stringify_leaves(values: Iterable[Any]) -> str:
    return json.dumps(list(values), default=str).lower()


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


def _is_case_project(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("ProjectType") == "CaseManagement"
