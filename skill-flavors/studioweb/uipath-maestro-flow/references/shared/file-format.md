<!--skill-flavor:flow-file-location-intro:start-->
The `.flow` file is a JSON document at `/solution/<ProjectName>/new.flow` — the entrypoint `uip flow init` seeds. It is the **only file you should edit** — other generated files will be overwritten.
<!--skill-flavor:flow-file-location-intro:end-->

<!--skill-flavor:flow-format-version-source:start-->
**Top-level `version`** = workflow file-format version. **Preserve the exact value the `uip flow init` scaffold writes into `new.flow`** (`1.9` today) — do not hand-pick, hardcode, or downgrade it. It is not a semver string; the schema gates on an exact literal for the current file-format version, so an older value (e.g. `"1.0"`, `"1.0.0"`) that worked for a legacy parser will fail for a new flow. Read the value from the scaffolded `new.flow` rather than remembering it.
<!--skill-flavor:flow-format-version-source:end-->

<!--skill-flavor:project-structure-scaffold:start-->
## Project structure (generated scaffold)

A fresh `uip flow init <ProjectName>` project contains only:

```
/solution/<ProjectName>/
├── .project/               # host metadata
├── new.flow                # ← edit this
└── project.uiproj          # { "ProjectType": "Flow", "Name": "<ProjectName>", ... }
```

After the first debug or publish the host adds `entry-points.json`, `new.bpmn`, `operate.json`, `package-descriptor.json`, `bindings_v2.json`, `simulations.json`, and an `evals/` folder (plus a `<uuid>/` folder per inline agent). Never hand-edit those files, and never treat their absence on a fresh project as an error.
<!--skill-flavor:project-structure-scaffold:end-->

<!--skill-flavor:edge-id-ncname-gotcha:start-->
> **Gotcha**: `targetPort` is required. Omitting it produces `[error] [edges[N].targetPort] Invalid input: expected string, received undefined` at validate time.
>
> **Gotcha**: the source field is `sourcePort`, not `sourceHandle`. If you write `sourceHandle`, validation fails with `[error] [edges[N].sourcePort] Invalid input: expected string, received undefined` — the path identifies the offending edge entry exactly.
>
> **Gotcha — edge `id` MUST start with a letter (XML NCName).** Never use a bare UUID or any id with a leading digit (`"12bd09dd-…"`, `"1edge-start"`). Edge ids become BPMN `<bpmn:incoming>/<bpmn:outgoing>` IDREFs; a leading digit makes the converter silently drop those references while still emitting the `sequenceFlow`, so `flow validate` passes and the file saves — but the engine cannot traverse: the run reports **Completed having executed only the start node**, every output null. Use descriptive ids (`e-<source>-<target>`, e.g. `e-start-agent`); prefixing a letter (`e12bd09dd-…`) also works. Same rule applies to node ids.
<!--skill-flavor:edge-id-ncname-gotcha:end-->

<!--skill-flavor:error-edge-add-example:start-->
```bash
# Confirm the node supports error handling
uip maestro flow registry get <node-type> --output json --output-filter "Node.SupportsErrorHandling"

# Add an outgoing edge with sourcePort: "error"
uip maestro flow edge add /solution/<ProjectName>/new.flow <actionNodeId> <errorHandlerId> \
  --source-port error --target-port input --output json
```
<!--skill-flavor:error-edge-add-example:end-->

<!--skill-flavor:minimal-example-version-source:start-->
Keep the `id` and `entryPointId` the `uip flow init` scaffold wrote into `new.flow`. When you need a fresh UUID (a second trigger, a new subflow), generate it with `node -e "console.log('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return (c==='x'?r:(r&3|8)).toString(16)}))"` — the Studio Web shell has no `crypto` module and no `uuidgen`. UUIDs apply ONLY to the top-level flow `id` and `entryPointId`. **Node and edge ids are NOT UUIDs** — they must start with a letter (see the Edge gotcha above). Keep top-level `version` exactly as scaffolded — never hand-pick it (see [Top-level structure](#top-level-structure)).
<!--skill-flavor:minimal-example-version-source:end-->

<!--skill-flavor:entry-points-lifecycle:start-->
`entry-points.json` declares the flow's external interface (input/output schemas and trigger entry points). The host creates and regenerates it on debug or publish; it is absent on a fresh project — never create or edit it.
<!--skill-flavor:entry-points-lifecycle:end-->

<!--skill-flavor:bindings-missing-debug-failure:start-->
**Why this is required.** The definition's `model.context[].value` fields are placeholders of the form `<bindings.{name}>` — deliberately invalid as runtime expressions, so they can't be confused with one. Before the BPMN is emitted, the runtime rewrites each placeholder to `=bindings.<id>` by finding a workflow-level binding with `(resourceKey, name)` matching the node's manifest `model.bindings.resourceKey` + the placeholder name. Without matching entries in top-level `bindings[]`, `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder" even though `uip maestro flow validate` passes.
<!--skill-flavor:bindings-missing-debug-failure:end-->

<!--skill-flavor:connector-binding-file-location:start-->
When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. This is configured in `/solution/<ProjectName>/bindings_v2.json`, written by `uip maestro flow node configure`.
<!--skill-flavor:connector-binding-file-location:end-->
