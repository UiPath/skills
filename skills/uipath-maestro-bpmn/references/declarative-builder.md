# Declarative structural renderer

Use `scripts/build-bpmn.py` for a **large new** BPMN project whose executable
work uses only the Variables and ScriptTask mapping forms documented below.
Do not use it for connectors, HITL, RPA, agents, send/receive tasks, another
registry payload absent from this contract, or an existing/imported BPMN.
Assemble unsupported registry nodes from their exact XML templates, and keep
brownfield edits surgical.

The renderer removes XML bookkeeping only. The JSON spec must still state every
process variable, node, gateway condition, Variables assignment, scope, error
boundary, loop, and sequence flow. Its documented mapping fields must come from
live registry templates.

This guide and `build-bpmn.py --example` are the renderer's authoring contract.
Do not inspect the renderer implementation or its tests to infer extra fields or
copy task-specific graphs. If a required construct is absent here, author that
small structural fragment from `structural-bpmn.md` or report the renderer gap.

## Start and render

```bash
python3 scripts/build-bpmn.py --example > <project>.spec.json
python3 scripts/build-bpmn.py <project>.spec.json <project-directory>
```

Rendering writes:

- the requested `.bpmn`;
- `project.uiproj`;
- `operate.json`;
- `entry-points.json`;
- `bindings_v2.json`;
- `package-descriptor.json`.

Keep registry evidence separately when the user requests it. Re-rendering is
safe for a new project whose spec is the authored source; do not hand-edit the
rendered XML and then overwrite it from a stale spec.

## Top-level shape

```json
{
  "project": {
    "name": "OrderTriage",
    "bpmnFile": "OrderTriage.bpmn",
    "startId": "Start_Main",
    "entryPointId": "Entry_Main"
  },
  "definitionsId": "Definitions_OrderTriage",
  "targetNamespace": "http://uipath.com/order-triage",
  "errors": [
    {
      "id": "Error_BackendUnavailable",
      "name": "BackendUnavailable",
      "errorCode": "BackendUnavailable"
    }
  ],
  "process": {
    "id": "Process_OrderTriage",
    "name": "OrderTriage",
    "variables": [],
    "bindings": [],
    "nodes": [],
    "flows": []
  },
  "constraints": {
    "publicInputs": ["orderId"],
    "publicOutputs": ["route"],
    "internalVariables": ["normalizedOrderId"],
    "scriptTasks": {
      "exact": 1,
      "allowedIds": ["Task_Normalize"],
      "allowedOutputsById": {
        "Task_Normalize": ["normalizedOrderId"]
      },
      "requiredInputReferencesById": {
        "Task_Normalize": ["orderId"]
      }
    },
    "errorEnds": {
      "singleGuardedIncoming": true,
      "allowedIds": ["End_AssessError"],
      "matchingBoundaryById": {
        "End_AssessError": "Boundary_AssessError"
      },
      "forbidUntypedBoundaries": true,
      "requiredGuardReferencesById": {
        "End_AssessError": ["backendAvailable", "severity"]
      }
    },
    "decisionPhases": {
      "SubProcess_Assess": {
        "minDivergingExclusiveGateways": 2
      }
    },
    "rootTopology": {
      "exactStartEvents": 1,
      "exactEndEvents": 1
    },
    "requiredReachability": [
      {
        "sources": ["SubProcess_Assess", "Boundary_AssessError"],
        "target": "Gateway_FanOut"
      }
    ]
  },
  "diagram": {
    "shapes": {},
    "edges": {}
  }
}
```

`constraints` is mandatory. Copy the exact public contract, internal working
variables, approved ScriptTask count/ids, each script's exact mapped outputs,
its required input-variable references, and the approved minimum number of
diverging exclusive gateways in each bounded decision subprocess into it before
authoring nodes. A required ScriptTask input may appear in its args mapping or
as a stable `vars.<id>` read in the script body; passing the full `vars` object
does not require redundant per-variable args. Rendering fails if internal
variables leak into the public contract, a script's inputs/outputs drift from
its approved responsibility, an error end lacks one visibly conditional
incoming flow, an error guard omits an approved qualification variable, or a
declared decision phase is underdeveloped. Error-end ids
and their matching, typed, interrupting boundaries must be exact; ordinary
business outcomes must not be smuggled into extra error ends. Root start/end
counts and required convergence points are also checked. Use an empty
`decisionPhases` object only when the approved design has no bounded decision
subprocess, and an empty `requiredReachability` list only when no cross-path
convergence was approved. These checks complement—not replace—the post-render
semantic review.

