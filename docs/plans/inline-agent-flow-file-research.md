# Research record: inline agents — flow file as source of truth

Companion to [inline-agent-flow-file-rewrite.md](inline-agent-flow-file-rewrite.md) (the implementation plan). This file is the raw research: the flow-workbench storage contract (Track A), the end-to-end lifecycle (Track B), and the inventory of everything in this repo documenting or testing the old sidecar pattern (Track C). Researched 2026-07-30 against flow-workbench `develop` @ `e4d2c24b4` (PR #2636 merge `197f1ef386185d50771d9e998f219bf2f364a33a` in HEAD). File:line citations reference the flow-workbench repository unless prefixed with a skills-repo path.

## Context

UiPath low-code agents come in two flavors: standalone agent projects, and **inline agents** embedded in a Maestro Flow project. Historically an inline agent lived as a GUID-named **sidecar folder** next to the `.flow` file (agent definition identical to a standalone `agent.json` project), and the flow file's agent node referenced it via `inputs.source` (the GUID). The `uipath-maestro-flow` skill's inline-agent plugin documents this sidecar-as-source-of-truth pattern and delegates agent-definition authoring to the `uipath-agents` skill.

**flow-workbench PR #2636** (merged 2026-07-28, merge commit `197f1ef38`, flag `services.agent-storage.self-contained-flow`) inverts this:

- The `.flow` file is now **self-contained and authoritative**: the agent node embeds the full agent cluster (prompts, model/settings, guardrails, and every resource node's config — tools, context, escalations, MCP, memory) directly in node `inputs`.
- The sidecar folder is a **derived artifact**, still required at runtime: every canvas save dual-writes the cluster into `<GUID>/agent.json` + `resources/` + `features/` (400ms debounce; immediate for new/recovered agents; forced flush before publish/eval).
- On load, embedded content wins — hydration **skips the sidecar read** entirely; a stale `agent.json` can never shadow the canvas.
- Legacy shell flows self-heal **on open**: `read()` writes hydrated sidecar content back into the `.flow`.
- Debug/publish **synthesize** the storage tree in-memory from `.flow` content (`overlayEmbeddedAgent` / `projectAgentCluster` in `packages/services/src/agent-storage/canvas-projection.ts`) — a bare `.flow` runs with no sidecar.
- In VS Code, an `agent.json` watcher threads `preferStorageSources` so out-of-band sidecar edits still reach the canvas, but the next save **re-embeds** them — the flow file always wins after that.

**The conflict:** the inline-agent plugin instructs coding agents to define inline agents in the sidecar folder. Once a project has been touched by the canvas (flow file embedded), sidecar edits are shadowed/overwritten. Coding agents must instead write the agent definition **directly into the flow file** — exactly as the canvas does.

## Track A — flow-file storage contract & sidecar derivation (flow-workbench)

Projection lives in `packages/services/src/agent-storage/canvas-projection.ts` (+ `canvas-to-storage.ts`, `agent-fields.ts`, `storage-sync.ts`); node schemas in `packages/flow-core/src/manifest/data/ootb-nodes/`; predicates in `packages/flow-schema/src/agents/agent-predicates.ts`.

**Agent node types:** `uipath.agent.autonomous`, `uipath.agent.conversational`, `uipath.agent.voice` (prefix-matched, so `.v2` variants count). `uipath.core.agent.*` = published agent, NOT inline, no sidecar.

**Self-contained agent node `inputs`** (autonomous manifest v1.3, required: `systemPrompt`,`userPrompt`,`model`): `systemPrompt`, `userPrompt`, `model`, `mode` (`standard|advanced`), `temperature`, `maxTokenPerResponse`, `modelMaxTokens`, `maxIterations`, `guardrails`, `agentInputVariables`, `agentOutputVariables`, plus `source` (GUID), `byomConnectionId`/`byomConnectorKey`, and (conversational/voice) `conversationalAgentSettings`, `endExchange`, `isConversational`, `voice`, `callContext`. Defaults: `systemPrompt: 'You are an agentic assistant.'`, `userPrompt: 'What is the current date?'`, `mode: 'standard'`, `agentOutputVariables: [{id:'content',type:'string'}]`.

**`inputs.source` is STILL always written** — minted `crypto.randomUUID()` at node creation (`packages/flow-core/src/node.ts:67-69`), unconditionally back-filled on load reconcile. It remains the sidecar folder name and becomes `agent.json.id` + `projectId`.

**`hasEmbeddedAgentContent` (`canvas-projection.ts:83-87`)** — embedded ⟺ `typeof inputs.systemPrompt === 'string' || typeof inputs.userPrompt === 'string'` (empty string counts), OR voice node with `inputs.voice` non-null object. Structural-only inputs (`source` + variables arrays) = legacy shell. **This is the doc-critical predicate: writing a string prompt into the flow node flips the node to self-contained and the sidecar stops being read.**

**Resource nodes & cluster membership:** association is one edge per resource from the agent node on artifact `sourcePort ∈ {memory, context, tool, escalation, mcp}` (AGENT_RESOURCE_SOURCE_HANDLES), resource `targetPort: 'input'`, depth exactly 1, one agent per resource (maxConnections 1). Kind predicates by type prefix: tool `uipath.agent.resource.tool.`, MCP `…tool.mcp.` (tested before tool), context `…context.`, escalation `…escalation` (bare type exists — OOTB fixed types include bare `uipath.agent.resource.escalation`, `.quick-form`, `.coded-action-app`), memory `…memory.`. Type-string producers: process family `…tool.<rpa|process|api|agent|connector|builtin|clientside|ixp|processorchestration|flow>.<sanitizedKey>`, context `…context.index.<name>.<id>`, memory `…memory.<name>.<id>`. **A resource node only projects if its manifest is present in the flow's `definitions[]`** — missing definition ⇒ no sidecar entry (and delete-guard keeps any stored copy).

**Self-contained resource-node `inputs` per kind** (hydration key set, `storage-to-canvas.ts`):
- tool base: `id, name, description, guardrails, isEnabled, referenceKey, inputSchema, outputSchema, properties, argumentProperties, settings, folderPath`; process family adds per-argument `{mode: variable|prompt|text-builder, textValue, promptValue, argumentPath}` keyed by arg name; connector tools carry `inputs.detail` (DAP blob: connectionId, endpoint, method, inputMetadata, configuration); ixp adds `projectName, versionTag, attachmentConfig`; builtin deep-rag/batch-transform/analyze-attachments have their own field sets
- context: `id, name, description, referenceKey, indexName, folderPath, resultCount, threshold, retrievalMode, query, fileExtension, folderPathPrefix` (+`citations`, `webSearchGrounding`, `outputColumns`)
- escalation: `id, name, description, type, schema, guardrails, app, recipients, outcomeMapping, _additionalProps{taskTitle,priority,labels}, _notifications, _appInputs, ixpToolName, bucket`
- MCP: `id, name, description, slug, serverUrl, folderPath, referenceKey, selectedTools, toolCatalog, discoveryMode`
- memory: `id, name, description, memorySpaceName, referenceKey, folderPath, dynamicFewShotLearning, semanticSimilarity, threshold, kValue, resultCount, searchMode, fieldSettings`

**Derivation — `projectAgentCluster` → `{agentJson, resourceEntries, representedIds}`** (single projection used by both save-flush and packaging synthesis; roundtrip "flushed bytes ≡ synthesized bytes" is test-asserted):
1. Scan `{{ $vars.* }}`/`{{ $metadata.* }}` refs across systemPrompt/userPrompt + all connected resources' inputs → derive `agentInputVariables` (legacy/.flow entries win on id collision; pruning only when prompts exist). Flat naming: `$vars.a.b[0]` → `a__b__0`, `$metadata.x` → `metadata__x`.
2. `inputsToStorage` over merge base = existing sidecar agent.json (server-only fields survive) or schema-package defaults: `systemPrompt/userPrompt` → `messages[{role,content,contentTokens}]`; `model/mode/temperature/maxIterations` → `settings.*`; `maxTokenPerResponse` → `settings.maxTokens`; `byomConnectionId+byomConnectorKey` → `settings.byomProperties`; `agentInputVariables` → `inputSchema` (binding dropped); `agentOutputVariables` → `outputSchema`; node type → `metadata.isConversational`; `file` type → `$ref job-attachment`; `settings.engine` never projected (comes from defaults/merge base).
3. Stamp `agentJson.id = inputs.source`, `agentJson.name = display.label`.
4. Resources: per-kind mappers → `resources/<id>/resource.json` where `id = inputs.source` (except builtin tools: `inputs.id` → node id, since their `source` can hold a `$vars` file expression); memory → `features/<id>/feature.json` (`$featureType: 'memorySpace'`). Notable restructures: tool `type` mapping (`connector`→`integration`, `builtin`→`internal`, `rpa`→`process`…), `location` derived (`external` for integration/ixp else `solution`), agent-node guardrails filtered per tool into `guardrail.policies`, per-arg `{mode:'variable',argumentPath}` → `argumentProperties["$['arg']"]={variant:'argument',argumentPath}`, context flat fields → `settings` discriminated union on `retrievalMode`, escalation → `channels[]` entries, `escalationType: 0` always.
5. **Token namespace changes twice**: `.flow` holds canvas form `{{ $vars.x.y }}`; resource files get `{{ $agent.<flat> }}`; agent.json messages get `{{input.<flat>}}` + regenerated `contentTokens`.

**Preserved from existing sidecar (never projected from .flow):** `evals/` (eval-sets, evaluators), `flow-layout.json`, unknown root files, server-only fields on stored entries (shallow merge, embedded wins). **Deletion guard:** stored resource dropped only when no connected canvas node represents it. **Invalid writes skipped** (Zod), keeping the stored copy.

**Defaults injected at projection** (not authored in .flow): context `retrievalMode:'semantic'/threshold:0/resultCount:3`, tool `isEnabled:true`, escalation `priority:'medium'` fallback, memory `searchMode:'hybrid'/dynamicFewShotSettings.isEnabled:true`, MCP `discoveryMode:'cached'`. All agent defaults (engine/version/model) owned by `@uipath/agents-storage-schemas` — never hardcoded.

**Sidecar layout at rest:** `<GUID>/` (= `inputs.source`, legacy fallback `model.source`) containing `agent.json`, `flow-layout.json`, `resources/<resourceId>/resource.json`, `features/<featureId>/feature.json`, `evals/{eval-sets,evaluators}`. Packaging output is a DIFFERENT tree: `content/<sanitizedGUID>/agent.json` (EntryPoint type Agent) + `<sanitizedGUID>/.agent-builder/{agent.json,bindings.json}`.

**Realistic minimal self-contained agent node** (from projection tests):
```json
{
  "id": "agent1", "type": "uipath.agent.autonomous", "typeVersion": "1",
  "display": { "label": "Research Agent" },
  "inputs": {
    "source": "aaaaaaaa-1111-2222-3333-444444444444",
    "systemPrompt": "Be helpful about {{ $vars.topic }}",
    "userPrompt": "Answer {{ $vars.question }}",
    "model": "gpt-4o", "temperature": 0.4,
    "maxTokenPerResponse": 8192, "maxIterations": 12,
    "guardrails": [],
    "agentInputVariables": [],
    "agentOutputVariables": [{ "id": "content", "type": "string" }]
  }
}
```

## Track B — end-to-end lifecycle: hydrate → edit/save → flush → package/publish; flag rollout state

**Flag state:** `services.agent-storage.self-contained-flow` defaults to **`false` on HEAD — never flipped** (`flag-definitions.ts:339-344`; single commit `197f1ef38`). Rollout = per-org/tenant platform flags. Per-project latch at hydrate time; mid-session flips can't strip embedded content. **Flag-off still strips** agent nodes to 6 structural keys (`source, agentInputVariables, agentOutputVariables, conversationalAgentSettings, endExchange, callContext`) and resource nodes to `source/detail/itemsDescription` on save.

**Open/hydrate (flag on):** per agent node — `hasEmbeddedAgentContent` true ⇒ zero sidecar I/O, `.flow` wins. Legacy shell ⇒ hydrate from sidecar (`loadProjectIfExists`, non-initializing since post-merge fix `04c61b21e`) and **self-heal on open**: `read()` writes hydrated content back into the `.flow` (`flow-storage-service.ts:249-256`). Missing/prompt-less sidecar + real `.flow` inputs ⇒ **recovery** from `.flow` (pre-existing PR #2097 path, works flag-off too). Bare self-contained `.flow` with no sidecar: opens read-only, renders fully; first save materializes the sidecar.

**Edit/save:** canvas debounce 500ms → `save`: `stripForPersistence` = identity no-op (flag on) → full inputs persist in `.flow`. Sidecar flush: 400ms debounce; **immediate awaited** for new agents / new client-side tools (post-merge `69b23e6c1`) / pending recoveries; forced `flushPendingWrites` at editor teardown and before publish/debug/eval. Guards: never flush un-hydrated/failed sources; schema-invalid writes skipped (stored copy kept); stored entries deleted only when no canvas node represents them; recovered sources promoted only after confirmed write.

**Debug/publish/package:** `buildInlineAgentPackages(… synthesizeAgent)` — hosts pass `overlayEmbeddedAgent` (flag on): projection over loaded sidecar (or `buildDefaultStorageRoot` if absent), preserving `evals/` + `flow-layout.json`. Output per agent: `<GUID>/.agent-builder/{agent.json,bindings.json}` (what the `pythonAgent` runtime dispatcher actually consumes), EntryPoint `content/<GUID>/agent.json` (uniqueId = projectId), bindings merged into `bindings_v2.json`. **Host asymmetry:** vsix uploads the fully synthesized tree (on-disk sidecar not runtime-load-bearing); **Studio Web ships `<GUID>/*` verbatim from project files** — i.e. from the dual-write flush — and only adds `.agent-builder/*` from synthesis. So the sidecar folder remains required-in-practice: Studio packaging, `uip` CLI/external tooling, legacy hydration, evals.

**Out-of-band sidecar edits (the coding-agent scenario):**

| Scenario | Outcome |
|---|---|
| Flow **closed** (either host); sidecar edited; flow reopened + saved | **Edit lost** — hydrate skips sidecar, next flush overwrites |
| Studio Web, flow open | **Edit lost + never visible** (no watcher, no `preferStorageSources` caller) |
| VS Code, flow open, canvas clean | Edit survives — watcher → `preferStorageSources` hydrate → re-embedded into `.flow` on next save |
| VS Code, flow open, unsaved canvas edits | Sidecar wins the hydrate; user's unsaved agent edits can be clobbered |
| Sidecar gains a resource folder unknown to `.flow`, then canvas saves | **Deleted** (unless id matches a connected node's id/source) |

⇒ Doc guidance: with embedded content present, the `.flow` wins unconditionally on next open in both hosts; sidecar-as-edit-surface is only semi-viable in open-VS-Code scenarios and dead in Studio Web.

**GUID minting:** `inputs.source = crypto.randomUUID()` at node add (manifest `model.source: true` on agent + every resource type); folder name ≡ raw source (writer unsanitized; packager sanitizes `[^a-zA-Z0-9_-]`→`_` — equal only for real UUIDs; non-UUID sources break watcher + folder-cleanup which gate on `AGENT_FOLDER_UUID_REGEX`).

**Key doc-relevant invariant:** the embedded shape is exactly what an un-flushed brand-new canvas agent looks like, flag-on or flag-off (no node version bump, `inputs` is freeform). A coding agent that writes a self-contained `.flow` is correct under both flag states: flag-on canvas reads `.flow`; flag-off canvas recovers from `.flow` when the sidecar is absent (and strips the `.flow` back to shell on its next save — no data loss when the sidecar has been materialized with identical content).

**Relevant post-merge commits:** `04c61b21e` (preserve sidecar when opening a copied project — `loadProjectIfExists`, `failedSources` skip), `3436b7be7` (hydrate inline-agent runtime input tokens before schema prune — **converter/CLI/bpmn-engine paths run cluster projection**; hints at CLI-side synthesis), `69b23e6c1` (inline agent client-side tools — immediate flush trigger).

## Track C — current skills-repo inline-agent docs & tests inventory

**The "inline-agent plugin" is precisely:**
- `skills/uipath-maestro-flow/references/author/references/plugins/inline-agent/impl.md` (515 lines — largest plugin impl in the skill)
- `skills/uipath-maestro-flow/references/author/references/plugins/inline-agent/planning.md` (116 lines)
- Agents-side twin: `skills/uipath-agents/references/lowcode/capabilities/inline-in-flow/inline-in-flow.md` (392 lines)

**Delegation contract today:** flow plugin owns node/edge/flow-JSON; delegates agent-side (agent.json config, resource.json bodies, prompts) to uipath-agents `lowcode/capabilities/inline-in-flow/inline-in-flow.md` + per-capability docs (process.md, built-in-tools.md, context/index.md, escalation.md, memory.md). Agents skill reciprocally hands node/edge authoring back to the flow skill (Critical Rule 15 — cited inconsistently as 16 in three capability files).

**Load-bearing inverted claims (must flip in rewrite):**
- planning.md L3 / inline-in-flow.md L3 / `uipath-agents/references/lowcode/critical-rules/autonomous-critical-rules.md` Rule 1: "the agent definition lives as a subdirectory of the flow project"
- impl.md L111/L121/L358/L508: flow-node `inputs.systemPrompt`/`userPrompt` are "validator placeholders only — canonical prompt lives in agent.json messages[]" ← **the single most inverted claim**
- impl.md L9–39: scaffold sidecar via `uip agent init "<FlowProjectDir>" --inline-in-flow`, record ProjectId → `inputs.source`, then edit `agent.json` in the sidecar (model/temperature/prompts/outputSchema)
- impl.md L225–317: resource nodes are `inputs.source: <RES_UUID>` shells; hand-author `<GUID>/resources/<RES_UUID>/resource.json`; 7-kind matrix (process/agent/api/processOrchestration tools, builtin tools, context.index, escalation); memory = `features/<Name>/feature.json`
- impl.md L390–405 validate ladder: `uip agent refresh --inline-in-flow [--bindings-target <Flow>/bindings_v2.json]` → `uip agent validate --inline-in-flow` → `uip maestro flow validate`; ordering rule "refresh AFTER all flow graph edits"
- inline-in-flow.md L336–357 "What Happens at Pack Time": flow-workbench reads the dir referenced by `inputs.source` → now inverted (canvas synthesizes from .flow)

**Supporting docs referencing the sidecar pattern** (need touch-ups, not rewrites): flow skill `SKILL.md` (L20, L73, L75, L88 rule 9), `author/CAPABILITY.md` (L17, L33, L73 rule 15, L123), `planning-arch.md` (L175, L238), `planning-impl.md` (L52 router), `greenfield.md` (L279), `brownfield.md` (L49), `editing-operations.md` (L58), `editing-operations-json.md` (L7, L132), `editing-operations-cli.md`, `shared/file-format.md` (L103, L115 — and a gap: project-structure tree omits the `<GUID>/` subdir; node/ports tables omit `uipath.agent.autonomous`). Agents skill: `project-lifecycle.md` (L35–47 inline mode), `lowcode.md`, `model-selection-guide.md` (L72), `coded-vs-lowcode-guide.md` (L113), capability files context/index.md L217, escalation.md L232, built-in-tools.md L18, memory.md L187, `SKILL.md` L68.

**Known pre-existing contradictions to resolve during rewrite:**
1. `shared/node-output-wiring.md` L74 + `agents .../autonomous-agent-prompting-guide.md` L55 claim `{{ $vars.<flowNodeId>.output }}` prompt tokens; impl.md L43–62 says `{{input.<trigger>__output__<var>}}` (post-`a3d6b0804` truth)
2. planning.md L53 says output is `$vars.<nodeId>.output.content`; impl.md L364 says typed outputSchema surfaces flat
3. escalation node type: impl.md uses bare `uipath.agent.resource.escalation`; agents escalation.md L232 says only variants exist (`.coded-action-app`)

**Test surface (18 tasks + 2 shared checkers grade the sidecar):**
- `tests/tasks/uipath-agents/_shared/inline_wiring.py` — single point of failure for 15/16 `lowcode/inline_*` tasks: `resolve_inline_agent_dir()` hard-fails if `inputs.source` dir missing; `find_inline_resource()` iterates `<dir>/resources/**/resource.json`
- `tests/tasks/uipath-maestro-flow/_shared/check_inline_agent.py` — globs `*/*/*/agent.json`, grades model/prompt/outputSchema from the **sidecar** file; used by `smoke/inline_agent_robust.yaml` (prompt hard-codes sidecar path) and `evaluate/inline_agent_eval`
- 16 `uipath-agents/lowcode/inline_*` tasks: all gate on `uip agent init/refresh/validate --inline-in-flow` `command_executed` + sidecar resource.json content; `inline_memory_space` forbids hand-writing `features/**/feature.json`
- `uipath-maestro-flow/multi_node/billing_*` (3 tasks): grade `.flow` node types + live debug only (pattern-agnostic) but ship committed sidecar fixtures `reference_agents/<GUID>/agent.json` (unreferenced by any checker — documentation-by-example)
- Misc: activation probe wording; `tests/reports/uipath-agents-lowcode.md` coverage narrative in sidecar terms; telemetry hooks bucket `*agent.json` edits (`hooks/send-telemetry.sh` L287 / `.ps1` L168); CODEOWNERS splits inline-agent plugin (L119 agents team) vs flow skill (L82) vs agents skill+tests (L41–42)

**Terminology:** repo never says "sidecar" — says "UUID-named subdirectory" / "inline agent directory". Search keys: `inline-in-flow`, `inputs.source`, `uipath.agent.autonomous`, `--inline-in-flow`.

**uipath-review audit (2026-07-31):** the skill's only inline-agent-specific content is semantic node-type-fit guidance needing no change (`references/flows/flow-review-checklist.md:132` resource-type row, `flow-common-issues.md:139` wrong-resource-type example — no `inputs.source`/sidecar/`uip agent` references). Separately, a **pre-existing bug** unrelated to the rewrite but relevant to derived sidecars: project discovery and orphan detection treat any `agent.json` as an executable project marker (`SKILL.md:47` find scan, `:97` executable definition, `:138` routing into `uip agent review`; `solution-review-guide.md:28/:45` orphan checks), so a sidecar `<GUID>/agent.json` is misclassified as a standalone agent project and flagged as an orphan executable — already misfires on today's published pattern; fix independently in uipath-review (exclude UUID-named subdirectories of flow projects).

## Track D — node manifest contract: `nodes[]`, `definitions[]`, canvas edit surface

How the flow canvas populates `nodes[]` + `definitions[]` from a node manifest, and where every canvas edit is written. This is the authoring contract the rewritten plugin must document.

### D.1 What a manifest is, and where it's defined

- Base type `NodeManifest` lives in `@uipath/apollo-react/canvas`; flow-workbench's `.flow`-facing contract is `FlowNodeManifest = NodeManifest & {projectId?, entryPointPath?}` (`packages/flow-schema/src/shims/apollo-canvas-schemas.ts:42,61-66` — the extension exists so those two keys survive `.flow` parsing).
- `manifest.model` is typed `z.ZodAny` — a free-form bag; anything in it survives parsing (`packages/flow-schema/src/packaging/types.ts:106-119`).
- Observed manifest fields (110 OOTB definitions + all dynamic mappers): `nodeType`, `version`, `category`, `description?`, `tags?`, `sortOrder?`, `display {label, icon, shape, description?, canvasLabel?, iconBackground?/iconBackgroundDark?}`, `handleConfiguration[] {position, handles[{id, type: source|target, handleType: input|output|artifact, label?, showButton?, isDefaultForType?, constraints{allowedTargets/allowedSources, validationMessage}}]}`, `form` (property-panel FormSchema: id/title/sections), `inputDefinition` (JSON Schema incl. validation: minLength/errorMessage/if-then/allOf), `inputDefaults`, `outputDefinition {output/error: {type, description, var, source?, schema?}}`, `model?`, `debug {runtime}`, `supportsErrorHandling?`, `runtimeConstraints?`, `toolbarExtensions?`, `projectId?`, `entryPointPath?`. No top-level `name` or `size` (size derives from `display.shape` → rect 288×96, circle 96×96).

### D.2 `definitions[]` = the manifest, verbatim

- The `.flow` document schema types `definitions: z.array(nodeManifestSchema)` — no transform, no field selection (`packages/flow-schema/src/versions/v1.0.ts:35` et seq.). The canvas pushes the whole resolved manifest object (`packages/canvas/src/components/hierarchical-canvas/FlowEditor.tsx:651-673`).
- **Keying:** `(nodeType, version)` matched from the instance's `(type, typeVersion)` (`packages/canvas/src/utils/conversion.ts:400`). Multiple versions of one nodeType coexist by design (migrations push new versions, never remove old — `packages/migrations/src/migrate-nodes.ts:291-307`; confirmed in the committed reference flow: `uipath.agent.autonomous` v1.0 AND v1.1 in one file). Exception: the agent sidecar projection matches on `nodeType` only (`canvas-projection.ts:93-95`).
- **Lifecycle — definitions are canvas-owned:** rebuilt from scratch on every canvas save from the live manifest registry, driven by the `(type, typeVersion)` pairs actually placed (incl. subflows); unused entries are pruned. Live manifest wins over the file's entry **except** in-solution resources (`fileDef.model.projectId` truthy), where the file's `inputDefinition`/`outputDefinition`/`form` are layered on top (`conversion.ts:104-119`). ⇒ Hand-edits to a definitions entry do not survive a canvas save unless `model.projectId` is set.
- Also mutated by: Studio background sync (entry-point I/O refresh rewrites `inputDefinition`/`outputDefinition`/`form` + regenerates `variables.nodes`; project rename rewrites labels/context/binding defaults; projectId reconcile), and workflow-file/node migrations.
- `sortOrder`/`category`/`form.metadata.propertyPanel` are declared display-only in the migration hash exclusions (`packages/migrations/src/fixtures/hash-definitions.ts:46,61,91`); the design canvas builds its manifest map from the registry and deliberately ignores the file's `definitions[]` (read-only surfaces do merge them).

### D.3 `nodes[]` entry creation

Two creators:
- Programmatic (`createNodeFromManifest`, `packages/flow-core/src/node.ts:54-79`): returns exactly `{id, type: manifest.nodeType, typeVersion: manifest.version, ui: {position}, display: {label}, inputs}` where `inputs = structuredClone(manifest.inputDefaults ?? manifest.inputDefinition)` (legacy fallback!) + mints `inputs.source = crypto.randomUUID()` when `model.source`, `inputs.entryPointId` when `model.entryPointId`. Doc comment: "**`node.model` is never written**."
- Canvas add-node (`mapDefinitionToNodeData` → `reconcileInputs`): same inputs seeding (no EV coercion), then: id/label deduped from the manifest label (`"Autonomous agent"` → `autonomousAgent1`, display gets `label`/`label 2`…); `display` = manifest display minus `canvasLabel` (icon/shape/description copied onto the instance; icon is manifest-owned — a baked icon is replaced from the live manifest on load); **for a new autonomous agent, `inputs.model` is overwritten with the first non-deprecated suggested model** from the agentsruntime designer API (`useNodeOperations.ts:265-272`; model list: `GET …/api/designer/{tenantId}/resources/models`); `manifest.model.bindings` hoisted into workflow-level `bindings[]` + `ResourceBindingCreated` event (or, for agent resources without a bindings template — index/mcpServer/memorySpace — a pre-resolved `ResourceBindingCreated` from inputs); position = viewport centre. **No sidecar is created at add time** — it materializes on first save flush.
- Instance write shape (`instance-converters.ts:76-98`): `{id, type, typeVersion, ui, display, inputs, outputs?, variableUpdates?, parentId?}`; `ui` is hoisted out to `layout.nodes.<id>` on file write. **Instance `outputs` persist only entries carrying a `source`** — for agent nodes that's `error` (`source: '=Error'`); `output` has no source and is not persisted (confirmed in the reference flow).
- `layout.nodes.<id> = {position:{x,y}, size:{width,height}, collapsed:false}` (schema passthrough; canvas always back-fills size from shape). Legal to omit — node lands at origin and canvas back-fills on first save.
- Document floor: hand-authored `.flow` files must declare root `"version": "1.9"` (`MINIMUM_SUPPORTED_SCHEMA_VERSION`, `packages/flow-schema/src/versions/index.ts:40`); root `id` must be a UUID.

### D.4 `reconcileInputs` on load (`conversion.ts:171-208`)

No `inputDefaults` backfill — a missing manifest-declared input stays missing. Non-string `source`/`entryPointId` dropped; legacy `node.model.source` hoisted into `inputs.source`; then **unconditional mint** when absent (MST-11176). ⇒ Authoring consequence: always author `inputs.source` explicitly — otherwise the canvas mints a fresh UUID that matches no existing sidecar. `typeVersion` upgrades happen in node migrations, not here.

### D.5 `model.*` semantics + per-kind matrix

- `source: true` → mint `inputs.source` (agent-storage identity/folder name). `entryPointId: true` → trigger identity. `type`/`serviceType`/`version` → BPMN emitter dispatch (`Orchestrator.StartInlineAgentJob` for all three agent node types; resource-type table: Process→StartJob, Agent→StartAgentJob, ProcessOrchestration→StartAgenticProcess, Api→ExecuteApiWorkflowAsync…; connector tools: `bpmn:SendTask` + `Intsvc.ActivityExecution`). `context[]` → `<uipath:context>` (with authoring-only `<bindings.NAME>` placeholders). `bindings {resource, resourceKey, values[{name, propertyAttribute, default}]}` → hoisted to top-level `bindings[]` rows `{id: 'b…', name, type:'string', resource, resourceKey, propertyAttribute, default?}`.
- Per kind: agent nodes (autonomous/conversational/voice) — `source` ✅, serviceType StartInlineAgentJob, no bindings. Escalations, clientside tool, MCP, context index, memory — `source` ✅ only. **Builtin summarize/batchtransform and IXP tools have NO `model` key** → no source mint → storage id falls back `inputs.id ?? node.id` (matches "builtin identity = inputs.id"). Process-family tools — `source` ✅ + bindings (2–3 rows: name/folderPath/folderKey) + context. Connector tools — `source` ✅ + bindings (2 rows, **empty `resourceKey`**, filled by the DAP panel at pick time).
- ⇒ **Top-level `bindings[]` rows are required only for process-family and connector tools.**

### D.6 Derived fields — never authored

- **`agentInputVariables` are DERIVED, not authored.** The manual editor was removed from the UI. At flush/packaging the whole cluster (agent prompts + every connected resource's inputs, deep) is scanned for `$vars.*`/`$metadata.*` refs → entries `{id: <flatName>, type: <resolved>, binding: "=" + path, description: "Bound from $vars.<path>"}` with `encodeFlatName`: `$vars.searchTerm`→`searchTerm`, `$vars.a.output.items[0].id`→`a__output__items__0__id`, `$metadata.x`→`metadata__x` (`agent-cluster-rewrite.ts:113-121,160-181,483-535`). Hand-authored entries win on id collision but are pruned when no live ref points at them. They persist in the `.flow` because `binding` is the reverse-rewrite map on load.
- **`derivedInputDefinition`** (`inputs`-level, `[{name, value: "=js:…", type?}]`): written only during BPMN emission (`preDeriveAgentInputDefinitions`), lifted onto the BPMN element's `model.inputDefinition`; a present-but-empty array is authoritative (MST-11996). May leak into saved `.flow` files after debug/publish. Never hand-write it.
- Agent prompts stay **plain strings** with `{{ $vars.* }}` tokens (the v1.3→v1.4 migration exists solely to undo ExpressionValue coercion on agent inputs); `contentTokens` exist only in the derived agent.json.

### D.7 Canvas edit surface → write targets (condensed)

Everything a user edits lands in **instance state** (`inputs.*`, `display.*`, `layout.nodes.<id>`, `edges[]`, `variables`) — property edits never mutate `definitions[]` and never write an instance `model` block.

| Edit | Write target | Derived sidecar field |
|---|---|---|
| Harness / model / BYO / temperature / max tokens / iterations | `inputs.mode|model|byomConnectionId+byomConnectorKey+modelMaxTokens|temperature|maxTokenPerResponse|maxIterations` | `settings.*` (`maxTokens` rename; `modelMaxTokens` flow-only) |
| System / user prompt | `inputs.systemPrompt|userPrompt` (plain string, `{{ $vars.* }}`) | `messages[]` + contentTokens |
| Guardrails (even from a TOOL's panel) | **agent node's** `inputs.guardrails[]` | `agent.json guardrails` + per-tool `guardrail.policies` |
| Add output | `inputs.agentOutputVariables[] {id,type,description?,required?,schema?}` | `outputSchema` |
| Rename agent (Label) | `display.label` | **`agent.json name`** (overrides `inputs.name`) |
| Rename context/MCP/memory/escalation | `inputs.name` ONLY (`display.label` ignored by projection) | `resource.json name` |
| Rename tool | `inputs.name` → fallback `display.label`; client-side tools mirror `display.label`↔`inputs.name` | `resource.json name` |
| Process-tool argument | `inputs.<arg> = {mode: text-builder|variable|prompt, textValue, promptValue, argumentPath}` (default mode `prompt`) | `variable`→`argumentProperties["$['arg']"]={variant:'argument',argumentPath:<flat>}`; `prompt`→omitted, text → `inputSchema.properties.<arg>.description`; `text-builder`→`{variant:'static',value}` |
| Connector tool config | `inputs.detail` (whole DAP blob: connectionId, connectionFolderKey, endpoint, method, inputMetadata, configuration, telemetryData) | `properties.*` + schemas |
| MCP tools/mode | `inputs.selectedTools[]`, `inputs.discoveryMode = {type:'cached'}|{type:'dynamic',allowAll}` | `availableTools`, `toolsConfiguration.discoveryMode` |
| Context settings | whole-`inputs` rewrite: `retrievalMode, query, folderPathPrefix (ValueSourceField shapes), threshold, resultCount, fileExtension, citations, outputColumns, webSearchGrounding` | `settings` union on retrievalMode |
| Escalation | `inputs.type ('quick-form'|'app-task'|'document-validation-task')`, `inputs.schema (HitlSchema)`, `inputs.app {appName,resourceKey,folderName,…}`, `inputs.recipients[]`, `inputs.outcomeMapping`, `inputs._additionalProps {taskTitle,priority,labels}`, `inputs._appInputs`, `inputs._notifications` (UI-only, not projected) | `channels[]` |
| Memory | `inputs.dynamicFewShotLearning|semanticSimilarity|kValue|searchMode` (`fieldSettings` has NO UI — round-trip only) | `feature.json dynamicFewShotSettings` |
| Node ID rename | `node.id` + all `edges[]` + `$vars.<id>` refs across other nodes | — |
| Drag / resize / collapse | `layout.nodes.<id>.position|size|collapsed` | — |
| Map flow output | End node `outputs.<globalId>.source` + `variables.globals[{direction:'out'}]` | — |

Cross-node side effects when authoring by hand: renaming/deleting a tool rewrites the parent agent's `inputs.guardrails[].selector.matchNames`; `variables.nodes[]` is auto-generated (one entry `{id: "<nodeId>.<outputId>", type, binding:{nodeId,outputId}}` per node output, stale entries pruned); `bindings[]` pruned to live references on every save.

**Memory-handle caveat:** the latest autonomous manifest (v1.3) does NOT expose a `memory` artifact handle (commented out since v1.0); the conversational manifest has it; `AGENT_RESOURCE_SOURCE_HANDLES` still accepts `memory` edges in the projection. Pin actual availability via `registry get` handleConfiguration during implementation.

### D.8 CLI registry relation

`uip maestro flow registry get --local` bakes the same `NodeManifest` JSON into `definitions[]` (consumed as `NodeManifest[]`), with four documented divergences from Studio's builder (vsix `inSolutionManifests.ts:11-31`): wrong icon for coded-vs-lowcode agents, missing `model.section`, `model.bindings.values` emitted as a flat object instead of an array (crashes `createBindingsFromManifest`), and `projectId` left inside `model` instead of hoisted. The vsix patches these in-memory. Registry endpoint internals are not determinable from flow-workbench.

### D.9 Authoring checklist (derived)

1. Root `"version": "1.9"`; root `id` = UUID.
2. One `definitions[]` entry per distinct `(nodeType, typeVersion)`, copied verbatim from `registry get`; every `nodes[].typeVersion` must exactly match a `definitions[].version` or the node loads unhydrated.
3. Author `inputs.source` (lowercase UUID) explicitly on the agent node and every resource node whose manifest has `model.source` (all except builtin summarize/batchtransform and IXP tools).
4. Prompts = plain strings with `{{ $vars.* }}` tokens; author `agentInputVariables: []` and let tooling derive entries (advanced: hand entries must have `id = encodeFlatName(binding)` and are pruned when unreferenced).
5. Instance `outputs`: only the `error` entry (source `=Error`); no `output` entry; no instance `model` block; never `derivedInputDefinition`.
6. `layout.nodes.<id>` optional (canvas back-fills `{position, size, collapsed}`); sizes rect 288×96 / circle 96×96.
7. `bindings[]` rows only for process-family + connector tools (mirror `propertyAttribute`/`default`; leave `<bindings.NAME>` placeholders in `model.context` untouched).
8. Artifact edges: agent `sourcePort ∈ {tool, context, escalation, memory, mcp}` → resource `targetPort: 'input'`.
9. Expect the canvas to rewrite `definitions[]` wholesale on its next save (in-solution defs with `model.projectId` keep their file-provided `inputDefinition`/`outputDefinition`/`form`).

## Decisions (2026-07-30)

1. **Full rewrite of the inline-agent plugin, entirely separated from uipath-agents.** The new plugin self-sufficiently documents the "inline agent in the flow file" pattern. uipath-agents remains authoritative for standalone agents only.
2. **Authoring contract: flow-only.** Coding agents author ONLY the `.flow` (full embedded inputs). No sidecar authoring, no `uip agent init --inline-in-flow` scaffold. `uip agent validate` remains uipath-agents/standalone-specific; flow validation folds into flow-specific validate commands. Local run and packaging are expected to adopt the sidecar synthesis from flow canvas — the sidecar is always derived deterministically from the flow file.
3. **CLI support for synthesis: not yet determined.** Docs must not depend on unshipped verbs; note the seam. Implementation starts with a smoke experiment: does `uip maestro flow validate`/debug/pack handle a flow-only inline agent today? (Hint: post-merge commit `3436b7be7` suggests converter/CLI/bpmn-engine paths already run cluster projection.)
4. **uipath-agents cleanup: remove + redirect, same PR.** inline-in-flow.md shrinks to a redirect stub; inline callouts in capability files become one-line pointers; body-level redirects only (avoid frontmatter description churn → no activation-gate recall eval).
5. **Tests: move under `tests/tasks/uipath-maestro-flow/` and rewrite to target the flow file** (embedded inputs, node types, edges) instead of the sidecar folder.

Added 2026-07-31:

6. **Mirror strategy.** The plugin is restructured as a subtree mirroring `uipath-agents/references/lowcode/` — same file organization, near-identical wording, surgical swaps where the flow representation differs — housed inside `uipath-maestro-flow` (not a separate skill). Measured mirror classes over the ~7,400-line lowcode tree: ~35-40% near-verbatim (prompting, model-selection, guardrails), ~35% identical skeleton with swapped authoring mechanics (per-capability files), ~15% N/A (CLI lifecycle, inline-in-flow.md), ~10% inline-only new (manifest/definitions contract, cluster wiring, derived sidecar, legacy migration).
7. **Mirror scope:** core capabilities + prompting + model-selection + critical-rules + guardrails (adapted to `inputs.guardrails` embedding). Out (future-work notes): inline-specific evaluations (flow-level evals via the evaluate capability cover current usage; note: `<GUID>/evals/` is authored via `uip maestro flow eval`, never derived — the sole sanctioned sidecar write) and conversational/voice inline agents. Solution-resource mechanics stay owned by the flow skill (not mirrored).
8. **No drift control for now** — correspondence map (agents file ↔ inline file ↔ delta class) produced as an authoring aid only; shared-knowledge governance between the two doc sets decided later.
9. **Incremental delivery on a long-lived feature branch** (`feat/inline-agent-flow-file`): M1 clean-slates the plugin covering only the agent itself (prompts, schemas, model config); each subsequent milestone adds one capability with its ported tests; merge to `main` gated on coding-agent eval pass-rate parity with the published architecture (per-task baseline recorded at M0). The plan doc is restructured as a living roadmap with a status board, per-milestone runbooks and exit gates, resumable across agentic sessions.

Implementation plan: [inline-agent-flow-file-rewrite.md](inline-agent-flow-file-rewrite.md).
