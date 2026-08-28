# Voice Nodes — Implementation

This plugin covers building the two voice topologies: scaffolding the voice agent's directory, the four node JSON shapes, `callContext` wiring, and what validate/pack/debug enforce. Inline-agent mechanics (the agent subdirectory, `inputs.source`, resource nodes, refresh) are identical to [inline-agent/impl.md](../inline-agent/impl.md) — the voice deltas below are complete on their own; open that file only when the voice agent has tools/contexts/escalations or prompt inputs (the two sections linked from here).

Node type: `uipath.agent.voice`, bound to a local subdirectory via `inputs.source = <projectId>` — the same BPMN contract as the autonomous inline agent. The create-call and end-call nodes serialize to `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` serviceTasks.

## Prerequisite — Scaffold the Voice Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --conversational --output json
```

Same layout as any inline agent (`<FlowProjectDir>/<projectId-uuid>/` with `agent.json`, `flow-layout.json`, `evals/`, `features/`, `resources/`). **Record the returned `ProjectId`** — the voice node's `inputs.source` must match it exactly.

The scaffold is a conversational agent but has **no `settings.voice` block** — adding it is mandatory (next section).

## Configure `agent.json`

`--conversational` already writes everything a conversational agent needs except the voice block (full `agent.json` shape and per-field rules: the `uipath-agents` skill's [`agent-definition.md`](../../../../../uipath-agents/references/lowcode/agent-definition.md)). **`Edit` one key into the existing `settings` object — never `Write` the file.** The fragment below is the key you add, not a document:

```json
"voice": {
  "model": "gemini-3.1-flash-live-preview",
  "maxTokens": 65536,
  "temperature": 0,
  "persona": "Aoede"
}
```

A full-file `Write` of that fragment drops `settings.model`, `settings.engine`, and `metadata.isConversational`. Two of those losses are silent: `flow validate` never reads `settings.engine` (rule 2 below), so the flow validates clean and every call fails.

Those are the current Studio Web defaults. **Nothing validates `model` or `persona`** — `flow validate` only applies the node manifest's bounds to the numbers (`temperature` 0-1, `maxTokens` >= 0), so a made-up model name or a persona that belongs to a different model passes validate and then fails when the call tries to connect. No CLI command lists the accepted values; the voice-settings dropdowns in Studio Web are the only place they are enumerated. `persona` is per-model — the personas offered for one realtime model are not accepted by another.

Field rules:

1. **`settings.voice` is required** — the realtime speech model, its token budget, and the spoken `persona`. This is a *second* model, separate from `settings.model`: `settings.model` is the conversational engine's LLM (reasoning, tool calls); `settings.voice.model` is the realtime audio model.
2. **Leave `settings.engine: "conversational-v1"` and `metadata.isConversational: true` exactly as scaffolded** — both are required at runtime. `flow validate` checks `metadata.isConversational` and errors with `is not a conversational agent` when it is off; a wrong `settings.engine` is *not* caught by validate and surfaces only as a failed call, so do not rely on validation to catch it. Never hand-flip `metadata.isConversational` to repair it; re-scaffold with `uip agent init --inline-in-flow --conversational` (`uipath-agents` critical rule 23).
3. **`outputSchema` is optional** — the scaffold leaves it empty (`{ "type": "object", "properties": {} }`) and a voice agent works that way, because the node already emits three fixed outputs on its own (`uipath__agent_response_messages`, `uipath__voice_call_context`, `uipath__voice_session`). Declare properties only when the flow needs typed data out of the call. Custom fields **merge with** the fixed three rather than replacing them — unlike an autonomous agent, whose typed schema replaces its manifest output. Both kinds land flat at `$vars.<nodeId>.output.<field>`. Keep the node's `inputs.agentOutputVariables[]` in sync (see step 4's sibling contract): Studio Web projects `outputSchema` properties into that array and flushes the array back on save, so a schema authored without it renders an empty Outputs list in the properties panel.
4. Author the system prompt in `messages[0].content` (empty is valid — voice agents have no required prompt field — but a real persona/goal prompt is what makes the call useful). Prompt inputs follow the inline-agent contract unchanged — all five pieces, including the node-side delivery binding:

   - **Delivery** — `inputs.agentInputVariables[]` on the voice node: `{ "id": "start__output__callerName", "type": "string", "binding": "=$vars.start.output.callerName" }`
   - **Contract** — the same key under `agent.json` `inputSchema.properties`
   - **Resolution** — `{{input.start__output__callerName}}` in `messages[].content` (never a bare `$vars.…` — nothing rewrites agent.json prompt text, so it reaches the model literally)
   - **Variable** — when the binding's source is a **trigger**, the field must be declared in `variables.globals[]` as `{ "id": "callerName", "direction": "in", "triggerNodeId": "start" }`. A binding sourced from any other node (a script or connector output) reads that node's own output and declares nothing
   - **Tokens** — rebuild `contentTokens` via `uip agent refresh --inline-in-flow`; never hand-author them

   Omit the Delivery binding and `flow debug` still works (it back-fills from `inputSchema`) while `flow pack` ships empty `JobArguments` — the published call gets no inputs. Full contract: [inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
5. `settings.model`, `maxTokens`, `temperature`, `maxIterations` tune the engine LLM as for any conversational agent (`uip agent model list` for the tenant's models).

## Registry Validation

Read the node definitions during Phase 2 to copy into `definitions[]`. All four voice types ship in the CLI's bundled node registry, so `registry get` answers locally — no `uip login` and no `registry pull` required. Fetch only the three types your topology uses:

```bash
uip maestro flow registry get uipath.agent.voice --output json
uip maestro flow registry get uipath.conversational.voice.end-call --output json
# inbound only:
uip maestro flow registry get core.trigger.voice --output json
# outbound only:
uip maestro flow registry get uipath.conversational.voice.create-outgoing-call --output json
```

`uipath.agent.voice` confirms identically to the autonomous inline agent — ports, `model.source: true` hoisting onto `inputs.source`, and `model.serviceType` / `model.version` — see [inline-agent/impl.md § Registry Validation](../inline-agent/impl.md#registry-validation). Voice adds no port or model field to that set. On the create-call and end-call nodes, confirm `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` as `model.serviceType`. Never hand-write `definitions[]` entries — always copy them from `registry get`.

**`registry get` succeeding does not mean the tenant can place calls.** It answers from the bundled registry, so it succeeds offline and on any tenant. Whether a SIP trunk is provisioned can only be established at deploy/debug time — check with `uip conversational trunks list` rather than treating a clean `registry get` as proof.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Voice nodes are user-owned — author them directly in the `.flow` JSON with `Edit` / `Write` (same rule as the inline autonomous agent; they are not a Flow CLI carve-out).

### The `callContext` wiring rule

The node that originates the call emits `output.callContext`. Bind it into **both** the voice agent and the end-call node, as a structured `jsExpression` binding object (this is the persisted Studio Web shape — not a `=js:` string):

- Inbound: origin is the `core.trigger.voice` node
- Outbound: origin is the `uipath.conversational.voice.create-outgoing-call` node
- `fieldType` is `"object"` on the voice agent and `"string"` on the end-call node (a code-editor text field) — the two values Studio Web persists. Write them as given; do not derive them from the node definition's `inputDefinition` (both properties are declared `object` there). For `type: "jsExpression"` bindings the validator never reads `fieldType` — it only checks that `expression` is non-empty — so neither value can fail validation

### Node JSON — inbound trigger

```json
{
  "id": "incomingCall1",
  "type": "core.trigger.voice",
  "typeVersion": "1.0",
  "display": { "label": "Incoming call", "shape": "circle", "icon": "phoneIncoming" },
  "inputs": { "entryPointId": "<generated-uuid>" }
}
```

`inputs.entryPointId` is a fresh UUID, same convention as other triggers ([shared/file-format.md](../../../shared/file-format.md)). The phone number is bound to the process at deploy time, not in the `.flow`.

### Node JSON — create outgoing call (outbound only)

```json
{
  "id": "createOutgoingCall1",
  "type": "uipath.conversational.voice.create-outgoing-call",
  "typeVersion": "1.0",
  "display": { "label": "Create outgoing call", "icon": "phoneOutgoing" },
  "inputs": {
    "from": "<SIP-trunk-E164-number>",
    "to": { "type": "literal", "expression": "<destination-E164-number>", "fieldType": "string" }
  }
}
```

`from` is a **plain string** (an E.164 number provisioned as a SIP trunk on the tenant); `to` is a literal binding object. Both are required.

`from` comes from the tenant — `uip conversational trunks list --direction outbound --output json` enumerates the trunks it can be, each `phoneNumber` a usable value. `to` comes from the user; it is a destination, not a tenant fact. See [planning.md § Phone Numbers and SIP Trunks](planning.md#phone-numbers-and-sip-trunks).

### Node JSON — voice agent

```json
{
  "id": "voiceAgent1",
  "type": "uipath.agent.voice",
  "typeVersion": "1.0",
  "display": { "label": "Voice agent", "shape": "rectangle", "icon": "phone" },
  "inputs": {
    "source": "<projectId-uuid>",
    "callContext": {
      "type": "jsExpression",
      "expression": "$vars.incomingCall1.output.callContext",
      "fieldType": "object"
    }
  }
}
```

Two inputs when you author the node — `source` and `callContext`. Hand-author nothing else; see § What NOT to Do for the fields that hydrate on their own, and for the Studio-Web-authored flow where they are already populated and must be left in place.

### Node JSON — end call

```json
{
  "id": "endCall1",
  "type": "uipath.conversational.voice.end-call",
  "typeVersion": "1.0",
  "display": { "label": "End call", "icon": "phoneOff" },
  "inputs": {
    "callContext": {
      "type": "jsExpression",
      "expression": "$vars.incomingCall1.output.callContext",
      "fieldType": "string"
    }
  }
}
```

Outbound flows bind from the create-outgoing-call node instead: `$vars.createOutgoingCall1.output.callContext`.

### Wire edges with Edit / Write

The trigger's source port is `output`; every other voice edge leaves `success`; targets are always `input`. Edge object shape: [editing-operations-json.md § Add an edge](../../editing-operations-json.md#add-an-edge).

**Inbound replaces the scaffolded trigger — it does not add beside it.** `flow init` scaffolds `start` / `core.trigger.manual` ([greenfield.md](../../greenfield.md)), and an inbound flow starts from `core.trigger.voice`. Delete the `start` node and any edge referencing it in the same edit that adds the voice trigger; leaving it in ships a two-trigger flow. Same replace-don't-append rule as [brownfield.md](../../brownfield.md)'s "Add a connector trigger" row. Outbound keeps the manual trigger — it is what starts the flow.

Outbound inserts the call node between trigger and agent: `manualTrigger1 (output) → createOutgoingCall1 (input)`, then `createOutgoingCall1 (success) → voiceAgent1 (input)`. Inbound wires straight through: `incomingCall1 (output) → voiceAgent1 (input)`. Tool/context/escalation resource nodes wire to the voice agent's artifact ports exactly as in [inline-agent/impl.md § Adding Resource Nodes](../inline-agent/impl.md#adding-resource-nodes).

## Accessing Output

```javascript
// In a Script node after the voice agent
const session = $vars.voiceAgent1.output.uipath__voice_session;
return { callEnded: session.callEnded, endedBy: session.endedBy };
```

- `$vars.{originNodeId}.output.callContext` — the live-call handle (`type`, `id`, `conversationId`); consumed by the voice agent and end-call bindings
- `$vars.{voiceAgentNodeId}.output.uipath__voice_session` — `callEnded` (bool), `endedBy` (`agent`/`user`/`system`/`error`), `reason`. The same node also emits `uipath__voice_call_context` and `uipath__agent_response_messages`
- `$vars.{voiceAgentNodeId}.output.<field>` — one entry per `agent.json` `outputSchema` property when you declared any (step 3). Flat, alongside the fixed `uipath__*` outputs, never nested under `.content.`
- `$vars.{endCallNodeId}.output.ended` — whether the call was ended
- `$vars.{nodeId}.error` — error details if one of the three action nodes fails (`core.trigger.voice` emits `output` only)

## Validate and Pack

```bash
uip maestro flow format <FlowName>.flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

