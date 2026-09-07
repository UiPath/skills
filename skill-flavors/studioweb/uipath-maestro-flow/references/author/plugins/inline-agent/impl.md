<!--skill-flavor:inline-agent-scaffold-command:start-->
```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

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
| RPA process tool | `tool` (bottom) | `uipath.agent.resource.tool.process.<release-key>` | `type: "process"` | Yes | `lowcode/capabilities/process/process.md` |
| Agent tool | `tool` (bottom) | `uipath.agent.resource.tool.agent.<release-key>` | `type: "agent"` | Yes | `lowcode/capabilities/process/process.md` |
| API workflow tool | `tool` (bottom) | `uipath.agent.resource.tool.api.<release-key>` | `type: "api"` | Yes | `lowcode/capabilities/process/process.md` |
| Process Orchestration tool | `tool` (bottom) | `uipath.agent.resource.tool.processorchestration.<release-key>` | `type: "processOrchestration"` | Yes | `lowcode/capabilities/process/process.md` |
| Built-in tool | `tool` (bottom) | `uipath.agent.resource.tool.builtin.<toolType>` | `type: "internal"` | **No** — self-contained at the agent level | `lowcode/capabilities/built-in-tools/built-in-tools.md` |
| Context (index / RAG) | `context` (bottom) | `uipath.agent.resource.context.index.<index-name>.<index-id>` | `$resourceType: "context"`, `contextType: "index"` | Yes | `lowcode/capabilities/context/index.md` |
| Escalation (HITL) | `escalation` (top) | `uipath.agent.resource.escalation` | `$resourceType: "escalation"` | Yes | `lowcode/capabilities/escalation/escalation.md` |
<!--skill-flavor:inline-agent-resource-matrix:end-->

<!--skill-flavor:inline-agent-discover-uuid:start-->
```bash
# Suffix-bearing kinds (process/agent/api/processorchestration tools, context):
uip maestro flow registry search "<prefix>" --output json   # e.g. "uipath.agent.resource.tool.process"
uip maestro flow registry get "<NodeType>" --output json

# Exact-string kinds:
uip maestro flow registry get uipath.agent.resource.escalation --output json
uip maestro flow registry get "uipath.agent.resource.tool.builtin.<toolType>" --output json

# One resource UUID — used as both inputs.source and the resource.json directory/id
# (the Studio Web shell has no UUID command and node has no crypto module)
RES=$(node -e "console.log('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return (c==='x'?r:(r&3|8)).toString(16)}))")
```
<!--skill-flavor:inline-agent-discover-uuid:end-->

<!--skill-flavor:inline-agent-refresh-resources:start-->
### 4. Refresh, validate, check solution resources

Set prompts in `agent.json` (system + user `messages` with `contentTokens` of `type: "simpleText"` and `rawString`), then:

```bash
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow \
  --bindings-target "/solution/<FlowProject>/bindings_v2.json" --output json
uip agent validate "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json
# All kinds EXCEPT built-in tools: the referenced resource must be on the open solution's Resources panel
uip solution resources list --kind Process --output json   # --kind App for an escalation app; `uip solution resources list --help` for other kinds
# if it is missing: `uip solution resources add` (see `--help`) or the designer's Resources panel
```

- **Process tools / context / escalation** resolve through `bindings_v2.json` (process / index / App binding). Pass `--bindings-target /solution/<FlowProject>/bindings_v2.json` on refresh so the binding is written into the flow project. `uip solution resources refresh` is unavailable in Studio Web (it needs a local `.uipx`): instead make sure the referenced resource appears in `uip solution resources list` (add it with `uip solution resources add` or the designer's Resources panel if missing), then run `uip flow debug`. Do not hand-edit `bindings_v2.json` — refresh regenerates it.
- **Built-in tools** carry `referenceKey: null` and `type: "internal"` — no `bindings[]`, no solution resource.
- **Verify both refresh and validate report `"resources": N` where N > 0.** If either shows `"resources": 0`, the `resource.json` is malformed or missing required fields — fix it and re-run before proceeding.

For agent.json prompt configuration and solution resource mechanics, see the `uipath-agents` skill (`lowcode/capabilities/inline-in-flow/inline-in-flow.md`).
<!--skill-flavor:inline-agent-refresh-resources:end-->

<!--skill-flavor:inline-agent-refresh-validate-commands:start-->
```bash
# 1. Refresh the inline agent (writes entry-points.json and bindings_v2.json)
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json

