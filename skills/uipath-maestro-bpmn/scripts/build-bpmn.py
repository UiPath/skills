#!/usr/bin/env python3
"""Render a complete UiPath Maestro BPMN project from a declarative JSON graph.

The renderer owns structural boilerplate only: BPMN elements, incoming/outgoing
references, sequence flows, loop markers, diagram interchange, and local
project metadata. Callers remain responsible for the process design and for
supplying mapping fields derived from live registry templates.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"
DC = "http://www.omg.org/spec/DD/20100524/DC"
DI = "http://www.omg.org/spec/DD/20100524/DI"
UIPATH = "http://uipath.org/schema/bpmn"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

NS = {
    "bpmn": BPMN,
    "bpmndi": BPMNDI,
    "dc": DC,
    "di": DI,
    "uipath": UIPATH,
    "xsi": XSI,
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def expand_attr(name: str) -> str:
    if ":" not in name:
        return name
    prefix, local = name.split(":", 1)
    if prefix not in NS:
        raise ValueError(f"unknown attribute namespace prefix: {prefix}")
    return q(prefix, local)


def stringify(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def attrs(values: dict[str, object] | None) -> dict[str, str]:
    return {
        expand_attr(key): stringify(value)
        for key, value in (values or {}).items()
        if value is not None
    }


def add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = ET.SubElement(parent, tag)
    child.text = text
    return child


def extension_elements(node: ET.Element) -> ET.Element:
    """Return the node's single BPMN extensionElements container."""
    extension = node.find(q("bpmn", "extensionElements"))
    if extension is None:
        extension = ET.Element(q("bpmn", "extensionElements"))
        node.insert(0, extension)
    return extension


def body_text(body: object) -> str:
    if isinstance(body, (dict, list)):
        return json.dumps(body, separators=(",", ":"))
    return stringify(body)


def add_mapping(
    node: ET.Element,
    mapping: dict[str, object] | None,
    *,
    script_version: str | None = None,
) -> None:
    if not mapping and not script_version:
        return
    extension = extension_elements(node)
    if mapping:
        mapping_el = ET.SubElement(
            extension,
            q("uipath", "mapping"),
            {"version": stringify(mapping.get("mappingVersion", "v1"))},
        )
        ET.SubElement(
            mapping_el,
            q("uipath", "type"),
            {
                "value": stringify(mapping["serviceType"]),
                "version": stringify(mapping.get("version", "v1")),
            },
        )
        context_fields = mapping.get("context", [])
        if context_fields:
            context_el = ET.SubElement(mapping_el, q("uipath", "context"))
            for field in context_fields:
                field = dict(field)
                name = stringify(field.pop("name"))
                body = field.pop("body", None)
                child = ET.SubElement(
                    context_el,
                    q("uipath", name),
                    attrs(field),
                )
                if body is not None:
                    child.text = body_text(body)
        for group, local in (
            ("inputs", "input"),
            ("outputs", "output"),
        ):
            for field in mapping.get(group, []):
                field = dict(field)
                body = field.pop("body", None)
                if group == "outputs" and "source" in field:
                    source = field["source"]
                    output_type = stringify(field.get("type", ""))
                    if not isinstance(source, str):
                        raise ValueError(
                            "mapping output source must be a string; use a "
                            "typed expression such as '=true' or '=42' for "
                            "non-string constants"
                        )
                    if (
                        output_type
                        in {"boolean", "integer", "number", "array", "object"}
                        and not source.startswith("=")
                    ):
                        raise ValueError(
                            f"mapping output {field.get('name')!r} has type "
                            f"{output_type!r}, so its source must be a typed "
                            "'=' expression rather than a string literal"
                        )
                child = ET.SubElement(
                    mapping_el,
                    q("uipath", local),
                    attrs(field),
                )
                if body is not None:
                    # The engine parser accepts CDATA or a value attribute.
                    # ElementTree cannot preserve CDATA, so use the equivalent
                    # parser-supported attribute. Ordinary XML text is ignored.
                    child.set("value", body_text(body))
    if script_version:
        ET.SubElement(
            extension,
            q("uipath", "scriptVersion"),
            {"value": script_version},
        )


def add_variables(
    process: ET.Element,
    variables: list[dict[str, object]],
    *,
    migration_version: str | None = None,
) -> None:
    if not variables:
        return
    extension = extension_elements(process)
    if migration_version is not None:
        ET.SubElement(
            extension,
            q("uipath", "migrationVersion"),
            {"version": migration_version},
        )
    variables_el = ET.SubElement(
        extension, q("uipath", "variables"), {"version": "v1"}
    )
    direction_tags = {
        "input": "input",
        "output": "output",
        "inputOutput": "inputOutput",
        "input/output": "inputOutput",
        "internal": "inputOutput",
    }
    for variable in variables:
        data = dict(variable)
        direction = stringify(data.pop("direction"))
        if direction not in direction_tags:
            raise ValueError(f"unsupported variable direction: {direction}")
        schema = data.pop("schema", None)
        variable_el = ET.SubElement(
            variables_el,
            q("uipath", direction_tags[direction]),
            attrs(data),
        )
        if schema is not None:
            variable_el.text = json.dumps(schema, separators=(",", ":"))


