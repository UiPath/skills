#!/usr/bin/env python3
"""Shared parsing helpers for the same-ground Flow advisory checkers."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
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
REGEX_PRECEDERS = set("(,=:[!&|?{};") | {""}
REGEX_KEYWORDS = {"return", "typeof", "case"}
VAR_PATH = r"\$vars\.[\w$]+(?:\??\.[\w$]+|(?:\?\.)?\[(?:\"[^\"]*\"|'[^']*')\])*"
VAR_PATHS = re.compile(VAR_PATH)
WHOLE_VAR_REF = re.compile(rf"(?:=js:)?{VAR_PATH}")
OUTPUT_REF = re.compile(
    r"\$vars\.([\w$]+)\??\.output(?:\??\.([\w$]+)|(?:\?\.)?\[[\"']([^\"']+)[\"']\])?"
)
JS_DECLARATION = re.compile(r"\b(?:const|let|var)\s+")
JS_DECLARATOR = re.compile(r"\s*(\{[^}]*\}|\[[^\]]*\]|[A-Za-z_$][\w$]*)\s*=(?!=)")
JS_CONTINUES_AFTER = set("+-*/%?:.&|=<>,([")
JS_CONTINUES_BEFORE = set("+-*/%?:.&|=<>,")
JS_UNDEFINED = "undefined"
JS_IDENTIFIER = re.compile(r"(?<![\w$.])[A-Za-z_$][\w$]*")
JS_ASSIGNED = re.compile(
    r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*(?:\*\*|<<|>>>?|&&|\|\||\?\?|[-+*/%&|^])?=(?![=>])"
)
JS_INLINE_LIMIT = 20_000
JS_RETURN_OBJECT = re.compile(r"\breturn\s*\{")
JS_ENTRY_KEY = re.compile(r"\s*(?:([A-Za-z_$][\w$]*)|\"([^\"]*)\"|'([^']*)')\s*(:)?")
FAILED_PORTS = {"error", "failed", "failure", "faulted"}
# Inner target handles on `core.logic.loop` that carry an edge from the last body
# node back into the loop container. Excluding them keeps a loop from turning a
# reachability walk cyclic. `loopBack` is NOT one of them — it never existed, and
# `flow validate` rejects it ("Edge references undeclared target handle") — but it
# is kept here so any legacy fixture still filters.
LOOP_BACK_PORTS = {"continue", "break", "loopBack"}
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


def transitive_refs(value: Any, dependencies: dict[str, set[str]]) -> set[str]:
    """Every node id reachable from a value's `$vars.<node>` references."""
    pending = list(value_refs(value))
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(dependencies.get(current, ()))
    return seen


def source_depends_on(value: Any, producer: str, dependencies: dict[str, set[str]]) -> bool:
    """Follow exact `$vars.<node>` references through any number of reader nodes."""
    return producer in transitive_refs(value, dependencies)


def references_field(value: Any, field: str) -> bool:
    rendered = str(unwrap(value) or "")
    return bool(re.search(rf"(?:^|\.){re.escape(field)}(?:$|[^\w$])", rendered))


def upstream_sources(value: Any, nodes: Iterable[dict[str, Any]]) -> list[str]:
    """Every string in the inputs of the nodes a value reads, directly or transitively."""
    nodes = list(nodes)
    upstream = transitive_refs(value, node_dependencies(nodes))

    def strings(item: Any) -> Iterable[str]:
        if isinstance(item, str):
            yield item
        elif isinstance(item, dict):
            for child in item.values():
                yield from strings(child)
        elif isinstance(item, list):
            for child in item:
                yield from strings(child)

    return [
        text
        for node in nodes
        if str(node.get("id")) in upstream
        for text in strings(node.get("inputs") or {})
    ]


def starts_regex(source: str, index: int, previous: str) -> bool:
    if previous in REGEX_PRECEDERS:
        return True
    word = re.search(r"[\w$]+$", source[:index].rstrip())
    return bool(word) and word.group() in REGEX_KEYWORDS


def interpolation_end(source: str, index: int) -> int:
    """The offset just past the `}` closing the `${` at ``index``."""
    inner = index + 2
    skips = {start: end for start, end, _, _ in js_tokens(source[inner:])}
    depth, offset = 1, 0
    while inner + offset < len(source):
        if offset in skips:
            offset = skips[offset]
            continue
        char = source[inner + offset]
        depth += (char == "{") - (char == "}")
        if not depth:
            return inner + offset + 1
        offset += 1
    return len(source)


