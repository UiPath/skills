---
name: uipath-maestro-case
description: "Always invoke for UiPath Maestro Case Management build work: `caseplan.json`, `sdd.md`, or building/creating a case when no SDD exists yet (the case design is produced first, then confirmed in one review). Resolves tenant resources then authors or edits caseplan.json directly with Write/Edit. For .xaml→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn. For standalone case SDD design, case `sdd.draft.md` finalization, PDD→SDD, or cross-product planning→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Build UiPath Case Management definitions from `sdd.md`. Resolve tenant resources into `tasks/registry-resolved.json`, then emit `caseplan.json` with `uip maestro case sdd convert` and fill what the document cannot determine, using the applicable per-plugin JSON recipes. The SDD is the plan — there is no intermediate plan file, and the converted `caseplan.json` is not one: it is the artifact itself, derived rather than restated.

> **Authoring invariant:** Never use mutating `uip maestro case` commands (`cases|stages|tasks|*-conditions ... add|update|remove`, including `tasks add-connector`) or explore them with `--help`. Use the CLI only for scaffolding, metadata reads, validation/debug, runtime operations, and solution sync/upload. Consult [case-commands.md](references/case-commands.md) only when exact syntax is needed. CLI availability or a final `validate` requirement never overrides this rule.

When `sdd.md` is absent, case design belongs exclusively to **`uipath-planner`**, which runs its Case Design Lane in this conversation. This skill never designs independently. The lane uses best-assumption design, Listen → Sketch → full design-time tenant resolution, a mandatory other-path sweep, and one decision-first eight-section Case Review. Its Build answer is consent; it writes template-conformant `sdd.md`, then this skill continues immediately with
<!--skill-flavor:design-handoff-next-step:start-->
`uip solution init`, Phase 1,
<!--skill-flavor:design-handoff-next-step:end-->
and later phases. The same handoff applies to `sdd.draft.md` finalization. Never overwrite an existing `sdd.md`.

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

1. **Design handoff and SDD authority.** If `sdd.md` is absent, immediately invoke `uipath-planner`’s Case Design Lane in this conversation, before reading references or running tenant commands. Do not improvise interviews, design subagents, generic Build Plan approvals, or design-only behavior here. The lane’s single Case Review has exactly these sections: Case Snapshot; Primary Journey; Other Paths Considered; SLA and Escalations; Rules and Outcomes; Resources and Integrations with design-time resolutions; Decisions I Made; Review Flags. It names every stage/task, type, activation/grouping, required status, routing/outcome, and SLA context; `sdd.md` separately contains the complete data contract, variables, and task inputs/outputs. The Build options incorporate Rule 12, and the Build answer is the sole consent. Corrections re-show only changed review sections. Before approval, every `selected-tasks-completed` selector must resolve to a non-adhoc sibling in the same stage. The lane writes `sdd.md` early, then this skill runs
<!--skill-flavor:design-handoff-rule-next-step:start-->
`uip solution init <SolutionName>` and Phase 1
<!--skill-flavor:design-handoff-rule-next-step:end-->
without another prompt unless explicitly requested. A design-only request stops after `sdd.md` per Rule 3's design-only exception. If `sdd.draft.md` is to be finalized, use the lane fast path with target basename `sdd.md`. Never overwrite `sdd.md`.
2. **SDD is the sole post-design input, across sessions.** Trust user-provided or previously written `sdd.md`; do not validate, gap-fill, or silently infer it. In the same conversation as design approval, use the in-memory model that wrote it rather than rereading mid-phase — except at Rule 8's Phase 2 and Phase 3 entry checkpoints, which always re-read because context may have compacted. Use AskUserQuestion for build-phase ambiguity. Before reading an SDD not watched being written, Read its first 40 lines as the receipt: the `<!-- planner-handoff:v1 -->` marker and a `Template validation` header value of `passed` must both be present. Anything else goes back through the planner's template conformance checklist.
3. **Phase 1 registry gate.** Run `uip login status --output json`, then `uip maestro case registry pull`, before cache inspection, carryover, resolution, or Phase 1 writes. Pull at most once per session, unless the user selects `Force pull and re-resolve` at Rule 18's empty-lookup gate. If the planner lane ran in this session, its pull succeeded, and it wrote the SDD, reuse the cache. With the lane’s in-context resolution outcomes, use verify-only planning: persist them verbatim to `tasks/registry-resolved.json`, spot-check cache entries, execute gate decisions, and re-resolve only stale/missing entries. Otherwise run the full gate. Login/pull failure stops Phase 1. Resolve with `uip maestro case registry search "<Name>" --type <type> --output json`, or read `~/.uip/case-resources/<type>-index.json` directly. Both return the same records, **not the same shape**: the index file is a flat list of camelCase objects (`entityKey`, `folders`); `registry search` wraps each hit as `Data.Resources[] = {ResourceType, Resource: {…}}` with PascalCase keys (`EntityKey`, `Folders`). Copy whichever you read verbatim into `tasks/registry-resolved.json`; never re-case or unwrap it. Before a successful pull, missing cache files are failed refresh preconditions, never zero matches; only after success may empty exact-name matches or absent indexes enter empty-lookup handling. Trust the SDD; the pull refreshes discovery only. The planner lane owns design-time resolution, lazily starting login/pull when tenant-bound work first appears, resolving identities with one batched Case Review gate, and recording SDD cells plus its resolution ledger. No schema discovery occurs there.

   **Design-only exception:** when explicitly stopping at `sdd.md` or `sdd.draft.md` without `caseplan.json`, solution, or build, do not run tenant registry, connection, schema, or user-discovery commands. Preserve intended names, leave identities `<UNRESOLVED>`, and report deferred wiring in the reply — never in a substitute plan file. This exception does not apply when the user requests resource/identity resolution, registry refresh, stale-audit replacement, `tasks/registry-resolved.json`, or `tasks/recipients-resolved.json`; then run the normal gate, resolve identities, write the ledger, and stop before Phase 2.
