#!/usr/bin/env python3
"""Asset SubType inference check.

Three asset retrieves at the call site, each annotated with a
different concrete type. The check requires:

  1. All three asset bindings exist with the right keys
     (`<name>.Shared`).
  2. Each binding's `metadata.SubType` is EITHER the matching SubType
     for the annotation (`stringAsset` / `integerAsset` /
     `booleanAsset`) OR absent. Per the bindings reference, omitting
     the SubType is always safe — `uipath push` falls back to the
     base `kind` and the asset still works. The annotation-driven
     inference is the high-confidence path; we accept either.
  3. No SubType is set to a *wrong* value (e.g. `credentialAsset`
     on a non-credential retrieve, or `integerAsset` on a `str` site).
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
    count_resources_by_type,
)

EXPECTED = {
    "api_key": "stringAsset",
    "max_retries": "integerAsset",
    "feature_enabled": "booleanAsset",
}


def main() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    n = count_resources_by_type(doc, "asset")
    if n != 3:
        sys.exit(f"FAIL: expected exactly 3 asset bindings, got {n}")
    print("OK: three asset bindings present")
    for name, expected_subtype in EXPECTED.items():
        entry = find_resource(doc, resource="asset", key=f"{name}.Shared")
        assert_value_field(entry, field="name", expected=name)
        assert_value_field(entry, field="folderPath", expected="Shared")
        metadata = entry.get("metadata") or {}
        actual = metadata.get("SubType")
        if actual is None:
            print(f'OK: {name} asset binding has no SubType (acceptable fallback)')
            continue
        if actual == expected_subtype:
            print(f'OK: {name} asset binding has SubType={actual!r} (high-confidence inference)')
            continue
        sys.exit(
            f'FAIL: {name} asset binding has SubType={actual!r}, expected '
            f'either {expected_subtype!r} (from annotation) or omitted. '
            f'Wrong SubType is worse than no SubType — `uipath push` would '
            f'create the wrong placeholder kind.'
        )


if __name__ == "__main__":
    main()
