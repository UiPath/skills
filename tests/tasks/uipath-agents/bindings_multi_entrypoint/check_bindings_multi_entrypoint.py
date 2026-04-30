#!/usr/bin/env python3
"""Multi-entrypoint binding resolution check.

The project has two entrypoints (`main` / `report`) and two SDK
calls (one per file). The bindings reference allows the agent to
either link each binding to a chosen entrypoint via
`EntryPointUniqueId` or leave the field off entirely (the user
might have chosen "None" in the disambiguation prompt). The wrong
outcome is fabricating an entrypoint id that matches neither real
entrypoint — that would silently break runtime resource resolution.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    count_resources_by_type,
)


def _real_entrypoint_uids() -> set[str]:
    path = ROOT / "entry-points.json"
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    uids = {ep.get("uniqueId") for ep in (doc.get("entryPoints") or [])}
    uids.discard(None)
    if len(uids) < 2:
        sys.exit(f"FAIL: expected ≥2 entrypoints, got uniqueIds={sorted(uids)}")
    return uids


def main() -> None:
    real = _real_entrypoint_uids()
    print(f"OK: entry-points.json declares {len(real)} entrypoint(s)")
    doc = load_bindings(ROOT / "bindings.json")
    bucket_n = count_resources_by_type(doc, "bucket")
    asset_n = count_resources_by_type(doc, "asset")
    if bucket_n != 1:
        sys.exit(f"FAIL: expected exactly 1 bucket binding, got {bucket_n}")
    if asset_n != 1:
        sys.exit(f"FAIL: expected exactly 1 asset binding, got {asset_n}")
    print("OK: one bucket + one asset binding present")
    bucket = find_resource(doc, resource="bucket", key="reports-bucket.Reports")
    assert_value_field(bucket, field="name", expected="reports-bucket")
    assert_value_field(bucket, field="folderPath", expected="Reports")
    asset = find_resource(doc, resource="asset", key="report_email.Reports")
    assert_value_field(asset, field="name", expected="report_email")
    assert_value_field(asset, field="folderPath", expected="Reports")
    # Validate any EntryPointUniqueId references a real entrypoint.
    for entry in (bucket, asset):
        value = entry.get("value") or {}
        ep = value.get("EntryPointUniqueId")
        if not isinstance(ep, dict):
            print(f"OK: {entry.get('resource')} binding has no EntryPointUniqueId (acceptable)")
            continue
        uid = ep.get("defaultValue")
        if uid not in real:
            sys.exit(
                f'FAIL: {entry.get("resource")} binding references '
                f'EntryPointUniqueId={uid!r}, which is not one of the real '
                f'entrypoints {sorted(real)}.'
            )
        print(
            f"OK: {entry.get('resource')} binding's EntryPointUniqueId "
            f"resolves to a real entrypoint ({uid!r})"
        )


if __name__ == "__main__":
    main()
