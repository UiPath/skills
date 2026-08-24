#!/usr/bin/env python3
"""Verify a configured Jira "Get Issue" activity exercises the DTL
loadByDefault=true feature: its Project and Issue Type dropdowns are
pre-populated, so the agent must resolve and pre-select the FIRST available
project + issue type and persist them in BOTH locations —

  * the runtime input bucket (`inputs.detail.queryParameters.{project,issuetype}`)
  * the design-time replay cache (`essentialConfiguration.customFieldsRequestDetails
    .parameterValues`, inside the `=jsonString:` configuration blob)

plus the target issue key in `inputs.detail.pathParameters.issueId`.

The runtime bucket is what the connector actually sends; the cache is what
Studio Web replays to re-render the parent-field-driven schema. Dropping
either leaves the field set unresolved (MST-9107-class silent corruption that
`flow validate` does not catch), so both must be present AND agree.

Usage:
    check_dtl_load_by_default.py [flow_glob]

flow_glob defaults to '**/DTLLoadByDefaultTrueTest*.flow'; falls back to any
.flow containing the Jira Get Issue activity.

Exit codes:
  0 — node found; issueId set; project + issuetype present in queryParameters
      and customFieldsRequestDetails, with matching values
  1 — assertion failed (message printed)
"""

from __future__ import annotations

import glob
import json
import sys

JSONSTRING_PREFIX = "=jsonString:"
NODE_TYPE = "uipath.connector.uipath-atlassian-jira.get-issue"
EXPECTED_ISSUE_KEY = "ENGCE-00000"


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _find_flow_with_node(pattern: str) -> tuple[str, dict]:
    candidates = glob.glob(pattern, recursive=True) or glob.glob(
        "**/*.flow", recursive=True
    )
    if not candidates:
        _fail("no .flow file found in the workspace")
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as handle:
                flow = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        for node in flow.get("nodes", []):
            if str(node.get("type", "")) == NODE_TYPE:
                return path, node
    _fail(
        f"no node of type {NODE_TYPE} found in any .flow "
        f"matching '{pattern}' (or fallback '**/*.flow') — the flow must use "
        "the Jira Get Issue activity"
    )
    raise AssertionError("unreachable")


def _tuples_to_map(parameter_values: object, path: str) -> dict:
    """customFieldsRequestDetails.parameterValues is an array of [key, value]
    tuples, never an object map (Studio Web emits Map.entries())."""
    if not isinstance(parameter_values, list):
        _fail(
            f"essentialConfiguration.customFieldsRequestDetails.parameterValues "
            f"is not an array of [key, value] tuples in {path}"
        )
    result: dict = {}
    for entry in parameter_values:
        if not isinstance(entry, list) or len(entry) != 2:
            _fail(
                f"parameterValues entry {entry!r} is not a [key, value] tuple "
                f"in {path}"
            )
        result[entry[0]] = entry[1]
    return result


def main() -> None:
    pattern = (
        sys.argv[1] if len(sys.argv) > 1 else "**/DTLLoadByDefaultTrueTest*.flow"
    )
    path, node = _find_flow_with_node(pattern)

    detail = (node.get("inputs") or {}).get("detail")
    if not isinstance(detail, dict):
        _fail(
            f"node '{node.get('id')}' in {path} has no inputs.detail — "
            "node configure was not run"
        )

    # 1. Target issue key in the path parameter.
    issue_id = (detail.get("pathParameters") or {}).get("issueId")
    if issue_id != EXPECTED_ISSUE_KEY:
        _fail(
            f"inputs.detail.pathParameters.issueId is '{issue_id}', "
            f"expected '{EXPECTED_ISSUE_KEY}' in {path}"
        )

    # 2. First available project + issue type pre-selected at runtime.
    query = detail.get("queryParameters") or {}
    query_project = query.get("project")
    query_issuetype = query.get("issuetype")
    if not query_project:
        _fail(f"inputs.detail.queryParameters.project is missing or empty in {path}")
    if not query_issuetype:
        _fail(
            f"inputs.detail.queryParameters.issuetype is missing or empty in {path}"
        )

    # 3. Same values persisted in the design-time replay cache.
    configuration = detail.get("configuration")
    if not isinstance(configuration, str) or not configuration.startswith(
        JSONSTRING_PREFIX
    ):
        _fail(
            f"inputs.detail.configuration is missing or not a "
            f"'{JSONSTRING_PREFIX}' envelope in {path}"
        )
    try:
        blob = json.loads(configuration[len(JSONSTRING_PREFIX) :])
    except json.JSONDecodeError as error:
        _fail(f"configuration blob is not valid JSON in {path}: {error}")

    essential = blob.get("essentialConfiguration")
    if not isinstance(essential, dict):
        _fail(f"configuration blob has no essentialConfiguration object in {path}")

    cfrd = essential.get("customFieldsRequestDetails")
    if not isinstance(cfrd, dict):
        _fail(
            "essentialConfiguration.customFieldsRequestDetails is missing — the "
            f"loadByDefault schema-replay cache was not written in {path}"
        )

    cache = _tuples_to_map(cfrd.get("parameterValues"), path)
    cache_project = cache.get("project")
    cache_issuetype = cache.get("issuetype")
    if not cache_project:
        _fail(f"customFieldsRequestDetails has no 'project' value in {path}")
    if not cache_issuetype:
        _fail(f"customFieldsRequestDetails has no 'issuetype' value in {path}")

    # 4. Runtime bucket and replay cache must agree.
    if str(cache_project) != str(query_project):
        _fail(
            f"project mismatch in {path}: queryParameters has "
            f"'{query_project}' but customFieldsRequestDetails has "
            f"'{cache_project}'"
        )
    if str(cache_issuetype) != str(query_issuetype):
        _fail(
            f"issuetype mismatch in {path}: queryParameters has "
            f"'{query_issuetype}' but customFieldsRequestDetails has "
            f"'{cache_issuetype}'"
        )

    print(
        f"OK: {path} node '{node.get('id')}' fetches issue "
        f"'{issue_id}' with project '{query_project}' + issuetype "
        f"'{query_issuetype}' pre-selected in queryParameters and "
        "customFieldsRequestDetails"
    )


if __name__ == "__main__":
    main()
