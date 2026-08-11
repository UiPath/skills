#!/usr/bin/env python3
"""Standalone low-code agent memory-space feature check.

Validates:
  1. features/SupportRecall/feature.json declares a CLI-managed
     memorySpace feature for the expected tenant memory space and folder.
  2. Dynamic few-shot retrieval uses the requested hybrid search, result
     count, and similarity threshold, weighting the `userQuestion` field.
  3. A starter memory item was seeded (matched loosely by content — the
     prompt describes the example in plain language, so ids/metadata/memory
     type are left to the agent and not asserted).
  4. agent.json schemas stay synchronized with entry-points.json.
  5. bindings_v2.json contains a generated memorySpace binding with
     the expected name and folderPath.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "MemorySol" / "SupportMemoryAgent"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
FEATURE = ROOT / "features" / "SupportRecall" / "feature.json"
BINDINGS = ROOT / "bindings_v2.json"
BUILDER = ROOT / ".agent-builder" / "agent.json"

EXPECTED_FEATURE_NAME = "SupportRecall"
EXPECTED_MEMORY_SPACE = "UiPathAgentsSupportMemory"
EXPECTED_FOLDER_PATH = "Shared/uipath-agents"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_schema_sync(agent: dict, entry: dict) -> tuple[dict, dict]:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    agent_in = agent.get("inputSchema")
    entry_in = ep.get("input")
    if agent_in != entry_in:
        sys.exit("FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input")
    agent_out = agent.get("outputSchema")
    entry_out = ep.get("output")
    if agent_out != entry_out:
        sys.exit("FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output")
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")
    return agent_in, agent_out


def assert_input_output_shape(input_schema: dict, output_schema: dict) -> None:
    in_props = input_schema.get("properties") if isinstance(input_schema, dict) else None
    if not isinstance(in_props, dict) or "userQuestion" not in in_props:
        sys.exit("FAIL: inputSchema.properties must contain userQuestion")
    if in_props["userQuestion"].get("type") != "string":
        sys.exit(f"FAIL: userQuestion must be a string, got {in_props['userQuestion']!r}")
    required = input_schema.get("required")
    if not isinstance(required, list) or "userQuestion" not in required:
        sys.exit(f"FAIL: inputSchema.required must include userQuestion, got {required!r}")

    out_props = output_schema.get("properties") if isinstance(output_schema, dict) else None
    if not isinstance(out_props, dict) or "answer" not in out_props:
        sys.exit("FAIL: outputSchema.properties must contain answer")
    if out_props["answer"].get("type") != "string":
        sys.exit(f"FAIL: answer must be a string, got {out_props['answer']!r}")
    print("OK: schemas declare required userQuestion:string and answer:string")


def assert_feature(feature: dict) -> None:
    if feature.get("$featureType") != "memorySpace":
        sys.exit(f'FAIL: $featureType should be "memorySpace", got {feature.get("$featureType")!r}')
    if feature.get("name") != EXPECTED_FEATURE_NAME:
        sys.exit(f"FAIL: feature name should be {EXPECTED_FEATURE_NAME!r}, got {feature.get('name')!r}")
    if feature.get("memorySpaceName") != EXPECTED_MEMORY_SPACE:
        sys.exit(
            f"FAIL: memorySpaceName should be {EXPECTED_MEMORY_SPACE!r}, "
            f"got {feature.get('memorySpaceName')!r}"
        )
    if feature.get("folderPath") != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: folderPath should be {EXPECTED_FOLDER_PATH!r}, "
            f"got {feature.get('folderPath')!r}"
        )
    if not feature.get("isEnabled"):
        sys.exit(f"FAIL: isEnabled must be truthy, got {feature.get('isEnabled')!r}")
    fid = feature.get("id")
    if not isinstance(fid, str) or "-" not in fid:
        sys.exit(f"FAIL: feature id missing or malformed: {fid!r}")
    print(
        f'OK: memory feature {EXPECTED_FEATURE_NAME!r} attaches '
        f"{EXPECTED_MEMORY_SPACE!r} in {EXPECTED_FOLDER_PATH!r}"
    )


def assert_dynamic_few_shot(feature: dict) -> None:
    settings = feature.get("dynamicFewShotSettings")
    if not isinstance(settings, dict):
        sys.exit(f"FAIL: dynamicFewShotSettings must be an object, got {settings!r}")
    if settings.get("isEnabled") is not True:
        sys.exit(f"FAIL: dynamic few-shot should be enabled, got {settings.get('isEnabled')!r}")
    if settings.get("searchMode") != "hybrid":
        sys.exit(f"FAIL: searchMode should be 'hybrid', got {settings.get('searchMode')!r}")
    if settings.get("resultCount") != 5:
        sys.exit(f"FAIL: resultCount should be 5, got {settings.get('resultCount')!r}")
    threshold = settings.get("threshold")
    if not isinstance(threshold, (int, float)) or abs(float(threshold) - 0.25) > 1e-9:
        sys.exit(f"FAIL: threshold should be 0.25, got {threshold!r}")
    fields = settings.get("fieldSettings")
    if not isinstance(fields, list):
        sys.exit(f"FAIL: fieldSettings must be a list, got {fields!r}")
    matches = [
        f for f in fields
        if isinstance(f, dict)
        and f.get("name") == "userQuestion"
        and isinstance(f.get("weight"), (int, float))
        and abs(float(f["weight"]) - 1.0) < 1e-9
    ]
    if not matches:
        sys.exit(f"FAIL: fieldSettings must contain userQuestion weight 1, got {fields!r}")
    print("OK: dynamic few-shot settings match requested hybrid retrieval configuration")


def assert_seed_item(feature: dict) -> None:
    items = feature.get("items")
    if not isinstance(items, list) or not items:
        sys.exit(f"FAIL: feature must contain at least one seeded item, got {items!r}")
    values = [i.get("value", "") for i in items if isinstance(i, dict)]
    # The prompt describes the starter example in plain language ("a refund
    # case that looks like a past escalation"); match on that gist rather than
    # an exact string, and don't assert key/feedbackId/memoryType/metadata.
    if not any(isinstance(v, str) and "refund" in v.lower() for v in values):
        sys.exit(f"FAIL: expected a seeded item about the refund example, got {values!r}")
    print("OK: a starter memory item about the refund example is present")


def assert_memory_binding(bindings: dict) -> None:
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        sys.exit(f"FAIL: bindings_v2.json resources must be a list, got {resources!r}")
    matches = [
        r for r in resources
        if isinstance(r, dict)
        and r.get("resource") == "memorySpace"
        and isinstance(r.get("value"), dict)
        and (r["value"].get("name") or {}).get("defaultValue") == EXPECTED_MEMORY_SPACE
        and (r["value"].get("folderPath") or {}).get("defaultValue") == EXPECTED_FOLDER_PATH
    ]
    if len(matches) != 1:
        sys.exit(
            "FAIL: expected exactly one memorySpace binding for "
            f"{EXPECTED_MEMORY_SPACE!r} in {EXPECTED_FOLDER_PATH!r}, got {len(matches)}"
        )
    metadata = matches[0].get("metadata") or {}
    if metadata.get("solutionsSupport") not in ("true", True):
        sys.exit(f"FAIL: memorySpace binding should declare solutionsSupport, got {metadata!r}")
    print("OK: bindings_v2.json contains the expected memorySpace binding")


def assert_builder_mentions_feature() -> None:
    if not BUILDER.is_file():
        sys.exit(f"FAIL: Missing {BUILDER}")
    text = BUILDER.read_text()
    for needle in (EXPECTED_FEATURE_NAME, EXPECTED_MEMORY_SPACE, "memorySpace"):
        if needle not in text:
            sys.exit(f"FAIL: .agent-builder/agent.json does not mention {needle!r}")
    print("OK: .agent-builder/agent.json includes the memory feature")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    feature = load(FEATURE)
    bindings = load(BINDINGS)

    input_schema, output_schema = assert_schema_sync(agent, entry)
    assert_input_output_shape(input_schema, output_schema)
    assert_feature(feature)
    assert_dynamic_few_shot(feature)
    assert_seed_item(feature)
    assert_memory_binding(bindings)
    assert_builder_mentions_feature()


if __name__ == "__main__":
    main()
