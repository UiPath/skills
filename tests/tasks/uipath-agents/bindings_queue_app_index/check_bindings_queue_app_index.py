#!/usr/bin/env python3
"""Five-binding-type sweep check.

Asserts the hand-authored project produced exactly the five bindings
expected by the bindings-reference tables — one each for queue, app,
index, connection, mcpServer — with the right key construction
(`<name>.<folder>` for most, bare `<key>` for connections) and the
load-bearing metadata fields (`ActivityName`, `DisplayLabel`).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    assert_metadata_field,
    count_resources_by_type,
)


def main() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    # queue — the `create_item_async` call site has no folder_path,
    # so per bindings-reference "No folder_path" rule the key is just
    # the queue name (no trailing dot).
    queue = find_resource(doc, resource="queue", key="OrderQueue")
    assert_value_field(queue, field="name", expected="OrderQueue")
    assert_metadata_field(queue, field="ActivityName", expected="create_item_async")
    # app (Action Center)
    app = find_resource(doc, resource="app", key="ReviewApp.Ops")
    assert_value_field(app, field="name", expected="ReviewApp")
    assert_value_field(app, field="folderPath", expected="Ops")
    assert_metadata_field(app, field="ActivityName", expected="create_async")
    assert_metadata_field(app, field="DisplayLabel", expected="ReviewApp")
    # index (Context Grounding)
    index = find_resource(doc, resource="index", key="kb_index.Shared")
    assert_value_field(index, field="name", expected="kb_index")
    assert_value_field(index, field="folderPath", expected="Shared")
    # The reference says ALL methods bind via the same `retrieve_async`
    # ActivityName, even when the call site is `search_async`.
    assert_metadata_field(index, field="ActivityName", expected="retrieve_async")
    # connection
    connection = find_resource(doc, resource="connection", key="salesforce-prod-conn")
    assert_value_field(connection, field="ConnectionId", expected="salesforce-prod-conn")
    assert_metadata_field(connection, field="UseConnectionService", expected="True")
    # mcpServer
    mcp = find_resource(doc, resource="mcpServer", key="weather-mcp.Tools")
    assert_value_field(mcp, field="name", expected="weather-mcp")
    assert_value_field(mcp, field="folderPath", expected="Tools")
    assert_metadata_field(mcp, field="ActivityName", expected="retrieve_async")
    # Deduplication / no-extras: each kind has exactly one entry.
    for kind in ("queue", "app", "index", "connection", "mcpServer"):
        n = count_resources_by_type(doc, kind)
        if n != 1:
            sys.exit(f"FAIL: expected exactly 1 `{kind}` binding entry, got {n}")
    print("OK: each of queue/app/index/connection/mcpServer has exactly one binding entry")


if __name__ == "__main__":
    main()
