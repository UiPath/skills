"""Reusable bindings.json assertions for coded-agent check scripts.

The schema is documented in
`skills/uipath-agents/references/coded/lifecycle/bindings-reference.md`.
These helpers exit the process with a `FAIL: ...` message on any
assertion failure (so they pair naturally with `run_command` success
criteria in task YAMLs — exit code 0 means PASS, anything else FAIL).

Print one `OK: ...` line per passing assertion so eval transcripts make
the diagnostic chain obvious.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_bindings(path: Path | str = "bindings.json") -> dict:
    """Load and validate the bindings.json envelope.

    Asserts `version == "2.0"` and `resources` is a list, then returns
    the whole document.
    """
    p = Path(path)
    if not p.is_file():
        sys.exit(f"FAIL: Missing {p}")
    try:
        doc = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {p} is not valid JSON: {e}")
    version = doc.get("version")
    if version != "2.0":
        sys.exit(f'FAIL: bindings.json version should be "2.0", got {version!r}')
    resources = doc.get("resources")
    if not isinstance(resources, list):
        sys.exit(f"FAIL: bindings.json resources must be a list, got {type(resources).__name__}")
    print(f'OK: bindings.json envelope is version="2.0" with {len(resources)} resource(s)')
    return doc


def find_resource(
    doc: dict,
    *,
    resource: str,
    key: str,
) -> dict:
    """Return the unique resource entry matching `resource` + `key`.

    Exits with FAIL if zero or more than one match is found — duplicate
    keys are a known authoring failure mode and should never pass.
    """
    resources = doc.get("resources") or []
    matches = [
        r for r in resources
        if isinstance(r, dict)
        and r.get("resource") == resource
        and r.get("key") == key
    ]
    if not matches:
        sys.exit(
            f'FAIL: no resource with resource=="{resource}" and key=="{key}" '
            f"in bindings.json. Got: {json.dumps(resources, indent=2)}"
        )
    if len(matches) > 1:
        sys.exit(
            f'FAIL: expected exactly one resource with resource=="{resource}" '
            f'and key=="{key}", got {len(matches)}'
        )
    print(f'OK: found {resource} entry with key="{key}"')
    return matches[0]


def assert_value_field(
    entry: dict,
    *,
    field: str,
    expected: Any,
    inner: str = "defaultValue",
) -> None:
    """Assert `entry["value"][field][inner] == expected`.

    Default `inner="defaultValue"` matches the standard binding shape
    (`"name": {"defaultValue": ..., "isExpression": false, ...}`). Pass
    `inner="displayName"` to assert the displayName label, etc.
    """
    value = entry.get("value")
    if not isinstance(value, dict):
        sys.exit(f"FAIL: entry value must be an object, got {value!r}")
    block = value.get(field)
    if not isinstance(block, dict):
        sys.exit(f'FAIL: entry value.{field} must be an object, got {block!r}')
    actual = block.get(inner)
    if actual != expected:
        sys.exit(
            f'FAIL: value.{field}.{inner} should be {expected!r}, got {actual!r}'
        )
    print(f'OK: value.{field}.{inner} == {expected!r}')


def assert_metadata_field(entry: dict, *, field: str, expected: Any) -> None:
    """Assert `entry["metadata"][field] == expected`."""
    metadata = entry.get("metadata")
    if not isinstance(metadata, dict):
        sys.exit(f"FAIL: entry metadata must be an object, got {metadata!r}")
    actual = metadata.get(field)
    if actual != expected:
        sys.exit(
            f'FAIL: metadata.{field} should be {expected!r}, got {actual!r}'
        )
    print(f'OK: metadata.{field} == {expected!r}')


def assert_entrypoint_link(
    entry: dict,
    *,
    unique_id: str,
    file_path: str,
) -> None:
    """Assert the resource is bound to an entrypoint via
    `EntryPointUniqueId` (preferred) with `displayName == file_path`.

    Falls back to `EntryPointPath` only if `EntryPointUniqueId` is
    absent — matches the resolver rules in `bindings-reference.md`
    Step 4.
    """
    value = entry.get("value") or {}
    uid_block = value.get("EntryPointUniqueId")
    if isinstance(uid_block, dict):
        if uid_block.get("defaultValue") != unique_id:
            sys.exit(
                f'FAIL: EntryPointUniqueId.defaultValue should be {unique_id!r}, '
                f'got {uid_block.get("defaultValue")!r}'
            )
        if uid_block.get("displayName") != file_path:
            sys.exit(
                f'FAIL: EntryPointUniqueId.displayName must equal the entrypoint '
                f'filePath ({file_path!r}), got {uid_block.get("displayName")!r}'
            )
        print(
            f'OK: entry bound to entrypoint uniqueId={unique_id!r} '
            f'(displayName={file_path!r})'
        )
        return
    path_block = value.get("EntryPointPath")
    if isinstance(path_block, dict):
        if path_block.get("defaultValue") != file_path:
            sys.exit(
                f'FAIL: EntryPointPath.defaultValue should be {file_path!r}, '
                f'got {path_block.get("defaultValue")!r}'
            )
        print(f'OK: entry bound to entrypoint filePath={file_path!r} (fallback)')
        return
    sys.exit(
        f'FAIL: entry has neither EntryPointUniqueId nor EntryPointPath; expected '
        f'a binding to entrypoint uniqueId={unique_id!r} (filePath={file_path!r})'
    )


def count_resources_by_type(doc: dict, resource_type: str) -> int:
    """Return the number of entries with `resource == resource_type`."""
    resources = doc.get("resources") or []
    return sum(
        1 for r in resources
        if isinstance(r, dict) and r.get("resource") == resource_type
    )