Voice flows get extra validation on top of the standard checks: the agent directory must exist with a conversational `agent.json` carrying `settings.voice`, both `callContext` bindings must be present, and no voice agent node may sit inside a subflow. Failure modes and fixes are in § Debug.

Packing (`uip maestro flow pack`, or `uip solution pack` — see the operate capability) serializes the voice agent to an `Orchestrator.StartInlineAgentJob` serviceTask that **embeds the complete built agent definition** (`agentDefinition` in the BPMN context: agent.json + resources + features), and sets `runtimeOptions.isConversational: true` in the packed `operate.json`. That embedding is why pack and debug fail early when the agent directory is missing. Pack also re-checks the written BPMN and fails if the embedded definition is absent — a package without it deploys and then drops every call, so this never ships silently.

### Debug covers outbound only

`uip maestro flow debug` **rejects an inbound flow**: only a real call can raise a `core.trigger.voice`, so the run would never advance.

```text
Inbound voice flows cannot be debugged from the CLI.
```

The instructions on that error are the whole inbound test loop — publish, bind a number (§ Bind an Inbound Phone Number), then dial it. Swapping the trigger for a manual one lifts the rejection but leaves the inbound flow itself unexercised.

An **outbound** flow does run under `flow debug`, and it dials for real. The run's `--timeout` window has to outlast the conversation (default: 300 polls × the 2s poll interval = 10 minutes). Get user consent first and confirm the `to` number — the flow **places a real phone call**.

