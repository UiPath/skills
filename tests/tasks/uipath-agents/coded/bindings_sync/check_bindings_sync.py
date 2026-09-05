#!/usr/bin/env python3
"""Multi-module bindings sync check."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-agents")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.bindings_assertions import (  # noqa: E402
    assert_entrypoint_link,
    assert_value_field,
    find_resource,
    load_bindings,
)


def _entrypoint() -> tuple[str, str]:
    """Return (uniqueId, filePath) of the project's single entrypoint."""
    path = ROOT / "entry-points.json"
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")
    entry_points = doc.get("entryPoints") or []
    if len(entry_points) != 1:
        sys.exit(f"FAIL: expected exactly 1 entrypoint, got {len(entry_points)}")
    ep = entry_points[0]
    unique_id, file_path = ep.get("uniqueId"), ep.get("filePath")
    if not unique_id or not file_path:
        sys.exit(f"FAIL: entrypoint missing uniqueId/filePath: {json.dumps(ep)}")
    print(f"OK: entry-points.json declares entrypoint {file_path!r} ({unique_id})")
    return unique_id, file_path


def main() -> None:
    unique_id, file_path = _entrypoint()
    doc = load_bindings(ROOT / "bindings.json")

    resources = doc["resources"]
    if len(resources) != 3:
        sys.exit(
            f"FAIL: expected exactly 3 resources (process + bucket + asset, "
            f"the two bucket calls deduped), got {len(resources)}: "
            f"{json.dumps(resources, indent=2)}"
        )
    print("OK: bindings.json has exactly 3 resources")

    process = find_resource(doc, resource="process", key="data-scraper")
    assert_value_field(process, field="name", expected="data-scraper")
    assert_value_field(process, field="folderPath", expected="")

    bucket = find_resource(doc, resource="bucket", key="invoice-data")
    assert_value_field(bucket, field="name", expected="invoice-data")
    assert_value_field(bucket, field="folderPath", expected="")

    asset = find_resource(doc, resource="asset", key="api-key.Shared")
    assert_value_field(asset, field="name", expected="api-key")
    assert_value_field(asset, field="folderPath", expected="Shared")

    for entry in (process, bucket, asset):
        assert_entrypoint_link(entry, unique_id=unique_id, file_path=file_path)


if __name__ == "__main__":
    main()
