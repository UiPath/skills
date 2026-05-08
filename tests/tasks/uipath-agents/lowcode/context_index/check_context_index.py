#!/usr/bin/env python3
"""Context (semantic index) resource check.

Validates:
  1. resources/ProductKnowledge/resource.json declares a context
     resource of type "index":
       - $resourceType == "context"
       - contextType == "index"
       - indexName == "ProductKnowledge"
  2. settings.retrievalMode is one of the documented values:
     "semantic" | "structured" | "deepRAG" | "batchTransform".
  3. agent.json.inputSchema  == entry-points.json entryPoints[0].input
     agent.json.outputSchema == entry-points.json entryPoints[0].output
     (Critical Rule 4 — schema sync.)
  4. agent.json.inputSchema declares a required `question` (string)
     and agent.json.outputSchema declares an `answer` (string).
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "KnowledgeSol" / "ProductSupportAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "ProductKnowledge" / "resource.json"

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
    index_name = resource.get("indexName")
    if index_name != "ProductKnowledge":
        sys.exit(
            f'FAIL: resource.json indexName should be "ProductKnowledge", got {index_name!r}'
        )
    print('OK: resource.json is $resourceType="context", contextType="index", indexName="ProductKnowledge"')


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


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    resource = load(RESOURCE)

    assert_context_resource(resource)
    assert_retrieval_mode(resource)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_input_shape(in_schema)
    assert_output_shape(out_schema)


if __name__ == "__main__":
    main()
