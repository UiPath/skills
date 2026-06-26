# Phase 1 — Planning: sdd.md → tasks.md

Generate reviewable task plan (`tasks.md`) from design document (`sdd.md`). Discovers registry resources, resolves task type IDs, produces declarative specification that downstream execution phases (Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Publish → Phase 6 Debug → Phase 7 Publish to Orchestrator) consume via direct JSON writes to `caseplan.json`. See [implementation.md](implementation.md) for execution detail and [phased-execution.md](phased-execution.md) for phase contracts.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this planning pipeline — see [brownfield.md](brownfield.md).

> **Output:** `tasks/tasks.md` + `tasks/registry-resolved.json` in the same directory as the sdd.md file. When SLA escalations are present, also `tasks/recipients-resolved.json` — see [`plugins/sla/planning.md` § Identity Resolution](plugins/sla/planning.md#identity-resolution). Explicit plan-only / no-build runs stop at `tasks/tasks.md` and skip registry-derived audit files because tenant lookup is deferred to the later build run — so a request that asks for those audit files is not a no-build run (Step 1).
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

> **Kickoff overview first (if not already shown).** When the design handoff did not run (user-provided `sdd.md`), this is the run's start — present the greenfield flow overview once before Step 0 so the dev knows the phases and the decision points. See [SKILL.md § Kickoff — set dev expectations](../SKILL.md#kickoff--set-dev-expectations-first). If the delegation window already showed it, skip.

## Step 0 — Resolve the `uip` binary

Resolve the `uip` binary (it may not be on PATH in nvm environments), capture its version, and upgrade only when the installed version is **older** than the latest published `@uipath/cli` — dev builds may be newer than the npm release, leave those alone. If `uip` is absent on a fresh machine, bootstrap with the official installer first; it installs Node.js >= 20, `@uipath/cli`, UiPath skills for installed AI coding agents, .NET SDK 8.0, and Python 3.11-3.14.

```bash
UIP=$(command -v uip 2>/dev/null || true)
if [ -z "$UIP" ] && command -v npm >/dev/null 2>&1; then
  UIP="$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip"
fi
if [ -z "$UIP" ] || [ ! -x "$UIP" ]; then
  curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash
  UIP=$(command -v uip 2>/dev/null || true)
fi
if [ -z "$UIP" ] || [ ! -x "$UIP" ]; then
  echo "Open a new shell so installer PATH changes take effect, then rerun this step." >&2
  exit 2
fi
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

On Windows PowerShell, use `irm https://download.uipath.com/uipath-cli/install.ps1 | iex` for the fresh-machine bootstrap. If `npm install -g` fails with a permission error during an upgrade, prompt the user to re-run it with the appropriate privileges (e.g., `sudo npm install -g @uipath/cli@latest`) — do not retry automatically.

## Step 1 — HARD GATE: check login and pull registry

Registry discovery happens during build planning, so login is required first. This gate runs on every Phase 1 build run — including SDD-without-ledger handoffs and runs with a staged `tasks/registry-resolved.json` — **with two exceptions:** the same-session fast path, and the explicit plan-only / no-build path in SKILL.md Rule 3. For the same-session fast path, when the planner subagent's report (SKILL.md Rule 15) says its `registry pull` succeeded in THIS session — the `~/.uip/case-resources/` cache is machine-global, so the subagent's pull is this session's pull — reuse that cache and skip the re-pull, and run this step **verify-only**: persist the subagent's returned resolution ledger verbatim to `tasks/registry-resolved.json`, spot-verify entries against the session cache, execute recorded `gateDecision`s (Rule 17), and re-resolve only stale or missing entries. Any doubt in a build run (user-provided SDD, cross-session resume, context compaction, failed or never-run design-lane pull, missing cache files) runs the gate in full.

**Plan-only / no-build exception:** when the request explicitly asks to stop at `tasks.md` and not create `caseplan.json`, do not run login, registry, connection, schema, or user-discovery commands. Generate `tasks/tasks.md` from the SDD's concrete intended resource/system names, mark tenant identities `resolve at build`, omit registry-derived audit files, and state that the later build run must rerun this hard gate before caseplan execution.

**Negative trigger — tenant work overrides it.** The exception defers tenant lookup; it does not describe where a run stops. It does NOT fire when the same request asks to resolve resources or identities, pull or refresh the registry, replace a stale registry audit, or produce `tasks/registry-resolved.json` / `tasks/recipients-resolved.json` — even when that request also says to stop before `caseplan.json`, a solution, or Phase 2. Such a run is a normal build-planning run: run this gate in full, resolve every identity, emit the build-path `tasks.md` shape (§4.6 plus each plugin's `planning.md`), and stop at the Rule 7 plan gate.

```bash
uip login status --output json
uip maestro case registry pull
```

Outside the fast path, do not inspect `~/.uip/case-resources/` first to decide whether the pull is necessary: cache absence is exactly why the pull must run. Do not continue to Step 2/3 and do not write `tasks.md` or `registry-resolved.json` unless the pull succeeds. If not logged in, prompt the user to log in and stop Phase 1; if the pull fails, surface the command error and stop Phase 1. After a successful pull, read [registry-discovery.md](registry-discovery.md) before the first cache lookup. The pull caches all resources locally at `~/.uip/case-resources/` so subsequent searches are local disk lookups.

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

If the plan-only / no-build exception is active — per Step 1, including its negative trigger, and not merely because the request stops before `caseplan.json` — skip registry and schema discovery in this step and do not fan out through every plugin `planning.md`. Use the compact no-build shape below for the review plan: preserve SDD portable names, emit tenant identities as `resolve at build`, carry every rationale, and stop after `tasks/tasks.md`. The compact no-build plan is exempt from the normal section-batched planning workflow because it is a review artifact, not a build handoff: create `tasks/` if needed and write the complete concise `tasks/tasks.md` with one direct Write, then stop. The later build run owns authoritative resource resolution and regenerates any registry-derived fields before Phase 2.

**Compact no-build T-entry shape:** each declaration still gets a T-number, but the fields are intentionally review-oriented:

- Task declarations use an H2 heading with a quoted display name: `## T{N}: task "{Task Name}"`. Do not use dotted task T-numbers (for example, `T12.1`) as the task entry heading; if you group entries by stage, the task's own T-entry still remains the H2.
- Stage entries: `stage-kind`, `entry-rule`, `exit-rule`, `interrupting`, `required`, `sla`, `rationale`.
- Task entries: `stage`, `type`, `activation-mode`, `entry-rule`, `lane`, `required`, `run-only-once`, `resource-intent`, `identity: resolve at build`, `rationale`.
- Trigger/condition/SLA entries: `rule-type`, `source/status`, `target stage/task`, `return-or-close behavior`, `rationale`. Every `selected-tasks-completed` entry carries `selected-tasks-ids`.
- Preserve each task's confirmed SDD activation semantics exactly. A singleton task that starts with its stage remains `activation-mode: parallel` + `entry-rule: current-stage-entered`; a single-task stage or list position does not make it sequential. Use `sequential` + `runs-sequentially` only when the source explicitly requires an ordered run or dependency.
- Global event/exception entries name exactly one interrupting secondary stage and the rule type (`wait-for-connector` or `sla-status-change`); do not duplicate those events across every primary stage. A `sla-status-change` entry names target + SLA title, plus an at-risk escalation title only for an at-risk row (a breach names the SLA alone) — all declared in the SDD and repeated verbatim in `tasks/tasks.md`. The case-level target is the literal `root` — never `Case`, the case name, or another synonym; stage-level targets use the exact stage display name.

**Rule-valued fields take canonical values, never prose.** `activation-mode`, `entry-rule`, `exit-rule`, and `rule-type` carry a value from their vocabulary exactly as spelled (`runs-sequentially`, `current-stage-entered`, `wait-for-connector`, `adhoc`, `selected-tasks-completed`, …) — review-oriented does not mean free text. When the supplied/approved SDD has an explicit rule row, copy that rule and its selectors exactly only after it passes the Critical Rules: every `selected-tasks-completed` selector must name a non-adhoc sibling in the same stage. An invalid selector is a stop-and-repair, never an authoritative carryover; task proximity and list order alone still never authorize planning to normalize a valid rule. Only derive `runs-sequentially` for ordered work whose source does not already declare an entry rule. Put the human phrasing in `rationale`.

**`lane` is a number, and grouping is expressed by sharing it.** `lane` is the zero-based `data.tasks` task-set index — `lane: 2`, never a descriptive name like `lane: payment confirmation`. Tasks that run as one task set carry the **same** number: `parallel-after-predecessor` siblings after one predecessor share a single lane value, and a strict chain increments. Giving two siblings different lanes contradicts their `activation-mode` and emits them as separate task sets, which is the defect the mode exists to prevent — the label alone does not group them.

Do not add `taskTypeId`, `activityTypeId`, `connectionId`, resolved schemas, `inputs`, `outputs`, `registry-resolved.json`, or `recipients-resolved.json` in this mode; those require tenant evidence and belong to the later build run.

**MANDATORY final gate:** the plan is not deliverable until the skill's deterministic audit prints `AUDIT OK` (read-only): `python3 "<this skill's folder>/scripts/audit_plan.py" tasks/tasks.md --sdd sdd.md`. On `AUDIT FAIL`, fix each finding with Edit and re-run; max 3 rounds, then surface the remaining findings. Quote the final `AUDIT OK` line in the reply as evidence. If `python3` is unavailable, re-check headings and per-task fields against this contract manually.

End the response with suggested next steps: review the SDD and plan, then run a later build to resolve tenant resources and create `caseplan.json`.

When the plan-only / no-build exception is not active, continue with the normal build-planning path:

1. **Identify the plugin** by matching the sdd.md component description to an entry in the catalogs below (§3.1–§3.3).
2. **Load the plugin's `planning.md` — once per plugin type, not per component.** It lists the exact fields to resolve from sdd.md, the cache file(s) to consult, and any discovery steps required. Group the SDD's components by plugin type, read that plugin's `planning.md` a single time, then resolve and emit EVERY component of that type from the one read. Re-reading a plugin reference per T-entry is a read-budget defect (observed: `planning.md` re-read 10–16×, `impl-json.md` up to 26× per build); after context compaction, re-read only the plugin for the section in progress.
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

> **Connector-bound condition rules.** Any of the 4 condition scopes above can carry a rule whose WHEN is `wait-for-connector` — binding an Integration Service connector event to gate the condition. These rules require the same connector-resolution pipeline as a task-class `wait-for-connector` (TypeCache + `case spec --type trigger` + reference-resolution). Plan-step planners MUST collect connector fields (`type-id`, `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`, optional `outputs`) in the condition's T-entry alongside the standard `display-name` / `rule-type` / `condition-expression` fields. Shared recipe: [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule); per-scope tasks.md format in each condition plugin's `planning.md`.

### 3.4 Unresolved resources

When a resource cannot be resolved (registry gap and no cache match, or missing connection), **do not fabricate a placeholder or mock**.

> **Missing connection — offer to create first.** A missing/empty IS connection is not immediately "unresolved". The connector pipeline offers to create one via `uip is connections create` ([connector-integration.md § Step 2](connector-integration.md), [connector-trigger-planning.md § Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)). Only after the user **declines** or creation fails does the connection become `<UNRESOLVED>` and fall through to the steps below.

> **Missing agent or API workflow — offer to create first.** A missing `agent` (no `agent-index.json` match) or `api-workflow` (no `api-index.json` match) is not immediately "unresolved". At the Rule 17 empty-lookup gate the skill offers to build it as an in-solution sibling — it spawns a sub-agent that invokes `uipath-agents` (agent) / `uipath-api-workflow` (API workflow), then rediscovers + binds via `registry --local` ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery); specifics in [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline) / [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline)). Only after the user **declines**/skips, the build fails, or the CLI lacks `registry --local` does it become `<UNRESOLVED>` and fall through to the steps below. Other kinds (regular RPA process, action, case-management, connectors, agentic process) have no inline-create path — they fall straight through.

