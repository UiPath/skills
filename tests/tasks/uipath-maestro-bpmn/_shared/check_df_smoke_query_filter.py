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

CI caught a real gap in the first version of this grader: a legitimate agent
solution encoded the curated `QueryEntityRecordsCurated` activity as
SEPARATE inputs, not a single body -- `entityName` as a `target="path"`
input, the filter as a `target="query"` input named `queryExpression`
holding a CEQL-like string (`(active = true)`), `start`/`limit`/`sortBy`/
`isAscending` as flat `target="query"` inputs, AND the structured
FilterBuilder tree duplicated in the context `metadata` JSON input under
`essentialConfiguration.savedFilterTrees.queryExpression` (`filters[]` of
`{id, operator, value: {value, rawString}}`, recursing into `groups[]`).
This is exactly the dual structured-tree-or-runtime-text representation
Flow's grader tolerated -- a single mandatory `target="body"` input was a
BPMN-only requirement the Flow prompt never had and the registry does not
actually mandate for this operation. Fixed below: a body input is now
optional, and the searchable representation is built from every input at
any depth plus the parsed `metadata` tree, not from one required body blob.

Re-homing notes (every Flow JSON key this grader used to read, and where its
BPMN equivalent lives):

  Flow `inputs.detail.filter` (design-time FilterBuilder tree) /
  `savedFilterTrees.queryExpression` / `configuration` (a `=jsonString:`
  -encoded blob holding the same tree)
      -> BPMN: a `savedFilterTrees.queryExpression` tree nested anywhere
         inside ANY JSON-shaped `uipath:input` on the node -- most often the
         context `metadata` input, but a `target="body"` input if the skill
         chooses to emit one is walked the same way. `filters[]` leaves
         (`{id, operator, value: {value, rawString}}`) are extracted the way
         Flow's `structured_filter_leaves` walked `filters`/`groups`, and
         dumped back to text. A runtime CEQL-like expression string
         (`target="query"` input named `queryExpression`) is covered too,
         since every input's raw name+value+text is part of the same search
         blob -- both representations are searched together, the same
         non-exclusive combination Flow's own `node_filter_text` uses.

  Flow `inputs.detail.queryParameters._sortFieldName` / `isAscending` /
  `limit` / `start`
      -> BPMN: read from a `uipath:input` whose `name` (case-insensitive)
         is one of `sortBy|sortField|orderBy|_sortFieldName|sort` (sort
         field), `isAscending|isDescending|direction|sortDirection`
         (direction), `limit|top|pageSize` (page size), or
         `start|offset|skip` (page offset) -- at ANY depth, meaning both a
         flat `target="query"` input (the real shape CI caught) and a
         same-named key nested inside a JSON-shaped input (a body-JSON
         alternate shape) are found by the same lookup, since both flat
         XML attributes and flattened JSON leaves land in one `(name,
         value)` pair list.

