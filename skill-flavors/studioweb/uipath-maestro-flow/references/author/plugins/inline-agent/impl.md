<!--skill-flavor:inline-agent-scaffold-command:start-->

`<FlowProjectDir>` = `/solution/<FlowProject>` = `CurrentProject.AbsolutePath`. This form runs the real CLI in Studio Web (it is not intercepted) and creates the inline-agent resource inside the Flow project.
<!--skill-flavor:inline-agent-scaffold-command:end-->

<!--skill-flavor:inline-agent-unknown-field-names:start-->
Connector-trigger output fields (e.g. email `subject`/`from`/`body`) aren't in the registry — only knowable after a real run. Author best-guess `{{input.<node>__output__<field>}}` paths with the matching `binding`/`inputSchema` key, **ask the user to confirm before the first `uip flow debug`** (don't invent field names silently), and correct the tokens + `contentTokens` mirrors after the first run.
<!--skill-flavor:inline-agent-unknown-field-names:end-->

<!--skill-flavor:inline-agent-type-shape-antipattern:start-->
- **Declared `type` must match the bound node's real output shape, in BOTH `agentInputVariables[].type` and `inputSchema`.** The runtime strict-validates `JobArguments` before the model runs: a list bound to an `object`-typed key faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` (incident `170002`, `"Input should be a valid dictionary … input_type=list"`), and both `flow validate` and `agent validate` still report `Valid`. **Data Service query-entity-records returns an array. A script-built value has the shape the script returns — `.map()` returns array, never object.** For an array, write `{"type": "array", "items": {"type": "object"}}` in `inputSchema.properties.<key>` and `"type": "array"` on the matching `agentInputVariables[]` entry — both, or startup validation still faults. The registry won't settle it — connector nodes declare `output.type: "object"` with no schema — so bind the leaf (`=$vars.crmLookup1.output[0].accountTier`) or read the shape from one `uip flow debug` run (if it prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer instead).
<!--skill-flavor:inline-agent-type-shape-antipattern:end-->

<!--skill-flavor:inline-agent-resource-matrix:start-->
| Kind | Edge source port | Node type | `resource.json` discriminator | Needs a solution resource? | `resource.json` reference (uipath-agents) |
|------|------------------|-----------|-------------------------------|----------------------------|--------------------------------------------|
<!--skill-flavor:inline-agent-resource-matrix:end-->

<!--skill-flavor:inline-agent-discover-uuid:start-->
# (the Studio Web shell has no UUID command and node has no crypto module)
RES=$(node -e "console.log('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return (c==='x'?r:(r&3|8)).toString(16)}))")
<!--skill-flavor:inline-agent-discover-uuid:end-->

<!--skill-flavor:inline-agent-refresh-resources:start-->
### 4. Refresh, validate, check solution resources
<!--skill-flavor:inline-agent-refresh-resources:end-->

<!--skill-flavor:inline-agent-refresh-resources-2:start-->
```bash
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow \
  --bindings-target "/solution/<FlowProject>/bindings_v2.json" --output json
uip agent validate "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json
# All kinds EXCEPT built-in tools: the referenced resource must be on the open solution's Resources panel
uip solution resources list --kind Process --output json   # --kind App for an escalation app; `uip solution resources --help` for the other kinds
# if it is missing: `uip solution resources add` (see `--help`) or the designer's Resources panel
```