4. **Convert before authoring.** At the top of Phase 2, after the Rule 3 registry gate, emit the plan with `uip maestro case sdd convert "<SDD_PATH>" --out "<SolutionName>/<ProjectName>/caseplan.json" --output json`. **The plan lives two levels down** — inside the project directory `uip solution init` created, never at the solution root and never beside `sdd.md`. Writing it shallow either leaves nothing where every grader, `validate`, `bindings sync` and `solution pack` look, or leaves two `caseplan.json` files and an ambiguous build. The SDD determines most of `caseplan.json`; deriving it once beats re-deriving it element by element, and hand-authoring what the parser already emits is the expensive path and the one that drifts from the document. Its `Data.Unresolved[]` is the work list — `resource-binding` closes at Phase 1 bindings, `output-type` at `uip maestro case splice --described` (Step 9.8), `connector-context` at Check 12 — and it is a floor, never a ceiling: it names what convert knew it skipped, never what it emitted wrongly. Known gap it does not name: every `jsonSchema` variable arrives with `body: null`; fill `body` and `_jsonSchema` from the SDD row per [`global-vars/impl-json.md` § jsonSchema type](references/plugins/variables/global-vars/impl-json.md#jsonschema-type). **`Data.Unresolved[]` is the complete list of what is left to do.** Read the emitted plan once, close those entries, and stop; do not re-derive, re-verify, or re-read references for anything convert already emitted. A shape that arrived in the converted plan is settled — reopening it costs more than the whole conversion saved. **Convert before you author any element.** Scaffold the project first per Rule 24 — `case init` refuses a non-empty directory, so converting first leaves the project with no `project.uiproj` and an unregistered manifest. Then run convert immediately; never hand-build stages, tasks, conditions, or variables first and convert second. Full procedure, including the mandatory task-entry-rule check that nothing upstream catches, in [references/phased-execution.md](references/phased-execution.md#convert-first--emit-from-the-document-before-authoring).

   > **Version guard.** If the CLI reports `sdd` or `convert` as an unknown command (`ErrorCode: "invalid_argument"`, exit 3), author Phase 2 by hand, say so in one line, and continue. Exit 3 without that message is a real failure, not a fallback. Never install, reinstall or change the CLI.
5. **Parsed reads require `--output json`.**
6. **Use plugin references for what you author, not for what convert emitted.** During planning, `cat` the matching plugin `planning.md`. During execution, `cat` a plugin's `impl-json.md` before authoring or repairing that plugin's shape **by hand** — the shapes `Data.Unresolved[]` names (Rule 4), anything Step 12 reports, and any plugin `sdd convert` does not cover. A shape that arrived in the converted plan needs no `impl-json.md` read: convert emitted it, Rule 4 settles it, and opening the recipe for it costs a whole-file read that changes nothing. Whatever you do open, read whole per Rule 25; never guess JSON shapes.
7. **The build is lossless against the SDD.** Never author an intermediate plan file: `sdd.md` is the plan, and restating it drifts from it. `caseplan.json` must end with one element for every SDD stage, task, trigger, condition, SLA rule, variable, and argument, including explicit defaults — most of them emitted by `sdd convert` (Rule 4) and the rest filled in after; this rule is about what the finished artifact contains, never about writing each element by hand. Preserve every valid explicit rule/selector exactly; reject and repair invalid `selected-tasks-completed` selectors. Copy a stage or task's `**Description:**` line into the element's `description`, word for word; use its `**Design Rationale:**` there only when the block writes no `**Description:**`. Rationales otherwise, the SLA rationale, and condition routing/activation rationales go into `build-issues.md`, which is also where a `**Description:**` goes when the element has no `description` slot. Preserve every Inputs row, binding mode, and value. Preserve JSON object literals exactly: native object or JSON-encoded string in `input.value`; add `=js:`/`=jsonString:` only when explicitly present in the SDD. Project Outputs through [`plugins/variables/io-binding/planning.md`](references/plugins/variables/io-binding/planning.md#sdd-outputs-table-to-caseplan-projection-mandatory), preserving operator and operands. SDD output rows require `->` or `=`; schema-discovered bare outputs are not authored SDD rows. Never simplify equal-name `->` rows; `greeting -> greeting` differs from schema-discovered bare `greeting`. `—` placeholders are not operands. AskUserQuestion for unrecognized or ambiguous rows; never omit silently. Regenerate greenfield builds from scratch; brownfield edits preserve IDs. Every task node carries its own `entryConditions` derived from its SDD **Entry Condition** table and **Activation Mode** — write it per task, never once for a group of similar tasks; `validate` only warns `Task has no entry rules`, while a miss hangs `case debug` indefinitely. See [references/implementation.md](references/implementation.md).

   > **Completion is `--strict --sdd`, never a default-profile `Valid`.** At Step 12 run `uip maestro case validate <caseplan.json> --strict --sdd sdd.md` and close every `STRICT_SDD_*` finding and every `sdd convert` `Data.Unresolved[]` entry before reporting the build complete. Plain `validate` returns `Valid` on a plan missing stages, tasks, conditions, SLA rules and output types; never report that `Valid` as the build's result.
8. **Build gate.** Phase 1 auto-proceeds to Phase 2. Stop after resolution only when the request explicitly says design-only, Phase 1 only, review first, or not to build. Re-read `sdd.md` and `tasks/registry-resolved.json` at Phase 2 and Phase 3 entry — context may have compacted.
9. **Unresolved resources.** Never fabricate IDs. Keep `<UNRESOLVED: ...>` in `tasks/registry-resolved.json`. A placeholder task has `type`, `displayName`, structural fields, and `data: {}`; conditions still reference its TaskId. A placeholder event trigger has render fields and only `data.inputs: { serviceType: "Intsvc.EventTrigger" }`; append its `entry-points.json` entry and create no trigger edge. See [references/placeholder-tasks.md](references/placeholder-tasks.md) and [references/plugins/triggers/event/impl-json.md](references/plugins/triggers/event/impl-json.md).
10. **Resolution audit.** Persist one object per task in `tasks/registry-resolved.json` with exact keys `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, and `rationale`, plus resolved I/O/review metadata. Add `gateDecision` only when the user answered the design-time resource gate; default deferrals have none. `matches` is the complete exact-name set from the refreshed cache; `selected` is a match or `null` after a genuine empty lookup. An entry whose `selected` is `null` MUST also carry the identity slot for its task type — `taskTypeId` for non-connector tasks, `typeId` / `connectionId` for connector tasks and triggers — holding the `<UNRESOLVED: <reason>>` text Rule 9 requires. `selected: null` on its own does not record the miss: the marker is what Phase 2 reads to emit a placeholder instead of fetching a schema. Same-session planner ledgers are persisted verbatim, then verified/extended under Rule 3. The resolution ledger and `registry-resolved.json` are machine-only — never shown to the user, including in the Case Review.
11. **Cross-task references.** Use `"Stage Name"."Task Name".output_name` and the common output-reference-ID algorithm in [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative). Use the source output’s `.id`; only a custom `=` output without `.id` uses its verified root companion’s `.id`. Never use a reassigned output’s `.var`. Discover names with `uip maestro case spec` for connector tasks or `uip maestro case tasks describe` for non-connectors. In larger `=js:` expressions use `vars.$xref('Stage','Task','output')`, resolved at Step 11.5. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md).
12. **Build-review preference.** Capture once at journey start. Design handoff folds it into the Case Review Build options (`Build it — straight through` or `Build it — pause at the build preview`); provided SDD asks once after the roadmap. Non-interactive and resumed runs without a preference default to straight-through. At Phase 2→3, try `validate --skeleton-v2`; fall back once to legacy `--skeleton` only when the response explicitly says v2 is unknown/unsupported, typically invalid_argument/exit 3. Exit 3 alone is insufficient; real v2 failures are reported. Validation findings do not halt this advisory gate. Straight-through continues without prompting. Pause-at-preview follows [references/phased-execution.md](references/phased-execution.md): AskUserQuestion `Publish for review` / `Skip publish and continue` / `Abort`; on publish, refresh resources, upload with the required filter, print `DesignerUrl` before the follow-up, then ask `Continue to implementation` / `Abort`. Hard stops always remain at Phase 4 retry exhaustion, Phase 5, Phase 6, Phase 7, and any re-publish after a Phase 6 fix.
13. **Never auto-debug or publish to Orchestrator.** `uip maestro case debug` executes real emails, messages, and API calls. Phase 7 (`case pack` → `solution pack` → `solution publish`) ships to the tenant. Each requires its own AskUserQuestion consent.
14. **Artifact I/O.** For `caseplan.json`, `sdd.md`, `sdd.draft.md`, `tasks/registry-resolved.json`, `tasks/trigger-spec-cache.json`, `tasks/spec-cache.<elementId>.json`, `id-map.json`, `entry-points.json`, and `build-issues.md`, use only your harness's file tools (`bindings_v2.json` is the exception: `uip maestro case bindings sync` generates it; never write it by hand. `caseplan.json` has one sanctioned generator too — `uip maestro case sdd convert --out` emits the initial plan from `sdd.md` at the top of Phase 2; every edit after that emission is Write/Edit like any other): mutate only with Write / Edit (or `apply_patch`). **The ban is on the write path only.** Never mutate one of these files by script: no `sed -i`, `perl -pi`, `awk`, `jq`, Python or Node rewrite, shell redirection, `tee`, `cp`, `mv`, `install`, `rsync`, or agent-authored script of any kind, including under `/tmp`. **Reading is unrestricted** — `cat`, `sed -n`, `head`, `rg`, `jq` projections, `python3 -c` reads are all allowed, on these artifacts and on `~/.uip/case-resources/`. This rule stops an artifact being AUTHORED or EDITED by script, never CHECKED; the caseplan's own check is `uip maestro case validate --strict --sdd` (Rule 7). If `caseplan.json` exceeds about 30KB, read it by the preview/detail cadence in [case-editing-operations.md](references/case-editing-operations.md) rather than whole. Bash is allowed for read-only inspection, UUID v4 generation without filesystem access, CLI metadata, validate, `format`, `bindings sync`, `splice`, `sdd parse`, `sdd convert`, debug, and solution scaffold/upload. Prefixed IDs are chosen inline. **Write `caseplan.json` pretty-printed, and run `uip maestro case format "<caseplan.json path>" --output json` after every write** — the only sanctioned reformat. A compact plan cannot be patched by Edit/`apply_patch`, and every observed `perl -pi`/`sed -i` violation of this rule started from a compact file. Format's exact output and idempotency: [case-commands.md § uip maestro case format](references/case-commands.md#uip-maestro-case-format).
15. **Runnable resources and sidecars.** Before Phase 4, run Step 12 Checks 7, 9, 11, and 12 even when publish, debug, or resource refresh is skipped. A non-null `selected` resource must not become a placeholder: retain `data.name` and `data.folderPath` with complete root bindings, regenerate the sidecar with `uip maestro case bindings sync`, and make its `resourceKey` self-consistent with its own defaults, never a copied tenant identity/UUID. Per-check scope and repairs are in [implementation.md § Step 12](references/implementation.md#step-12--end-of-phase-3-validator-pass). Every connector context's `connection` entry must resolve to a declared Connection root binding — connector tasks get it from `uip maestro case splice`, which writes the `=bindings.<id>` reference and both root bindings from the saved spec in one call; the event-trigger node and connector-bound rules take the spec's `=bindings.<id>` reference and the ConnectionId and FolderKey root bindings in the same edit; a `folderKey` holding the connection id, or a connector with no Connection binding in `bindings[]`, is a resource that will never resolve. Completion is `--strict --sdd` per Rule 7; which profile runs in which phase, the don't-chain rule and the CLI 1.202 version guard are in [case-commands.md § uip maestro case validate](references/case-commands.md#uip-maestro-case-validate). Repair and recheck mismatches; halt before Phase 4 if they remain. Repeat Check 7 before every `resources refresh`. **Run `uip solution resources refresh` whenever the plan binds a connector connection — not only before an upload or a debug**, and again before every upload or debug: it is what emits `resources/*/connection/*.json`, and without it a plan that validates clean packs a solution that cannot connect ([bindings-v2-sync.md](references/bindings-v2-sync.md)). Upload flags and the DesignerUrl report are in [phased-execution.md § Phase 5](references/phased-execution.md#phase-5--publish).
16. **Handoff contract.** Invoke `uipath-planner`’s Case Design Lane in this conversation, never as a subagent. It owns design, resolution, review, and SDD writing; this skill resumes at solution initialization. User-facing language presents one continuous flow and never mentions the handoff. If unavailable, say so in one line, request `sdd.md` or an approved pasted design, and stop. Cross-product planning remains a plain-text suggestion to the planner. Apply the Rule 2 receipt spot-check before unobserved SDD reads.
17. **Closed task types.** `caseplan.json` task `type` must be exactly one of: `process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `execute-connector-activity`, `wait-for-connector`, `wait-for-timer`. Never use plugin folder or CLI names, `external-agent`, `external-workflow`, `document-extraction`, `flow-process`, `wait-for-event`, or other invented values. The unsupported types remain unsupported. See [references/case-schema.md](references/case-schema.md) and the Plugin Index.
18. **Empty lookup gate.** If the same-session ledger has a user `gateDecision`, execute it without asking again: `resolve-at-build` → placeholder; `create-during-build` → inline create; `pick:<name>` → bind it. A missing decision is a default deferral, not consent; run the full gate. For zero matches, use one batched AskUserQuestion grouped by `(name,type)` with: `Force pull and re-resolve`; `Use placeholders for all`; and, only when creatable resources exist and `registry --local` is supported, `Create missing resources inline`. Create only selected `agent` or `api-workflow` resources, invoking `uipath-agents` or `uipath-api-workflow`; never infer Create from SDD content. Other empty types remain placeholder-only. Selected resources with identical I/O may share one build; differing I/O splits later with the anchor retaining the name, and SDD updates require permission. See [registry-discovery.md § 1c](references/registry-discovery.md#1c--dedup-the-selected-builds-one-resource-per-name-and-type), [Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery), and [§ MUST Confirm](references/registry-discovery.md#must-confirm-before-placeholder-fallback).
19. **Layout.** Emit top-level `layout: {}` only. Do not emit node `position`, `style`, `measured`, `width`, `height`, `zIndex`, or edge `data.waypoints`; do not compute positions.
20. **Global output IDs.** Run Step 12 Check 8 once at Phase 3 exit. It is mandatory; do not enter Phase 4 until it passes and do not substitute CLI validate.
21. **No authored edges.** Keep `schema.edges` as `[]`; never author TriggerEdge/Edge objects. Conditions provide stage flow; the first stage uses `case-entered`. Read-only edge shapes are documented in [case-schema.md Appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author).
22. **Global events and SLA responses.** Model a global external event once as an interrupting secondary-stage `wait-for-connector` entry. Choose SLA response explicitly: `notify-only`, `start-task`, `enter-stage`, `exit-stage`, or `exit-case`. A `start-task` response belongs on the follow-up task’s own `sla-status-change` entry, not a stage entry. Interrupting depends on whether active work stops, pauses, or reroutes; parallel oversight uses `Interrupting: No` and remains secondary. `sla-status-change` names `slaId`; add `escalationId` only for at-risk responses. Without a stated response, at-risk and breach are notifications. Do not replicate rules across primary stages. See [references/sla-response-shapes.md](references/sla-response-shapes.md) and the SLA Response Map.
23. **Formal argument IDs.** `variables.inputs[].id` and `variables.outputs[].id` must be synthetic `v` + 8 characters and distinct from `name`/`var`; never copy companion names. Run Step 12 Check 10 once at Phase 3 exit and non-interactively re-mint violations. CLI validate does not check this. See [global-vars/impl-json.md § Formal-arg slot ID format](references/plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format).
<!--skill-flavor:project-scaffold-rule:start-->
24. **Scaffold with `uip solution init`, then `uip maestro case init` from inside the solution directory.** `cd <SolutionDir>` first; `&&`-chaining after `uip solution init` does not satisfy it and lands the project outside the solution, auto-scaffolding a second one. Confirm `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. Use the T01 direct-JSON scaffold in [implementation.md § Step 6](references/implementation.md#step-6--create-the-case-project-structure) only when `case init` is unavailable. See [case-commands.md § case init](references/case-commands.md#uip-maestro-case-init).
<!--skill-flavor:project-scaffold-rule:end-->
25. **Read references to EOF before mutation.** Every `references/*.md` ends with `<!-- END: <filename> -->`. Ingest a reference with one `cat <path>` — the preferred way on every harness, and the only way on a Bash-only harness; a harness with a Read tool may Read the whole file instead. Before the first Write/Edit using a shape, procedure, constraint, or verification rule, that file's exact END marker must have appeared in tool output during this session. Windowed reads (`sed -n '1,240p'`, `head`), search hits, tables of contents, memory, and sibling references do not satisfy this, and neither does testing that the marker exists (`wc -l`, `tail -n 2`, `grep END`) — read to the marker, do not probe for it. The largest reference is about 68KB and `cat`s cleanly; do not split a read to keep output short. Reopen after compaction or when the prior read is unavailable. Tail contracts are normative.
26. **Unique labels and task names.** Stage `data.label` values are unique case-wide; task `displayName` values are unique across all stages, exact and untrimmed, and contain no `:`. A missing display name binds to the resource name and participates in uniqueness. Condition `displayName` values are unique case-wide across all four condition scopes, **except the frontend's own default names** (`Entry rule <N>`, `Exit rule <N>`, `Completion rule <N>`, `Stage complete`, `Stage exit`, `Tasks completed rule`, `Previous task completed`), which repeat freely and are never renumbered. Number the names you author yourself with a case-wide counter per label kind, never a per-stage or per-task one ([case-schema.md § Condition name uniqueness](references/case-schema.md#condition-name-uniqueness)). Assign names in Phase 1; later renaming touches the SDD, plan, ID map, and name-keyed references.

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

The trigger is binary: if no `.md` whose basename contains `sdd` exists at the resolved path, hand off. If the prompt names another SDD basename, copy it to `./sdd.md` using Read + Write; do not invoke the lane. If no `.md` is named, use `./sdd.md`. Do not read planning/plugin references or run tenant commands before the Case Review. For an explicit no-build design request, write `sdd.md` after approval, without plugin references, schema, registry, connection, or user discovery, then stop — do not author a plan file in place of the build. Planner-owned drafts and `sdd-viewer.html` stay with the planner. If unavailable, request an SDD and stop.

### Phase 1 — Resolution

Read [references/planning.md](references/planning.md) to produce:

- `tasks/registry-resolved.json`: complete resolution audit — tenant identities only, never a copy of the SDD's structure or contract.
- If Create is selected at Rule 18: build selected agents/API workflows as in-solution siblings through the permitted sub-agent paths, ensure a solution exists, register them, refresh resources, rediscover, and bind them. See [registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery).

`tasks/` is adjacent to `sdd.md`, never inside the solution/project. Auto-proceed to Phase 2 unless the request explicitly asks to stop before the build. Re-read `sdd.md` and the ledger first.

### Phase 2 — Prototyping

Read [references/implementation.md](references/implementation.md) and [references/phased-execution.md](references/phased-execution.md). Follow Steps 6–11.9:

<!--skill-flavor:phase-two-step-six:start-->
1. Step 6: `uip solution init` and project registration, then **`sdd convert --out` the caseplan into that project** (Rule 4). The T01 direct-JSON recipe in [plugins/case/impl-json.md](references/plugins/case/impl-json.md) is the fallback when the installed CLI has no `sdd convert`, and the reference for the root shape either way; never `case init`.
<!--skill-flavor:phase-two-step-six:end-->
2. Step 6.1: manual, timer, and event triggers, including Rule 9 placeholders; capture trigger IDs.
3. Step 6.2: global variables and arguments; In-argument `elementId` references the trigger named by `sourceTriggers`, or the primary trigger when blank.
4. Step 6.3: synchronize `entry-points.json` from declared In/Out arguments per [entry-points-sync.md](references/entry-points-sync.md). Emit the `job-attachment` `definitions` block byte-for-byte from that reference — reproduce its `MimeType.description` inner quotes exactly (single-`\"` escaping); never re-escape (`\\"`) or rebalance them, or the JSON breaks.
5. Step 7: stages.
6. Step 9: task shapes; non-connectors get complete `data.inputs[]` with empty values, connectors only `typeId`/`connectionId`, unresolved resources use placeholders.
7. Step 11: SLA/escalation objects with stable IDs.
8. Step 10: all four condition scopes; connector waits use canonical stubs regardless of resolution.
9. Step 11.9: informational skeleton validation with Rule 12 fallback behavior.
10. Apply the Phase 2→3 preference. Preview branch uses resource refresh, filtered solution upload, printed DesignerUrl, and the prescribed continuation gate; Abort writes `build-issues.md` and exits.

### Phase 3 — Implementation

Re-read the SDD's task detail blocks, `tasks/registry-resolved.json`, and `caseplan.json` (Step 9.6), then follow Steps 9.7, 9.8, 10.5, and 11.5:

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

<!--skill-flavor:phase-seven-publish:start-->
Hard-stop AskUserQuestion (Step 16): `Publish to Orchestrator` / `Done`. On publish, run in order:

1. `uip solution resources refresh`
2. `uip maestro case pack <SolutionDir>/<ProjectName> <SolutionDir>/dist --output json`
3. `uip solution pack <SolutionDir> <SolutionDir>/dist --output json`
4. `uip solution publish <packagePath> --wait --output json`

`case pack` is mandatory because it creates `caseplan.json.bpmn`; `validate` does not. Publish the `solution pack` `.zip`, not the case `.nupkg`; read `<packagePath>` from `Data.Packages`, never guess. `Done` exits.
<!--skill-flavor:phase-seven-publish:end-->

## Reference Navigation

| Need | Reference |
|---|---|
| Design without SDD | `uipath-planner` Case Design Lane; Rule 16 |
| Resolve resources from SDD | [references/planning.md](references/planning.md) |
| Build caseplan from SDD | [references/implementation.md](references/implementation.md) |
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

- Do not leave a regular stage without an entry condition. The first stage uses `case-entered`; every other regular stage needs a reachable predecessor. Edges are retired. `validate` errors on this (`CASE_MGMT_STAGE_ENTRY_CONDITION_MISSING`).
- Do not design here, start Phase 1 before Case Review approval, or build from a summary SDD. The planner owns design, other-path analysis, and template conformance.
- Do not validate after each element or validate twice without an intervening edit. Phase 2 validation is informational; Phase 4 validation is authoritative and runs `--strict` — do not finish on a default-profile `Valid`.
- Do not author `tasks/tasks.md`, a T-numbered task list, or any other restatement of the SDD. The SDD is the plan; Phase 2 derives `caseplan.json` from it with `sdd convert` (Rule 4) and completes the remainder, and Step 12's `validate --strict --sdd sdd.md` audits the artifact against it. A generated `caseplan.json` is the artifact, not a restatement — this prohibition is about prose plans, never about the converter's output.
- Never one Write for the whole `caseplan.json`: `sdd convert` emits it and every change after that is a targeted Edit preserving untouched siblings. Re-read the plan and `sdd.md` after an interruption. Write cadence for the cases that still need one — brownfield section rewrites, a `case init`-unavailable scaffold — is in [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical).
- Do not emit standalone narration between tool calls. Bundle status with the next tool call; keep ordinary text under 200 tokens and allow-listed kickoff, hard-stop preambles, completion reports, DesignerUrl prints, and validation summaries under 500. Do not announce imminent actions with verbs such as `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next`, `Approach`, `Strategy`, `Plan`, `Let me`, or equivalent.
- Preserve ordered task semantics. Sequential mode uses ordered `data.tasks` sets and one `runs-sequentially` rule per task; do not add `current-stage-entered` alongside it. Use parallel `current-stage-entered` only for independent work and `selected-tasks-completed` only for required fan-in. Event-triggered tasks use event/condition rules; manually triggered/adhoc tasks use one `adhoc` rule, `isRequired: false`, and no additional entry event. `adhoc` is an activation mode, not a task type.
- Model secondary stages as interrupting exception lanes: `case-management:Stage`, `data.stageType: "secondary"`, `isRequired: false`, and `Interrupting: Yes` on stage and entries. Use `Interrupting: No` only for parallel SLA oversight. Use `return-to-origin`; do not connect secondary stages as normal flow or count them in required completion.
- Do not replicate global events or SLA rules across primary stages. Case completion requires a root `metadata.caseExitRules[]` rule with `marksCaseComplete: true`; stage completion alone is insufficient. Non-completing outcomes use `marksCaseComplete: false`.
- Do not edit generated `caseplan.json.bpmn`; do not place `caseplan.json` under `content/`; do not fabricate conditional-SLA expression syntax — `validate --strict` errors on a namespace-less `=js:` identifier (`STRICT_JS_UNKNOWN_IDENTIFIER`); describe conditions naturally until execution resolves them.
- Do not place `tasks/` in the solution/project; it stays beside `sdd.md`.
- Do not invoke other skills automatically except Rule 16 design handoff and Rule 18’s gate-selected inline creation of agents/API workflows. Do not spawn subagents for design, draft finalization, or plan-only documents.
- Do not read the installed CLI to interpret its own output. `validate` findings name the element path and the repair; the fix is in the caseplan or the reference that owns that shape, never in `node_modules/@uipath/**/dist`. Grepping a bundled chunk, or reimplementing a compare in `node -e` to predict it, spends the turn budget on the tool instead of the plan — one nightly task spent 56 of its 151 commands there and ran out of clock. If a finding is unclear after re-reading the named element and its reference, repair what the message names and move on; if it still fires, report it with `/uipath-feedback`.
- Use `uipath-feedback` for trouble.

> **Trouble?** Use `/uipath-feedback` to send a report.
