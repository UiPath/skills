#!/usr/bin/env python3
"""Inline low-code agent memory-space feature check.

Validates:
  1. The flow has a uipath.agent.autonomous node whose inputs.source
     points to an inline-agent subdirectory.
  2. The inline agent has features/SupportRecall/feature.json, not a
     memory feature modeled as resources/**/resource.json.
  3. The feature declares the expected memory space, folder path, and
     dynamic few-shot settings.
  4. The parent flow project's bindings_v2.json contains the generated
     memorySpace binding, proving migrate ran with --bindings-target.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.inline_wiring import (  # noqa: E402
    find_autonomous_agent_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "MemoryFlowSol" / "MemoryFlow" / "MemoryFlow.flow"
FLOW_BINDINGS = Path(os.getcwd()) / "MemoryFlowSol" / "MemoryFlow" / "bindings_v2.json"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

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


def assert_inline_agent_dir(flow: dict) -> Path:
    node = find_autonomous_agent_node(flow)
    source = (node.get("inputs") or {}).get("source")
    if not isinstance(source, str) or not UUID_RE.match(source):
        sys.exit(
            f"FAIL: uipath.agent.autonomous inputs.source must be an inline agent UUID, got {source!r}"
        )
    agent_dir = resolve_inline_agent_dir(FLOW_PATH, node)
    if agent_dir.name != source:
        sys.exit(
            f"FAIL: autonomous node source {source!r} does not match inline agent dir {agent_dir.name!r}"
        )
    print(f"OK: autonomous agent node points to inline agent directory {agent_dir.name}")
    return agent_dir


def assert_no_memory_resource(agent_dir: Path) -> None:
    resources_dir = agent_dir / "resources"
    if not resources_dir.exists():
        print("OK: inline agent has no resources/ directory for memory")
        return
    memory_resources = []
    for path in resources_dir.rglob("resource.json"):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("$featureType") == "memorySpace" or data.get("$resourceType") == "memorySpace":
            memory_resources.append(path)
    if memory_resources:
        rels = [str(p.relative_to(Path(os.getcwd()))) for p in memory_resources]
        sys.exit(
            "FAIL: memory spaces must be feature files under features/, not resources/: "
            + ", ".join(rels)
        )
    print("OK: no memory space was modeled as a resource.json file")


def assert_feature(agent_dir: Path) -> None:
    feature_path = agent_dir / "features" / EXPECTED_FEATURE_NAME / "feature.json"
    feature = load(feature_path)
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
    if not isinstance(fields, list) or not any(
        isinstance(f, dict)
        and f.get("name") == "userQuestion"
        and isinstance(f.get("weight"), (int, float))
        and abs(float(f["weight"]) - 1.0) < 1e-9
        for f in fields
    ):
        sys.exit(f"FAIL: fieldSettings must contain userQuestion weight 1, got {fields!r}")
    print(
        f"OK: inline memory feature {EXPECTED_FEATURE_NAME!r} attaches "
        f"{EXPECTED_MEMORY_SPACE!r} in {EXPECTED_FOLDER_PATH!r}"
    )


def assert_parent_memory_binding(bindings: dict) -> None:
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        sys.exit(f"FAIL: parent bindings_v2.json resources must be a list, got {resources!r}")
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
            "FAIL: expected exactly one parent memorySpace binding for "
            f"{EXPECTED_MEMORY_SPACE!r} in {EXPECTED_FOLDER_PATH!r}; got {len(matches)}. "
            "Run uip agent migrate --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json."
        )
    print("OK: parent flow bindings_v2.json contains the propagated memorySpace binding")


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_dir = assert_inline_agent_dir(flow)
    assert_no_memory_resource(agent_dir)
    assert_feature(agent_dir)
    assert_parent_memory_binding(load(FLOW_BINDINGS))


if __name__ == "__main__":
    main()