Also asserts a `=bindings.<id>` connection reference backed by a declared
process-level `<uipath:binding resource="Connection">` (mirrors
check_drive_to_slack.py's `require_connection_binding`) -- the one
registry-contract assertion from the first version that CI did not flag,
kept as-is.

Checks performed:
  1. BPMN file exists, is well-formed XML, DI and sequence-flow integrity hold.
  2. Exactly 3 bpmn:sendTask nodes carry Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and either objectName matching
     Query Entity Records (QueryEntityRecordsCurated|QueryEntityRecords_V3)
     or objectName == FlowCodeEvalEntity with operation List / method GET
     (a dynamic per-entity query shape) -- and each references
     FlowCodeEvalEntity somewhere (input value/text at any depth, or
     objectName).
  3. Any `target="body"` input present is valid JSON (optional -- absence
     is not an error).
  4. Every one of the nine filter conditions appears somewhere across the
     three nodes, and the complete nine-condition set appears together in
     at least TWO nodes (queries 1 and 2 both reuse the full tree, per the
     prompt).
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
ENTITY = "flowcodeevalentity"

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

SORT_FIELD_NAMES = {"sortby", "sortfield", "orderby", "_sortfieldname", "sort"}
DIRECTION_NAMES = {"isascending", "isdescending", "direction", "sortdirection"}
LIMIT_NAMES = {"limit", "top", "pagesize"}
OFFSET_NAMES = {"start", "offset", "skip"}


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def activity_root(task: ET.Element) -> ET.Element | None:
    return task.find(".//uipath:activity", NS)


def all_inputs(task: ET.Element) -> list[ET.Element]:
    """Every uipath:input at any depth under this node's uipath:activity --
    context inputs, top-level path/query/body inputs, all of it."""
    root = activity_root(task)
    if root is None:
        return []
    return root.findall(".//uipath:input", NS)


def input_val(inp: ET.Element) -> str:
    return inp.attrib.get("value") or (inp.text or "")


def context_value(task: ET.Element, name: str) -> str:
    for inp in all_inputs(task):
        if inp.attrib.get("name") == name:
            return input_val(inp)
    return ""


def entity_referenced(task: ET.Element, object_name: str) -> bool:
    if ENTITY in (object_name or "").lower():
        return True
    for inp in all_inputs(task):
        name = (inp.attrib.get("name") or "").lower()
        value = str(input_val(inp)).lower()
        if ENTITY in name or ENTITY in value:
            return True
    return False


def query_entity_nodes(root: ET.Element) -> list[ET.Element]:
    nodes = []
    for task in elements(root, "sendTask"):
        if not has_type(task, ACTIVITY_TYPE):
            continue
        if context_value(task, "connectorKey") != CONNECTOR_KEY:
            continue
        object_name = context_value(task, "objectName")
        object_name_l = object_name.lower()
        operation = context_value(task, "operation").lower()
        method = context_value(task, "method").upper()
        is_curated = object_name_l in OBJECT_NAMES
        is_dynamic_list = object_name_l == ENTITY and (operation == "list" or method == "GET")
        if not (is_curated or is_dynamic_list):
            continue
        if not entity_referenced(task, object_name):
            continue
        nodes.append(task)
    return nodes


def validate_body_inputs(task: ET.Element) -> None:
    """A target="body" input is optional; if present it must be valid JSON."""
    label = task.attrib.get("id", "<unnamed>")
    for inp in all_inputs(task):
        if inp.attrib.get("target") != "body":
            continue
        raw = input_val(inp)
        if not raw.strip():
            continue
        try:
            json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            fail(f'Query node {label!r} target="body" input is not valid JSON: {exc}')


def parse_json_maybe(value: str):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def flatten_json_pairs(node, pairs: list) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                pairs.append((k, ""))
                flatten_json_pairs(v, pairs)
            else:
                pairs.append((k, "" if v is None else str(v)))
    elif isinstance(node, list):
        for item in node:
            flatten_json_pairs(item, pairs)


def find_saved_filter_trees(node, out: list) -> None:
    """Recursively find every `savedFilterTrees.queryExpression` tree,
    wherever it is nested -- Flow's own grader tolerated several possible
    nesting depths for the equivalent `configuration`/`savedFilterTrees`
    blob, so this does not pin one exact path
    (`essentialConfiguration.savedFilterTrees...` in the observed artifact,
    but not asserted as the only valid one)."""
    if isinstance(node, dict):
        sft = node.get("savedFilterTrees")
        if isinstance(sft, dict) and "queryExpression" in sft:
            out.append(sft["queryExpression"])
        for value in node.values():
            find_saved_filter_trees(value, out)
    elif isinstance(node, list):
        for item in node:
            find_saved_filter_trees(item, out)


def filter_leaves_from_tree(tree, leaves: list) -> None:
    if not isinstance(tree, dict):
        return
    leaves.extend(tree.get("filters") or [])
    for child in tree.get("groups") or []:
        filter_leaves_from_tree(child, leaves)


def structured_filter_leaves(parsed_json) -> list:
    trees: list = []
    find_saved_filter_trees(parsed_json, trees)
    leaves: list = []
    for tree in trees:
        filter_leaves_from_tree(tree, leaves)
    return leaves


def node_representation(task: ET.Element) -> tuple[list, str]:
    """(pairs, text) for one query node.

    `pairs` is every (name, value) from a flat uipath:input attribute AND
    every leaf of any JSON-shaped input's parsed value (context `metadata`,
    a target="body" input if present, or any other JSON input) -- used for
    the sort/limit/offset keyword lookups, which need a name paired with its
    value regardless of whether the skill put it in a flat query-string
    input or nested inside a JSON blob.

    `text` is the Flow-style flattened lowercase search blob for the
    nine-condition filter check: every input's raw name+value+text (this
    alone already contains a CEQL queryExpression string's tokens, and a
    JSON input's raw CDATA text verbatim), plus the structured FilterBuilder
    leaves -- if a savedFilterTrees.queryExpression tree is found in any
    JSON-shaped input -- dumped back to text. Mirrors Flow's
    structured_filter_leaves/node_filter_text, which combines a structured
    tree and a runtime expression string the same non-exclusive way.
    """
    inputs = all_inputs(task)
    pairs: list = [(inp.attrib.get("name") or "", input_val(inp)) for inp in inputs]
    text_parts = [f"{k} {v}".lower() for k, v in pairs]
    for inp in inputs:
        parsed = parse_json_maybe(input_val(inp))
        if parsed is None:
            continue
        flatten_json_pairs(parsed, pairs)
        leaves = structured_filter_leaves(parsed)
        if leaves:
            text_parts.append(json.dumps(leaves).lower())
    return pairs, " ".join(text_parts)


def has_expected_filter(text: str, field: str, tokens: tuple, operators: tuple) -> bool:
    return (
        field in text
        and all(token.lower() in text for token in tokens)
        and (field != "externalid" or UUID_RE.search(text))
        and (not operators or any(op.lower() in text for op in operators))
    )


def values_by_name(pairs: list, names: set) -> list:
    return [v for k, v in pairs if k.lower() in names and v not in (None, "")]


# A sort may also ride inside the CEQL-like query string itself
# ("... ORDER BY score DESC"), as the eval agent emitted on CI run 35489744689.
ORDER_BY_RE = re.compile(r"\border\s+by\s+([a-z0-9_]+)(?:\s+(asc|desc))?", re.IGNORECASE)


def sorted_field(pairs: list, text: str = "") -> str:
    values = values_by_name(pairs, SORT_FIELD_NAMES)
    if values:
        return values[0].lower()
    match = ORDER_BY_RE.search(text)
    return match.group(1).lower() if match else ""


def is_descending(pairs: list, text: str = "") -> bool:
    match = ORDER_BY_RE.search(text)
    if match and (match.group(2) or "").lower() == "desc":
        return True
    for k, v in pairs:
        key = k.lower()
        val = str(v).strip().lower()
        if key == "isdescending" and val in ("true", "1"):
            return True
        if key == "isascending" and val in ("false", "0"):
            return True
        if key in ("direction", "sortdirection") and val.startswith("desc"):
            return True
    return False


def has_numeric(pairs: list, names: set) -> bool:
    for k, v in pairs:
        if k.lower() in names:
            try:
                int(v)
                return True
            except (TypeError, ValueError):
                continue
    return False


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
    for task in nodes:
        validate_body_inputs(task)

    reps = [node_representation(task) for task in nodes]
    pairs_list = [pairs for pairs, _ in reps]
    texts = [text for _, text in reps]

    missing = [
        name
        for name, (field, tokens, operators) in EXPECTED.items()
        if not any(has_expected_filter(text, field, tokens, operators) for text in texts)
    ]
    if missing:
        fail(f"missing filter coverage: {', '.join(missing)}")

    matrix_texts = [
        text
        for text in texts
        if all(
            has_expected_filter(text, field, tokens, operators)
            for field, tokens, operators in EXPECTED.values()
        )
    ]
    if len(matrix_texts) < 2:
        fail(
            "the complete nine-condition FilterBuilder tree must appear together "
            f"in at least TWO query nodes (queries 1 and 2 both reuse it per the "
            f"prompt); found it in {len(matrix_texts)} node(s)"
        )

    if len(nodes) != 3:
        fail(
            f"expected exactly 3 Query Entity Records connector nodes "
            f"(connectorKey={CONNECTOR_KEY!r}, objectName matching Query Entity "
            f"Records or a dynamic List/GET on {ENTITY!r}), found {len(nodes)}"
        )

    sorted_by_score = [
        (task, pairs)
        for task, pairs, text in zip(nodes, pairs_list, texts)
        if sorted_field(pairs, text) == "score"
    ]
    if len(sorted_by_score) < 2:
        fail(f"expected >=2 query nodes sorted by score, found {len(sorted_by_score)}")

    paginated = [
        (task, pairs)
        for task, pairs in sorted_by_score
        if has_numeric(pairs, LIMIT_NAMES) and has_numeric(pairs, OFFSET_NAMES)
    ]
    if len(paginated) < 2:
        fail(
            f"expected >=2 score-sorted queries with limit + start/offset set, "
            f"found {len(paginated)}"
        )

    descending = [
        task for task, pairs, text in zip(nodes, pairs_list, texts) if is_descending(pairs, text)
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
        f"OK: {path} -- 3 Query Entity Records nodes; the full filter tree "
        f"appears in {len(matrix_texts)} of them; {len(paginated)} paginated + "
        f"{len(descending)} descending query nodes present"
    )


if __name__ == "__main__":
    main()
