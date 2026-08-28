# BPMN runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in [the generated API](api.md).

## Events and timers

<!-- RULE:bpmn.event.payload-live -->
- Connector event payloads and timer firing are runtime facts. Static validation
  proves the declaration, not that a tenant subscription fires.

## HTTP and Orchestrator work

<!-- RULE:bpmn.orchestrator.names -->
- Published work is addressed by name and folder. Queue items require a folder;
  live execution is the evidence that the resource exists and is runnable.

<!-- RULE:bpmn.runtime.metadata -->
- `metadata.*` values are empty in local `flow-debug`. Use literals or `vars.*`
  when an offline behavior check must observe the value.

## Human task outcomes

<!-- RULE:bpmn.hitl.output-map -->
- Map any decision used by later routing through `outputs`; the typed platform
  output is not populated by the local runtime. Exercise each important outcome.

<!-- RULE:bpmn.hitl.default-path -->
- With no injected outcome, local debug takes the gateway default. Choose that
  path deliberately and use `--hitl-response` to verify non-default outcomes.

## Connectors and bindings

<!-- RULE:bpmn.connector.bindings -->
- Keep connection and folder values symbolic in TypeScript and resolve them from
  `bindings.json`. Only a live run proves those environment bindings.

<!-- RULE:bpmn.activity.escape-hatch -->
- Use `.activity(...)` for a registry type with no typed method only after reading
  its exact registry shape. Prefer a typed method when one exists.

## Brownfield editing

<!-- RULE:bpmn.brownfield.merge -->
- For a targeted edit, decompile the original, compile a baseline before editing,
  compile the edit, then merge with `--baseline`. A bare recompile rewrites
  untouched elements and drops original layout.

<!-- RULE:bpmn.brownfield.format -->
- Format after adding elements that need diagram shapes. Avoid formatting a
  metadata-only edit because it replaces preserved geometry.

## Packaging and layout

<!-- RULE:bpmn.package.derived -->
- Treat project metadata as derived from the BPMN. `project.uiproj` and
  `operate.json` use the bare filename; `entry-points.json` adds `#<start-id>`;
  `package-descriptor.json` uses a top-level `content` array.

  Before `.startEvent('<start-id>')`, declare
  `.metadata({ entryPointId: '<stable-unique-id>' })`. Compilation puts that value
  on the root start event, which is what the package generator uses to discover
  the entry point. Then generate the files from the built BPMN:

  ```sh
  uip maestro bpmn update-metadata Demo/Demo.bpmn --output-dir Demo
  ```

  For `Demo.bpmn` with root start event `start`, the minimal derived values are:

  ```jsonc
  // project.uiproj
  { "name": "Demo", "main": "Demo.bpmn", "designOptions": { "projectType": "ProcessOrchestration" } }
  // operate.json
  { "main": "Demo.bpmn", "contentType": "ProcessOrchestration" }
  // entry-points.json
  { "entryPoints": [{ "filePath": "/content/Demo.bpmn#start", "input": [], "output": [] }] }
  // bindings_v2.json
  { "version": "2.0", "resources": [] }
  // package-descriptor.json
  { "content": ["content/Demo.bpmn", "content/bindings_v2.json", "content/entry-points.json", "content/operate.json"] }
  ```

  Inspect every generated metadata file against this contract. In particular,
  `entry-points.json.entryPoints` must be non-empty and reference the built BPMN
  plus its start id. If it is empty, do not hand-write the JSON: add/fix the
  builder's `.metadata({ entryPointId: ... })`, rebuild, and rerun
  `update-metadata`. A successful `update-metadata --dry-run` only proves agreement
  with that command's output; it does not prove the entry point was discovered.

<!-- RULE:bpmn.layout.separate -->
- Compile emits semantic XML. Run `uip maestro bpmn format` only when a canvas
  layout is required.

## Product boundary

<!-- RULE:bpmn.validation.layers -->
- TypeScript checks call shape, `bpmn check` checks graph semantics, and
  `uip maestro bpmn validate` checks the compiled product contract. A live run
  is still required for tenant resources and runtime outcomes.
