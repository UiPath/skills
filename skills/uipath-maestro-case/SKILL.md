---
name: uipath-maestro-case
description: "TRIGGER for UiPath Maestro Case Management work: create or edit `caseplan.json`; plan/build from `sdd.md`; finalize `sdd.draft.md`; design a new Case when no SDD exists; answer Case-schema questions; or operate/troubleshoot Case instances. DO NOT TRIGGER for `.xaml`, `.flow`, `.bpmn`, standalone agents/APIs/processes, or general cross-product PDD-to-SDD planning; route those to their owning UiPath skills. Suggest `uipath-planner` in text only for explicit cross-product planning; never auto-invoke it."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Build new Case projects from a provided or skill-generated `sdd.md`, make targeted edits to an existing `caseplan.json`, explain the Case schema, and operate or troubleshoot live Case instances.

> **Direct-JSON authoring invariant:** Read Case artifacts and mutate them only with Write/Edit. Never use or explore mutating `uip maestro case` authoring commands (`cases|stages|tasks|*-conditions ... add|update|remove`, including `tasks add-connector`). Never edit `caseplan.json.bpmn`; validate/pack regenerates it. CLI use is limited to solution scaffold/registration/sync/upload, registry and metadata reads, validation, consent-gated debug, and runtime operations. Read [case-commands.md](references/case-commands.md) only when exact surviving syntax is needed.

<a id="routing--greenfield-vs-brownfield"></a>

## Select one request journey

Choose one row before loading details. Do not preload excluded journeys.