def js_tokens(source: str) -> list[tuple[int, int, str, str]]:
    """``(start, end, kind, body)`` of each comment, regex, string and template in JS ``source``.

    ``kind`` is the opening quote for a string or template; ``body`` is its unescaped contents,
    each `${…}` in a template reduced to `${}`.
    """
    tokens: list[tuple[int, int, str, str]] = []
    index, previous = 0, ""
    while index < len(source):
        char, start = source[index], index
        if source.startswith("//", index):
            index = source.find("\n", index)
            index = len(source) if index < 0 else index
            tokens.append((start, index, "comment", ""))
            continue
        if source.startswith("/*", index):
            index = source.find("*/", index + 2)
            index = len(source) if index < 0 else index + 2
            tokens.append((start, index, "comment", ""))
            continue
        if char == "/" and starts_regex(source, index, previous):
            index += 1
            in_class = False
            while index < len(source) and source[index] != "\n":
                current = source[index]
                if current == "\\":
                    index += 2
                    continue
                if current == "/" and not in_class:
                    break
                in_class = (in_class or current == "[") and current != "]"
                index += 1
            index = min(index + 1, len(source))
            tokens.append((start, index, "regex", ""))
            previous = "/"
            continue
        if char in "\"'`":
            body: list[str] = []
            index += 1
            while index < len(source) and source[index] != char:
                if char == "`" and source.startswith("${", index):
                    close = interpolation_end(source, index)
                    body.append("${}")
                    index = close
                    continue
                if source[index] == "\\" and index + 1 < len(source):
                    index += 1
                body.append(source[index])
                index += 1
            index = min(index + 1, len(source))
            tokens.append((start, index, char, "".join(body)))
            previous = char
            continue
        if not char.isspace():
            previous = char
        index += 1
    return tokens


def js_code(source: str) -> str:
    """``source`` with comments blanked and each literal blanked to a trailing `0`, offsets kept; `${…}` stays."""
    chars = list(source)
    for start, end, kind, _ in js_tokens(source):
        chars[start:end] = " " * (end - start)
        if kind != "comment":
            chars[end - 1] = "0"
        if kind != "`":
            continue
        index = start + 1
        while index < end - 1:
            if source[index] == "\\":
                index += 2
                continue
            if not source.startswith("${", index):
                index += 1
                continue
            close = interpolation_end(source, index)
            chars[index:close] = "${" + js_code(source[index + 2:close - 1]) + "}"
            index = close
    return "".join(chars)


def js_depths(code: str) -> list[int]:
    """The bracket depth at each offset of masked JS ``code``."""
    depths, depth = [], 0
    for char in code:
        depth -= char in ")]}"
        depths.append(depth)
        depth += char in "([{"
    return depths


def quotes_column_value(source: str, column: str) -> bool:
    """True when the JS literals in ``source`` build a quoted CEQL value on ``column``.

    `"invoiceNumber = '" + n + "'"` and `` `invoiceNumber = '${n}'` `` pass;
    `'invoiceNumber = ' + n` and `"invoiceNumber = '" + n.replace(/'/g, "''")` do not:
    the closing quote has to sit at the opening literal's own depth.
    """
    pattern = re.compile(rf"\b{re.escape(column)}\s*=\s*'")
    depths = js_depths(js_code(source))
    literals = [token for token in js_tokens(source) if token[2] in "\"'`"]
    for index, (start, end, _, body) in enumerate(literals):
        opened = pattern.search(body)
        if not opened:
            continue
        if "'" in body[opened.end():]:
            return True
        depth = depths[start]
        for later_start, _, _, later_body in literals[index + 1:]:
            if min(depths[end:later_start] or [depth]) < depth:
                break
            if depths[later_start] == depth and later_body.startswith("'"):
                return True
    return False


def object_entries(code: str, open_brace: int) -> list[tuple[int, int]]:
    """``(start, end)`` of each top-level entry of the object literal opening at ``open_brace``."""
    entries: list[tuple[int, int]] = []
    depth, start = 0, open_brace + 1
    for index in range(open_brace + 1, len(code)):
        char = code[index]
        if char in "([{":
            depth += 1
            continue
        if char not in ")]},":
            continue
        if depth:
            depth -= char != ","
            continue
        entries.append((start, index))
        if char != ",":
            break
        start = index + 1
    return entries


