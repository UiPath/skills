# Inline Agent Node — Implementation

The inline agent is authored **entirely in the `.flow` file**. This plugin covers the agent node itself — prompts, model config, schemas, identity, wiring in/out, validation — plus the derived-sidecar contract and legacy migration. Resource capabilities (tools, context, escalation) get their own files under `capabilities/` (landing per roadmap milestone; see [§ Resource Nodes](#7-resource-nodes)).

Mandatory constraints: [critical-rules.md](critical-rules.md). Prompt quality: [prompting/autonomous-agent-prompting-guide.md](prompting/autonomous-agent-prompting-guide.md). Model choice: [model-selection-guide.md](model-selection-guide.md).

## 1. The Contract — the Node IS the Agent Definition

- **The `.flow` node is the source of truth.** `uipath.agent.autonomous` embeds the full agent definition in `inputs`: prompts, model, generation settings, guardrails, typed outputs, identity.
- **Embed trigger:** a **string** `inputs.systemPrompt` or `inputs.userPrompt` marks the node self-contained — tooling and the canvas then never read the sidecar. Structural-only inputs (`source` + variables arrays, no string prompts) mark a **legacy shell** (see [§ 11 Legacy Flows](#11-legacy-flows--detect-and-migrate)).
- **The GUID subdirectory is derived, never authored.** The canvas regenerates `<GUID>/agent.json` + `resources/` + `features/` from the `.flow` on every save; packaging synthesizes the same bytes. Never create or edit sidecar files. Sole exception: `<GUID>/evals/` is authored via `uip maestro flow eval` — the eval tree is never derived.
- **No `uip agent` lifecycle verbs.** No `init`, `refresh`, or `validate` (with or without `--inline-in-flow`) — there is no agent project to scaffold or refresh. The single `uip agent` verb this plugin uses is `uip agent model list --output json` (model discovery; works from the flow project directory).
- **Valid under both rollout states.** The embedded node shape is byte-identical to an un-flushed brand-new canvas agent, so a self-contained `.flow` is correct whether or not the tenant's canvas has the self-contained-flow flag enabled.

## 2. Agent Node `inputs` Spec

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `source` | string | Yes | Lowercase UUIDv4 **you mint** — see [planning.md § Identity](planning.md#identity--mint-the-uuids-yourself). Becomes the derived folder name + packaging identity. |
| `systemPrompt` | string | Yes | Real structured prompt — the embed trigger. Plain string with `{{ $vars.* }}` tokens; never `contentTokens`. |
| `userPrompt` | string | Yes | Task + data references. Same token form. |
| `model` | string | Yes | Discovered model name — see [model-selection-guide.md](model-selection-guide.md). Never the scaffold default. |
| `mode` | string | No | `standard` (default) \| `advanced`. |
| `temperature` | number | No | 0 for extraction/classification/judgment; raise only when variation is wanted. |
| `maxTokenPerResponse` | number | No | ≤ the chosen model's `MaxTokens` cap. Derived to `settings.maxTokens`. |
| `maxIterations` | number | No | Default 25. `≤5` only tool-less single-shot; a looping agent needs a prompt stop rule, not a higher cap. |
| `guardrails` | array | No | Author `[]`; guardrail authoring doc lands per roadmap milestone. |
| `agentInputVariables` | array | Yes | **Author `[]` — entries are derived** (see § 4). |
| `agentOutputVariables` | array | Yes | Typed output declarations `{id, type, description?}` — see § 5. Default `[{"id": "content", "type": "string"}]` is the untyped fallback; declare real fields. |
| `byomConnectionId` / `byomConnectorKey` | string | No | Bring-your-own-model connection pair; omit otherwise. |

Quality obligations (build-time minimum; the *how* is in the linked guides):

1. **Override the model** — discover with `uip agent model list --output json`, pick the newest GA model for the task class ([model-selection-guide.md](model-selection-guide.md)).
2. **Write a real system prompt** — bounded role, per-tool call/stop criteria, output contract, grounding ([prompting guide](prompting/autonomous-agent-prompting-guide.md#1-system-prompt-skeleton)). Every tool/context handle needs a call cap plus a decide-anyway fallback, or the agent re-queries until the runtime kills it (`AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS` — surfaced under incident `170002`, the generic job-failure envelope):

   ```text
   Call <toolName> at most <N> times (N ≤ 3 for a single decision). After the last call, stop retrieving and decide with the evidence you already have.
   If the retrieved content does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every declared output field. Never end a run without a determination.
   ```

3. **Declare typed `agentOutputVariables`** — not a bare `content` string — so downstream nodes consume fields, not prose.

## 3. Manifest and `definitions[]` Contract

Every node instance `(type, typeVersion)` needs a matching `definitions[]` entry `(nodeType, version)` — an exact match on both; multiple versions of one nodeType legally coexist in a file.

- Copy the definition **verbatim** from `uip maestro flow registry get <nodeType> --output json` (`Data.Node` or the top-level node object, depending on CLI version). Set the instance `typeVersion` to the copied definition's exact `version`.
- **Definitions are canvas-owned:** the canvas rebuilds `definitions[]` wholesale from its live manifest registry on every save (in-solution entries with `model.projectId` keep their file-provided `inputDefinition`/`outputDefinition`/`form`). Hand-edits to a definition don't survive — repairs mean re-fetching from the registry (§ 13), not patching.
- **Definitions-or-nothing law:** a resource node whose `(type, typeVersion)` has no `definitions[]` entry does not hydrate, fails `flow validate` (the error names the exact `registry get` command), and silently vanishes from the derived agent and the package.

### Add the node

Root document requirements: `"version": "1.9"` floor, root `id` = UUID. The instance carries only per-instance data (`inputs`, `outputs`, `display`) — BPMN type, `serviceType` (`Orchestrator.StartInlineAgentJob`), and context templates come from the definition. **Never write an instance `model` block.**

```json
{
  "id": "triageAgent",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.3",
  "display": { "label": "Email Triage Agent" },
  "inputs": {
    "source": "3f2c9a1e-7b4d-4e2a-9c1f-5a8d0b6e4c21",
    "systemPrompt": "You are a support-email triage classifier for a SaaS product. <full structured prompt per the prompting guide>",
    "userPrompt": "Classify the following email.\n\nSubject: {{ $vars.start.output.subject }}\n\n{{ $vars.start.output.body }}",
    "model": "anthropic.claude-sonnet-4-6",
    "temperature": 0,
    "maxTokenPerResponse": 4096,
    "maxIterations": 10,
    "guardrails": [],
    "agentInputVariables": [],
    "agentOutputVariables": [
      { "id": "category", "type": "string", "description": "One of: billing, technical, sales, other" },
      { "id": "needsHuman", "type": "boolean", "description": "true if the email requires human review" }
    ]
  },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Also:

- Instance `outputs` = the `error` entry only (`source: "=Error"`). No `output` entry — only source-carrying outputs persist.
- `layout.nodes.<id>` optional — `uip maestro flow format` back-fills position/size and generates `variables.nodes[]` entries.
- Wire sequence edges: upstream `output` → agent `input`; agent `success` → downstream `input`:

```json
{ "id": "e_start_agent", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "triageAgent", "targetPort": "input" }
```

```json
{ "id": "e_agent_end", "sourceNodeId": "triageAgent", "sourcePort": "success", "targetNodeId": "done", "targetPort": "input" }
```

Add/edit procedures shared with all nodes: [editing-operations.md](../../editing-operations.md). The inline-agent graph is not a Flow CLI carve-out — author nodes, edges, variables, layout directly in the `.flow` JSON with `Edit` / `Write`.

## 4. Wire Flow Data Into Prompts

Prompts are **plain strings** carrying canvas-form tokens (spaced braces):

- `{{ $vars.<nodeId>.output.<field> }}` — upstream node output
- `{{ $metadata.<field> }}` — flow metadata

Write the token where the value belongs; done. Tooling scans the cluster's prompts (and connected resources' inputs) for `$vars.*`/`$metadata.*` refs and **derives** `agentInputVariables[]` entries + the runtime input schema from them.

- **`agentInputVariables[]` is derived — author `[]`.** The canvas removed its manual editor. Hand-authored entries win on id collision but are pruned when no live ref points at them; derived entries persist in the `.flow` after a canvas/debug touch (each has `id` = flattened path, `binding: "=$vars.<path>"`) — leave them alone.
- **Trigger-globals prerequisite:** a `{{ $vars.<triggerId>.output.<field> }}` reference resolves only if the field is declared in `variables.globals[]` as a trigger-associated input — `direction: "in"`, `triggerNodeId: "<triggerId>"`:

  ```json
  { "id": "invoiceNumber", "direction": "in", "type": "string", "triggerNodeId": "start" }
  ```

  `flow validate` does not check that a referenced path exists — an undeclared field passes validate, then yields an empty value at run time.
- Each referenced `$vars.<node>.output.<field>` must name a real node `id` with an edge path reaching the agent node. Full expression contract: [../../../../shared/node-output-wiring.md](../../../../shared/node-output-wiring.md); trigger-global mechanics: [../../../../shared/variables-and-expressions.md](../../../../shared/variables-and-expressions.md) (§ Input associated with a trigger), [editing-operations-json.md § Add a workflow variable](../../editing-operations-json.md#add-a-workflow-variable).

### When the source field name is unknown at authoring time

Connector-trigger output fields (e.g. email `subject`/`from`/`body`) aren't in the registry — only knowable after a real run. Author best-guess `{{ $vars.<node>.output.<field> }}` paths, **ask the user to confirm before upload** (don't invent field names silently), and correct after the first run.

### Anti-patterns

- **Never `{{input.<flat>}}` in `.flow` prompts.** That namespace exists only in the *derived* `agent.json`; `{{ $agent.<flat> }}` only in derived resource files. Porting sidecar prompt text verbatim brings these along — the runtime then renders the literal token. `flow validate` cannot catch this (prompts are opaque strings to it).
- **Never `contentTokens`** — a derived agent.json artifact. `.flow` prompts are plain strings.
- **Never `derivedInputDefinition`** — a BPMN-emission artifact that can leak into canvas-saved files after debug/publish. Never hand-write it.
- **Never ExpressionValue objects in prompts** — `systemPrompt`/`userPrompt` are plain strings, not `{type, expression}` wrappers.

## 5. Wire Agent Output Out

Typed outputs declared in `inputs.agentOutputVariables[]` surface **flat** at `$vars.<nodeId>.output.<field>` — there is no `.content.` wrapper. `$vars.<nodeId>.output.content` exists only when no typed outputs are declared.

To expose a field as a flow output:

1. Declare the field: `agentOutputVariables: [{ "id": "determination", "type": "string" }, …]` — one entry per field, NOT a single `content` object.
2. Declare a `direction: "out"` global in `variables.globals[]`.
3. Map it on **every reachable End node**: `"determination": { "source": "=js:$vars.triageAgent.output.determination" }`.

**Anti-pattern:** `agentOutputVariables: [{ "id": "content", "type": "object" }]` paired with End `=js:$vars.<node>.output.content.<field>`. Validate passes, debug Completes, flow output is **null** — typed fields are flat at `output.<field>`.

## 6. Registry Validation

Validate the node type against the registry during Phase 2 to confirm current product state:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json
```

Confirm:

- Handles: `input` (target), `success`/`error` (source), artifact `tool`/`context`/`escalation`
- `model.source: true` — the definition-level identity declaration; on the instance the identity lives at `inputs.source` (never an instance `model` block)
- `model.serviceType` — `Orchestrator.StartInlineAgentJob`
- Required inputs (`systemPrompt`, `userPrompt`, `model`) and `inputDefaults` — the current manifest's field set is authoritative over this doc

## 7. Resource Nodes

Resource nodes carry their **full config in their own `inputs`** (plus their own `inputs.source` UUID) and attach via exactly ONE artifact edge: agent `sourcePort ∈ {tool, context, escalation}` → resource `targetPort: "input"`, depth 1, one agent per resource.

Universal recipe, all kinds: discover the node type (`registry search` prefix → `registry get`), mint a lowercase UUID for `inputs.source`, add the node with full `inputs`, copy its definition verbatim into `definitions[]`, wire the one artifact edge, validate. The **definitions-or-nothing law** (§ 3) applies with force here: a resource node without its definition silently vanishes from the derived agent and the package.

| Kind | Edge source port | Node type pattern | Capability doc |
|------|------------------|-------------------|----------------|
| Process-family tool (RPA / agent / API / process orchestration) | `tool` | `uipath.agent.resource.tool.<process\|agent\|api\|processorchestration>.<release-key>` | lands per roadmap milestone |
| Built-in tool | `tool` | `uipath.agent.resource.tool.builtin.<toolType>` | lands per roadmap milestone |
| IS connector tool | `tool` | `uipath.agent.resource.tool.connector.<key>.<name>` | lands per roadmap milestone |
| Context (index / RAG) | `context` | `uipath.agent.resource.context.index.<name>.<id>` | lands per roadmap milestone |
| Escalation (HITL) | `escalation` | `uipath.agent.resource.escalation.<variant>` | lands per roadmap milestone |

Until a kind's capability doc lands, pin its exact `inputs` shape from a canvas-authored flow or the manifest's `inputDefaults` — do not guess field sets. Process-family and connector tools additionally require top-level `bindings[]` rows mirroring the definition's `model.bindings`; built-ins require none.

## 8. Worked Example — Trigger → Agent → End

Complete single-agent flow (definitions abbreviated). Two trigger inputs, two typed outputs.

```json
{
  "version": "1.9",
  "id": "b7e2f4d0-1a2b-4c3d-8e9f-0a1b2c3d4e5f",
  "name": "DisputeTriage",
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0",
      "display": { "label": "Manual trigger" },
      "inputs": { "entryPointId": "cd3aa493-b55d-4226-b548-156213beb7c3", "isDefaultEntryPoint": true },
      "outputs": { "output": { "type": "object", "description": "Data passed when manually triggering the workflow.", "source": "null", "var": "output" } }
    },
    {
      "id": "disputeAnalyst",
      "type": "uipath.agent.autonomous",
      "typeVersion": "1.3",
      "display": { "label": "Dispute Analyst" },
      "inputs": {
        "source": "e5715a3f-0d31-4ad8-9c70-91df180760e6",
        "systemPrompt": "You are a billing-dispute analyst for a SaaS product. Determine whether each dispute is justified.\n\nScope:\n- In scope: analyzing the dispute and producing a determination with rationale.\n- Out of scope: contacting the customer or issuing refunds — only analyze.\n\nOutput:\n- Return every declared output field. determination MUST be one of: justified, unjustified, needs-review.\n- Never invent invoice details not present in the input.\n\nUncertainty:\n- If the dispute description is empty or unintelligible, set determination=\"needs-review\" and say why in rationale.",
        "userPrompt": "Analyze this billing dispute.\n\nInvoice: {{ $vars.start.output.invoiceNumber }}\nDispute: {{ $vars.start.output.disputeDescription }}\n\nReturn the determination and a one-sentence rationale.",
        "model": "anthropic.claude-sonnet-4-6",
        "temperature": 0,
        "maxTokenPerResponse": 4096,
        "maxIterations": 5,
        "guardrails": [],
        "agentInputVariables": [],
        "agentOutputVariables": [
          { "id": "determination", "type": "string", "description": "justified | unjustified | needs-review" },
          { "id": "rationale", "type": "string", "description": "One sentence citing the dispute facts" }
        ]
      },
      "outputs": { "error": { "type": "object", "description": "Error information if the node fails", "source": "=Error", "var": "error" } }
    },
    {
      "id": "done",
      "type": "core.control.end",
      "typeVersion": "1.0",
      "display": { "label": "Done" },
      "inputs": {},
      "outputs": {
        "determination": { "source": "=js:$vars.disputeAnalyst.output.determination" },
        "rationale": { "source": "=js:$vars.disputeAnalyst.output.rationale" }
      }
    }
  ],
  "edges": [
    { "id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "disputeAnalyst", "targetPort": "input" },
    { "id": "e2", "sourceNodeId": "disputeAnalyst", "sourcePort": "success", "targetNodeId": "done", "targetPort": "input" }
  ],
  "variables": {
    "globals": [
      { "id": "invoiceNumber", "direction": "in", "type": "string", "defaultValue": "", "triggerNodeId": "start" },
      { "id": "disputeDescription", "direction": "in", "type": "string", "defaultValue": "", "triggerNodeId": "start" },
      { "id": "determination", "direction": "out", "type": "string" },
      { "id": "rationale", "direction": "out", "type": "string" }
    ]
  },
  "definitions": [
    { "…": "core.trigger.manual — verbatim from registry get" },
    { "…": "uipath.agent.autonomous — verbatim from registry get" },
    { "…": "core.control.end — verbatim from registry get" }
  ]
}
```

Then `uip maestro flow format` (back-fills layout + `variables.nodes[]`) and `uip maestro flow validate` (§ 9). No sidecar exists and none is needed.

## 9. Validate

```bash
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

`flow validate` is the authoring gate: it checks embedded-agent semantics (required prompts/model, resource `input` max-connections, escalation required fields, definitions presence — with the exact `registry get` hint when one is missing, undeclared source handles). There is **no `uip agent refresh` / `uip agent validate` step** — nothing to regenerate; the flow file is complete.

> **Known CLI gap — surface it; never hand-write sidecar/bindings.** `uip maestro flow validate` fully supports flow-only inline agents, but `uip maestro flow debug` and `uip solution pack` do not yet synthesize the derived sidecar: debug faults with incident `170002` ("Package resolution failed", `Serverless.PythonAgent.PrepareEnvironmentError`) and pack ships a package whose BPMN references a missing `content/<GUID>/agent.json`. When the user needs a local debug run or package of a flow-only inline agent, tell them about the gap and point them to opening/saving the flow once in a canvas host (Studio Web or VS Code), which derives the sidecar. Do NOT hand-write `<GUID>/` files or `bindings_v2.json` to work around it.

## 10. Derived Sidecar — Reference

Read this to understand what the canvas materializes — never to author it.

**Layout at rest:** `<GUID>/` (= agent `inputs.source`) containing `agent.json`, `flow-layout.json`, `resources/<resourceId>/resource.json`, `features/<featureId>/feature.json` (memory features — not derivable from autonomous agents today; the current autonomous manifest exposes no `memory` handle), `evals/{eval-sets,evaluators}`.

**Who derives, when:** one projection is used by both the canvas save-flush (400ms debounce; immediate for new agents; forced before publish/debug/eval) and packaging synthesis — flushed bytes ≡ synthesized bytes. Packaging additionally emits `<GUID>/.agent-builder/{agent.json,bindings.json}` (what the `pythonAgent` runtime consumes) and an `Agent` entry point at `content/<GUID>/agent.json`.

**Field derivation:**

| `.flow` node data | Derived artifact |
|---|---|
| `systemPrompt` / `userPrompt` | `agent.json` `messages[]` (+ regenerated `contentTokens`) |
| `model`, `mode`, `temperature`, `maxTokenPerResponse`, `maxIterations`, BYOM keys | `agent.json` `settings.*` (`maxTokens` rename; `engine` comes from schema defaults, never projected) |
| `agentInputVariables[]` / `agentOutputVariables[]` | `agent.json` `inputSchema` / `outputSchema` |
| `inputs.source`, `display.label` | `agent.json` `id` + `projectId`, `name` |
| tool/context/escalation nodes | `resources/<sourceUUID>/resource.json` (per-kind restructures injected at derivation) |

**Token namespaces — the same reference changes form twice:**

| File | Token form |
|---|---|
| `.flow` prompts (authored) | `{{ $vars.<nodeId>.output.<field> }}` / `{{ $metadata.* }}` |
| derived `agent.json` `messages[]` | `{{input.<flat>}}` (e.g. `{{input.start__output__subject}}`) |
| derived `resources/*/resource.json` | `{{ $agent.<flat> }}` |

Only the first form is ever authored.

**`.flow` wins — out-of-band sidecar edits are lost:** flow closed → shadowed on next open, overwritten on next save (both hosts); Studio Web never sees them. Only a VS-Code-open flow with the file watcher re-embeds a sidecar edit into the `.flow`. Treat the sidecar as read-only build output.

**Never derived (sidecar-only, preserved by the projection):** `evals/` (authored via `uip maestro flow eval` — the sole sanctioned write under `<GUID>/`), `flow-layout.json`, server-only fields on stored entries.

## 11. Legacy Flows — Detect and Migrate

**Detection:** the agent node's `inputs.systemPrompt` / `inputs.userPrompt` are absent or non-string — the node is a **shell**; the definition lives in the sidecar `<GUID>/agent.json` (GUID = `inputs.source`, or hoisted from a stale `model.source` — § 13).

**Migrate** (edit the agent in the flow file; leave the sidecar in place — the canvas keeps deriving over it):

1. Read `<GUID>/agent.json` (read-only source material).
2. Map into node `inputs`:

   | Sidecar `agent.json` | Node `inputs` |
   |---|---|
   | `messages[role=system].content` | `systemPrompt` (reverse-map tokens, step 3) |
   | `messages[role=user].content` | `userPrompt` (reverse-map tokens, step 3) |
   | `settings.model` / `.temperature` / `.maxIterations` / `.mode` | `model` / `temperature` / `maxIterations` / `mode` |
   | `settings.maxTokens` | `maxTokenPerResponse` |
   | `settings.byomProperties` | `byomConnectionId` + `byomConnectorKey` |
   | `outputSchema.properties.<field>` | one `agentOutputVariables[]` entry `{id, type, description?}` per field |
   | `guardrails` | `guardrails` |
   | `inputSchema` | drop — derived from prompt tokens |

3. **Reverse token mapping:** each `{{input.<flat>}}` in a message becomes `{{ $vars.<dotted-path> }}` — recover the dotted path from the node's existing `agentInputVariables[]` entry whose `id` matches the flat key (its `binding` is `=$vars.<dotted-path>`), or un-flatten mechanically (`__` → `.`): `{{input.start__output__subject}}` → `{{ $vars.start.output.subject }}`. Drop `contentTokens` — never ported.
4. Keep existing `agentInputVariables[]` entries as-is (they are valid derived state); keep `inputs.source` unchanged (it must keep matching the sidecar folder).
5. `flow format` + `flow validate`.

**Flag-off ping-pong — expected, not data loss:** on tenants where the canvas flag is off, a canvas save flushes the sidecar (content preserved) and then strips embedded nodes back to shells. If you find a shell whose sidecar you (or a canvas) just derived, re-embed per this section; the round-trip is lossless.

## 12. Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate`: `systemPrompt` / `userPrompt` / `model` required | Missing required embedded inputs — node is a shell or half-migrated | Embed the full `inputs` per § 2; migrate per § 11 if a sidecar holds the content |
| `flow validate`: definitions entry missing for a node type (error names a `registry get` command) | Node instance `(type, typeVersion)` has no `definitions[]` match | Run the suggested `registry get`, copy the definition verbatim, match `typeVersion` to its `version` (§ 3) |
| `flow validate`: edge rejected, "rewire to one of: escalation, context, tool, success, error" | Edge uses a source handle the manifest doesn't expose (e.g. `memory` on the current autonomous manifest) | Use a declared artifact handle; confirm handles via `registry get` (§ 6) |
| `flow debug` faults: incident `170002`, "Package resolution failed", `Serverless.PythonAgent.PrepareEnvironmentError` | Known CLI gap — debug does not yet synthesize the derived sidecar for a flow-only agent | Surface the gap (§ 9). Open/save the flow once in a canvas host, then re-debug. Never hand-write the sidecar |
| Runtime shows the literal token `{{input.some__flat__key}}` | Prompt carries the derived-agent.json namespace (ported sidecar text) | Rewrite as `{{ $vars.<dotted-path> }}` (§ 4, § 11 step 3) |
| Prompt value empty at run time, validate clean | Referenced trigger field not declared in `variables.globals[]` (`direction: "in"`, `triggerNodeId`), or the `$vars` path names no real node output | Declare the trigger global; verify the node id + field (§ 4) |
| Debug Completes but an `out` global is null | `.content.` wrapper on a typed output — `agentOutputVariables:[{content}]` + End `=js:…output.content.<field>` | Declare each field in `agentOutputVariables[]`, map End to `=js:$vars.<node>.output.<field>` (§ 5) |
| `Orchestrator.StartAgentJob` error at runtime | Stale instance `model` block overrides the definition's `serviceType` | Delete the instance `model` block; keep `Orchestrator.StartInlineAgentJob` in the `definitions[]` entry (§ 13) |
| Agent runs with a stale/wrong model | `inputs.model` left on a copied example or manifest-default value — validate requires the field but not that it's current | Discover + set per [model-selection-guide.md](model-selection-guide.md) |
| My sidecar edits disappeared | Expected — the `.flow` wins; the canvas overwrites the sidecar on save (§ 10) | Make the edit in the node `inputs` |
| `agentInputVariables` entries appeared/disappeared after a canvas touch | Expected — entries are derived from `$vars` refs and pruned when unreferenced (§ 4) | Leave them; author `[]` for new nodes |
| Agent node lost its `source` / got a fresh UUID after canvas open | `inputs.source` was absent — canvas minted one | Always author `inputs.source` explicitly ([planning.md § Identity](planning.md#identity--mint-the-uuids-yourself)) |

## 13. Repair Recipes

Direct JSON edits; if a bulk scripted rewrite is explicitly approved, use the `python3` heredoc pattern from [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling), otherwise `Edit` / `Write`.

### Replace a definition entry

Use when a `definitions[]` entry is wrong, stale, or hand-written. Re-fetch from the registry, splice matching `(nodeType, version)`:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json > /tmp/registry_response.json
python3 - <<'PY'
import json
resp = json.load(open("/tmp/registry_response.json"))
new_def = resp.get("Data", {}).get("Node") or resp.get("Data") or resp
flow = json.load(open("<FILE>.flow"))
for i, d in enumerate(flow["definitions"]):
    if d.get("nodeType") == new_def["nodeType"] and d.get("version") == new_def["version"]:
        flow["definitions"][i] = new_def
        break
else:
    flow["definitions"].append(new_def)
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate "<FILE>.flow" --output json
```

Update the instance `typeVersion` if the registry returned a newer `version` than the entry replaced.

### Hoist `model.source` → `inputs.source` (legacy instances)

Stale flows carry identity on an instance `model` block. Move it and delete the block — on the agent node and every attached resource node:

```bash
python3 - <<'PY'
import json
flow = json.load(open("<FILE>.flow"))
for node in flow["nodes"]:
    t = node.get("type", "")
    if t == "uipath.agent.autonomous" or t.startswith("uipath.agent.resource."):
        model = node.pop("model", None) or {}
        if isinstance(model.get("source"), str):
            node.setdefault("inputs", {})["source"] = model["source"]
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate "<FILE>.flow" --output json
```

## 14. What NOT to Do

- **Do not create or edit sidecar files** — `<GUID>/agent.json`, `resources/**/resource.json`, `features/**/feature.json`, `flow-layout.json` are derived; edits are shadowed and overwritten (§ 10). Sole exception: `evals/` via `uip maestro flow eval`.
- **Do not run `uip agent init` / `refresh` / `validate`** (with or without `--inline-in-flow`) — no agent project exists; the flow file is complete. `uip agent model list` is the only `uip agent` verb in scope.
- **Do not hand-write `bindings_v2.json`, `entry-points.json`, or `.agent-builder/`** — packaging artifacts, not authoring surfaces.
- **Do not write an instance `model` block** on the agent node or any resource node — identity is `inputs.source`; serviceType/version/context come from `definitions[]`.
- **Do not write `contentTokens` or `derivedInputDefinition`** into node `inputs` — derived/BPMN-emission artifacts (§ 4).
- **Do not use `{{input.<flat>}}` or `{{ $agent.<flat> }}` in `.flow` prompts** — derived-file namespaces; flow prompts use `{{ $vars.* }}` / `{{ $metadata.* }}` (§ 4).
- **Do not hand-populate `agentInputVariables[]`** — author `[]`; entries are derived from prompt/resource `$vars` refs (§ 4).
- **Do not leave `inputs.source` unset or non-UUID** — mint a lowercase UUIDv4 yourself ([planning.md § Identity](planning.md#identity--mint-the-uuids-yourself)).
- **Do not use Flow CLI `node add` / `edge add` / `variable` commands for inline-agent graph edits** — non-carve-out structural `.flow` mutations; author directly with `Edit` / `Write`.
- **Do not hand-edit a `definitions[]` entry** — re-fetch from the registry (§ 13); the canvas rebuilds definitions on save anyway.
