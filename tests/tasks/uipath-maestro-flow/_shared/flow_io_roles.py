"""Feed and read a flow whose variable names the agent chose.

Business-user prompts describe what the automation receives and returns in
plain words and name no variables, so a grader cannot pass `--inputs` by fixed
keys or read outputs by fixed names. This module maps the grader's seeded
values onto the flow's declared inputs by MEANING, and finds results among the
declared outputs by VALUE:

- A *role* is one thing the prompt says the automation receives ("the invoice
  number"), with the seeded value and the name fragments that mean it.
- `map_inputs` scores every declared `in` variable against every role by those
  fragments (in the id and the description), assigns each role to at most one
  input, and coerces the value to the input's declared type.
- An `object` input is filled from the paths the flow itself reads off it
  (`$vars.<trigger>.output.<id>.a.b`): each leaf name is matched to a role the
  same way. A task may add a `fallback` object for paths the flow reads in a
  way a regex cannot see (inside a script loop), which is merged underneath.
- `out_values` returns the declared `out` variables' runtime values, inputs
  excluded, and `texts` flattens strings nested in objects.

Deterministic on purpose: the same flow and payload always map the same way.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

_NORM = re.compile(r"[^a-z0-9]")


def normalize(name: Any) -> str:
    return _NORM.sub("", str(name or "").lower())


def declared(flow: dict, direction: str) -> list[dict]:
    variables = flow.get("variables") or flow.get("workflow", {}).get("variables") or {}
    return [v for v in variables.get("globals") or [] if v.get("direction") == direction and v.get("id")]


def _score(name: str, keywords: list[str]) -> int:
    """How strongly a normalized name means a role: the longest fragment it holds."""
    return max((len(k) for k in keywords if re.search(k, name)), default=0)


def _coerce(value: Any, declared_type: str | None) -> Any:
    t = (declared_type or "").lower()
    if t in ("number", "integer", "int", "float", "double", "decimal"):
        try:
            return float(value) if not float(value).is_integer() else int(float(value))
        except (TypeError, ValueError):
            return value
    if t in ("boolean", "bool"):
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "1")
        return bool(value)
    if t == "string" and not isinstance(value, str):
        return value if isinstance(value, (dict, list)) else str(value)
    return value


def referenced_paths(flow: dict, var_id: str) -> list[list[str]]:
    """Dotted paths the flow reads off an input, e.g. [['customer', 'accountNumber']]."""
    text = json.dumps(flow)
    pattern = re.compile(
        r"\$vars\.(?:[A-Za-z_$][\w$]*\.output\.)?" + re.escape(var_id) + r"((?:\??\.[A-Za-z_$][\w$]*)+)"
    )
    paths = []
    for match in pattern.finditer(text):
        parts = [p for p in re.split(r"\??\.", match.group(1)) if p]
        if parts and parts not in paths:
            paths.append(parts)
    return paths


def _set_path(target: dict, parts: list[str], value: Any) -> None:
    node = target
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            node[part] = nxt
        node = nxt
    node.setdefault(parts[-1], value)


def _merge_under(base: Any, overlay: Any) -> Any:
    """`overlay` wins; `base` fills what overlay lacks."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        out = dict(base)
        for k, v in overlay.items():
            out[k] = _merge_under(base.get(k), v) if k in base else v
        return out
    return overlay


def fill_object(flow: dict, var_id: str, roles: dict[str, dict], fallback: dict | None) -> dict:
    """An object input built from the leaf paths the flow reads, plus `fallback`."""
    built: dict = {}
    for parts in referenced_paths(flow, var_id):
        leaf = normalize(parts[-1])
        best = max(roles.items(), key=lambda kv: _score(leaf, kv[1]["keywords"]), default=None)
        if best and _score(leaf, best[1]["keywords"]) > 0:
            _set_path(built, parts, best[1]["value"])
    return _merge_under(fallback or {}, built)


