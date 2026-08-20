---
name: uipath-maestro-case
description: "Always invoke for UiPath Maestro Case Management: `caseplan.json`, `sdd.md`, or a case with no SDD yet (design-first). `.xaml`→uipath-rpa, `.flow`→uipath-maestro-flow, `.bpmn`→uipath-maestro-bpmn; case SDD/`sdd.draft.md`/PDD→SDD/cross-product→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Build UiPath Case Management definitions from `sdd.md`. Generate `tasks.md`, then write `caseplan.json` directly using the applicable per-plugin JSON recipes.

> **Authoring invariant:** Never use mutating `uip maestro case` commands (`cases|stages|tasks|*-conditions ... add|update|remove`, including `tasks add-connector`) or explore them with `--help`. Use the CLI only for scaffolding, metadata reads, validation/debug, runtime operations, and solution sync/upload. Consult [case-commands.md](references/case-commands.md) only when exact syntax is needed. CLI availability or a final `validate` requirement never overrides this rule.

When `sdd.md` is absent, case design belongs exclusively to **`uipath-planner`**, which runs its Case Design Lane in this conversation. This skill never designs independently. The lane uses best-assumption design, Listen → Sketch → full design-time tenant resolution, a mandatory other-path sweep, and one decision-first eight-section Case Review. Its Build answer is consent; it writes template-conformant `sdd.md`, then this skill continues immediately with `uip solution init`, Phase 1, and later phases. The same handoff applies to `sdd.draft.md` finalization. Never overwrite an existing `sdd.md`.

**Scope:** greenfield builds from `sdd.md` and brownfield targeted edits to an existing `caseplan.json`; see [references/brownfield.md](references/brownfield.md). For Studio Web cases, pull current server state first with `uip solution download` or `solution projects resync` so publishing cannot clobber server changes.

## When to Use This Skill

Use for:

- Building a Case Management project from `sdd.md`.
- Creating a case when no SDD exists; hand design to `uipath-planner` in this conversation.
- Generating implementation tasks from an SDD.
- Editing an existing `caseplan.json` by targeted intent: stage/task changes, conditions, or triggers.
- Questions about case JSON schema, nodes, transitions, tasks, rules, SLA, or runtime case instances.

Do not use for `.xaml` → `uipath-rpa`, `.flow` → `uipath-maestro-flow`, or standalone agents/APIs/processes outside case context.

## Critical Rules