# 1b. For tool-bearing inline agents, refresh with --bindings-target to propagate tool bindings:
uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow \
  --bindings-target "/solution/<FlowProject>/bindings_v2.json" --output json

# 2. Validate the inline agent (read-only schema check)
uip agent validate "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json

# 3. Validate the flow
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```
<!--skill-flavor:inline-agent-refresh-validate-commands:end-->

<!--skill-flavor:inline-agent-older-cli:start-->
The CLI version is fixed by the Studio Web host and cannot be probed or updated. If its validator still rejects absent prompt keys with `[REQUIRED_FIELD] "systemPrompt" is required`:

1. Add minimal placeholder `inputs.systemPrompt` / `inputs.userPrompt` strings — **only** after validate rejects the absent keys. Never use `""`; empty strings fail the same check.
2. Run `uip flow debug` and read its `Execution trace:` section. `JobArguments` must carry your bound inputs, not `{"input":""}`. If the run prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer and read the trace there.
3. If `JobArguments` is `{"input":""}`, that CLI also carries the converter prune (`@uipath/flow-converter` 0.25.1+): the placeholder text references no input, so the converter drops every `agentInputVariables[]` entry. No node edit fixes this — the placeholders satisfy the old validator and break the wiring at the same time. Report the CLI gap to the user; do not ship a workaround.
<!--skill-flavor:inline-agent-older-cli:end-->

<!--skill-flavor:inline-agent-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate` reports `[SCHEMA_ERROR] System prompt is required` or `[REQUIRED_FIELD] systemPrompt` / `userPrompt` required | The node carries **empty-string** prompt keys, the `inputs.source` UUID is missing, or the inline agent subdirectory cannot be found | Delete `inputs.systemPrompt` / `inputs.userPrompt` (delete the keys — `""` fails), or run `uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json` to strip them. Set `inputs.source` to the inline agent UUID, and verify `<FlowDir>/<projectId>/agent.json` exists |
| Debug faults with `JobArguments {"input":""}` — `AGENT_STARTUP.INPUT_VALIDATION_ERROR` `"Field required"` per `inputSchema` key (incident `170002` family); **expected, not yet observed:** `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` when the schema marks nothing required | Prompt keys on the agent node — the converter drops every `agentInputVariables[]` entry the node prompt text does not reference. Stub text references nothing, so every entry goes. Discriminator: the entries already use `binding:` | Delete `inputs.systemPrompt` and `inputs.userPrompt` from the node — delete the keys, because empty strings fail `flow validate`. Or run `uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json` — shell-ify strips node prompts. Verify: the agent node instance must contain no `systemPrompt` key. See § Wiring Flow Variables into Agent Prompts |
| `inputs.source` UUID does not match any subdirectory | Wrong source value, or folder renamed | Set `inputs.source` to the exact UUID of the inline agent directory |
| Flow runs a different agent than expected | `inputs.source` points to a stale/leftover inline agent dir | Check subdirectory names — only one inline agent dir should correspond to each agent node |
| `Orchestrator.StartAgentJob` error at runtime | Stale instance `model` fields override the inherited inline-agent definition | Remove the inline-agent node's instance `model` block and keep the registry definition's `model.serviceType: "Orchestrator.StartInlineAgentJob"` in `definitions[]` |
| Studio Web reports "System prompt is required" | Inline agent's `agent.json.messages[]` has empty `content`, OR derived files (`entry-points.json`, `bindings_v2.json`) are stale, OR the node carries no `inputs.systemPrompt` and Studio Web's node form validates the field | Set prompts in `agent.json`, re-run `uip agent refresh --inline-in-flow` to regenerate derived files, then `uip agent validate --inline-in-flow` to check — see `uipath-agents` skill. For the third cause: keep the keys off, set real prompts in `agent.json`, re-run `uip agent refresh --inline-in-flow`, and reload the designer tab so the canvas hydrates the form from the sidecar |
| Studio Web debug: "Could not find process for tool" | Flow project's `bindings_v2.json` is missing the tool's process binding, or the process is not on the open solution's Resources panel | Re-run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` to propagate bindings, then `uip agent validate --inline-in-flow` to check schema, then confirm the process appears in `uip solution resources list --kind Process --output json` (add it with `uip solution resources add` if missing), then `uip flow debug` |
| `bindings_v2.json` is empty or missing tool bindings | Tool bindings were not propagated to the flow project level, or a later tool overwrote the file | Re-run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` after all flow node and edge edits are complete. Refresh is the verb that writes the file — do not hand-edit it |
| Agent tool (process / agent / api / processOrchestration) cannot resolve at runtime | Missing top-level `bindings[]` entries, mismatched tool-node `inputs.source` / `resource.json` id, the resource missing from the open solution's Resources panel, or missing project-level `bindings_v2.json` | Add the resource bindings from the tool definition, keep the tool node's `inputs.source` equal to the resource UUID, run `uip agent refresh --inline-in-flow --bindings-target /solution/<FlowProject>/bindings_v2.json` to write bindings, then `uip agent validate --inline-in-flow` to check, then make sure the resource is listed by `uip solution resources list` (add it if missing) |
| `inputs.agentProjectId` unrecognized | Wrong field name | Use `inputs.source` — `agentProjectId` is not valid for inline agents |
| Inline agent rejected by `uip agent validate` | `entry-points.json` or `project.uiproj` present inside the inline agent dir | Delete those files — they belong only to standalone agent projects |
| Folder name is human-readable instead of UUID | Folder renamed after scaffolding | Rename to the original `projectId` UUID — the folder name must match `inputs.source` and the `projectId` field inside `agent.json` |
| Agent runs but returns empty `output.content` | Missing or malformed `contentTokens` in `agent.json` | Rebuild `messages[].contentTokens` using `{ "type": "simpleText", "rawString": "..." }` entries; see `uipath-agents` for detail |
| `flow validate` passes, debug Completes, but the `out` global (e.g. `emailBody`) is null | Typed agent output read with a `.content.` wrapper — `agentOutputVariables:[{content}]` + End `=js:$vars.<node>.output.content.<field>` — but typed fields surface flat at `output.<field>` | List each field in `agentOutputVariables[]` (`{id:"subject"},{id:"body"}`) and map End to `=js:$vars.<node>.output.<field>` (no `.content.`). See § Wiring Agent Output Into Flow Outputs. |
| `agent validate` flags `Expected type "simpleText" but got "text"` | Hand-edited `contentToken` written with `type: "text"` | Re-run `uip agent refresh` — it regenerates `contentTokens` from `content` (correct `simpleText`/`variable` types). Don't hand-edit the token. See § The `content` ↔ `contentTokens` mirror invariant. |
| `agent validate` flags `Expected "input.X" but got "{{input.X}}"` | Hand-edited `variable` token has the braces/extra spaces in its `rawString` | Re-run `uip agent refresh` to regenerate the tokens from `content` (brace-free `rawString`) — don't hand-fix it. See § The `content` ↔ `contentTokens` mirror invariant. |
| `agent validate` flags `contentTokens has N entries but content requires M. Rebuild contentTokens to match content.` | `content` and `contentTokens` drifted (e.g. tokens edited without `content`, or vice versa) | Re-run `uip agent refresh` to regenerate `contentTokens` from `content`. If the prompt itself is wrong, fix `content` first, then refresh. See § The `content` ↔ `contentTokens` mirror invariant. |
| Prompt shows literal `{{input.X}}` at runtime | `inputSchema.properties` missing the referenced key (`flow validate` flags this — run it) | Add the `<trigger>__output__<var>` key to `inputSchema`. |
| `flow validate` passes but debug faults `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` (literal `input.<key>`) | Node `agentInputVariables` uses `value:` instead of `binding:` (or is missing) → empty `JobArguments` | Set `binding:"=$vars.<trigger>.output.<var>"` on the node entry; ensure the trigger global is declared (`direction:"in"`). If `binding:` is already correct, check for prompt keys on the node — see the prune row. |
| Debug faults `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` "Template placeholders detected instead of actual values" — and the node *does* have `agentInputVariables[]` | Entries use `value: "=js:$vars…"` (Studio Web's canvas form) instead of `binding`; the converter only reads `binding`, so `JobArguments` are empty | Rename `value` → `binding` on each entry and strip the `=js:` prefix: `{ "id": "<key>", "binding": "=$vars.<trigger>.output.<var>" }`. If `binding:` is already correct, check for prompt keys on the node — see the prune row. See § Wiring Flow Variables into Agent Prompts. |
<!--skill-flavor:inline-agent-debug-table:end-->

<!--skill-flavor:inline-agent-repair-recipes:start-->
Use direct JSON edits for inline-agent graph repairs. The Flow CLI has no node-update command (see [editing-operations-cli.md § Operations Not Supported by CLI](../../editing-operations-cli.md#operations-not-supported-by-cli)), and the inline-agent graph is not a Flow CLI carve-out. If a bulk scripted rewrite is explicitly approved, script it with `jq` or `node` (the Studio Web shell has no `python3`, `yq`, or `sqlite3`): write the script to `/tmp` line by line with `printf '%s\n' … > /tmp/fix.js` (multi-line heredocs get collapsed), write the result to `/tmp`, then `cp` it back over `new.flow` — `/solution` rejects `rm`/`mv`. Otherwise apply the same transformations through `Edit` / `Write`.

### Replace a definition entry

Use when the `definitions[]` entry for a node type is wrong, stale, or hand-written. The fix is always: re-fetch from the registry, splice into `definitions[]` matching on `nodeType`, then keep the node instance minimal.

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

### Resolve a `[REQUIRED_FIELD] systemPrompt is required` validator error

Current CLIs report the same fault as `[SCHEMA_ERROR] System prompt is required`. Two causes. (a) Empty-string prompt keys on the node. (b) The validator's hydration through `inputs.source` short-circuited — missing UUID, missing subdirectory, or empty `agent.json` messages. Absent prompt keys pass on a current CLI; if they do not, see § Refresh and Validate § Older CLI. Check in order:

1. **UUID at `inputs.source`** — the `projectId` UUID must be set at `inputs.source`. Diagnose:

    ```bash
    jq '.nodes[] | select(.type == "uipath.agent.autonomous" or (.type | startswith("uipath.agent.resource."))) | {type, inputsSource: .inputs.source, modelSource: .model.source}' /solution/<FlowProject>/new.flow
    ```

    If a stale flow has the UUID at `model.source` on the inline agent node **or any attached resource node** (tool, escalation, context), move it to `inputs.source` and remove the instance `model` block:

    ```bash
    jq '(.nodes[] | select(.type == "uipath.agent.autonomous" or (.type | startswith("uipath.agent.resource.")))) |= (if .model.source then .inputs.source = .model.source else . end | del(.model))' /solution/<FlowProject>/new.flow > /tmp/new.flow
    cp /tmp/new.flow /solution/<FlowProject>/new.flow
    ```

2. **Subdirectory** — confirm `/solution/<FlowProject>/<projectId>/` exists and contains `agent.json`. If not, re-run `uip agent init "/solution/<FlowProject>" --inline-in-flow --output json` and bind the returned `ProjectId` through `inputs.source`.

3. **Prompts in `agent.json`** — set `messages[0].content` (system) and `messages[1].content` (user) to real prompts before validate. Rebuild `messages[].contentTokens` to match — `[{ "type": "simpleText", "rawString": "<your prompt text>" }]` per message.

4. **Prompt keys on the flow node** — delete `inputs.systemPrompt` and `inputs.userPrompt` if present. Deleting the keys passes validate; `""` does not. Or run `uip agent refresh "/solution/<FlowProject>/<projectId>" --inline-in-flow --output json` — shell-ify strips node prompts. Verify: the agent node instance must contain no `systemPrompt` key. Keep the canonical prompt text in `agent.json`.
<!--skill-flavor:inline-agent-repair-recipes:end-->
