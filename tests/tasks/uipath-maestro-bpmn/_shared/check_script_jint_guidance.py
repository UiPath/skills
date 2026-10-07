#!/usr/bin/env python3
"""Assert the supported ScriptTask serialization and public I/O behavior."""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
    text_content,
)

FORBIDDEN = (
    "require(",
    "import ",
    "fetch(",
    "XMLHttpRequest",
    "process.",
    "fs.",
    "setTimeout",
    "setInterval",
    "window.",
    "document.",
    "await ",
    "Math.random",
    "Date.now",
    "new Date",
    "crypto.",
)

FLOW_NODE_NAMES = {
    "adHocSubProcess",
    "boundaryEvent",
    "businessRuleTask",
    "callActivity",
    "callChoreography",
    "choreographyTask",
    "complexGateway",
    "endEvent",
    "eventBasedGateway",
    "exclusiveGateway",
    "implicitThrowEvent",
    "inclusiveGateway",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "manualTask",
    "parallelGateway",
    "receiveTask",
    "scriptTask",
    "sendTask",
    "serviceTask",
    "startEvent",
    "subChoreography",
    "subProcess",
    "task",
    "transaction",
    "userTask",
}

ERROR_SCHEMA_PROPERTIES = {
    "code": "string",
    "message": "string",
    "detail": "string",
    "category": "string",
    "status": "number",
    "element": "string",
}


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def root_variables(root: ET.Element) -> list[ET.Element]:
    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process")
    return process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    )


def exactly_one(
    values: list[ET.Element],
    description: str,
) -> ET.Element:
    if len(values) != 1:
        fail(f"expected exactly one {description}, found {len(values)}")
    return values[0]


def one_variable(
    variables: list[ET.Element],
    *,
    name: str,
    kind: str,
    element_id: str,
    or_element_id: str | None = None,
) -> ET.Element:
    # elementId is the scope: the owning element's id, never absent (#3211). A public
    # input or output has two legitimate owners: the canvas and the converter scope it
    # to the start / end event, the builder SDK to the process it belongs to. Both
    # validate and both resolve, so a caller names the alternative.
    # `name` is matched against the id OR the display name. The wire has both: `id` is
    # what expressions read (`vars.<id>`), `name` is what the designer shows. The v1
    # skill writes them identically; the builder SDK defaults `name` to the id but lets
    # an author give a display name (`.input('amount', …, { name: 'Amount' })`), and a
    # grader keyed on `name` alone failed a correct process on capitalisation
    # (skill-bpmn-script-jint-guidance, run 2026-09-25).
    return exactly_one(
        [
            variable
            for variable in variables
            if local_name(variable) == kind
            and name in (variable.attrib.get("id"), variable.attrib.get("name"))
            and variable.attrib.get("elementId") in {element_id, or_element_id}
        ],
        f"{kind} variable named {name!r} (by id or name) scoped to {element_id!r}"
        + (f" or {or_element_id!r}" if or_element_id else ""),
    )


def variable_by_id(
    variables: list[ET.Element],
    variable_id: str,
) -> ET.Element:
    return exactly_one(
        [
            variable
            for variable in variables
            if variable.attrib.get("id") == variable_id
        ],
        f"variable with id {variable_id!r}",
    )


def mapping_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        "bpmn:extensionElements/uipath:mapping/uipath:output",
        NS,
    )


def variables_mapping(element: ET.Element) -> ET.Element:
    mapping = exactly_one(
        element.findall(
            "bpmn:extensionElements/uipath:mapping",
            NS,
        ),
        f"BPMN.Variables mapping on {attr(element, 'id')!r}",
    )
    if mapping.attrib.get("version") != "v1":
        fail(f"{attr(element, 'id')!r} mapping must use version='v1'")
    mapping_type = exactly_one(
        mapping.findall("uipath:type", NS),
        f"mapping type on {attr(element, 'id')!r}",
    )
    if (
        mapping_type.attrib.get("value") != "BPMN.Variables"
        or mapping_type.attrib.get("version") != "v1"
    ):
        fail(f"{attr(element, 'id')!r} must use a BPMN.Variables v1 mapping")
    return mapping


