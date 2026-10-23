---
name: uipath-maestro-case
description: "Always invoke for UiPath Maestro Case Management build work: `caseplan.case`/`caseplan.json` (Studio Web: `case.stage.json`, `default.stage.json`), `sdd.md`, or creating a case with no SDD yet (design produced, then confirmed in one review). Resolves tenant resources, then authors/edits caseplan.case directly. .xaml→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn. Standalone case SDD design, case `sdd.draft.md` finalization, PDD→SDD, cross-product planning→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Build UiPath Case Management definitions from `sdd.md`: resolve tenant resources into `tasks/registry-resolved.json`, run `uip maestro case sdd convert`, then fill only what the SDD/converter cannot determine with applicable plugin JSON recipes. The SDD is authoritative; no intermediate plan exists; `caseplan.case` is derived.

> **Authoring invariant:** Never use or explore with `--help` any mutating `uip maestro case` command (`cases|stages|tasks|*-conditions ... add|update|remove`, including `tasks add-connector`). Use the CLI only for scaffolding, metadata reads, validation/debug, runtime operations, and solution sync/upload. Consult [case-commands.md](references/case-commands.md) only when exact syntax is needed; availability or a final `validate` requirement never overrides this rule.

If `sdd.md` is absent, design belongs exclusively to **`uipath-planner`**, which runs its Case Design Lane here: best-assumption design; Listen → Sketch → full design-time tenant resolution; mandatory other-path sweep; one decision-first eight-section Case Review; Build answer as consent; template-conformant `sdd.md`; then this skill continues immediately with
<!--skill-flavor:design-handoff-next-step:start-->
`uip solution init`, Phase 1,
<!--skill-flavor:design-handoff-next-step:end-->
and later phases. The same applies to finalizing `sdd.draft.md`. Never overwrite an existing `sdd.md`.

**Scope:** greenfield builds from `sdd.md` and brownfield targeted edits to `caseplan.case`; see [references/brownfield.md](references/brownfield.md). For Studio Web cases, pull current server state first with `uip solution download` or `solution projects resync` so publishing cannot clobber server changes.

## When to Use This Skill

Use for greenfield Case Management builds, SDD implementation, targeted `caseplan.case` edits, case JSON/schema, node, transition, task, rule, SLA, or runtime-instance questions. For no SDD, hand design to `uipath-planner` here. Do not use for `.xaml` → `uipath-rpa`, `.flow` → `uipath-maestro-flow`, or standalone agents/APIs/processes outside case context.

## Critical Rules

1. **Design handoff and authority.** If `sdd.md` is absent, immediately invoke `uipath-planner`’s Case Design Lane here before references or tenant commands; do not improvise interviews, design subagents, generic Build Plan approvals, or design-only behavior. Its single Case Review has exactly: Case Snapshot; Primary Journey; Other Paths Considered; SLA and Escalations; Rules and Outcomes; Resources and Integrations with design-time resolutions; Decisions I Made; Review Flags. It names every stage/task, type, activation/grouping, required status, routing/outcome, and SLA context; `sdd.md` separately contains the complete data contract, variables, and task inputs/outputs. Build options incorporate Rule 12 and the Build answer is sole consent; corrections re-show only changed sections. Before approval, every `selected-tasks-completed` selector must resolve to a non-adhoc sibling in the same stage. The lane writes `sdd.md` early, then this skill runs
<!--skill-flavor:design-handoff-rule-next-step:start-->
`uip solution init <SolutionName>` and Phase 1
<!--skill-flavor:design-handoff-rule-next-step:end-->
without another prompt unless explicitly requested. A design-only request stops after `sdd.md` per Rule 3's design-only exception; finalize `sdd.draft.md` through the lane fast path with target basename `sdd.md`. Never overwrite `sdd.md`.

2. **SDD authority.** `sdd.md` is the sole post-design input across sessions: trust it, do not validate, gap-fill, or silently infer it. In the same conversation as design approval, use the in-memory model that wrote it rather than rereading mid-phase, except Rule 8 Phase 2/3 entry checkpoints, which always re-read. AskUserQuestion for build ambiguity. Before reading an unwatched SDD, Read its first 40 lines and require `<!-- planner-handoff:v1 -->` and a `Template validation` header value of `passed`; otherwise return it to the planner checklist.

