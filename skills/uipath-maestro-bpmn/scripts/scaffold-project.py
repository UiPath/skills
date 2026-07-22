#!/usr/bin/env python3
"""Create a small local Maestro BPMN project skeleton from a typed contract."""

from __future__ import annotations

import argparse
import json
import re
import uuid
from html import escape
from pathlib import Path


ALLOWED_TYPES = {"string", "integer", "boolean", "number", "array", "object", "json"}
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_variable(raw: str) -> tuple[str, str]:
    name, separator, variable_type = raw.partition(":")
    if not separator or not NAME_RE.fullmatch(name):
        raise argparse.ArgumentTypeError(
            f"variable must use name:type with an identifier name, got {raw!r}"
        )
    if variable_type not in ALLOWED_TYPES:
        allowed = ", ".join(sorted(ALLOWED_TYPES))
        raise argparse.ArgumentTypeError(
            f"unsupported type {variable_type!r}; expected one of {allowed}"
        )
    return name, variable_type


def variable_id(name: str) -> str:
    parts = [part for part in re.split(r"_+", name) if part]
    normalized = "_".join(part[:1].upper() + part[1:] for part in parts)
    return f"Var_{normalized}"


def schema(variables: list[tuple[str, str]]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {name: {"type": variable_type} for name, variable_type in variables},
    }


def variable_lines(
    inputs: list[tuple[str, str]], outputs: list[tuple[str, str]], start_id: str
) -> str:
    lines: list[str] = []
    for name, variable_type in inputs:
        lines.append(
            "        <uipath:inputOutput "
            f'id="{escape(variable_id(name), quote=True)}" '
            f'name="{escape(name, quote=True)}" '
            f'type="{escape(variable_type, quote=True)}" '
            f'elementId="{escape(start_id, quote=True)}" />'
        )
    for name, variable_type in outputs:
        lines.append(
            "        <uipath:inputOutput "
            f'id="{escape(variable_id(name), quote=True)}" '
            f'name="{escape(name, quote=True)}" '
            f'type="{escape(variable_type, quote=True)}" />'
        )
    return "\n".join(lines)


def bpmn_text(
    inputs: list[tuple[str, str]],
    outputs: list[tuple[str, str]],
    start_id: str,
    end_id: str,
    entry_point_id: str,
) -> str:
    variables = variable_lines(inputs, outputs, start_id)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="UiPath (https://bpmn.uipath.com)" exporterVersion="1.0">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:extensionElements>
      <uipath:migrationVersion version="11.5" />
      <uipath:variables version="v1">
{variables}
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="{escape(start_id, quote=True)}" name="Start">
      <bpmn:extensionElements>
        <uipath:entryPointId value="{escape(entry_point_id, quote=True)}" />
      </bpmn:extensionElements>
      <bpmn:outgoing>Flow_Skeleton</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="{escape(end_id, quote=True)}" name="End">
      <bpmn:incoming>Flow_Skeleton</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_Skeleton" sourceRef="{escape(start_id, quote=True)}" targetRef="{escape(end_id, quote=True)}" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="Shape_Start" bpmnElement="{escape(start_id, quote=True)}">
        <dc:Bounds x="160" y="182" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Shape_End" bpmnElement="{escape(end_id, quote=True)}">
        <dc:Bounds x="300" y="182" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Edge_Skeleton" bpmnElement="Flow_Skeleton">
        <di:waypoint x="196" y="200" />
        <di:waypoint x="300" y="200" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
'''


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument(
        "--name",
        help="project name (defaults to the project directory basename)",
    )
    parser.add_argument("--input", action="append", default=[], type=parse_variable)
    parser.add_argument(
        "--output-variable", action="append", default=[], type=parse_variable
    )
    parser.add_argument("--start-id", default="Start_1")
    parser.add_argument("--end-id", default="End_1")
    parser.add_argument("--entry-point-id")
    args = parser.parse_args()

    project_name = args.name or args.project_dir.name
    if not NAME_RE.fullmatch(project_name):
        parser.error("--name must be a filesystem-safe identifier")
    if not args.input:
        parser.error("at least one --input is required")
    if not args.output_variable:
        parser.error("at least one --output-variable is required")

    all_names = [name for name, _ in args.input + args.output_variable]
    if len(all_names) != len(set(all_names)):
        parser.error("input and output variable names must be unique")
    all_ids = [variable_id(name) for name in all_names]
    if len(all_ids) != len(set(all_ids)):
        parser.error("variable names produce duplicate BPMN ids")

    project_dir = args.project_dir.resolve()
    target_names = {
        f"{project_name}.bpmn",
        "project.uiproj",
        "operate.json",
        "entry-points.json",
        "bindings_v2.json",
        "package-descriptor.json",
    }
    existing_targets = sorted(
        path.name for path in project_dir.iterdir() if path.name in target_names
    ) if project_dir.is_dir() else []
    if existing_targets:
        parser.error(
            "refusing to overwrite existing project files: "
            + ", ".join(existing_targets)
        )
    project_dir.mkdir(parents=True, exist_ok=True)
    entry_point_id = args.entry_point_id or str(uuid.uuid4())
    bpmn_name = f"{project_name}.bpmn"

    (project_dir / bpmn_name).write_text(
        bpmn_text(
            args.input,
            args.output_variable,
            args.start_id,
            args.end_id,
            entry_point_id,
        ),
        encoding="utf-8",
    )
    write_json(
        project_dir / "project.uiproj",
        {
            "projectVersion": "1.0.0",
            "ProjectType": "ProcessOrchestration",
            "Name": project_name,
            "main": bpmn_name,
        },
    )
    write_json(
        project_dir / "operate.json",
        {
            "main": bpmn_name,
            "contentType": "ProcessOrchestration",
            "projectId": str(uuid.uuid4()),
        },
    )
    write_json(
        project_dir / "entry-points.json",
        {
            "entryPoints": [
                {
                    "id": entry_point_id,
                    "filePath": f"/content/{bpmn_name}#{args.start_id}",
                    "inputSchema": schema(args.input),
                    "outputSchema": schema(args.output_variable),
                }
            ]
        },
    )
    write_json(project_dir / "bindings_v2.json", {"version": "2.0", "resources": []})
    write_json(
        project_dir / "package-descriptor.json",
        {
            "content": [
                f"content/{bpmn_name}",
                "content/bindings_v2.json",
                "content/entry-points.json",
                "content/operate.json",
            ]
        },
    )

    print(
        json.dumps(
            {
                "projectDir": str(project_dir),
                "bpmn": str(project_dir / bpmn_name),
                "entryPointId": entry_point_id,
                "inputs": len(args.input),
                "outputs": len(args.output_variable),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