1. **Design handoff and SDD authority.** If `sdd.md` is absent, immediately invoke `uipath-planner`’s Case Design Lane in this conversation, before reading references or running tenant commands. Do not improvise interviews, design subagents, generic Build Plan approvals, or design-only behavior here. The lane’s single Case Review has exactly these sections: Case Snapshot; Primary Journey; Other Paths Considered; SLA and Escalations; Rules and Outcomes; Resources and Integrations with design-time resolutions; Decisions I Made; Review Flags. It names every stage/task, type, activation/grouping, required status, routing/outcome, and SLA context; `sdd.md` separately contains the complete data contract, variables, and task inputs/outputs. The Build options incorporate Rule 11, and the Build answer is the sole consent. Corrections re-show only changed review sections. Before approval, every `selected-tasks-completed` selector must resolve to a non-adhoc sibling in the same stage. The lane writes `sdd.md` early, then this skill runs `uip solution init <SolutionName>` and Phase 1 without another prompt unless explicitly requested. If the request asks only for `sdd.md` plus `tasks/tasks.md`, write compact `tasks/tasks.md` after Save/Build, do not read plugin references or run tenant discovery, and stop before `caseplan.json`. If `sdd.draft.md` is to be finalized, use the lane fast path with target basename `sdd.md`. Never overwrite `sdd.md`.
2. **SDD is the sole post-design input, across sessions.** Trust user-provided or previously written `sdd.md`; do not validate, gap-fill, or silently infer it. In the same conversation as design approval, use the in-memory model that wrote it without rereading. Use AskUserQuestion for build-phase ambiguity. Run a one-Grep receipt spot-check before reading an SDD not watched being written: it must contain `## Section 1: Case Definition` through `## Section 4: Integrations` and at least one `##### Task` block. Freeform/summary SDDs go back through the planner template-conformance gate.
3. **Phase 1 registry gate.** Run `uip login status --output json`, then `uip maestro case registry pull`, before cache inspection, carryover, resolution, or Phase 1 writes. Pull at most once per session. If the planner lane ran in this session, its pull succeeded, and it wrote the SDD, reuse the cache. With the lane’s in-context resolution outcomes, use verify-only planning: persist them verbatim to `tasks/registry-resolved.json`, spot-check cache entries, execute gate decisions, and re-resolve only stale/missing entries. Otherwise run the full gate. Login/pull failure stops Phase 1. Read `~/.uip/case-resources/<type>-index.json` directly; `registry search` has known gaps, especially action-apps. Before a successful pull, missing cache files are failed refresh preconditions, never zero matches; only after success may empty exact-name matches or absent indexes enter empty-lookup handling. Trust the SDD; the pull refreshes discovery only. The planner lane owns design-time resolution, lazily starting login/pull when tenant-bound work first appears, resolving identities with one batched Case Review gate, and recording SDD cells plus its resolution ledger. No schema discovery occurs there.

   **Plan-only exception:** when explicitly stopping at `sdd.md`, `sdd.draft.md`, or `tasks.md` without `caseplan.json`, solution, or build, do not run tenant registry, connection, schema, or user-discovery commands. Preserve intended names, mark identities `resolve at build`, and report deferred wiring. This exception does not apply when the user requests resource/identity resolution, registry refresh, stale-audit replacement, `tasks/registry-resolved.json`, or `tasks/recipients-resolved.json`; then run the normal gate, resolve identities, emit build-path `tasks.md`, and stop at the Rule 7 plan gate.