| Request | Direct first owner | Excluded until selected |
|---|---|---|
| New Case, no `sdd.md` | [Phase 0 interview](references/phase-0-interview.md) | Planning, plugins, tenant schemas, and resource prompts before Case Review approval |
| Build/rebuild from provided `sdd.md` | [Planning](references/planning.md) | Phase 0, brownfield, and troubleshooting |
| Finalize `sdd.draft.md` | [Phase 0 direct resumption](references/phase-0-interview.md#resumption) | Planning, plugins, tenant discovery, and subagents unless the request continues into a build |
| Plan-only/no-build | No SDD: [Phase 0 bounded path](references/phase-0-interview.md#build-start--sdd-written-alongside-the-build). Provided SDD: [Planning plan-only path](references/planning.md#step-1--hard-gate-check-login-and-pull-registry). | Tenant registry, connections, schemas, recipients/users, and implementation |
| Targeted edit to an existing Case | [Brownfield router](references/brownfield.md) | Greenfield planning and prototyping |
| Case-schema question | [Case schema](references/case-schema.md) | Build workflow |
| Runtime instance/process operation | Relevant section of [Case commands](references/case-commands.md) | Authoring workflow |
| Failed debug/deployed run | [Troubleshooting](references/troubleshooting-guide.md), only after failure | Success-path troubleshooting preload |

For `.xaml`, `.flow`, and `.bpmn`, use `uipath-rpa`, `uipath-maestro-flow`, and `uipath-maestro-bpmn`. Route standalone agent/API/process work to its owner. Never auto-invoke `uipath-planner`.

<a id="kickoff--set-dev-expectations-first"></a>

## User-facing roadmap and lifecycle

After routing, show the matching roadmap once in five lines or fewer, before questions or work. Use business language; do not expose internal modes or implementation mechanics.

| Journey | Roadmap |
|---|---|
| New Case without an SDD | `1. I read your request and make the design calls, checking your UiPath tenant only when needed. 2. You receive one review packet covering the journey, other paths, SLAs, rules, resources, and my decisions. 3. After your confirmation, I build and validate. 4. I pause before publishing or running anything.` |
| New Case with an SDD | `1. I read the design and verify available UiPath resources. 2. You choose once whether to build straight through or pause at a preview. 3. I plan, build, and validate without further interruptions. 4. I pause before publishing or running anything.` |
| Targeted edit | `1. I pull the latest Case when it lives in Studio Web. 2. I apply the requested change in place. 3. I validate it. 4. I ask before publishing or running anything.` |

Other routes need a roadmap only when they contain a decision or hard stop; schema-only questions do not. Greenfield lifecycle is Phase 0 design (only without SDD) → Phase 1 planning → Phase 2 reviewable structure → Phase 3 implementation → Phase 4 validation → Phase 5 optional publish → Phase 6 optional debug. Only decisions and hard stops below interrupt it.

## Critical Rules

1. **Phase 0 is best-assumption design with one eight-section Case Review.** When no SDD exists, infer from the request and documents, sweep other paths, disclose every assumption/override/resource choice, and inform rather than interrogate. Allow at most one batched clarifying call—only for an empty or contradictory request, user-requested questions, or no source signal for other paths—plus one confirmation. The Case Review must contain, in order, Case Snapshot, Primary Journey, Other Paths Considered, SLA and Escalations, Rules and Outcomes, Resources and Integrations, Decisions I Made, and Review Flags; name every stage/task and its type, activation/grouping, required status, routing/outcome, and SLA context, while leaving data, variables, and task I/O to the full SDD. It is the only valid plan-first approval surface; a generic build-plan approval or “Yes” is not a Build answer. Follow the [Phase 0 owner](references/phase-0-interview.md#confirm--the-single-checkpoint), including full-template `sdd.md` rendering on Build, draft/design/no-build fast paths, explicit-sign-off behavior, and no overwrite of an existing `sdd.md`. Direct draft finalization uses no subagent or planning/plugin preload. For an authored `user-selected-stage`, replace each eligible origin's `required-tasks-completed | exit-only | Yes` row with exactly `required-tasks-completed | wait-for-user | Yes`; retain neither the old completion row nor a non-completing duplicate. `wait-for-user` exposes the picker; it creates no automatic event/SLA/decision route.
2. **`sdd.md` is the sole post-Phase-0 input across sessions.** Trust a provided, resumed, re-run, or post-compaction SDD as written; do not validate or gap-fill it. In the session that just rendered it, the confirmed in-memory model drives planning without re-reading the file. If later build ambiguity remains, AskUserQuestion rather than infer silently. Follow [Phase 0 build start](references/phase-0-interview.md#build-start--sdd-written-alongside-the-build) and [Planning Step 2](references/planning.md#step-2--locate-and-parse-the-design-document).
3. **Phase 1 has one fresh-registry hard gate per session.** Before cache inspection, carryover, resolution, or Phase 1 writes, run `uip login status --output json`, then one normal `uip maestro case registry pull`; reuse only a successful same-session Phase 0 pull that rendered the current SDD. Failure stops Phase 1. Before success, a missing cache/index is a failed precondition, never empty; after success, a still-absent index is genuinely empty and only Rule 17's Force choice may refresh it. Read `~/.uip/case-resources/<type>-index.json` directly. Explicit plan-only/no-build work skips tenant registry, connection, schema, recipient, and user discovery, keeps intended names, marks identity `resolve at build`, and defers wiring. A Phase 0 build starts light grounding lazily at the first tenant-bound need and performs only one name pass without schema or resource prompts. Read [registry discovery](references/registry-discovery.md) after the gate and before lookup.
4. **Use `--output json` on every CLI read whose output is parsed programmatically.**
5. **Follow only the selected node/trigger owner.** Open its `planning.md` for planning and `impl-json.md` for execution; connector triggers also load [connector-trigger-common.md](references/connector-trigger-common.md). Never preload siblings or guess a shape. Use the direct tables below.
6. **`tasks.md` is declarative, lossless, and one-to-one.** Use plain field identifiers and no shell commands. Emit one level-two `## T<n>: <action>` per SDD declaration; quote every task display name. Preserve supplied/approved rules and selectors, every rationale, every input binding mode/value and literal/expression form, and every output operator with both operands. Each task T-entry owns exactly one `activation-mode:` and `entry-rule:`; a separate condition entry is not a substitute. Ask about any ambiguous/unrecognized row; never omit it. Regenerate greenfield plans, but preserve IDs during brownfield edits. At Phase 1 Step 4—before the first `tasks.md` write—read the complete [task-plan contract](references/tasks-plan-contract-guide.md).
7. **The plan auto-proceeds unless the request opted into a stop.** Treat `tasks.md` as approved and continue to Phase 2 without sign-off. Stop only for an explicit plan-only/review-first request. Re-read `tasks.md` before execution.
8. **Only the owning fallback path may assign a placeholder; never fabricate IDs.** Genuine empties first pass Rule 17, and `<UNRESOLVED: ...>` remains in `tasks.md` until fallback is assigned. A placeholder task keeps its type, display name, structural envelope, placement, TaskId, and conditions with `data: {}`. A placeholder event trigger keeps its render fields plus only `data.inputs: { serviceType: "Intsvc.EventTrigger" }`, appends its `entry-points.json` item, and creates no trigger edge. Read [placeholder tasks](references/placeholder-tasks.md) and the [event fallback](references/plugins/triggers/event/impl-json.md#placeholder-fallback-unresolved-connector--connection) only on that route.
9. **Audit every lookup in `tasks/registry-resolved.json`.** Each SDD task gets one object with exact keys `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, and `rationale`, plus applicable metadata. `stage` + `task` identify the declaration; `cacheFile` is the searched basename; `matches` is the complete exact-name set from Rule 3. Normally `selected` is a member of `matches` or `null`. After Rule 17 inline creation, retain the tenant `matches: []` and put the exact rediscovered local resource in `selected`. Follow [registry discovery](references/registry-discovery.md#4-return-all-matches).
10. **Both cross-task-reference forms use one output-ID resolver.** Plan a whole value as `input <- "Stage"."Task".output`; inside a larger `=js:` expression use `vars.$xref('Stage','Task','output')`, resolved at Step 11.5. Use the source output's `.id`; only a custom `=` output with no `.id` resolves through its verified root companion. Never use a reassigned output's `.var`, which points to the target Case variable. Discover output names with `uip maestro case spec` for connectors or `uip maestro case tasks describe --output json` for non-connectors; never fabricate them. Read [bindings and expressions](references/bindings-and-expressions.md) and the [I/O resolver](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative) when this route is selected.
11. **Capture build-review preference once, up front, and preserve every later hard stop.** Phase 0 includes `Build it — straight through` / `Build it — pause at the build preview`; a provided-SDD run asks once immediately after its roadmap. Non-interactive, resumed, or legacy runs with no preference default to straight-through. At the Phase 2 boundary try advisory `validate --skeleton-v2`; fall back once to `--skeleton` only when the parser explicitly says `--skeleton-v2` is unknown/unsupported—exit 3 alone or genuine validation findings do not qualify. Name the profile and counts. Straight-through continues without a prompt or mid-build publish; pause-at-preview follows `Publish for review` / `Skip publish and continue` / `Abort` and prints `DesignerUrl` before its follow-up prompt. Regardless of preference, keep the Phase 4 third-failure stop (`Retry with fix` / `Pause for manual edit` / `Abort`), Phase 5 (`Publish to Studio Web` / `Skip to Debug`), and Phase 6 (`Run debug session` / `Done`). Preserve the current publish-then-debug order. Read [phased execution](references/phased-execution.md).
12. **Never run `uip maestro case debug` automatically.** It executes the Case for real and can send messages, call APIs, or mutate external systems. Run only after explicit user consent.
13. **Every skill artifact uses Read + Write/Edit only.** This includes Case/SDD/plan files, raw caches, sidecars, entry points, bindings, ID maps, and issue logs. Never use an interpreter, helper/assembler script, shell redirection/`tee`, or shell copy/move/install/rsync to open, parse, create, replace, rename, relocate, or save an artifact—including promoting `sdd.draft.md` to `sdd.md`. The `node -e ... fs.*` ban also covers resource-cache reads; use Read or a read-only `cat ... | python3 -c "..."` cache lookup. Shell subprocesses are allowed only for stdout-only UUID v4 generation for `operate.json.projectId` and entry-point `uniqueId` (no filesystem access/redirection), CLI metadata/scaffold/validate/debug/runtime/sync/upload operations, and directory setup. Pick prefixed IDs inline. Before any artifact mutation, read [tool usage and batching](references/case-editing-operations.md#tool-usage--mandatory).
14. **Resolved resources must be runnable, and sidecar parity is an unconditional Phase 3 exit gate.** Run Step 12 Checks 7, 9, and 11 even when refresh, publish, and debug are skipped. A non-null `selected` audit entry must map to a real, non-placeholder task. Non-connectors must keep `data.name` and `data.folderPath` bound through complete root bindings, project into `bindings_v2.json.resources[]`, and use a binding-pair `resourceKey` consistent with that pair's own defaults—not a copied tenant identity. Apply only the named targeted repair or one full sidecar regeneration, then recheck in the owner's bounded order; halt before Phase 4 while any mismatch remains. Repeat Check 7 before every resource refresh. Always refresh before upload/debug. Every `uip solution upload` must include `--output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`. At Step 12 read [case validation](references/case-validation-guide.md) and the routed sidecar/resource owners.
15. **Never auto-invoke `uipath-planner`.** For explicit cross-product planning, suggest its name in plain text; the user must invoke it.
16. **Case task `type` is a closed nine-value schema enum.** Use only `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `execute-connector-activity`, `wait-for-connector`, or `wait-for-timer`. The validated SDD type controls JSON; a cache identifier, plugin-folder name, or CLI spelling never rewrites it. Follow the naming-asymmetry table below and [task schema](references/case-schema.md#7-tasks--basetask-shape-shared).
17. **A genuine-empty batch requires one user gate before fallback.** After the normal pull and any existing-local sibling check, group all empties by `(name, type)`, list every usage, and label non-creatable kinds `placeholder only`. Ask once: `Force pull and re-resolve` (force-refresh, then repeat the gate for remaining empties), `Use placeholders for all`, or—only when `registry --local` is supported and at least one empty is an agent/API workflow—`Create missing resources inline`. Do not pre-judge names or load creation guidance before this choice. On Create, read the [shared selection/orchestration guide](references/inline-resource-creation-guide.md); only after its Select step read [create-inline-common.md](references/plugins/tasks/create-inline-common.md) and only the checked [agent](references/plugins/tasks/agent/inline-creation-guide.md) and/or [API-workflow](references/plugins/tasks/api-workflow/inline-creation-guide.md) guide. Build only selected resources; assign unchecked, non-creatable, skipped, unavailable-skill, or failed resources to fallback. Delegate only these selected sibling builds and degrade gracefully to visible fallback.
18. **Layout state is top-level only.** Emit `layout: {}`. Never emit node-level `position`, `style`, `measured`, `width`, `height`, or `zIndex`, compute positions, or emit edge `data.waypoints`. Read [structural operations](references/case-editing-operations.md) before scaffold writes.
19. **Generated output IDs share one global namespace.** Run blocking Step 12 Check 8 across root, task, trigger, and all connector-rule outputs at Phase 3 exit; repair only the later producer and its consumers, rescan, and do not enter Phase 4 until unique. CLI validate is not a substitute. Read [case validation](references/case-validation-guide.md).
20. **Edges are retired.** The `schema.edges: []` invariant is represented by current top-level `edges: []`; never author `TriggerEdge`, `Edge`, handles, or waypoints. Case start uses the first stage's `case-entered` condition, and transitions use target entry conditions plus divergent source exit conditions. Edge shapes are read-only in the [schema appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author).
21. **Model global events once; choose SLA responses from intent.** A global external event that requires work/routing belongs on one destination secondary stage as an interrupting `wait-for-connector` entry, never duplicated across primary stages. Choose exactly `notify-only`, `start-task`, `enter-stage`, `exit-stage`, or `exit-case`; absent a stated response, both at-risk and breach are notifications. `start-task` puts a follow-up task inside the breached stage with `sla-status-change` on that task's own entry—never stage re-entry. `enter-stage` uses a separate stage. Interrupting follows whether active work stops/pauses/reroutes, not SLA scope; `start-task` has none, and non-interrupting oversight stays a non-required secondary stage. Every status rule names the SLA; breach uses `slaId` alone, while at-risk also names an at-risk `escalationId` from that SLA. Never add an escalation to a breach or duplicate primary-stage routes. Read [SLA response shapes](references/sla-response-shapes.md) before the selected SLA/condition owner.
22. **Formal-argument slot IDs are synthetic and blocking.** Every `variables.inputs[].id` and `variables.outputs[].id` is `v` plus eight alphanumeric characters, distinct from readable `name`/`var` companions. Run Step 12 Check 10 at Phase 3 exit; re-mint a violation and update only its In-arg bridge when applicable, rescan, and halt before Phase 4 if invalid. CLI validate does not enforce this. Read the [formal-slot owner](references/plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format) and [case validation](references/case-validation-guide.md).
23. **Never run `uip maestro case init`.** Outside the intended solution it auto-creates a second manifest and forks the Case from its sibling resources, often failing only later. Keep one solution: follow [Implementation Step 6](references/implementation.md#step-6--create-the-case-project-structure)—`uip solution init <SolutionName>`, the T01 direct-JSON scaffold, then absolute-path `uip solution projects add`. The [command reference](references/case-commands.md#uip-maestro-case-init) explains the hazard; it does not authorize the command.

## Conditional owner routes

Read a destination only when its condition is true; these owners contain the algorithms and shapes.

| Condition | Direct owner to load before action |
|---|---|
| Phase 1 starts | [Planning](references/planning.md); after discovery reaches Step 4, [task-plan contract](references/tasks-plan-contract-guide.md) |
| First Case artifact mutation | [Case editing operations](references/case-editing-operations.md) |
| Brownfield operation selected | [Brownfield](references/brownfield.md); load [composites](references/brownfield-operations-guide.md) only for a row that selects one |
| Connector target selected | [Connector integration](references/connector-integration.md), then only the target owner; load [complex inputs](references/plugins/tasks/connector-activity/complex-inputs-guide.md) only when the discovered schema requires it |
| Output uses `->`, `=`, reassignment, or companion | [Output projection](references/plugins/variables/global-vars/output-projection-guide.md) before emission |
| Phase 3 exit begins | [Case validation](references/case-validation-guide.md) and [I/O exit validation](references/plugins/variables/io-binding/validation-guide.md) directly, before Check 1 |
| SLA recipient is not already a UUID | [Recipient resolution](references/plugins/sla/recipient-resolution-guide.md) before writing it |
| Debug/deployed run fails | [Troubleshooting](references/troubleshooting-guide.md); load an implementation owner only after confirming an artifact cause |

## Structural owners

| Object | Planning | Implementation |
|---|---|---|
| Root Case | [plan](references/plugins/case/planning.md) | [write](references/plugins/case/impl-json.md) |
| Stage | [plan](references/plugins/stages/planning.md) | [write](references/plugins/stages/impl-json.md) |
| SLA/escalation | [plan](references/plugins/sla/planning.md) | [write](references/plugins/sla/impl-json.md) |
| Global variables/arguments | [plan](references/plugins/variables/global-vars/planning.md) | [write](references/plugins/variables/global-vars/impl-json.md) |
| Task I/O | [plan](references/plugins/variables/io-binding/planning.md) | [write](references/plugins/variables/io-binding/impl-json.md) |
| Resource bindings / issue log | — | [bindings](references/plugins/variables/bindings/impl-json.md) / [logging](references/plugins/logging/impl-json.md) |

## Task owners and naming asymmetry

Only `Schema type` goes into `caseplan.json.type`; the folder selects the owner and CLI spelling is metadata-only.

| Schema type | Plugin folder | CLI `tasks describe --type` | Planning | Implementation |
|---|---|---|---|---|
| `process` | `process` | `process` | [plan](references/plugins/tasks/process/planning.md) | [write](references/plugins/tasks/process/impl-json.md) |
| `agent` | `agent` | `agent` | [plan](references/plugins/tasks/agent/planning.md) | [write](references/plugins/tasks/agent/impl-json.md) |
| `rpa` | `rpa` | `rpa` | [plan](references/plugins/tasks/rpa/planning.md) | [write](references/plugins/tasks/rpa/impl-json.md) |
| `action` | `action` | `action` | [plan](references/plugins/tasks/action/planning.md) | [write](references/plugins/tasks/action/impl-json.md) |
| `api-workflow` | `api-workflow` | `api-workflow` | [plan](references/plugins/tasks/api-workflow/planning.md) | [write](references/plugins/tasks/api-workflow/impl-json.md) |
| `case-management` | `case-management` | `case-management` | [plan](references/plugins/tasks/case-management/planning.md) | [write](references/plugins/tasks/case-management/impl-json.md) |
| `execute-connector-activity` | `connector-activity` | `connector-activity` | [plan](references/plugins/tasks/connector-activity/planning.md) | [write](references/plugins/tasks/connector-activity/impl-json.md) |
| `wait-for-connector` | `connector-trigger` | `connector-trigger` | [plan](references/plugins/tasks/connector-trigger/planning.md) | [write](references/plugins/tasks/connector-trigger/impl-json.md) |
| `wait-for-timer` | `wait-for-timer` | no describe | [plan](references/plugins/tasks/wait-for-timer/planning.md) | [write](references/plugins/tasks/wait-for-timer/impl-json.md) |

## Trigger owners

| Trigger | Planning | Implementation |
|---|---|---|
| Manual | [plan](references/plugins/triggers/manual/planning.md) | [write](references/plugins/triggers/manual/impl-json.md) |
| Timer | [plan](references/plugins/triggers/timer/planning.md) | [write](references/plugins/triggers/timer/impl-json.md) |
| External event | [plan](references/plugins/triggers/event/planning.md) + [common](references/connector-trigger-common.md) | [write](references/plugins/triggers/event/impl-json.md) + [common](references/connector-trigger-common.md) |

## Condition owners

| Scope | Planning | Implementation |
|---|---|---|
| Stage entry | [plan](references/plugins/conditions/stage-entry-conditions/planning.md) | [write](references/plugins/conditions/stage-entry-conditions/impl-json.md) |
| Stage exit | [plan](references/plugins/conditions/stage-exit-conditions/planning.md) | [write](references/plugins/conditions/stage-exit-conditions/impl-json.md) |
| Task entry | [plan](references/plugins/conditions/task-entry-conditions/planning.md) | [write](references/plugins/conditions/task-entry-conditions/impl-json.md) |
| Case exit | [plan](references/plugins/conditions/case-exit-conditions/planning.md) | [write](references/plugins/conditions/case-exit-conditions/impl-json.md) |

For a selected connector-bound `wait-for-connector` condition, additionally read the [target rule contract](references/connector-trigger-common.md#target-connector-bound-condition-rule); never load every condition owner.
