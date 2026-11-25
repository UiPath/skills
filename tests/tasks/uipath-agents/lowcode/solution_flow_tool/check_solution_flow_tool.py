#!/usr/bin/env python3
"""Solution Maestro Flow tool resource check.

The fixture solution `OrdersSol` ships a registered Flow project `OrderFlow`
with two `in` variables bound to the start trigger (`orderId`, a string, and
`customer`, an object whose nested fields live in the variable's `schema`),
one `out` variable (`status`) and one `inout` variable (`retryCount`, internal
Flow state). The agent adds `OrderDeskAgent` and wires the Flow in as a tool.

Validates the tool resource under OrderDeskAgent/resources/:
  1. $resourceType == "tool" and type == "flow" — lowercase. A deployed Flow is
     listed with Type "Flow" and an agentic process uses "processOrchestration";
     both casings/kinds are called out explicitly instead of surfacing as a
     generic "no flow tool found".
  2. location == "solution" and properties.folderPath == "solution_folder"
     (the Flow lives in the same solution).
  3. properties.processName == "OrderFlow".
  4. referenceKey equals the Flow's process key from the solution-level
     declaration (resources/solution_folder/process/flow/OrderFlow.json).
  5. id is a UUID, isEnabled is truthy, guardrail.policies is a list, and the
     resource folder is named after the resource `name`.
  6. inputSchema.properties == {orderId, customer} and
     outputSchema.properties == {status}: a local Flow project exposes no
     schema through `uip solution resources get`, so the contract is built
     from the Flow's `in` / `out` variables. The `inout` variable is not part
     of the packed entry point and must appear in neither schema.
  7. inputSchema.properties.customer carries the nested fields {email,
     accountNumber}. `uip maestro flow variables list` reports the variable as
     a bare `object`; the fields are in `variables.globals[].schema` in the
     Flow file, and packing keeps them. A bare `{"type": "object"}` hides
     them from the model.
"""

import json
import os
import sys
import uuid
from pathlib import Path

SOLUTION = Path(os.getcwd()) / "OrdersSol"
ROOT = SOLUTION / "OrderDeskAgent"
RESOURCES = ROOT / "resources"
FLOW_DECLARATION = (
    SOLUTION / "resources" / "solution_folder" / "process" / "flow" / "OrderFlow.json"
)
FLOW_NAME = "OrderFlow"
EXPECTED_INPUTS = {"orderId", "customer"}
EXPECTED_OUTPUTS = {"status"}
EXPECTED_CUSTOMER_FIELDS = {"email", "accountNumber"}


def load_resources() -> list:
    if not RESOURCES.is_dir():
        sys.exit(f"FAIL: {RESOURCES} does not exist — the agent authored no resources")
    out = []
    for path in sorted(RESOURCES.rglob("resource.json")):
        try:
            out.append((path, json.loads(path.read_text())))
        except (OSError, json.JSONDecodeError) as e:
            sys.exit(f"FAIL: {path} is not valid JSON: {e}")
    if not out:
        sys.exit(f"FAIL: no resource.json files found under {RESOURCES}")
    return out


def find_flow_tool(resources: list) -> tuple:
    for path, data in resources:
        if data.get("type") == "flow":
            print(f"OK: found flow tool at {path.relative_to(SOLUTION)}")
            return path, data

    for path, data in resources:
        rtype = data.get("type")
        if str(rtype or "").lower() == "flow":
            sys.exit(
                f"FAIL: {path.relative_to(SOLUTION)} has type {rtype!r}; the agent "
                'resource type is "flow" (lowercase). "Flow" is how discovery '
                "reports a Maestro Flow and is rejected by `uip agent validate`."
            )
        if rtype == "processOrchestration":
            sys.exit(
                f"FAIL: {path.relative_to(SOLUTION)} has type "
                '"processOrchestration"; OrderFlow is a Maestro Flow project, '
                'whose tool type is "flow".'
            )

    found = sorted({str(d.get("type")) for _, d in resources if d.get("type")})
    sys.exit(
        f'FAIL: no flow tool (type=="flow") found under {RESOURCES}. '
        f"Tool types present: {found or 'none'}"
    )


def expected_reference_key() -> str:
    if not FLOW_DECLARATION.is_file():
        sys.exit(
            f"FAIL: {FLOW_DECLARATION} is missing — the fixture's Flow declaration "
            "was removed or the Flow project was re-created"
        )
    key = json.loads(FLOW_DECLARATION.read_text()).get("resource", {}).get("key")
    if not isinstance(key, str) or not key:
        sys.exit(f"FAIL: {FLOW_DECLARATION} has no resource.key")
    return key