## Bind an Inbound Phone Number

An inbound flow does nothing until a trunk points at its deployed process. Nothing in the `.flow` carries the number — the binding is made against the **release key** after deploy.

> **Confirm with the user before running step 1.** `solution publish` and `solution deploy run` mutate the tenant, and this skill never defaults to an Orchestrator deploy — full flow and the Studio-Web alternative: [operate/ship.md § Path 2](../../../operate/ship.md#path-2--orchestrator-deploy-explicit-only).

```bash
# 1. ship the solution (the flow project alone is not deployable)
uip solution pack "<SolutionDir>" "<OutDir>" --output json
uip solution publish "<OutDir>/<SolutionName>_<version>.zip" --output json
uip solution deploy run --name <DEPLOYMENT_NAME> --folder-name <FOLDER_NAME> \
  --package-name <SolutionName> --package-version <version> \
  --parent-folder-path Shared --output json

# 2. read the release key + folder key back
uip or processes list --folder-path "Shared/<FOLDER_NAME>" --output json   # Key, FolderKey

# 3. point the trunk at it
uip conversational trunks assign <E164-number> \
  --process-key <Key> --folder-key <FolderKey> --yes --output json
```

- `<FOLDER_NAME>` must be identical in step 1's `--folder-name` and step 2's `--folder-path` — deploy creates that folder under `--parent-folder-path`, and step 2 reads the process back out of it. `<DEPLOYMENT_NAME>` is independent and names the deployment only.
- `--process-key` is the **release `Key`** from `or processes list` (a GUID), not the package name and not the process id.
- `--entry-point` is optional and resolves automatically when the flow has exactly one incoming-call entry point — the normal case. Pass it explicitly only for a multi-entry-point package.
- `--yes` is required when the trunk already has a non-null `processKey`; it re-points the number and the previous process stops receiving calls.
- Verify with `uip conversational trunks list --direction inbound --output json` — `processName` should show your process and `entryPoint` should match the `core.trigger.voice` node's `inputs.entryPointId`. A mismatch there means the trunk is bound to a different build.
- To release a number, `uip conversational trunks assign <E164-number> --clear --yes` — after that the number rings nothing. Only run it when the user asks for the number back.

### Shipping an outbound flow

Outbound needs no binding step — `inputs.from` names the trunk directly, so the flow is complete once `flow debug` places its call. Two places it can go from there, both tenant-mutating (consent gate per SKILL.md rule #2):

- **Orchestrator**, to run it on a schedule or trigger it as a process — same `solution pack` → `publish` → `deploy run` sequence as above, minus step 3.
- **Studio Web**, to hand the flow to someone to open in the designer — `uip solution upload "<SolutionDir>"`. Note the `SolutionId` caveat in § Debug if `flow debug` already ran on this project.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate`: `agent.json not found at <path>` | `inputs.source` UUID doesn't match any subdirectory, or the agent directory was never created | Run `uip agent init "<FlowProjectDir>" --inline-in-flow --conversational`, set `inputs.source` to the returned `ProjectId` |
| `flow validate`: `` has no `settings.voice` `` | Scaffolded agent.json was not hand-edited | Add the `settings.voice` block (§ Configure `agent.json`) |
| `flow validate`: `is not a conversational agent` | `metadata.isConversational` is not `true` — usually the agent was scaffolded without `--conversational` | Re-scaffold with `uip agent init --inline-in-flow --conversational` and repoint `inputs.source` — do not hand-flip `metadata.isConversational` (`uipath-agents` critical rule 23) |
| `flow validate`: `[CONVERSATIONAL_VOICE_CALL_CONTEXT_REQUIRED]` (rule `conversational-voice-call-context`) | Voice agent node lacks the `inputs.callContext` binding | Bind `$vars.<originNodeId>.output.callContext` as a `jsExpression` object with `fieldType: "object"` |
| `flow validate` flags the end-call node's call context (rule `conversational-voice-end-call-context`) | End-call node lacks `inputs.callContext` | Same expression as the voice agent, `fieldType: "string"` |
| `flow validate`: `requires a source UUID at inputs.source` | Voice agent node has no `inputs.source` | Set it to the agent directory's UUID |
| `flow validate` / `flow pack`: `voice agent nodes are not supported inside subflows` | The voice agent node was placed in a `core.subflow`. Only top-level voice nodes get an embedded definition, so pack raises the same thing validate does | Move the node to the top-level flow. There is no flag for this and no partial support — a subflow voice agent would ship a serviceTask with no `agentDefinition` |
| `flow debug`: `Inbound voice flows cannot be debugged from the CLI.` | The flow starts from `core.trigger.voice`, which only a real call raises | Not a bug and not fixable locally — publish, bind a number, dial it (§ Bind an Inbound Phone Number). Do not swap in a manual trigger to force a run |
| `flow pack` / `flow debug`: `Missing agent definition for voice agent node …` | Agent directory deleted or moved after validate | Restore `<FlowProjectDir>/<projectId>/agent.json` or fix `inputs.source`; the BPMN is never written without the embedded definition |
| `flow pack` / `flow debug`: `Converted BPMN carries no agentDefinition for voice agent node(s) …` | Different failure from the row above — the agent directory is fine, but the CLI's bundled `@uipath/flow-converter` does not forward `voiceAgentDefinitions` to the BPMN serializer. Pack catches it rather than shipping a package that deploys and drops every call | `uip tools update` to a CLI whose converter supports voice, then re-pack. Nothing in the project can work around an old converter |
| `registry get` reports the voice type not found | The installed CLI predates voice support (the types ship in its bundled registry, so this is a CLI-version problem, not a tenant one) | `uip tools update`; re-run `registry get` |
| `uip conversational trunks …`: `unknown command 'trunks'` (and `uip conversational --help` lists no `trunks`) | The CLI predates the trunk commands. Independent of node support: the voice node types ship in the bundled registry, so authoring, `registry get`, and `validate` all work on a CLI whose `conversational` tool has no `trunks` | Tool packages resolve on the CLI's own `N.Nx` minor line, so `uip tools update` cannot pull a `trunks` that only exists on a later line — the CLI itself has to be on one that ships it (`uip --version`, and `which -a uip` when more than one is installed). A trunk's number and direction flags are also readable from the Phone numbers page. Note a tool's `-dev.<run>` number is a global CI counter, not a per-line one: a tool run number higher than the CLI's says nothing about which line it came from |
| Call never connects on a tenant that packs and deploys fine | No SIP trunk provisioned, or the number lacks the direction your topology needs — not detectable from the CLI at author time | `uip conversational trunks list` to see whether the tenant has any trunk at all. Adding a number, enabling a direction on it, and releasing it are portal-only — send the user to `{baseUrl}/{orgName}/agents_/phone-numbers` (e.g. `https://alpha.uipath.com/conversationalagents/agents_/phone-numbers`). Raise it as an Open Question rather than re-authoring the flow |
| Call connects but the agent is silent / call drops immediately | Package built without the embedded `agentDefinition` (hand-rolled pack pipeline), or `settings.voice` removed after pack | Re-pack with the CLI; verify the staged `.bpmn` has `name="agentDefinition"` on the voice serviceTask |
| Outbound call never dials | `from` is not a SIP trunk number on the tenant, or `to` is malformed, or the trunk exists but is not outbound-enabled | `uip conversational trunks list --direction outbound --output json`; use a number with `outboundEnabled: true` for `from`; `to` must be E.164 in a literal binding. Turning outbound *on* for an existing number is portal-only — the Phone numbers page, `{baseUrl}/{orgName}/agents_/phone-numbers` |
| Inbound number rings but nothing runs | Trunk not bound, bound to a different process, or bound to an older build | `uip conversational trunks list --direction inbound --output json` — check `processName` and that `entryPoint` matches the trigger's `inputs.entryPointId`; re-run `trunks assign` (§ Bind an Inbound Phone Number) |
| `solution deploy run`: `DraftDeploymentHasDifferentPackageVersion` | An earlier failed deploy left a draft under that deployment name, pinned to the version it first tried | Deploy under a new `--name`/`--folder-name`, or clear the stale draft |
| `solution upload`: `Studio Web already has a solution with SolutionId … Refusing to overwrite without --force` | `flow debug` stamped its staging `SolutionId` into the local `.uipx`, so upload now targets that cloud solution | Re-run with `--force` to update that project in place (this discards its Studio Web version history), or remove `SolutionId` from the `.uipx` to upload as a new solution |

## What NOT to Do

- **Do not scaffold a standalone voice agent** — there is no such thing; `uip agent init` without `--inline-in-flow` builds text agents. A voice agent exists only as an inline conversational agent inside a flow project.
- **Do not set an `isVoice` input flag on the node** — deprecated contract. The converter derives voice mode from the `uipath.agent.voice` node type; the `{"isVoice":true}` job body is emitted for you at pack time.
- **Do not hand-author a `model` block, `systemPrompt`/`userPrompt`, or `inputs.voice` on the voice node instance** — author it as a shell carrying `inputs.source` + `inputs.callContext` (plus `inputs.agentInputVariables[]` when the prompt reads flow data — that binding is the node's job, see step 4). Prompts live in the sidecar `agent.json`; flow-core hoists `model.source` onto `inputs.source`; validate/pack hydrate `voice` from `agent.json` `settings.voice`. **A Studio-Web-authored flow is the other case:** self-contained flows embed the agent's config inline, so `inputs.voice.model` / `persona` / `temperature` / `maxTokens` and `inputs.systemPrompt` are legitimately populated there — **leave them alone, never delete them as stray fields**. `uip agent refresh --inline-in-flow` shell-ifies the node back to structural inputs from your sidecar edits — see [inline-agent/impl.md § Refresh and Validate](../inline-agent/impl.md#refresh-and-validate).
- **Do not declare `outputSchema` properties on a voice agent and forget `inputs.agentOutputVariables[]`** — the schema is legal and optional (step 3), but the two are one fact in two places. Author neither, or both. Session data needs no schema: it always arrives at `$vars.<nodeId>.output.uipath__voice_session`.
- **Do not collapse `settings.voice.model` into `settings.model`** — they are two different models (realtime speech vs engine LLM) and both are read.
- **Do not `Write` a whole `agent.json` to add `settings.voice`** — `Edit` the key into the scaffolded file. A full-file write drops `settings.model`, `settings.engine`, and `metadata.isConversational`, and validate catches only the last of the three.
- **Do not leave the scaffolded `core.trigger.manual` in an inbound flow** — `core.trigger.voice` replaces it. Two triggers is not a topology; delete `start` and its edges (§ Wire edges with Edit / Write).
- **Do not put a voice agent node inside a subflow** — only top-level voice nodes get their agent definition embedded at pack time, so both `flow validate` and pack reject one in a `core.subflow`. Keep the whole call — trigger/dial, agent, end-call — in the top-level flow.
- **Do not run `uip maestro flow eval` on a voice flow** — the platform blocks voice agents from eval runs; the CLI rejects it with a clear error.
- **Do not try to `flow debug` an inbound flow, or rewrite it as outbound to get a local run** — the CLI rejects an incoming-call trigger by design (§ Debug covers outbound only). Inbound is tested by publishing, binding a number, and dialing it.
- **Do not hand-write `definitions[]` entries** — copy verbatim from `uip maestro flow registry get <node-type>`.
