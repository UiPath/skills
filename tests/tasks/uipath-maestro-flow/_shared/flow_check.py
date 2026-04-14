"""Shared helpers for uipath-maestro-flow e2e checks.

Runs ``uip flow debug --output json`` and asserts:

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
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence


# ── Public helpers ──────────────────────────────────────────────────────────


def run_debug(
    *,
    inputs: dict | None = None,
    timeout: int = 240,
    project_glob: str = "**/project.uiproj",
) -> dict:
    """Locate the project, run ``uip flow debug --output json``, and return the
    parsed ``Data`` payload. Exits on any step failing."""
    project_dir = _find_project(project_glob)
    cmd = ["uip", "flow", "debug", project_dir, "--output", "json"]
    if inputs is not None:
        cmd.extend(["--inputs", json.dumps(inputs)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        _fail(f"flow debug exit {r.returncode}\n{r.stderr[:500]}")
    data = _parse_json(r.stdout)
    if data is None:
        _fail(f"Could not parse JSON from flow debug\n{r.stdout[:500]}")
    payload = data.get("Data") or {}
    status = payload.get("finalStatus")
    if status != "Completed":
        _fail(f"Flow did not complete (finalStatus={status})\n{r.stdout[:1000]}")
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
    project_dir = _find_project(project_glob)
    types_seen: set[str] = set()
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        for node in flow.get("nodes") or []:
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
    variables = payload.get("variables") or {}
    for val in (variables.get("globals") or {}).values():
        out.extend(_leaves(val))
    for v in variables.get("globalVariables") or []:
        if "value" in v:
            out.extend(_leaves(v.get("value")))
    for e in variables.get("elements") or []:
        out.extend(_leaves(e.get("outputs") or {}))
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
        _fail(
            f"Outputs missing {mode} {list(needles)}; present={present}; "
            f"missing={missing}\nOutputs: {haystack[:1000]}"
        )


def assert_output_int_in_range(payload: dict, lo: int, hi: int) -> int:
    """Assert at least one integer in [lo, hi] appears in the outputs, and
    return the first match. Extracts integers from output values only, not
    from the full debug payload."""
    haystack = _stringify(collect_outputs(payload))
    hits = [int(m) for m in re.findall(r"-?\d+", haystack) if lo <= int(m) <= hi]
    if not hits:
        _fail(
            f"No integer in [{lo}, {hi}] found in outputs\nOutputs: {haystack[:1000]}"
        )
    return hits[0]


def assert_output_value(payload: dict, expected: Any) -> None:
    """Assert that some declared output equals ``expected``. For numerics this
    is equality; for strings it is substring (case-insensitive)."""
    outs = collect_outputs(payload)
    for v in outs:
        if v == expected:
            return
        if isinstance(expected, str) and isinstance(v, str):
            if expected.lower() in v.lower():
                return
        if isinstance(expected, (int, float)) and isinstance(v, str):
            if re.search(rf"(?<!\d){expected}(?!\d)", v):
                return
    _fail(f"No output equals expected {expected!r}\nOutputs: {_stringify(outs)[:1000]}")


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


def _find_project(pattern: str) -> str:
    projects = glob.glob(pattern, recursive=True)
    if not projects:
        _fail(f"No project.uiproj found matching {pattern}")
    return os.path.dirname(projects[0])


def _stringify(values: Iterable[Any]) -> str:
    return json.dumps(list(values), default=str).lower()


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")
