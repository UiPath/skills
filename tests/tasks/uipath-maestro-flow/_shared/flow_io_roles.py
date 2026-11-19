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
  input, and coerces the value to the input's declared type. A fragment
  that matches whole words of the name (`disputedLineNo` holds `line` and
  `lineno`) outranks one found only inside a word (`deadline` holds `line`,
  `invoicenumber` holds `invoice`); ties go to the name the fragment covers
  most, then by name, never by declaration order.
- An `object` input is filled from the paths the flow itself reads off it
  (`$vars.<trigger>.output.<id>.a.b`): each leaf name is matched to a role the
  same way. A task may add a `fallback` object for paths the flow reads in a
  way a regex cannot see (inside a script loop), which is merged underneath.
- An `array` input only takes a role whose value is a list.
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


_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
_PLAIN = re.compile(r"^[a-z0-9]+$")


def _words(text: Any) -> list[str]:
    """`disputed_lineNo` -> ['disputed', 'line', 'no']."""
    return [w.lower() for w in _WORD.findall(str(text or ""))]


def _runs(words: list[str]) -> list[str]:
    return ["".join(words[i:j]) for i in range(len(words)) for j in range(i + 1, len(words) + 1)]


WHOLE_WORD_BONUS = 1000


def _match(texts: list[Any], keywords: list[str], *, substring: bool = True) -> tuple[int, int]:
    """(score, leftover) of the best fragment found in any of `texts`.

    A plain fragment that equals a run of whole words, a plural `s`/`es`
    allowed, scores WHOLE_WORD_BONUS plus its length; a fragment with regex
    syntax (`^from$`) searched in the whole normalized text scores the same.
    Only when nothing matches that way, and `substring` is on, does a plain
    fragment found inside the normalized text count, at its bare length: so
    `invoicenumber` still means the invoice, while a real `lineNumber` beats
    `deadline` for the line. Leftover is what of that text the fragment does
    not cover, so the closer name wins a tie."""
    best = (0, 0)
    for allow_inside in ((False, True) if substring else (False,)):
        for text in texts:
            whole = normalize(text)
            runs = set(_runs(_words(text)))
            for k in keywords:
                if not _PLAIN.match(k):
                    hit, bonus = not allow_inside and bool(re.search(k, whole)), WHOLE_WORD_BONUS
                elif allow_inside:
                    hit, bonus = k in whole, 0
                else:
                    hit, bonus = k in runs or f"{k}s" in runs or f"{k}es" in runs, WHOLE_WORD_BONUS
                score = bonus + len(k)
                if hit and (score, -(len(whole) - len(k))) > (best[0], -best[1]):
                    best = (score, len(whole) - len(k))
        if best[0]:
            return best
    return best


SCALAR_TYPES = ("number", "integer", "int", "float", "double", "decimal", "boolean", "bool")


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


def fill_object(
    flow: dict, var_id: str, roles: dict[str, dict], fallback: dict | None
) -> tuple[dict, set[str]]:
    """An object input built from the leaf paths the flow reads, plus `fallback`,
    and the roles those paths placed."""
    built: dict = {}
    placed: set[str] = set()
    for parts in referenced_paths(flow, var_id):
        scored = [(_match([parts[-1]], spec["keywords"]), role) for role, spec in roles.items()]
        scored = [(score, leftover, role) for (score, leftover), role in scored if score]
        if scored:
            _score_, _left, role = min(scored, key=lambda t: (-t[0], t[1], t[2]))
            _set_path(built, parts, roles[role]["value"])
            placed.add(role)
    return _merge_under(fallback or {}, built), placed


TEXT_TYPE = "string"


SUBMISSION_WORDS = ("submission", "request", "payload", "message", "claim", "dispute")


def _camel(name: str) -> str:
    words = _words(name)
    return words[0] + "".join(w.capitalize() for w in words[1:]) if words else ""


def spelled_object(roles: dict[str, dict]) -> dict:
    """Every role under each plain name fragment, plus its camelCase spellings, for a flow whose reads of an object input a regex cannot see.

    JS keys are case-sensitive: a role's camelCase names are its own name
    (`invoice number` -> `invoiceNumber`)."""
    spelled: dict = {}
    for role, spec in roles.items():
        names = [k for k in spec["keywords"] if _PLAIN.match(k)]
        names.append(_camel(role))
        spelled.update({k: spec["value"] for k in names if k})
    return spelled


def _reads_as_submission(var: dict) -> bool:
    text = f"{var.get('id')} {var.get('description') or ''}".lower()
    return any(w in text for w in SUBMISSION_WORDS)


