"""
Case Initialization Script

Implements the case-init-guide.md specification:
  Step 1: Create project directory with 5 scaffolding files
  Step 2: Create case.json with root + default trigger
  Step 3: Add stages (unshift into nodes[], auto-position, Stage_ + 6 random chars)
  Step 4: Add edges (push to edges[], auto-detect type from source node, edge_ + 6 random chars)
"""

import json
import os
import random
import string
import uuid


# ---------------------------------------------------------------------------
# Inputs (hardcoded for this test run)
# ---------------------------------------------------------------------------
PROJECT_NAME = "case_demo5"
CASE_NAME = "case_demo5"
STAGE_LABELS = ["stage_1", "stage_2", "stage_3"]
EDGE_CONNECTIONS = [
    ("trigger_1", "stage_1"),
    ("stage_1", "stage_2"),
    ("stage_2", "stage_3"),
]
OUTPUT_DIR = "/Users/song.zhao/Vscode/skills/uipath-maestro-case-workspace/iteration-7/outputs/case_demo5"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def random_id(prefix: str, length: int = 6) -> str:
    """Generate an ID with the given prefix + random alphanumeric chars."""
    chars = string.ascii_letters + string.digits
    suffix = "".join(random.choice(chars) for _ in range(length))
    return f"{prefix}{suffix}"


