# Phase 1 — Resolution: sdd.md → registry-resolved.json

Resolve every resource the design document (`sdd.md`) names into tenant identities, and record them in `tasks/registry-resolved.json`. `sdd.md` stays the plan; this phase only fills in what the SDD could not know — task type IDs, connection IDs, folder paths, recipient identities. The downstream execution phases (Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Publish → Phase 6 Debug → Phase 7 Publish to Orchestrator) read the SDD and this ledger and write `caseplan.json` directly. See [implementation.md](implementation.md) for execution detail and [phased-execution.md](phased-execution.md) for phase contracts.

> **There is no intermediate plan file.** The SDD is the plan. Do not author a `tasks.md`, a T-numbered task list, or any other restatement of the SDD — it costs a full rewrite of the design and drifts from it. Losslessness is enforced against the finished artifact by the Step 12 `audit_caseplan.py` gate ([implementation.md](implementation.md)).

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this planning pipeline — see [brownfield.md](brownfield.md).

> **Output:** `tasks/registry-resolved.json` in the same directory as the sdd.md file. When SLA escalations are present, also `tasks/recipients-resolved.json` — see [`plugins/sla/planning.md` § Identity Resolution](plugins/sla/planning.md#identity-resolution). `tasks/` is adjacent to `sdd.md`, never inside the solution/project.
>
> **Exit:** Auto-proceeds to Phase 2. Stops after resolution only when the request explicitly asked to stop before the build.

> **Per-node-type detail lives in plugins.** This document covers the cross-cutting resolution workflow. For which SDD fields a specific node reads and how to resolve them, consult the relevant plugin:
> - Root case → `plugins/case/planning.md`
> - Stages (primary / secondary) → `plugins/stages/planning.md`
> - Tasks → `plugins/tasks/<type>/planning.md`
> - Triggers → `plugins/triggers/<type>/planning.md`
> - Conditions → `plugins/conditions/<scope>/planning.md`
> - SLA → `plugins/sla/planning.md`
> - Global variables & arguments → `plugins/variables/global-vars/planning.md`
> - Task I/O binding → `plugins/variables/io-binding/planning.md` (**always read alongside the matching task plugin**)

Each plugin's `planning.md` says how to read that element out of the SDD and what to resolve for it; the sibling `impl-json.md` turns the result into `caseplan.json` JSON.

---

> **Kickoff overview first (if not already shown).** When the design handoff did not run (user-provided `sdd.md`), this is the run's start — present the greenfield flow overview once before Step 0 so the dev knows the phases and the decision points. See [SKILL.md § Kickoff — set dev expectations](../SKILL.md#kickoff--set-dev-expectations-first). If the delegation window already showed it, skip.

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

Registry discovery happens during build planning, so login is required first. This gate runs on every Phase 1 build run — including SDD-without-ledger handoffs and runs with a staged `tasks/registry-resolved.json` — **with two exceptions:** the same-session fast path, and the Design-only exception in SKILL.md Rule 3 (restated below). For the same-session fast path, when the planner subagent's report (SKILL.md Rule 15) says its `registry pull` succeeded in THIS session — the `~/.uip/case-resources/` cache is machine-global, so the subagent's pull is this session's pull — reuse that cache and skip the re-pull, and run this step **verify-only**: persist the subagent's returned resolution ledger verbatim to `tasks/registry-resolved.json`, spot-verify entries against the session cache, execute recorded `gateDecision`s (Rule 17), and re-resolve only stale or missing entries. Any doubt in a build run (user-provided SDD, cross-session resume, context compaction, failed or never-run design-lane pull, missing cache files) runs the gate in full.

**Design-only exception:** when the request explicitly asks to stop at the design and not create `caseplan.json`, do not run login, registry, connection, schema, or user-discovery commands. The deliverable is `sdd.md` alone, with tenant identities left `<UNRESOLVED>`; state that the later build run must run this hard gate before caseplan execution. Do not author a substitute plan file.

**Negative trigger — tenant work overrides it.** The exception defers tenant lookup; it does not describe where a run stops. It does NOT fire when the same request asks to resolve resources or identities, pull or refresh the registry, replace a stale registry audit, or produce `tasks/registry-resolved.json` / `tasks/recipients-resolved.json` — even when that request also says to stop before `caseplan.json`, a solution, or Phase 2. Such a run is a normal resolution run: run this gate in full, resolve every identity, write the ledger, and stop before Phase 2.

```bash
uip login status --output json
uip maestro case registry pull
```

Outside the fast path, do not inspect `~/.uip/case-resources/` first to decide whether the pull is necessary: cache absence is exactly why the pull must run. Do not continue to Step 2/3 and do not write `registry-resolved.json` unless the pull succeeds. If not logged in, prompt the user to log in and stop Phase 1; if the pull fails, surface the command error and stop Phase 1. After a successful pull, read [registry-discovery.md](registry-discovery.md) before the first cache lookup. The pull caches all resources locally at `~/.uip/case-resources/` so subsequent searches are local disk lookups.

## Step 2 — Locate and parse the design document

Accept the `sdd.md` file path from the user, or ask if not provided. When the directory contains multiple `.md` files, use **AskUserQuestion** with the candidates + "Something else" to disambiguate.

If the resolved path has **no `sdd.md`**, the skill hands the design to the `uipath-planner` Case Design Lane in this conversation before this step (SKILL.md Rule 15 + § Design handoff). Phase 1 begins after the Case Review's Build answer, once the lane has written `sdd.md`. The in-memory model that rendered the file drives planning directly (Rule 2 — do not re-read the just-written file); the Case Review is approval context, not a parsing source.

`sdd.md` is the **sole required input**. It describes stages, tasks, conditions, SLA, component types, persona information, and provides the search keys for registry lookups. The portable name is type-specific: `Resolved Resource` for process/agent/rpa/api-workflow, the Action App title in `HITL Implementation` for action, and `Child Case` for case-management. The corresponding identity cell (`Resource Identity` or `Action App ID`) says whether an earlier phase resolved it. (The SDD does not describe edges — transitions are stage entry/exit conditions; Rule 20.) The skill does not validate or gap-fill sdd.md — trust it as written. (The delegated design lane may have produced it; once approved, Rule 2 applies regardless of source.)

> **Cache-state distinction — mandatory.** Step 1 refreshes discovery state; it does not validate or override sdd.md. Before a successful pull, a missing cache directory or type index is a failed refresh precondition, not evidence that the SDD resource is unavailable. After a successful pull, search by the SDD's concrete portable name; only an empty exact-name match set (or a still-absent type index) is a genuine empty lookup. An `<UNRESOLVED>` identity or folder means name-only discovery, not permission to skip discovery.

> **Design-lane carryover.** `tasks/registry-resolved.json` is an optional performance cache/audit artifact, never the source of resource intent. Same-session, it is seeded verbatim from the planner's resolution ledger (Rule 9); the reuse conditions below apply to every entry regardless of origin. Step 1 still runs first. If it exists, read it, associate an entry by exact `stage` + `task`, and reuse it **only when ALL four hold against the current SDD contract**:
>
> 1. `taskType` matches the SDD task type.
> 2. `cacheFile` is compatible with that type under [registry-discovery.md](registry-discovery.md) (`action` and `case-management` require their primary cache exactly).
> 3. `searchQuery` and the selected entry's canonical name equal the SDD's type-specific portable name.
> 4. The SDD identity and folder are both concrete and equal the selected entry's identity and exact folder.
>
> Canonical selected fields: `deploymentTitle` / `deploymentFolder.fullyQualifiedName` / `id` for action; `name` / `folders[0].fullyQualifiedName` / `entityKey` for the other non-connector types. Normalize a labeled SDD identity (e.g. `agentId <uuid> (v1.0.6)`) before comparison — the ID token must equal `entityKey`, and any SDD version must equal the selected entry's version metadata (e.g. `customData.ProcessVersion`) when present. **If any field is missing, `<UNRESOLVED>`, or mismatched, treat the entry as stale:** ignore it, re-run discovery from the SDD, and replace that task's audit entry. Never let a cached identity upgrade or override unresolved or edited SDD fields. If the file is absent, run the same discovery from each task's portable name and write a fresh file. This rule covers the portable-resource task types above; connector resolution continues through [connector-integration.md](connector-integration.md), unchanged.

## Step 3 — Resolve resources

Before resource resolution, seed TodoWrite with the items below to track Phase 1 progress. Mark each `in_progress` on entry, `completed` on exit. One item per class — never per SDD row.

1. Resolve task resources (registry lookups — this Step 3)
2. Resolve trigger resources (connector key, connection, activity type)
3. Resolve connector-bound condition resources
4. Resolve SLA escalation recipients (`recipients-resolved.json`)
5. Write `registry-resolved.json`, auto-proceed to Phase 2 (Step 5)

For every task, trigger, and condition in the sdd.md:

If the design-only exception is active — per Step 1, including its negative trigger, and not merely because the request stops before `caseplan.json` — skip registry and schema discovery in this step and do not fan out through every plugin `planning.md`. The SDD already carries the design; leave its tenant identities `<UNRESOLVED>`, report which resources the later build run must resolve, and stop. Do not write a plan file in its place.

End the response with suggested next steps: review the SDD, then run a build to resolve tenant resources and create `caseplan.json`.

Otherwise, continue with the normal resolution path:

1. **Identify the plugin** by matching the sdd.md component description to an entry in the catalogs below (§3.1–§3.3).
2. **Load the plugin's `planning.md` — once per plugin type, not per component.** It lists the exact fields to resolve from sdd.md, the cache file(s) to consult, and any discovery steps required. Group the SDD's components by plugin type, read that plugin's `planning.md` a single time, then resolve and emit EVERY component of that type from the one read. Re-reading a plugin reference per element is a read-budget defect (observed: `planning.md` re-read 10–16×, `impl-json.md` up to 26× per build); after context compaction, re-read only the plugin for the section in progress.
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

> **`agent` & `api-workflow` — create-on-missing.** Both kinds can be built inline at the Rule 17 gate — flow in [§ 3.4](#34-unresolved-resources); type specifics: [agent](plugins/tasks/agent/planning.md#creating-an-agent-inline) / [api-workflow](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline). All other kinds (regular RPA `process`, action, connectors, agentic process) use the §3.4 placeholder path.

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

> **Connector-bound condition rules.** Any of the 4 condition scopes above can carry a rule whose WHEN is `wait-for-connector` — binding an Integration Service connector event to gate the condition. These rules require the same connector-resolution pipeline as a task-class `wait-for-connector` (TypeCache + `case spec --type trigger` + reference-resolution). Resolution MUST collect the connector fields (`type-id`, `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`, optional `outputs`) alongside the condition's `display-name` / `rule-type` / `condition-expression` from the SDD. Collect them into the condition's `registry-resolved.json` entry so Phase 2 does not re-discover them. Shared recipe: [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule); per-scope fields in each condition plugin's `planning.md`.

### 3.4 Unresolved resources

When a resource cannot be resolved (registry gap and no cache match, or missing connection), **do not fabricate a placeholder or mock**.

> **Missing connection — offer to create first.** A missing/empty IS connection is not immediately "unresolved". The connector pipeline offers to create one via `uip is connections create` ([connector-integration.md § Step 2](connector-integration.md), [connector-trigger-planning.md § Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)). Only after the user **declines** or creation fails does the connection become `<UNRESOLVED>` and fall through to the steps below.

> **Missing agent or API workflow — offer to create first.** A missing `agent` (no `agent-index.json` match) or `api-workflow` (no `api-index.json` match) is not immediately "unresolved". At the Rule 17 empty-lookup gate the skill offers to build it as an in-solution sibling — it spawns a sub-agent that invokes `uipath-agents` (agent) / `uipath-api-workflow` (API workflow), then rediscovers + binds via `registry --local` ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery); specifics in [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline) / [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline)). Only after the user **declines**/skips, the build fails, or the CLI lacks `registry --local` does it become `<UNRESOLVED>` and fall through to the steps below. Other kinds (regular RPA process, action, case-management, connectors, agentic process) have no inline-create path — they fall straight through.

