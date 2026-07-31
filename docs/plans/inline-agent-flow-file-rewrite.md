# Roadmap: Rewrite the inline-agent plugin — flow file as source of truth

Status: **in progress** — see [Status board](#4-status-board). Update the board + milestone notes at every session close.
Driver: [flow-workbench PR #2636](https://github.com/UiPath/flow-workbench/pull/2636) (merged 2026-07-28, merge commit `197f1ef38`, flag `services.agent-storage.self-contained-flow`)
Owner: uipath-maestro-flow + uipath-agents skill owners
Research record (storage contract, lifecycle, repo inventory, manifest contract): [inline-agent-flow-file-research.md](inline-agent-flow-file-research.md)
Branch: **`feat/inline-agent-flow-file`** — long-lived; milestone PRs target this branch; merges to `main` only at M11 after full parity. Created 2026-07-31 off `main` @ `3a4afbe8f`; checked out as a git worktree at `~/.herdr/worktrees/skills/feat-inline-agent-flow-file` (Herdr workspace "inline-agent-rewrite", grouped under the skills repo). Note: the two docs/plans files are untracked in the main checkout — committing them is the branch's first commit (M0).

## 1. Context

Inline agents (low-code agents embedded in a Maestro Flow project) historically lived in a GUID-named subdirectory next to the `.flow` file — the "sidecar" — holding a standalone-style `agent.json` + `resources/` + `features/`; the flow node was a shell carrying only `inputs.source = <GUID>`. The inline-agent plugin (`skills/uipath-maestro-flow/references/author/references/plugins/inline-agent/`) documents that pattern and delegates agent authoring to the `uipath-agents` skill.

flow-workbench PR #2636 inverts it: the `.flow` node embeds the **full agent definition** in `inputs`; hydration skips the sidecar whenever embedded content is present; every canvas save dual-writes the sidecar as a **derived artifact**; packaging synthesizes the runtime tree from the `.flow`. A coding agent following the current plugin docs (edit the sidecar) produces edits the canvas **shadows and overwrites**.

Goal: full rewrite of the inline-agent plugin so coding agents define inline agents directly in the flow file, exactly as the flow canvas does — plus the reciprocal uipath-agents cleanup and test migration. Because the existing skills are already published, the rewrite is delivered **incrementally on a feature branch**, gated on coding-agent eval pass-rate parity with the published architecture.

## 2. The new contracts (ground truth from flow-workbench @ `develop`)

### 2.1 Flow-file storage contract

- Agent node `uipath.agent.autonomous` (siblings `.conversational` / `.voice` exist; out of authoring scope). Self-contained `inputs`: `source` (identity UUID), `systemPrompt`, `userPrompt`, `model` (required trio), `mode` (`standard|advanced`), `temperature`, `maxTokenPerResponse`, `maxIterations`, `guardrails: []`, `agentInputVariables[]`, `agentOutputVariables[]`, optional `byomConnectionId`/`byomConnectorKey`. Never an instance `model` block.
- **Embed trigger** (`hasEmbeddedAgentContent`, `packages/services/src/agent-storage/canvas-projection.ts`): a **string** `inputs.systemPrompt` or `inputs.userPrompt` ⇒ node is self-contained ⇒ tooling never reads the sidecar. Structural-only inputs (`source` + variables arrays) ⇒ legacy shell ⇒ sidecar hydrates, and the canvas self-heals the `.flow` on open.
- Prompts use canvas-form tokens `{{ $vars.<nodeId>.output.<field> }}` / `{{ $metadata.* }}` (spaced braces). `{{input.<flat>}}` exists only in the *derived* agent.json. No `contentTokens` in the `.flow`.
- Input delivery: **`agentInputVariables[]` are DERIVED, not authored** (the manual editor was removed from the canvas). Tooling scans the cluster (prompts + all connected resources' inputs) for `$vars.*`/`$metadata.*` refs and generates entries `{id: <flatName>, type, binding: "=$vars.<path>"}` (`$vars.a.b[0]` → `a__b__0`, `$metadata.x` → `metadata__x`); hand-authored entries win on id collision but are pruned when unreferenced. Authoring contract: write `agentInputVariables: []` (the manifest default) and let tooling derive. Converter builds runtime JobArguments from the derived entries.
- **Manifest contract** (research Track D): `definitions[]` = the resolved node manifest **verbatim**, keyed `(nodeType, version)` ↔ instance `(type, typeVersion)` (multiple versions of one nodeType coexist); the canvas **rebuilds `definitions[]` from its live manifest registry on every save** (in-solution entries with `model.projectId` keep their file-provided `inputDefinition`/`outputDefinition`/`form`). Instance `outputs` persist only source-carrying entries (agent: `error` with `=Error`; no `output` entry). Root document `"version": "1.9"` floor. Top-level `bindings[]` rows required only for process-family and connector tools (manifests with `model.bindings`). Never author: instance `model` blocks, `derivedInputDefinition` (BPMN-emission artifact), `contentTokens`.
- Typed `agentOutputVariables[]` surface flat at `$vars.<nodeId>.output.<field>` (no `.content.` wrapper).
- Resource nodes (`uipath.agent.resource.tool.*` incl. `tool.mcp.*` / `tool.builtin.*` / `tool.connector.*`, `…context.index.*`, `…escalation*`, `…memory.*`) attach via exactly ONE artifact edge: agent `sourcePort ∈ {tool, context, escalation, memory, mcp}` → resource `targetPort: "input"`, depth 1, one agent per resource. Each carries its **full config in `inputs`** + its own `inputs.source` UUID (builtin tools: identity at `inputs.id`; their `source` may hold a `$vars` file expression). **A resource node whose type has no `definitions[]` entry does not project — it silently vanishes from the derived agent and the package.**

### 2.2 Sidecar derivation (why it is never authored)

One projection — `projectAgentCluster` / `overlayEmbeddedAgent` in `packages/services/src/agent-storage/canvas-projection.ts` (+ `canvas-to-storage.ts`, `agent-fields.ts`) — is used by both the save-time flush and packaging synthesis (flushed bytes ≡ synthesized bytes, test-asserted):

| `.flow` node data | Derived sidecar artifact |
|---|---|
| `systemPrompt` / `userPrompt` (tokens rewritten `{{ $vars… }}` → `{{input.<flat>}}` + regenerated `contentTokens`) | `<GUID>/agent.json` `messages[]` |
| `model`, `mode`, `temperature`, `maxTokenPerResponse`, `maxIterations`, BYOM keys | `agent.json` `settings.*` (`maxTokens` rename; `engine` comes from schema defaults, never projected) |
| `agentInputVariables[]` (binding dropped) / `agentOutputVariables[]` | `agent.json` `inputSchema` / `outputSchema` |
| `inputs.source`, `display.label` | `agent.json` `id`+`projectId`, `name` |
| tool/context/escalation/MCP nodes (tokens rewritten to `{{ $agent.<flat> }}`) | `resources/<sourceUUID>/resource.json` (per-kind restructures injected at derivation: tool `type`/`location`, per-arg `argumentProperties`, context `settings` union, escalation `channels[]`) |
| memory nodes | `features/<id>/feature.json` (`$featureType: memorySpace`) |

Sidecar-only, never derived: `evals/` (authored via `uip maestro flow eval` — the sole sanctioned write under `<GUID>/`), `flow-layout.json`, server-only fields (shallow-merged from the stored copy). Deletion guard: stored entries removed only when no connected canvas node represents them. Packaging additionally emits `<GUID>/.agent-builder/{agent.json,bindings.json}` — what the `pythonAgent` runtime actually consumes — plus an `Agent` entry point at `content/<GUID>/agent.json`.

### 2.3 End-to-end data flow (flag on)

1. **Configure** — node written with full `inputs`; `source` minted `crypto.randomUUID()` at node creation.
2. **Save** — `stripForPersistence` is a no-op; full inputs persist in the `.flow` (source of truth).
3. **Flush (dual-write)** — 400ms-debounced projection writes the sidecar; immediate for new agents; forced before publish/debug/eval.
4. **Open** — embedded ⇒ zero sidecar I/O; legacy shell ⇒ hydrate from sidecar + write back into the `.flow` (self-heal on open); a bare self-contained `.flow` with no sidecar renders and runs.
5. **Package/debug/publish** — synthesis projects the cluster from the `.flow` over the loaded sidecar (or schema defaults when absent).
6. **Out-of-band sidecar edits are lost** — flow closed: shadowed on next open, overwritten on next save (both hosts); Studio Web never sees them; only VS-Code-open + file watcher (`preferStorageSources`) re-embeds them.
7. **Rollout** — flag default-off on HEAD, per-tenant platform-flag rollout, per-project latch. Flag-off canvas still strips nodes to shells on save — but an embedded node is byte-identical to an un-flushed brand-new canvas agent, so flow-first content is valid under both flag states.

## 3. Decisions

2026-07-30:

1. **Full plugin rewrite, entirely separated from uipath-agents.** uipath-agents stays authoritative for standalone agents only. Zero cross-skill doc links.
2. **Flow-only authoring.** Author ONLY the `.flow`. No `uip agent init/refresh/validate --inline-in-flow`, no hand-authored sidecar files. The sidecar is always derived deterministically from the flow file (canvas today; CLI local run/pack expected to adopt the same synthesis).
3. **CLI synthesis support: not yet determined** → docs must not depend on unshipped verbs; the gating experiment (M0) opens implementation.
4. **uipath-agents cleanup: remove + redirect** — body-level only (frontmatter descriptions untouched → no activation-gate churn).
5. **Tests move under `tests/tasks/uipath-maestro-flow/` and are rewritten to grade the flow file** instead of the sidecar.

2026-07-31:

6. **The plugin mirrors the uipath-agents skill.** Same construct, different representation: the plugin is a subtree mirroring `uipath-agents/references/lowcode/` — same file organization, near-identical wording, surgical swaps where the flow representation differs. Housed inside `uipath-maestro-flow` (plugins/inline-agent/), not a separate skill: one drift boundary, no routing churn, graph mechanics link to same-skill shared refs.
7. **Mirror scope:** core capabilities (process/connector/built-in/context/escalation/memory/mcp) + prompting + model-selection + critical-rules + **guardrails** (adapted to flow-file embedding). **Out of scope, noted as future work:** inline-agent-specific evaluations (today covered only at flow level via the evaluate capability + `uip maestro flow eval`) and conversational/voice inline agents (plugin stays autonomous-only). **Solution-resource mechanics are NOT mirrored** — the flow skill owns solution + flow project registration; inline agents are only embedded in the flow file.
8. **No drift control for now.** Shared-knowledge governance between the inline docs and uipath-agents is deferred; the correspondence map is an authoring aid only.
9. **Incremental delivery on a long-lived feature branch.** Existing skills are published, so the rewrite lands on `feat/inline-agent-flow-file`: M1 clean-slates the plugin and covers ONLY the agent itself (prompt, schemas, model config); each subsequent milestone adds one capability with its ported tests; merge to `main` only when the new plugin matches the published architecture's coding-agent eval pass rate across the full migrated suite. This document is the living roadmap — status board updated at every milestone close so any agentic session can resume.

## 4. Status board

Legend: ☐ not started · ◐ in progress · ☑ done (date + PR). Update at session close; add one-line notes under the milestone.

| # | Milestone | Docs scope | Tests (ported → new) | Status | Gate result |
|---|---|---|---|---|---|
| M0 | Foundations: gating experiment + baseline + branch + checker skeleton | — (findings → this doc) | — (baseline run of 18 existing tasks) | ◐ 2026-07-31 | validate ✅ / debug+pack ❌-no-synthesis → M1–M9 unblocked. Baseline table DEFERRED (owner call) — fill before M1 gate evaluation |
| M1 | Agent core — clean slate | planning.md, impl.md, critical-rules.md, model-selection-guide.md, prompting/, supporting-ref flips, uipath-agents redirects | `inline_in_flow`→`inline_agent/base`; `smoke/inline_agent_robust`; `evaluate/inline_agent_eval` | ☑ 2026-07-31 ([PR #2410](https://github.com/UiPath/skills/pull/2410) merged) | branch run 3/3 tasks at **1.000** — twice: initial + post-review re-run under tightened criteria (9/9 replicates each, claude-sonnet-5); baseline table still DEFERRED — fill retroactively (branch at ceiling, any baseline ≤ 1.0 passes) |
| M2 | Process-family tools | capabilities/process.md | 8 tasks: `inline_{solution,external}_{rpa,agent,apiworkflow,maestro}_tool` → `inline_agent/tool_{rpa,agent,api,maestro}_{solution,external}` | ☐ | — |
| M3 | Built-in tools | capabilities/built-in-tools.md (+ per-tool files) | `inline_builtin_tool` → `inline_agent/tool_builtin` | ☐ | — |
| M4 | Context grounding | capabilities/context-index.md | `inline_context_index` → `inline_agent/context_index` | ☐ | — |
| M5 | Escalations | capabilities/escalation.md | `inline_{solution,external}_escalation` → `inline_agent/escalation_{solution,external}` | ☐ | — |
| M6 | IS connector tool | capabilities/integration-service.md | `inline_is_connector_tool` → `inline_agent/tool_connector` | ☐ | — |
| M7 | MCP server tool | capabilities/mcp.md | `inline_mcp_server_tool` → `inline_agent/tool_mcp` (stays `skip: true`) | ☐ | — (no run possible) |
| M8 | Memory spaces | capabilities/memory.md | `inline_memory_space` → `inline_agent/memory_space` | ☐ | — |
| M9 | Guardrails | capabilities/guardrails.md | no existing inline test — optional new task (note coverage gap) | ☐ | — |
| M10 | Brownfield: legacy-shell migration | impl.md § legacy already in M1; fixture work here | NEW `inline_agent/legacy_shell_migration` (+ optional `stale_shadow_edit`) | ☐ | — |
| M11 | Final sweep + merge to main | billing touch-ups, activation probes, CODEOWNERS, reports, audit | full-suite parity run | ☐ | — |

## 5. Delivery model

**Branch workflow.** All work on `feat/inline-agent-flow-file`. Each milestone = one PR targeting the feature branch (reviewable, one logical change). Rebase the branch on `main` at each milestone start; while rebasing, check whether `uipath-agents/references/lowcode/` twins of already-mirrored files changed upstream and fold the changes in (branch hygiene during the branch's life — distinct from the deferred permanent drift-control, decision 8). `main` stays fully on the published architecture until M11; nightlies are unaffected.

**Parity gate.** Baseline = per-task pass rates of the 18 existing inline tasks on `main` (M0 records them: prefer aggregating the last ~5 nightly runs from the codereval blob (`coderevaltests`/`runs`); fall back to a dedicated baseline run with `experiments/default.yaml`). Baselines are recorded **per model** (nightlies exercise claude-sonnet-5 and codex/gpt-5.6-terra). A milestone closes when each of its migrated tasks, run on the branch (≥3 replicates, default experiment model), reaches pass rate ≥ its baseline; M11's full-suite run covers both models. Regressions are investigated (doc gap vs checker bug vs genuine model failure) before closing. Old not-yet-migrated tasks remain in-tree on the branch but are not run there; each migration deletes its old task in the same PR. Delete `tests/tasks/uipath-agents/_shared/inline_wiring.py` in the milestone that migrates its last importer.

**Review coordination.** Milestone PRs cross up to three CODEOWNERS groups (plugin dir = agents team; flow-skill refs = Maestro team; uipath-agents files + tests = agents team) — tag reviewers accordingly, heaviest at M1.

**Session resumption.** A fresh session: (1) read this doc + the research record; (2) check the status board, pick the first ☐/◐ milestone; (3) execute its runbook; (4) update board + notes, close with the milestone PR. Every milestone body below is self-contained given the two docs.

**Standing runbook (every milestone).** `git fetch && git rebase origin/main` → docs edits → `/lint-task` over changed task YAMLs → `bash hooks/validate-skill-descriptions.sh` + `python3 scripts/check-skill-status.py` (expect clean — no frontmatter/status changes) → relative-link check over the plugin → `coder-eval` run of the milestone's tasks + a 1-replicate regression pass over previously-migrated tasks → record gate results in the board → PR to the feature branch with the run evidence.

## 6. Milestones

### M0 — Foundations: gating experiment, baseline, branch, checker skeleton

No shipped docs. Deliverables:

1. **Branch**: ☑ done 2026-07-31 — `feat/inline-agent-flow-file` off `3a4afbe8f`, worktree at `~/.herdr/worktrees/skills/feat-inline-agent-flow-file`. First commit: add the two `docs/plans/inline-agent-flow-file-*.md` files (untracked in the main checkout today).
2. **Gating experiment** (logged-in dev machine, staging tenant) — decides how M1+ document validate/debug and whether billing touch-ups (M11) are unblocked:
   - `uip solution init ExpSol` + `uip maestro flow init ExpFlow`; hand-author a **flow-only** inline agent (manual trigger → autonomous node with full embedded inputs, fresh UUID `source`, real model/prompts, typed outputs → end; `definitions[]` from `uip maestro flow registry get uipath.agent.autonomous --output json`). No sidecar.
   - `uip maestro flow validate` → `uip maestro flow debug` → `uip solution pack`: record per command whether the flow-only agent works and whether `<GUID>/` or `.agent-builder/` materializes (hint: flow-workbench commit `3436b7be7` shows converter/CLI paths already run cluster projection).
   - `uip maestro flow eval evaluator add` against the bare project (does the eval CLI need `<GUID>/`?).
   - Repeat with one wired resource per ambiguous kind (context index, solution RPA tool, escalation) AND capture one canvas-authored flow to pin exact input shapes: process-tool `properties` nesting, escalation `app` sub-shape, memory `dynamicFewShotLearning`/`kValue` vs `resultCount`, brace-spacing tolerance of the ref scanner, UUID case, instance-`outputs` shape (error-only expected), **`memory` handle availability on the latest autonomous manifest** (v1.3 exposes none — decide whether M8 targets autonomous at all).
   - Verify `uip agent model list --output json` runs from a flow project directory (no agent project on disk) — it is the single `uip agent` verb the plugin keeps, for `inputs.model` discovery.
   - Prerequisite for the canvas capture: an editor with `services.agent-storage.self-contained-flow` ON (vsix local `uipath.featureFlags` override, or a flag-enabled tenant) — a flag-off canvas strips saves back to shells, so embedded shapes cannot be captured there.
   - Fallback matrix: all synthesize → full roadmap unblocked. Validate OK but debug/pack don't → M1–M9 unblocked (validate is their grading ceiling); billing tasks keep current prompts; impl.md § Validate gains a "known CLI gap — surface it; never hand-write sidecar/bindings" callout. **Validate FAILS on a bare flow → STOP; file the CLI gap** — flow-only docs are not viable until the primary gate accepts them. Eval CLI needs `<GUID>/` → `inline_agent_eval` keeps its old init gate temporarily with a TODO.
3. **Baseline table**: per-task `main` pass rates for the 18 tasks, recorded in this doc (append below the status board).
4. **Checker skeleton**: `tests/tasks/uipath-maestro-flow/_shared/flow_inline_wiring.py` with the agent-level API (`load_json`, `find_autonomous_agent_node`, `assert_embedded_agent` — embed predicate + model-override + real-prompt bar + UUID source, **no directory requirement** —, `assert_agent_output_vars`, `assert_agent_input_vars`, `assert_edge`, `assert_definition_present`) + pytest beside it. Per-kind helpers (`find_wired_resource`, `assert_resource_inputs`, `assert_resource_source_uuid`) grow in M2–M8 as each kind's shapes are pinned.
5. **Correspondence map** started: `docs/plans/inline-agent-mirror-map.md` — uipath-agents file ↔ plugin file ↔ delta class (authoring aid only, decision 8).

Exit: experiment matrix + pinned shapes recorded here; baseline table filled; checker skeleton merged to branch.

#### M0 results (2026-07-31, codereval tenant on alpha, uip 1.200.0)

Branch ☑ (`bd8b2ff8c`). Checker skeleton ☑ (`flow_inline_wiring.py` + 45-test pytest; hardened post-review with never-author guards — instance `model` block, `contentTokens`, `derivedInputDefinition` — and `assert_prompt_tokens` failing on derived `{{input.*}}`/`{{ $agent.* }}` namespaces, which validate cannot catch). Correspondence map ☑ ([inline-agent-mirror-map.md](inline-agent-mirror-map.md)). Baseline table **DEFERRED** (owner call, no az tooling on dev machine) — must be filled before M1's exit gate is evaluated. Canvas capture NOT done (no flag-enabled editor this session) — see "still unpinned" below.

**Experiment matrix** (flow-only = full embedded `inputs`, fresh lowercase UUID `source`, registry-verbatim `definitions[]`, root `"version": "1.9"`, error-only instance `outputs`, NO sidecar):

| Probe | Result |
|---|---|
| `uip maestro flow validate` (bare flow-only agent) | ✅ Valid — the primary gate. Also enforces semantics: escalation `app`/`recipients` required (`ESCALATION_APP_REQUIRED`/`ESCALATION_RECIPIENT_REQUIRED`), missing `definitions[]` entry → actionable error with the exact `registry get` hint, undeclared source handle rejected, resource `input` max-connections 1 enforced |
| `uip maestro flow format` | ✅ (repositions, sets canonical sizes, generates `variables` entries) |
| `uip agent model list --output json` from flow project dir | ✅ works with no agent project on disk — safe to keep as the single `uip agent` verb in the plugin |
| `uip solution pack` (flow-only) | ⚠️ **succeeds but does NOT synthesize** — nupkg lacks `content/<GUID>/agent.json`, the Agent entry point, and `.agent-builder/`; the emitted BPMN references `entryPoint: content/<GUID>/agent.json` → broken agent package |
| `uip maestro flow debug` (flow-only) | ❌ Faulted — incident `170002` "Failure in the Orchestrator Job", errorDetails "Package resolution failed", dependentFaultCode `Serverless.PythonAgent.PrepareEnvironmentError`. Upload itself succeeded |
| `uip maestro flow debug` (same flow + hand-derived sidecar `<GUID>/agent.json`) | ✅ Completed — control isolates the failure to missing synthesis. Typed output surfaced **flat** (`$vars.expAgent.output.answer`), confirming no `.content.` wrapper |
| `uip solution pack` (sidecar present) | ✅ ships `content/<GUID>/agent.json` **verbatim from disk** + Agent entry point (uniqueId = GUID). Still no `.agent-builder/` in the nupkg — debug ran fine without it (server-side concern) |
| `uip maestro flow eval evaluator add` (bare project) | ✅ needs no sidecar — writes project-root `evals/<flow-doc-id>/evaluators/` (keyed by the flow document id, not the agent GUID). `inline_agent_eval` drops its init gate at M1 |

**Fallback-matrix row hit: "Validate OK but debug/pack don't"** → M1–M9 unblocked (validate is their grading ceiling); billing tasks keep current prompts at M11; impl.md § Validate gains the "known CLI gap — surface it; never hand-write sidecar/bindings" callout.

**Pinned shapes (tenant registry get + validate-accepted flow):**

- **Autonomous v1.3 manifest handles**: `escalation`/`context`/`tool` (artifact) + `input`/`success`/`error` only — **no `memory`, no `mcp` handle**; validator rejects a `memory`-port edge ("…rewire to one of: escalation, context, tool, success, error"). **M8 answer: memory is NOT autonomous-attachable today** — plan for the "document the limitation" path. Tenant registry also exposes **zero memory or MCP node types** (M7's no-run exemption reconfirmed at the type level). Conversational is `AvailableOnTenant: false` here.
- **Escalation (M5)**: only variants exist on tenant — `…escalation.coded-action-app` v1.1 available, `…escalation.quick-form` v1.1 NOT (`AvailableOnTenant: false`); no bare type. `model: {source: true}`; required `[name]`; validated `app` sub-shape `{appName, resourceKey, folderName}` (values from `uip solution resources list --kind App`); `recipients: [{type: 3, value: "<email>"}]`; `_additionalProps {taskTitle, priority, labels}`, `_notifications` bool, `_appInputs`/`outcomeMapping` nullable.
- **Context index (M4)**: flat inputs; `query`/`folderPathPrefix` are ValueSourceField objects `{mode: text-builder|variable|prompt, textValue, promptValue, argumentPath}`; `citations: "enabled"` (string, not bool); `webSearchGrounding: {value}`; tenant identity (indexId/indexName/folderKey/folderPath) baked into the manifest's `inputDefaults` — copy from there.
- **Builtin summarize v1.1 (M3)**: `model: null` — confirms no source mint, identity = `inputs.id`; fields `description`, `source` (string; may hold `$vars` file expr), `query` (ValueSourceField), `fileExtension {value}`, `citationMode {value}`. Tenant builtins: `analyzefiles`/`batchtransform`/`summarize` (no `deeprag` — reconcile naming at M3).
- **Process family (M2)**: remote tenant types are `tool.process.*` (RPA processes; serviceType `Orchestrator.StartJob`), `tool.flow.*` (`StartFlowProcess`), `tool.processorchestration.*`, `tool.agent.*`, `tool.api.*`, `tool.ixp.*`, `tool.connector.*` — **no `tool.rpa.*` on the remote registry; RPA surfaces as `process`** (the projection's rpa→process rename, upstream of storage). Remote `registry get` emits `model.bindings.values` as a proper **array** (the D.8 object-shape divergence is `--local`-specific — probe at M2 with an in-solution project). Manifest `inputDefinition` lists raw args (e.g. `RPAExpenseRequestIn: string`); `inputDefaults` carry `inputSchema`/`outputSchema`. Validate accepted per-argument ValueSourceField instance inputs + `properties {processName, folderPath}` + top-level `bindings[]` rows `{id, name, type, resource, resourceKey, propertyAttribute, default}` mirroring `model.bindings.values`.
- **Misc**: lowercase UUID `source` authored end-to-end OK (validate → pack → debug); wired 4-node cluster (agent + escalation + context + process tool on their artifact ports) validates clean; `registry search` on this tenant returns 217 dynamic nodes (2 context, 6 external agents).

**Still unpinned (needs a flag-enabled canvas capture; carry into M2/M5):** exact canvas-written per-arg nesting beyond validate acceptance, any extra keys the canvas writes into escalation `app`, brace-spacing tolerance of the `$vars` ref scanner, instance-`outputs` shape beyond the error-only entry (billing fixture + debug agree it's error-only).

### M1 — Agent core: clean slate

Scope: the inline agent itself — prompts, schemas, model config, identity, wiring in/out, validation, derived-sidecar knowledge, legacy detection. **No capabilities** (no tools/context/escalation/memory/mcp/guardrails).

Docs (clean-slate `plugins/inline-agent/`, delete current planning.md + impl.md content):
- **planning.md** (~100 ln): header flips the claim ("full definition in node `inputs`; `<GUID>/` is derived — never authored"); node type; inline-vs-published decision table (anchor kept — `planning-arch.md:178` links it); ports table (artifact ports listed; capability rows marked "docs land per milestone"); output variables (typed → flat); **"Identity — mint the UUIDs yourself"** (lowercase UUIDv4; why real: derived folder name, watcher regex, packaging identity); planning annotations updated (drop "`<projectId-placeholder>` assigned when init runs").
- **impl.md** (~450 ln), sections: (1) The contract — node IS the definition; string prompt = embed trigger; sidecar derived, never create/edit (sole exception `evals/` via `uip maestro flow eval`); no `uip agent` lifecycle verbs; valid under both flag states. (2) Agent node `inputs` spec — field table + compact quality obligations; depth in the mirrored same-plugin guides. (3) Manifest & definitions contract + add the node — definitions verbatim from `registry get`, exact `(type, typeVersion)` match, canvas rebuilds definitions on save, canonical node JSON, instance `outputs` = `error` only, layout optional, root `"version": "1.9"`, `input`/`success` edges. (4) Wire flow data into prompts — `{{ $vars.* }}` plain-string tokens; **`agentInputVariables` derived — author `[]`**; trigger-globals prerequisite; anti-patterns (never `{{input.*}}`, `derivedInputDefinition`, EV objects). (5) Wire agent output out — flat fields, End-node mapping, `.content.` anti-pattern. (6) Registry validation. (7) Resource nodes — kind matrix as a stub routing into `capabilities/` ("capability docs land per roadmap milestone"), the definitions-or-nothing law, the universal recipe. (8) Worked example — trigger → agent → end (agent-only at M1; extend with a tool + context in M2/M4). (9) Validate — `flow format` → `flow validate --output json`; no `uip agent refresh/validate`; toolchain-seam note per M0. (10) Derived sidecar — reference (layout, who derives when, `.flow`-wins + loss scenarios, never-derived list with evals carve-out, token-namespace table, packaging one-liner). (11) Legacy flows — detect and migrate (shell detection; agent.json→inputs mapping; reverse token mapping; leave sidecar in place) + the flag-off ping-pong note: on flag-off tenants a canvas save flushes the sidecar then strips embedded nodes back to shells — content is preserved, re-embed per this section; expected and harmless, not data loss. (12) Debug table (agent-core rows). (13) Repair recipes (definition-replace; `model.source`→`inputs.source` hoist). (14) What NOT to Do.
- **critical-rules.md** ← mirrors `lowcode/critical-rules/*` (~half swapped to node rules). **model-selection-guide.md** ← near-verbatim (`settings.model` → `inputs.model`). **prompting/autonomous-agent-prompting-guide.md** ← near-verbatim (`{{input.x}}` → `{{ $vars.x }}`).
- **Supporting-ref flips** (all load-bearing routing surfaces, so branch eval sessions never see the old pattern): flow `SKILL.md` L20/L73 + **L88 rule 9 rewritten**; `author/CAPABILITY.md` L17/L33/L73/L123; `planning-arch.md` L175 + L238 ports row; `greenfield.md` L279; `brownfield.md` L49 (route to planning/impl/capabilities + legacy section); `editing-operations.md` L24/L58 + `editing-operations-json.md` L7/L132 (drop CLI carve-outs; builtin `inputs.id` note); `shared/file-format.md` (derived `<GUID>/` in project tree; `inputs.source` rows; agent node in node/ports tables; generic `definitions[]` contract subsection; root version floor); `shared/node-output-wiring.md` L74 row → canvas-form token contract; `shared/cli-commands.md` gains the `uip agent model list` entry; `references/evaluate/CAPABILITY.md` L18 — inline-agent eval routing note (flow-level evals; `<GUID>/evals/` is CLI-authored, never derived); `plugins/summarize/impl.md` L192 + `plugins/batch-transform/impl.md` L169 `--source` notes; `plugins/agent/{planning,impl}.md` "UUID subdirectory" → "directly in the flow file".
- **uipath-agents redirects** (branch is the new world; per-capability docs return via M2–M9): `inline-in-flow.md` → ~20-line redirect stub; `autonomous-critical-rules.md` Rule 1 + `critical-rules.md` inline rule rewritten; `project-lifecycle.md` `--inline-in-flow` sections → "legacy; not part of any recipe"; capability files' inline callouts (context/index.md, escalation.md, built-in-tools.md, memory.md) → one-line "embedded in the `.flow`; owned by uipath-maestro-flow"; `model-selection-guide.md` L72 deleted; `lowcode.md` routing rows; agents `SKILL.md` L68 row (body only); `prompting/autonomous-agent-prompting-guide.md` standalone-only token form (cross-skill deep link removed); `coded-vs-lowcode-guide.md` L113.

Tests (rewrite + `git mv`, old tasks deleted in the same PR; global transforms per §7):
- `uipath-agents/lowcode/inline_in_flow` → `uipath-maestro-flow/inline_agent/base` (`skill-flow-inline-agent-base`; tags `[uipath-maestro-flow, e2e, mode:build, lifecycle:generate, node:inline-agent, shape:single-node]`): `assert_embedded_agent` + typed outputs + definition present + serviceType guard + input/success edges; keep `project.uiproj` check.
- `smoke/inline_agent_robust.yaml` rewritten flow-file-first (+ missing `smoke` tier tag — joins the sampled smoke pool, call out in PR; drop `uip agent init` + `model list` gates — model-list at most advisory `pass_threshold: 0`); `_shared/check_inline_agent.py` rewritten to read the `.flow`.
- `evaluate/inline_agent_eval`: checker item 1 → embedded assertions on `TriageEval.flow`; eval-file items unchanged; drop init gate (unless M0 found the eval CLI needs the sidecar — then keep temporarily + TODO).

Exit gate: the 3 tasks ≥ baseline. Notes (2026-07-31 session):

- Docs shipped: clean-slate `plugins/inline-agent/{planning.md,impl.md,critical-rules.md,model-selection-guide.md,prompting/autonomous-agent-prompting-guide.md}`; all listed supporting-ref flips (flow SKILL.md incl. rule 9 rewrite, author/CAPABILITY.md, planning-arch, greenfield, brownfield, editing-operations(+json), shared/file-format (project tree + identity rows + definitions-contract subsection + 1.9 floor + node/ports rows), node-output-wiring L74, cli-commands (`uip agent model list` section), evaluate/CAPABILITY.md, summarize+batch-transform `--source` notes, agent plugin wording); all listed uipath-agents redirects (inline-in-flow.md → 16-line stub; critical-rules AP-22 + autonomous Rule 1; project-lifecycle `--inline-in-flow` → legacy; 4 capability callouts → one-liners; model-selection L72; lowcode.md rows; SKILL.md L68 body row; prompting guide standalone-only incl. §2/§4 token-form conversion; coded-vs-lowcode L113).
- Tests migrated: `inline_agent/base` (new `skill-flow-inline-agent-base`, e2e; validate-only rationale documented — debug can't run flow-only agents per M0), `smoke/inline_agent_robust` (renamed id `skill-flow-inline-agent-robust`, **new `smoke` tier tag — joins the sampled smoke pool**), `evaluate/inline_agent_eval` (init gate dropped per M0 eval finding). `_shared/check_inline_agent.py` rewritten to grade the `.flow`. Old `uipath-agents/lowcode/inline_in_flow/` deleted. `/lint-task`: base=Medium (validate-only e2e, rationale documented), robust=OK, eval=Low (integration without debug, "local CRUD only" by design). Checkers verified against synthetic pass/fail flows; `_shared` pytest suite 104/104.
- Known leftovers for M3 (built-in tools): uipath-agents `built-in-tools/{batch-transform,deeprag}/{planning,impl-json}.md` still describe inline flow-wiring + reference the old `inline_builtin_tool` checker path.
- Branch eval run 2026-07-31 (claude-sonnet-5, 3 replicates each, `experiments/default.yaml`, local): `skill-flow-inline-agent-base` **1.000**, `skill-flow-inline-agent-robust` **1.000**, `skill-flow-eval-inline-agent` **1.000** (9/9 replicates SUCCESS). Artifact audit: no sidecar directory created; embedded prompts + `agentInputVariables: []` + minted UUID source + discovered model; zero `uip agent init/refresh/validate` invocations. Baseline (main) side still DEFERRED — no az tooling on dev machine; owner to fill before formally closing the gate (branch results are at ceiling, so any baseline ≤ 1.0 passes).
- PR #2410 review addressed (same day): all 3 Mediums (impl.md intro anchor; `require_vars_ref=True` in base+eval checkers; robust+eval validate graded by outcome via `validate_flow.py`) + Lows (base `file_contains` fallback, absent `agentInputVariables` accepted as `[]`, `node:inline-agent` added to tests/README vocabulary, SCAFFOLD_MODEL re-pin noted for M11, doc polish). Gate **re-run under the tightened criteria: 3/3 tasks at 1.000 again** (9/9 replicates SUCCESS). Deliberately not taken: `require_vars_ref` on the smoke checker (robust's prompt doesn't mandate flow-data wiring).

### M2 — Process-family tools

Docs: `capabilities/process.md` ← `lowcode/capabilities/process/process.md` (semantics/discovery verbatim: `uip solution resources list/get`, Source Local/Remote → folder handling; authoring → node type `…tool.<rpa|process|agent|api|processorchestration>.<release-key>`, full `inputs` incl. per-argument `{mode: text-builder|variable|prompt, textValue, promptValue, argumentPath}` (default `prompt`), `properties.processName`/`folderPath`, `inputSchema`/`outputSchema`, **top-level `bindings[]` rows** mirroring the definition's `model.bindings`; name authority `inputs.name` → `display.label`; derived fields not to author: `type`/`location`/`argumentProperties`). Extend impl.md worked example with the RPA tool. Watch M0's pinned `properties` nesting + the `registry get --local` divergences (bindings values object-vs-array — decide whether repair recipes cover fixing a CLI-baked definition).
Tests: 8 tasks → `inline_agent/tool_{rpa,agent,api,maestro}_{solution,external}` (`skill-flow-inline-tool-*`); checker gains `find_wired_resource` + `assert_resource_inputs` + process-family expectations (solution: `properties.folderPath == "solution_folder"`; external: real folder + `referenceKey` UUID); keep brownfield guards (`command_not_executed uip solution init` / `flow init EmployeeOnboarding` / `uip agent init ["']?ToolAgent`) and discovery gates.
Exit gate: 8 tasks ≥ baseline. Notes: —

### M3 — Built-in tools

Docs: `capabilities/built-in-tools.md` (+ per-tool files mirroring the twin's `analyze-attachments.md`, `deeprag/`, `batch-transform/` where content survives the swap): node type `…tool.builtin.<toolType>`; **no `model.source` on summarize/batch-transform ⇒ identity = `inputs.id`**; `source` may hold a `$vars` file expression; per-tool field sets from `registry get` manifests (cross-check flow-workbench `storage-to-canvas.ts` hydration sets); no `bindings[]`.
Tests: → `inline_agent/tool_builtin`; node-type-suffix assertion replaces resource.json `toolType`; drop source==dirname cross-check; registry gates kept.
Exit gate: 1 task ≥ baseline. Notes: —

### M4 — Context grounding

Docs: `capabilities/context-index.md` ← `lowcode/capabilities/context/index.md` (index discovery verbatim; authoring → node type `…context.index.<name>.<id>`, inputs `indexId/indexName/folderKey/folderPath/retrievalMode/threshold/resultCount/query/folderPathPrefix/fileExtension/citations/outputColumns/webSearchGrounding`; **name authority `inputs.name` only**; derived `settings` union not authored). Extend the worked example with the context node.
Tests: → `inline_agent/context_index`; flat `retrievalMode` valid + `indexName`/`folderPath` asserts; edge on `context`.
Exit gate: 1 task ≥ baseline. Notes: —

### M5 — Escalations

Docs: `capabilities/escalation.md` ← twin (variant selection via `registry search` + `AvailableOnTenant` — bare type exists as OOTB, tenant registries may expose only variants; inputs `type/schema (HitlSchema)/app {appName,resourceKey,folderName}/recipients/outcomeMapping/_additionalProps {taskTitle,priority,labels}/_appInputs`; `_notifications` UI-only; derived `channels[]` not authored; app discovery `uip solution resources list --kind App`).
Tests: → `inline_agent/escalation_{solution,external}`; app-binding subset asserts per M0's pinned `app` sub-shape; external adds `resourceKey` UUID + deployed folder.
Exit gate: 2 tasks ≥ baseline. Notes: —

### M6 — IS connector tool

Docs: `capabilities/integration-service.md` ← twin (connection discovery `uip is connections list --all-folders` verbatim; authoring → `…tool.connector.<key>.<name>` + `inputs.detail` blob at key level — validator-safety confirmed by M0/experiment; `bindings[]` 2 rows resource `connection`; solution-connection provisioning links to flow-skill solution guidance, not mirrored).
Tests: → `inline_agent/tool_connector` (adds flat `connector` tag); `inputs.detail` non-empty with bound `connectionId`; keep `bindings_v2.json` + `resources/solution_folder/connection/` asserts (solution-side, unaffected).
Exit gate: 1 task ≥ baseline. Notes: —

### M7 — MCP server tool

Docs: `capabilities/mcp.md` ← twin (server discovery; node `…tool.mcp.<name>.<key>`; inputs `slug/serverUrl/selectedTools/toolCatalog/discoveryMode = {type:'cached'}|{type:'dynamic',allowAll}`; edge `sourcePort: "mcp"`).
Tests: → `inline_agent/tool_mcp`, stays `skip: true` (tenant path broken — `path-to-ga`); state the no-run exemption in the PR.
Exit gate: lint + review only. Notes: —

### M8 — Memory spaces

Gated on M0's memory-handle finding (autonomous v1.3 manifest exposes no `memory` handle; conversational does). If autonomous-attachable: docs `capabilities/memory.md` ← twin (inputs `memorySpaceName/folderPath/searchMode/threshold|semanticSimilarity/kValue/dynamicFewShotLearning/fieldSettings` — `fieldSettings` has no canvas UI, round-trip only; derived to `features/<id>/feature.json`; never `uip agent memory add` for inline); tests → `inline_agent/memory_space` (drop the `uip agent memory add` gate + both feature.json `command_not_executed` guards — node inputs ARE the documented path; keep the parent `bindings_v2.json` memorySpace binding as a tolerant check). If NOT autonomous-attachable: document the limitation, keep the old task parked, note as future work.
Exit gate: 1 task ≥ baseline (or documented deferral). Notes: —

### M9 — Guardrails

Docs: `capabilities/guardrails.md` ← `lowcode/capabilities/guardrails/guardrails.md` (near-verbatim — the guardrails array projects unchanged; swap: authored on the agent node's `inputs.guardrails`, tool-scoped `selector.matchNames` reference node `inputs.name`; note canvas cross-writes — tool renames rewrite matchNames; decide whether `guardrails-recommend.md` mirrors or stays standalone-only after checking its CLI dependencies).
Tests: none exist for inline guardrails — optional new task; at minimum record the coverage gap in `tests/reports` regeneration (M11).
Exit gate: docs review; optional task ≥ 0.8 if added. Notes: —

### M10 — Brownfield: legacy-shell migration

Fixture: shell `.flow` + populated sidecar built from the billing reference fixtures (strip embedded keys from a copy of `BillingDisputeAnalyst.reference.flow`; repurpose one `reference_agents/<GUID>/`).
Tests: NEW `inline_agent/legacy_shell_migration` (integration tier — fully local): prompt asks for an agent edit with no pattern words; grades config landing embedded in the node (w5.0 checker + w3.0 validate + w2.0 `file_contains` + w1.0 negative guard). Optional `stale_shadow_edit` (embedded flow + divergent stale sidecar) if the first lands cleanly.
Exit gate: new task passes ≥ 0.8 across 3 replicates (no baseline — new coverage). Notes: —

### M11 — Final sweep + merge to main

- Billing tasks (`multi_node/billing_*`): delete "`scaffold with uip agent init --inline-in-flow`" from prompts/descriptions — **only if M0 confirmed flow-only debug synthesis** (they run live debug); update the 3 `*.reference.flow` fixtures to the embedded exemplary bar; delete remaining `reference_agents/<GUID>/` dirs.
- Side-edits: activation probes `uipath-agents-037`/`-066` → `uipath-maestro-flow.jsonl` with flipped `expected_skill` (run the activation probe suite once after the move); CODEOWNERS — add `/tests/tasks/uipath-maestro-flow/inline_agent/` mirroring the plugin-owner line; regenerate `tests/reports/*` via `/test-coverage uipath-agents` + `/test-coverage uipath-maestro-flow`; `/audit-verbs` (40+ `--inline-in-flow` references disappear); final grep sweeps (`grep -rn "inline-in-flow" skills/` → only stub + legacy notices; `grep -rn "uip agent init" skills/uipath-maestro-flow/` → nothing).
- **Full-suite parity run**: every migrated task, ≥3 replicates, against the baseline table. Merge `feat/inline-agent-flow-file` → `main` when the suite meets parity; PR carries the parity table + M0 experiment matrix.
- Future-work notes filed (issues or memory): inline-agent evaluations documentation; conversational/voice inline agents; guardrails eval coverage; permanent drift-control decision (decision 8).
- Verify the **independent uipath-review sidecar fix** landed (not gated on this branch — it misfires on the published pattern today): project discovery and orphan detection treat any `agent.json` as an executable project (`uipath-review/SKILL.md:47,:97,:138`; `references/solution-review-guide.md:28,:45`), so a derived `<GUID>/agent.json` sidecar is classified as a standalone agent project and flagged as an orphan executable. Fix in uipath-review: exclude UUID-named subdirectories of flow projects from executable/orphan detection and treat their contents as derived artifacts. (Audited 2026-07-31: the skill's only inline-agent-specific content — flow-review-checklist.md:132, flow-common-issues.md:139 — is semantic node-type-fit guidance needing NO change.)

Exit gate: full parity table green; merge completed. Notes: —

## 7. Shared reference (cited by milestones)

**Global test transforms (every migrated task):**

| Old criterion | Disposition |
|---|---|
| `command_executed` on `uip agent init/refresh/validate --inline-in-flow` | DROP → `.flow` `file_contains` + checker assertions + `run_command validate_flow.py` (w3.0) |
| — | ADD `command_not_executed: '(uip|\$UIP)\s+agent\s+(init|refresh|validate)\s+.*--inline-in-flow'` (w1.0) |
| solution/discovery/brownfield gates | KEEP unchanged |
| `run_command check_*.py` (w5.0) | REWRITE to flow-file assertions via `flow_inline_wiring` |

Graded artifact = the `.flow`; sidecar existence neither required nor forbidden (debug/eval/pack may legitimately materialize it). Task-id scheme `skill-flow-inline-*`; tags `[uipath-maestro-flow, e2e, mode:build, lifecycle:generate, node:inline-agent, shape:multi-node]` (base: `shape:single-node`).

**Mirrored plugin tree (target end state):**

```
plugins/inline-agent/
├── planning.md, impl.md                          # inline-only core (M1)
├── critical-rules.md                             # ← lowcode/critical-rules/* (M1)
├── model-selection-guide.md                      # ← near-verbatim (M1)
├── prompting/autonomous-agent-prompting-guide.md # ← near-verbatim (M1)
└── capabilities/
    ├── process.md (M2) · built-in-tools.md + per-tool files (M3) · context-index.md (M4)
    ├── escalation.md (M5) · integration-service.md (M6) · mcp.md (M7)
    └── memory.md (M8) · guardrails.md (M9)
```

Each capability file keeps its twin's heading skeleton; "author the resource.json" sections are replaced by: node-type pattern + full `inputs` spec + `definitions[]` requirement + artifact edge + name-authority note + projection-derived fields not to author. Correspondence map: `docs/plans/inline-agent-mirror-map.md` (M0, authoring aid only).

**Baseline table** (fill DEFERRED at M0 by owner decision, 2026-07-31 — no az tooling on the dev machine; fill before evaluating M1's exit gate; extended with branch results per milestone):

| Task (old id) | Baseline (claude-sonnet-5) | Baseline (codex) | Branch result (milestone) |
|---|---|---|---|
| `lowcode/inline_in_flow` → `inline_agent/base` | _DEFERRED_ | _DEFERRED_ | 1.000 (M1, 3 reps) |
| `smoke/inline_agent_robust` | _DEFERRED_ | _DEFERRED_ | 1.000 (M1, 3 reps) |
| `evaluate/inline_agent_eval` | _DEFERRED_ | _DEFERRED_ | 1.000 (M1, 3 reps) |
| _15 remaining rows — DEFERRED; fill per milestone_ | | | |

## 8. Critical files

- Plugin subtree: `skills/uipath-maestro-flow/references/author/references/plugins/inline-agent/` (planning.md, impl.md, critical-rules.md, model-selection-guide.md, prompting/, capabilities/*).
- uipath-agents redirects: `references/lowcode/capabilities/inline-in-flow/inline-in-flow.md` (→ stub), `critical-rules/*`, `project-lifecycle.md`, `lowcode.md`, capability files' inline callouts.
- Flow-skill supporting refs: `SKILL.md`, `references/author/CAPABILITY.md`, `references/shared/{file-format.md,node-output-wiring.md,cli-commands.md}`, `references/author/references/{planning-arch,greenfield,brownfield,editing-operations,editing-operations-json}.md`.
- Tests: `tests/tasks/uipath-maestro-flow/_shared/{flow_inline_wiring.py (new), check_inline_agent.py}`, `tests/tasks/uipath-maestro-flow/inline_agent/**`; delete `tests/tasks/uipath-agents/lowcode/inline_*` + `tests/tasks/uipath-agents/_shared/inline_wiring.py` (per milestone).
- Ground truth: flow-workbench `packages/services/src/agent-storage/canvas-projection.ts` (+ `canvas-to-storage.ts`, `storage-to-canvas.ts`, `agent-fields.ts`, `storage-sync.ts`, `agent-cluster-rewrite.ts`), PR #2636, and `tests/tasks/uipath-maestro-flow/multi_node/billing_dispute_analyst/BillingDisputeAnalyst.reference.flow`.