3. **Phase 1 registry gate.** Run `uip login status --output json`, then `uip maestro case registry pull`, before cache inspection, carryover, resolution, or Phase 1 writes. Pull at most once per session except Rule 18 `Force pull and re-resolve` or stale-cache handling. If the planner lane ran in this session, its pull succeeded, and it wrote the SDD, reuse the cache; with the lane's in-context resolution outcomes, use verify-only planning: persist them verbatim to `tasks/registry-resolved.json`, spot-checking entries, executing gate decisions, and re-resolving only stale/missing entries; otherwise run the full gate. Login/pull failure stops Phase 1. Outside that fast path run `uip maestro case sdd resolve "<SDD_PATH>" --out tasks/registry-resolved.json --output json`; it performs task-type index selection, exact-name search, folder narrowing, and the Rule 10 ledger in one call. If `Data.Warnings` reports `Data.Scope.cache.stale: true`, run `uip maestro case registry pull --force --output json` once without asking, then `sdd resolve` again; plain pull reuses caches under 24 hours and `--force` refreshes them. If still stale, report and continue. Never hand-author the ledger.

   `Data.Unresolved[]` is the only manual work: `absent` uses registry-discovery.md cross-type fallback and in-solution sibling check before Rule 18; `ambiguous` (folder did not narrow multiple exact matches) never gets an arbitrary selection and goes to Rule 18, remaining `<UNRESOLVED>` without an answer. Manual lookup uses `uip maestro case registry search "<Name>" --type <type> --output json` and `~/.uip/case-resources/<type>-index.json`; equivalent records differ as a flat camelCase list (`entityKey`, `folders`) versus `Data.Resources[] = {ResourceType, Resource: {…}}` with PascalCase (`EntityKey`, `Folders`). If `sdd resolve` is unknown (`ErrorCode: "invalid_argument"`, exit 3), resolve every task by hand per registry-discovery.md and say so in one line. Before a successful pull, missing cache files are failed refresh preconditions, not zero matches; only after success may empty exact-name matches/absent indexes enter empty-lookup handling. The pull refreshes discovery only. The planner owns design-time resolution, lazily login/pull-bound, one batched Case Review gate, SDD cells and its ledger; it does no schema discovery.

   **Design-only exception:** when explicitly stopping at `sdd.md`/`sdd.draft.md` without `caseplan.case`, solution, or build, do not run tenant registry, connection, schema, or user-discovery commands. Preserve names, leave identities `<UNRESOLVED>`, and report deferred wiring, never a substitute plan. This does not apply when resource/identity resolution, registry refresh, stale-audit replacement, `tasks/registry-resolved.json`, or `tasks/recipients-resolved.json` is requested; then run the normal gate, resolve identities, write the ledger, and stop before Phase 2.