`diagram` is optional. When coordinates are omitted, the renderer emits
complete DI, expands subprocesses around their child nodes, places boundary
events on their attached activity, and keeps child shapes inside their
subprocess. Supply shape/edge overrides only when intentional layout matters.

## Variables

```json
{
  "direction": "input",
  "id": "Var_OrderId",
  "name": "orderId",
  "type": "string"
}
```

Directions are `input`, `output`, `inputOutput`, or `internal`. The renderer
serializes `internal` as a mutable process variable but excludes it from the
generated entry-point input/output schemas. Use `internal` for unbound working
values such as normalized strings; do not expose implementation variables by
marking them `inputOutput`. The renderer binds public input variables to the
configured root start event and public outputs to the configured root end event.
For a public variable with id `Var_OrderId`, it creates the external
`input_Var_OrderId` or `output_Var_OrderId` declaration, keeps `Var_OrderId` as
the mutable process variable, and adds the Start/End bridge mapping
automatically. Declare the plain stable id once: do not pre-prefix it with
`input_`/`output_`, and do not manually repeat that public field in the root
Start/End mapping. The renderer rejects duplicate bridge names because a
double-prefixed bridge such as `input_input_Var_OrderId` can validate locally
while discarding the caller's value at runtime. Preserve contract types exactly:
`integer`, `number`, `array`, `object`, and `json` are distinct.

Use `schema` when generated entry-point metadata needs more detail:

```json
{
  "direction": "input",
  "id": "Var_Attachments",
  "name": "attachments",
  "type": "array",
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "name": { "type": "string" }
      },
      "required": ["name"]
    }
  }
}
```

## Nodes and flows

Supported `kind` values:

- `startEvent`, `endEvent`, `boundaryEvent`;
- `task`, `scriptTask`, `serviceTask`, `sendTask`, `userTask`,
  `callActivity`;
- `exclusiveGateway`, `parallelGateway`;
- `subProcess`;
- `intermediateThrowEvent`, `intermediateCatchEvent`.

Basic node and flow:

```json
{
  "nodes": [
    { "kind": "startEvent", "id": "Start_Main", "name": "Start" },
    {
      "kind": "exclusiveGateway",
      "id": "Gateway_Route",
      "name": "Route",
      "default": "Flow_Route_Default"
    },
    { "kind": "endEvent", "id": "End_Main", "name": "End" }
  ],
  "flows": [
    {
      "id": "Flow_Start_Route",
      "source": "Start_Main",
      "target": "Gateway_Route"
    },
    {
      "id": "Flow_Route_Default",
      "source": "Gateway_Route",
      "target": "End_Main"
    }
  ]
}
```

A conditional flow adds:

```json
{
  "condition": "=js:vars.Var_Route === \"NewEscalation\""
}
```

Every non-default guard leaving one exclusive gateway must be mutually
exclusive with its siblings. An exclusive gateway is not an ordered `if /
else-if` list: do not rely on which true flow the engine happens to inspect
first. Encode precedence in the predicates (for example, the lower-priority
guard also excludes the higher-priority case), or split the decision into
cascaded exclusive gateways. Every diverging exclusive gateway must name
exactly one outgoing `default` flow. Leave that default flow unconditional and
give every other outgoing flow an explicit condition; the renderer rejects an
incomplete split before it can become a runtime stall.

For a parallel fork/join region, each forked workstream must contribute one
token to the matching parallel join. When a workstream has exclusive internal
alternatives, add an exclusive merge inside that workstream and connect the
merge to the parallel join. Do not wire all mutually exclusive alternative
tasks directly into the parallel join; the join waits for every incoming path
and will deadlock. For example, a three-way fork whose branches each contain
their own decisions still needs exactly three incoming flows at the parallel
join, not one incoming flow per alternative task.

A workstream owns behavior, not merely an output name. If an approved branch
owns an intent or result, assign its real outcome values inside that branch.
Do not precompute the value upstream and add a no-op mapping such as
`action <- vars.action` to satisfy a shape review; that hides policy in the
wrong phase and makes the branch semantically empty.

The renderer derives every node's `<bpmn:incoming>` and `<bpmn:outgoing>` from
the owning scope's `flows`.

## Registry-derived mappings

Copy the service type, version, and field names/types/targets from
`registry get`. The renderer converts a mapping into the registry-owned
`uipath:mapping` shape.

Variables assignment:

```json
{
  "kind": "task",
  "id": "Task_SetRoute",
  "name": "Set route",
  "mapping": {
    "serviceType": "BPMN.Variables",
    "version": "v1",
    "outputs": [
      {
        "name": "route",
        "type": "string",
        "var": "route",
        "source": "NewEscalation"
      }
    ]
  }
}
```

