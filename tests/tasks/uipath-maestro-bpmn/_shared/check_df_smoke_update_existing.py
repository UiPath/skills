#!/usr/bin/env python3
"""Data Fabric smoke_update_existing_flow (BPMN): verify a brownfield revert.

Ported from Flow
`connector_features/datafabric_connector/check_smoke_update_existing_flow.py`.
Same scenario: `pre_run` (`scaffold_movie_report_bpmn.py`) builds a real
`MovieReportBpmn` with one Query Entity Records activity on
FlowCodeEvalEntity, no filter, no sort, and snapshots the initial bytes to
`pre_state.bpmn`. The agent must set a filter (active=true AND
score>=8.5) and a descending sort on that one activity, then revert both,
touching no other node/edge/binding/variable. This checker proves the
final `.bpmn` is equivalent to the snapshot on the three fields the agent
was allowed to touch, and identical everywhere else.

Assertion map (Flow -> BPMN):
  F check_smoke_update_existing_flow.py:47-50 (queryParameters.queryExpression reverted)
        -> has_filter(final) must be False (initial never has one; see NOTE on equality vs. presence below)
  F check_smoke_update_existing_flow.py:51-54 (bodyParameters._sortFieldName reverted)
        -> sorted_field(final) == sorted_field(initial) (exact match, both "" expected)
  F check_smoke_update_existing_flow.py:55-57 (queryParameters.isAscending reverted, default False)
        -> ascending_flag(final) == ascending_flag(initial) (exact match on the raw flag)
  F check_smoke_update_existing_flow.py:60-66 (`if initial != final`: whole-document no-drift check)
        -> canonical XML equality on both documents after scrubbing ONLY the
           filter/sort-named inputs from the query node in both copies
  I  locate/parse .bpmn (fixed brownfield path, no name hint -- Flow's task
     names its project too, so the path is hardcoded exactly as Flow's
     grader hardcodes FLOW/SNAP)                      -> load()
  I  parse a JSON-shaped uipath:input's value when present (Flow read a
     structured FilterBuilder dict directly)           -> parse_json_maybe()
  T  curated|generic entity-CRUD node classification (never by objectName
     alone)                                            -> is_query_node()
  T  inputs at any depth under uipath:activity          -> all_inputs()
  T  structured FilterBuilder tree (savedFilterTrees.queryExpression) OR a
     runtime CEQL-like `where`/`filter` string OR ORDER BY in query text
                                                        -> has_filter(), sorted_field(), ORDER_BY_RE
  T  sort field-name synonyms (sortField/sortBy/orderBy/_sortFieldName/sort)
                                                        -> SORT_FIELD_NAMES
  DROPPED  require_no_private_connector_values   (not in Flow grader)
  DROPPED  require_sequence_integrity             (not in Flow grader; `bpmn validate` criterion covers structure)
  DROPPED  require_di_for_visible_elements         (not in Flow grader; `bpmn validate` criterion covers structure)
  DROPPED  "exactly one" / uniqueness checks       (Flow's q_node() takes the FIRST matching node with
                                                     no count assertion; this checker does the same --
                                                     an extra node is still caught by the no-drift diff)

NOTE on filter equality vs. presence: Flow compares
`i_qp.get("queryExpression") != f_qp.get("queryExpression")` on parsed JSON
values, which -- because the scaffold's initial value is always absent
(None) -- reduces to "final must also have no queryExpression". BPMN has no
single fixed field for a filter (curated separate query inputs, a runtime
CEQL string, or a structured tree nested in the context `metadata` JSON are
all legitimate; see BATCH1-ADDENDUM.md), so this checker asserts the BPMN
equivalent of that reduced condition directly: the query node carries no
filter expression in any of those shapes. This is not a weaker check than
Flow's for this fixture -- both ultimately require "no filter present";
translating Flow's literal `!=` into an exact-value comparison would require
picking one filter representation to pin, which would fail a legitimate
agent that reverted via a different (but equally empty) representation.

Checks performed:
  1. Both `pre_state.bpmn` and the final `.bpmn` exist and are well-formed XML.
  2. Each contains a classified Query Entity Records node (curated
     `QueryEntityRecordsCurated`/`QueryEntityRecords_V3`, or the generic
     entity-CRUD List/GET form) on FlowCodeEvalEntity.
  3. `pre_state.bpmn`'s query node carries no filter (sanity: catches a
     scaffold regression before blaming the agent).
  4. The final query node carries no filter (queryExpression / where /
     filter input, structured FilterBuilder tree, or CEQL text all absent).
  5. The final query node's sort field and ascending/descending flag match
     the initial node's exactly.
  6. The two documents are canonically identical once the filter/sort
     inputs are stripped from the query node in both -- no label, limit,
     edge, binding, variable, or other-node drift.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail  # noqa: E402

BPMN = Path("MovieReportSolution/MovieReportBpmn/MovieReportBpmn.bpmn")
SNAP = Path("MovieReportSolution/MovieReportBpmn/pre_state.bpmn")

CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
ENTITY = "flowcodeevalentity"
OBJECT_NAMES = {"queryentityrecordscurated", "queryentityrecords_v3"}

FILTER_NAMES = {"queryexpression", "filterexpression", "filter", "where"}
SORT_FIELD_NAMES = {"sortby", "sortfield", "orderby", "_sortfieldname", "sort"}
DIRECTION_NAMES = {"isascending", "isdescending", "direction", "sortdirection"}

ORDER_BY_RE = re.compile(r"\border\s+by\s+([a-z0-9_]+)(?:\s+(asc|desc))?", re.IGNORECASE)


def load(path: Path) -> ET.Element:
    if not path.exists():
        fail(f"missing {path}")
    raw = path.read_text()
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        fail(f"{path} is not well-formed XML: {exc}")


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def activity_root(task: ET.Element) -> ET.Element | None:
    return task.find(".//uipath:activity", NS)


def all_inputs(task: ET.Element) -> list[ET.Element]:
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


def is_query_node(task: ET.Element) -> bool:
    if not has_type(task, ACTIVITY_TYPE):
        return False
    if context_value(task, "connectorKey") != CONNECTOR_KEY:
        return False
    object_name = context_value(task, "objectName").lower()
    operation = context_value(task, "operation").lower()
    method = context_value(task, "method").upper()
    if object_name in OBJECT_NAMES:
        return True
    return object_name == ENTITY and (operation == "list" or method == "GET")


def find_query_node(root: ET.Element) -> ET.Element | None:
    """First connector sendTask classified as Query Entity Records. Mirrors
    Flow's `q_node()`, which returns the FIRST `.query-entity-records` node
    with no uniqueness assertion (see PORTING-BRIEF.md Grading contract:
    never add an "exactly one" rule Flow's grader did not have)."""
    for task in elements(root, "sendTask"):
        if is_query_node(task):
            return task
    return None


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


def find_saved_filter_trees(node, out: list) -> None:
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


def structured_filter_leaves(parsed) -> list:
    trees: list = []
    find_saved_filter_trees(parsed, trees)
    leaves: list = []
    for tree in trees:
        filter_leaves_from_tree(tree, leaves)
    return leaves


def flatten_json_pairs(node, pairs: list) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                flatten_json_pairs(v, pairs)
            else:
                pairs.append((k, "" if v is None else str(v)))
    elif isinstance(node, list):
        for item in node:
            flatten_json_pairs(item, pairs)


def node_signals(task: ET.Element) -> tuple[list, str]:
    """(pairs, text) for a query node: `pairs` is every flat uipath:input
    (name, value) plus every leaf of any JSON-shaped input's parsed value
    (covers a sort/filter field nested inside the context `metadata` JSON
    instead of a flat input); `text` is a lowercase search blob of every
    input's raw name+value+text plus any structured FilterBuilder leaves
    found in a JSON-shaped input. Mirrors
    check_df_smoke_query_filter.py's node_representation()."""
    inputs = all_inputs(task)
    pairs = [(inp.attrib.get("name") or "", input_val(inp)) for inp in inputs]
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


def has_filter(pairs: list, text: str) -> bool:
    """True if the node carries ANY filter expression: a flat
    queryExpression/filter/where input with non-empty, non-trivial content,
    a structured FilterBuilder tree with at least one leaf, or a WHERE
    clause inside the query text."""
    for k, v in pairs:
        if k.lower() in FILTER_NAMES and str(v).strip() not in ("", "{}", "[]"):
            return True
    if re.search(r'"filters"\s*:\s*\[\s*[{"\[]', text):
        return True
    if re.search(r"\bwhere\b", text, re.IGNORECASE):
        return True
    return False


def sorted_field(pairs: list, text: str) -> str:
    for k, v in pairs:
        if k.lower() in SORT_FIELD_NAMES and str(v).strip():
            return str(v).strip().lower()
    match = ORDER_BY_RE.search(text)
    return match.group(1).lower() if match else ""


def ascending_flag(pairs: list, text: str) -> str:
    """Raw normalized direction signal, defaulting to 'unset' when absent --
    equality between initial and final is what matters (mirrors Flow's
    `queryParameters.get("isAscending", False)` default-then-compare, not a
    judgment about which direction is "the" default)."""
    match = ORDER_BY_RE.search(text)
    if match and match.group(2):
        return match.group(2).lower()
    for k, v in pairs:
        if k.lower() in DIRECTION_NAMES:
            return str(v).strip().lower()
    return "unset"


def strip_filter_sort_inputs(task: ET.Element | None) -> None:
    """Remove filter/sort-named uipath:input elements from `task` in place --
    used to build a scrubbed copy of the document for the document-wide
    no-drift comparison (see main())."""
    if task is None:
        return
    root = activity_root(task)
    if root is None:
        return
    input_tag = f"{{{NS['uipath']}}}input"
    for parent in root.iter():
        for child in list(parent):
            if child.tag != input_tag:
                continue
            name = (child.attrib.get("name") or "").lower()
            if name in FILTER_NAMES or name in SORT_FIELD_NAMES or name in DIRECTION_NAMES:
                parent.remove(child)


def canonical(root: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(root, encoding="unicode"), strip_text=True)


def main() -> int:
    initial_root = load(SNAP)
    final_root = load(BPMN)

    i_q = find_query_node(initial_root)
    f_q = find_query_node(final_root)
    if i_q is None or f_q is None:
        fail(
            f"Query Entity Records node missing on {ENTITY} "
            f"(pre_state={i_q is not None}, final={f_q is not None})"
        )

    i_pairs, i_text = node_signals(i_q)
    f_pairs, f_text = node_signals(f_q)

    if has_filter(i_pairs, i_text):
        fail("pre_state.bpmn's query node unexpectedly already carries a filter -- scaffold drifted")

    if has_filter(f_pairs, f_text):
        fail("final query node still carries a filter -- revert not clean (filter not removed)")

    i_sort = sorted_field(i_pairs, i_text)
    f_sort = sorted_field(f_pairs, f_text)
    if f_sort != i_sort:
        fail(f"sort field not reverted: pre_state={i_sort!r} final={f_sort!r}")

    i_dir = ascending_flag(i_pairs, i_text)
    f_dir = ascending_flag(f_pairs, f_text)
    if f_dir != i_dir:
        fail(f"sort direction not reverted: pre_state={i_dir!r} final={f_dir!r}")

    # No drift anywhere else in the document: scrub only the filter/sort
    # inputs from a COPY of the query node in each document, then require
    # the two documents to be canonically identical. Catches label / limit
    # / edge / binding / variable / other-node changes the targeted checks
    # above would miss -- the XML analog of Flow's `if initial != final`
    # whole-document diff.
    initial_copy = ET.fromstring(ET.tostring(initial_root, encoding="unicode"))
    final_copy = ET.fromstring(ET.tostring(final_root, encoding="unicode"))
    strip_filter_sort_inputs(find_query_node(initial_copy))
    strip_filter_sort_inputs(find_query_node(final_copy))

    i_canon = canonical(initial_copy)
    f_canon = canonical(final_copy)
    if i_canon != f_canon:
        fail("document drift beyond the query node's filter/sort fields -- revert not clean")

    print("OK: MovieReportBpmn reverted cleanly; query node has no filter, no sort, "
          "document byte-equivalent to pre_state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
