#!/usr/bin/env python3
"""DF smoke_query (BPMN): verify the complete filter and pagination matrix.

Ported from Flow
`connector_features/datafabric_connector/check_smoke_query_filter.py`. Same
scenario (three Query Entity Records activities against FlowCodeEvalEntity: a
nine-condition FilterBuilder tree paged twice, plus a third active-only
descending query) and the same assertions, re-homed from a Flow node's
`inputs.detail` JSON dict to a BPMN `bpmn:sendTask` carrying the registry
`Intsvc.ActivityExecution` wrapper (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4). Flow's task
names no project, so this grader locates the BPMN file with no name hint.

Assertion map (Flow → BPMN):
  F check_smoke_query_filter.py:82-85    node type suffix `.query-entity-records`                → T: curated|generic entity-CRUD objectName classification (query_entity_nodes)
  F check_smoke_query_filter.py:71-75,90-95  nine filter conditions via structured tree or runtime text → has_expected_filter() / node_representation()
  F check_smoke_query_filter.py:97-104   full nine-condition tree present in >=1 node             → matrix_texts non-empty check (see NOTE below)
  F check_smoke_query_filter.py:106-109  exactly 3 Query Entity Records activities                 → len(nodes) != 3 check
  F check_smoke_query_filter.py:130-135  >=2 nodes sorted by score                                 → sorted_field() == "score", count >= 2
  F check_smoke_query_filter.py:137-143  >=2 score-sorted nodes carry limit + start                → has_numeric(LIMIT_NAMES) and has_numeric(OFFSET_NAMES)
  F check_smoke_query_filter.py:145-151  >=1 node with descending sort (isAscending=false)         → is_descending()
  I                locate/parse .bpmn (file exists, well-formed XML, no name hint)                 → parse_bpmn()
  I                parse a target="body" CDATA as JSON when present (Flow read structured fields)  → validate_body_inputs() / parse_json_maybe()
  T                curated|generic entity-CRUD node classification                                 → query_entity_nodes()
  T                inputs at any depth                                                             → all_inputs() walks `.//uipath:input`
  T                ORDER BY in query text                                                          → bpmn_check.order_by() fallback in sorted_field()/is_descending()
  T                sort/limit/offset field-name synonyms (registry may name the field differently)  → SORT_FIELD_NAMES/LIMIT_NAMES/OFFSET_NAMES sets
  DROPPED          entity_referenced() gate on node classification    (Flow's node-type filter is entity-agnostic; not in Flow)
  DROPPED          connection-binding check (=bindings.<id> resolves to a declared Connection binding)  (Flow never checked connections)
  DROPPED          require_no_private_connector_values                (not in Flow)
  DROPPED          require_sequence_integrity                         (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED          require_di_for_visible_elements                     (not in Flow; `bpmn validate` criterion covers structure)

  NOTE: a prior version of this grader required the complete nine-condition
  tree to appear in at least TWO nodes. Flow's grader (line 100, `if not
  matrix_nodes`) only requires it in at least ONE. Restored to match Flow
  exactly -- see the `matrix_texts` check in `main()` below.

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
         since the VALUE of every filter-bearing input (FILTER_TEXT_NAMES) is
         part of the same search blob -- both representations are searched
         together, the same non-exclusive combination Flow's own
         `node_filter_text` uses. Nothing else goes into that blob: see
         node_representation() for why input names and binding references are
         excluded.

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

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. Exactly 3 bpmn:sendTask nodes carry Intsvc.ActivityExecution with
     connectorKey uipath-uipath-dataservice and either objectName matching
     Query Entity Records (QueryEntityRecords|QueryEntityRecordsCurated|QueryEntityRecords_V3)
     or objectName == FlowCodeEvalEntity with operation List / method GET
     (a dynamic per-entity query shape).
  3. Any `target="body"` input present is valid JSON (optional -- absence
     is not an error).
  4. Every one of the nine filter conditions appears somewhere across the
     three nodes, and the complete nine-condition set appears together in
     at least ONE node (Flow's threshold -- queries 1 and 2 both reuse the
     full tree per the prompt, but only one match is required to pass).
  5. At least 2 nodes are sorted by `score` (any direction).
  6. At least 2 of those score-sorted nodes carry both a limit and a
     start/offset value.
  7. At least 1 node has a descending sort.
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
    context_value,
    elements,
    fail,
    has_type,
    order_by,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
OBJECT_NAMES = {"queryentityrecords", "queryentityrecordscurated", "queryentityrecords_v3"}
ENTITY = "flowcodeevalentity"

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
# Every operator tuple carries BOTH spellings the two representations use: the
# Flow FilterBuilder vocabulary word that appears in a structured tree leaf's
# `operator`, and the CEQL token the CLI emits into a runtime queryExpression
# string. `boolean` and `uuid` assert no operator at all (Flow does not either
# -- the value/UUID shape is the assertion), so they stay empty.
EXPECTED = {
    "boolean": ("active", ("true",), ()),
    "decimal": ("score", ("8.5",), ("greaterthanorequal", ">=")),
    "integer": ("viewcount", ("1000",), ("greaterthanorequal", ">=")),
    "string": ("title", ("filterfixture-matrix",), ("equals", "=")),
    "multiline": ("description", ("sci-fi",), ("contains", "like")),
    "date": ("releasedate", ("2025-01-01",), ("lessthan", "<")),
    "datetime": ("lastupdated", ("2024-01-01",), ("greaterthanorequal", ">=")),
    "uuid": ("externalid", (), ()),
    "null": ("description", (), ("isnull", "is null")),
}

SORT_FIELD_NAMES = {"sortby", "sortfield", "orderby", "_sortfieldname", "sort"}
DIRECTION_NAMES = {"isascending", "isdescending", "direction", "sortdirection"}
LIMIT_NAMES = {"limit", "top", "pagesize"}
OFFSET_NAMES = {"start", "offset", "skip"}

# The only inputs whose VALUE may carry a filter expression. Flow's
# `node_filter_text` read exactly one field (`queryParameters.queryExpression`)
# plus the structured tree; this is the BPMN equivalent set, widened only by
# the alternate names a skill may pick for the same runtime string and by
# `metadata`, the context input the observed artifacts nest the structured tree
# inside. Everything else (`entityName`, `limit`, `start`, `isAscending`,
# `connection`, `folderKey`, ...) is deliberately excluded.
FILTER_TEXT_NAMES = {
    "queryexpression",
    "where",
    "filter",
    "filterexpression",
    "query",
    "metadata",
}

# A Maestro binding reference is not a filter: `=bindings.Binding_X` and
# `=vars.Y` would otherwise put a free `=` into every node's search blob and
# make the operator half of most EXPECTED rows unfalsifiable.
BINDING_VALUE_RE = re.compile(r"^\s*=\s*(bindings|vars)\.", re.IGNORECASE)


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

    `text` is the Flow-style lowercase search blob for the nine-condition
    filter check, and carries ONLY what Flow's `node_filter_text` carried: the
    VALUE of a filter-bearing input (FILTER_TEXT_NAMES -- Flow read
    `queryParameters.queryExpression`), plus the structured FilterBuilder
    leaves dumped back to text if a savedFilterTrees.queryExpression tree is
    found in any JSON-shaped input. Both representations are searched together,
    the same non-exclusive way Flow combined them.

    Input NAMES, binding references (`=bindings.X`, `=vars.Y`) and the
    non-filter inputs (`entityName`, `limit`, `start`, `isAscending`, ...) are
    deliberately NOT in `text`: they guarantee an `=` and other operator
    characters in every blob, which makes the operator half of most EXPECTED
    rows unfalsifiable. They remain in `pairs`, which is name-keyed.
    """
    inputs = all_inputs(task)
    pairs: list = [(inp.attrib.get("name") or "", input_val(inp)) for inp in inputs]
    text_parts: list[str] = []
    for name, value in pairs:
        if name.lower() not in FILTER_TEXT_NAMES:
            continue
        if BINDING_VALUE_RE.match(value or ""):
            continue
        text_parts.append((value or "").lower())
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


def sorted_field(pairs: list, text: str = "") -> str:
    values = values_by_name(pairs, SORT_FIELD_NAMES)
    if values:
        return values[0].lower()
    # A sort may also ride inside the CEQL-like query string itself
    # ("... ORDER BY 'score' ASC") -- bpmn_check.order_by() is the one
    # definition of that clause, shared with check_df_smoke_update_existing.
    return order_by(text)[0]


def is_descending(pairs: list, text: str = "") -> bool:
    if order_by(text)[1] == "desc":
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
    if not matrix_texts:
        fail(
            "the nine filter conditions are split across query nodes; one Query "
            "Entity Records node must contain the complete FilterBuilder tree"
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

    print(
        f"OK: {path} -- 3 Query Entity Records nodes; the full filter tree "
        f"appears in {len(matrix_texts)} of them; {len(paginated)} paginated + "
        f"{len(descending)} descending query nodes present"
    )


if __name__ == "__main__":
    main()
