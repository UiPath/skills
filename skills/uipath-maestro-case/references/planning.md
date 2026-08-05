# Phase 1 — Planning: sdd.md → tasks.md

Generate reviewable task plan (`tasks.md`) from design document (`sdd.md`). Discovers registry resources, resolves task type IDs, produces declarative specification that downstream execution phases (Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Publish → Phase 6 Debug → Phase 7 Publish to Orchestrator) consume via direct JSON writes to `caseplan.json`. See [implementation.md](implementation.md) for execution detail and [phased-execution.md](phased-execution.md) for phase contracts.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this planning pipeline — see [brownfield.md](brownfield.md).

> **Output:** `tasks/tasks.md` + `tasks/registry-resolved.json` in the same directory as the sdd.md file. When SLA escalations are present, also `tasks/recipients-resolved.json` — see [`plugins/sla/planning.md` § Identity Resolution](plugins/sla/planning.md#identity-resolution). Explicit plan-only / no-build runs stop at `tasks/tasks.md` and skip registry-derived audit files because tenant lookup is deferred to the later build run.
>
> **Exit:** Auto-proceeds to Phase 2 — plan treated as approved, no prompt by default. Stops after `tasks.md` only when the request explicitly asked for a plan-only / review-first run. Re-read `tasks.md` before execution.

> **Per-node-type detail lives in plugins.** This document covers the cross-cutting planning workflow. For how to fill fields for a specific node, consult the relevant plugin:
> - Root case → `plugins/case/planning.md`
> - Stages (primary / secondary) → `plugins/stages/planning.md`
> - Tasks → `plugins/tasks/<type>/planning.md`
> - Triggers → `plugins/triggers/<type>/planning.md`
> - Conditions → `plugins/conditions/<scope>/planning.md`
> - SLA → `plugins/sla/planning.md`
> - Global variables & arguments → `plugins/variables/global-vars/planning.md`
> - Task I/O binding → `plugins/variables/io-binding/planning.md` (**always read alongside the matching task plugin**)

---

> **Kickoff overview first (if not already shown).** When Phase 0 did not run (user-provided `sdd.md`), this is the run's start — present the greenfield flow overview once before Step 0 so the dev knows the phases and the decision points. See [SKILL.md § Kickoff — set dev expectations](../SKILL.md#kickoff--set-dev-expectations-first). If Phase 0 already showed it, skip.

## Step 0 — Resolve the `uip` binary

`uip` is installed via npm. Resolve the binary (it may not be on PATH in nvm environments), capture its version, and upgrade only when the installed version is **older** than the latest published `@uipath/cli` — dev builds may be newer than the npm release, leave those alone:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
CURRENT=$($UIP --version 2>/dev/null | awk '{print $NF}')
LATEST=$(npm view @uipath/cli version 2>/dev/null)
OLDEST=$(printf '%s\n%s\n' "$LATEST" "$CURRENT" | sort -V | head -n1)
if [ -z "$CURRENT" ] || { [ "$CURRENT" != "$LATEST" ] && [ "$OLDEST" = "$CURRENT" ]; }; then
  npm install -g @uipath/cli@latest
  UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
fi
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

If `npm install -g` fails with a permission error, prompt the user to re-run it with the appropriate privileges (e.g., `sudo npm install -g @uipath/cli@latest`) — do not retry automatically.

## Step 1 — HARD GATE: check login and pull registry

Registry discovery happens during build planning, so login is required first. This gate runs on every Phase 1 build run — including SDD-only handoffs and runs with a staged `tasks/registry-resolved.json` — **with two exceptions:** the same-session fast path, and the explicit plan-only / no-build path in SKILL.md Rule 3. For the same-session fast path, when Phase 0's `registry pull` already succeeded in THIS session and `sdd.md` was just rendered from the confirmed in-memory model, reuse that cache and skip the re-pull. Any doubt in a build run (user-provided SDD, cross-session resume, context compaction, failed or never-run Phase 0 pull, missing cache files) runs the gate in full.

**Plan-only / no-build exception:** when the request explicitly asks to stop at `tasks.md` and not create `caseplan.json`, do not run login, registry, connection, schema, or user-discovery commands. Generate `tasks/tasks.md` from the SDD's concrete intended resource/system names, mark tenant identities `resolve at build`, omit registry-derived audit files, and state that the later build run must rerun this hard gate before caseplan execution.

```bash
uip login status --output json
uip maestro case registry pull
```

Outside the fast path, do not inspect `~/.uip/case-resources/` first to decide whether the pull is necessary: cache absence is exactly why the pull must run. Do not continue to Step 2/3 and do not write `tasks.md` or `registry-resolved.json` unless the pull succeeds. If not logged in, prompt the user to log in and stop Phase 1; if the pull fails, surface the command error and stop Phase 1. After a successful pull, read [registry-discovery.md](registry-discovery.md) before the first cache lookup. The pull caches all resources locally at `~/.uip/case-resources/` so subsequent searches are local disk lookups.

## Step 2 — Locate and parse the design document

Accept the `sdd.md` file path from the user, or ask if not provided. When the directory contains multiple `.md` files, use **AskUserQuestion** with the candidates + "Something else" to disambiguate.

If the resolved path has **no `sdd.md`**, skill enters Phase 0 (interview mode) before this step. See [phase-0-interview.md](phase-0-interview.md). Phase 1 begins after Phase 0's confirmation (a Build answer). **Same-session fast path:** Phase 0 just rendered `sdd.md` from the confirmed in-memory model — plan from that model directly and skip re-reading the file; re-read `sdd.md` only when working memory may be stale (context compaction, resumed session), and then trust it as written (Rule 2).

`sdd.md` is the **sole required input**. It describes stages, tasks, conditions, SLA, component types, persona information, and provides the search keys for registry lookups. The portable name is type-specific: `Resolved Resource` for process/agent/rpa/api-workflow, the Action App title in `HITL Implementation` for action, and `Child Case` for case-management. The corresponding identity cell (`Resource Identity` or `Action App ID`) says whether an earlier phase resolved it. (The SDD does not describe edges — transitions are stage entry/exit conditions; Rule 20.) The skill does not validate or gap-fill sdd.md — trust it as written. (Phase 0 may have generated it; once approved, Rule 2 applies regardless of source.)

> **Cache-state distinction — mandatory.** Step 1 refreshes discovery state; it does not validate or override sdd.md. Before a successful pull, a missing cache directory or type index is a failed refresh precondition, not evidence that the SDD resource is unavailable. After a successful pull, search by the SDD's concrete portable name; only an empty exact-name match set (or a still-absent type index) is a genuine empty lookup. An `<UNRESOLVED>` identity or folder means name-only discovery, not permission to skip discovery.

> **Phase 0 carryover.** `tasks/registry-resolved.json` is an optional performance cache/audit artifact, never the source of resource intent. Step 1 still runs first. If it exists, read it, associate an entry by exact `stage` + `task`, and reuse it **only when ALL four hold against the current SDD contract**:
>
> 1. `taskType` matches the SDD task type.
> 2. `cacheFile` is compatible with that type under [registry-discovery.md](registry-discovery.md) (`action` and `case-management` require their primary cache exactly).
> 3. `searchQuery` and the selected entry's canonical name equal the SDD's type-specific portable name.
> 4. The SDD identity and folder are both concrete and equal the selected entry's identity and exact folder.
>
> Canonical selected fields: `deploymentTitle` / `deploymentFolder.fullyQualifiedName` / `id` for action; `name` / `folders[0].fullyQualifiedName` / `entityKey` for the other non-connector types. Normalize a labeled SDD identity (e.g. `agentId <uuid> (v1.0.6)`) before comparison — the ID token must equal `entityKey`, and any SDD version must equal the selected entry's version metadata (e.g. `customData.ProcessVersion`) when present. **If any field is missing, `<UNRESOLVED>`, or mismatched, treat the entry as stale:** ignore it, re-run discovery from the SDD, and replace that task's audit entry. Never let a cached identity upgrade or override unresolved or edited SDD fields. If the file is absent, run the same discovery from each task's portable name and write a fresh file. This rule covers the portable-resource task types above; connector resolution continues through [connector-integration.md](connector-integration.md), unchanged.

## Step 3 — Resolve resources

Before resource resolution, seed TodoWrite with the items below to track Phase 1 progress through registry lookups and §4 T-entry emit. Mark each `in_progress` on entry, `completed` on exit. One item per emit class — never per T-entry.

1. Resolve registry resources (this Step 3)
2. Write case file T01 (§4.2)
3. Write trigger entries T02+ (§4.3)
4. Write variable / argument entries (§4.2.1)
5. Write stage entries (§4.4)
6. Write task entries (§4.6)
7. Write condition entries (§4.7)
8. Write SLA entries (§4.8)
9. Finalize tasks.md, auto-proceed to Phase 2 (Step 5)

For every task, trigger, and condition in the sdd.md:

If the plan-only / no-build exception is active, skip registry and schema discovery in this step and do not fan out through every plugin `planning.md`. Use the compact no-build shape below for the review plan: preserve SDD portable names, emit tenant identities as `resolve at build`, carry every rationale, and stop after `tasks/tasks.md`. The compact no-build plan is exempt from the normal section-batched planning workflow because it is a review artifact, not a build handoff: create `tasks/` if needed and write the complete concise `tasks/tasks.md` with one direct Write, then stop. The later build run owns authoritative resource resolution and regenerates any registry-derived fields before Phase 2.

**Compact no-build T-entry shape:** each declaration still gets a T-number, but the fields are intentionally review-oriented:

- Task declarations use an H2 heading with a quoted display name: `## T{N}: task "{Task Name}"`. Do not use dotted task T-numbers (for example, `T12.1`) as the task entry heading; if you group entries by stage, the task's own T-entry still remains the H2.
- Stage entries: `stage-kind`, `entry-rule`, `exit-rule`, `interrupting`, `required`, `sla`, `rationale`.
- Task entries: `stage`, `type`, `activation-mode`, `entry-rule`, `lane`, `required`, `run-only-once`, `resource-intent`, `identity: resolve at build`, `rationale`.
- Trigger/condition/SLA entries: `rule-type`, `source/status`, `target stage/task`, `return-or-close behavior`, `rationale`. Every `selected-tasks-completed` entry carries `selected-tasks-ids`.

**Rule-valued fields take canonical values, never prose.** `activation-mode`, `entry-rule`, `exit-rule`, and `rule-type` carry a value from their vocabulary exactly as spelled (`runs-sequentially`, `current-stage-entered`, `wait-for-connector`, `adhoc`, `selected-tasks-completed`, …) — review-oriented does not mean free text. When the supplied/approved SDD has an explicit rule row, copy that rule and its selectors exactly; task proximity and list order never authorize planning to normalize it. Only derive `runs-sequentially` for ordered work whose source does not already declare an entry rule. Put the human phrasing in `rationale`.

**`lane` is a number, and grouping is expressed by sharing it.** `lane` is the zero-based `data.tasks` task-set index — `lane: 2`, never a descriptive name like `lane: payment confirmation`. Tasks that run as one task set carry the **same** number: `parallel-after-predecessor` siblings after one predecessor share a single lane value, and a strict chain increments. Giving two siblings different lanes contradicts their `activation-mode` and emits them as separate task sets, which is the defect the mode exists to prevent — the label alone does not group them.

Do not add `taskTypeId`, `activityTypeId`, `connectionId`, resolved schemas, `inputs`, `outputs`, `registry-resolved.json`, or `recipients-resolved.json` in this mode; those require tenant evidence and belong to the later build run. End the response with suggested next steps: review the SDD and plan, then run a later build to resolve tenant resources and create `caseplan.json`.

When the plan-only / no-build exception is not active, continue with the normal build-planning path:

1. **Identify the plugin** by matching the sdd.md component description to an entry in the catalogs below (§3.1–§3.3).
2. **Load the plugin's `planning.md`** — it lists the exact fields to resolve from sdd.md, the cache file(s) to consult, and any discovery steps required.
3. **Apply registry discovery** via [registry-discovery.md](registry-discovery.md) when a taskTypeId is needed. Use the type-specific portable-name field as the query: `Resolved Resource` for process/agent/rpa/api-workflow, Action App title for action, and `Child Case` for case-management. A missing or `<UNRESOLVED>` portable name violates the SDD contract and must be surfaced instead of silently falling back to `Task Name`.
4. **Persist every resolution** to `registry-resolved.json` using Rule 9's exact keys (`stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`). Keep the full exact-name match objects for debugging and stale-cache validation.

### 3.1 Task Type catalog

> **Closed enum — 9 values.** sdd.md `Type:` and caseplan.json `type` field both use the schema-kebab values in column 1. Plugin folder name (column 2) is what to open during planning + execution; it is NOT what gets written into JSON. See SKILL.md Rule 16 + Plugin Index naming-asymmetry note. Any value outside this set (`external-agent`, `connector-activity`, `wait-for-event`, etc.) is invalid — write a `<UNRESOLVED>` placeholder instead.

| sdd.md `Type:` / caseplan.json `type` | Plugin folder |
|---|---|
| `process` (covers `AGENTIC_PROCESS` legacy label) | `plugins/tasks/process/` |
| `agent` | `plugins/tasks/agent/` |
| `rpa` | `plugins/tasks/rpa/` |
| `action` | `plugins/tasks/action/` |
| `api-workflow` | `plugins/tasks/api-workflow/` |
| `case-management` | `plugins/tasks/case-management/` |
| `execute-connector-activity` | `plugins/tasks/connector-activity/` |
| `wait-for-connector` | `plugins/tasks/connector-trigger/` |
| `wait-for-timer` | `plugins/tasks/wait-for-timer/` |

> **`agent` and `api-workflow` are conditionally creatable.** Resolve them normally first. Only a genuine empty that Rule 17 assigns to **Create** loads the shared and selected type guides; resolved, pre-gate, unchecked, and fallback paths do not. Every other kind is non-creatable but still joins the Rule 17 batch as `placeholder only`.

### 3.2 Trigger Type catalog (case-level)

| sdd.md description | Plugin |
|--------------------|--------|
| "Start manually" / "User initiates" | `plugins/triggers/manual/` |
| "Every N hours/days" / scheduled / cron-like | `plugins/triggers/timer/` |
| Event from external system (connector-based) | `plugins/triggers/event/` |

### 3.3 Condition Scope catalog

| Where the condition attaches | Plugin |
|------------------------------|--------|
| On stage entry | `plugins/conditions/stage-entry-conditions/` |
| On stage exit | `plugins/conditions/stage-exit-conditions/` |
| On task entry | `plugins/conditions/task-entry-conditions/` |
| On case exit | `plugins/conditions/case-exit-conditions/` |

> **Connector-bound condition rules.** Any of the 4 condition scopes above can carry a rule whose WHEN is `wait-for-connector` — binding an Integration Service connector event to gate the condition. These rules require the same connector-resolution pipeline as a task-class `wait-for-connector` (TypeCache + `case spec --type trigger` + reference-resolution). Plan-step planners MUST collect connector fields (`type-id`, `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`, optional `outputs`) in the condition's T-entry alongside the standard `display-name` / `rule-type` / `condition-expression` fields. Shared recipe: [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule); per-scope tasks.md format in each condition plugin's `planning.md`.

### 3.4 Unresolved resources

When a resource cannot be resolved (registry gap and no cache match, or missing connection), **do not fabricate a placeholder or mock**.

> **Missing connection — offer to create first.** A missing/empty IS connection is not immediately "unresolved". The connector pipeline offers to create one via `uip is connections create` ([connector-integration.md § Step 2](connector-integration.md), [connector-trigger-planning.md § Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)). Only after the user **declines** or creation fails does the connection become `<UNRESOLVED>` and fall through to the steps below.

> **Every genuine empty enters Rule 17 before this fallback.** The [registry owner](registry-discovery.md#must-confirm-before-placeholder-fallback) batches agent, API-workflow, and non-creatable empties together. A batch **Create** choice loads [inline-resource-creation-guide.md](inline-resource-creation-guide.md) first; only its checked-resource result loads [create-inline-common.md](plugins/tasks/create-inline-common.md) and the represented type guide. Otherwise load no Create guide. Unchecked/failed resources and every `placeholder only` item reach the steps below only after the Rule 17 flow assigns fallback.

Otherwise:

1. Mark the line in `tasks.md` with `<UNRESOLVED: <reason>>` in the `taskTypeId` / `typeId` / `connectionId` slot.
2. **Omit `inputs:` and `outputs:` entirely** on that task entry — there is no schema to wire against. Any input mapping the sdd.md described becomes a fenced ```` ```text ```` code block under the entry with a `wiring notes (user must attach):` header line. **Do not start lines with `#`** — they would render as markdown headings; use a fenced code block instead. Example shape is in [placeholder-tasks.md § `tasks.md` Planning-Entry Shape](placeholder-tasks.md).
3. Keep every other structural field (display-name, isRequired, runOnlyOnce, order). Task-entry conditions still emit normally.
4. **Continue planning — do not halt.**

At execution time, unresolved tasks become **placeholder tasks** in `caseplan.json` (display-name + type only, no task-type-id, no bindings). The workflow graph is still reviewable end-to-end, and the user attaches real resources + bindings externally before runtime. See [placeholder-tasks.md](placeholder-tasks.md).

## Step 4 — Generate tasks.md and registry-resolved.json

**Load boundary.** Only when Phase 1 reaches this step — after discovery and resource resolution — read [tasks-plan-contract-guide.md](tasks-plan-contract-guide.md) in full before the first Step 4 artifact write.

Create a `tasks/` folder adjacent to the sdd.md file. Generate `tasks/tasks.md` as a declarative, lossless handoff: every sdd.md declaration has its own T-entry, and the implementation phase translates those entries into the matching plugin's JSON writes.

Also write `tasks/registry-resolved.json` — full detail per task using Rule 9's exact keys: task type, searched cache filename, search query, all exact-name matches, selected entry, and rationale.

### 4.0 Completeness principle (no omissions)

Compatibility route: at Step 4, follow [§4.0 in the tasks.md plan contract](tasks-plan-contract-guide.md#40-completeness-principle-no-omissions).

### 4.0a — Section-batched write contract (mandatory)

Compatibility route: at Step 4, follow [§4.0a in the tasks.md plan contract](tasks-plan-contract-guide.md#40a--section-batched-write-contract-mandatory).

### 4.3 Configure trigger(s) (T02+)

Compatibility route: at Step 4, follow [§4.3 in the tasks.md plan contract](tasks-plan-contract-guide.md#43-configure-triggers-t02).

---

## Step 5 — Finalize tasks.md (auto-proceed to Phase 2)

Treat the generated `tasks.md` as approved and proceed directly to Phase 2 by default — no AskUserQuestion approval prompt, no wait for sign-off.

**Stop-after-plan exception (the virtual gate).** When the request explicitly scoped the work to planning only (e.g. "just build tasks.md", "Phase 1 only", "stop after the plan for review", "don't build the case yet"), stop here: report the finished plan and do NOT create a solution or caseplan. This is the only condition that halts the auto-proceed.

Re-read `tasks.md` before proceeding to Phase 2 (see [implementation.md](implementation.md)); context may have compacted during planning. `tasks.md` is complete handoff artifact — all resolved IDs, inputs, outputs, and references captured there.

**Plan-shape gate.** Before Phase 2, re-read every [§4.6 task T-entry](tasks-plan-contract-guide.md#46-add-tasks) itself (not the §4.7 condition entries) and confirm it literally contains its own `- activation-mode:` line and its own `- entry-rule:` line — **exactly one of each, colocated on the task's own T-entry** — and that the pair is legal for that mode. Re-run the [§4.6 Activation-mode audit](tasks-plan-contract-guide.md#46-add-tasks) over the finished plan, covering all seven modes, not just `sequential`.

**Known failure pattern:** deferring the rule to a *separate* §4.7 task-entry-condition entry (`rule-type:`) does not satisfy this gate — `caseplan.json` can end up fully correct while `tasks.md` itself still fails this check, because §4.6 and §4.7 are graded as separate artifacts. See [task-entry-conditions/planning.md § Phase 1 Plan Presentation Contract](plugins/conditions/task-entry-conditions/planning.md#phase-1-plan-presentation-contract) for the compliant §4.6 shape.

Correct the plan before building; validation of `caseplan.json` cannot detect a malformed Phase 1 handoff.

<!-- END: planning.md -->
