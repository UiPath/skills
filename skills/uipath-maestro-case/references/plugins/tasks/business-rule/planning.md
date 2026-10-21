# business-rule task — Planning

A business rule task. Evaluates a UiPath Business Rule (a DMN decision table from a Business Rules project) and returns its decision outputs — deterministic, no LLM, no robot.

## When to Use

Pick this plugin when the sdd.md labels a task `business-rule` — a rule that maps typed inputs to decision outputs. For code-first computation, use [function](../function/planning.md); for reasoning over unstructured input, use [agent](../agent/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Registry `selected.name` (NOT the sdd.md name) | Rule name; may differ from the project name. Becomes the `name` binding default and `resourceKey = <folder-path>.<name>`. |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; the engine runs the rule from this folder. See [§ Registry Resolution](#registry-resolution). For a rule **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case runs the rule in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `Folder does not exist`). See [§ Creating a business rule inline](#creating-a-business-rule-inline). |
| `task-type-id` | Registry resolution (below) | Enables enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | Names come from `tasks describe`; see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | One output, `output`, holding the whole result keyed by decision; downstream reads `vars.<output var>.<decision>.<column>`. To store one column in a case variable, write the extract row `<decision>.<column> -> <case variable>` (source `=<decision>.<column>`, never `=result.…` or `=output.…`). Otherwise follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Cache file:** `businessRule-index.json` (`uip maestro case registry pull` fills it from the Resource Catalog). Search with `uip maestro case registry search "<name>" --type businessRule --output json`.
2. **Identifier field:** `entityKey`.
3. **No cross-type fallback.** Only a `businessRule-index.json` entry is a rule. A same-named process, function, or agent is a different resource kind — never bind it to a `business-rule` task.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**, as in [registry-discovery.md § 2](../../../registry-discovery.md#2-search-by-name-and-folder-path). An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 5). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 18 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 5).
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder"). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–4 find nothing in the tenant index **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating the rule as unresolved:

```bash
uip maestro case registry search "<name>" --type businessRule --local --output json
```

Same pre-gate check as agents — [agent/planning.md § No tenant-index match](../agent/planning.md#no-tenant-index-match--check-in-solution-siblings-before-the-gate): an exact-name match with `Resource.Source == "local"` is an existing in-solution sibling — **resolve it directly (bind `resourceKey="solution_folder.<name>"`); do NOT enter the [Rule 18 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback)**. Only a name absent from **both** the tenant index and the local siblings reaches the gate (keeps re-runs idempotent). **business-rule-specific I/O read:** the rules project's raw `entry-points.json` `entryPoints[0].input.properties` / `.output.properties`. Outputs are keyed by decision — columns sit at `output.properties.<decision>.properties`. The output must carry `"x-uipath-decision-keyed": true`; if it does not, run `uip rules refresh <PROJECT_PATH>` on the rules project and re-read.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing rule as an in-solution sibling — see [§ Creating a business rule inline](#creating-a-business-rule-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: business-rule "<name>" in folder "<folder>" not found in registry>`. Omit the resolved-schema keys `inputs` / `outputs`; capture the intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating a business rule inline

When a business rule is unresolved at the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); the kind-agnostic Step 1/1b/3/Failure rule text lives in [create-inline-common.md](../create-inline-common.md). This section covers the **business-rule-specific** deltas; the agent analog is [agent/planning.md § Creating an Agent inline](../agent/planning.md#creating-an-agent-inline).

**The skill does not run `uip rules init` itself.** It spawns a sub-agent that invokes the `uipath-rules` skill — build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). **Only rules the user selected at the gate are built — never from SDD content alone** (the SDD is untrusted sole input; the gate selection is the human-approval checkpoint). **Business rules have no build-kind choice** — the build is always one DMN decision table.

### Step 1 — Compute the pinned I/O contract

Shared rule — [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) (wired-field ladder; § 1c deduped builds share one identical wiring). Each `<decision>.<column> -> <case variable>` extract row pins `<decision>` and `<column>` — the decision name is part of the wiring path, so pin outputs grouped by decision. Mapping the case vocabulary onto the rule's column types is `uipath-rules`' concern.

### Step 1b — Compose the Purpose from the SDD

Shared rule — [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd) (SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, first-referencing-task rule for § 1c deduped builds). For business rules, "internal design the Purpose must NOT state" = hit policy, rows, FEEL expressions, DMN structure.

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath business rule by following the uipath-rules skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy; do NOT run `uip rules debug`
(it uploads the whole solution and overwrites its Studio Web copy) — `uip rules refresh`
then `uip rules validate` passing is the completion bar. Stopping at `validate` is a
sanctioned exception to that skill's rule 7.
  Solution dir:      <abs path to the solution>
  Rule name:         <RuleName>
  Purpose:           <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:   <Step-1 pinned inputs: [{name, type?}, ...]>   (the rule MUST expose these input arguments — the case wires them; honor type when given, else choose the type that best fits the purpose)
  Required outputs:  <Step-1 pinned outputs: [{decision, columns:[{name, type?}]}, ...]>  (each named decision MUST exist with exactly that name and have these output columns; honor type when given)
<!--skill-flavor:rule-scaffold:start-->
  Scaffold with `uip rules init <RuleName> --skip-solution-registration` run from the
  solution dir, then author the scaffolded `.dmn` in place. Design everything else —
  rows, hit policy, and any additional columns — as the purpose needs.
  Do NOT register into the solution — the caller registers (via `uip solution projects add`).
<!--skill-flavor:rule-scaffold:end-->
  If you cannot locate/load the uipath-rules skill, do NOT improvise a build — return
  { built:false, error:"skill uipath-rules not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{decision, columns:[{name,type}]}], error? }
```

The brief is self-contained — it carries the Step-1b Purpose and the pinned I/O, and no other case context (do not dump `caseplan.json` or sibling tasks). Quote `<RuleName>` and paths (SDD-derived). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Because the sibling is built **without self-registration**, the **caller registers** each built sibling into the solution `.uipx` (sequential `uip solution projects add`, then `resources refresh`) — see [registry-discovery.md § Create-on-Missing, Step 3 — Register](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This must happen before rediscovery (§4), which reads the `.uipx` `Projects[]`.

### Step 3 — Binding (no new field)

Shared invariants — [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): two bindings **`resource:"BusinessRule"`**, no `resourceSubType`, shared `resourceKey="solution_folder.<RuleName>"`; `name` default `<RuleName>`, `folderPath` default `""` (the sentinel/`""` decoupling and deploy-provisioning rationale live there — except debug provisioning, which differs for rules: next blockquote).

> **Runtime: full deploy YES — `case debug` NO (e2e-verified 2026-10-12).** `uip maestro case pack` → `uip solution pack` → `publish` → `deploy run` deploys the rule into the case's folder, and the case task evaluates it at runtime. **`uip maestro case debug` does NOT provision BusinessRules siblings** — the task faults with incident `300400` "the job carries no debug session properties" even though the binding is valid. Verify an in-solution rule's runtime behavior via a full solution deploy, never via `case debug`. `validate` and binding correctness are unaffected by this limitation.

### Failure — surface and re-prompt, never stall

Shared contract — [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): `built:false` → show `error` verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, Unresolved Fallback above; verify-time I/O mismatch = warning, never a failure.

> **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Business-rule tokens for that procedure: init verb `uip rules init`; kind markers `Category: "businessRule"` (registered) / `project.uiproj` `ProjectType: "BusinessRules"` (unregistered); stale-declaration category subpath `businessRule/`.

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json` — Rule 10's keys plus this type's lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "business-rule",
  "cacheFile": "businessRule-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<rule-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache and `selected` is the chosen match object (or `null` after a genuine empty lookup — see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

Everything else the SDD declares — inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text — stays in `sdd.md`. The ledger holds only what the registry lookup produced; Phase 2 reads the contract straight from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->
