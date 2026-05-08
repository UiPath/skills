#!/usr/bin/env python3
"""Context (semantic index) resource check.

Validates:
  1. resources/UiPathAgentsProductKnowledge/resource.json declares a context
     resource of type "index":
       - $resourceType == "context"
       - contextType == "index"
       - name == indexName == "UiPathAgentsProductKnowledge"
       - folderPath == "Shared/uipath-agents" (the deployed Orchestrator folder)
  2. settings.retrievalMode is one of the documented values:
     "semantic" | "structured" | "deepRAG" | "batchTransform".
  3. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
  4. agent.json.inputSchema declares a required `question` (string)
     and agent.json.outputSchema declares an `answer` (string).
  5. bindings_v2.json contains an "index" resource binding whose
     key + value.name.defaultValue + value.folderPath.defaultValue
     match the deployed UiPathAgentsProductKnowledge index.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "KnowledgeSol" / "ProductSupportAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "UiPathAgentsProductKnowledge" / "resource.json"
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


def assert_context_resource(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "context":
        sys.exit(f'FAIL: resource.json $resourceType should be "context", got {rtype!r}')
    ctype = resource.get("contextType")
    if ctype != "index":
        sys.exit(f'FAIL: resource.json contextType should be "index", got {ctype!r}')
    name = resource.get("name")
    if name != EXPECTED_INDEX_NAME:
        sys.exit(
            f'FAIL: resource.json name should be {EXPECTED_INDEX_NAME!r} '
            f"(matching the deployed index), got {name!r}"
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
        f"name=indexName={EXPECTED_INDEX_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
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


def assert_schema_sync(agent: dict, entry: dict) -> tuple[dict, dict]:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    agent_in = agent.get("inputSchema")
    entry_in = ep.get("input")
    if agent_in != entry_in:
        sys.exit(
            "FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input"
        )
    agent_out = agent.get("outputSchema")
    entry_out = ep.get("output")
    if agent_out != entry_out:
        sys.exit(
            "FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output"
        )
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")
    return agent_in, agent_out


def assert_input_shape(schema: dict) -> None:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict) or "question" not in props:
        sys.exit(
            f"FAIL: inputSchema.properties missing 'question'; got {list(props) if isinstance(props, dict) else props!r}"
        )
    q = props["question"]
    if not isinstance(q, dict) or q.get("type") != "string":
        sys.exit(f"FAIL: inputSchema.properties.question.type should be 'string', got {q!r}")
    required = schema.get("required")
    if not isinstance(required, list) or "question" not in required:
        sys.exit(f"FAIL: inputSchema.required must contain 'question', got {required!r}")
    print("OK: inputSchema declares required question:string")


def assert_output_shape(schema: dict) -> None:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict) or "answer" not in props:
        sys.exit(
            f"FAIL: outputSchema.properties missing 'answer'; got {list(props) if isinstance(props, dict) else props!r}"
        )
    a = props["answer"]
    if not isinstance(a, dict) or a.get("type") != "string":
        sys.exit(f"FAIL: outputSchema.properties.answer.type should be 'string', got {a!r}")
    print("OK: outputSchema declares answer:string")


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
    resource = load(RESOURCE)
    bindings = load(BINDINGS)

    assert_context_resource(resource)
    assert_retrieval_mode(resource)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_input_shape(in_schema)
    assert_output_shape(out_schema)
    assert_bindings_index(bindings)


if __name__ == "__main__":
    main()
