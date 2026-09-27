# BPMN runtime decisions

This reference contains only choices that types and static validation cannot
make from syntax alone. Exact signatures remain in the generated API.

## Variables and the process contract

<!-- RULE:bpmn.variables.public-scope -->
- Declare a process's public contract with `.input()` and `.output()`, not `.var()`:
  the compiler scopes a top-level input to the manual start event and a top-level
  output to the end event whose mapping writes it (`elementId`), which is where the
  canvas declares them and where a grader of the process contract reads them. A
  `.var()` is internal, process-level state. Name an `elementId` only to scope a
  variable to a specific element yourself.

<!-- RULE:bpmn.variables.read-inputs-directly -->
- A script or expression reads a public input as `vars.<id>` directly; the runtime
  seeds every declaration by id. The start-event mapping that bridges each input into
  an internal variable is the canvas's spelling, not a requirement.

<!-- RULE:bpmn.variables.input-name -->
- Input values are matched to declarations by display `name` when a run starts, so an
  input given a `name` (`.input('amount', 'number', { name: 'Amount' })`) is supplied
  under `Amount`. Leave `name` off unless the caller's key is meant to differ from the id.

## Events and timers

<!-- RULE:bpmn.event.payload-live -->
- Connector event payloads and timer firing are runtime facts. Static validation
  proves the declaration, not that a tenant subscription fires.

<!-- RULE:bpmn.event.net-scope -->
- An event sub-process catches only failures raised in the container it sits directly in.
  Declared at process level it ends the whole run on the first failure; declared inside a multi-instance sub-process it ends only that iteration.
  Place `.eventSubProcess()` in the scope whose failure it should absorb.

<!-- RULE:bpmn.event.error-context -->
- The engine surfaces a failed element's error under the capital-`Error` key with lowercase fields (`code`, `message`, `detail`, `category`, `status`, `traceId`, `response`, `element`).
  `.eventSubProcess({ error: true })` captures it on its start event by default, into `vars.<net>_Error` — a per-net id, which is how the designer names one: every error capture in the measured exports has a unique id with the display name `Error`, and the bare `vars.Error` appears in none. So a net called `failures` reads `vars.failures_Error.<field>` with nothing more written; `errorVar` names it something else and `errorVar: false` omits the capture.
  The platform validator needs the declaration: a `vars.<id>` read with no captured variable is `VARIABLE_DOES_NOT_EXIST`, in a net or anywhere else. Note the runtime resolves `vars.<id>` in ONE flat scope whatever a declaration's `elementId` says, so two captures cannot share an id — that is why the default is per-net.
  A boundary handler captures nothing by default; there `errorVar` is what makes the error readable.

<!-- RULE:bpmn.event.non-interrupting-path -->
- A non-interrupting boundary handler runs beside a token that still reaches the next step, so its path must end on its own; rejoining the main path would run everything after it twice.
  The builder refuses a non-interrupting handler path left open.

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

<!-- RULE:bpmn.connector.folder-companion -->
- A `folderKey` binding is the companion of a connection, not a resource of its
  own: its `resourceKey` is the connection's key and only its `default` is the
  folder key. That is how the platform resolves the connection, and `validate`
  reports `MISSING_BINDING` for a folder binding keyed by the folder. Declare the
  pair once — `.binding(c, { resource: 'Connection', propertyAttribute:
  'ConnectionId', value })` and `.binding(f, { resource: 'Connection',
  propertyAttribute: 'folderKey', value })` — and read both from the same node
  (`connection: '=bindings.c'`, `folderKey: '=bindings.f'`); the compiler keys the
  folder by that connection, and `check` warns `FOLDER_BINDING_KEYED_BY_FOLDER` /
  `FOLDER_BINDING_UNPAIRED` when it cannot.

