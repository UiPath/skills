# Phase 1 — Resolution: sdd.md → registry-resolved.json

Resolve every resource named by `sdd.md` into tenant identities in `tasks/registry-resolved.json`. The SDD remains the plan; add only task type IDs, connection IDs, folder paths, and recipient identities. Phases 2–7 read the SDD and ledger and derive `caseplan.case` with `sdd convert`. See [implementation.md](implementation.md) and [phased-execution.md](phased-execution.md).

> **No intermediate plan.** The SDD is the plan. Do not author `tasks.md`, a T-numbered task list, or another SDD restatement. Step 12 walks the SDD against the artifact and closes with `validate --strict` ([implementation.md](implementation.md)).
>
> **Existing case:** targeted edits to `caseplan.case` skip this pipeline; see [brownfield.md](brownfield.md).
>
> **Output:** write `tasks/registry-resolved.json` beside `sdd.md`; with SLA escalations also write `tasks/recipients-resolved.json` (see [`plugins/sla/planning.md` § Identity Resolution](plugins/sla/planning.md#identity-resolution)). `tasks/` is adjacent to `sdd.md`, never inside the solution/project.
>
> **Exit:** auto-proceed to Phase 2; stop after resolution only when explicitly requested.
>
> **Plugin detail:** read root case → `plugins/case/planning.md`; stages → `plugins/stages/planning.md`; tasks → `plugins/tasks/<type>/planning.md`; triggers → `plugins/triggers/<type>/planning.md`; conditions → `plugins/conditions/<scope>/planning.md`; SLA → `plugins/sla/planning.md`; global variables/arguments → `plugins/variables/global-vars/planning.md`; task I/O → `plugins/variables/io-binding/planning.md` (**always read alongside the matching task plugin**). Each `planning.md` defines SDD fields and resolution; sibling `impl-json.md` maps results to `caseplan.case` JSON.
>
> **Kickoff overview first (if not already shown).** If handoff did not run because the user supplied `sdd.md`, present the greenfield flow overview once before Step 0; see [SKILL.md § Kickoff — set dev expectations](../SKILL.md#kickoff--set-dev-expectations-first). Skip if the delegation window showed it.

## Step 0 — Resolve the `uip` binary

Resolve `uip`, capture its version, and upgrade only when installed `@uipath/cli` is **older** than the latest published version; leave newer dev builds alone. If absent, stop and ask the user to run the official installer; never auto-run one.

```bash
UIP=$(command -v uip 2>/dev/null || true)
if [ -z "$UIP" ] && command -v npm >/dev/null 2>&1; then
  UIP="$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip"
fi
if [ -z "$UIP" ] || [ ! -x "$UIP" ]; then
  echo "UiPath CLI not found. Ask the user to run the official installer, then rerun this step with PATH updated:" >&2
  echo "  curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash" >&2
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

Use `$UIP` thereafter when plain `uip` is unavailable. On Windows PowerShell, ask the user to run `irm https://download.uipath.com/uipath-cli/install.ps1 | iex`. If `npm install -g` fails for permissions, prompt for appropriate privileges (for example, `sudo npm install -g @uipath/cli@latest`); do not retry automatically.

## Step 1 — HARD GATE: check login and pull registry

Login is required before registry discovery on every Phase 1 build run, including SDD-without-ledger and staged-ledger runs, except the same-session fast path and Design-only exception. If the planner subagent report (SKILL.md Rule 16) says `registry pull` succeeded **in this session**, reuse machine-global `~/.uip/case-resources/` and run verify-only: persist its resolution ledger verbatim to `tasks/registry-resolved.json`, spot-verify the cache, execute recorded `gateDecision`s (Rule 18), and re-resolve only stale/missing entries. Any doubt (user SDD, cross-session resume, compaction, failed/never-run design-lane pull, or missing cache files) requires the full gate.

**Design-only exception:** when explicitly asked to stop at design and not create `caseplan.case`, do not run login, registry, connection, schema, or user-discovery commands. Deliver only `sdd.md`, leave tenant identities `<UNRESOLVED>`, state that the later build must run this gate, and do not author a substitute plan.

**Negative trigger — tenant work overrides it.** The exception defers tenant lookup; it does not describe where a run stops. It does NOT fire when the same request asks to resolve resources or identities, pull or refresh the registry, replace a stale registry audit, or produce `tasks/registry-resolved.json` / `tasks/recipients-resolved.json` — even when that request also says to stop before `caseplan.case`, a solution, or Phase 2. Such a run is a normal resolution run: run this gate in full, resolve every identity, write the ledger, and stop before Phase 2.

```bash
<!--skill-flavor:planning-login-command:start-->
uip login status --output json
<!--skill-flavor:planning-login-command:end-->
uip maestro case registry pull
```

Outside the fast path, do not inspect `~/.uip/case-resources/` first to decide whether the pull is necessary: cache absence is exactly why the pull must run. Do not continue or write `registry-resolved.json` unless pull succeeds. If not logged in, prompt login and stop Phase 1; if pull fails, surface its error and stop. Exit 0 with `Warning` is partial: read `Data.Errors[]`. A 5xx `typecache-*` row routes its indexed elements to [connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx); do not re-run pull. A 401/403 `typecache-*` row is login/permission failure: surface and stop. Other rows mean indexes were not pulled; `sdd resolve` reports them in `Data.Scope.missingIndexes` and, when recorded, `Data.Scope.unavailableIndexes`. After successful pull, read [registry-discovery.md](registry-discovery.md) before the first cache lookup. Pull caches resources at `~/.uip/case-resources/`; later searches are local.

## Step 2 — Locate and parse the design document

Accept the user's `sdd.md` path or ask for it. If its directory has multiple `.md` files, use **AskUserQuestion** with candidates plus "Something else".

If the path has no `sdd.md`, the skill hands design to the `uipath-planner` Case Design Lane before this step (SKILL.md Rule 16 + § Design handoff). Phase 1 starts after Case Review's Build answer and lane-written `sdd.md`; use the in-memory model that rendered it directly (Rule 2), not a re-read. Case Review is approval context, not a parsing source.

`sdd.md` is the sole required input and describes stages, tasks, conditions, SLA, component types, persona information, and registry search keys. Portable name is type-specific: `Resolved Resource` for process/agent/rpa/api-workflow/function/business-rule, Action App title in `HITL Implementation` for action, and `Child Case` for case-management. `Resource Identity` or `Action App ID` states whether it was previously resolved. The SDD has no edges; transitions are stage entry/exit conditions (Rule 21). Trust it as written; do not validate or gap-fill it.

> **Cache-state distinction — mandatory.** Step 1 refreshes discovery state but does not validate/override the SDD. Before a successful pull, absent cache/index is a failed refresh precondition, not evidence of unavailability. After pull, search the SDD's concrete portable name; only an empty exact-name set or still-absent index is a genuine empty lookup. `<UNRESOLVED>` identity/folder means name-only discovery, not permission to skip it.
>
> **Design-lane carryover.** `tasks/registry-resolved.json` is an optional performance cache/audit artifact, never resource intent. In the same session, seed it verbatim from the planner ledger (Rule 10); Step 1 still runs first. Associate entries by exact `stage` + `task`; reuse only if: (1) `taskType` matches; (2) `cacheFile` is compatible under [registry-discovery.md](registry-discovery.md), with `action` and `case-management` requiring their primary cache exactly; (3) `searchQuery` and selected canonical name equal the type-specific portable name; and (4) concrete SDD identity and folder equal selected identity and exact folder.
>
> Canonical selected fields: action uses `deploymentTitle` / `deploymentFolder.fullyQualifiedName` / `id`; other non-connectors use `name` / `folders[0].fullyQualifiedName` / `entityKey`. Normalize labeled identities (for example, `agentId <uuid> (v1.0.6)`): ID token must equal `entityKey`, and SDD version must equal selected version metadata (for example, `customData.ProcessVersion`) when present. Missing, `<UNRESOLVED>`, or mismatched fields make the entry stale: ignore it, rediscover from the SDD, and replace its audit entry. Never let cache upgrade or override unresolved/edited SDD fields. If absent, rediscover each portable name and write a fresh file. This applies to portable-resource task types; connector resolution remains [connector-integration.md](connector-integration.md).

## Step 3 — Resolve resources

Seed TodoWrite before resolution; mark each item `in_progress` on entry and `completed` on exit, one item per class, never per SDD row:

1. Resolve task resources (registry lookups — this Step 3).
2. Resolve trigger resources (connector key, connection, activity type).
3. Resolve connector-bound condition resources.
4. Resolve SLA escalation recipients (`recipients-resolved.json`).
5. Complete `registry-resolved.json` (Step 4 additions), then auto-proceed to Phase 2 (Step 5).

For every task, trigger, and condition in the sdd.md:

If the design-only exception is active — per Step 1, including its negative trigger, and not merely because the request stops before `caseplan.case` — skip registry and schema discovery in this step and do not fan out through every plugin `planning.md`. The SDD already carries the design; leave its tenant identities `<UNRESOLVED>`, report which resources the later build run must resolve, and stop. Do not write a plan file in its place.

End the response with suggested next steps: review the SDD, then run a build to resolve tenant resources and create `caseplan.case`.

Otherwise, continue with the normal resolution path:

1. Match each SDD component to the catalogs in §§3.1–3.3.
2. Group by plugin type and read each `planning.md` once, resolving/emitting every component from that read. Re-reading per element is a read-budget defect (observed `planning.md` 10–16× and `impl-json.md` up to 26× per build); after compaction reread only the plugin for the section in progress.
3. Resolve all tasks in one call: `uip maestro case sdd resolve "<SDD_PATH>" --out tasks/registry-resolved.json --output json` (SKILL.md Rule 3), from the solution directory when present so in-solution siblings are found ([registry-discovery.md § Resolve with the CLI first](registry-discovery.md#resolve-with-the-cli-first)). It reads each type-specific portable name, searches its index, narrows by folder, and writes the whole Rule 10 ledger. `Data.Counts` reports selected count; `Data.Unresolved[]` reports the rest. Missing/`<UNRESOLVED>` portable name violates the SDD contract and must be surfaced; never fall back to `Task Name`.
4. Work only `Data.Unresolved[]` manually under [registry-discovery.md](registry-discovery.md) and the plugin Registry Resolution section. `absent` runs cross-type fallback and in-solution sibling check unless `Data.Scope.siblingsChecked: true`, before Rule 18 gate; `ambiguous` follows match priority. Never re-search selected tasks or rewrite their entries.

### 3.1 Task Type catalog

> **Closed enum — 17 values.** SDD `Type:` and caseplan.case `type` use column-1 schema-kebab values; column 2 is the planning/execution plugin folder, not JSON. See SKILL.md Rule 17 and Plugin Index naming-asymmetry note. Any other value (`connector-activity`, `wait-for-event`, etc.) is invalid; write `<UNRESOLVED>`.

| sdd.md `Type:` / caseplan.case `type` | Plugin folder |
|---|---|
| `process` (covers `AGENTIC_PROCESS` legacy label) | `plugins/tasks/process/` |
| `agent` | `plugins/tasks/agent/` |
| `rpa` | `plugins/tasks/rpa/` |
| `action` | `plugins/tasks/action/` |
| `api-workflow` | `plugins/tasks/api-workflow/` |
| `function` | `plugins/tasks/function/` |
| `business-rule` | `plugins/tasks/business-rule/` |
| `case-management` | `plugins/tasks/case-management/` |
| `execute-connector-activity` | `plugins/tasks/connector-activity/` |
| `flow-process` | `plugins/tasks/flow-process/` |
| `http-request` | `plugins/tasks/http-request/` |
| `document-extraction` | `plugins/tasks/document-extraction/` |
| `script` | `plugins/tasks/script/` |
| `wait-for-connector` | `plugins/tasks/connector-trigger/` |
| `external-agent` | `plugins/tasks/connector-activity/` (External agents and automations) |
| `external-workflow` | `plugins/tasks/connector-activity/` (External agents and automations) |
| `wait-for-timer` | `plugins/tasks/wait-for-timer/` |

> **Create-on-missing:** `agent`, `api-workflow`, and `business-rule` may be built inline at Rule 18; see [§ 3.4](#34-unresolved-resources), [agent](plugins/tasks/agent/planning.md#creating-an-agent-inline), [api-workflow](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline), and [business-rule](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline). All others, including regular RPA `process`, action, function, connectors, and agentic process, use §3.4 placeholder flow.

### 3.2 Trigger Type catalog (case-level)

| sdd.md description | Plugin |
|---|---|
| "Start manually" / "User initiates" | `plugins/triggers/manual/` |
| "Every N hours/days" / scheduled / cron-like | `plugins/triggers/timer/` |
| Event from external system (connector-based) | `plugins/triggers/event/` |

### 3.3 Condition Scope catalog

| Where condition attaches | Plugin |
|---|---|
| On stage entry | `plugins/conditions/stage-entry-conditions/` |
| On stage exit | `plugins/conditions/stage-exit-conditions/` |
| On task entry | `plugins/conditions/task-entry-conditions/` |
| On case exit | `plugins/conditions/case-exit-conditions/` |

> **Connector-bound conditions.** Any scope may have a `wait-for-connector` WHEN rule binding an Integration Service connector event. Use the same pipeline as task-class `wait-for-connector` (TypeCache + `case spec --type trigger` + reference-resolution). Collect from the SDD, in the condition's `registry-resolved.json` entry, `type-id`, `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`, optional `outputs`, plus `display-name`, `rule-type`, and `condition-expression`. See [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule) and each scope plugin's `planning.md`.

### 3.4 Unresolved resources

When registry resolution and cache matching fail, or a connection is missing, do not fabricate a placeholder or mock.

> **Connector catalog unavailable — no gate, no create offer.** Elements of a `typecache-*` index listed in `Data.Errors` with 5xx go directly to step 1 below with reason `connector catalog unavailable (TypeCache <status>)`; see [connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx) for served elements.
>
> **Missing connection — offer to create first.** A missing/empty IS connection is not immediately "unresolved". The connector pipeline offers to create one via `uip is connections create` ([connector-integration.md § Step 2](connector-integration.md), [connector-trigger-planning.md § Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)). Only after the user **declines** or creation fails does the connection become `<UNRESOLVED>` and fall through to the steps below.

> **Missing agent, API workflow, or business rule — offer to create first.** A missing `agent` (no `agent-index.json` match), `api-workflow` (no `api-index.json` match), or `business-rule` (no `businessRule-index.json` match) is not immediately "unresolved". At the Rule 18 empty-lookup gate the skill offers to build it as an in-solution sibling — it spawns a sub-agent that invokes `uipath-agents` (agent) / `uipath-api-workflow` (API workflow) / `uipath-rules` (business rule), then rediscovers + binds via `registry --local` ([registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery); specifics in [agent/planning.md § Creating an Agent inline](plugins/tasks/agent/planning.md#creating-an-agent-inline) / [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline) / [business-rule/planning.md § Creating a business rule inline](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline)). Only after the user **declines**/skips, the build fails, or the CLI lacks `registry --local` does it become `<UNRESOLVED>` and fall through to the steps below. Other kinds (regular RPA process, action, case-management, connectors, agentic process) have no inline-create path — they fall straight through.

Otherwise:

1. Record `<UNRESOLVED: <reason>>` in the entry's `taskTypeId` / `typeId` / `connectionId` slot in `registry-resolved.json`, and set `selected` to `null`.
2. Carry SDD input mapping into the entry's `wiringNotes` string array; Phase 2 has no schema to wire against and the completion report reads it. See [placeholder-tasks.md](placeholder-tasks.md).
3. Continue; do not halt. The SDD still supplies display name, required, and run-only-once, and Phase 2 still writes the task node and entry conditions.

At execution, unresolved tasks become **placeholder tasks** in `caseplan.case` (display-name + type only, no task-type-id or bindings). The graph remains reviewable; the user attaches resources and bindings externally before runtime. See [placeholder-tasks.md](placeholder-tasks.md).

## Step 4 — Complete `registry-resolved.json`

Step 3's `sdd resolve` already wrote `tasks/registry-resolved.json` (creating `tasks/`) with one entry per task under `resolved`, using Rule 10's exact keys: `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`. Do not rewrite it. This step only **adds**, with Edit, what resolve cannot know:

- one entry per case trigger and connector-bound condition from the connector pipeline;
- `gateDecision` for Rule 18 answers;
- each genuine miss's `<UNRESOLVED: <reason>>` identity-slot marker (SKILL.md Rule 10) and §3.4 `wiringNotes`.

`rationale` explains selection (for example, `"exact name match in caseManagement folder"`); never use it for verify-text, SDD/spec field translation, or downstream-plugin claims.

This ledger holds **only what registry lookups produced**. It is not a copy of the SDD: do not restate stage/task structure, activation modes, entry rules, inputs, outputs, or design rationale in it. Phase 2 and Phase 3 read those straight from `sdd.md`, which stays the single source of the design contract. Duplicating the contract here re-creates the drift the retired `tasks.md` caused.

Use the same section-batched write discipline the caseplan uses — one Read per section (tasks → triggers → conditions → SLA recipients), N Edit-appends, no re-Read between siblings. See [case-editing-operations.md](case-editing-operations.md).

> **Registry handoff labels.** Phase 2 reads resolved `action`/`case-management` identities from `selected`; nothing is copied:
>
> | Task type | `name` | `folder-path` | `taskTypeId` |
> |---|---|---|---|
> | `action` | `selected.name` | `selected.folder` | `selected.identifier` (`identifierField: "id"`) |
> | `case-management` | `selected.name` | `selected.folder` | `selected.identifier` (`identifierField: "entityKey"`) |
>
> A planner-lane ledger persisted verbatim (SKILL.md Rule 3) instead carries raw cache fields: action uses `selected.deploymentTitle`, `selected.deploymentFolder.fullyQualifiedName`, `selected.id`; case-management uses `selected.name`, `selected.folders[0].fullyQualifiedName`, `selected.entityKey`.

## Step 5 — Hand off to Phase 2 (auto-proceed)

Phase 1 completes when every SDD resource row has a ledger entry: resolved, `<UNRESOLVED: …>`, or created inline at Rule 18. Report resolved / created inline / unresolved counts and proceed directly to Phase 2—no AskUserQuestion approval or sign-off wait.

**Stop-before-build exception:** if explicitly scoped to design or resolution only (for example, "just the SDD", "resolve resources but don't build", or "don't build the case yet"), stop; report SDD and ledger and do not create a solution or `caseplan`. This is the only auto-proceed halt.

At Phase 2 entry, re-read `sdd.md` and `registry-resolved.json` because context may have compacted; see [implementation.md](implementation.md).

<!-- END: planning.md -->