The renderer resolves an output `var` given as a declared variable name to that
variable's stable id.

Mapping `source` is always a string because it becomes an XML attribute. A bare
value is therefore a string literal. For non-string constants, use a typed
expression: `"source": "=true"` / `"source": "=false"` for booleans and
`"source": "=42"` for a number. Do not use JSON `true`, `false`, or a numeric
value as `source`; the renderer rejects those before their type can collapse
into XML text. Array and object constants likewise need an expression such as
`=js:[]` or `=js:{}`.

ScriptTask:

```json
{
  "kind": "scriptTask",
  "id": "Task_Normalize",
  "name": "Normalize",
  "scriptFormat": "JavaScript",
  "scriptVersion": "v3",
  "mapping": {
    "serviceType": "BPMN.Variables",
    "version": "v1",
    "context": [
      {
        "name": "inputSchema",
        "type": "jsonSchema",
        "body": {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "properties": {
            "vars": { "type": "object" },
            "metadata": { "type": "object" }
          },
          "required": []
        }
      }
    ],
    "inputs": [
      {
        "name": "args",
        "type": "json",
        "target": "bodyField",
        "body": {
          "vars": "=vars",
          "metadata": "=metadata"
        }
      }
    ],
    "outputs": [
      {
        "name": "scriptResponse",
        "type": "string",
        "var": "normalizedValue",
        "source": "=result.response"
      },
      {
        "name": "Error",
        "type": "jsonSchema",
        "var": "normalizeError",
        "source": "=Error"
      }
    ]
  },
  "script": "return (vars.Var_Value || \"\").trim();"
}
```

For new v3 ScriptTasks, use the Studio serializer's `BPMN.Variables`
mapping shape, pass the `vars` and `metadata` objects through `args`, and read
stable ids as `vars.<id>` in the script. The renderer serializes an input
`body` as the engine-readable `value` attribute; ordinary XML text is ignored
by the runtime mapping parser. A multi-instance script also passes
`"iterator": "=iterator"` and declares it in the input schema when the
ScriptTask itself owns the marker. For a ScriptTask inside a multi-instance
subprocess, map `=iterator[0].item` to a typed named argument such as
`currentItem` and read that argument. Passing the whole `=iterator` object into
the nested ScriptTask can produce a null global at runtime.

Declare both the response variable and the typed Error variable in the process
variable block. Return the response value directly; the runtime exposes it as
`result.response` to output mappings. Do not add another `{ response: ... }`
wrapper in the script.

When downstream expressions dereference properties of a ScriptTask's object
response, declare those properties in the response variable's JSON schema.
An unshaped `type: "object"` variable does not give Studio or the validator the
property contract needed for expressions such as `vars.<id>.fileId`.
List every property the script guarantees in that schema's `required` array.
Apply the same rule to typed object arguments: declare and require each field
the script reads, rather than leaving a permissive object shell.
Use semantically specific property names in both the returned object and its
schema (for example, `duplicateIssueKey` rather than an ambiguous `key`) so the
data contract remains auditable.

The Error target is activity-scoped, not a generic working variable. Declare it
with `name: "Error"`, `type: "jsonSchema"`, and
`elementId: "<script-task-id>"`. A process with several ScriptTasks therefore
has several same-named Error declarations with distinct ids. In each script
mapping, set the Error output's `var` to that declaration's explicit stable id;
using the ambiguous name `Error` would resolve to only one of them.

Do not put business routing/classification policy in a normalization script.

### Connector activities and connection resources

Discover the connector, connection, object, and activity through the session's
single authenticated registry pull. Save the exact enriched
`registry get Intsvc.ActivityExecution --connection-id ... --object-name ...`
response when evidence is requested. Do not invent operation names, fields, or
targets.

Connector execution uses the registry-owned `uipath:activity` extension rather
than a generic `uipath:mapping`. In a context field, set `element` to `input`
when the XML shape is `<uipath:input name="...">`:

- Keep the context `path` static. Start with the enrichment `Path` and append a
  `{parameterName}` segment for every method parameter whose `Type` is `path`.
  Never put an expression or query string in this field.
- Represent every path or query parameter as its own mapping input using the
  exact registry `Name` and `Type` as `name` and `target`. A path input must
  have the matching `{name}` placeholder in the static context path.