def bridge_target(
    element: ET.Element,
    *,
    source: str,
) -> str:
    # Matched by source + a non-empty target var. The output's `name` and
    # `type` are display metadata — expressions resolve ids and the type
    # contract lives on the variable declarations, so pinning either here
    # would grade serialization style, not behaviour.
    output = exactly_one(
        [
            candidate
            for candidate in mapping_outputs(element)
            if candidate.attrib.get("source") == source
            and candidate.attrib.get("var")
        ],
        f"variable bridge from {source!r}",
    )
    return attr(output, "var")


def flow_reference_ids(element: ET.Element, direction: str) -> list[str]:
    return [
        (reference.text or "").strip()
        for reference in element.findall(f"bpmn:{direction}", NS)
    ]


def input_body(node: ET.Element) -> str:
    return (node.attrib.get("value") or text_content(node)).strip()


def strip_js_comments(script: str) -> str:
    result: list[str] = []
    index = 0
    in_string: str | None = None
    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""
        if in_string:
            result.append(char)
            if char == "\\" and index + 1 < len(script):
                result.append(script[index + 1])
                index += 2
                continue
            if char == in_string:
                in_string = None
            index += 1
            continue
        if char in {'"', "'", "`"}:
            in_string = char
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(script) and script[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(script) and script[index : index + 2] != "*/":
                index += 1
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def main() -> None:
    path, root = parse_bpmn("RiskScoreScriptBpmn")
    bpmn_path = Path(path)
    # The project descriptor `bpmn init` writes beside the artifact. A harness that
    # builds the `.bpmn` on the grader's side (the SDK repo's ladder compiles the
    # agent's `.bpmn.ts` into the workspace root) has no project to grade and sets
    # BPMN_GRADER_SKIP_PROJECT=1; both arms of this suite scaffold one.
    if os.environ.get("BPMN_GRADER_SKIP_PROJECT") != "1":
        project_path = bpmn_path.parent / "project.uiproj"
        if not project_path.is_file():
            fail(f"missing project descriptor beside BPMN: {project_path}")
        try:
            project = json.loads(project_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"project.uiproj is not valid JSON: {exc}")
        if project.get("Name") != "RiskScoreScriptBpmn":
            fail("project.uiproj Name must be RiskScoreScriptBpmn")
        if project.get("ProjectType") != "ProcessOrchestration":
            fail("project.uiproj ProjectType must be ProcessOrchestration")

    process = root.find("bpmn:process", NS)
    if process is None:
        fail("missing bpmn:process")
    process_id = attr(process, "id")
    if not process_id:
        fail("bpmn:process must have a non-empty id")
    # `isExecutable` is not graded: nothing in the CLI reads it, so grading it
    # would grade doc style rather than behaviour (same call as
    # check_simple_approval_bpmn.py; see .claude/rules/test-writing.md).

    start = exactly_one(elements(root, "startEvent"), "root start event")
    end = exactly_one(elements(root, "endEvent"), "root end event")
    task = exactly_one(elements(root, "scriptTask"), "script task")
    start_id = attr(start, "id")
    end_id = attr(end, "id")
    task_id = attr(task, "id")
    for description, element_id in (
        ("StartEvent", start_id),
        ("ScriptTask", task_id),
        ("EndEvent", end_id),
    ):
        if not element_id:
            fail(f"{description} must have a non-empty id")
    if len({start_id, task_id, end_id}) != 3:
        fail("StartEvent, ScriptTask, and EndEvent ids must be distinct")

    flow_nodes = [
        element
        for element in root.iter()
        if local_name(element) in FLOW_NODE_NAMES
    ]
    actual_flow_nodes = [
        (local_name(element), attr(element, "id"))
        for element in flow_nodes
    ]
    expected_flow_nodes = [
        ("startEvent", start_id),
        ("scriptTask", task_id),
        ("endEvent", end_id),
    ]
    if sorted(actual_flow_nodes) != sorted(expected_flow_nodes):
        fail(
            "process must contain exactly StartEvent -> ScriptTask -> EndEvent; "
            f"found {actual_flow_nodes}"
        )

    flows = elements(root, "sequenceFlow")
    if len(flows) != 2:
        fail(f"expected exactly two sequence flows, found {len(flows)}")
    start_flow = exactly_one(
        [
            flow
            for flow in flows
            if attr(flow, "sourceRef") == start_id
            and attr(flow, "targetRef") == task_id
        ],
        "StartEvent-to-ScriptTask sequence flow",
    )
    end_flow = exactly_one(
        [
            flow
            for flow in flows
            if attr(flow, "sourceRef") == task_id
            and attr(flow, "targetRef") == end_id
        ],
        "ScriptTask-to-EndEvent sequence flow",
    )
    start_flow_id = attr(start_flow, "id")
    end_flow_id = attr(end_flow, "id")
    if (
        not start_flow_id
        or not end_flow_id
        or start_flow_id == end_flow_id
        or start_flow_id in {start_id, task_id, end_id}
        or end_flow_id in {start_id, task_id, end_id}
    ):
        fail("sequence flows must have distinct non-empty ids")
    start_incoming_ids = flow_reference_ids(start, "incoming")
    start_outgoing_ids = flow_reference_ids(start, "outgoing")
    if start_incoming_ids or (start_outgoing_ids != [start_flow_id]):
        fail("StartEvent incoming/outgoing references do not match its sequence flow")
    task_incoming_ids = flow_reference_ids(task, "incoming")
    task_outgoing_ids = flow_reference_ids(task, "outgoing")
    if task_incoming_ids != [start_flow_id] or task_outgoing_ids != [end_flow_id]:
        fail("ScriptTask incoming/outgoing references do not match its sequence flows")
    end_incoming_ids = flow_reference_ids(end, "incoming")
    end_outgoing_ids = flow_reference_ids(end, "outgoing")
    if (end_incoming_ids != [end_flow_id]) or end_outgoing_ids:
        fail("EndEvent incoming/outgoing references do not match its sequence flow")

    # The entryPointId is what `bpmn init` assigns and `decompile` carries into the
    # source; like the project descriptor above, it is a product of the scaffold
    # workflow, so the same harness flag skips it.
    if os.environ.get("BPMN_GRADER_SKIP_PROJECT") != "1":
        entry_point = exactly_one(
            start.findall(
                "bpmn:extensionElements/uipath:entryPointId",
                NS,
            ),
            "manual-start entryPointId",
        )
        entry_point_id = entry_point.attrib.get("value", "").strip()
        try:
            UUID(entry_point_id)
        except (ValueError, AttributeError):
            fail("manual start entryPointId must be a valid UUID")
        if entry_point_id == "00000000-0000-4000-8000-000000000001":
            fail("manual start entryPointId copied the documentation example")

    if attr(task, "scriptFormat") != "JavaScript":
        fail('script task must set scriptFormat="JavaScript"')
    script_version = exactly_one(
        task.findall(
            "bpmn:extensionElements/uipath:scriptVersion",
            NS,
        ),
        "scriptVersion",
    )
    version_match = re.fullmatch(r"v(\d+)", script_version.attrib.get("value", ""))
    if version_match is None or int(version_match.group(1)) < 3:
        fail("script task must use a supported vars/metadata script version")
    # The ScriptTask mapping is the contract; a StartEvent/EndEvent mapping is present
    # only when the author bridged through one, and is then held to the same shape.
    task_mapping = variables_mapping(task)
    for event in (start, end):
        if event.findall("bpmn:extensionElements/uipath:mapping", NS):
            variables_mapping(event)

    variables = root_variables(root)
    variable_ids = [variable.attrib.get("id", "") for variable in variables]
    if not all(variable_ids) or len(variable_ids) != len(set(variable_ids)):
        fail("all root variables must have unique non-empty ids")

    public_amount = one_variable(
        variables, name="amount", kind="input", element_id=start_id, or_element_id=process_id
    )
    public_days = one_variable(
        variables, name="daysOverdue", kind="input", element_id=start_id, or_element_id=process_id
    )
    public_risk = one_variable(
        variables, name="riskScore", kind="output", element_id=end_id, or_element_id=process_id
    )
    # The script's result reaches a variable through the task's `=result.response`
    # output row — that row IS the contract (ScriptActivities.DoInvokeScriptTaskAsync
    # wraps a v2+ return as `{ response }`). Which variable it lands in, and what the
    # row is called, are the author's: the canvas template names both `scriptResponse`
    # and scopes the variable to the task, the SDK writes `outputs: { riskScore:
    # '=result.response' }` and lands it in the public output directly. Grading the
    # canvas spelling failed every SDK-authored process on a name (2026-09-25 run,
    # arm-neutrality invariant 4 in README.md), so the variable is found from the row.
    task_outputs = mapping_outputs(task)
    response_row = exactly_one(
        [
            output
            for output in task_outputs
            if output.attrib.get("source") == "=result.response"
            and output.attrib.get("var")
        ],
        "ScriptTask output row reading =result.response",
    )
    response = variable_by_id(variables, attr(response_row, "var"))
    if local_name(response) not in {"inputOutput", "output"}:
        fail("the =result.response row must land in a mutable (inputOutput) or output variable")
    if response.attrib.get("elementId") not in {task_id, process_id, end_id}:
        fail(
            "the =result.response variable must carry elementId of the script task, "
            "the process, or the end event (#3211)"
        )
    for variable, expected_types, description in (
        # Public declarations reach entry-point schema derivation, so they use
        # the refresh vocabulary (number), not the canvas float type.
        (public_amount, {"number"}, "public amount"),
        (public_days, {"integer"}, "public daysOverdue"),
        (public_risk, {"number"}, "public riskScore"),
        # The canvas types the response from the script's inferred return
        # (ScriptTaskProperties.tsx:347) as `double`; the refresh vocabulary for the
        # same value is `number`. Both name a float, and this script returns one.
        (response, {"double", "number"}, "script response"),
    ):
        if variable.attrib.get("type") not in expected_types:
            fail(f"{description} variable must use type {sorted(expected_types)!r}")

    # The Error slot is OPTIONAL: the canvas template always writes a task-scoped
    # `Error` variable and an `=Error` row; the SDK writes neither unless asked (a
    # boundary or an event sub-process is how it reads a failure). When the author
    # did write one, it must be the platform's error envelope.
    error_rows = [
        output
        for output in task_outputs
        if output.attrib.get("source") in {"=Error", "=result.Error"}
    ]
    error = None
    if error_rows:
        error_row = exactly_one(error_rows, "ScriptTask Error output row")
        if not error_row.attrib.get("var"):
            fail("the ScriptTask Error row must name the variable it writes")
        error = variable_by_id(variables, attr(error_row, "var"))
        if error.attrib.get("type") != "jsonSchema" or error_row.attrib.get("type") != "jsonSchema":
            fail("the ScriptTask Error variable and row must use type='jsonSchema'")
        try:
            error_schema = json.loads(text_content(error).strip())
        except json.JSONDecodeError as exc:
            fail(f"task-scoped Error schema is not valid JSON: {exc}")
        if not isinstance(error_schema, dict) or error_schema.get("type") != "object":
            fail("task-scoped Error schema must describe an object")
        error_properties = error_schema.get("properties")
        if not isinstance(error_properties, dict):
            fail("task-scoped Error schema must declare properties")
        for property_name, property_type in ERROR_SCHEMA_PROPERTIES.items():
            property_schema = error_properties.get(property_name)
            if (
                not isinstance(property_schema, dict)
                or property_schema.get("type") != property_type
            ):
                fail(
                    "task-scoped Error schema must declare "
                    f"{property_name!r} as {property_type!r}"
                )

    # Public inputs reach the script one of two ways, and both are the platform's:
    # the canvas template BRIDGES each public input into a process-scoped internal
    # variable on the start event and the script reads the internal one; the SDK
    # reads the public variable directly (`inputs: { amount: '=vars.amount' }`). The
    # same on the way out — a bridge on the end event, or the `=result.response` row
    # landing in the public output itself. Grade that the value flows, not which of
    # the two spellings carried it.
    def bridge_or_self(public_variable: ET.Element) -> str:
        public_id = attr(public_variable, "id")
        bridges = [
            candidate
            for candidate in mapping_outputs(start)
            if candidate.attrib.get("source") == f"=vars.{public_id}"
            and candidate.attrib.get("var")
        ]
        if not bridges and mapping_outputs(start):
            # The author bridged SOME input on the start event — then every input must
            # be bridged, or the script reads one that was never carried across.
            exactly_one(bridges, f"variable bridge from =vars.{public_id}")
        if not bridges:
            return public_id
        return attr(exactly_one(bridges, f"variable bridge from =vars.{public_id}"), "var")

    internal_amount_id = bridge_or_self(public_amount)
    internal_days_id = bridge_or_self(public_days)
    if internal_amount_id == internal_days_id:
        fail("the amount and daysOverdue bridges must target distinct variables")
    end_bridges = [
        output
        for output in mapping_outputs(end)
        if output.attrib.get("var") == attr(public_risk, "id")
        and re.fullmatch(
            r"=vars\.[\w.-]+",
            output.attrib.get("source", ""),
        )
    ]
    if end_bridges:
        end_output = exactly_one(end_bridges, "numeric result to public riskScore output bridge")
        result_variable_id = attr(end_output, "source").removeprefix("=vars.")
    else:
        # No bridge: the script's own row must land in the public output.
        result_variable_id = attr(public_risk, "id")
        if attr(response, "id") != result_variable_id:
            fail(
                "riskScore is neither bridged on the EndEvent nor written by the "
                "ScriptTask's =result.response row"
            )

    for variable_id, public_variable, expected_types in (
        (internal_amount_id, public_amount, {"double", "number"}),
        (internal_days_id, public_days, {"integer"}),
    ):
        if variable_id == attr(public_variable, "id"):
            continue  # read directly; the public declaration was typed above
        variable = variable_by_id(variables, variable_id)
        if local_name(variable) != "inputOutput":
            fail(f"{variable_id!r} must be a mutable inputOutput variable")
        if variable.attrib.get("type") not in expected_types:
            fail(f"{variable_id!r} must use type {sorted(expected_types)!r}")
        if variable.attrib.get("elementId") != process_id:
            fail(
                f"{variable_id!r} must be process-scoped via "
                f"elementId={process_id!r} (#3211)"
            )

    response_id = attr(response, "id")

    start_bridge_count = len(mapping_outputs(start))
    if start_bridge_count not in {0, 2}:
        fail("StartEvent mapping must bridge both public inputs or neither")
    if len(mapping_outputs(end)) > 1:
        fail("EndEvent mapping must contain at most the public-output bridge")

    # The script's inputs arrive through the one `args` row, and the platform writes
    # them two ways: the canvas template passes the WHOLE state (`{"vars": "=vars",
    # "metadata": "=metadata"}`, with a matching inputSchema) and the script reads
    # `vars.<id>`; the SDK passes each input by name (`{"amount": "=vars.amount"}`) and
    # the script reads `amount`. Both are the runtime's contract (`ScriptActivities`
    # binds every args key as a script global). Grade that each input reaches the
    # script under some name, and that an inputSchema, when written, describes the
    # args it accompanies.
    task_inputs = task.findall(
        "bpmn:extensionElements/uipath:mapping/uipath:input",
        NS,
    )
    args = exactly_one(
        [
            task_input
            for task_input in task_inputs
            if task_input.attrib.get("name") == "args"
        ],
        "ScriptTask args input",
    )
    if len(task_inputs) != 1:
        fail("ScriptTask mapping must contain exactly one args input")
    if args.attrib.get("type") != "json" or args.attrib.get("target") != "bodyField":
        fail("ScriptTask must declare args targeting bodyField")
    try:
        args_value = json.loads(input_body(args))
    except json.JSONDecodeError as exc:
        fail(f"ScriptTask args is not valid JSON: {exc}")
    if not isinstance(args_value, dict) or not args_value:
        fail("ScriptTask args must be a non-empty JSON object")
    whole_state = args_value == {"vars": "=vars", "metadata": "=metadata"}
    # arg name -> the variable id it reads, for the per-input form.
    arg_sources: dict[str, str] = {}
    if not whole_state:
        for arg_name, arg_value in args_value.items():
            match = re.fullmatch(r"=vars\.([A-Za-z0-9_]+)", str(arg_value))
            if match is None:
                fail(
                    f"ScriptTask args entry {arg_name!r} must read one process variable "
                    f"(=vars.<id>); got {arg_value!r}"
                )
            arg_sources[arg_name] = match.group(1)

    input_schemas = task.findall(
        "bpmn:extensionElements/uipath:mapping/uipath:context/uipath:inputSchema",
        NS,
    )
    if whole_state and not input_schemas:
        fail("a whole-state args row needs the vars/metadata inputSchema beside it")
    if input_schemas:
        input_schema = exactly_one(input_schemas, "ScriptTask inputSchema")
        if input_schema.attrib.get("type") != "jsonSchema":
            fail("ScriptTask must declare a jsonSchema inputSchema")
        exactly_one(
            task_mapping.findall("uipath:context", NS),
            "ScriptTask mapping context",
        )
        try:
            schema = json.loads(input_body(input_schema))
        except json.JSONDecodeError as exc:
            fail(f"ScriptTask inputSchema is not valid JSON: {exc}")
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        if not isinstance(schema, dict) or schema.get("type") != "object" or not isinstance(properties, dict):
            fail("ScriptTask inputSchema must describe an object")
        if whole_state:
            if schema.get("required", []) or set(properties) != {"vars", "metadata"}:
                fail("ScriptTask inputSchema must use the current vars/metadata schema")
            for name in ("vars", "metadata"):
                if not isinstance(properties.get(name), dict) or properties[name].get("type") != "object":
                    fail(f"ScriptTask inputSchema must declare {name!r} as an object")
        elif set(properties) != set(args_value):
            fail(
                "ScriptTask inputSchema must describe exactly the args it accompanies; "
                f"schema has {sorted(properties)}, args has {sorted(args_value)}"
            )

    script = task.find("bpmn:script", NS)
    if script is None or not text_content(script).strip():
        fail("script task is missing JavaScript source")
    body = strip_js_comments(text_content(script))
    forbidden = [token for token in FORBIDDEN if token in body]
    if forbidden:
        fail(f"script uses APIs outside the Jint boundary: {forbidden}")
    if re.search(r"return\s*\{\s*response\s*:", body):
        fail("ScriptTask must return the intended value without a response wrapper")
    if not re.search(r"(^|[;{}]\s*)return\b", body, re.MULTILINE):
        fail("script must contain an executable return statement")
    for variable_id in (internal_amount_id, internal_days_id):
        # Whole-state args: the script reads `vars.<id>`. Per-input args: it reads the
        # arg bound to `=vars.<id>`, as a bare identifier.
        names = [name for name, source in arg_sources.items() if source == variable_id]
        if whole_state:
            if f"vars.{variable_id}" not in body:
                fail(f"script must read input through vars.{variable_id}")
        elif not names:
            fail(f"ScriptTask args pass no entry reading =vars.{variable_id}")
        elif not any(re.search(rf"(?<![\w.]){re.escape(name)}\b", body) for name in names):
            fail(f"script must read {' or '.join(names)} (the args bound to vars.{variable_id})")

    # The response row's type must agree with the variable it writes — the runtime
    # coerces by the row's type, so a float row landing in an integer variable (or the
    # reverse) is the D1 hazard. `double` and `number` name the same float.
    row_type = response_row.attrib.get("type")
    var_type = response.attrib.get("type")
    if not (row_type == var_type or {row_type, var_type} <= {"double", "number"}):
        fail(f"the =result.response row is typed {row_type!r} but writes a {var_type!r} variable")
    standard_rows = 1 + len(error_rows)
    if result_variable_id == response_id:
        if len(task_outputs) != standard_rows:
            fail(
                "a script result that reaches riskScore directly requires exactly "
                "the standard ScriptTask outputs (=result.response, and Error when written)"
            )
    else:
        business_result = variable_by_id(variables, result_variable_id)
        if local_name(business_result) != "inputOutput":
            fail("the optional business result must be a mutable inputOutput variable")
        if business_result.attrib.get("type") != "double":
            fail("the optional mutable business result must use type='double'")
        if business_result.attrib.get("elementId") not in {task_id, process_id}:
            fail(
                "the optional business result must carry elementId of the "
                "script task or the process (#3211)"
            )
        if len(task_outputs) != standard_rows + 1:
            fail(
                "a distinct business-result variable requires exactly one "
                "custom output in addition to the standard ScriptTask outputs"
            )
        risk_mapping = exactly_one(
            [
                output
                for output in task_outputs
                if output.attrib.get("var") == result_variable_id
                and output.attrib.get("source") == f"=vars.{response_id}"
                and output.attrib.get("type") == "double"
            ],
            "optional scriptResponse-to-business-result output mapping",
        )
        if risk_mapping.attrib.get("custom") != "true":
            fail("the optional business-result mapping must be marked custom=true")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} uses the supported ScriptTask contract")


if __name__ == "__main__":
    main()
