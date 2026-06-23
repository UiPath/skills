#!/usr/bin/env python3
"""Conversational context (semantic index) resource check.

NEAR-MIRROR of `lowcode/context_index/check_context_index.py`. The context
resource discovery, resource assertions, and bindings validation are IDENTICAL
to the autonomous flavor. The ONLY difference is the schema assertion:

  - Autonomous: typed `question`/`answer` schemas + schema sync (Rule 4).
  - Conversational: input/output schemas MUST be empty (Critical Rule 24).

Validates:
  1. A context resource under resources/<folder> (located by type; the folder
     name is the agent's choice) declares:
       - $resourceType == "context"
       - contextType == "index"
       - name == its folder name (convention: the folder matches `name`)
       - indexName == "UiPathAgentsProductKnowledge" (the deployed index)
       - folderPath == "Shared/uipath-agents" (the deployed Orchestrator folder)
  2. settings.retrievalMode is one of the documented values:
     "semantic" | "structured" | "deepRAG" | "batchTransform".
  3. agent.json + entry-points.json input/output schemas are BOTH empty
     (conversational; Critical Rule 24).
  4. bindings_v2.json contains an "index" resource binding whose
     key + value.name.defaultValue + value.folderPath.defaultValue
     match the deployed UiPathAgentsProductKnowledge index.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "SupportSol" / "SupportBot"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCES = ROOT / "resources"
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


def find_context_resource() -> tuple[str, dict]:
    """Locate the context resource by type. The resource folder name is the
    agent's choice (convention: it matches the resource's `name` field) — it is
    NOT pinned to the index name; the index identity lives in `indexName`."""
    if not RESOURCES.is_dir():
        sys.exit(f"FAIL: {RESOURCES} does not exist — no context resource authored")
    for path in sorted(RESOURCES.rglob("resource.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("$resourceType") == "context" and data.get("contextType") == "index":
            print(f"OK: found context resource at {path.relative_to(ROOT.parent)}")
            return path.parent.name, data
    sys.exit(
        f'FAIL: no context resource ($resourceType=="context", contextType=="index") '
        f"found under {RESOURCES}"
    )


def assert_context_resource(folder_name: str, resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "context":
        sys.exit(f'FAIL: resource.json $resourceType should be "context", got {rtype!r}')
    ctype = resource.get("contextType")
    if ctype != "index":
        sys.exit(f'FAIL: resource.json contextType should be "index", got {ctype!r}')
    name = resource.get("name")
    if name != folder_name:
        sys.exit(
            f"FAIL: resource.json name {name!r} must match its folder name {folder_name!r} "
            "(convention: the resource folder matches the resource's `name`)"
        )
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
            f"(the deployed Orchestrator folder of the index), got {folder_path!r}"
        )
    print(
        f'OK: resource.json is $resourceType="context", contextType="index", '
        f"name=folder={resource.get('name')!r}, indexName={EXPECTED_INDEX_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
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
    """The ONLY divergence from the autonomous check: a conversational agent
    leaves input/output schemas empty (Critical Rule 24), instead of asserting
    a typed question/answer contract + schema sync."""
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
            "uip agent validate should emit one for the context-grounding index."
        )
    if len(index_bindings) > 1:
        sys.exit(
            f"FAIL: bindings_v2.json contains {len(index_bindings)} index bindings; "
            "exactly one is expected."
        )
    binding = index_bindings[0]

    key = binding.get("key")
    if key != EXPECTED_INDEX_NAME:
        sys.exit(
            f"FAIL: bindings_v2.json index binding key should be {EXPECTED_INDEX_NAME!r}, got {key!r}"
        )

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
        f"OK: bindings_v2.json index binding key={EXPECTED_INDEX_NAME!r}, "
        f"name={EXPECTED_INDEX_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
    )


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    folder_name, resource = find_context_resource()
    bindings = load(BINDINGS)

    assert_context_resource(folder_name, resource)
    assert_retrieval_mode(resource)
    assert_conversational_schemas_empty(agent, entry)
    assert_bindings_index(bindings)


if __name__ == "__main__":
    main()