- Put request fields inside the single `body` input. Enrichment field names
  such as `fields.project.key` are dotted leaf paths: reconstruct them as
  nested JSON (`{"fields":{"project":{"key":...}}}`), rather than sending the
  dotted path as a literal top-level key. Preserve every path segment's exact
  casing. Display names and the enrichment dictionary's lookup keys are not
  request field names. Do not replace a leaf with a provider synonym—for
  example, if enrichment exposes `fields.reporter.id`, author `id`, not
  `accountId`.
- Treat required method parameters and required request fields as mandatory.
  The renderer checks the structural path/query split, but only the saved
  enrichment tells you which operation-specific inputs are required.

```json
{
  "kind": "sendTask",
  "id": "Task_SendMessage",
  "name": "Send message",
  "mapping": {
    "extensionTag": "activity",
    "serviceType": "Intsvc.ActivityExecution",
    "version": "v1",
    "context": [
      {
        "element": "input",
        "name": "activity",
        "type": "string",
        "value": "<registry activity>"
      },
      {
        "element": "input",
        "name": "connectorKey",
        "type": "string",
        "value": "<registry connector key>"
      },
      {
        "element": "input",
        "name": "connection",
        "type": "string",
        "value": "=bindings.Binding_Connection"
      },
      {
        "element": "input",
        "name": "folderKey",
        "type": "string",
        "value": "=bindings.Binding_Folder"
      },
      {
        "element": "input",
        "name": "operation",
        "type": "string",
        "value": "<registry operation>"
      },
      {
        "element": "input",
        "name": "objectName",
        "type": "string",
        "value": "<registry object name>"
      },
      {
        "element": "input",
        "name": "method",
        "type": "string",
        "value": "<registry HTTP method>"
      },
      {
        "element": "input",
        "name": "path",
        "type": "string",
        "value": "<registry path>"
      },
      {
        "element": "input",
        "name": "metadata",
        "type": "json",
        "body": {}
      }
    ],
    "inputs": [
      {
        "name": "<path parameter name>",
        "type": "string",
        "target": "path",
        "value": "=vars.<stable variable id>"
      },
      {
        "name": "<query parameter name>",
        "type": "string",
        "target": "query",
        "value": "=vars.<stable variable id>"
      },
      {
        "name": "body",
        "type": "json",
        "target": "body",
        "body": {
          "<exact request field name>": "=vars.<stable variable id>"
        }
      }
    ],
    "outputs": [
      {
        "name": "result",
        "type": "custom",
        "var": "connectorResult",
        "source": "."
      }
    ]
  }
}
```

Every connection reference also needs two process-level bindings: one for the
connection id and one for its folder. Use the exact connection and folder ids
returned by authenticated discovery; placeholders below describe the shape,
not values to copy:

```json
{
  "bindings": [
    {
      "id": "Binding_Connection",
      "name": "<connector> connection",
      "displayName": "<discovered account name>",
      "type": "string",
      "elementId": "Task_SendMessage",
      "default": "<connection id>",
      "resource": "Connection",
      "resourceKey": "<connection id>",
      "propertyAttribute": "ConnectionId"
    },
    {
      "id": "Binding_Folder",
      "name": "FolderKey",
      "type": "string",
      "elementId": "Task_SendMessage",
      "default": "<folder key>",
      "resource": "Connection",
      "resourceKey": "<connection id>",
      "propertyAttribute": "folderKey"
    }
  ]
}
```

The renderer deduplicates Connection resources by `resourceKey` and writes
their complete records to `bindings_v2.json`. Reusing one connection across
several activities still requires only one resource record, while each
activity may have its own element-scoped binding pair.

## Embedded subprocess and error boundary

`subProcess` owns nested `nodes` and `flows`:

```json
{
  "kind": "subProcess",
  "id": "SubProcess_Assess",
  "name": "Assess",
  "nodes": [
    { "kind": "startEvent", "id": "Start_Assess", "name": "Start" },
    {
      "kind": "endEvent",
      "id": "End_AssessError",
      "name": "Backend unavailable",
      "errorRef": "Error_BackendUnavailable"
    }
  ],
  "flows": [
    {
      "id": "Flow_Assess_Error",
      "source": "Start_Assess",
      "target": "End_AssessError",
      "condition": "=js:vars.Var_Severity === \"Sev1\" && !vars.Var_BackendAvailable"
    }
  ]
}
```

Every execution scope must be connected. Give each root or subprocess
`startEvent` exactly one outgoing flow, keep every flow's source and target in
that same scope, and make every node reachable from a start, boundary, or event
subprocess entry. The renderer rejects disconnected scopes because Alpha can
otherwise enter a subprocess, find no schedulable work, complete it without an
incident, and return unset outputs.

