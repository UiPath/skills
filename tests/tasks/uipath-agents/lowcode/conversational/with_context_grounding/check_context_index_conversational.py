#!/usr/bin/env python3
"""Conversational + context-grounding (semantic index) check.

Mirrors `lowcode/context_index/check_context_index.py` but for the
conversational flavor. Differences:
  - `inputSchema.properties` and `outputSchema.properties` MUST be empty
    on a conversational agent (Critical Rule 24); the autonomous version
    asserts question/answer typed fields.
  - No `.agent-builder/` assertion — that's a publish-prep build artifact
    not required for source editing.
  - All context-resource and bindings checks are identical to autonomous
    (the context resource shape does not differ between flavors).

The local context-resource folder and its `name` field are the author's free
choice — the binding resolves the index by `indexName` (see
`references/lowcode/capabilities/context/index.md`: refresh resolves the ECS
index by `indexName`, and the emitted binding is keyed by the index name).
So the resource is located by SCANNING `resources/<*>/resource.json` for the
one bound to EXPECTED_INDEX_NAME — never by a hard-coded folder name (same
approach as `inline_context_index`). Only the load-bearing fields are asserted:
`indexName`, `folderPath`, retrieval mode, and the emitted binding's
`value.name` / `value.folderPath`.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "SupportSol" / "SupportBot"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCES_DIR = ROOT / "resources"
BINDINGS = ROOT / "bindings_v2.json"

EXPECTED_INDEX_NAME = "UiPathAgentsProductKnowledge"
EXPECTED_FOLDER_PATH = "Shared/uipath-agents"

VALID_RETRIEVAL_MODES = {"semantic", "structured", "deepRAG", "batchTransform"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_context_resource() -> dict:
    """Locate the context resource by indexName, not by folder name.

    The resource folder and `name` are arbitrary local labels; the binding
    resolves the index by `indexName`. Scan every `resources/<*>/resource.json`
    and return the one bound to EXPECTED_INDEX_NAME. Exactly one is expected.
    """
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: Missing resources directory {RESOURCES_DIR}")
    matches = []
    for sub in sorted(RESOURCES_DIR.iterdir()):
        rj = sub / "resource.json"
        if not rj.is_file():
            continue
        try:
            d = json.loads(rj.read_text())
        except json.JSONDecodeError:
            continue
        if (
            d.get("$resourceType") == "context"
            and d.get("contextType") == "index"
            and d.get("indexName") == EXPECTED_INDEX_NAME
        ):
            matches.append((rj, d))
    if not matches:
        sys.exit(
            f"FAIL: no context/index resource bound to indexName="
            f"{EXPECTED_INDEX_NAME!r} found under {RESOURCES_DIR} — the resource "
            f"folder name is free, but exactly one context resource with that "
            f"indexName must exist"
        )
    if len(matches) > 1:
        names = [p.parent.name for p, _ in matches]
        sys.exit(
            f"FAIL: {len(matches)} context resources bound to {EXPECTED_INDEX_NAME!r} "
            f"({names}); expected exactly one"
        )
    rj, resource = matches[0]
    print(
        f"OK: found context resource bound to indexName={EXPECTED_INDEX_NAME!r} "
        f"at resources/{rj.parent.name}/resource.json (folder name is the author's choice)"
    )
    return resource


def assert_context_resource(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "context":
        sys.exit(f'FAIL: resource.json $resourceType should be "context", got {rtype!r}')
    ctype = resource.get("contextType")
    if ctype != "index":
        sys.exit(f'FAIL: resource.json contextType should be "index", got {ctype!r}')
    # The resource `name` field is a free local label and is intentionally NOT
    # asserted — the index binds by `indexName` (below), not by the label.
    index_name = resource.get("indexName")
    if index_name != EXPECTED_INDEX_NAME:
        sys.exit(
            f"FAIL: resource.json indexName should be {EXPECTED_INDEX_NAME!r} "
            f"(matching the deployed index), got {index_name!r}"
        )
    folder_path = resource.get("folderPath")
    if folder_path != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: resource.json folderPath should be {EXPECTED_FOLDER_PATH!r} "
            f"(the full deployed Orchestrator folder of the index, from "
            f"`uip solution resources list` — do not truncate to the parent), "
            f"got {folder_path!r}"
        )
    print(
        f'OK: resource.json is $resourceType="context", contextType="index", '
        f"indexName={EXPECTED_INDEX_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
    )


def assert_retrieval_mode(resource: dict) -> None:
    settings = resource.get("settings")
    if not isinstance(settings, dict):
        sys.exit(f"FAIL: resource.json settings must be an object: got {settings!r}")
    mode = settings.get("retrievalMode")
    if mode not in VALID_RETRIEVAL_MODES:
        sys.exit(
            f"FAIL: settings.retrievalMode must be one of {sorted(VALID_RETRIEVAL_MODES)}, "
            f"got {mode!r}"
        )
    print(f"OK: settings.retrievalMode is {mode!r}")


def assert_conversational_schemas_empty(agent: dict, entry: dict) -> None:
    in_props = (agent.get("inputSchema") or {}).get("properties") or {}
    if in_props:
        sys.exit(
            f"FAIL: agent.json inputSchema.properties must be empty for conversational "
            f"(Rule 24), got keys: {list(in_props)}"
        )
    in_required = (agent.get("inputSchema") or {}).get("required") or []
    if in_required:
        sys.exit(
            f"FAIL: agent.json inputSchema.required must be empty for conversational "
            f"(Rule 24), got {in_required!r}"
        )
    out_props = (agent.get("outputSchema") or {}).get("properties") or {}
    if out_props:
        sys.exit(
            f"FAIL: agent.json outputSchema.properties must be empty for conversational "
            f"(Rule 24), got keys: {list(out_props)}"
        )
    print("OK: agent.json inputSchema and outputSchema both empty (Rule 24)")

    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    ep_in_props = (ep.get("input") or {}).get("properties") or {}
    ep_out_props = (ep.get("output") or {}).get("properties") or {}
    if ep_in_props or ep_out_props:
        sys.exit(
            f"FAIL: entry-points.json schemas must mirror agent.json (both empty for conversational), "
            f"got input.properties={list(ep_in_props)}, output.properties={list(ep_out_props)}"
        )
    print("OK: entry-points.json schemas mirror agent.json (both empty)")


def assert_bindings_index(bindings: dict) -> None:
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        sys.exit(f"FAIL: bindings_v2.json resources must be a list, got {resources!r}")

    index_bindings = [r for r in resources if isinstance(r, dict) and r.get("resource") == "index"]
    if not index_bindings:
        sys.exit(
            'FAIL: bindings_v2.json has no resource entry with resource="index". '
            "uip agent refresh should emit one for the context-grounding index."
        )
    if len(index_bindings) > 1:
        sys.exit(
            f"FAIL: bindings_v2.json contains {len(index_bindings)} index bindings; "
            "exactly one is expected."
        )
    binding = index_bindings[0]

    # The binding `key` mirrors the resource's local name (the author's free
    # choice), so it is intentionally NOT asserted. The load-bearing identity is
    # value.name (the ECS index name) + value.folderPath (the deployment folder).
    value = binding.get("value")
    if not isinstance(value, dict):
        sys.exit(f"FAIL: bindings_v2.json index binding value must be an object, got {value!r}")

    name_field = value.get("name") or {}
    name_default = name_field.get("defaultValue") if isinstance(name_field, dict) else None
    if name_default != EXPECTED_INDEX_NAME:
        sys.exit(
            f"FAIL: bindings_v2.json index binding value.name.defaultValue should be "
            f"{EXPECTED_INDEX_NAME!r}, got {name_default!r}"
        )

    folder_field = value.get("folderPath") or {}
    folder_default = folder_field.get("defaultValue") if isinstance(folder_field, dict) else None
    if folder_default != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: bindings_v2.json index binding value.folderPath.defaultValue should be "
            f"{EXPECTED_FOLDER_PATH!r} (matching the deployed index folder), got {folder_default!r}"
        )

    print(
        f"OK: bindings_v2.json index binding value.name={EXPECTED_INDEX_NAME!r}, "
        f"folderPath={EXPECTED_FOLDER_PATH!r}"
    )


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    resource = find_context_resource()
    bindings = load(BINDINGS)

    assert_context_resource(resource)
    assert_retrieval_mode(resource)
    assert_conversational_schemas_empty(agent, entry)
    assert_bindings_index(bindings)

    print("\nAll conversational context-grounding checks passed.")


if __name__ == "__main__":
    main()