Otherwise:

1. Record `<UNRESOLVED: <reason>>` in that entry's `taskTypeId` / `typeId` / `connectionId` slot in `registry-resolved.json`, and set its `selected` to `null`.
2. Carry the input mapping the sdd.md described into the entry's `wiringNotes` string array — Phase 2 has no schema to wire against, and the completion report reads this back to the user. See [placeholder-tasks.md](placeholder-tasks.md).
3. **Continue resolving — do not halt.** The SDD still carries every structural field (display name, required, run-only-once), and Phase 2 still writes the task node and its entry conditions.

At execution time, unresolved tasks become **placeholder tasks** in `caseplan.json` (display-name + type only, no task-type-id, no bindings). The workflow graph is still reviewable end-to-end, and the user attaches real resources + bindings externally before runtime. See [placeholder-tasks.md](placeholder-tasks.md).

## Step 4 — Write `registry-resolved.json`

Create a `tasks/` folder adjacent to the sdd.md file and write `tasks/registry-resolved.json` — one entry per resolved task, trigger, and connector-bound condition, using Rule 9's exact keys: `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`. Keep the full exact-name match objects for debugging and stale-cache validation. `rationale` explains the selection choice (`"exact name match in caseManagement folder"`); it is never used for verify-text, SDD-vs-spec field translation, or downstream-plugin-behavior claims.