Values assigned inside an embedded subprocess are scoped to that subprocess.
When later root workstreams or public outputs need them, add a
`BPMN.Variables` mapping on the subprocess itself and map each value explicitly
from `=vars.<stable-id>` back to the root variable. A structurally valid file
without this scope bridge can complete while its root outputs remain unset.

That subprocess mapping is a **normal-completion bridge**, not an error payload.
When an error end terminates the subprocess, Alpha does not apply its normal
output mapping, and the matching parent boundary cannot read the terminated
child scope. If the boundary path must retain a child-computed business result,
model that explicitly in parent scope. Prefer a visible exclusive gateway plus
`BPMN.Variables` assignment tasks that re-establish each allowed result from
parent-visible inputs/state. Alternatively, compute and retain the required
state in the parent before entering the subprocess. Do not rely on a
child-scope "checkpoint" mapping or on an undocumented error payload.

The interrupting boundary is a root sibling:

```json
{
  "kind": "boundaryEvent",
  "id": "Boundary_AssessError",
  "name": "Backend unavailable",
  "attachedTo": "SubProcess_Assess",
  "cancelActivity": true,
  "errorRef": "Error_BackendUnavailable"
}
```

An error end should have one visibly guarded incoming flow. Merge multiple
eligible routes before the complete error guard. Declare the exact error-end id
under `constraints.errorEnds.allowedIds`, map it to this boundary under
`matchingBoundaryById`, and give both elements the same `errorRef`. Never use an
untyped catch-all boundary to stand in for a requested matching error.

Before authoring, list every variable that the approved design says qualifies
each error route under `requiredGuardReferencesById`. Use the semantic variable
name or its stable id; the rendered guard must visibly reference the stable
`vars.<id>` form for every listed variable. Do not leave this map empty when an
error route is qualified by availability, severity, eligibility, or another
approved condition. This constraint proves reference presence, not boolean
polarity or the complete business expression, so review those semantics
separately.

## Sequential multi-instance

Add `loop` to a task or subprocess:

```json
{
  "loop": {
    "sequential": true,
    "collection": "=vars.Var_Attachments"
  }
}
```

For a multi-instance task, read the current item with the documented
`iterator.item` expression and omit `item`; emitting an `inputElement` alias on
a task-level marker leaves the runtime `iterator` null. For a multi-instance
subprocess, bind
`item: "iterator[0]"`. Direct body activity mappings may use
`=iterator[0].item`. A nested ScriptTask must instead receive that expression
through a typed named `args` property (for example,
`"currentItem":"=iterator[0].item"`) and read `currentItem`; do not pass
`"iterator":"=iterator"` and expect a populated global inside the nested
script.
Per-iteration task outputs are marker records, not an implicit scalar
process-level result. For a subprocess marker, declare a custom output on the
subprocess and target a scoped `Collection{T}` variable; the engine aggregates
one value per completed iteration in marker order. A separate reducer after
the marker can then read that completed collection. If no marker output is
needed, a reducer after a sequential task marker may instead read the original
input collection for a deterministic property of the final input item.

Use all three parts of the subprocess-output contract together:

```json
{
  "direction": "internal",
  "id": "Var_ProcessedNames",
  "name": "processedNames",
  "type": "Collection{string}",
  "elementId": "SubProcess_CopyItems",
  "custom": true
}
```

```json
{
  "kind": "subProcess",
  "id": "SubProcess_CopyItems",
  "loop": {
    "sequential": true,
    "collection": "=vars.Var_Items",
    "item": "iterator[0]"
  },
  "mapping": {
    "serviceType": "BPMN.Variables",
    "outputs": [
      {
        "name": "itemName",
        "type": "string",
        "var": "Var_ProcessedNames",
        "source": "=vars.Var_ItemResult.itemName",
        "custom": true
      }
    ]
  }
}
```

Do not substitute a JSON-schema `array` variable or omit either `custom: true`
or the marker's `elementId`; those shapes do not declare an Alpha
multi-instance marker aggregate. The renderer rejects such partial contracts.

## Required review

After rendering:

1. Parse the XML.
2. Audit the rendered source against the approved design: exact ScriptTask
   count/responsibilities, visible policy predicates and tokens, decision-gateway
   counts, error guards, mappings, and loops. Confirm that sibling exclusive
   guards cannot both be true. Do not use a default branch to conceal a named
   business value or predicate that the user expects to audit.
3. Trace every path to each root end and confirm that every declared public
   output is explicitly assigned on every completing path. Do not rely on an
   implicit type default. Use visible Variables tasks for neutral initial values
   or assign the neutral value on each applicable branch.
4. Run `uip maestro bpmn validate <file.bpmn> --output json`.
5. Pack when requested.