def map_inputs(
    flow: dict,
    roles: dict[str, dict],
    *,
    object_fallback: dict | None,
    file_path: str | None,
) -> tuple[dict, dict, list[str]]:
    """Return (inputs, attachments, unmapped_roles) for `uip maestro flow debug`.

    `roles` maps a role name to {"value": ..., "keywords": [name fragments, see
    `_match`]}. An object input is filled by `fill_object`; the roles its paths
    placed are not given to another input. Each other input gets the
    best-scoring unassigned role: an array input only a list, any other input
    only a non-list. A file input gets `file_path`. A role counts as mapped
    when an input took it, or when an object input was filled with a non-empty
    `object_fallback` (which carries every role under its common spellings).
    An object input whose read paths are not found, and no `object_fallback`,
    gets `spelled_object` in its place. A lone free-text submission gets
    `spelled_object` as JSON, with `object_fallback` laid over it.
    """
    inputs: dict = {}
    attachments: dict = {}
    taken: set[str] = set()
    carried = False
    others = []
    for var in declared(flow, "in"):
        var_type = str(var.get("type") or "").lower()
        if var_type == "file":
            if file_path:
                attachments[var["id"]] = file_path
            continue
        if var_type in ("object", "jsonschema"):
            fallback = object_fallback
            if fallback is None and not referenced_paths(flow, var["id"]):
                fallback = spelled_object(roles)
            inputs[var["id"]], placed = fill_object(flow, var["id"], roles, fallback)
            taken |= placed
            carried = carried or bool(fallback)
            continue
        others.append(var)
    pairs = []
    for var in others:
        var_type = str(var.get("type") or "").lower()
        is_array = var_type == "array"
        for role, spec in roles.items():
            if isinstance(spec["value"], list) != is_array:
                continue
            if isinstance(spec["value"], dict) and var_type in SCALAR_TYPES:
                continue
            score, leftover = _match([var["id"], var.get("description")], spec["keywords"])
            if score:
                pairs.append((score, leftover, var["id"], role, var.get("type")))
    used_vars: set[str] = set()
    for _score_, _left, var_id, role, var_type in sorted(pairs, key=lambda p: (-p[0], p[1], p[2], p[3])):
        if var_id in used_vars or role in taken:
            continue
        inputs[var_id] = _coerce(roles[role]["value"], var_type)
        used_vars.add(var_id)
        taken.add(role)
    missing = [r for r in roles if r not in taken]
    free_text = [v for v in others if v["id"] not in used_vars and str(v.get("type") or "").lower() == TEXT_TYPE
                 and _reads_as_submission(v)]
    if missing and not carried and len(free_text) == 1:
        inputs[free_text[0]["id"]] = json.dumps({**spelled_object(roles), **(object_fallback or {})})
        return inputs, attachments, []
    return inputs, attachments, [] if carried else missing


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


def means(names: list[Any], keywords: list[str], *, substring: bool = True) -> int:
    """How strongly any of `names` (an id, a description, a key) means a role; 0 for not at all.
    `substring=False` takes whole-word matches only (see `_match`)."""
    return _match(names, keywords, substring=substring)[0]


def outs_meaning(flow: dict, keywords: list[str]) -> list[str]:
    """Ids of declared `out` variables whose id or description means a role, best match first."""
    inputs = {normalize(v["id"]) for v in declared(flow, "in")}
    scored = [(_match([v["id"], v.get("description")], keywords), v["id"]) for v in declared(flow, "out")
              if normalize(v["id"]) not in inputs]
    return [i for (score, left), i in sorted(scored, key=lambda t: (-t[0][0], t[0][1], t[1])) if score]


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


def is_empty_text(value: Any) -> bool:
    """Text set to "" or whitespace. An output never set (None) is not empty text."""
    return isinstance(value, str) and not value.strip()


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
"""Exit code a checker uses when the grader, not the agent, may be at fault.

Nothing reads it: every criterion expects exit 0, so it scores as a failure
like any other non-zero exit. It and the stderr label only tell whoever
triages the run to look at the grader's mapping first."""


def unmapped_error(flow: dict, unmapped: list[str], inputs: dict | None = None) -> str | None:
    """The failure to report when a role the flow needs found no input, else None.

    When `inputs` (what was mapped) is given and the flow still declares inputs the
    grader could not match, this prints a `possible grader mapping miss, or an unrelated input`
    line and exits with `GRADER_ERROR_EXIT`: the grader's fragments may have
    missed the agent's name, though an unrelated extra input the agent added
    lands here too. Otherwise the agent never declared the input, and the
    returned message is an ordinary failure."""
    if not unmapped:
        return None
    ids = [v["id"] for v in declared(flow, "in")]
    if inputs is not None:
        spare = [v["id"] for v in declared(flow, "in")
                 if v["id"] not in inputs and str(v.get("type") or "").lower() != "file"]
        if spare:
            sys.stderr.write(
                f"possible grader mapping miss, or an unrelated input: could not map {', '.join(unmapped)} "
                f"onto the flow's unmatched inputs {spare} (all inputs: {ids})\n"
            )
            sys.exit(GRADER_ERROR_EXIT)
    return f"could not map {', '.join(unmapped)} onto inputs {ids}"