def map_inputs(
    flow: dict,
    roles: dict[str, dict],
    *,
    object_fallback: dict | None,
    file_path: str | None,
) -> tuple[dict, dict, list[str]]:
    """Return (inputs, attachments, unmapped_roles) for `uip maestro flow debug`.

    `roles` maps a role name to {"value": ..., "keywords": [regex fragments over a
    normalized name]}. Scalar inputs get the best-scoring unassigned role. An
    object input is filled by `fill_object`; a file input gets `file_path`.
    """
    inputs: dict = {}
    attachments: dict = {}
    taken: set[str] = set()
    scalars = []
    for var in declared(flow, "in"):
        var_type = str(var.get("type") or "").lower()
        if var_type == "file":
            if file_path:
                attachments[var["id"]] = file_path
            continue
        if var_type in ("object", "jsonschema", "array"):
            inputs[var["id"]] = fill_object(flow, var["id"], roles, object_fallback)
            taken.update(roles)  # an object input carries the whole submission
            continue
        scalars.append(var)
    pairs = []
    for var in scalars:
        name = normalize(var["id"]) + normalize(var.get("description"))
        for role, spec in roles.items():
            score = _score(name, spec["keywords"])
            if score:
                pairs.append((score, var["id"], role, var.get("type")))
    used_vars: set[str] = set()
    for score, var_id, role, var_type in sorted(pairs, key=lambda p: -p[0]):
        if var_id in used_vars or role in taken:
            continue
        inputs[var_id] = _coerce(roles[role]["value"], var_type)
        used_vars.add(var_id)
        taken.add(role)
    return inputs, attachments, [r for r in roles if r not in taken]


def _named(payload: dict, name: str) -> Any:
    variables = payload.get("variables") or payload.get("Variables") or {}
    globals_ = variables.get("globals") or variables.get("Globals") or {}
    for key, value in globals_.items():
        if str(key).lower() == name.lower():
            return value
    for entry in variables.get("globalVariables") or variables.get("GlobalVariables") or []:
        if str(entry.get("id") or entry.get("Id") or "").lower() == name.lower():
            return entry.get("value", entry.get("Value"))
    return None


def out_values(flow: dict, payload: dict) -> dict[str, tuple[str | None, Any]]:
    """Declared `out` variables -> (declared type, runtime value)."""
    inputs = {normalize(v["id"]) for v in declared(flow, "in")}
    return {
        v["id"]: (v.get("type"), _named(payload, v["id"]))
        for v in declared(flow, "out")
        if normalize(v["id"]) not in inputs
    }


def texts(value: Any) -> list[str]:
    """Every string in a value, including inside objects and lists."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in texts(v)]
    if isinstance(value, (list, tuple)):
        return [t for v in value for t in texts(v)]
    return []


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("USD", "").strip())
    except ValueError:
        return None


def as_bool(value: Any) -> bool | None:
    """A boolean, or the text "true"/"false" or "yes"/"no" (any case)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false", "yes", "no"):
        return value.strip().lower() in ("true", "yes")
    return None


def find_out(outs: dict, predicate) -> list[str]:
    """Ids of declared outputs whose value satisfies `predicate`."""
    return [k for k, (_t, v) in outs.items() if predicate(v)]


def equals_text(expected: str):
    want = expected.strip().lower()
    return lambda v: isinstance(v, str) and v.strip().lower() == want


def equals_number(expected: float, tol: float):
    return lambda v: (n := as_number(v)) is not None and abs(n - expected) <= tol


def equals_bool(expected: bool):
    return lambda v: as_bool(v) is expected


def equals_exact(expected: str):
    """Case-sensitive text match, outer whitespace ignored: "MCS-2026-04872", "Approved"."""
    return lambda v: isinstance(v, str) and v.strip() == expected


GRADER_ERROR_EXIT = 3
"""Exit code a checker uses when the GRADER, not the agent, could not evaluate the run."""


def unmapped_error(flow: dict, unmapped: list[str], inputs: dict | None = None) -> str | None:
    """The failure to report when a role the flow needs found no input, else None.

    When `inputs` (what was mapped) is given and the flow still declares inputs the
    grader could not match, the grader is at fault, not the agent: this prints a
    `GRADER ERROR (not an agent failure)` line and exits with `GRADER_ERROR_EXIT`, so
    reports can count it apart from agent failures. Otherwise the agent never
    declared the input, and the returned message is an ordinary failure."""
    if not unmapped:
        return None
    ids = [v["id"] for v in declared(flow, "in")]
    if inputs is not None:
        spare = [v["id"] for v in declared(flow, "in")
                 if v["id"] not in inputs and str(v.get("type") or "").lower() != "file"]
        if spare:
            sys.stderr.write(
                f"GRADER ERROR (not an agent failure): could not map {', '.join(unmapped)} "
                f"onto the flow's unmatched inputs {spare} (all inputs: {ids})\n"
            )
            sys.exit(GRADER_ERROR_EXIT)
    return f"could not map {', '.join(unmapped)} onto inputs {ids}"
