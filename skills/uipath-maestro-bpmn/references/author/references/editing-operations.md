# Editing Operations

Use this reference to choose how to change existing BPMN projects while preserving source clarity and imported extension XML.

## Tool selection ladder

1. **Reviewable XML edit** - default for `.bpmn` source changes: elements, flows, diagrams, variables, mappings, scripts, and documented non-Integration-Service extensions.
2. **CLI enrichment or generation** - use for Integration Service activities/triggers, generated schemas, bindings resources, entry points, packaging metadata, and project scaffolding when commands are available.
3. **Advisory placeholder** - use when the requested executable metadata is CLI-owned but enrichment tooling or user resource selection is unavailable.
4. **Bulk rewrite** - use only when most of the BPMN source is being replaced, and preserve or explicitly account for existing extension payloads first.

Do not patch generated JSON files as the primary way to fix source behavior.

## Add a task or event

1. Add the BPMN element with a stable ID and public-safe name.
2. Add incoming and outgoing sequence flow references on the element.
3. Add sequence flow elements in the owning process or subprocess scope.
4. Add or update BPMN DI shape and edge waypoints.
5. Add pass 2 extension XML only after the shape is confirmed.

## Delete a node

1. Identify incoming and outgoing flows, attached boundary events, data associations, mappings, and diagram shapes.
2. Decide whether neighboring nodes should reconnect or whether the branch should be removed.
3. Remove orphaned sequence flows and BPMN DI edges.
4. Remove or preserve extension data intentionally; do not delete unknown `uipath:*` payloads unless normalizing explicitly.
5. Recheck entry point variables, output mappings, and binding references.

## Insert a gateway

1. Split the existing sequence flow into incoming and outgoing flows.
2. Add gateway conditions to outgoing flows when it is a decision split.
3. Set a default flow when a fallthrough route exists.
4. Add a matching join only when branches actually need synchronization.
5. Add gateway shape and all edge waypoints.

## Move logic into a subprocess

1. Move only elements that share a valid scope.
2. Recreate incoming/outgoing flow boundaries with legal subprocess connections.
3. Add a subprocess shape and, when nested content must render in Studio Web, a second diagram plane for the subprocess.
4. Move variables into subprocess scope only when every mapping and expression remains valid.
5. Preserve existing extension payloads and migration metadata.

## Add an entry point

1. Use a root-level start event.
2. Add `uipath:entryPointId` with a generated stable unique value.
3. Add input variables with `elementId` matching the start event.
4. Ensure outputs are declared as root output variables and mapped by reachable end events.
5. Validate generated `entry-points.json` when package files exist.

## Add a variable or mapping

1. Choose root or subprocess scope deliberately.
2. Add the variable before adding mappings or expressions that reference it.
3. Use CDATA for JSON schema bodies.
4. Add `uipath:mapping` or service outputs that reference declared variables.
5. Validate all output targets and entry point schema extraction.

## Add an Integration Service activity or trigger

1. Add the standard BPMN wrapper and diagram geometry in pass 1.
2. Record connector, operation/event, object, filters, required inputs, connection selection, and outputs.
3. Use CLI enrichment for `uipath:activity` or `uipath:event` payloads, bindings, and schemas.
4. Treat missing enrichment as a blocker for upload/debug/publish/run.

## Brownfield preservation checklist

- Preserve unknown `uipath:*` extension elements.
- Preserve `uipath:migrationVersion` and tags.
- Preserve generated JSON for comparison unless regeneration is requested.
- Preserve private values already present locally, but never copy them into docs, fixtures, or commit messages.
- Report suspected private values in files intended for commit.