def random_uuid() -> str:
    """Generate a random UUID v4 string."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Step 1: Create the Project Directory with 5 scaffolding files
# ---------------------------------------------------------------------------
def create_scaffolding(project_dir: str, project_name: str) -> None:
    os.makedirs(project_dir, exist_ok=True)

    # 1. project.uiproj
    project_uiproj = {
        "Name": project_name,
        "ProjectType": "CaseManagement",
    }
    write_json(os.path.join(project_dir, "project.uiproj"), project_uiproj)

    # 2. operate.json
    operate = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/operate",
        "projectId": random_uuid(),
        "contentType": "CaseManagement",
        "targetFramework": "Portable",
        "runtimeOptions": {
            "requiresUserInteraction": False,
            "isAttended": False,
        },
    }
    write_json(os.path.join(project_dir, "operate.json"), operate)

    # 3. entry-points.json
    entry_points = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
        "$id": "entry-points.json",
        "entryPoints": [
            {
                "filePath": "/content/case.stage.json.bpmn#trigger_1",
                "uniqueId": random_uuid(),
                "type": "CaseManagement",
                "input": {"type": "object", "properties": {}},
                "output": {"type": "object", "properties": {}},
                "displayName": "Trigger 1",
            }
        ],
    }
    write_json(os.path.join(project_dir, "entry-points.json"), entry_points)

    # 4. bindings_v2.json
    bindings = {
        "version": "2.0",
        "resources": [],
    }
    write_json(os.path.join(project_dir, "bindings_v2.json"), bindings)

    # 5. package-descriptor.json
    package_descriptor = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/package-descriptor",
        "files": {
            "operate.json": "content/operate.json",
            "entry-points.json": "content/entry-points.json",
            "bindings.json": "content/bindings_v2.json",
            "case.stage.json": "content/case.stage.json",
            "case.stage.json.bpmn": "content/case.stage.json.bpmn",
        },
    }
    write_json(os.path.join(project_dir, "package-descriptor.json"), package_descriptor)

    print(f"[Step 1] Created project directory with 5 scaffolding files: {project_dir}")


# ---------------------------------------------------------------------------
# Step 2: Create the Case JSON with root + default trigger
# ---------------------------------------------------------------------------
def create_case_json(case_name: str) -> dict:
    case = {
        "root": {
            "id": "root",
            "name": case_name,
            "type": "case-management:root",
            "caseIdentifier": case_name,
            "caseAppEnabled": False,
            "caseIdentifierType": "constant",
            "version": "v12",
            "data": {},
        },
        "nodes": [
            {
                "id": "trigger_1",
                "type": "case-management:Trigger",
                "position": {"x": 0, "y": 0},
                "data": {"label": "Trigger 1"},
            }
        ],
        "edges": [],
    }
    print(f"[Step 2] Created case JSON with root and default trigger for '{case_name}'")
    return case


# ---------------------------------------------------------------------------
# Step 3: Add Stages (unshift into nodes[])
# ---------------------------------------------------------------------------
def add_stages(case: dict, stage_labels: list[str]) -> dict:
    """Add stages to the case. Each stage is unshifted (inserted at index 0)
    of nodes[]. Stage IDs are Stage_ + 6 random alphanumeric chars.
    Auto-positioning: x = 100 + (existingStageCount * 500), y = 200.
    """
    # Build a label -> id mapping so edges can reference stages by label
    label_to_id = {}

    for label in stage_labels:
        # Count existing stage nodes before adding this one
        existing_stage_count = sum(
            1
            for n in case["nodes"]
            if n["type"] in ("case-management:Stage", "case-management:ExceptionStage")
        )

        x = 100 + (existing_stage_count * 500)
        y = 200

        stage_id = random_id("Stage_")
        label_to_id[label] = stage_id

        stage_node = {
            "id": stage_id,
            "type": "case-management:Stage",
            "position": {"x": x, "y": y},
            "style": {"width": 304, "opacity": 0.8},
            "measured": {"width": 304, "height": 128},
            "width": 304,
            "zIndex": 1001,
            "data": {
                "label": label,
                "parentElement": {"id": "root", "type": "case-management:root"},
                "isInvalidDropTarget": False,
                "isPendingParent": False,
                "tasks": [],
            },
        }

        # Unshift: insert at the beginning of nodes[]
        case["nodes"].insert(0, stage_node)
        print(f"[Step 3] Added stage '{label}' (id={stage_id}) at position x={x}, y={y}")

    return case, label_to_id


# ---------------------------------------------------------------------------
# Step 4: Add Edges (push to edges[])
# ---------------------------------------------------------------------------
def add_edges(case: dict, edge_connections: list[tuple[str, str]], label_to_id: dict) -> dict:
    """Add edges to the case. Each edge is pushed (appended) to edges[].
    Edge IDs are edge_ + 6 random alphanumeric chars.
    Edge type is auto-detected from the source node type.
    """
    # Build a quick lookup: node_id -> node_type
    node_type_map = {}
    for node in case["nodes"]:
        node_type_map[node["id"]] = node["type"]

    for source_label, target_label in edge_connections:
        # Resolve labels to IDs.  The trigger has a fixed id "trigger_1",
        # so if the label is "trigger_1" we use it directly.
        source_id = label_to_id.get(source_label, source_label)
        target_id = label_to_id.get(target_label, target_label)

        # Determine edge type based on source node type
        source_type = node_type_map.get(source_id)
        if source_type == "case-management:Trigger":
            edge_type = "case-management:TriggerEdge"
        else:
            edge_type = "case-management:Edge"

        edge_id = random_id("edge_")

        edge_obj = {
            "id": edge_id,
            "type": edge_type,
            "source": source_id,
            "target": target_id,
            "sourceHandle": f"{source_id}____source____right",
            "targetHandle": f"{target_id}____target____left",
            "data": {"label": None},
        }

        # Push: append to edges[]
        case["edges"].append(edge_obj)
        print(
            f"[Step 4] Added edge '{edge_id}' ({source_id} -> {target_id}), type={edge_type}"
        )

    return case


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    project_dir = os.path.join(OUTPUT_DIR, PROJECT_NAME)

    # Step 1: Scaffolding
    create_scaffolding(project_dir, PROJECT_NAME)

    # Step 2: Case JSON
    case = create_case_json(CASE_NAME)

    # Step 3: Add stages
    case, label_to_id = add_stages(case, STAGE_LABELS)

    # Step 4: Add edges
    case = add_edges(case, EDGE_CONNECTIONS, label_to_id)

    # Write final case.json
    case_json_path = os.path.join(project_dir, "case.json")
    write_json(case_json_path, case)
    print(f"\n[Done] Wrote case.json to {case_json_path}")

    # Print summary
    print(f"\nSummary:")
    print(f"  Project dir: {project_dir}")
    print(f"  Scaffolding files: project.uiproj, operate.json, entry-points.json, bindings_v2.json, package-descriptor.json")
    print(f"  case.json nodes: {len(case['nodes'])} ({len(case['nodes']) - 1} stages + 1 trigger)")
    print(f"  case.json edges: {len(case['edges'])}")


if __name__ == "__main__":
    main()