def index_scope(
    scope: dict[str, object],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    incoming: dict[str, list[str]] = {}
    outgoing: dict[str, list[str]] = {}
    for flow in scope.get("flows", []):
        flow_id = stringify(flow["id"])
        source = stringify(flow["source"])
        target = stringify(flow["target"])
        outgoing.setdefault(source, []).append(flow_id)
        incoming.setdefault(target, []).append(flow_id)
    return incoming, outgoing


def node_tag(kind: str) -> str:
    supported = {
        "startEvent",
        "endEvent",
        "task",
        "scriptTask",
        "subProcess",
        "exclusiveGateway",
        "parallelGateway",
        "boundaryEvent",
        "intermediateThrowEvent",
        "intermediateCatchEvent",
        "callActivity",
        "serviceTask",
        "userTask",
    }
    if kind not in supported:
        raise ValueError(f"unsupported BPMN node kind: {kind}")
    return q("bpmn", kind)


def add_loop(node: ET.Element, loop: dict[str, object] | None) -> None:
    if not loop:
        return
    item = loop.get("item")
    if node.tag == q("bpmn", "subProcess"):
        if item != "iterator[0]":
            raise ValueError(
                "multi-instance subprocess loops require "
                "item='iterator[0]'"
            )
    elif item is not None:
        raise ValueError(
            "task-level multi-instance loops must omit item; "
            "use iterator.item inside the activity"
        )
    loop_el = ET.SubElement(
        node,
        q("bpmn", "multiInstanceLoopCharacteristics"),
        {"isSequential": stringify(loop.get("sequential", False))},
    )
    if loop.get("completionCondition") is not None:
        condition = ET.SubElement(
            loop_el,
            q("bpmn", "completionCondition"),
            {q("xsi", "type"): "bpmn:tFormalExpression"},
        )
        condition.text = stringify(loop["completionCondition"])
    extension = ET.SubElement(loop_el, q("bpmn", "extensionElements"))
    loop_attrs = {
        "inputCollection": stringify(loop["collection"]),
        "version": stringify(loop.get("version", "v1")),
    }
    if item is not None:
        loop_attrs["inputElement"] = stringify(item)
    ET.SubElement(
        extension,
        q("uipath", "loopCharacteristics"),
        loop_attrs,
    )


def add_event_definition(node: ET.Element, spec: dict[str, object]) -> None:
    error_ref = spec.get("errorRef")
    if error_ref is not None:
        ET.SubElement(
            node,
            q("bpmn", "errorEventDefinition"),
            {"errorRef": stringify(error_ref)},
        )
    terminate = spec.get("terminate")
    if terminate:
        ET.SubElement(node, q("bpmn", "terminateEventDefinition"))


def add_node(
    parent: ET.Element,
    spec: dict[str, object],
    incoming: dict[str, list[str]],
    outgoing: dict[str, list[str]],
    variable_ids: dict[str, str],
) -> None:
    kind = stringify(spec["kind"])
    node_id = stringify(spec["id"])
    node_attrs = {"id": node_id}
    if spec.get("name") is not None:
        node_attrs["name"] = stringify(spec["name"])
    node_attrs.update(attrs(spec.get("attrs")))
    if kind == "boundaryEvent":
        node_attrs["attachedToRef"] = stringify(spec["attachedTo"])
        node_attrs["cancelActivity"] = stringify(spec.get("cancelActivity", True))
    if spec.get("default") is not None:
        node_attrs["default"] = stringify(spec["default"])
    if kind == "scriptTask":
        node_attrs["scriptFormat"] = stringify(spec.get("scriptFormat", "JavaScript"))

    node = ET.SubElement(parent, node_tag(kind), node_attrs)

    mapping = spec.get("mapping")
    if mapping:
        mapping = json.loads(json.dumps(mapping))
        for field in mapping.get("outputs", []):
            target = field.get("var")
            if target in variable_ids:
                field["var"] = variable_ids[target]
    add_mapping(
        node,
        mapping,
        script_version=(
            stringify(spec.get("scriptVersion", "v3"))
            if kind == "scriptTask"
            else None
        ),
    )
    if spec.get("entryPointId") is not None:
        extension = extension_elements(node)
        ET.SubElement(
            extension,
            q("uipath", "entryPointId"),
            {"value": stringify(spec["entryPointId"])},
        )

    for flow_id in incoming.get(node_id, []):
        add_text(node, q("bpmn", "incoming"), flow_id)
    for flow_id in outgoing.get(node_id, []):
        add_text(node, q("bpmn", "outgoing"), flow_id)

    add_loop(node, spec.get("loop"))

    if kind == "scriptTask":
        add_text(node, q("bpmn", "script"), stringify(spec.get("script", "")))

    add_event_definition(node, spec)

    if kind == "subProcess":
        internal = {
            "nodes": spec.get("nodes", []),
            "flows": spec.get("flows", []),
        }
        add_scope(node, internal, variable_ids)


def add_flow(parent: ET.Element, spec: dict[str, object]) -> None:
    flow = ET.SubElement(
        parent,
        q("bpmn", "sequenceFlow"),
        {
            "id": stringify(spec["id"]),
            "sourceRef": stringify(spec["source"]),
            "targetRef": stringify(spec["target"]),
        },
    )
    if spec.get("name") is not None:
        flow.set("name", stringify(spec["name"]))
    if spec.get("condition") is not None:
        condition = ET.SubElement(
            flow,
            q("bpmn", "conditionExpression"),
            {q("xsi", "type"): "bpmn:tFormalExpression"},
        )
        condition.text = stringify(spec["condition"])


def add_scope(
    parent: ET.Element,
    scope: dict[str, object],
    variable_ids: dict[str, str],
) -> None:
    incoming, outgoing = index_scope(scope)
    for spec in scope.get("nodes", []):
        add_node(parent, spec, incoming, outgoing, variable_ids)
    for spec in scope.get("flows", []):
        add_flow(parent, spec)


def collect_nodes(scope: dict[str, object]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for node in scope.get("nodes", []):
        result.append(node)
        if node.get("kind") == "subProcess":
            result.extend(
                collect_nodes(
                    {
                        "nodes": node.get("nodes", []),
                        "flows": node.get("flows", []),
                    }
                )
            )
    return result


def collect_flows(scope: dict[str, object]) -> list[dict[str, object]]:
    result = list(scope.get("flows", []))
    for node in scope.get("nodes", []):
        if node.get("kind") == "subProcess":
            result.extend(
                collect_flows(
                    {
                        "nodes": node.get("nodes", []),
                        "flows": node.get("flows", []),
                    }
                )
            )
    return result


def collect_node_owners(
    scope: dict[str, object],
    owner: str | None = None,
) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for node in scope.get("nodes", []):
        node_id = stringify(node["id"])
        result[node_id] = owner
        if node.get("kind") == "subProcess":
            result.update(
                collect_node_owners(
                    {
                        "nodes": node.get("nodes", []),
                        "flows": node.get("flows", []),
                    },
                    node_id,
                )
            )
    return result


def reachable(
    source: str,
    target: str,
    outgoing: dict[str, list[str]],
    flows_by_id: dict[str, dict[str, object]],
) -> bool:
    pending = [source]
    seen: set[str] = set()
    while pending:
        node_id = pending.pop()
        if node_id == target:
            return True
        if node_id in seen:
            continue
        seen.add(node_id)
        for flow_id in outgoing.get(node_id, []):
            pending.append(stringify(flows_by_id[flow_id]["target"]))
    return False


def validate_stable_variable_references(
    process: dict[str, object],
) -> None:
    """Reject runtime expressions that use variable names instead of ids."""
    serialized = json.dumps(process)
    for variable in process.get("variables", []):
        name = stringify(variable["name"])
        variable_id = stringify(variable["id"])
        if name == variable_id:
            continue
        pattern = rf"vars\.{re.escape(name)}(?![A-Za-z0-9_])"
        if re.search(pattern, serialized):
            raise ValueError(
                f"runtime expression references declared variable name "
                f"'vars.{name}'; use its stable id 'vars.{variable_id}'"
            )


def validate_script_error_bindings(
    scripts_by_id: dict[str, dict[str, object]],
    variables: list[dict[str, object]],
) -> None:
    """Require the current activity-scoped Error contract on every script."""
    variables_by_id = {
        stringify(variable["id"]): variable for variable in variables
    }
    variables_by_name: dict[str, list[dict[str, object]]] = {}
    for variable in variables:
        variables_by_name.setdefault(
            stringify(variable["name"]), []
        ).append(variable)

    for script_id, script in scripts_by_id.items():
        outputs = script.get("mapping", {}).get("outputs", [])
        error_outputs = [
            output for output in outputs if output.get("name") == "Error"
        ]
        if len(error_outputs) != 1:
            raise ValueError(
                f"ScriptTask {script_id} needs exactly one Error output"
            )
        error_output = error_outputs[0]
        if (
            error_output.get("type") != "jsonSchema"
            or error_output.get("source") != "=Error"
        ):
            raise ValueError(
                f"ScriptTask {script_id} Error output needs "
                "type='jsonSchema' and source='=Error'"
            )
        variable_ref = stringify(error_output.get("var", ""))
        variable = variables_by_id.get(variable_ref)
        if variable is None:
            candidates = variables_by_name.get(variable_ref, [])
            if len(candidates) != 1:
                raise ValueError(
                    f"ScriptTask {script_id} Error output must map an "
                    "unambiguous declared variable id"
                )
            variable = candidates[0]
        if (
            variable.get("name") != "Error"
            or variable.get("type") != "jsonSchema"
            or variable.get("elementId") != script_id
        ):
            raise ValueError(
                f"ScriptTask {script_id} Error output needs a variable with "
                "name='Error', type='jsonSchema', and matching elementId"
            )


def validate_script_runtime_contracts(
    scripts_by_id: dict[str, dict[str, object]],
    variables: list[dict[str, object]],
) -> None:
    """Require the canonical v3 response/Error outputs on every script."""
    validate_script_error_bindings(scripts_by_id, variables)
    variable_ids = {
        stringify(variable["id"]) for variable in variables
    }
    variable_names: dict[str, list[str]] = {}
    for variable in variables:
        variable_names.setdefault(
            stringify(variable["name"]), []
        ).append(stringify(variable["id"]))

    for script_id, script in scripts_by_id.items():
        if stringify(script.get("scriptVersion", "v3")) != "v3":
            raise ValueError(
                f"ScriptTask {script_id} must use scriptVersion='v3'"
            )
        mapping = script.get("mapping", {})
        if mapping.get("serviceType") != "BPMN.Variables":
            raise ValueError(
                f"ScriptTask {script_id} must use a BPMN.Variables mapping"
            )
        response_outputs = [
            output
            for output in mapping.get("outputs", [])
            if output.get("name") == "scriptResponse"
        ]
        if len(response_outputs) != 1:
            raise ValueError(
                f"ScriptTask {script_id} needs exactly one "
                "scriptResponse output"
            )
        response = response_outputs[0]
        if (
            response.get("source") != "=result.response"
            or not stringify(response.get("type", ""))
        ):
            raise ValueError(
                f"ScriptTask {script_id} scriptResponse output needs a "
                "non-empty type and source='=result.response'"
            )
        variable_ref = stringify(response.get("var", ""))
        resolved = (
            variable_ref
            if variable_ref in variable_ids
            else (
                variable_names.get(variable_ref, [""])[0]
                if len(variable_names.get(variable_ref, [])) == 1
                else ""
            )
        )
        if not resolved:
            raise ValueError(
                f"ScriptTask {script_id} scriptResponse output must map an "
                "unambiguous declared variable id"
            )


def script_references_stable_variable(
    script: dict[str, object],
    variable_id: str,
) -> bool:
    reference = f"vars.{variable_id}"
    serialized_inputs = json.dumps(
        script.get("mapping", {}).get("inputs", [])
    )
    script_body = stringify(script.get("script", ""))
    return reference in serialized_inputs or reference in script_body


def validate_diverging_exclusive_gateways(
    nodes: list[dict[str, object]],
    flows: list[dict[str, object]],
) -> None:
    """Require a complete, explicit default/guard contract for every XOR split."""
    outgoing: dict[str, list[dict[str, object]]] = {}
    for flow in flows:
        outgoing.setdefault(stringify(flow["source"]), []).append(flow)

    for gateway in [
        node for node in nodes if node.get("kind") == "exclusiveGateway"
    ]:
        gateway_id = stringify(gateway["id"])
        gateway_flows = outgoing.get(gateway_id, [])
        if len(gateway_flows) < 2:
            continue
        default_id = stringify(gateway.get("default", ""))
        flow_ids = {
            stringify(flow["id"])
            for flow in gateway_flows
        }
        if not default_id:
            raise ValueError(
                f"diverging exclusive gateway {gateway_id} needs an "
                "explicit default flow"
            )
        if default_id not in flow_ids:
            raise ValueError(
                f"exclusive gateway {gateway_id} default {default_id} "
                "must identify one of its outgoing flows"
            )
        for flow in gateway_flows:
            flow_id = stringify(flow["id"])
            condition = stringify(flow.get("condition", "")).strip()
            if flow_id == default_id and condition:
                raise ValueError(
                    f"exclusive gateway {gateway_id} default flow "
                    f"{flow_id} must not have a condition"
                )
            if flow_id != default_id and not condition:
                raise ValueError(
                    f"exclusive gateway {gateway_id} non-default flow "
                    f"{flow_id} needs a condition"
                )


def validate_scope_execution_paths(
    scope: dict[str, object],
    scope_id: str = "process",
) -> None:
    """Reject disconnected execution graphs before rendering deployable BPMN."""
    nodes = scope.get("nodes", [])
    flows = scope.get("flows", [])
    nodes_by_id = {
        stringify(node["id"]): node
        for node in nodes
    }
    outgoing: dict[str, list[str]] = {}
    for flow in flows:
        flow_id = stringify(flow["id"])
        source = stringify(flow["source"])
        target = stringify(flow["target"])
        if source not in nodes_by_id or target not in nodes_by_id:
            raise ValueError(
                f"scope {scope_id} flow {flow_id} must connect nodes in "
                "that same scope"
            )
        outgoing.setdefault(source, []).append(target)

    start_ids = {
        node_id
        for node_id, node in nodes_by_id.items()
        if node.get("kind") == "startEvent"
    }
    for start_id in sorted(start_ids):
        outgoing_count = len(outgoing.get(start_id, []))
        if outgoing_count != 1:
            raise ValueError(
                f"start event {start_id} in scope {scope_id} needs exactly "
                f"one outgoing flow; found {outgoing_count}"
            )

    entry_ids = start_ids | {
        node_id
        for node_id, node in nodes_by_id.items()
        if node.get("kind") == "boundaryEvent"
        or (
            node.get("kind") == "subProcess"
            and bool(node.get("triggeredByEvent", False))
        )
    }
    pending = list(entry_ids)
    reachable_ids: set[str] = set()
    while pending:
        node_id = pending.pop()
        if node_id in reachable_ids:
            continue
        reachable_ids.add(node_id)
        pending.extend(outgoing.get(node_id, []))

    unreachable_ids = sorted(set(nodes_by_id) - reachable_ids)
    if unreachable_ids:
        raise ValueError(
            f"scope {scope_id} has nodes unreachable from a start, boundary, "
            f"or event-subprocess entry: {unreachable_ids}"
        )

    for node_id, node in nodes_by_id.items():
        if node.get("kind") != "subProcess":
            continue
        validate_scope_execution_paths(
            {
                "nodes": node.get("nodes", []),
                "flows": node.get("flows", []),
            },
            node_id,
        )


def validate_constraints(spec: dict[str, object]) -> None:
    constraints = spec.get("constraints")
    if not isinstance(constraints, dict):
        raise ValueError(
            "spec must declare constraints for publicInputs, publicOutputs, "
            "scriptTasks, errorEnds, and decisionPhases"
        )
    process = spec["process"]
    variables = process.get("variables", [])
    validate_stable_variable_references(process)
    public_inputs = {
        stringify(variable["name"])
        for variable in variables
        if variable["direction"] in {"input", "inputOutput", "input/output"}
    }
    public_outputs = {
        stringify(variable["name"])
        for variable in variables
        if variable["direction"] in {"output", "inputOutput", "input/output"}
    }
    expected_inputs = set(constraints.get("publicInputs", []))
    expected_outputs = set(constraints.get("publicOutputs", []))
    if public_inputs != expected_inputs:
        raise ValueError(
            f"public input contract mismatch: expected {sorted(expected_inputs)}, "
            f"found {sorted(public_inputs)}"
        )
    if public_outputs != expected_outputs:
        raise ValueError(
            f"public output contract mismatch: expected {sorted(expected_outputs)}, "
            f"found {sorted(public_outputs)}"
        )
    internal_variables = {
        stringify(variable["name"])
        for variable in variables
        if variable["direction"] == "internal"
    }
    expected_internal = set(constraints.get("internalVariables", []))
    if internal_variables != expected_internal:
        raise ValueError(
            f"internal variable contract mismatch: expected "
            f"{sorted(expected_internal)}, found {sorted(internal_variables)}"
        )

    scope = {
        "nodes": process.get("nodes", []),
        "flows": process.get("flows", []),
    }
    validate_scope_execution_paths(scope)
    nodes = collect_nodes(scope)
    flows = collect_flows(scope)
    validate_diverging_exclusive_gateways(nodes, flows)
    nodes_by_id = {stringify(node["id"]): node for node in nodes}
    owners_by_id = collect_node_owners(scope)
    script_ids = {
        stringify(node["id"])
        for node in nodes
        if node.get("kind") == "scriptTask"
    }
    script_constraint = constraints.get("scriptTasks", {})
    exact = script_constraint.get("exact")
    if exact is None:
        raise ValueError("constraints.scriptTasks.exact is required")
    if len(script_ids) != int(exact):
        raise ValueError(
            f"ScriptTask count mismatch: expected {exact}, found "
            f"{len(script_ids)} ({sorted(script_ids)})"
        )
    allowed_ids = script_constraint.get("allowedIds")
    if allowed_ids is not None and script_ids != set(allowed_ids):
        raise ValueError(
            f"ScriptTask ids mismatch: expected {sorted(allowed_ids)}, "
            f"found {sorted(script_ids)}"
        )
    scripts_by_id = {
        stringify(node["id"]): node
        for node in nodes
        if node.get("kind") == "scriptTask"
    }
    validate_script_runtime_contracts(scripts_by_id, variables)
    outputs_by_id = script_constraint.get("allowedOutputsById", {})
    refs_by_id = script_constraint.get("requiredInputReferencesById", {})
    if set(outputs_by_id) != script_ids:
        raise ValueError(
            "constraints.scriptTasks.allowedOutputsById must declare every "
            "ScriptTask id exactly once"
        )
    if set(refs_by_id) != script_ids:
        raise ValueError(
            "constraints.scriptTasks.requiredInputReferencesById must declare "
            "every ScriptTask id exactly once"
        )
    variable_ids = {
        stringify(variable["name"]): stringify(variable["id"])
        for variable in variables
    }
    for script_id, script in scripts_by_id.items():
        mapping = script.get("mapping", {})
        output_names = {
            stringify(field["name"])
            for field in mapping.get("outputs", [])
        }
        expected_names = set(outputs_by_id[script_id])
        if output_names != expected_names:
            raise ValueError(
                f"ScriptTask {script_id} outputs mismatch: expected "
                f"{sorted(expected_names)}, found {sorted(output_names)}"
            )
        for reference in refs_by_id[script_id]:
            variable_id = variable_ids.get(reference, reference)
            if not script_references_stable_variable(script, variable_id):
                raise ValueError(
                    f"ScriptTask {script_id} does not reference "
                    f"required variable {reference!r} by stable id "
                    f"'vars.{variable_id}'"
                )

    error_constraint = constraints.get("errorEnds", {})
    if error_constraint.get("singleGuardedIncoming") is not True:
        raise ValueError(
            "constraints.errorEnds.singleGuardedIncoming must be true"
        )
    incoming: dict[str, list[dict[str, object]]] = {}
    for flow in flows:
        incoming.setdefault(stringify(flow["target"]), []).append(flow)
    error_ends = [
        node
        for node in nodes
        if node.get("kind") == "endEvent" and node.get("errorRef")
    ]
    actual_error_end_ids = {
        stringify(node["id"])
        for node in error_ends
    }
    allowed_error_end_ids = error_constraint.get("allowedIds")
    if allowed_error_end_ids is None:
        raise ValueError("constraints.errorEnds.allowedIds is required")
    if actual_error_end_ids != set(allowed_error_end_ids):
        raise ValueError(
            "error-end ids mismatch: expected "
            f"{sorted(allowed_error_end_ids)}, found "
            f"{sorted(actual_error_end_ids)}"
        )
    if error_constraint.get("forbidUntypedBoundaries") is not True:
        raise ValueError(
            "constraints.errorEnds.forbidUntypedBoundaries must be true"
        )
    for boundary in [
        node for node in nodes if node.get("kind") == "boundaryEvent"
    ]:
        if not boundary.get("errorRef"):
            raise ValueError(
                f"boundary event {boundary['id']} must declare an errorRef"
            )

    matching_boundaries = error_constraint.get("matchingBoundaryById")
    if not isinstance(matching_boundaries, dict):
        raise ValueError(
            "constraints.errorEnds.matchingBoundaryById is required"
        )
    if set(matching_boundaries) != actual_error_end_ids:
        raise ValueError(
            "constraints.errorEnds.matchingBoundaryById must declare every "
            "error end exactly once"
        )
    for node in error_ends:
        node_id = stringify(node["id"])
        error_incoming = incoming.get(stringify(node["id"]), [])
        if len(error_incoming) != 1 or not error_incoming[0].get("condition"):
            raise ValueError(
                f"error end {node['id']} must have exactly one conditional "
                "incoming flow"
            )
        boundary_id = matching_boundaries[node_id]
        if boundary_id is None:
            continue
        boundary = nodes_by_id.get(stringify(boundary_id))
        if boundary is None or boundary.get("kind") != "boundaryEvent":
            raise ValueError(
                f"matching boundary {boundary_id} for error end {node_id} "
                "does not identify a boundary event"
            )
        if boundary.get("errorRef") != node.get("errorRef"):
            raise ValueError(
                f"error end {node_id} and boundary {boundary_id} must use "
                "the same errorRef"
            )
        if boundary.get("attachedTo") != owners_by_id[node_id]:
            raise ValueError(
                f"boundary {boundary_id} must attach to the subprocess "
                f"containing error end {node_id}"
            )
        if boundary.get("cancelActivity", True) is not True:
            raise ValueError(
                f"matching error boundary {boundary_id} must be interrupting"
            )

    decision_phases = constraints.get("decisionPhases")
    if not isinstance(decision_phases, dict):
        raise ValueError("constraints.decisionPhases is required")
    for phase_id, phase_constraint in decision_phases.items():
        phase = nodes_by_id.get(phase_id)
        if phase is None or phase.get("kind") != "subProcess":
            raise ValueError(
                f"decision phase {phase_id} must identify an embedded subprocess"
            )
        minimum = phase_constraint.get("minDivergingExclusiveGateways")
        if minimum is None:
            raise ValueError(
                f"decision phase {phase_id} must declare "
                "minDivergingExclusiveGateways"
            )
        phase_outgoing = index_scope(phase)[1]
        diverging = [
            node
            for node in phase.get("nodes", [])
            if node.get("kind") == "exclusiveGateway"
            and len(phase_outgoing.get(stringify(node["id"]), [])) >= 2
        ]
        if len(diverging) < int(minimum):
            raise ValueError(
                f"decision phase {phase_id} requires at least {minimum} "
                f"diverging exclusive gateways, found {len(diverging)}"
            )

    root_topology = constraints.get("rootTopology")
    if not isinstance(root_topology, dict):
        raise ValueError("constraints.rootTopology is required")
    root_nodes = process.get("nodes", [])
    for kind, key in (
        ("startEvent", "exactStartEvents"),
        ("endEvent", "exactEndEvents"),
    ):
        expected = root_topology.get(key)
        if expected is None:
            raise ValueError(f"constraints.rootTopology.{key} is required")
        actual = len([node for node in root_nodes if node.get("kind") == kind])
        if actual != int(expected):
            raise ValueError(
                f"root topology requires exactly {expected} {kind} nodes, "
                f"found {actual}"
            )

    reachability_rules = constraints.get("requiredReachability")
    if not isinstance(reachability_rules, list):
        raise ValueError("constraints.requiredReachability is required")
    root_ids = {stringify(node["id"]) for node in root_nodes}
    _root_incoming, root_outgoing = index_scope(process)
    root_flows_by_id = {
        stringify(flow["id"]): flow
        for flow in process.get("flows", [])
    }
    for rule in reachability_rules:
        target = stringify(rule["target"])
        sources = [stringify(source) for source in rule["sources"]]
        unknown = sorted(({target, *sources}) - root_ids)
        if unknown:
            raise ValueError(
                f"required reachability references unknown root nodes: {unknown}"
            )
        unreachable = [
            source
            for source in sources
            if not reachable(source, target, root_outgoing, root_flows_by_id)
        ]
        if unreachable:
            raise ValueError(
                f"root nodes {unreachable} do not reach required convergence "
                f"target {target}"
            )


def default_size(kind: str) -> tuple[int, int]:
    if kind in {"startEvent", "endEvent", "boundaryEvent", "intermediateThrowEvent", "intermediateCatchEvent"}:
        return 36, 36
    if kind in {"exclusiveGateway", "parallelGateway"}:
        return 50, 50
    if kind == "subProcess":
        return 600, 420
    return 120, 80


def layout_scope(
    scope: dict[str, object],
    overrides: dict[str, object],
    positions: dict[str, tuple[float, float, float, float]],
    *,
    origin_x: float,
    origin_y: float,
    max_columns: int,
) -> tuple[float, float]:
    """Lay out one BPMN scope while keeping embedded scopes spatially nested."""
    nodes = list(scope.get("nodes", []))
    regular_nodes = [
        node for node in nodes if node.get("kind") != "boundaryEvent"
    ]
    boundary_nodes = [
        node for node in nodes if node.get("kind") == "boundaryEvent"
    ]
    cursor_x = origin_x
    cursor_y = origin_y
    row_height = 0.0
    column = 0
    scope_right = origin_x
    scope_bottom = origin_y

    for node in regular_nodes:
        if column >= max_columns:
            cursor_x = origin_x
            cursor_y += row_height + 80
            row_height = 0.0
            column = 0

        node_id = stringify(node["id"])
        kind = stringify(node["kind"])
        override = overrides.get(node_id, {})
        if not isinstance(override, dict):
            raise ValueError(f"diagram shape override for {node_id} must be an object")
        default_width, default_height = default_size(kind)
        x = float(override.get("x", cursor_x))
        y = float(override.get("y", cursor_y))
        width = float(override.get("width", default_width))
        height = float(override.get("height", default_height))

        if kind == "subProcess":
            child_scope = {
                "nodes": node.get("nodes", []),
                "flows": node.get("flows", []),
            }
            child_nodes = collect_nodes(child_scope)
            if child_nodes:
                child_right, child_bottom = layout_scope(
                    child_scope,
                    overrides,
                    positions,
                    origin_x=x + 40,
                    origin_y=y + 70,
                    max_columns=5,
                )
                width = max(width, child_right - x + 40)
                height = max(height, child_bottom - y + 50)

        positions[node_id] = (x, y, width, height)
        cursor_x = max(cursor_x, x + width + 80)
        row_height = max(row_height, y + height - cursor_y)
        scope_right = max(scope_right, x + width)
        scope_bottom = max(scope_bottom, y + height)
        column += 1

    boundary_counts: dict[str, int] = {}
    for node in boundary_nodes:
        node_id = stringify(node["id"])
        attached_to = stringify(node.get("attachedTo", ""))
        if attached_to not in positions:
            raise ValueError(
                f"boundary event {node_id} references unknown DI host "
                f"{attached_to!r}"
            )
        host_x, host_y, host_width, host_height = positions[attached_to]
        default_width, default_height = default_size("boundaryEvent")
        ordinal = boundary_counts.get(attached_to, 0)
        boundary_counts[attached_to] = ordinal + 1
        override = overrides.get(node_id, {})
        if not isinstance(override, dict):
            raise ValueError(
                f"diagram shape override for {node_id} must be an object"
            )
        width = float(override.get("width", default_width))
        height = float(override.get("height", default_height))
        default_x = host_x + host_width - 55 - ordinal * (width + 12)
        default_y = host_y + host_height - height / 2
        x = float(override.get("x", default_x))
        y = float(override.get("y", default_y))
        positions[node_id] = (x, y, width, height)
        scope_right = max(scope_right, x + width)
        scope_bottom = max(scope_bottom, y + height)

    return scope_right, scope_bottom


def add_di(
    definitions: ET.Element,
    process_id: str,
    scope: dict[str, object],
    diagram_spec: dict[str, object],
) -> None:
    diagram = ET.SubElement(
        definitions,
        q("bpmndi", "BPMNDiagram"),
        {"id": stringify(diagram_spec.get("id", f"Diagram_{process_id}"))},
    )
    plane = ET.SubElement(
        diagram,
        q("bpmndi", "BPMNPlane"),
        {
            "id": stringify(diagram_spec.get("planeId", f"Plane_{process_id}")),
            "bpmnElement": process_id,
        },
    )

    positions: dict[str, tuple[float, float, float, float]] = {}
    overrides = diagram_spec.get("shapes", {})
    if not isinstance(overrides, dict):
        raise ValueError("diagram.shapes must be an object")
    layout_scope(
        scope,
        overrides,
        positions,
        origin_x=100,
        origin_y=100,
        max_columns=8,
    )

    for node in collect_nodes(scope):
        node_id = stringify(node["id"])
        kind = stringify(node["kind"])
        override = overrides.get(node_id, {})
        x, y, width, height = positions[node_id]
        shape_attrs = {
            "id": stringify(override.get("id", f"Shape_{node_id}")),
            "bpmnElement": node_id,
        }
        if kind == "subProcess":
            shape_attrs["isExpanded"] = stringify(
                override.get("isExpanded", True)
            )
        shape = ET.SubElement(plane, q("bpmndi", "BPMNShape"), shape_attrs)
        ET.SubElement(
            shape,
            q("dc", "Bounds"),
            {
                "x": stringify(x),
                "y": stringify(y),
                "width": stringify(width),
                "height": stringify(height),
            },
        )

    edge_overrides = diagram_spec.get("edges", {})
    for flow in collect_flows(scope):
        flow_id = stringify(flow["id"])
        source = positions[stringify(flow["source"])]
        target = positions[stringify(flow["target"])]
        points = edge_overrides.get(flow_id)
        if not points:
            points = [
                {"x": source[0] + source[2], "y": source[1] + source[3] / 2},
                {"x": target[0], "y": target[1] + target[3] / 2},
            ]
        edge = ET.SubElement(
            plane,
            q("bpmndi", "BPMNEdge"),
            {
                "id": f"Edge_{flow_id}",
                "bpmnElement": flow_id,
            },
        )
        for point in points:
            ET.SubElement(
                edge,
                q("di", "waypoint"),
                {
                    "x": stringify(point["x"]),
                    "y": stringify(point["y"]),
                },
            )


def schema_for_variable(variable: dict[str, object]) -> dict[str, object]:
    if variable.get("schema") is not None:
        return variable["schema"]
    variable_type = stringify(variable["type"])
    if variable_type == "json":
        return {}
    return {"type": variable_type}


def prefixed_variable_id(prefix: str, variable_id: str) -> str:
    return f"{prefix}_{variable_id}"


def runtime_variable_contract(
    variables: list[dict[str, object]],
    start_id: str,
    end_id: str | None,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Expand public variables into external declarations plus mutable internals.

    Alpha runtime binds entry-point payloads to public input declarations and
    reads results from public output declarations. Gateway and task expressions
    operate on internal variables. Explicit Start/End mappings bridge those two
    contracts while preserving callers' stable ids for expressions.
    """
    rendered: list[dict[str, object]] = []
    start_outputs: list[dict[str, object]] = []
    end_outputs: list[dict[str, object]] = []
    reserved_ids = {stringify(variable["id"]) for variable in variables}

    def public_id(prefix: str, variable_id: str) -> str:
        candidate = prefixed_variable_id(prefix, variable_id)
        if candidate in reserved_ids:
            raise ValueError(
                f"generated public variable id {candidate!r} collides with a "
                "declared variable id"
            )
        reserved_ids.add(candidate)
        return candidate

    for variable in variables:
        original = copy.deepcopy(variable)
        direction = stringify(original["direction"])
        variable_id = stringify(original["id"])
        variable_name = stringify(original["name"])
        is_input = direction in {"input", "inputOutput", "input/output"}
        is_output = direction in {"output", "inputOutput", "input/output"}

        if is_input:
            external_input = copy.deepcopy(original)
            external_input["direction"] = "input"
            external_input["id"] = public_id("input", variable_id)
            external_input["elementId"] = start_id
            rendered.append(external_input)
            start_outputs.append(
                {
                    "name": variable_name,
                    "type": original["type"],
                    "var": variable_id,
                    "source": f"=vars.{external_input['id']}",
                }
            )

        if is_output:
            if end_id is None:
                raise ValueError(
                    "project.endId is required when a process with public "
                    "outputs has multiple root end events"
                )
            external_output = copy.deepcopy(original)
            external_output["direction"] = "output"
            external_output["id"] = public_id("output", variable_id)
            external_output["elementId"] = end_id
            rendered.append(external_output)
            end_outputs.append(
                {
                    "name": variable_name,
                    "type": original["type"],
                    "var": external_output["id"],
                    "source": f"=vars.{variable_id}",
                }
            )

        internal = copy.deepcopy(original)
        internal["direction"] = "internal"
        if is_input:
            internal.setdefault("elementId", start_id)
        rendered.append(internal)

    return rendered, start_outputs, end_outputs


def merge_bridge_mapping(
    node: dict[str, object],
    outputs: list[dict[str, object]],
) -> None:
    if not outputs:
        return
    mapping = node.setdefault(
        "mapping",
        {
            "serviceType": "BPMN.Variables",
            "version": "v1",
            "outputs": [],
        },
    )
    if mapping.get("serviceType") != "BPMN.Variables":
        raise ValueError(
            f"public variable bridge on {node['id']} requires "
            "serviceType BPMN.Variables"
        )
    existing = {
        stringify(field["var"])
        for field in mapping.setdefault("outputs", [])
    }
    existing_names = {
        stringify(field["name"])
        for field in mapping["outputs"]
    }
    duplicates = existing & {
        stringify(field["var"])
        for field in outputs
    }
    duplicate_names = existing_names & {
        stringify(field["name"])
        for field in outputs
    }
    if duplicates or duplicate_names:
        details = []
        if duplicates:
            details.append(f"targets {sorted(duplicates)}")
        if duplicate_names:
            details.append(f"names {sorted(duplicate_names)}")
        raise ValueError(
            f"public variable bridge on {node['id']} duplicates output "
            + " and ".join(details)
        )
    mapping["outputs"].extend(outputs)


def write_metadata(
    project_dir: Path,
    project_name: str,
    bpmn_name: str,
    start_id: str,
    entry_point_id: str,
    variables: list[dict[str, object]],
) -> None:
    inputs = {
        stringify(variable["name"]): schema_for_variable(variable)
        for variable in variables
        if variable["direction"] in {"input", "inputOutput", "input/output"}
    }
    outputs = {
        stringify(variable["name"]): schema_for_variable(variable)
        for variable in variables
        if variable["direction"] in {"output", "inputOutput", "input/output"}
    }
    files = {
        "project.uiproj": {
            "projectVersion": "1.0.0",
            "ProjectType": "ProcessOrchestration",
            "Name": project_name,
            "main": bpmn_name,
        },
        "operate.json": {
            "main": bpmn_name,
            "contentType": "ProcessOrchestration",
        },
        "entry-points.json": {
            "entryPoints": [
                {
                    "id": entry_point_id,
                    "filePath": f"/content/{bpmn_name}#{start_id}",
                    "inputSchema": {"type": "object", "properties": inputs},
                    "outputSchema": {"type": "object", "properties": outputs},
                }
            ]
        },
        "bindings_v2.json": {"version": "2.0", "resources": []},
        "package-descriptor.json": {
            "content": [
                f"content/{bpmn_name}",
                "content/bindings_v2.json",
                "content/entry-points.json",
                "content/operate.json",
            ]
        },
    }
    for filename, payload in files.items():
        (project_dir / filename).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )


def build(spec: dict[str, object], project_dir: Path) -> Path:
    validate_constraints(spec)
    project = spec["project"]
    project_name = stringify(project["name"])
    bpmn_name = stringify(project.get("bpmnFile", f"{project_name}.bpmn"))
    process_spec = copy.deepcopy(spec["process"])
    process_id = stringify(process_spec["id"])
    start_id = stringify(project["startId"])
    entry_point_id = stringify(project["entryPointId"])

    definitions = ET.Element(
        q("bpmn", "definitions"),
        {
            "id": stringify(spec.get("definitionsId", f"Definitions_{process_id}")),
            "targetNamespace": stringify(
                spec.get("targetNamespace", f"http://uipath.com/{project_name}")
            ),
            "exporter": "UiPath BPMN structural renderer",
            "exporterVersion": "1.0",
        },
    )
    for error in spec.get("errors", []):
        ET.SubElement(
            definitions,
            q("bpmn", "error"),
            attrs(error),
        )

    process = ET.SubElement(
        definitions,
        q("bpmn", "process"),
        {
            "id": process_id,
            "name": stringify(process_spec.get("name", project_name)),
            "isExecutable": stringify(process_spec.get("isExecutable", False)),
        },
    )
    variables = process_spec.get("variables", [])
    scope = {
        "nodes": copy.deepcopy(process_spec.get("nodes", [])),
        "flows": copy.deepcopy(process_spec.get("flows", [])),
    }
    start_nodes = [
        node
        for node in scope["nodes"]
        if node.get("kind") == "startEvent" and node.get("id") == start_id
    ]
    if len(start_nodes) != 1:
        raise ValueError(f"startId must identify one root startEvent: {start_id}")
    start_nodes[0]["entryPointId"] = entry_point_id
    root_end_nodes = [
        node
        for node in scope["nodes"]
        if node.get("kind") == "endEvent"
    ]
    end_id = project.get("endId")
    if end_id is None and len(root_end_nodes) == 1:
        end_id = root_end_nodes[0]["id"]
    if end_id is not None:
        matching_end_nodes = [
            node for node in root_end_nodes if node.get("id") == end_id
        ]
        if len(matching_end_nodes) != 1:
            raise ValueError(
                f"endId must identify one root endEvent: {end_id}"
            )
        end_node = matching_end_nodes[0]
    else:
        end_node = None

    rendered_variables, start_bridge, end_bridge = runtime_variable_contract(
        variables,
        start_id,
        stringify(end_id) if end_id is not None else None,
    )
    merge_bridge_mapping(start_nodes[0], start_bridge)
    if end_bridge:
        if end_node is None:
            raise ValueError(
                "public outputs require project.endId or exactly one root "
                "end event"
            )
        merge_bridge_mapping(end_node, end_bridge)

    add_variables(
        process,
        rendered_variables,
        migration_version=stringify(process_spec.get("migrationVersion", 15)),
    )
    variable_ids = {
        stringify(variable["name"]): stringify(variable["id"])
        for variable in variables
    }
    add_scope(process, scope, variable_ids)
    add_di(definitions, process_id, scope, spec.get("diagram", {}))
    ET.indent(definitions, space="  ")

    project_dir.mkdir(parents=True, exist_ok=True)
    bpmn_path = project_dir / bpmn_name
    tree = ET.ElementTree(definitions)
    tree.write(bpmn_path, encoding="utf-8", xml_declaration=True)
    write_metadata(
        project_dir,
        project_name,
        bpmn_name,
        start_id,
        entry_point_id,
        variables,
    )
    return bpmn_path


def example() -> dict[str, object]:
    return {
        "project": {
            "name": "Example",
            "bpmnFile": "Example.bpmn",
            "startId": "Start_Main",
            "entryPointId": "Entry_Main",
        },
        "process": {
            "id": "Process_Example",
            "variables": [
                {
                    "direction": "input",
                    "id": "Var_Request",
                    "name": "request",
                    "type": "string",
                },
                {
                    "direction": "output",
                    "id": "Var_Result",
                    "name": "result",
                    "type": "string",
                },
            ],
            "nodes": [
                {"kind": "startEvent", "id": "Start_Main", "name": "Start"},
                {
                    "kind": "task",
                    "id": "Task_Set",
                    "name": "Set result",
                    "mapping": {
                        "serviceType": "BPMN.Variables",
                        "outputs": [
                            {
                                "name": "result",
                                "type": "string",
                                "var": "result",
                                "source": "Done",
                            }
                        ],
                    },
                },
                {"kind": "endEvent", "id": "End_Main", "name": "End"},
            ],
            "flows": [
                {
                    "id": "Flow_Start_Set",
                    "source": "Start_Main",
                    "target": "Task_Set",
                },
                {
                    "id": "Flow_Set_End",
                    "source": "Task_Set",
                    "target": "End_Main",
                },
            ],
        },
        "constraints": {
            "publicInputs": ["request"],
            "publicOutputs": ["result"],
            "internalVariables": [],
            "scriptTasks": {
                "exact": 0,
                "allowedIds": [],
                "allowedOutputsById": {},
                "requiredInputReferencesById": {},
            },
            "errorEnds": {
                "singleGuardedIncoming": True,
                "allowedIds": [],
                "matchingBoundaryById": {},
                "forbidUntypedBoundaries": True,
            },
            "decisionPhases": {},
            "rootTopology": {
                "exactStartEvents": 1,
                "exactEndEvents": 1,
            },
            "requiredReachability": [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", nargs="?", type=Path)
    parser.add_argument("project_dir", nargs="?", type=Path)
    parser.add_argument(
        "--example",
        action="store_true",
        help="print a minimal declarative spec",
    )
    args = parser.parse_args()
    if args.example:
        json.dump(example(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if not args.spec or not args.project_dir:
        parser.error("spec and project_dir are required unless --example is used")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    path = build(spec, args.project_dir)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