This ledger holds **only what registry lookups produced**. It is not a copy of the SDD: do not restate stage/task structure, activation modes, entry rules, inputs, outputs, or design rationale in it. Phase 2 and Phase 3 read those straight from `sdd.md`, which stays the single source of the design contract. Duplicating the contract here re-creates the drift the retired `tasks.md` caused.

Use the same section-batched write discipline the caseplan uses — one Read per section (tasks → triggers → conditions → SLA recipients), N Edit-appends, no re-Read between siblings. See [case-editing-operations.md](case-editing-operations.md).

> **Registry handoff labels.** For a resolved `action` or `case-management` entry, record the selected audit object under the canonical labels Phase 2 reads:
>
> | Task type | `name` from | `folder-path` from | `taskTypeId` from |
> |---|---|---|---|
> | `action` | `selected.deploymentTitle` | `selected.deploymentFolder.fullyQualifiedName` | `selected.id` |
> | `case-management` | `selected.name` | `selected.folders[0].fullyQualifiedName` | `selected.entityKey` |
>
> Confirm these values match the `selected` object in the same entry before leaving Step 4.

## Step 5 — Hand off to Phase 2 (auto-proceed)

Phase 1 is complete when every resource row in the SDD has an entry in `registry-resolved.json` — resolved, marked `<UNRESOLVED: …>`, or created inline at the Rule 17 gate. Report the counts (resolved / created inline / unresolved) and proceed directly to Phase 2 — no AskUserQuestion approval prompt, no wait for sign-off.

**Stop-before-build exception.** When the request explicitly scoped the work to design or resolution only (e.g. "just the SDD", "resolve the resources but don't build", "don't build the case yet"), stop here: report the SDD and the ledger, and do NOT create a solution or caseplan. This is the only condition that halts the auto-proceed.

Phase 2 reads `sdd.md` for the design and `registry-resolved.json` for identities. Both are on disk; re-read them at Phase 2 entry (context may have compacted during resolution) — see [implementation.md](implementation.md).

<!-- END: planning.md -->