def assert_header(path: Path, resource: dict) -> None:
    if resource.get("$resourceType") != "tool":
        sys.exit(
            f'FAIL: $resourceType should be "tool", got {resource.get("$resourceType")!r}'
        )
    if resource.get("location") != "solution":
        sys.exit(
            'FAIL: location should be "solution" for a Flow project in the same '
            f'solution, got {resource.get("location")!r}'
        )
    name = resource.get("name")
    if not isinstance(name, str) or not name.strip():
        sys.exit(f"FAIL: flow tool name missing or empty: {name!r}")
    if path.parent.name != name:
        sys.exit(
            f"FAIL: resource folder {path.parent.name!r} must be named after the "
            f"resource name {name!r}"
        )
    description = resource.get("description")
    if not isinstance(description, str) or not description.strip():
        sys.exit("FAIL: flow tool description missing or empty — the model selects the tool by it")
    print(f'OK: $resourceType="tool", type="flow", location="solution", name={name!r}')


def assert_properties(resource: dict) -> None:
    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: properties is not an object: {props!r}")
    if props.get("folderPath") != "solution_folder":
        sys.exit(
            'FAIL: properties.folderPath should be "solution_folder" for a '
            f'solution-internal Flow tool, got {props.get("folderPath")!r}'
        )
    if props.get("processName") != FLOW_NAME:
        sys.exit(
            f"FAIL: properties.processName should be {FLOW_NAME!r}, got "
            f'{props.get("processName")!r}'
        )
    print(f'OK: properties.folderPath="solution_folder", processName="{FLOW_NAME}"')


def assert_identity(resource: dict) -> None:
    rid = resource.get("id")
    try:
        uuid.UUID(str(rid))
    except ValueError:
        sys.exit(f"FAIL: resource id is not a UUID: {rid!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: isEnabled must be truthy, got {resource.get('isEnabled')!r}")
    policies = (resource.get("guardrail") or {}).get("policies")
    if not isinstance(policies, list):
        sys.exit(f"FAIL: guardrail.policies must be a list, got {policies!r}")

    expected = expected_reference_key()
    got = resource.get("referenceKey")
    if not isinstance(got, str) or got.lower() != expected.lower():
        sys.exit(
            f"FAIL: referenceKey should be the Flow's key {expected!r} (the `Key` "
            f"of the OrderFlow row from `uip solution resources list`), got {got!r}"
        )
    print(f"OK: id is a UUID, isEnabled, guardrail.policies present, referenceKey={got}")


def schema_properties(resource: dict, field: str) -> set:
    schema = resource.get(field)
    if not isinstance(schema, dict):
        sys.exit(f"FAIL: {field} must be a JSON Schema object, got {schema!r}")
    props = schema.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: {field}.properties must be an object, got {props!r}")
    return set(props)


def assert_schemas(resource: dict) -> None:
    inputs = schema_properties(resource, "inputSchema")
    if inputs != EXPECTED_INPUTS:
        sys.exit(
            f"FAIL: inputSchema.properties should be exactly {sorted(EXPECTED_INPUTS)} "
            f"(the Flow's `in` variables), got {sorted(inputs)}"
        )
    outputs = schema_properties(resource, "outputSchema")
    if outputs != EXPECTED_OUTPUTS:
        sys.exit(
            f"FAIL: outputSchema.properties should be exactly {sorted(EXPECTED_OUTPUTS)} "
            f"(the Flow's `out` variables), got {sorted(outputs)}"
        )
    print(
        f"OK: inputSchema.properties={sorted(inputs)}, "
        f"outputSchema.properties={sorted(outputs)}"
    )

    customer = resource["inputSchema"]["properties"]["customer"]
    nested = customer.get("properties") if isinstance(customer, dict) else None
    if not isinstance(nested, dict) or set(nested) != EXPECTED_CUSTOMER_FIELDS:
        got = sorted(nested) if isinstance(nested, dict) else customer
        sys.exit(
            "FAIL: inputSchema.properties.customer should carry exactly the nested "
            f"fields {sorted(EXPECTED_CUSTOMER_FIELDS)} from the Flow variable's "
            "`schema` (`variables.globals[]` in OrderFlow.flow — `uip maestro flow "
            f"variables list` does not return it), got {got!r}"
        )
    print(f"OK: inputSchema.properties.customer.properties={sorted(nested)}")


def main() -> None:
    path, resource = find_flow_tool(load_resources())
    assert_header(path, resource)
    assert_properties(resource)
    assert_identity(resource)
    assert_schemas(resource)


if __name__ == "__main__":
    main()