4. **Parsed reads require `--output json`.**
5. **Use plugin references.** Read the matching plugin `planning.md` during planning and `impl-json.md` during execution; never guess JSON shapes.
6. **`tasks.md` is declarative and lossless.** No shell commands. Use plain field identifiers, not CLI flags. Create one T-entry for every SDD stage, task, trigger, condition, SLA rule, variable, and argument, including explicit defaults. Preserve every valid explicit rule/selector exactly; reject and repair invalid `selected-tasks-completed` selectors. Preserve stage/task/SLA `Design Rationale` and condition routing/activation rationales as `rationale:`. Preserve every Inputs row, binding mode, and value. Preserve JSON object literals exactly: native object or JSON-encoded string in `input.value`; add `=js:`/`=jsonString:` only when explicitly present in the SDD. Project Outputs through [`plugins/variables/io-binding/planning.md`](references/plugins/variables/io-binding/planning.md#sdd-outputs-table-to-tasksmd-projection-mandatory), preserving operator and operands. SDD output rows require `->` or `=`; schema-discovered bare outputs are not authored SDD rows. Never simplify equal-name `->` rows; `greeting -> greeting` differs from schema-discovered bare `greeting`. `—` placeholders are not operands. AskUserQuestion for unrecognized or ambiguous rows; never omit silently. Regenerate greenfield plans from scratch; brownfield edits preserve IDs. Every §4.6 task entry has its own `activation-mode:` and `entry-rule:` — repeat this per task, never author it once and drop it for later similar tasks; `validate` only warns `Task has no entry rules`, while a miss hangs `case debug` indefinitely. Every task heading is exactly `## T<n>: Add <type> task "<name>" to "<stage>"`. See [references/planning.md §4.0](references/planning.md) and the [Plan-shape gate](references/planning.md#step-5--finalize-tasksmd-auto-proceed-to-phase-2).
7. **Plan gate.** Phase 1 auto-proceeds to Phase 2 and treats the plan as approved. Stop after `tasks.md` only when the request explicitly says plan-only, Phase 1 only, review first, or not to build. Re-read `tasks.md` before execution.
8. **Unresolved resources.** Never fabricate IDs. Keep `<UNRESOLVED: ...>` in `tasks.md`. A placeholder task has `type`, `displayName`, structural fields, and `data: {}`; conditions still reference its TaskId. A placeholder event trigger has render fields and only `data.inputs: { serviceType: "Intsvc.EventTrigger" }`; append its `entry-points.json` entry and create no trigger edge. See [references/placeholder-tasks.md](references/placeholder-tasks.md) and [references/plugins/triggers/event/impl-json.md](references/plugins/triggers/event/impl-json.md).
9. **Resolution audit.** Persist one object per task in `tasks/registry-resolved.json` with exact keys `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, and `rationale`, plus resolved I/O/review metadata. Add `gateDecision` only when the user answered the design-time resource gate; default deferrals have none. `matches` is the complete exact-name set from the refreshed cache; `selected` is a match or `null` after a genuine empty lookup. Same-session planner ledgers are persisted verbatim, then verified/extended under Rule 3. The resolution ledger and `registry-resolved.json` are machine-only — never shown to the user, including in the Case Review.
10. **Cross-task references.** Use `"Stage Name"."Task Name".output_name` and the common output-reference-ID algorithm in [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative). Use the source output’s `.id`; only a custom `=` output without `.id` uses its verified root companion’s `.id`. Never use a reassigned output’s `.var`. Discover names with `uip maestro case spec` for connector tasks or `uip maestro case tasks describe` for non-connectors. In larger `=js:` expressions use `vars.$xref('Stage','Task','output')`, resolved at Step 11.5. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md).
11. **Build-review preference.** Capture once at journey start. Design handoff folds it into the Case Review Build options (`Build it — straight through` or `Build it — pause at the build preview`); provided SDD asks once after the roadmap. Non-interactive and resumed runs without a preference default to straight-through. At Phase 2→3, try `validate --skeleton-v2`; fall back once to legacy `--skeleton` only when the response explicitly says v2 is unknown/unsupported, typically invalid_argument/exit 3. Exit 3 alone is insufficient; real v2 failures are reported. Validation findings do not halt this advisory gate. Straight-through continues without prompting. Pause-at-preview follows [references/phased-execution.md](references/phased-execution.md): AskUserQuestion `Publish for review` / `Skip publish and continue` / `Abort`; on publish, refresh resources, upload with the required filter, print `DesignerUrl` before the follow-up, then ask `Continue to implementation` / `Abort`. Hard stops always remain at Phase 4 retry exhaustion, Phase 5, Phase 6, and Phase 7.
12. **Never auto-debug or publish to Orchestrator.** `uip maestro case debug` executes real emails, messages, and API calls. Phase 7 (`case pack` → `solution pack` → `solution publish`) ships to the tenant. Each requires its own AskUserQuestion consent.
13. **Artifact I/O.** For `caseplan.json`, `sdd.md`, `sdd.draft.md`, `tasks.md`, `tasks/registry-resolved.json`, `tasks/trigger-spec-cache.json`, `tasks/spec-cache.<elementId>.json`, `bindings_v2.json`, `id-map.json`, `entry-points.json`, and `build-issues.md`, use only Read and Write/Edit. No Python, Node, jq, sed, awk, scripts, shell redirection, `tee`, `cp`, `mv`, `install`, or `rsync`; no helper scripts, including under `/tmp`. The `node -e ... fs.*` ban covers all file reads, including `~/.uip/case-resources/`; use Read or `cat ... | python3 -c ...` for cache lookup. If `caseplan.json` exceeds about 30KB, use the preview/detail cadence in [case-editing-operations.md](references/case-editing-operations.md), never a helper. Bash is allowed only for UUID v4 generation without filesystem access, CLI metadata, validate, debug, and solution scaffold/upload. Prefixed IDs are chosen inline.
14. **Runnable resources and sidecars.** Before Phase 4, run Step 12 Checks 7, 9, 11, and 12 even when publish, debug, or resource refresh is skipped. A non-null `selected` resource must not become a placeholder: retain `data.name` and `data.folderPath` with complete root bindings, project it into `bindings_v2.json.resources[]`, and make its `resourceKey` self-consistent with its own defaults, never a copied tenant identity/UUID. Checks 9/11 exempt connector nodes; Check 12 covers resolved connector tasks, event triggers, and `wait-for-connector` rules, which require spliced `caseShape.context` plus Connection/Folder root bindings, not degraded typeId/connectionId-only data. CLI validate is insufficient. Repair and recheck mismatches; halt before Phase 4 if they remain. Repeat Check 7 before every `resources refresh`. Refresh before every upload or debug. Every upload uses `--output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`; print the returned DesignerUrl.
15. **Handoff contract.** Invoke `uipath-planner`’s Case Design Lane in this conversation, never as a subagent. It owns design, resolution, review, and SDD writing; this skill resumes at solution initialization. User-facing language presents one continuous flow and never mentions the handoff. If unavailable, say so in one line, request `sdd.md` or an approved pasted design, and stop. Cross-product planning remains a plain-text suggestion to the planner. Apply the Rule 15 receipt spot-check before unobserved SDD reads.
16. **Closed task types.** `caseplan.json` task `type` must be exactly one of: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `execute-connector-activity`, `wait-for-connector`, `wait-for-timer`. Never use plugin folder or CLI names, `external-agent`, `external-workflow`, `document-extraction`, `flow-process`, `wait-for-event`, or other invented values. The unsupported types remain unsupported. See [references/case-schema.md](references/case-schema.md) and the Plugin Index.
17. **Empty lookup gate.** If the same-session ledger has a user `gateDecision`, execute it without asking again: `resolve-at-build` → placeholder; `create-during-build` → inline create; `pick:<name>` → bind it. A missing decision is a default deferral, not consent; run the full gate. For zero matches, use one batched AskUserQuestion grouped by `(name,type)` with: `Force pull and re-resolve`; `Use placeholders for all`; and, only when creatable resources exist and `registry --local` is supported, `Create missing resources inline`. Create only selected `agent` or `api-workflow` resources, invoking `uipath-agents` or `uipath-api-workflow`; never infer Create from SDD content. Other empty types remain placeholder-only. Selected resources with identical I/O may share one build; differing I/O splits later with the anchor retaining the name, and SDD updates require permission. See [registry-discovery.md § 1c](references/registry-discovery.md#1c--dedup-the-selected-builds-one-resource-per-name-and-type), [Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery), and [§ MUST Confirm](references/registry-discovery.md#must-confirm-before-placeholder-fallback).
18. **Layout.** Emit top-level `layout: {}` only. Do not emit node `position`, `style`, `measured`, `width`, `height`, `zIndex`, or edge `data.waypoints`; do not compute positions.
19. **Global output IDs.** Run Step 12 Check 8 once at Phase 3 exit. It is mandatory; do not enter Phase 4 until it passes and do not substitute CLI validate.
20. **No authored edges.** Keep `schema.edges` as `[]`; never author TriggerEdge/Edge objects. Conditions provide stage flow; the first stage uses `case-entered`. Read-only edge shapes are documented in [case-schema.md Appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author).
21. **Global events and SLA responses.** Model a global external event once as an interrupting secondary-stage `wait-for-connector` entry. Choose SLA response explicitly: `notify-only`, `start-task`, `enter-stage`, `exit-stage`, or `exit-case`. A `start-task` response belongs on the follow-up task’s own `sla-status-change` entry, not a stage entry. Interrupting depends on whether active work stops, pauses, or reroutes; parallel oversight uses `Interrupting: No` and remains secondary. `sla-status-change` names `slaId`; add `escalationId` only for at-risk responses. Without a stated response, at-risk and breach are notifications. Do not replicate rules across primary stages. See [references/sla-response-shapes.md](references/sla-response-shapes.md) and the SLA Response Map.
22. **Formal argument IDs.** `variables.inputs[].id` and `variables.outputs[].id` must be synthetic `v` + 8 characters and distinct from `name`/`var`; never copy companion names. Run Step 12 Check 10 once at Phase 3 exit and non-interactively re-mint violations. CLI validate does not check this. See [global-vars/impl-json.md § Formal-arg slot ID format](references/plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format).
23. **Never run `uip maestro case init`.** It may create a second solution and separate manifest. Use `uip solution init <SolutionName>` and the T01 direct-JSON scaffold in [implementation.md § Step 6](references/implementation.md#step-6--create-the-case-project-structure). See [case-commands.md § case init](references/case-commands.md#uip-maestro-case-init).
24. **Read references to EOF before mutation.** Every `references/*.md` ends with `<!-- END: <filename> -->`. Before the first Write/Edit using a shape, procedure, constraint, or verification rule, Read that exact reference until its exact END marker appears in tool output during this session. Ranges, truncation, search hits, tables of contents, memory, and sibling references do not satisfy this. Reopen after compaction or when the prior read is unavailable. Keep reads modest to avoid output truncation. Tail contracts are normative.
25. **Unique labels and task names.** Stage `data.label` values are unique case-wide; task `displayName` values are unique across all stages, exact and untrimmed, and contain no `:`. A missing display name binds to the resource name and participates in uniqueness. Assign names in Phase 1; later renaming touches the SDD, plan, ID map, and name-keyed references.

## Routing

| Condition | Journey |
|---|---|
| New case, SDD provided, no caseplan, or rebuild from spec | **Greenfield:** handoff if needed, then Phases 1–7 |
| Existing caseplan and targeted edit intent | **Brownfield:** skip handoff and Phases 1–7; use [brownfield.md](references/brownfield.md) |

Brownfield still requires latest-state pull, debug consent, and Orchestrator-publish consent, and reuses Phase 5–7 contracts.

## User-Facing Roadmap

Print once, after routing and before detailed work, in five lines or fewer. Do not expose phases, modes, filenames, or implementation mechanics.

- **New case without SDD:** `1. I read your request and make the design calls, checking your UiPath tenant along the way. 2. One review packet: case snapshot, primary journey, other paths, SLA responses, business rules, resources, and every decision I made — you confirm or correct. 3. Build and validate without interruptions; the full technical design doc is saved alongside for reference. 4. Pause for your call before any run or publish.`
- **New case with SDD:** `1. Read the design and verify available UiPath resources. 2. One question: build straight through, or pause at a mid-build preview. 3. Plan, build, and validate without further interruptions. 4. Pause for your call before any run or publish.`
- **Targeted edit:** `1. Pull the latest case. 2. Apply the requested change. 3. Validate the updated case. 4. Ask before running or publishing anything.`

## Workflow

Front-load decisions, then run unattended to consent gates:

**Design handoff when required → Phase 1 Planning → Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Publish → Phase 6 Debug → Phase 7 Publish to Orchestrator.**

At invocation start, present once the matching kickoff block below, at handoff start or Phase 1 start. Status text must follow the Anti-patterns limits.

**Greenfield kickoff:**

> Here's how I'll build this case, and where I'll stop for your call:
> - **Planning** — I draft a task plan from the spec and continue; ask up front if you want to review it first.
> - **Prototyping** — I build the reviewable case flow (stages, tasks, triggers, rules, SLA/escalation; connector rules use stubs). Whether I pause here for a Studio Web preview is **your up-front call** — asked once at the start, never mid-build.
> - **Implementation** — I wire task inputs/outputs, connector schemas, and resolved connector-rule details.
> - **Validate** — I run validation and fix errors.
> - **Publish** (optional) — **you choose** whether to upload to Studio Web.
> - **Debug** (optional) — **you choose** whether to run the case for real (live emails / API calls).
> - **Publish to Orchestrator** (optional) — **you choose** whether to publish the case to Orchestrator.

For handoff, prefix: `First I'll design the case from what you've given me — checking your UiPath tenant along the way — and show one decision-first review packet with the case snapshot, primary journey, other paths, SLA responses, business rules, resources, and every decision made — one confirmation, then I build; the full technical design doc (sdd.md) is saved alongside for reference.`

For brownfield, use the short entry flow in [references/brownfield.md](references/brownfield.md).

### Design handoff

The trigger is binary: if no `.md` whose basename contains `sdd` exists at the resolved path, hand off. If the prompt names another SDD basename, copy it to `./sdd.md` using Read + Write; do not invoke the lane. If no `.md` is named, use `./sdd.md`. Do not read planning/plugin references or run tenant commands before the Case Review. For an explicit no-build design+plan request, write `sdd.md` and compact `tasks/tasks.md` after approval, without plugin references, schema, registry, connection, or user discovery, then stop. Planner-owned drafts and `sdd-viewer.html` stay with the planner. If unavailable, request an SDD and stop.

### Phase 1 — Planning

Read [references/planning.md](references/planning.md) to produce:

- `tasks/tasks.md`: T-numbered stages, tasks, conditions, SLA, variables, and arguments.
- `tasks/registry-resolved.json`: complete resolution audit.
- If Create is selected at Rule 17: build selected agents/API workflows as in-solution siblings through the permitted sub-agent paths, ensure a solution exists, register them, refresh resources, rediscover, and bind them. See [registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery).

`tasks/` is adjacent to `sdd.md`, never inside the solution/project. Auto-proceed to Phase 2 unless the request explicitly asks to stop for plan review. Re-read `tasks.md` first.

### Phase 2 — Prototyping

Read [references/implementation.md](references/implementation.md) and [references/phased-execution.md](references/phased-execution.md). Follow Steps 6–11.9:

1. Step 6: `uip solution init`, project, and root case (T01 direct-JSON recipe in [plugins/case/impl-json.md](references/plugins/case/impl-json.md)); never `case init`.
2. Step 6.1: manual, timer, and event triggers, including Rule 8 placeholders; capture trigger IDs.
3. Step 6.2: global variables and arguments; In-argument `elementId` references the trigger named by `sourceTriggers`, or the primary trigger when blank.
4. Step 6.3: synchronize `entry-points.json` from declared In/Out arguments per [entry-points-sync.md](references/entry-points-sync.md). Emit the `job-attachment` `definitions` block byte-for-byte from that reference — reproduce its `MimeType.description` inner quotes exactly (single-`\"` escaping); never re-escape (`\\"`) or rebalance them, or the JSON breaks.
5. Step 7: stages.
6. Step 9: task shapes; non-connectors get complete `data.inputs[]` with empty values, connectors only `typeId`/`connectionId`, unresolved resources use placeholders.
7. Step 11: SLA/escalation objects with stable IDs.
8. Step 10: all four condition scopes; connector waits use canonical stubs regardless of resolution.
9. Step 11.9: informational skeleton validation with Rule 11 fallback behavior.
10. Apply the Phase 2→3 preference. Preview branch uses resource refresh, filtered solution upload, printed DesignerUrl, and the prescribed continuation gate; Abort writes `build-issues.md` and exits.

### Phase 3 — Implementation

Re-read `tasks.md` and `caseplan.json` (Step 9.6), then follow Steps 9.7, 9.8, 10.5, and 11.5:

1. Resolve connector schemas/defaults with `uip maestro case spec`.
2. Bind I/O for all task classes using [io-binding/impl-json.md](references/plugins/variables/io-binding/impl-json.md).
3. Upgrade resolved connector-bound condition stubs in place; unresolved connectors retain stubs and are reported.
4. Resolve in-expression `vars.$xref` markers.
5. Perform resolved-resource emission, preservation, resourceKey, and connector completeness checks.

Proceed directly to Phase 4 after the Phase 3 checks pass.

### Phase 4 — Validate

Run Step 12 once at the Phase 3 boundary. It performs Checks 1–15, including Check 7 sidecar parity, Check 8 global output-ID uniqueness, Check 9 resource emission/preservation, Check 10 formal-arg IDs, Check 11 resourceKey consistency, Check 12 connector completeness, and Check 15 every task carrying a non-empty entry rule (`validate` only warns on a missing one). Then run full `uip maestro case validate`. Retry at most three times, with an edit before every retry; on the third failure, hard-stop with AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`. Summarize `build-issues.md` using Step 12.1.

### Phase 5 — Publish

Provide the completion report, then hard-stop AskUserQuestion: `Publish to Studio Web` / `Skip to Debug` (Step 13). On publish, refresh resources and upload with the mandatory output filter, print DesignerUrl, and continue to Phase 6 either way.

### Phase 6 — Debug

Hard-stop AskUserQuestion (Step 15): `Run debug session` / `Continue to publish`. On Run, refresh resources, run `uip maestro case debug`, and loop after completion until `Continue to publish`. Never run debug automatically.

### Phase 7 — Publish to Orchestrator

Hard-stop AskUserQuestion (Step 16): `Publish to Orchestrator` / `Done`. On publish, run in order:

1. `uip solution resources refresh`
2. `uip maestro case pack <SolutionDir>/<ProjectName> <SolutionDir>/dist --output json`
3. `uip solution pack <SolutionDir> <SolutionDir>/dist --output json`
4. `uip solution publish <packagePath> --wait --output json`

`case pack` is mandatory because it creates `caseplan.json.bpmn`; `validate` does not. Publish the `solution pack` `.zip`, not the case `.nupkg`; read `<packagePath>` from `Data.Packages`, never guess. `Done` exits.

## Reference Navigation

| Need | Reference |
|---|---|
| Design without SDD | `uipath-planner` Case Design Lane; Rule 15 |
| Plan from SDD | [references/planning.md](references/planning.md) |
| Execute plan | [references/implementation.md](references/implementation.md) |
| Brownfield edit | [references/brownfield.md](references/brownfield.md) |
| Phase contracts | [references/phased-execution.md](references/phased-execution.md) |
| Edit mechanics | [references/case-editing-operations.md](references/case-editing-operations.md) |
| Schema | [references/case-schema.md](references/case-schema.md) |
| Allowed CLI | [references/case-commands.md](references/case-commands.md) |
| Troubleshooting | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Registry resolution | [references/registry-discovery.md](references/registry-discovery.md) |
| Bindings/expressions | [references/bindings-and-expressions.md](references/bindings-and-expressions.md) |
| Connector integration | [references/connector-integration.md](references/connector-integration.md) |
| Case spec input details | [references/case-spec-input-details.md](references/case-spec-input-details.md) |
| Placeholders | [references/placeholder-tasks.md](references/placeholder-tasks.md) |
| Bindings sidecar | [references/bindings-v2-sync.md](references/bindings-v2-sync.md) |
| Prune orphaned solution resource | [bindings-v2-sync.md § Prune orphaned solution resources](references/bindings-v2-sync.md#prune-orphaned-solution-resources) |
| Entry points | [references/entry-points-sync.md](references/entry-points-sync.md) |
| SLA responses | [references/sla-response-shapes.md](references/sla-response-shapes.md) |

### Plugin Index

**Structural:** [case/planning.md](references/plugins/case/planning.md), [stages/planning.md](references/plugins/stages/planning.md), [sla/planning.md](references/plugins/sla/planning.md), [global-vars/planning.md](references/plugins/variables/global-vars/planning.md), [io-binding/planning.md](references/plugins/variables/io-binding/planning.md), and [logging/impl-json.md](references/plugins/logging/impl-json.md).

**Tasks:**

| Schema `type` / SDD value | Plugin planning reference | CLI describe type |
|---|---|---|
| `process` | [process](references/plugins/tasks/process/planning.md) | `process` |
| `agent` | [agent](references/plugins/tasks/agent/planning.md) | `agent` |
| `rpa` | [rpa](references/plugins/tasks/rpa/planning.md) | `rpa` |
| `action` | [action](references/plugins/tasks/action/planning.md) | `action` |
| `api-workflow` | [api-workflow](references/plugins/tasks/api-workflow/planning.md) | `api-workflow` |
| `case-management` | [case-management](references/plugins/tasks/case-management/planning.md) | `case-management` |
| `execute-connector-activity` | [connector-activity](references/plugins/tasks/connector-activity/planning.md) | `connector-activity` |
| `wait-for-connector` | [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) | `connector-trigger` |
| `wait-for-timer` | [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md) | `wait-for-timer` |

Schema-kebab is the only JSON value; plugin and CLI names are not interchangeable. Unsupported types include `external-agent`, `external-workflow`, `document-extraction`, `flow-process`, and `wait-for-event`.

**Triggers:** [manual](references/plugins/triggers/manual/planning.md), [timer](references/plugins/triggers/timer/planning.md), and [event](references/plugins/triggers/event/planning.md).

**Conditions:** [stage-entry-conditions](references/plugins/conditions/stage-entry-conditions/planning.md), [stage-exit-conditions](references/plugins/conditions/stage-exit-conditions/planning.md), [task-entry-conditions](references/plugins/conditions/task-entry-conditions/planning.md), and [case-exit-conditions](references/plugins/conditions/case-exit-conditions/planning.md).

Connector-bound rules in any condition scope require `rule.uipath` built from `case spec --type trigger`; bare connector rules are invalid in Studio Web even when CLI validate passes. See [connector-trigger-impl.md](references/connector-trigger-impl.md).

## Anti-patterns

- Do not leave a regular stage without an entry condition. The first stage uses `case-entered`; every other regular stage needs a reachable predecessor. Edges are retired.
- Do not design here, start Phase 1 before Case Review approval, or build from a summary SDD. The planner owns design, other-path analysis, and template conformance.
- Do not validate after each T-entry or validate twice without an intervening edit. Phase 2 validation is informational; Phase 4 validation is authoritative.
- Write `tasks.md` with a seeded header and per-section batched Edit-appends: §4.2.1 variables, §4.3 triggers, §4.4 stages, §4.6 tasks, §4.7 conditions, and §4.8 SLA. Never write per T-entry, use a mega-Write, or exceed a 30KB single Edit payload. Recovery re-reads and resumes at the next unapplied entry. See [planning.md §4.0a](references/planning.md).
- Write `caseplan.json` by section, preserving untouched siblings — never one Write for the whole file. Read once at section entry; use per-entry Edits for fewer than 10 entries, or one Write covering only that section's container (the stages array, or one stage's task array) for 10 or more; gather CLI-gated sections before writing. Cap any single Write at ~15K output tokens / ~40KB; split a case with ≥40 tasks or ≥8 stages across the Phase 2 and Phase 3 writes rather than emitting the fully populated file at once. Re-read both files after interruption. See [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical).
- Do not emit standalone narration between tool calls. Bundle status with the next tool call; keep ordinary text under 200 tokens and allow-listed kickoff, hard-stop preambles, completion reports, DesignerUrl prints, and validation summaries under 500. Do not announce imminent actions with verbs such as `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next`, `Approach`, `Strategy`, `Plan`, `Let me`, or equivalent.
- Preserve ordered task semantics. Sequential mode uses ordered `data.tasks` sets and one `runs-sequentially` rule per task; do not add `current-stage-entered` alongside it. Use parallel `current-stage-entered` only for independent work and `selected-tasks-completed` only for required fan-in. Event-triggered tasks use event/condition rules; manually triggered/adhoc tasks use one `adhoc` rule, `isRequired: false`, and no additional entry event. `adhoc` is an activation mode, not a task type.
- Model secondary stages as interrupting exception lanes: `case-management:Stage`, `data.stageType: "secondary"`, `isRequired: false`, and `Interrupting: Yes` on stage and entries. Use `Interrupting: No` only for parallel SLA oversight. Use `return-to-origin`; do not connect secondary stages as normal flow or count them in required completion.
- Do not replicate global events or SLA rules across primary stages. Case completion requires a root `metadata.caseExitRules[]` rule with `marksCaseComplete: true`; stage completion alone is insufficient. Non-completing outcomes use `marksCaseComplete: false`.
- Do not edit generated `caseplan.json.bpmn`; do not place `caseplan.json` under `content/`; do not fabricate conditional-SLA expression syntax; describe conditions naturally until execution resolves them.
- Do not place `tasks/` in the solution/project; it stays beside `sdd.md`.
- Do not invoke other skills automatically except Rule 15 design handoff and Rule 17’s gate-selected inline creation of agents/API workflows. Do not spawn subagents for design, draft finalization, or plan-only documents.
- Use `uipath-feedback` for trouble.

> **Trouble?** Use `/uipath-feedback` to send a report.