<!-- RULE:bpmn.connector.data-service -->
- Data Fabric (Data Service, connector `uipath-uipath-dataservice`) records and
  file fields are `.dataService(id, { entity, connection, folder, op, … })`, one of
  eight operations: `create`, `update`, `get`, `query`, `delete`, `downloadFile`,
  `uploadFile`, `deleteFile`. It writes the `Intsvc.ActivityExecution` node the
  way the platform's own tools do and needs no connector library or `prepare`
  step. The response lands in `<id>_response` and the error payload in
  `<id>_Error`, both declared for you — read the created record's id as
  `=vars.<id>_response.Id`. Map results onto process outputs on the end event
  (`payload: { type: 'BPMN.Variables', outputRows: [{ name, type, var, source:
  '=vars.<id>_response' }] }`). Do not hand-fill
  `.activity('Intsvc.ActivityExecution', …)` for these operations: the library
  ships one Data Service operation, so `.connector()` cannot author the rest, and a
  hand-filled node gets `objectName`, the parameter targets and the folder binding
  wrong in ways `validate` does not report. `examples/ContractRegistry.bpmn.ts` is
  the full lifecycle.

<!-- RULE:bpmn.connector.parameter-rows -->
- A connector's path and query parameters are one `uipath:input` row each, under
  the library's own parameter name and tagged `target="path"` / `target="query"`;
  the request body is the one json `target="body"` row. `.connector()` and
  `.dataService()` write that. Through `.activity()`, an undeclared scalar input is
  written as a `type="string"` attribute and a structured one as a json body, the
  key as its target; when a row's target is not its name — a query parameter — spell
  it out with `inputRows: [{ name, type, target, value }]` instead of `inputs`.

## Registry extension types

<!-- RULE:bpmn.activity.escape-hatch -->
- Use `.activity(id, 'Type.Name', opts)` for any registry extension type with no
  typed method. Prefer a typed method when one exists.

<!-- RULE:bpmn.activity.discover-type -->
- Find the type name with `uip maestro bpmn registry search <term> --output json`,
  then `registry get <Type.Name> --output json` to read its context and input
  fields. The SDK's typed methods cover only the types in its committed snapshot,
  so a type absent from them is not evidence the platform lacks it — ask the
  registry before concluding a node cannot be authored.

<!-- RULE:bpmn.activity.registry-freshness -->
- `registry search` and `registry get` answer from a local cache that does not
  refresh itself. Run `uip maestro bpmn registry pull --force` first whenever a
  type may be newer than that cache, or a real type reads as missing.

<!-- RULE:bpmn.activity.inline-spec -->
- A type the registry does not describe at all (`registry get` answers "Extension
  type not found") is still emittable: pass its emission spec inline,
  `.activity(id, 'Type.Name', { spec, context, inputs })`, where `spec` is a
  `RegistryTypeSpec` — the BPMN element and `uipath:*` tag, the context fields
  with their types and defaults, the payload `inputPattern`, and the output row.
  The spec is used as is, in place of the snapshot and the tenant. `decompile`
  cannot recover it, so keep it in the source.

<!-- RULE:bpmn.activity.offsnapshot-resolve -->
- You do not have to transcribe the shape by hand: a type outside the SDK's
  snapshot is resolved from the registry at compile time. The build warns that it
  needed a tenant and names the snapshot refresh — report that warning rather
  than suppressing it, because until the snapshot is refreshed that project no
  longer compiles offline.

## Brownfield editing

<!-- RULE:bpmn.brownfield.merge -->
- For a targeted edit, decompile the original, compile a baseline before editing,
  compile the edit, then merge with `--baseline`. A bare recompile rewrites
  untouched elements and drops original layout.

<!-- RULE:bpmn.brownfield.nested-style -->
- `bpmn decompile --style nested` lifts an import's boundary events, gateways and event sub-processes into the nesting constructs only where the lifted source builds the very same graph, and prints why each region it left flat stayed flat.
  A flow id that is not `Flow_<source>_<target>` keeps its region flat; the graph, its ids and `merge` are unaffected either way, so the choice is about the source you read and edit, not the artifact.

<!-- RULE:bpmn.brownfield.format -->
- Format after adding elements that need diagram shapes. Avoid formatting a
  metadata-only edit because it replaces preserved geometry.

## Contract metadata

<!-- RULE:bpmn.metadata.case-management -->
- A process-level `uipath:caseManagement` marker is distinct from a typed
  `Orchestrator.StartCaseMgmtProcess` or `Orchestrator.StartCaseMgmtProcessAsync`
  call activity. When a contract or fixture explicitly requires that marker,
  author it with synthetic content through
  `.metadata({ caseManagement: { version: 'v1', value: '{"mode":"preserve-only"}' } })`.
  A case-process call does not emit or replace the marker.

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
