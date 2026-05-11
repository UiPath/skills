# Brownfield Authoring

Use this journey when inspecting or editing an existing Maestro BPMN Process Orchestration project.

## Steps

1. Inventory local files: BPMN source, project metadata, generated JSON, and any package output.
2. Identify the primary `.bpmn` source file and preserve imported extension XML.
3. Parse the BPMN mentally before editing: definitions, root process, diagrams, IDs, variables, bindings, entry points, and service extensions.
4. Classify requested edits as model-owned XML, CLI-owned enrichment, generated package metadata, or cloud lifecycle.
5. If topology changes, run **pass 1** from [planning-arch.md](planning-arch.md): edit the standard BPMN skeleton first, including IDs, flows, events, gateways, subprocess scopes, and diagram geometry.
6. Summarize the changed shape and ask for operator confirmation when the edit changes the process path, entry points, subprocess boundaries, or error handling.
7. Run **pass 2** from [planning-impl.md](planning-impl.md): update model-owned variables, bindings, mappings, entry point IDs, scripts, and non-Integration-Service extension XML.
8. For Integration Service changes, follow [plugins/integration-service/impl.md](plugins/integration-service/impl.md) and use CLI enrichment where available.
9. Reconcile IDs, sequence flows, gateway defaults, boundary attachments, scoped variables, binding references, and diagram geometry.
10. Run local validation from [validation.md](validation.md).
11. Summarize whether generated JSON needs regeneration before Operate.

## Preservation rules

- Preserve unknown `uipath:*` extension elements.
- Preserve existing `uipath:migrationVersion` values.
- Preserve tags unless the user asks to remove them.
- Preserve generated JSON for comparison, but do not treat it as authoritative over BPMN.
- Preserve Integration Service payloads as imported unless CLI enrichment is explicitly updating them.
- Preserve stable element IDs when possible; ID churn makes generated JSON and runtime diagnostics harder to compare.

## Editing operation guide

Use [editing-operations.md](editing-operations.md) for common source mutations:

- Add, delete, or reconnect nodes.
- Insert gateways.
- Move logic into a subprocess.
- Add entry points.
- Add variables and mappings.
- Add Integration Service placeholders.

## Red flags

- BPMN imports without any diagram.
- A diagram plane references a missing process, collaboration, or subprocess.
- Rendered elements lack shapes or waypoints.
- Entry point variables reference the wrong start event.
- Context values reference missing bindings.
- Integration Service elements contain hand-authored connection details.
- Generated JSON contains private tenant data in a file intended for commit.
- A topology edit rewrites UiPath extension XML that was unrelated to the request.