def statement_ends(code: str, start: int, newline: int) -> bool:
    """True when a newline at depth 0 ends the statement, as automatic semicolon insertion would."""
    before = code[start:newline].rstrip()
    after = code[newline:].lstrip()
    return bool(before) and before[-1] not in JS_CONTINUES_AFTER and (
        not after or after[0] not in JS_CONTINUES_BEFORE
    )


def initializer_end(code: str, start: int) -> tuple[int, str]:
    """``(offset, delimiter)`` where the initializer starting at ``start`` ends."""
    depth = 0
    for index in range(start, len(code)):
        char = code[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if not depth:
                return index, char
            depth -= 1
        elif not depth and char in ",;":
            return index, char
        elif not depth and char == "\n" and statement_ends(code, start, index):
            return index, char
    return len(code), ""


def js_bindings(script: str, code: str) -> dict[str, str]:
    """Each local name in ``script`` mapped to its initializer; `{ a, b: c }` binds `a` and `c`."""
    bindings: dict[str, str] = {}
    for declaration in JS_DECLARATION.finditer(code):
        index = declaration.end()
        while declarator := JS_DECLARATOR.match(code, index):
            end, delimiter = initializer_end(code, declarator.end())
            initializer = script[declarator.end():end].strip()
            target = declarator.group(1)
            if target.startswith("{"):
                for part in target[1:-1].split(","):
                    key, _, alias = part.split("=")[0].partition(":")
                    if key.strip():
                        bindings[(alias or key).strip()] = f"{initializer}.{key.strip()}"
            else:
                for name in JS_IDENTIFIER.findall(target):
                    bindings[name] = initializer
            if delimiter != ",":
                break
            index = end + 1
    return bindings


def inline_bindings(
    value: str, bindings: dict[str, str], active: frozenset[str] = frozenset()
) -> str | None:
    """``value`` with each local name it reads replaced by that name's initializer, transitively.

    None once the result passes JS_INLINE_LIMIT characters.
    """
    parts, size, last = [], 0, 0
    for name in JS_IDENTIFIER.finditer(js_code(value)):
        if name.group() not in bindings or name.group() in active:
            continue
        inlined = inline_bindings(bindings[name.group()], bindings, active | {name.group()})
        if inlined is None:
            return None
        parts += [value[last:name.start()], inlined]
        size += name.start() - last + len(inlined)
        if size > JS_INLINE_LIMIT:
            return None
        last = name.end()
    parts.append(value[last:])
    return "".join(parts)


def script_output(node: dict[str, Any] | None, key: str | None) -> str | None:
    """The source of ``key`` in a Script's `return { … }`, with local names inlined.

    `undefined` when no returned object names ``key``. None when the node is no
    Script, a returned object spreads, or the trace is ambiguous (two
    returns name ``key``, a name is bound or assigned twice); callers then fall
    back to every string the node reads.
    """
    script = ((node or {}).get("inputs") or {}).get("script")
    if not key or not isinstance(script, str):
        return None
    code = js_code(script)
    returns = list(JS_RETURN_OBJECT.finditer(code))
    if not returns:
        return None

    spreads, values = False, []
    for returned in returns:
        for start, end in object_entries(code, returned.end() - 1):
            start = end - len(code[start:end].lstrip())
            spreads = spreads or code.startswith("...", start)
            entry = JS_ENTRY_KEY.match(script, start, end)
            if entry and key in entry.groups()[:3]:
                values.append(script[entry.end():end] if entry.group(4) else key)
    if spreads:
        return None
    if not values:
        return JS_UNDEFINED

    bindings = js_bindings(script, code)
    assigned = Counter(JS_ASSIGNED.findall(code))
    if len(values) > 1 or any(count > 1 or name not in bindings for name, count in assigned.items()):
        return None
    return inline_bindings(values[0].strip(), bindings)


def reaches_field(value: Any, field: str, nodes: list[dict[str, Any]], seen: set[str] | None = None) -> bool:
    """True when a `$vars` path in ``value`` reads ``field``, directly or through the nodes it reads.

    A Script is followed through the `return` entry the path names, so a Script
    that reads the input but returns something else does not count.
    """
    seen = set() if seen is None else seen
    by_id = {str(node.get("id")): node for node in nodes}
    for path in VAR_PATHS.findall(str(unwrap(value) or "")):
        if path in seen:
            continue
        seen.add(path)
        ref = OUTPUT_REF.match(path)
        entry = script_output(by_id.get(ref.group(1)), ref.group(2) or ref.group(3)) if ref else None
        if entry is not None:
            if reaches_field(entry, field, nodes, seen):
                return True
            continue
        if references_field(path, field):
            return True

        # Node-level fallback passes a dead read, e.g. `const out = {…constant…}; return out;`.
        if any(references_field(source, field) for source in upstream_sources(path, nodes)):
            return True
    return False


def hop_quotes_column(path: str, column: str, nodes: list[dict[str, Any]], seen: set[str] | None = None) -> bool:
    """True when the value a whole `$vars` ``path`` reads builds a quoted CEQL value on ``column``."""
    seen = set() if seen is None else seen
    path = path.strip().removeprefix("=js:")
    if path in seen:
        return False
    seen.add(path)

    ref = OUTPUT_REF.match(path)
    by_id = {str(node.get("id")): node for node in nodes}
    entry = script_output(by_id.get(ref.group(1)), ref.group(2) or ref.group(3)) if ref else None
    if entry is None:
        return any(quotes_column_value(source, column) for source in upstream_sources(path, nodes))
    if quotes_column_value(entry, column):
        return True
    return bool(VAR_PATHS.fullmatch(entry.strip())) and hop_quotes_column(entry, column, nodes, seen)


def query_references_input(detail: dict[str, Any], field: str, nodes: list[dict[str, Any]]) -> bool:
    """Accept direct `$vars` filters and v1's `{var_*}` + filterVariables form."""
    query = unwrap((detail.get("queryParameters") or {}).get("queryExpression"))
    rendered = str(query or "")
    if reaches_field(rendered, field, nodes):
        return True
    filter_variables = detail.get("filterVariables") or {}
    return any(
        placeholder in filter_variables and reaches_field(filter_variables[placeholder], field, nodes)
        for placeholder in FILTER_REF.findall(rendered)
    )


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
# READ alongside a native one is a flow with two sets of the same reads.
CONNECTOR_READ_OPS = (".query-entity-records", ".get-entity-record-by-id")

# Operators the native serializer can emit, spelled as the file spells them
# (data-fabric/impl.md — Filters). There is deliberately no `not in`, `not
# contains`, or null check, and an operator outside this set refuses the WHOLE
# query: the node emits nothing and every downstream `$vars` reference breaks.
NATIVE_FILTER_OPERATORS = {
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
    "starts with",
    "ends with",
    "in",
    # The legacy spelling of `in`. The platform still reads it (impl.md —
    # Filters), so rejecting it fails a filter the serializer accepts.
    "is any of",
}


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
        and str(node.get("type") or "").endswith(CONNECTOR_READ_OPS)
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
    if "entityName" not in path:
        query = {key: unwrap(value) for key, value in (detail.get("queryParameters") or {}).items()}
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


def assert_read_filters_input(
    node: dict[str, Any],
    shape: str,
    field: str,
    label: str,
    nodes: Iterable[dict[str, Any]] = (),
    *,
    column: str,
) -> None:
    """Assert the read filters on ``field``, computed, in a form the server accepts.

    ``field`` is the flow input the value must come from; ``column`` is the
    entity column the filter has to sit on. They coincide in every current
    scenario and are not the same thing, so ``column`` is passed explicitly:
    inferring it from ``field`` would false-fail a scenario whose input and
    column are spelled differently. Without it, a row on the WRONG column
    carrying the right value passes while querying nothing useful.

    The computed half is the anti-hardcode gate: a filter that writes the answer
    in satisfies every behaviour rung while querying nothing. The accepted half
    is a refusal the offline rungs cannot see — CEQL 400s on an unquoted string
    literal, and the native serializer refuses the WHOLE query on a blank
    expression, a `$self` reference, or an operator it cannot emit, which leaves
    the node with no output and breaks every downstream `$vars` reference.
    """
    if shape == NATIVE_READ:
        rows = native_filter_rows(node)
        if not rows:
            mode = str(unwrap(entity_config(node).get("resultMode")) or "").strip()
            consequence = (
                "faults on the over-match as soon as the entity holds more than one row"
                if mode == "single"
                else "returns the first 100 rows in arbitrary order, not the record the flow asked for"
            )
            fail(
                f"the {label} read sets no `entityConfig._filters` rows — an unfiltered "
                f"`resultMode: {mode or 'multiple'!r}` read {consequence}"
            )
        if not read_references_input(node, shape, field, nodes, column=column):
            fail(
                f"no {label} filter row on column {column!r} reaches $vars.…{field}, directly or "
                f"through a node it reads — the rows are "
                f"{[{'field': row.get('field'), 'value': unwrap(row.get('value'))} for row in rows]!r}. "
                f"Each lookup must filter its own column on its own flow input; a literal there is "
                f"the answer written in, and the right value on the wrong column queries nothing"
            )
        for row in rows:
            operator = str(row.get("operator") or "")
            if operator not in NATIVE_FILTER_OPERATORS:
                fail(
                    f"the {label} filter row on {row.get('field')!r} uses operator {operator!r}; the "
                    f"serializer can emit only {sorted(NATIVE_FILTER_OPERATORS)} and refuses the whole "
                    f"query otherwise"
                )
            value = str(unwrap(row.get("value")) or "").strip()
            if not value:
                fail(
                    f"the {label} filter row on {row.get('field')!r} has a blank value — an expression "
                    f"switched on and left blank is refused rather than dropped, so the read emits nothing"
                )
            if "$self" in value:
                fail(
                    f"the {label} filter row on {row.get('field')!r} references `$self` ({value!r}) — a "
                    f"query cannot wait on the record it is being run to fetch, and the serializer "
                    f"refuses the whole query"
                )
        return

    query = {key: unwrap(value) for key, value in (read_detail(node).get("queryParameters") or {}).items()}
    if "queryExpression" not in query:
        fail(f"the {label} query sets no queryExpression; queryParameters: {sorted(query)}")
    expression = str(query["queryExpression"])
    if not read_references_input(node, shape, field, nodes, column=column):
        fail(
            f"the {label} queryExpression is {expression!r} and neither it nor a node it reads "
            f"references {field!r} — each lookup must filter on its own flow input. Build it from "
            f"the input: where: tmpl`{column} = '${{input('{field}')}}'` (connector-params.md). "
            f"This advisory also accepts a Script whose returned CEQL string reads the input"
        )
    if "'" in VAR_PATHS.sub("", expression):
        return
    if not WHOLE_VAR_REF.fullmatch(expression.strip()):
        fail(
            f"the {label} queryExpression is {expression!r} — a CEQL string literal has to be "
            f"single-quoted (an unquoted RHS parses as subtraction server-side and 400s)"
        )
    if not hop_quotes_column(expression, column, nodes):
        fail(
            f"the {label} queryExpression is {expression!r}, and the value it reads does not build "
            f"`{column} = '<value>'` — the filter has to sit on {column!r}, and a CEQL string literal "
            f"has to be single-quoted (an unquoted RHS parses as subtraction server-side and 400s)"
        )


def read_references_input(
    node: dict[str, Any],
    shape: str,
    field: str,
    nodes: Iterable[dict[str, Any]] = (),
    *,
    column: str | None = None,
) -> bool:
    """True when the read's filter reaches the named flow input.

    A filter row may read the input directly, or read a node that does: the
    prompts ask for normalisation before the lookup ("trim, uppercase, prepend
    `MCS-`"), and a native row is a single `value`, so a Script hop is at least
    as natural there as the connector's inline template. The same advisory
    already tolerates the hop for outputs, and for the same reason.
    """
    nodes = list(nodes)
    if shape != NATIVE_READ:
        return query_references_input(read_detail(node), field, nodes)

    wanted = (column or "").strip().lower()
    for row in native_filter_rows(node):
        # Case-insensitive: a column whose CASE is wrong is a different defect,
        # caught live, and failing it here is the over-strictness this file keeps
        # paying for.
        if wanted and str(row.get("field") or "").strip().lower() != wanted:
            continue
        value = row.get("value")
        if "$vars." not in str(unwrap(value) or ""):
            continue
        if reaches_field(value, field, nodes):
            return True
    return False


def assert_read_resolves(node: dict[str, Any], shape: str, label: str, flow: dict[str, Any]) -> str:
    """Assert the read reaches the tenant it is pointed at; describe how.

    Connector: the resolved connection is a connection/folder pair of distinct
    real uuids. Measured while writing these cards — a `bindings.json` whose
    FolderKey entry carried the CONNECTION id collapsed both entries into one at
    FIL emission and the live dispatch sent the folder key as `--connection-id`,
    answering 401.

    Native: nothing to resolve while the entity is tenant-scoped — the node
    needs no Integration Service connection and no `bindings[]` connection row.
    A `_folderKey` switches the emitted target to the folder-qualified form, and
    without `_resourceKey`/`_entityKey` plus both `resource: "Entity"` rows the
    name and folder serialize as source-org literals: it packages and breaks on
    deploy (impl.md — Folder-scoped entities and bindings).
    """
    if shape == NATIVE_READ:
        config = entity_config(node)
        if "_folderKey" not in config:
            return "tenant-scoped entity (no connection, no binding row)"
        folder = str(unwrap(config.get("_folderKey")) or "").strip()
        if not folder:
            fail(
                f"the {label} read declares `_folderKey` but leaves it blank ({config.get('_folderKey')!r}). "
                f"It is the key's PRESENCE that switches the emitted target to the folder-qualified form, "
                f"so a blank one emits that form with no folder. Omit the key to stay tenant-scoped"
            )
        if not is_real_uuid(folder):
            fail(
                f"the {label} read's `_folderKey` is {folder!r}, which is not a folder id. It is the "
                f"entity's `folderId` from `uip df entities list`, so the emitted folder-qualified "
                f"target cannot resolve a value of this shape"
            )

        key = str(unwrap(config.get("_resourceKey")) or unwrap(config.get("_entityKey")) or "").strip()
        if not key:
            fail(
                f"the {label} read carries `_folderKey` {folder!r} but no `_resourceKey`/`_entityKey`, so "
                f"its name and folder serialize as source-org literals. A half-authored folder scope is "
                f"worse than none — it packages and breaks on deploy. Keep the entity tenant-scoped, or "
                f"let the canvas entity picker write all three"
            )
        rows = [
            binding
            for binding in (flow.get("bindings") or [])
            if isinstance(binding, dict)
            and str(binding.get("resource") or "") == "Entity"
            and str(binding.get("resourceKey") or "") == key
        ]
        attributes = {str(binding.get("propertyAttribute") or "") for binding in rows}
        missing = sorted({"name", "folderKey"} - attributes)
        if missing:
            fail(
                f"the {label} read is folder-scoped on `_resourceKey` {key!r} but the flow declares no "
                f"`resource: \"Entity\"` binding row with propertyAttribute {missing} (it declares "
                f"{sorted(attributes) or 'none'}). Both rows are required, `resource` is the capitalized "
                f"\"Entity\" — packaging ignores a lowercase row, so the deploy side gets no override"
            )
        # The row's whole purpose is to carry the value packaging overrides with
        # (impl.md — Folder-scoped entities and bindings). Matching the metadata
        # and skipping `default` reports success on a pair that overrides nothing.
        valueless = sorted(
            str(binding.get("propertyAttribute") or "")
            for binding in rows
            if str(binding.get("propertyAttribute") or "") in {"name", "folderKey"}
            and not str(unwrap(binding.get("default")) or "").strip()
        )
        if valueless:
            fail(
                f"the {label} read's `Entity` binding row(s) for propertyAttribute {valueless} carry no "
                f"`default`. That field is the value packaging substitutes, so a row without one is "
                f"matched and then overrides nothing — the deploy side still gets the source-org literal"
            )
        return f"folder-scoped entity, both Entity binding rows on {key[:8]}…"

    detail = read_detail(node)
    connection = str(unwrap(detail.get("connectionId")) or "")
    folder = str(unwrap(detail.get("connectionFolderKey")) or "")
    for attribute, value in (("connectionId", connection), ("connectionFolderKey", folder)):
        if not is_real_uuid(value):
            fail(
                f"the {label} query's detail.{attribute} is {value!r}, not a real uuid — `bindings.json` "
                f"has to name the real Data Fabric connection and its folder "
                f"(uip is connections list --all-folders)"
            )
    if connection == folder:
        fail(
            f"the {label} query's detail.connectionId and detail.connectionFolderKey are the SAME uuid "
            f"({connection}) — the folder binding needs the connection's FOLDER key, not its id "
            f"(measured: the two collapse into one binding at FIL emission and the live dispatch sends "
            f"the folder key as --connection-id, answering 401 Unauthorized)"
        )
    return f"connection={connection[:8]}… folder={folder[:8]}…"


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
        if not source or not target or edge.get("targetPort") in LOOP_BACK_PORTS:
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