4. **Convert before authoring.** At Phase 2 top, after the registry gate, run `uip maestro case sdd convert "<SDD_PATH>" --resolved tasks/registry-resolved.json --out "<SolutionName>/<ProjectName>/<PLAN_FILE>" --output json`, where `<PLAN_FILE>` is the `case init` seed: `caseplan.case`, or older CLI `caseplan.json`. The plan is two levels down in Rule 24’s project, never solution-root or beside `sdd.md`; scaffold first because `case init` refuses non-empty directories. Convert immediately; never hand-build elements first. `Data.Unresolved[]` is the work list: `resource-binding` closes in Phase 1, `output-type` at `uip maestro case splice --described` (Step 9.8), and `connector-context` at Check 12; it is a floor, not a correction list. Every `jsonSchema` variable arrives with `body: null`; fill `body` and `_jsonSchema` from the SDD per [`global-vars/impl-json.md` § jsonSchema type](references/plugins/variables/global-vars/impl-json.md#jsonschema-type). Read the emitted plan once, close unresolved entries, and do not re-derive or reopen emitted shapes. Follow [references/phased-execution.md](references/phased-execution.md#convert-first--emit-from-the-document-before-authoring). If `sdd`/`convert` is unknown (`ErrorCode: "invalid_argument"`, exit 3), author Phase 2 by hand, say so in one line, and continue. Exit 3 without that message is a real failure, not a fallback. Never install, reinstall or change the CLI.

5. Parsed reads require `--output json`.
   `bindings_v2.json` is the exception: `uip maestro case bindings sync` generates it; never write it by hand.

6. **Plugin references.** During planning, `cat` matching `planning.md`; during execution, `cat` `impl-json.md` before hand-authoring/repairing a plugin shape named by `Data.Unresolved[]`, Step 12, or uncovered by `sdd convert`. Read only the needed section and never guess JSON shapes. Converted shapes require no recipe read.

7. **Lossless build.** Finished `caseplan.case` contains one element for every SDD stage, task, trigger, condition, SLA rule, variable, argument, and explicit default. Preserve explicit rules/selectors exactly; repair invalid `selected-tasks-completed`. Copy `**Description:**` into `description` word-for-word; otherwise use `**Design Rationale:**` only when no Description exists. Put other rationales, SLA rationale, and condition routing/activation rationales in `build-issues.md`; put a Description there when no element description slot exists. Preserve every Inputs row, binding mode/value, and JSON object literal exactly (native object or JSON-encoded string); add `=js:`/`=jsonString:` only when explicitly present. Project outputs through [`plugins/variables/io-binding/planning.md`](references/plugins/variables/io-binding/planning.md#sdd-outputs-table-to-caseplan-projection-mandatory), preserving operator/operands. SDD output rows require `->` or `=`; schema-discovered bare outputs are not authored rows; never simplify equal-name `->` rows; `—` is not an operand. AskUserQuestion for unrecognized/ambiguous rows; never omit silently. Regenerate greenfield builds; preserve brownfield IDs. Every task has its own `entryConditions` from its SDD Entry Condition table and Activation Mode — write it per task, never once for a group of similar tasks; a missing rule may only warn in `validate` but hangs `case debug`. See [references/implementation.md](references/implementation.md).

   Completion is `--strict --sdd`, never default-profile `Valid`: at Step 12 run `uip maestro case validate <caseplan.case> --strict --sdd sdd.md`; close every `STRICT_SDD_*` finding and every convert `Data.Unresolved[]` entry before completion. Plain `validate` can return `Valid` for missing stages/tasks/conditions/SLA/output types.
   This rule stops an artifact being AUTHORED or EDITED by script, never CHECKED; the caseplan's own check is `uip maestro case validate --strict --sdd` (Rule 7). Plain `validate` returns `Valid` on a plan missing stages, tasks, conditions, SLA rules and output types; never report that `Valid` as the build's result.

8. **Build gate.** Phase 1 auto-proceeds to Phase 2. Stop after resolution only for explicit design-only, Phase 1 only, review-first, or no-build requests. Re-read `sdd.md` and `tasks/registry-resolved.json` at Phase 2 and 3 entry.

9. **Unresolved resources.** Never fabricate IDs; keep `<UNRESOLVED: ...>` in the ledger. A placeholder task has `type`, `displayName`, structural fields, and `data: {}`; conditions still reference its TaskId. A placeholder event trigger has render fields and `data.inputs` containing only `serviceType: "Intsvc.EventTrigger"`, `entryPointId: "<entry-points.json uniqueId>"`, and one context `{ "name": "objectName", "type": "string", "value": "<SDD Source>" }`. Keep the converter’s `objectName`; append the `entry-points.json` entry and create no trigger edge. See [references/placeholder-tasks.md](references/placeholder-tasks.md) and [references/plugins/triggers/event/impl-json.md](references/plugins/triggers/event/impl-json.md).

10. **Resolution audit.** `tasks/registry-resolved.json` contains one object per task with exact keys `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`, plus resolved I/O/review metadata. `uip maestro case sdd resolve --out` writes `{resolved:[...], unresolved, scope}`; preserve that shape, never re-wrap/flatten it. Each resolved resource is `{name, identifierField, identifier, folder}`; read identity only from those fields. Add with Edit only `gateDecision` for a user design-time answer, identity-slot marker, `wiringNotes`, and one entry for each trigger/connector-bound condition. Planner ledgers are persisted verbatim and consumed in either shape. `matches` is the complete refreshed exact-name set; `selected` is a match or `null` after genuine empty lookup. A genuine miss (`unresolved[]` or manual empty lookup) must include the task-type identity slot: `taskTypeId` for non-connectors, `typeId`/`connectionId` for connectors/triggers, containing the Rule 9 unresolved text. `wait-for-timer` is not a miss and gets no marker. Connector resolution uses [connector-integration.md](references/connector-integration.md), not resolve; `selected: null` alone is not a miss—the marker controls placeholder emission. Ledgers are machine-only and never shown, including Case Review.

11. **Cross-task references.** Use `"Stage Name"."Task Name".output_name` and [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), using source output `.id`; only custom `=` without `.id` uses its verified root companion `.id`. Never use reassigned `.var`. Discover connector names with `uip maestro case spec`, non-connector names with `uip maestro case tasks describe`. In larger `=js:` expressions use `vars.$xref('Stage','Task','output')`, resolved at Step 11.5. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md).

12. **Build-review preference.** Capture once at journey start. Design handoff puts it in Build options (`Build it — straight through` / `Build it — pause at the build preview`); provided SDD asks once after roadmap. Noninteractive/resumed runs default straight-through. At Phase 2→3 try `validate --skeleton-v2`; fall back once to legacy `--skeleton` only when explicitly unknown/unsupported, typically invalid_argument/exit 3; exit 3 alone is insufficient. Findings are advisory. Pause asks `Publish for review` / `Skip publish and continue` / `Abort`; publish refreshes resources, uploads with required filter, prints `DesignerUrl`, then asks `Continue to implementation` / `Abort`. Hard stops remain at Phase 4 retry exhaustion and Phases 5–7, including any re-publish after a Phase 6 fix.

13. **Never auto-debug or publish.** `uip maestro case debug` performs real emails/messages/API calls; Phase 7 (`case pack` → `solution pack` → `solution publish`) ships to the tenant. Each requires its own AskUserQuestion consent.

14. **Artifact I/O.** The plan is `caseplan.case`; entry points name `caseplan.case.bpmn` and package descriptor names both. If an existing Studio Web plan is named `caseplan.json`, `case.stage.json`, `default.stage.json`, etc., use it and never create a second; `case pack` rejects an entry point naming another sidecar. T01 direct-JSON fallback uses `caseplan.json`. For `caseplan.case`, `sdd.md`, `sdd.draft.md`, `tasks/registry-resolved.json`, `tasks/trigger-spec-cache.json`, `tasks/spec-cache.<elementId>.json`, `id-map.json`, `entry-points.json`, and `build-issues.md`, use harness file tools only. Exceptions: `bindings_v2.json` is generated by `uip maestro case bindings sync`; the initial plan by `uip maestro case sdd convert --out`; the ledger by `uip maestro case sdd resolve --out`; and spec caches by `uip maestro case spec --output json > tasks/spec-cache.<elementId>.json` (also `tasks/trigger-spec-cache.json`), write-once and never edited. Never mutate covered artifacts by `sed -i`, `perl -pi`, `awk`, `jq`, Python/Node rewrite, shell redirection, `tee`, `cp`, `mv`, `install`, `rsync`, or scripts, including `/tmp`; the ban is write-path only. Reading is unrestricted, including `cat`, `sed -n`, `head`, `rg`, `jq` projections, `python3 -c`, and `~/.uip/case-resources/`. Bash is allowed for read-only inspection, UUID v4 generation without filesystem access, CLI metadata, validate, `format`, `bindings sync`, `splice`, `sdd parse`, `sdd resolve`, `sdd convert`, debug, and solution scaffold/upload. Prefixed IDs are chosen inline. Pretty-print `caseplan.case`; after every write run `uip maestro case format "<caseplan.case path>" --output json`. Compact plans cannot be patched. If over about 30KB, use [case-editing-operations.md](references/case-editing-operations.md) preview/detail cadence. See [case-commands.md § uip maestro case format](references/case-commands.md#uip-maestro-case-format).

15. **Runnable resources/sidecars.** Before Phase 4 run Step 12 Checks 7, 9, 11, and 12 even if publish/debug/refresh is skipped. Non-null `selected` resources are never placeholders: retain `data.name`/`data.folderPath` with complete root bindings, regenerate sidecars with `uip maestro case bindings sync`, and make `resourceKey` self-consistent with defaults, not copied tenant identity/UUID. Connector `connection` entries must resolve to declared Connection root bindings: connector tasks use `uip maestro case splice` to write `=bindings.<id>` plus both roots from saved spec; event triggers and connector-bound rules use that reference and ConnectionId/FolderKey roots in the same edit. A `folderKey` containing connection ID or missing Connection binding never resolves. Repair and recheck; halt before Phase 4 if mismatched. Run `uip solution resources refresh` whenever a connector connection is bound, and again before every upload/debug; it emits `resources/*/connection/*.json` ([bindings-v2-sync.md](references/bindings-v2-sync.md)). Repeat Check 7 before every `resources refresh`. See [implementation.md § Step 12](references/implementation.md#step-12--end-of-phase-3-validator-pass), [case-commands.md § uip maestro case validate](references/case-commands.md#uip-maestro-case-validate), and [phased-execution.md § Phase 5](references/phased-execution.md#phase-5--publish).
    **Run `uip solution resources refresh` whenever the plan binds a connector connection — not only before an upload or a debug**, and again before every upload or debug: it is what emits `resources/*/connection/*.json`, and without it a plan that validates clean packs a solution that cannot connect ([bindings-v2-sync.md](references/bindings-v2-sync.md)).

16. **Handoff contract.** Invoke `uipath-planner`’s Case Design Lane here, never as a subagent. It owns design, resolution, review, and SDD writing; this skill resumes at solution initialization. User-facing language is one continuous flow and never mentions handoff. If unavailable, say so in one line, request `sdd.md` or approved pasted design, and stop. Cross-product planning is plain-text guidance to the planner. Apply Rule 2 receipt checks.

17. **Closed task types.** `caseplan.case` task `type` must be exactly one of: `process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `execute-connector-activity`, `flow-process`, `http-request`, `document-extraction`, `wait-for-connector`, `external-agent`, `external-workflow`, `wait-for-timer`. Never use plugin/CLI names, `wait-for-event`, or invented values. See [references/case-schema.md](references/case-schema.md) and Plugin Index.

18. **Empty lookup gate.** Execute same-session user `gateDecision` without asking: `resolve-at-build` → placeholder; `create-during-build` → inline create; `pick:<name>` → bind. Missing decision is deferral, not consent; run the full gate. For zero matches, one batched AskUserQuestion by `(name,type)`: `Force pull and re-resolve`; `Use placeholders for all`; and, only for creatable types with `registry --local`, `Create missing resources inline`. For folder-unresolved multiple matches, never select by position; ask one folder-named option per candidate plus `Use a placeholder`; unanswered/noninteractive stays `<UNRESOLVED>`. Create only selected `agent`, `api-workflow`, or `business-rule` resources through `uipath-agents`, `uipath-api-workflow`, or `uipath-rules`; never infer Create. Other empty types are placeholder-only. Same-I/O selected resources may share one build; differing I/O splits later with anchor retaining name, and SDD updates require permission. See [registry-discovery.md § 1c](references/registry-discovery.md#1c--dedup-the-selected-builds-one-resource-per-name-and-type), [Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery), and [§ MUST Confirm](references/registry-discovery.md#must-confirm-before-placeholder-fallback).

19. **Layout.** Emit top-level `layout: {}` only. Do not emit node `position`, `style`, `measured`, `width`, `height`, `zIndex`, or edge `data.waypoints`; do not compute positions.

20. Run Step 12 Check 8 once at Phase 3 exit; it is mandatory; do not enter Phase 4 until it passes and do not substitute CLI validate.

21. **No authored edges.** Keep `schema.edges` `[]`; never author TriggerEdge/Edge objects. Conditions provide flow; first stage uses `case-entered`. Read-only shapes: [case-schema.md Appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author).

22. **Global events/SLA responses.** Model each global external event once as an interrupting secondary-stage `wait-for-connector` entry. Choose exactly: `notify-only`, `start-task`, `enter-stage`, `exit-stage`, `exit-case`. `start-task` belongs on the follow-up task’s `sla-status-change`, not stage entry. Interrupting depends on stop/pause/reroute; parallel oversight uses `Interrupting: No` and stays secondary. `sla-status-change` names `slaId`; add `escalationId` only for at-risk. Unstated at-risk/breach responses are notifications; never replicate rules across primary stages. See [references/sla-response-shapes.md](references/sla-response-shapes.md) and SLA Response Map.

23. **Formal argument IDs.** `variables.inputs[].id` and `variables.outputs[].id` must be synthetic `v` + 8 characters and distinct from `name`/`var`; never copy companion names. Run Step 12 Check 10 once at Phase 3 exit and non-interactively re-mint violations; CLI validate does not check it. See [global-vars/impl-json.md § Formal-arg slot ID format](references/plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format).

<!--skill-flavor:project-scaffold-rule:start-->
24. **Scaffold with `uip solution init`, then `uip maestro case init` from inside the solution directory.** `cd <SolutionDir>` first; `&&`-chaining after `uip solution init` does not satisfy it and places the project outside the solution, auto-scaffolding another. Confirm `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. Use T01 direct-JSON scaffold in [implementation.md § Step 6](references/implementation.md#step-6--create-the-case-project-structure) only when `case init` is unavailable. See [case-commands.md § case init](references/case-commands.md#uip-maestro-case-init).
<!--skill-flavor:project-scaffold-rule:end-->

25. **Read the passage a mutation uses.** Before the first Write/Edit using a reference shape/procedure/constraint/verification rule, find its heading/term and read that whole section through the next same-level heading; follow pointed sections too. Whole-file reads and `<!-- END: <filename> -->` are unnecessary. Brownfield recipes in [edit-recipes-guide.md](references/edit-recipes-guide.md) require only the recipe unless it names another reference. Search hits, memory, or sibling references do not satisfy this; reopen after compaction/unavailable reads.

26. **Unique labels/names.** Stage `data.label` values are unique case-wide. Task `displayName` values are unique across stages, exact/untrimmed, and contain no `:`; missing names bind to resource names and participate in uniqueness. Condition `displayName` values are unique case-wide across four scopes, except frontend defaults (`Entry rule <N>`, `Exit rule <N>`, `Completion rule <N>`, `Stage complete`, `Stage exit`, `Tasks completed rule`, `Previous task completed`), which repeat and are never renumbered. Number authored names with a case-wide counter per label kind, never per stage/task ([case-schema.md § Condition name uniqueness](references/case-schema.md#condition-name-uniqueness)). Assign names in Phase 1; later renaming updates SDD, plan, ID map, and name-keyed references.

## Routing and Roadmap

| Condition | Journey |
|---|---|
| New case, SDD provided, no caseplan, or rebuild from spec | **Greenfield:** handoff if needed, then Phases 1–7 |
| Existing caseplan and targeted edit intent | **Brownfield:** skip handoff and Phases 1–7; use [brownfield.md](references/brownfield.md) |

Brownfield still requires latest-state pull, debug consent, and Orchestrator-publish consent, and reuses Phase 5–7 contracts.

Print once after routing and before detailed work, in five lines or fewer; do not expose phases, modes, filenames, or mechanics:

- **New case without SDD:** `1. I read your request and make the design calls, checking your UiPath tenant along the way. 2. One review packet: case snapshot, primary journey, other paths, SLA responses, business rules, resources, and every decision I made — you confirm or correct. 3. Build and validate without interruptions; the full technical design doc is saved alongside for reference. 4. Pause for your call before any run or publish.`
- **New case with SDD:** `1. Read the design and verify available UiPath resources. 2. One question: build straight through, or pause at a mid-build preview. 3. Plan, build, and validate without further interruptions. 4. Pause for your call before any run or publish.`
- **Targeted edit:** `1. Pull the latest case. 2. Apply the requested change. 3. Validate the updated case. 4. Ask before running or publishing anything.`

## Workflow

Front-load decisions, then run unattended to consent gates: **Design handoff when required → Phase 1 Planning → Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Publish → Phase 6 Debug → Phase 7 Publish to Orchestrator.** Present the matching kickoff once at invocation or handoff/Phase 1 start; status follows Anti-pattern limits.

**Greenfield kickoff:**

> Here's how I'll build this case, and where I'll stop for your call:
> - **Planning** — I draft a task plan from the spec and continue; ask up front if you want to review it first.
> - **Prototyping** — I build the reviewable case flow (stages, tasks, triggers, rules, SLA/escalation; connector rules use stubs). Whether I pause here for a Studio Web preview is **your up-front call** — asked once at the start, never mid-build.
> - **Implementation** — I wire task inputs/outputs, connector schemas, and resolved connector-rule details.
> - **Validate** — I run validation and fix errors.
> - **Publish** (optional) — **you choose** whether to upload to Studio Web.
> - **Debug** (optional) — **you choose** whether to run the case for real (live emails / API calls).
> - **Publish to Orchestrator** (optional) — **you choose** whether to publish the case to Orchestrator.

For handoff prefix: `First I'll design the case from what you've given me — checking your UiPath tenant along the way — and show one decision-first review packet with the case snapshot, primary journey, other paths, SLA responses, business rules, resources, and every decision made — one confirmation, then I build; the full technical design doc (sdd.md) is saved alongside for reference.` For brownfield use [references/brownfield.md](references/brownfield.md).

### Design handoff

If no `.md` basename containing `sdd` exists at the resolved path, hand off. If the prompt names another SDD basename, copy it to `./sdd.md` with Read + Write and do not invoke the lane. If no basename is named, use `./sdd.md`. Before Case Review do not read planning/plugin references or run tenant commands. For explicit no-build design, write `sdd.md` after approval without plugin references, schema, registry, connection, or user discovery, then stop; do not substitute a plan. Planner drafts and `sdd-viewer.html` remain with planner. If unavailable, request an SDD and stop.

### Phase 1 — Resolution

Read [references/planning.md](references/planning.md). Produce `tasks/registry-resolved.json` as the complete tenant-identity audit, never an SDD structure/contract copy. If Rule 18 Create is selected, build selected agents/API workflows/business rules as in-solution siblings through permitted paths, ensure a solution, register, refresh, rediscover, and bind; see [registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery). `tasks/` is adjacent to `sdd.md`, never inside solution/project. Auto-proceed unless explicitly stopped; reread SDD and ledger first.

### Phase 2 — Prototyping

Read [references/implementation.md](references/implementation.md) and [references/phased-execution.md](references/phased-execution.md). Follow Steps 6–11.9:

<!--skill-flavor:phase-two-step-six:start-->
1. Step 6: `uip solution init`, then `uip maestro case init` inside the solution directory (Rule 24), then **`sdd convert --out` the caseplan into the plan file `case init` seeded** (Rule 4). Use [plugins/case/impl-json.md](references/plugins/case/impl-json.md) T01 direct-JSON fallback when `case init` or `sdd convert` is unavailable, and for the root shape.
<!--skill-flavor:phase-two-step-six:end-->
2. Step 6.1: manual, timer, event triggers and Rule 9 placeholders; capture IDs.
3. Step 6.2: global variables/arguments; an In argument’s `elementId` references its `sourceTriggers` trigger, or the primary trigger when blank.
4. Step 6.3: synchronize `entry-points.json` from In/Out arguments per [entry-points-sync.md](references/entry-points-sync.md). Emit `job-attachment` `definitions` byte-for-byte from that reference, reproducing its `MimeType.description` inner quotes exactly (single-`\"` escaping); never re-escape (`\\"`) or rebalance them, or the JSON breaks.
5. Step 7: stages.
6. Step 9: task shapes; non-connectors get complete empty `data.inputs[]`, connectors only `typeId`/`connectionId`, unresolved resources placeholders.
7. Step 11: SLA/escalation objects with stable IDs.
8. Step 10: all four condition scopes; connector waits use canonical stubs regardless of resolution.
9. Step 11.9: informational skeleton validation with Rule 12 fallback.
10. Apply Phase 2→3 preference. Preview uses refresh, filtered solution upload, printed DesignerUrl, and continuation gate; Abort writes `build-issues.md` and exits.

### Phase 3 — Implementation

Re-read SDD task details, `tasks/registry-resolved.json`, and `caseplan.case` (Step 9.6); follow Steps 9.7, 9.8, 10.5, 11.5: run `uip maestro case spec` for connector schemas/defaults; bind all task-class I/O using [io-binding/impl-json.md](references/plugins/variables/io-binding/impl-json.md); upgrade resolved connector-bound condition stubs in place while reporting unresolved stubs; resolve `vars.$xref`; perform resource emission/preservation, resourceKey, and connector checks. Proceed to Phase 4 only after checks pass.

### Phase 4 — Validate

Run Step 12 once at the Phase 3 boundary: Checks 1–15, including 7 sidecar parity, 8 global output-ID uniqueness, 9 resource emission/preservation, 10 formal-arg IDs, 11 resourceKey consistency, 12 connector completeness, and 15 non-empty task entry rules. Then run full `uip maestro case validate`. Retry at most three times, editing before each retry; on third failure hard-stop AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`. Summarize `build-issues.md` using Step 12.1.

### Phase 5 — Publish

Provide completion report, then hard-stop AskUserQuestion: `Publish to Studio Web` / `Skip to Debug` (Step 13). On publish refresh resources, upload with mandatory output filter, print DesignerUrl, and continue to Phase 6 either way.

### Phase 6 — Debug

<!--skill-flavor:phase-six-debug-gate:start-->
Hard-stop AskUserQuestion (Step 15): `Run debug session` / `Continue to publish`. On Run, refresh resources, run `uip maestro case debug`, and loop after completion until `Continue to publish`. Never run debug automatically.
<!--skill-flavor:phase-six-debug-gate:end-->

### Phase 7 — Publish to Orchestrator

<!--skill-flavor:phase-seven-publish:start-->
Hard-stop AskUserQuestion (Step 16): `Publish to Orchestrator` / `Done`. On publish, run in order:

1. `uip solution resources refresh`
2. `uip maestro case pack <SolutionDir>/<ProjectName> <SolutionDir>/dist --output json`
3. `uip solution pack <SolutionDir> <SolutionDir>/dist --output json`
4. `uip solution publish <packagePath> --wait --output json`

`case pack` is mandatory because it creates `caseplan.case.bpmn`; `validate` does not. Publish the `solution pack` `.zip`, not the case `.nupkg`; read `<packagePath>` from `Data.Packages`, never guess. `Done` exits.
<!--skill-flavor:phase-seven-publish:end-->

## References

| Need | Reference |
|---|---|
| Design without SDD | `uipath-planner` Case Design Lane; Rule 16 |
| Resolve resources from SDD | [references/planning.md](references/planning.md) |
| Build caseplan from SDD | [references/implementation.md](references/implementation.md) |
| Brownfield edit | [references/brownfield.md](references/brownfield.md); common edits: [references/edit-recipes-guide.md](references/edit-recipes-guide.md) |
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
| `function` | [function](references/plugins/tasks/function/planning.md) | `function` |
| `business-rule` | [business-rule](references/plugins/tasks/business-rule/planning.md) | `business-rule` |
| `case-management` | [case-management](references/plugins/tasks/case-management/planning.md) | `case-management` |
| `execute-connector-activity` | [connector-activity](references/plugins/tasks/connector-activity/planning.md) | `connector-activity` |
| `flow-process` | [flow-process](references/plugins/tasks/flow-process/planning.md) | `flow-process` |
| `http-request` | [http-request](references/plugins/tasks/http-request/planning.md) | — (`sdd convert` writes it) |
| `document-extraction` | [document-extraction](references/plugins/tasks/document-extraction/planning.md) | — (`sdd convert` writes it) |
| `wait-for-connector` | [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) | `connector-trigger` |
| `external-agent` | [connector-activity § External agents and automations](references/plugins/tasks/connector-activity/planning.md#external-agents-and-automations) | `external-agent` |
| `external-workflow` | [connector-activity § External agents and automations](references/plugins/tasks/connector-activity/planning.md#external-agents-and-automations) | `external-workflow` |
| `wait-for-timer` | [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md) | `wait-for-timer` |

Schema-kebab is the only JSON value; plugin/CLI names are not interchangeable. Unsupported types include `wait-for-event`.

**Triggers:** [manual](references/plugins/triggers/manual/planning.md), [timer](references/plugins/triggers/timer/planning.md), and [event](references/plugins/triggers/event/planning.md).

**Conditions:** [stage-entry-conditions](references/plugins/conditions/stage-entry-conditions/planning.md), [stage-exit-conditions](references/plugins/conditions/stage-exit-conditions/planning.md), [task-entry-conditions](references/plugins/conditions/task-entry-conditions/planning.md), and [case-exit-conditions](references/plugins/conditions/case-exit-conditions/planning.md).

Connector-bound rules in every condition scope require `rule.uipath` from `case spec --type trigger`; bare connector rules are invalid in Studio Web even if CLI validate passes. See [connector-trigger-impl.md](references/connector-trigger-impl.md).

## Anti-patterns

- Never leave a regular stage without an entry condition: first uses `case-entered`, others need reachable predecessors; edges are retired and `validate` errors `CASE_MGMT_STAGE_ENTRY_CONDITION_MISSING`.
- Do not design here, start Phase 1 before Case Review approval, or build from a summary SDD; planner owns design, other paths, and conformance.
- Do not validate after each element or twice without an intervening edit. Phase 2 is informational; Phase 4 authoritative and `--strict`.
- Never author `tasks/tasks.md`, T-numbered lists, or any SDD restatement. Converter output is the artifact; Step 12 audits it.
- Never one Write for the whole `caseplan.case`: converter emits it; subsequent changes are targeted Edits preserving siblings. After interruption reread plan and SDD. Brownfield/scaffold cadence is [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical).
- Do not narrate between tool calls. Bundle status with the next call; ordinary text stays under 200 tokens, allow-listed kickoff/hard-stop/completion/DesignerUrl/validation summaries under 500. Do not announce with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next`, `Approach`, `Strategy`, `Plan`, `Let me`, or equivalent.
- Preserve ordered task semantics: sequential mode uses ordered `data.tasks` and one `runs-sequentially` per task, never `current-stage-entered` alongside it; parallel uses `current-stage-entered` only for independent work and `selected-tasks-completed` only for required fan-in. Event tasks use event/condition rules; manual/adhoc tasks use exactly one `adhoc`, `isRequired: false`, and no additional entry event. `adhoc` is activation, not type.
- Secondary stages are interrupting exception lanes: `case-management:Stage`, `data.stageType: "secondary"`, `isRequired: false`, and `Interrupting: Yes` on stage/entries. `Interrupting: No` only for parallel SLA oversight. Use `return-to-origin`; do not normal-flow/connect or count them in required completion.
- Model secondary stages as interrupting exception lanes: `case-management:Stage`, `data.stageType: "secondary"`, `isRequired: false`, and `Interrupting: Yes` on stage and entries. Use `return-to-origin`; do not connect secondary stages as normal flow or count them in required completion.
- Do not replicate global events/SLA rules across primary stages. Completion requires root `metadata.caseExitRules[]` with `marksCaseComplete: true`; stage completion alone is insufficient. Non-completing outcomes use `false`.
- Do not edit generated `caseplan.case.bpmn`, put `caseplan.case` under `content/`, or fabricate conditional-SLA expression syntax. `validate --strict` rejects namespace-less `=js:` identifiers (`STRICT_JS_UNKNOWN_IDENTIFIER`); describe conditions naturally until execution resolves them.
- Keep `tasks/` beside `sdd.md`, not in solution/project.
- Invoke no other skills automatically except Rule 16 handoff and Rule 18 selected inline creation. Do not spawn design/draft-finalization/plan-only subagents.
- Do not inspect bundled CLI code to interpret output. Findings name the path and repair; use the plan/reference, not `node_modules/@uipath/**/dist` or predictive `node -e` comparisons. If unclear, reread the named element/reference, repair the message’s subject, and if it persists report with `/uipath-feedback`.
- Use `uipath-feedback` for trouble.

> **Trouble?** Use `/uipath-feedback` to send a report.