#!/usr/bin/env python3
"""DF smoke_query (BPMN): verify the complete filter and pagination matrix.

Ported from Flow
`connector_features/datafabric_connector/check_smoke_query_filter.py`. Same
scenario (three Query Entity Records activities against FlowCodeEvalEntity: a
nine-condition FilterBuilder tree paged twice, plus a third active-only
descending query) and the same assertions, re-homed from a Flow node's
`inputs.detail` JSON dict to a BPMN `bpmn:sendTask` carrying the registry
`Intsvc.ActivityExecution` wrapper (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4).

Re-homing notes (every Flow JSON key this grader used to read, and where its
BPMN equivalent lives):

  Flow `inputs.detail.filter` (design-time FilterBuilder tree) /
  `savedFilterTrees.queryExpression` / `configuration` (a `=jsonString:`
  -encoded blob holding the same tree)
      -> BPMN: the single `target="body"` `<uipath:input>` JSON payload
         (registry-workflow.md's "exactly ONE target=body input holding the
         whole request JSON" contract -- Flow's three possible filter
         locations collapse to this one slot). A structured filter tree
         round-trips as nested JSON inside that CDATA; a runtime expression
         lands as plain text (`=js:...`) in the same slot. Both are covered
         the same way Flow covers its own two representations: dump the
         parsed body back to text and search it for field+value+operator
         tokens, never assert *where* in the tree a condition sits.

  Flow `inputs.detail.queryParameters._sortFieldName` / `isAscending` /
  `limit` / `start`
      -> BPMN: no fixed field-name vocabulary is available for this
         operation -- no live Data Service connection exists on this box to
         `uip is resources describe` it (BATCH1-ADDENDUM.md). Rather than
         pin a guessed key spelling, the body is parsed as JSON and walked
         structurally: a "sort spec" is any dict carrying both a
         field-name-ish key (`fieldName`, `field`, `sortField`,
         `sortFieldName`, `orderBy`) and a direction-ish sibling key
         (`isDescending`, `isAscending`, `direction`, `sortDirection`,
         `ascending`) -- a filter *condition* dict (field + operator + value
         siblings) never has a direction-ish sibling, so a query that both
         filters AND sorts on the same field (`score`, in queries 1 and 2)
         is not confused between the two roles. `limit`/`start` are found
         the same tolerant way: by key-name family, at any nesting depth.
         GUESS: this key-name family is modeled on the public Data Service
         entities-query REST shape (`filterGroup.conditions[]`,
         `sortOptions[].{fieldName,isDescending}`, `start`, `limit`); it is
         unverified against a live `describe` output, so the walk is
         deliberately tolerant of alternate spellings (including Flow's own
         flat `_sortFieldName`/`isAscending`/`limit`/`start`, which also
         satisfies the same field+direction sibling test at the body's own
         top level).

This also asserts the registry contract a read-only smoke doesn't get to
skip: exactly one `target="body"` JSON input per query node
(registry-workflow.md's single-body-input rule -- several such inputs on one
node do not merge at runtime) and a `=bindings.<id>` connection reference
backed by a declared process-level `<uipath:binding resource="Connection">`
(mirrors check_drive_to_slack.py's `require_connection_binding`).

Checks performed:
  1. BPMN file exists, is well-formed XML, DI and sequence-flow integrity hold.
  2. Exactly 3 bpmn:sendTask nodes carry Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and objectName matching Query
     Entity Records (QueryEntityRecordsCurated|QueryEntityRecords_V3).
  3. Each such node has exactly one target="body" input, and it is valid JSON.
  4. Every one of the nine filter conditions appears somewhere across the
     three nodes, and at least one single node's body contains all nine
     together (the FilterBuilder tree is not split across query activities).
  5. At least 2 nodes are sorted by `score` (any direction).
  6. At least 2 of those score-sorted nodes carry both a limit and a
     start/offset value.
  7. At least 1 node has a descending sort.
  8. Every query node references a declared connection binding.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
OBJECT_NAMES = {"queryentityrecordscurated", "queryentityrecords_v3"}

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
EXPECTED = {
    "boolean": ("active", ("true",), ()),
    "decimal": ("score", ("8.5",), ("greaterthanorequal", ">=")),
    "integer": ("viewcount", ("1000",), ("greaterthanorequal", ">=")),
    "string": ("title", ("filterfixture-matrix",), ("equals", "=")),
    "multiline": ("description", ("sci-fi",), ("contains",)),
    "date": ("releasedate", ("2025-01-01",), ("lessthan", "<")),
    "datetime": ("lastupdated", ("2024-01-01",), ("greaterthanorequal", ">=")),
    "uuid": ("externalid", (), ()),
    "null": ("description", (), ("isnull", "is null")),
}

FIELD_KEYS = {"fieldname", "field", "sortfield", "sortfieldname", "orderby"}
DIRECTION_KEYS = {"isdescending", "isascending", "direction", "sortdirection", "ascending"}
LIMIT_KEYS = {"limit", "pagesize", "top"}
OFFSET_KEYS = {"start", "offset", "skip"}


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def context_value(task: ET.Element, name: str) -> str:
    for inp in task.findall(".//uipath:input", NS):
        if inp.attrib.get("name") == name:
            return inp.attrib.get("value") or (inp.text or "")
    return ""


def body_inputs(task: ET.Element) -> list[ET.Element]:
    return [
        inp
        for inp in task.findall(".//uipath:input", NS)
        if inp.attrib.get("target") == "body"
    ]


def query_entity_nodes(root: ET.Element) -> list[ET.Element]:
    nodes = []
    for task in elements(root, "sendTask"):
        if not has_type(task, ACTIVITY_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        if context_value(task, "objectName").lower() not in OBJECT_NAMES:
            continue
        nodes.append(task)
    return nodes


def node_body(task: ET.Element) -> dict:
    label = task.attrib.get("id", "<unnamed>")
    bodies = body_inputs(task)
    if len(bodies) != 1:
        fail(
            f'Query node {label!r} must carry exactly ONE target="body" '
            f"<uipath:input> holding the request JSON "
            f"(registry-workflow.md single-body-input rule); found {len(bodies)}"
        )
    raw = bodies[0].text or bodies[0].attrib.get("value") or ""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        fail(f'Query node {label!r} target="body" is not valid JSON: {exc}')
    if not isinstance(parsed, dict):
        fail(
            f'Query node {label!r} target="body" JSON must be an object, '
            f"found {type(parsed).__name__}"
        )
    return parsed


def node_text(task: ET.Element, body: dict) -> str:
    """One lowercase search blob per node: the parsed body dumped back to
    text (covers a structured filter/sort tree) plus every input's raw
    name+value (covers a value sent as a separate query/path-targeted input
    instead of folded into the body). Mirrors Flow's
    `node_filter_text`, which combines `queryParameters.queryExpression`
    text with `json.dumps(leaves)` of the structured tree."""
    parts = [json.dumps(body).lower()]
    for inp in task.findall(".//uipath:input", NS):
        name = inp.attrib.get("name") or ""
        value = inp.attrib.get("value") or (inp.text or "")
        parts.append(f"{name} {value}".lower())
    return " ".join(parts)


def has_expected_filter(text: str, field: str, tokens: tuple, operators: tuple) -> bool:
    return (
        field in text
        and all(token.lower() in text for token in tokens)
        and (field != "externalid" or UUID_RE.search(text))
        and (not operators or any(op.lower() in text for op in operators))
    )


def _walk(node, visit) -> None:
    if isinstance(node, dict):
        visit(node)
        for value in node.values():
            _walk(value, visit)
    elif isinstance(node, list):
        for item in node:
            _walk(item, visit)


def sort_specs(body: dict) -> list[dict]:
    """Every dict in `body` shaped like a sort spec: a field-name-ish key
    paired with a direction-ish sibling. A filter condition dict (field +
    operator + value) never has a direction-ish sibling, so the two are not
    confused even when both name the same field."""
    found: list[dict] = []

    def visit(d: dict) -> None:
        keys = {k.lower() for k in d}
        if (keys & FIELD_KEYS) and (keys & DIRECTION_KEYS):
            found.append(d)

    _walk(body, visit)
    return found


def sort_field_name(spec: dict) -> str:
    keys = {k.lower(): k for k in spec}
    for candidate in FIELD_KEYS:
        if candidate in keys:
            return str(spec[keys[candidate]]).lower()
    return ""


def is_descending(spec: dict) -> bool:
    keys = {k.lower(): k for k in spec}
    if "isdescending" in keys:
        return bool(spec[keys["isdescending"]])
    if "isascending" in keys:
        return spec[keys["isascending"]] is False
    if "ascending" in keys:
        return spec[keys["ascending"]] is False
    for name in ("direction", "sortdirection"):
        if name in keys:
            return str(spec[keys[name]]).strip().lower().startswith("desc")
    return False


def numeric_values(body: dict, key_names: set) -> list:
    found = []

    def visit(d: dict) -> None:
        for k, v in d.items():
            if k.lower() in key_names:
                try:
                    found.append(int(v))
                except (TypeError, ValueError):
                    pass

    _walk(body, visit)
    return found


def binding_ids(root: ET.Element) -> set:
    return {
        b.attrib.get("id", "")
        for b in root.findall(".//uipath:bindings/uipath:binding", NS)
        if b.attrib.get("resource") == "Connection"
    }


def require_connection_binding(task: ET.Element, bindings: set) -> None:
    label = task.attrib.get("id", "<unnamed>")
    connection = context_value(task, "connection")
    match = re.match(r"^=bindings\.(\S+)$", connection)
    if not match:
        fail(
            f"Query node {label!r} has no `=bindings.<id>` connection reference "
            f"(found connection={connection!r})"
        )
    binding_id = match.group(1)
    if binding_id not in bindings:
        fail(
            f"Query node {label!r} references binding {binding_id!r} with no "
            f'matching <uipath:binding resource="Connection"> in the '
            f"process-level <uipath:bindings> block (declared: {sorted(bindings)})"
        )


def main() -> None:
    path, root = parse_bpmn()

    nodes = query_entity_nodes(root)
    bodies = [node_body(task) for task in nodes]
    texts = [node_text(task, body) for task, body in zip(nodes, bodies)]

    missing = [
        name
        for name, (field, tokens, operators) in EXPECTED.items()
        if not any(has_expected_filter(text, field, tokens, operators) for text in texts)
    ]
    if missing:
        fail(f"missing filter coverage: {', '.join(missing)}")

    matrix_nodes = [
        text
        for text in texts
        if all(
            has_expected_filter(text, field, tokens, operators)
            for field, tokens, operators in EXPECTED.values()
        )
    ]
    if not matrix_nodes:
        fail(
            "the nine filter conditions are split across query nodes; one "
            "Query Entity Records node must contain the complete FilterBuilder tree"
        )

    if len(nodes) != 3:
        fail(
            f"expected exactly 3 Query Entity Records connector nodes "
            f"(connectorKey={CONNECTOR_KEY!r}, objectName in {sorted(OBJECT_NAMES)}), "
            f"found {len(nodes)}"
        )

    all_specs = [sort_specs(body) for body in bodies]
    sorted_by_score = [
        (task, body)
        for task, body, specs in zip(nodes, bodies, all_specs)
        if any(sort_field_name(s) == "score" for s in specs)
    ]
    if len(sorted_by_score) < 2:
        fail(f"expected >=2 query nodes sorted by score, found {len(sorted_by_score)}")

    paginated = [
        (task, body)
        for task, body in sorted_by_score
        if numeric_values(body, LIMIT_KEYS) and numeric_values(body, OFFSET_KEYS)
    ]
    if len(paginated) < 2:
        fail(
            f"expected >=2 score-sorted queries with limit + start/offset set, "
            f"found {len(paginated)}"
        )

    descending = [
        task for task, specs in zip(nodes, all_specs) if any(is_descending(s) for s in specs)
    ]
    if not descending:
        fail("expected at least one query with a descending sort")

    bindings = binding_ids(root)
    if not bindings:
        fail('no process-level <uipath:binding resource="Connection"> declared')
    for task in nodes:
        require_connection_binding(task, bindings)

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)

    print(
        f"OK: {path} -- 3 Query Entity Records nodes; one contains all 9 filter "
        f"cases; {len(paginated)} paginated + {len(descending)} descending query "
        f"nodes present"
    )


if __name__ == "__main__":
    main()
