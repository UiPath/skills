"""
Initialize a UiPath Maestro case project with 100 stages and 100 edges.

Project: case_100stages
Case: case_100stages
Stages: stage_1 through stage_100
Edges: trigger_1 -> stage_1, stage_1 -> stage_2, ..., stage_99 -> stage_100
"""

import json
import os
import random
import string
import uuid
import sys


def random_alphanum(length=6):
    """Generate a random alphanumeric string of given length (A-Z, a-z, 0-9)."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def random_uuid():
    """Generate a random UUID v4 string."""
    return str(uuid.uuid4())


def create_scaffolding_files(project_dir, project_name):
    """Step 1: Create the 5 scaffolding files in the project directory."""

    # project.uiproj
    project_uiproj = {
        "Name": project_name,
        "ProjectType": "CaseManagement"
    }
    with open(os.path.join(project_dir, "project.uiproj"), "w") as f:
        json.dump(project_uiproj, f, indent=2)

    # operate.json
    operate = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/operate",
        "projectId": random_uuid(),
        "contentType": "CaseManagement",
        "targetFramework": "Portable",
        "runtimeOptions": {
            "requiresUserInteraction": False,
            "isAttended": False
        }
    }
    with open(os.path.join(project_dir, "operate.json"), "w") as f:
        json.dump(operate, f, indent=2)

    # entry-points.json
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
                "displayName": "Trigger 1"
            }
        ]
    }
    with open(os.path.join(project_dir, "entry-points.json"), "w") as f:
        json.dump(entry_points, f, indent=2)

    # bindings_v2.json
    bindings = {
        "version": "2.0",
        "resources": []
    }
    with open(os.path.join(project_dir, "bindings_v2.json"), "w") as f:
        json.dump(bindings, f, indent=2)

    # package-descriptor.json
    package_descriptor = {
        "$schema": "https://cloud.uipath.com/draft/2024-12/package-descriptor",
        "files": {
            "operate.json": "content/operate.json",
            "entry-points.json": "content/entry-points.json",
            "bindings.json": "content/bindings_v2.json",
            "case.stage.json": "content/case.stage.json",
            "case.stage.json.bpmn": "content/case.stage.json.bpmn"
        }
    }
    with open(os.path.join(project_dir, "package-descriptor.json"), "w") as f:
        json.dump(package_descriptor, f, indent=2)

    print("Created 5 scaffolding files.")


def create_case_json(project_dir, case_name, stages_config, edges_config):
    """
    Steps 2-4: Create case.json with root, trigger, stages, and edges.

    stages_config: list of dicts with 'label' and optional 'type' (default 'stage')
    edges_config: list of dicts with 'source' (label or 'trigger_1') and 'target' (label)
    """

    # Step 2: Initialize case.json with root and default trigger
    case_data = {
        "root": {
            "id": "root",
            "name": case_name,
            "type": "case-management:root",
            "caseIdentifier": case_name,
            "caseAppEnabled": False,
            "caseIdentifierType": "constant",
            "version": "v12",
            "data": {}
        },
        "nodes": [
            {
                "id": "trigger_1",
                "type": "case-management:Trigger",
                "position": {"x": 0, "y": 0},
                "data": {
                    "label": "Trigger 1"
                }
            }
        ],
        "edges": []
    }

    # Step 3: Add stages (unshift into nodes[])
    # Build a mapping from stage label -> generated stage ID
    label_to_id = {}
    # Also keep trigger_1 in the mapping for edge lookup
    label_to_id["trigger_1"] = "trigger_1"

    for i, stage in enumerate(stages_config):
        label = stage["label"]
        stage_type = stage.get("type", "stage")
        stage_id = "Stage_" + random_alphanum(6)
        label_to_id[label] = stage_id

        # Count existing stage nodes before adding this one
        existing_stage_count = sum(
            1 for n in case_data["nodes"]
            if n["type"] in ("case-management:Stage", "case-management:ExceptionStage")
        )

        x = 100 + (existing_stage_count * 500)
        y = 200

        if stage_type == "exception":
            node = {
                "id": stage_id,
                "type": "case-management:ExceptionStage",
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
                    "entryConditions": [],
                    "exitConditions": []
                }
            }
        else:
            node = {
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
                    "tasks": []
                }
            }

        # Unshift: insert at beginning of nodes[]
        case_data["nodes"].insert(0, node)

    print(f"Added {len(stages_config)} stages to nodes[].")

    # Step 4: Add edges (push to edges[])
    # Build a lookup from node ID -> node type for edge type detection
    node_type_lookup = {}
    for node in case_data["nodes"]:
        node_type_lookup[node["id"]] = node["type"]

    for edge_def in edges_config:
        source_label = edge_def["source"]
        target_label = edge_def["target"]

        source_id = label_to_id[source_label]
        target_id = label_to_id[target_label]

        edge_id = "edge_" + random_alphanum(6)

        # Detect edge type based on source node type
        source_node_type = node_type_lookup[source_id]
        if source_node_type == "case-management:Trigger":
            edge_type = "case-management:TriggerEdge"
        else:
            edge_type = "case-management:Edge"

        edge = {
            "id": edge_id,
            "type": edge_type,
            "source": source_id,
            "target": target_id,
            "sourceHandle": f"{source_id}____source____right",
            "targetHandle": f"{target_id}____target____left",
            "data": {"label": None}
        }

        # Push to edges[]
        case_data["edges"].append(edge)

    print(f"Added {len(edges_config)} edges to edges[].")

    # Write case.json
    case_json_path = os.path.join(project_dir, "case.json")
    with open(case_json_path, "w") as f:
        json.dump(case_data, f, indent=2)

    print(f"Wrote case.json to {case_json_path}")

    return case_data


def main():
    project_name = "case_100stages"
    case_name = "case_100stages"
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    project_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)

    # Step 1: Create scaffolding files
    create_scaffolding_files(project_dir, project_name)

    # Define 100 stages: stage_1 through stage_100
    stages_config = [{"label": f"stage_{i}", "type": "stage"} for i in range(1, 101)]

    # Define 100 edges:
    # 1 trigger edge: trigger_1 -> stage_1
    # 99 stage-to-stage edges: stage_1 -> stage_2, ..., stage_99 -> stage_100
    edges_config = [{"source": "trigger_1", "target": "stage_1"}]
    for i in range(1, 100):
        edges_config.append({"source": f"stage_{i}", "target": f"stage_{i + 1}"})

    # Steps 2-4: Create case.json
    case_data = create_case_json(project_dir, case_name, stages_config, edges_config)

    # Print summary
    print(f"\nProject created at: {project_dir}")
    print(f"  Nodes: {len(case_data['nodes'])} (1 trigger + {len(case_data['nodes']) - 1} stages)")
    print(f"  Edges: {len(case_data['edges'])} (1 TriggerEdge + {len(case_data['edges']) - 1} Edges)")


if __name__ == "__main__":
    main()
