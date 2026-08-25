#!/usr/bin/env python3
"""SubType=credentialAsset binding check.

Validates that the agent, given a Python file containing
`await sdk.assets.retrieve_credential_async("billing_api_key",
folder_path="Finance")`, produced a bindings.json that:

  1. is well-formed JSON with `version == "2.0"` and a `resources`
     array,
  2. contains exactly one resource entry whose `resource == "asset"`
     and whose `key == "billing_api_key.Finance"`,
  3. carries the correct asset shape — `name.defaultValue ==
     "billing_api_key"` and `folderPath.defaultValue == "Finance"`,
  4. emits `metadata.SubType == "credentialAsset"`. This is the
     specific rule introduced by the SubType inference change in
     bindings-reference.md (high-confidence, method-name-definitive).

A missing or wrong SubType is the primary failure mode the change
exists to prevent: without it, `uipath push` creates a plain
string-asset virtual placeholder for what should be a credential.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())
BINDINGS = ROOT / "bindings.json"

EXPECTED_NAME = "billing_api_key"
EXPECTED_FOLDER = "Finance"
EXPECTED_KEY = f"{EXPECTED_NAME}.{EXPECTED_FOLDER}"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_envelope(bindings: dict) -> list:
    version = bindings.get("version")
    if version != "2.0":
        sys.exit(f'FAIL: bindings.json version should be "2.0", got {version!r}')
    resources = bindings.get("resources")
    if not isinstance(resources, list) or not resources:
        sys.exit(f"FAIL: bindings.json resources must be a non-empty list, got {resources!r}")
    print(f'OK: bindings.json envelope is version="2.0" with {len(resources)} resource(s)')
    return resources


def find_asset_entry(resources: list) -> dict:
    matches = [
        r for r in resources
        if isinstance(r, dict)
        and r.get("resource") == "asset"
        and r.get("key") == EXPECTED_KEY
    ]
    if not matches:
        sys.exit(
            f'FAIL: no resource with resource=="asset" and key=="{EXPECTED_KEY}" in '
            f"resources: {json.dumps(resources, indent=2)}"
        )
    if len(matches) > 1:
        sys.exit(f"FAIL: expected exactly one matching asset entry, got {len(matches)}")
    print(f'OK: found asset entry with key="{EXPECTED_KEY}"')
    return matches[0]


def assert_value_shape(entry: dict) -> None:
    value = entry.get("value")
    if not isinstance(value, dict):
        sys.exit(f"FAIL: asset entry value must be an object: {value!r}")
    name_block = value.get("name", {})
    if name_block.get("defaultValue") != EXPECTED_NAME:
        sys.exit(
            f'FAIL: value.name.defaultValue should be "{EXPECTED_NAME}", '
            f"got {name_block.get('defaultValue')!r}"
        )
    folder_block = value.get("folderPath", {})
    if folder_block.get("defaultValue") != EXPECTED_FOLDER:
        sys.exit(
            f'FAIL: value.folderPath.defaultValue should be "{EXPECTED_FOLDER}", '
            f"got {folder_block.get('defaultValue')!r}"
        )
    print(
        f'OK: value.name="{EXPECTED_NAME}", value.folderPath="{EXPECTED_FOLDER}"'
    )


def assert_subtype(entry: dict) -> None:
    metadata = entry.get("metadata")
    if not isinstance(metadata, dict):
        sys.exit(f"FAIL: asset entry metadata must be an object: {metadata!r}")
    subtype = metadata.get("SubType")
    if subtype != "credentialAsset":
        sys.exit(
            f'FAIL: metadata.SubType should be "credentialAsset" for a '
            f"retrieve_credential_async call, got {subtype!r}. Without "
            "this, `uipath push` creates a plain string-asset placeholder "
            "instead of a credential."
        )
    print('OK: metadata.SubType == "credentialAsset"')


def main() -> None:
    bindings = load(BINDINGS)
    resources = assert_envelope(bindings)
    entry = find_asset_entry(resources)
    assert_value_shape(entry)
    assert_subtype(entry)


if __name__ == "__main__":
    main()