- **Process tools / context / escalation** resolve through `bindings_v2.json` (process / index / App binding). Pass `--bindings-target /solution/<FlowProject>/bindings_v2.json` on refresh so the binding is written into the flow project. `uip solution resources refresh` is unavailable in Studio Web (it needs a local `.uipx`): instead make sure the referenced resource appears in `uip solution resources list --kind <Kind> --output json` (add it with `uip solution resources add` or the designer's Resources panel if missing), then run `uip flow debug`. Do not hand-edit `bindings_v2.json` — refresh regenerates it.
- **Built-in tools** carry `referenceKey: null` and `type: "internal"` — no `bindings[]`, no solution resource.
<!--skill-flavor:inline-agent-refresh-resources-2:end-->

<!--skill-flavor:inline-agent-refresh-validate-commands:start-->
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json

# 1b. For tool-bearing inline agents, refresh with --bindings-target to propagate tool bindings:
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow \
  --bindings-target "/solution/<FlowProject>/bindings_v2.json" --output json

# 2. Validate the inline agent (read-only schema check)
uip agent validate "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json

# 3. Validate the flow
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
<!--skill-flavor:inline-agent-refresh-validate-commands:end-->

<!--skill-flavor:inline-agent-older-cli:start-->
The CLI version is fixed by the Studio Web host and cannot be probed or updated. If its validator still rejects absent prompt keys with `[REQUIRED_FIELD] "systemPrompt" is required`:

1. Add minimal placeholder `inputs.systemPrompt` / `inputs.userPrompt` strings — **only** after validate rejects the absent keys. Never use `""`; empty strings fail the same check.
2. Run `uip flow debug` and read its `Execution trace:` section. `JobArguments` must carry your bound inputs, not `{"input":""}`. If the run prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer and read the trace there.
3. If `JobArguments` is `{"input":""}`, that CLI also carries the converter prune (`@uipath/flow-converter` 0.25.1+): the placeholder text references no input, so the converter drops every `agentInputVariables[]` entry. No node edit fixes this — the placeholders satisfy the old validator and break the wiring at the same time. Report the CLI gap to the user; do not ship a workaround.
<!--skill-flavor:inline-agent-older-cli:end-->

<!--skill-flavor:inline-agent-debug-table:start-->
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR derived files (`entry-points.json`, `bindings_v2.json`) are stale, OR the node carries no `inputs.systemPrompt` and Studio Web's node form validates the field | Set prompts in `agent.json`, re-run `uip agent refresh --inline-in-flow` to regenerate derived files, then `uip agent validate --inline-in-flow` to check — see `uipath-agents` skill. For the third cause: keep the keys off, set real prompts in `agent.json`, re-run `uip agent refresh --inline-in-flow`, and reload the designer tab so the canvas hydrates the form from the sidecar |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, or the process is not on the open solution's Resources panel | Re-run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` to propagate bindings, then `uip agent validate --inline-in-flow` to check schema, then confirm the process appears in `uip solution resources list --kind Process --output json` (add it with `uip solution resources add` if missing), then `uip flow debug` |
| `bindings_v2.json` is empty or missing tool bindings | Tool bindings were not propagated to the flow project level, or a later tool overwrote the file | Re-run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` after all flow node and edge edits are complete. Refresh is the verb that writes the file — do not hand-edit it |
| Agent tool (process / agent / api / processOrchestration) cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched tool-node `inputs.source` / `resource.json` id, the resource missing from the open solution's Resources panel, or missing project-level `bindings_v2.json` | Add the resource bindings from the tool definition, keep the tool node's `inputs.source` equal to the resource UUID, run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` to write bindings, then `uip agent validate --inline-in-flow` to check, then make sure the resource is listed by `uip solution resources list --kind <Kind> --output json` (add it if missing) |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | They belong only to standalone agent projects, but `/solution` rejects `rm`/`mv` so you cannot remove them from the shell: ask the user to delete them in the Studio Web file explorer, or re-run `uip agent init … --inline-in-flow` to get a fresh inline-agent directory and leave those files out |
<!--skill-flavor:inline-agent-debug-table:end-->

<!--skill-flavor:inline-agent-repair-recipes:start-->
Use direct JSON edits for inline-agent graph repairs. The Flow CLI has no node-update command (see [editing-operations-cli.md § Operations Not Supported by CLI](../../editing-operations-cli.md#operations-not-supported-by-cli)), and the inline-agent graph is not a Flow CLI carve-out. If a bulk scripted rewrite is explicitly approved, script it with `jq` or `node` (the Studio Web shell has no `python3`, `yq`, or `sqlite3`): write the script to `/tmp` line by line with `printf '%s\n' … > /tmp/fix.js` (multi-line heredocs get collapsed), write the result to `/tmp`, then `cp` it back over `new.flow` — `/solution` rejects `rm`/`mv`. Otherwise apply the same transformations through `Edit` / `Write`.
<!--skill-flavor:inline-agent-repair-recipes:end-->

<!--skill-flavor:inline-agent-repair-recipes-2:start-->
```bash
uip maestro flow registry get uipath.agent.autonomous --output json > /tmp/registry_response.json
printf '%s\n' \
  'const fs = require("fs");' \
  'const [flowPath, defPath] = process.argv.slice(2);' \
  'const newDef = JSON.parse(fs.readFileSync(defPath, "utf8")).Data.Node;' \
  'const flow = JSON.parse(fs.readFileSync(flowPath, "utf8"));' \
  'const i = flow.definitions.findIndex(d => d.nodeType === "uipath.agent.autonomous");' \
  'if (i >= 0) flow.definitions[i] = newDef;' \
  'for (const node of flow.nodes) {' \
  '  const t = node.type || "";' \
  '  if (t === "uipath.agent.autonomous" || t.startsWith("uipath.agent.resource.")) {' \
  '    const model = node.model || {}; delete node.model;' \
  '    if (typeof model.source === "string") (node.inputs = node.inputs || {}).source = model.source;' \
  '  }' \
  '}' \
  'fs.writeFileSync("/tmp/new.flow", JSON.stringify(flow, null, 2));' \
  > /tmp/fix.js
node /tmp/fix.js /solution/<FlowProject>/new.flow /tmp/registry_response.json
cp /tmp/new.flow /solution/<FlowProject>/new.flow
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```

Same pattern works for any node type — substitute the `nodeType` string in both the `registry get` command and the `findIndex` guard. The `model.source` → `inputs.source` rewrite above is applied to both the inline agent node and every attached resource node (tool, escalation, context) — all of them carry source identity at `inputs.source` and never on an instance `model` block.
<!--skill-flavor:inline-agent-repair-recipes-2:end-->

<!--skill-flavor:inline-agent-repair-recipes-3:start-->
    jq '.nodes[] | select(.type == "uipath.agent.autonomous" or (.type | startswith("uipath.agent.resource."))) | {type, inputsSource: .inputs.source, modelSource: .model.source}' /solution/<FlowProject>/new.flow
<!--skill-flavor:inline-agent-repair-recipes-3:end-->

<!--skill-flavor:inline-agent-repair-recipes-4:start-->
    ```bash
    jq '(.nodes[] | select(.type == "uipath.agent.autonomous" or (.type | startswith("uipath.agent.resource.")))) |= (if .model.source then .inputs.source = .model.source else . end | del(.model))' /solution/<FlowProject>/new.flow > /tmp/new.flow
    cp /tmp/new.flow /solution/<FlowProject>/new.flow
    ```

2. **Subdirectory** — confirm `/solution/<FlowProject>/<projectId>/` exists and contains `agent.json`. If not, re-run `uip agent init "/solution/<FlowProject>" --inline-in-flow --output json` and bind the returned `ProjectId` through `inputs.source`.
<!--skill-flavor:inline-agent-repair-recipes-4:end-->

<!--skill-flavor:inline-agent-repair-recipes-5:start-->
4. **Prompt keys on the flow node** — delete `inputs.systemPrompt` and `inputs.userPrompt` if present. Deleting the keys passes validate; `""` does not. Or run `uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json` — shell-ify strips node prompts. Verify: the agent node instance must contain no `systemPrompt` key. Keep the canonical prompt text in `agent.json`.
<!--skill-flavor:inline-agent-repair-recipes-5:end-->

<!--skill-flavor:inline-agent-release-key-source:start-->
`<release-key>` is the resource's release-key GUID from `uip solution resources list --kind Process --output json` (the row's `key`). `<toolType>` is the built-in's fixed kebab discriminator (e.g. `analyze-attachments`), identical to the `resource.json` `properties.toolType`.
<!--skill-flavor:inline-agent-release-key-source:end-->

<!--skill-flavor:inline-agent-process-tool-shape:start-->
**Process / agent / api / processOrchestration tools** share one shape — use the exact shape in the `uipath-agents` skill: `lowcode/capabilities/process/process.md` § Tool resource.json Shape (read it first). The subtype is the `type` field (§ Subtypes in `process.md`). RPA uses raw .NET arrays (Template A in `solution-files.md`); Agent / API / Process Orchestration use JSON Schema V2 (Template B). Run `uip solution resources list --kind Process --output json` + `uip solution resources get <KEY> --output json` to populate `referenceKey`, `folderPath`, `inputSchema`, `outputSchema` (`--kind` is required — the kindless form is not served by the host and falls through to the browser bundle, which needs a `.uipx`). Inline-in-flow specifics:
<!--skill-flavor:inline-agent-process-tool-shape:end-->
