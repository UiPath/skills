# Planning Implementation

Use this reference for pass 2 of BPMN authoring: fill the model-owned UiPath extension XML after the BPMN skeleton has been confirmed.

## Pass 2 goal

Pass 2 makes the confirmed skeleton locally coherent for validation and packaging:

- Root variables and scoped subprocess variables.
- Entry point IDs on runnable root start events.
- Variable mappings on tasks, events, scripts, subprocesses, and ends.
- Resource bindings for documented non-Integration-Service service shells.
- Script task metadata and input/output mapping.
- Retry, error mapping, loop metadata, transaction marker, and tags when specified.
- Draft Integration Service intent handed to CLI enrichment.

## Fill order

1. **Entry points** - add `uipath:entryPointId` to root start events that should be runnable.
2. **Variables** - add root `uipath:variables` for entry point inputs, process globals, outputs, and schemas; add subprocess variables only when scope requires them.
3. **Mappings** - add `uipath:mapping` where values move between variables, task inputs, task outputs, and end outputs.
4. **Bindings** - add root `uipath:bindings` only for documented non-Integration-Service resources or placeholder-safe binding shapes.
5. **Task shells** - add documented non-Integration-Service `uipath:activity` or `uipath:event` metadata when the task wrapper and service type contract are known. Use [supported-elements.md](supported-elements.md) and [task-recipes/](task-recipes/) before writing XML.
6. **Scripts** - add BPMN script CDATA, `uipath:scriptVersion`, merged `args` input, schema, and outputs.
7. **Runtime behavior metadata** - add retry, error mapping, loop characteristics, transaction marker, or tags only when user intent is explicit.
8. **CLI-owned enrichment** - hand Integration Service activities/triggers and generated package metadata to the CLI.

## Variables

Root variables define the public entry point contract and process-wide data. Use stable IDs and preserve existing IDs during brownfield edits unless renaming is required.

- `uipath:input` is read-only entry input.
- `uipath:inputOutput` can be updated during execution.
- `uipath:output` is emitted by entry point outputs.
- `elementId` scopes entry inputs to the root start event that owns the entry point.
- JSON schema variables store schema content in CDATA.
- Do not move a variable between root and subprocess scope without checking every mapping and expression.

## Bindings

Root bindings describe resources that packaging turns into `bindings_v2.json`.

- Use expressions in service context values: `=bindings.<binding id>`.
- Keep `resourceKey`, `resourceSubType`, and `propertyAttribute` placeholder-safe unless a public-safe value is provided.
- Do not paste connection IDs, folder keys, URLs, queue IDs, release keys, or tenant-specific names.
- Let the CLI generate or enrich binding resources for Integration Service and dynamic schemas.

## Expressions

- Use a leading `=` where Maestro expects an expression.
- Treat strings without `=` as literals.
- Avoid assignment operators in condition, skip, and mapping expressions where fields require read-only expression evaluation.
- Keep gateway condition expressions on sequence flows, not on the gateway itself.
- Keep script source in BPMN `script` CDATA with `scriptFormat="JavaScript"`.

## Non-Integration-Service task shells

The model may fill documented non-Integration-Service shells only when the required fields are known and public-safe. Examples include variable mappings, script tasks, Orchestrator process/agent/API workflow starts, business rules, queue item creation, HITL, message events, and supported agent execution shells.

Wrapper choices are not optional:

- RPA, agent, API workflow, A2A, and create-and-wait queue work use `bpmn:serviceTask`.
- Queue create uses `bpmn:sendTask`.
- Business rules use `bpmn:businessRuleTask`.
- HITL uses `bpmn:userTask`.
- Agentic and case-management process calls use `bpmn:callActivity`.
- Script work uses `bpmn:scriptTask`.

For every shell:

- Include the correct `uipath:type` service type and version only when documented.
- Add required `uipath:context` fields.
- Add `uipath:input` bodies with CDATA for JSON payloads.
- Add `uipath:output` mappings to declared variables.
- Validate that each binding or variable reference resolves.

## Integration Service handoff

For `Intsvc.*` activities and triggers, pass 2 should stop at the enrichment boundary unless registry-backed CLI output is available.

The CLI must own:

- Connector key, operation/event, object, and version metadata.
- Selected connection binding and generated resource metadata.
- Trigger property bindings.
- Dynamic input/output schemas and generated output metadata.
- `bindings_v2.json` entries.

If the CLI cannot enrich yet, leave a clear blocker in the summary and do not treat the project as ready for Operate.

## Done state

Pass 2 is done when model-owned XML is complete, Integration Service enrichment is either complete or explicitly blocked, generated package files are current or intentionally absent, and validation has been run.