Otherwise:

1. Mark the line in `tasks.md` with `<UNRESOLVED: <reason>>` in the `taskTypeId` / `typeId` / `connectionId` slot.
2. **Omit `inputs:` and `outputs:` entirely** on that task entry — there is no schema to wire against. Any input mapping the sdd.md described becomes a fenced ```` ```text ```` code block under the entry with a `wiring notes (user must attach):` header line. **Do not start lines with `#`** — they would render as markdown headings; use a fenced code block instead. Example shape is in [placeholder-tasks.md § `tasks.md` Planning-Entry Shape](placeholder-tasks.md).
3. Keep every other structural field (display-name, isRequired, runOnlyOnce, order). Task-entry conditions still emit normally.
4. **Continue planning — do not halt.**

At execution time, unresolved tasks become **placeholder tasks** in `caseplan.json` (display-name + type only, no task-type-id, no bindings). The workflow graph is still reviewable end-to-end, and the user attaches real resources + bindings externally before runtime. See [placeholder-tasks.md](placeholder-tasks.md).

## Step 4 — Generate tasks.md and registry-resolved.json

Create a `tasks/` folder adjacent to the sdd.md file. Generate `tasks.md` using the structure below. Each section is a numbered task (`T01`, `T02`, …) — declarative parameters only. Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax. The implementation phase translates each entry into the matching plugin's JSON writes.

