#!/usr/bin/env python3
"""Native connector use OR task-specific managed HTTP fallback (BPMN).

Ported from Flow `connector_features/check_managed_http_fallback.py`: same
three scenarios (Jira Get Issue path params, Google Tasks query params, Gmail
Send Mail enum), translated from a whole-flow JSON blob search to an XML walk
over the registry-driven ``Intsvc.*`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3 "Connector
enrichment" and §"Connectionless vs connector HTTP"). One shared grader
serves all three ports (`path_params.yaml`, `query_params.yaml`, `enum.yaml`)
per _porting/BATCH1-ADDENDUM.md, mirroring Flow's own single shared script.

Assertion map (Flow -> BPMN):
  F check_managed_http_fallback.py:110 "connector_key in full_text" (native  -> whole-document blob search for
    connector present, whole-flow blob search)                                 connector_key (main(), same leniency)
  F check_managed_http_fallback.py:57-66  _check_path_params required
      -> FALLBACK_CHECKS["path_params"]["required"]
    evidence ["engce-00000","method","get"]                                     checked against each candidate node's
    blob
  F check_managed_http_fallback.py:69-81  _check_query_params required
      -> FALLBACK_CHECKS["query_params"]["required"]
    evidence [...]
  F check_managed_http_fallback.py:84-95  _check_enum required evidence      -> FALLBACK_CHECKS["enum"]["required"]
    ["gmail.googleapis.com","method","post","importance","medium"] (Flow's    (kept verbatim, including "medium" --
    own literal list, kept as-is even though the scenario asks for "high":     see the note below)
    faithfulness contract forbids "fixing" a Flow assertion during a port)
  F check_managed_http_fallback.py:32-40  http-fallback node selection
      -> is_managed_http_node(): Intsvc.HttpExecution
    (flow node type == core.action.http.v2)                                      or Intsvc.UnifiedHttpRequest
    (construct-
                                                                                   translation table's "Managed HTTP"
                                                                                   row)
  I               locate/parse .bpmn                                        -> parse_bpmn(NAME_HINT)
  T               curated OR generic connectorKey match for the native       -> main(): connectorKey anywhere in the
                  branch (BATCH1-ADDENDUM: classify by connectorKey, not       document, regardless of curated/generic
                  by objectName)                                               objectName spelling
  T               generic HTTP connector (uipath-uipath-http) accepted as    -> is_managed_http_node() also accepts
                  an additional managed-HTTP wrapper form: query_params.yaml   Intsvc.ActivityExecution whose
                  prompt explicitly asks for "a managed HTTP fallback through   connectorKey == uipath-uipath-http,
                  the generic uipath-uipath-http connector" -- the connector-   the same shape check_non_catalog_http_
                  mode-HTTP-via-generic-connector pattern documented in         fallback.py (batch 1 pilot) accepts for
                  BATCH1-ADDENDUM and modeled by check_non_catalog_http_       an unrelated non-catalog service. This
                  fallback.py, which is Intsvc.ActivityExecution, not          widens acceptance (never narrows a Flow
                  Intsvc.HttpExecution                                         assertion), so it is safe under the
                                                                                 Normalization pass's "dropping/widening
                                                                                 only" rule.
  T               collect uipath:input elements at any depth under the node -> context_inputs()/all_node_values() via
                                                                                 node_blob()

Note on the enum fallback list: Flow's `_check_enum` requires the literal
substring "medium" in the HTTP fallback node's blob although the scenario's
fixed value is "importance": "high" (a schema/enum-documentation check, or a
latent Flow bug). Kept verbatim: the port never weakens or corrects a Flow
assertion. In CI the native-connector branch has carried every run so far
(run 35789221753), so the fallback list has not been exercised.

No Flow assertions dropped: the native-connector short-circuit, all three
required-evidence lists, and the http-fallback-node-must-exist precondition
all have a BPMN counterpart above.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_managed_http_fallback.py <NAME_HINT> <connector_key>
    <path_params|query_params|enum>
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import context_value, elements, fail, has_type, parse_bpmn  # noqa: E402

# Task-like leaf elements only -- NOT root.iter(), which also yields ancestor
# containers (bpmn:process, bpmn:definitions). Those ancestors' serialized
# subtree recursively contains every descendant's inputs, so has_type()/
# context_value() would misclassify them as matching "nodes" too and collapse
# the per-node evidence check into a whole-document one (see
# check_slack_http_fallback.py's is_slack_connector_node docstring for the
# same root.iter() ancestor-matching pitfall).
CANDIDATE_TAGS = (
    "sendTask",
    "serviceTask",
    "task",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
)

ACTIVITY_TYPE = "Intsvc.ActivityExecution"
HTTP_TYPES = ("Intsvc.HttpExecution", "Intsvc.UnifiedHttpRequest")
# The generic HTTP connector -- query_params.yaml's prompt explicitly names it
# as the fallback path (BATCH1-ADDENDUM's connector-mode-HTTP-via-generic-
# connector pattern, same shape as check_non_catalog_http_fallback.py).
GENERIC_HTTP_CONNECTOR_KEY = "uipath-uipath-http"

# Required evidence per check, kept verbatim from Flow's own literal lists
# (see the module note on "enum"'s "medium").
FALLBACK_CHECKS: dict[str, dict[str, object]] = {
    "path_params": {
        "label": "Jira Get Issue path-params HTTP fallback",
        "required": ["engce-00000", "method", "get"],
    },
    "query_params": {
        "label": "Google Tasks query-params HTTP fallback",
        "required": [
            "tasks.googleapis.com/tasks/v1/lists",
            "/tasks",
            "method",
            "get",
            "showhidden",
            "true",
        ],
    },
    "enum": {
        "label": "Gmail send-mail enum HTTP fallback",
        "required": ["gmail.googleapis.com", "method", "post", "importance", "medium"],
    },
}


def is_managed_http_node(node: ET.Element) -> bool:
    if any(has_type(node, token) for token in HTTP_TYPES):
        return True
    if has_type(node, ACTIVITY_TYPE):
        return context_value(node, "connectorKey").strip().lower() == GENERIC_HTTP_CONNECTOR_KEY
    return False


def node_blob(node: ET.Element) -> str:
    """Whole serialized node, lowercased -- mirrors Flow's
    ``json.dumps(http_nodes, sort_keys=True).lower()`` whole-node blob
    search."""
    return ET.tostring(node, encoding="unicode").lower()


def require_all(haystack: str, needles: list[str]) -> list[str]:
    return [needle for needle in needles if needle.lower() not in haystack]


def main() -> None:
    if len(sys.argv) != 4:
        fail(
            "usage: check_managed_http_fallback.py <name_hint> <connector_key> "
            f"<{'|'.join(FALLBACK_CHECKS)}>"
        )

    name_hint, connector_key, check_name = sys.argv[1], sys.argv[2], sys.argv[3]
    check = FALLBACK_CHECKS.get(check_name)
    if check is None:
        fail(f"unknown check {check_name!r}; expected one of {sorted(FALLBACK_CHECKS)}")

    path, root = parse_bpmn(name_hint)

    # Native connector branch -- mirrors Flow's whole-document blob search
    # (main():110) exactly, including its leniency (a connectorKey mention
    # anywhere in the document is accepted, not only on a matched node).
    full_blob = ET.tostring(root, encoding="unicode").lower()
    if connector_key.lower() in full_blob:
        print(f"OK: native connector present ({connector_key}) in {path}")
        return

    candidates = [node for tag in CANDIDATE_TAGS for node in elements(root, tag)]
    fallback_nodes = [node for node in candidates if is_managed_http_node(node)]
    if not fallback_nodes:
        fail(
            "Neither native connector nor managed HTTP fallback found "
            f"(connector_key={connector_key!r}, check={check_name!r}) in {path}"
        )

    label = str(check["label"])
    required = list(check["required"])  # type: ignore[arg-type]
    best_missing: list[str] | None = None
    for node in fallback_nodes:
        missing = require_all(node_blob(node), required)
        if not missing:
            print(f"OK: managed HTTP fallback has {check_name} evidence in {path}")
            return
        if best_missing is None or len(missing) < len(best_missing):
            best_missing = missing

    fail(f"{label} missing expected evidence: {best_missing}")


if __name__ == "__main__":
    main()
