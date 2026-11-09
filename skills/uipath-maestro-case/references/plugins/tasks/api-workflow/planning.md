# api-workflow task — Planning

An API Workflow (formerly “Coded Workflow”) task invoking a UiPath API workflow by entityKey.

## When to Use

Use this plugin when sdd.md labels a task `API_WORKFLOW`, typically a TypeScript / C# coded workflow exposing an API-style interface.

## Required Fields from sdd.md

| Field | Source | Notes |
|---|---|---|
| `display-name` | Task `Task Name` | |
| `name` | Resolved registry entry `name` (not sdd.md `Resolved Resource`) | Binds to `data.name` and supplies `resourceKey` suffix `<folderPath>.<name>`. `Resolved Resource` only searches `folders[0].displayName`. Read the fetched entry’s `name` verbatim; it may be generic `"API Workflow"` or real (for example `"ContractOperationsApi"`). See [§ Registry Resolution](#registry-resolution). |
| `folder-path` | Resolved `folders[0].fullyQualifiedName` (not sdd.md `Folder`) | Binds to `data.folderPath`; Orchestrator starts here. `Folder` only seeds lookup and may be parent/truncated. For an inline in-solution sibling use empty `""` (co-located); keep `resourceKey` as `solution_folder.<name>` and never put the `solution_folder` sentinel in `folder-path` (`runtime folder not exist`). See [§ Creating an API workflow inline](#creating-an-api-workflow-inline). |
| `task-type-id` | Registry resolution | `entityKey` in `api-index.json` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md Outputs + resolved schema | Follow [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not task type. |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. Use `api-index.json` and identify entries by `entityKey`.
2. Match in order: exact name + exact folder > exact name with multiple folders (pick matching) > exact name only > **no match**. An exact-name entry in another folder, including an sdd.md-folder child, is exact-name-only: **resolve it**, bind `folder-path` to its full path, and do not treat the folder difference as no-match or enter Create. The sdd.md folder may be parent/truncated and only seeds lookup.
3. Take BOTH `name` and `folder-path` from the selected entry, never sdd.md: `folder-path` = `folders[0].fullyQualifiedName`; `name` = entry `name`, verbatim. Do not assume `"API Workflow"`; an incorrect value can pass `validate` but fault at `resources refresh` / `case debug` (`process "<name>" not found`). On no registry match, fall back to the sdd.md folder/name (Unresolved path).
4. Discover inputs/outputs via `tasks describe`; see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

**Skip this check when `sdd resolve` reported `Data.Scope.siblingsChecked: true`**—resolve already searched solution projects ([registry-discovery.md § Resolve with the CLI first](../../../registry-discovery.md#resolve-with-the-cli-first)). Otherwise, if steps 1–2 find nothing and the CLI supports `registry --local`, run:

```bash
uip maestro case registry search "<name>" --type api --local --output json
```

As in [agent/planning.md § No tenant-index match](../agent/planning.md#no-tenant-index-match--check-in-solution-siblings-before-the-gate), an exact-name `Resource.Source == "local"` match is an existing sibling: resolve it directly with `resourceKey="solution_folder.<name>"`; do NOT enter the [Rule 18 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback). Only a name absent from both tenant and local indexes reaches the gate. For sibling I/O, use this fallback chain and warn in the completion report whenever fallback is used: raw `entry-points.json` `entryPoints[0].input/.output.properties` (flat deploy shape) → `input.schema.document.properties` wrapper variant →, if entirely `null`, `Workflow.json` root input/output schema properties. No CLI verb syncs that file for a user-built sibling.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback), the user may choose **Create** to build a missing API workflow as an in-solution sibling; see [§ Creating an API workflow inline](#creating-an-api-workflow-inline). This fallback applies only when the user declines/skips Create, build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: api-workflow "<name>" in folder "<folder>" not found in api-index.json>`. Omit resolved-schema keys `inputs` / `outputs`; put intended wiring in the entry’s `wiringNotes` string array. Execution creates a placeholder task; see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an API workflow inline

At the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback), when the user selects **Create**, build an **in-solution sibling**. Cross-cutting capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, and rediscover/verify/bind are in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); kind-agnostic Step 1/1b/3/Failure rules are in [create-inline-common.md](../create-inline-common.md). API-specific deltas follow. The agent analog is [agent/planning.md § Creating an Agent inline](../agent/planning.md#creating-an-agent-inline).

Do not run `uip api-workflow init` yourself. Spawn a sub-agent invoking `uipath-api-workflow`; cross-skill invocation is allowed here, overriding the “never auto-invoke other skills” rule in `SKILL.md § Non-negotiable prohibitions`. Build only API workflows selected at the gate, never from SDD content alone. API workflows have no build-kind choice: always build JSON-DSL `Workflow.json`.

### Step 1 — Compute the pinned I/O contract

Apply [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract), including the wired-field ladder and § 1c deduped-build identity. Mapping case vocabulary to JSON-Schema I/O is `uipath-api-workflow`’s concern.

### Step 1b — Compose the Purpose from the SDD

Apply [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd): SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, and first-referencing-task rule for § 1c deduped builds. For API workflows, Purpose must not state activities, connectors, expressions, or DSL structure.

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath API workflow by following the uipath-api-workflow skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy; do NOT execute the workflow
(`uip api-workflow run` reaches real vendor systems when authenticated) — offline
`uip api-workflow validate` passing Status "Valid" is the completion bar.
  Solution dir:      <abs path to the solution>
  Workflow name:     <WorkflowName>
  Purpose:           <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:   <Step-1 pinned inputs: [{name, type?}, ...]>   (the workflow MUST expose these — the case wires them; honor type when given, else choose the type that best fits the purpose)
  Required outputs:  <Step-1 pinned outputs: [{name, type?}, ...]>  (the workflow MUST expose these; honor type when given)
  Scaffold with `uip api-workflow init <WorkflowName> --skip-solution-registration` run from
the solution dir (name is positional; registration status `OptedOut` is expected, not an
error), then author the generated `Workflow.json` in place.
  Declare the pinned I/O consistently in BOTH files: the `Workflow.json` root input/output
schemas AND `entry-points.json` `entryPoints[0].input` / `.output` — using the FLAT deploy
shape, agent-identical: `"input": {"type":"object","properties":{...},"required":[...]}`.
  Do NOT nest Workflow.json’s `schema.document` wrapper inside the entry point (no
`input.schema.document.properties`). `init` scaffolds the entry-point input/output as null,
no CLI verb fills them, and `validate` does not flag drift; the caller reads the finished
contract from `entry-points.json` `entryPoints[0].input.properties`.
  Back-filling entry-points.json this way is a sanctioned exception to that skill’s rule 19a
"Then edit Workflow.json only" (and to its "input/output may be null") — populated
entry-point I/O is part of the deliverable; null is NOT acceptable here.
  Design everything else — activities, expressions, control flow, connectors, and additional
I/O — as Purpose needs; the uipath-api-workflow skill owns that choice, including HTTP and
Integration Service connectors (`uip login` is already active, so its `registry resolve` +
`stub` work). Remain non-interactive: where rule 16 would stop and ask because a required
Integration Service activity lacks a connection confirmed by `uip is connections ping`, do
NOT ship `<REPLACE_WITH_*>` or improvise; return
{ built:false, error:"<name> needs an unavailable Integration Service connection" } so the
caller placeholders the task. If you author an Integration Service connector, run
`uip api-workflow bindings sync --workflow <Workflow.json>` before returning (rule 16),
even though registration is deferred; it writes the connection to `bindings_v2.json`, which
the caller’s `uip solution resources refresh` (run post-register) catalogs into the solution.
  Http-kind (`ImplicitConnection`) and pure-compute workflows need no connection or bindings sync.
  Do NOT register into the solution — the caller registers via `uip solution projects add`.
  If you cannot locate/load the uipath-api-workflow skill, do NOT improvise a build — return
{ built:false, error:"skill uipath-api-workflow not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

The brief carries only Step-1b Purpose and pinned I/O, not `caseplan.case` or sibling tasks; quote `<WorkflowName>` and paths (SDD-derived). Build in a sub-agent and use orchestration/parallelism from [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Because registration is skipped, the caller sequentially runs `uip solution projects add` for each sibling, then `resources refresh`, before §4 rediscovery, which reads `.uipx` `Projects[]`; see [registry-discovery.md § Create-on-Missing, Step 3 — Register](../../../registry-discovery.md#create-on-missing-build-and-rediscovery).

### Step 3 — Binding (no new field)

Apply [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): two bindings with `resource:"process"`, **`resourceSubType:"Api"`**, and shared `resourceKey="solution_folder.<WorkflowName>"`; default `name` is `<WorkflowName>` and `folderPath` is `""`. The sentinel/`""`` decoupling and deploy-provisioning rationale are there; Api debug differs:

> **Runtime: full deploy YES — `case debug` NO (e2e-verified 2026-07).** `uip maestro case pack` → `uip solution pack` → `publish` → `deploy run` provisions the sibling as a runnable process in the case’s Orchestrator folder (process key `<Package>.Api.<Name>`), and the task invokes it successfully. `uip maestro case debug` does **NOT** provision Api siblings (unlike agent siblings); the task reaches `Orchestrator.StartJob` and faults with incident `170007` "The job's associated process could not be found" despite a valid binding. Verify inline API runtime behavior via full solution deploy, never `case debug`. `validate` and binding correctness are unaffected.

### Failure — surface and re-prompt, never stall

Apply [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): `built:false` → show `error` verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, use Unresolved Fallback; verify-time I/O mismatch is a warning, never a failure.

> **"Already exists" is NOT a failure**—adopt an interrupted prior build per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). API tokens: init verb `uip api-workflow init`; kind markers `Category: "api"` (registered) / `project.uiproj` `ProjectType: "Api"` (unregistered); stale-declaration category subpath `process/api/`.

## Fields to Resolve

Ledger entry in `tasks/registry-resolved.json`—Rule 10 keys plus this lookup output:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "api-workflow",
  "cacheFile": "api-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<resource-name>",
  "taskTypeId": "<entityKey>",
  "folder-path": "<folder>",
  "rationale": "<why this match was selected>"
}
```

`matches` is the complete exact-name set from the refreshed cache; `selected` is the chosen match object, or `null` after a genuine empty lookup (see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape)).

All other SDD declarations—inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text—remain in `sdd.md`. The ledger contains only registry output; Phase 2 reads the contract directly from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->