Cross-reference: [case-schema.md](case-schema.md) for JSON shape, [bindings-and-expressions.md](bindings-and-expressions.md) for inputs/outputs wiring.

Also write `registry-resolved.json` — full detail per task using Rule 9's exact keys: task type, searched cache filename, search query, all exact-name matches, selected entry, and rationale.

### 4.0 Completeness principle (no omissions)

Every declaration in `sdd.md` must become a T-task in `tasks.md`. Mapping is 1-to-1:

- **Never filter** declarations on the grounds that the default rule-type, default field value, or "implicit behavior" would cover them. If `sdd.md` lists a task, stage, trigger, condition, SLA row, **variable, or argument**, `tasks.md` emits a T-task for it — regardless of rule-type (`current-stage-entered`, `case-entered`, `exit-only`, `required-tasks-completed`, etc.).
- **Never merge** two sdd.md items into one T-task "because they're similar."
- **Never drop** defaults-looking items (e.g., `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). The explicit declaration is the signal — honor it.
- **Never drop design rationale.** Copy each SDD stage/task/SLA `Design Rationale` into `rationale:` on its matching T-entry. Condition T-entries copy the rationale for the routing/activation choice they implement. Rationale is reviewer/audit context; the execution plugin ignores it when composing JSON.
- **When in doubt, emit.** It is always correct to create a T-task that mirrors an sdd.md row. It is never correct to silently omit one.
- **When format is ambiguous or unrecognized, ASK — do not skip.** If a row exists but you cannot determine the right plugin, category, or T-entry shape (e.g., trigger "Initial Variable Mapping" uses an aggregate phrase instead of explicit per-field mappings; a variable's category — In / Out / Variable — is unclear; a task type does not match the closed enum), invoke **AskUserQuestion** with the row content + the specific ambiguity + bounded options. Silent omission is a defect. This obligation applies to every sdd.md declaration class above, including variables and arguments.

Before finalizing `tasks.md` at Step 5, run a completeness cross-check: for every declared stage / task / trigger / condition / SLA row **and every Case Variables table row (one T-entry each, per §4.2.1)** in sdd.md, verify a corresponding T-task exists. Gaps are a defect — fix before proceeding to Phase 2.

**Cross-check inventory.** Before proceeding to Phase 2, count and report each class:

| Class | Source in sdd.md | T-entry section |
|---|---|---|
| Case file | Case Metadata | §4.2 (T01) |
| Triggers | Case Triggers | §4.3 (T02+) |
| Variables / arguments | Case Variables | §4.2.1 (after last trigger) |
| Stages | Section 2 stage headings | §4.4 |
| Tasks | Per-stage Tasks tables | §4.6 |
| Conditions | Stage Entry / Stage Exit / Task Entry / Case Exit tables | §4.7 |
| SLA | Case-Level SLA + per-stage Stage SLA + per-action Task SLA | §4.8 |

Counts that don't match the sdd.md → fix before Step 5 (before proceeding to Phase 2).

### 4.0a — Section-batched write contract (mandatory)

**Per-section batching.** Build `tasks.md` one section at a time — never compose the full body in memory and Write once, but do not pay a Read between sibling T-entries inside a section either.

Procedure:

1. **Seed.** Write `tasks.md` with a `## Inventory` placeholder section only. Single Write.
2. **Per section.** Sections are §4.2.1 vars → §4.3 triggers → §4.4 stages → §4.6 tasks → §4.7 conditions → §4.8 SLA. For each section:
   - **One Read** of `tasks.md` at section entry.
   - **N Edit-appends** in sequence, one per T-entry in the section. Skip the re-Read between sibling Edits — Edit's tool result confirms applied state in context.
   - TaskUpdate marks each T-entry `in_progress` → `completed` as it goes — that is the per-T-entry audit trail, not the file diff.
3. **Inventory finalize.** After last T-entry, Edit the inventory section with class-by-class counts (per §4.0 cross-check table).
4. **`registry-resolved.json`.** Same section-batched discipline — one Read per section, N Edit-appends, no re-Read between siblings.

**T-entry heading contract.** Every declaration is its own level-two heading in the exact form `## T<n>: <action>`. Do not use level-three-or-deeper headings for T-entries, and do not nest a task beneath a stage's T-entry. A task heading must quote its display name, for example `## T08: Add wait-for-timer task "First Step" to "Process"`. This keeps the plan independently addressable by Phase 2 and by plan validators.

Why: section-batched round-trips keep tool-call transcript reviewable, preserve rollback granularity at section boundary, allow mid-run interruption recovery via re-Read + resume from next un-applied T-entry, and surface omissions before they propagate — without paying a per-T-entry Read tax that inflates inference latency by ~5s per turn.

**Hard cap on tasks.md write size.** After the §4.0a Step 1 Seed Write (Inventory placeholder, <1KB), the only legal mutation of `tasks.md` is **Edit-append** per the section-batched contract above. A single Write replacing the whole `tasks.md` is **forbidden** regardless of size. A single Edit-append payload >30KB is also forbidden — split into per-section Edit-appends even when consecutive Edits would total >30KB combined. Rationale: a single 96KB Write of tasks.md emits ~40K output tokens in one turn = ~360s inference latency = ~20% of total session in one tool call. Section-batched Edit-appends spread that cost across ~7 turns of ~50s each, recovers reviewability, and matches the recovery contract (re-Read + resume from next un-applied T-entry).

**Recovery on interruption:** re-Read `tasks.md`, scan for next un-applied T-entry (the audit trail in TaskUpdate identifies it), resume from there. No sidecar checkpoint file.

This contract mirrors Phase 3's per-section JSON-write contract (see [implementation.md § Per-plugin execution](implementation.md)).

### 4.1 Task ordering

Always in this order: stages → tasks → conditions → SLA.

The task **title IS the action description** — do not add a redundant `what` or `type` field. Absorb type into the title (e.g., `Add api-workflow task "..."` not `Add task` + `type: api-workflow`).

### 4.2 Create case file (T01)

Title format: `Create case file "<name>"`

Consult [`plugins/case/planning.md`](plugins/case/planning.md) for required fields (name, file path, case-identifier, identifier-type, case-app-enabled, description). Source all fields from sdd.md.

When `identifier-type: external`, `case-identifier` carries the sdd.md expression verbatim (`=vars.<varId>` or `=js:…`); any `=vars.<varId>` it references must be a variable declared in §4.2.1 (an **In** argument or **Variable**). See [`plugins/case/planning.md` § External identifier value](plugins/case/planning.md).

### 4.2.1 Declare global variables and arguments

Title format: `Declare <category> "<name>"` where category is `In argument`, `Out argument`, or `variable`.

One T-entry per variable or argument from the sdd.md "Case Variables" table. Place these after the case file (T01) and **all** trigger T-entries (T02+) — i.e., after the last trigger row, before stages. In multi-trigger cases the variables block starts at `T0<last-trigger>+1`, not at `T03`. Consult [`plugins/variables/global-vars/planning.md`](plugins/variables/global-vars/planning.md) for the SDD-to-category mapping rules and entry format.

### 4.3 Configure trigger(s) (T02+)

Title format: `Configure <trigger-type> trigger "<name>"`

Consult the corresponding trigger plugin (`plugins/triggers/<type>/planning.md`) for required fields.

**One T-entry per trigger row in sdd.md.** A case with N entry-point rows in its triggers table emits N trigger T-entries (T02, T03, …) — even when several rows would resolve to `<UNRESOLVED>` because the IS connection isn't provisioned. Per §4.0, "value can't be resolved yet" is not a reason to omit a row; it's a reason to mark `<UNRESOLVED: …>` and continue. Regardless of how many triggers a case has, no per-trigger edge is created (Rule 20; §4.5) — the case starts at the first stage's `case-entered` entry condition whenever any trigger fires.

Each trigger row uses its plugin's full field set — see `plugins/triggers/<type>/planning.md` for the per-type entry format. Worked example — sdd.md declares 3 entry-point rows (one manual + two events), one of which is unresolved:

```markdown
## T02: Configure manual trigger "Operator Starts Case"
- display-name: "Operator Starts Case"
- description: "Operator kicks off a case from the portal"
- order: after T01
- verify: Confirm node appended; capture TriggerId

## T03: Configure event trigger "New Inbound Email"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: uipath-microsoft-office-365-outlook
- object-name: Email
- event-operation: created
- event-mode: webhooks
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- order: after T02
- verify: Confirm trigger configured with correct event parameters

## T04: Configure event trigger "Jira Issue Created"
- type-id: <UNRESOLVED: no IS connection for uipath-atlassian-jira>
- connection-id: <UNRESOLVED>
- connector-key: <UNRESOLVED>
- object-name: <UNRESOLVED>
- event-operation: <UNRESOLVED>
- event-mode: <UNRESOLVED>
- order: after T03
- verify: trigger skipped at execution; user attaches after registering connection
```

Do **not** collapse the unresolved trigger into a note on T02 or omit it entirely — execution behavior for unresolved event triggers is documented in [`triggers/event/planning.md § Unresolved Fallback`](plugins/triggers/event/planning.md#unresolved-fallback), but the planning row is still required.

### 4.4 Create stages

Title format: `Create stage "<name>"` or `Create secondary stage "<name>"`

One task per stage. Consult [`plugins/stages/planning.md`](plugins/stages/planning.md) for required fields and the `stage` vs `secondary` decision. Basic properties only — SLA and escalation come later (§4.7).

Every stage T-entry includes `rationale:` copied from the SDD. It must explain the stage-kind decision and routing shape, especially when one interrupting secondary-stage entry handles a global event.

### 4.5 Edges — not authored (RETIRED)

The skill does not author edges (Rule 20). Emit no edge T-entries. Stage transitions derive entirely from stage entry/exit conditions (§4.7); `caseplan.json.edges` stays `[]`; case start is the first stage's `case-entered` entry condition. Reachability is condition-driven: every stage needs an entry condition naming a reachable producer (the first stage carries `case-entered`); orphan/unreachable stages are design defects owned by the planner's design lane and surfaced by skeleton/full `validate`.

### 4.6 Add tasks

Title format: `Add <type> task "<name>" to "<stage>"`

One task per task from the sdd.md — do NOT group multiple tasks under a single T-number. Read both the task-type plugin (`plugins/tasks/<type>/planning.md`) and the shared I/O-binding plugin (`plugins/variables/io-binding/planning.md`) before writing the entry. The task plugin owns resource-specific fields; the I/O-binding plugin is the single source of truth for the common output-row grammar.

Every task entry includes at least:

- **taskTypeId** — resolved from the registry in Step 3
- **rationale** — copied from the SDD; explains the task-type and activation/sequencing choice
- **activation-mode** — required on every task. One of `sequential`, `parallel`, `parallel-after-predecessor`, `event-triggered`, `adhoc`, `fan-in`, or `conditional-gate`. This is the user-visible task mode decision, not layout state.
- **entry-rule** — required on every task; mirrors the planned task-entry condition rule. Sequential tasks MUST say `runs-sequentially`, event-triggered tasks normally say `wait-for-connector`, adhoc tasks say `adhoc`, parallel stage-start tasks say `current-stage-entered`, parallel siblings after an immediate predecessor say `runs-sequentially`, and fan-in / non-immediate gates say `selected-tasks-completed`.
- **inputs** / **outputs** — see [bindings-and-expressions.md](bindings-and-expressions.md) for the two input modes (literal/expression and cross-task reference)
- **runOnlyOnce** — from sdd.md (default `false` if not specified). Design-lane-generated SDDs should always state `Run Only Once: Yes/No`; when a user-authored SDD omits it, use the frontend/default-new-task behavior (`false`) and do not infer `true` from task type.
- **isRequired** — from sdd.md (default `true` if not specified)
- **order** — authoring order in `tasks.md` (`after T05`, etc.). It is not allowed to carry execution semantics by itself; execution is carried by `activation-mode` + `entry-rule`.
- **lane** — integer task-set index, default increments per task within the stage starting at 0 for structural/layout compatibility. Lane does not express sequencing by itself; it controls the inner `data.tasks[lane][]` grouping only after `activation-mode` and `entry-rule` are decided. For a strict sequential chain, use consecutive single-task lanes (`[[A], [B], [C]]`) and never reuse a lane. Reuse the same lane only for tasks intentionally modeled as parallel siblings (`activation-mode: parallel`, `entry-rule: current-stage-entered`, same lane, and rationale says why they run together as `[[A, B], [C]]`).
- **verify** — what the execution phase should check after running

Additional fields are plugin-specific; read the plugin's `planning.md` before filling the entry.

> **Activation-mode audit before writing §4.7.** After §4.6 is drafted and before any condition T-entry is written, scan every stage's task list and make the task mode visible in the plan:
>
> **Authority order:** an explicit rule in the supplied/approved SDD wins. This audit verifies the handoff; it does not redesign or normalize authored rules. Use the derivation bullets below only when authoring from source behavior that has no explicit task-entry rule.
>
> - Contiguous ordered work in one stage (`then`, `after`, `before`, `in order`, direct previous-step wording, or an upstream prerequisite) → every task in that ordered run gets `activation-mode: sequential` and `entry-rule: runs-sequentially`, including the first task, unless the SDD explicitly declares another legal rule.
> - Independent work that starts with the stage → `activation-mode: parallel`, `entry-rule: current-stage-entered`, and rationale says why the tasks are independent.
> - Connector/event callback wait → `activation-mode: event-triggered`, usually `entry-rule: wait-for-connector`.
> - User-launched optional work → `activation-mode: adhoc`, `entry-rule: adhoc`, `isRequired: false`.
> - Branch convergence, fan-in, decision-result routing, or a non-immediate dependency → `activation-mode: fan-in` or `conditional-gate`, `entry-rule: selected-tasks-completed`, with the selected tasks named.
>
> While authoring a new SDD, do not invent `selected-tasks-completed` merely because a task follows the immediately previous task; model a plain contiguous run as `runs-sequentially`. Once an SDD is supplied or approved, preserve each explicit `selected-tasks-completed` row and selector only after confirming every selected task is a non-adhoc sibling in the same stage. Stop and repair an invalid selector before writing `tasks.md` or `caseplan.json`; SDD approval never overrides this Critical Rule. Map a valid selected-task gate to `conditional-gate` or `fan-in` as its authored rationale supports, never to `sequential`.
> Before leaving §4.6, audit each stage's planned lanes: sequential tasks that form a strict chain MUST NOT share a lane with each other or with adhoc/event-driven/parallel work. If `activation-mode`/`entry-rule` conflicts with `lane`, the mode wins and the lane must be corrected. Same-lane grouping is reserved for intentionally parallel siblings, and the rationale must say why they run in parallel.

> **Outputs are a lossless handoff, not a discovered-name summary.** Project each SDD Outputs table row through the common grammar in [`plugins/variables/io-binding/planning.md` § SDD Outputs table → `tasks.md` projection](plugins/variables/io-binding/planning.md#sdd-outputs-table-to-tasksmd-projection-mandatory), then preserve the resulting list item exactly. Schema discovery may add truly undeclared fields as bare items, but it must not rewrite an SDD row. An explicit equal-name extract such as `greeting -> greeting` stays exactly that; collapsing it to bare `greeting` changes the binding from "write the existing case variable" to "auto-mint a task output." Before the Step 5 approval gate, compare every SDD Outputs row to its task T-entry and fix any missing or changed operator/operand or leaked table placeholder.

> **Registry handoff:** For a resolved `action` or `case-management` T-entry, translate the selected audit object into the canonical `tasks.md` labels and values:
>
> | Task type | `name` from | `folder-path` from | `taskTypeId` from |
> |---|---|---|---|
> | `action` | `selected.deploymentTitle` | `selected.deploymentFolder.fullyQualifiedName` | `selected.id` |
> | `case-management` | `selected.name` | `selected.folders[0].fullyQualifiedName` | `selected.entityKey` |
>
> Before Step 5, confirm these labels and values match the `selected` object in `registry-resolved.json`.

> **No shell commands in task entries.** Each task is a declarative specification. Never write `uip` invocations or any other shell commands inside a task body — the execution phase translates specs into JSON mutations.

> **Record `lane: <n>` per task only when required by the artifact contract.** It is structural/layout state, not a sequencing control. For sequential tasks, preserve their order in `data.tasks`, write `activation-mode: sequential`, put each strict-chain task in its own consecutive lane, and add the `runs-sequentially` entry condition to each task.

> **Placeholder shape for unresolved resources.** If `taskTypeId` / `typeId` / `connectionId` is `<UNRESOLVED: …>`, omit `inputs:` and `outputs:` entirely and capture wiring intent in a trailing comment block. Execution creates a bare task node — structural only. See [placeholder-tasks.md](placeholder-tasks.md) for the full pattern and upgrade path.

### 4.7 Configure conditions

One task per condition. Order within §4.7: stage entry → stage exit → case exit → task entry.

Title format: `Add <scope> condition for "<target>"`

For per-scope fields, consult the corresponding condition plugin:
- `plugins/conditions/stage-entry-conditions/planning.md`
- `plugins/conditions/stage-exit-conditions/planning.md`
- `plugins/conditions/task-entry-conditions/planning.md`
- `plugins/conditions/case-exit-conditions/planning.md`

Every condition T-entry includes `rationale:` copied from the SDD choice it implements. For global events, state why one interrupting secondary-stage entry replaces per-primary-stage exits/tasks.

### 4.8 Set SLA and escalation rules

SLA comes last. Consult [`plugins/sla/planning.md`](plugins/sla/planning.md) for the three sub-operations (default SLA, conditional SLA rules, escalation rules) and per-target ordering. Root rules target `metadata.slaRules[]`; stage rules target that stage's `data.slaRules[]`. Every SLA/escalation T-entry includes `rationale:` copied from the SDD's case/stage SLA rationale.

### 4.9 Not Covered section

Add a brief section at the end of `tasks.md` listing things referenced in sdd.md but outside the scope of `caseplan.json` (e.g., Data Fabric entity schemas). These stay as notes for the user.

---

## Step 5 — Finalize tasks.md (auto-proceed to Phase 2)

Treat the generated `tasks.md` as approved and proceed directly to Phase 2 by default — no AskUserQuestion approval prompt, no wait for sign-off.

**Stop-after-plan exception (the virtual gate).** When the request explicitly scoped the work to planning only (e.g. "just build tasks.md", "Phase 1 only", "stop after the plan for review", "don't build the case yet"), stop here: report the finished plan and do NOT create a solution or caseplan. This is the only condition that halts the auto-proceed.

Re-read `tasks.md` before proceeding to Phase 2 (see [implementation.md](implementation.md)); context may have compacted during planning. `tasks.md` is complete handoff artifact — all resolved IDs, inputs, outputs, and references captured there.

**Plan-shape gate.** Before Phase 2, re-read every §4.6 task T-entry itself (not the §4.7 condition entries) and confirm it literally contains its own `- activation-mode:` line and its own `- entry-rule:` line — **exactly one of each, colocated on the task's own T-entry** — and that the pair is legal for that mode. Re-run the §4.6 Activation-mode audit over the finished plan, covering all six modes, not just `sequential`.

**Known failure pattern:** deferring the rule to a *separate* §4.7 task-entry-condition entry (`rule-type:`) does not satisfy this gate — `caseplan.json` can end up fully correct while `tasks.md` itself still fails this check, because §4.6 and §4.7 are graded as separate artifacts. See [task-entry-conditions/planning.md § Phase 1 Plan Presentation Contract](plugins/conditions/task-entry-conditions/planning.md#phase-1-plan-presentation-contract) for the compliant §4.6 shape.

Correct the plan before building; validation of `caseplan.json` cannot detect a malformed Phase 1 handoff.

<!-- END: planning.md -->
