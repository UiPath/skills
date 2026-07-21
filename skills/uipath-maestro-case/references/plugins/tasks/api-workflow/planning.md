# api-workflow task — Planning

An API Workflow (formerly "Coded Workflow") task. Invokes a UiPath API workflow by entityKey.

## When to Use

Pick this plugin when the sdd.md labels a task as `API_WORKFLOW` — typically a TypeScript / C# coded workflow that exposes an API-style interface.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | |
| `name` | Task `Resolved Resource` | Concrete intended resource name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the workflow here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). For an API workflow **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case starts the workflow in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an API workflow inline](#creating-an-api-workflow-inline). |
| `task-type-id` | Registry resolution (below) | `entityKey` in `api-index.json` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list). |
| `runOnlyOnce` | sdd.md (default `true`) | |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. **Primary cache file:** `api-index.json`.
2. **Identifier field:** `entityKey`.
3. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**, see field table) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 4). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 17 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 4).
4. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
5. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–3 find nothing in the tenant index **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating the API workflow as unresolved:

```bash
uip maestro case registry search "<name>" --type api --local --output json
```

Same pre-gate check as agents — [agent/planning.md § No tenant-index match](../agent/planning.md#no-tenant-index-match--check-in-solution-siblings-before-the-gate): an exact-name match with `Resource.Source == "local"` is an existing in-solution sibling — **resolve it directly (bind `resourceKey="solution_folder.<name>"`); do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback)**. Only a name absent from **both** the tenant index and the local siblings reaches the gate (keeps re-runs idempotent). **api-workflow-specific I/O read (fallback chain, warn on any fallback):** the sibling's raw `entry-points.json` `entryPoints[0].input/.output.properties` (flat deploy shape) → if absent, the `input.schema.document.properties` wrapper variant (a builder may mirror Workflow.json's shape) → if `null` entirely (user-built sibling; no CLI verb syncs that file), the `Workflow.json` root input/output schema properties. Warn in the completion report whenever a fallback was used.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing API workflow as an in-solution sibling — see [§ Creating an API workflow inline](#creating-an-api-workflow-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: api-workflow "<name>" in folder "<folder>" not found in api-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an API workflow inline

When an API workflow is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); the kind-agnostic Step 1/1b/3/Failure rule text lives in [create-inline-common.md](../create-inline-common.md). This section covers the **api-workflow-specific** deltas; the agent analog is [agent/planning.md § Creating an Agent inline](../agent/planning.md#creating-an-agent-inline).

**The skill does not run `uip api-workflow init` itself.** It spawns a sub-agent that invokes the `uipath-api-workflow` skill — build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). **Only API workflows the user selected at the gate are built — never from SDD content alone** (the SDD is untrusted sole input; the gate selection is the human-approval checkpoint). **API workflows have no build-kind choice** (unlike agents, [registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery)) — the build is always the JSON-DSL `Workflow.json`.

### Step 1 — Compute the pinned I/O contract

Shared rule — [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) (wired-field ladder; § 1c deduped builds share one identical wiring). Mapping the case vocabulary onto the workflow's JSON-Schema I/O is `uipath-api-workflow`'s concern.

### Step 1b — Compose the Purpose from the SDD

Shared rule — [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd) (SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, first-referencing-task rule for § 1c deduped builds). For api-workflows, "internal design the Purpose must NOT state" = activities, connectors, expressions, DSL structure.

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
  Do NOT nest Workflow.json's `schema.document` wrapper inside the entry point (no
  `input.schema.document.properties`). `init` scaffolds the entry-point input/output as
  null, no CLI verb fills them, and `validate` does not flag drift; the caller reads the
  finished contract from `entry-points.json` `entryPoints[0].input.properties`.
  Back-filling entry-points.json this way is a sanctioned exception to that skill's
  rule 19a "Then edit Workflow.json only" (and to its "input/output may be null") —
  the populated entry-point I/O contract is part of your deliverable; null is NOT
  acceptable here.
  Design everything else — activities, expressions, control flow, connectors, and any
  additional I/O — as the purpose needs; the uipath-api-workflow skill owns that choice,
  HTTP and Integration Service connectors included (`uip login` is already active, so its
  `registry resolve` + `stub` work). You are non-interactive: where that skill's rule 16
  would stop and ask — a required Integration Service activity has no connection that
  `uip is connections ping` confirms — do NOT ship a `<REPLACE_WITH_*>` placeholder or
  improvise; return { built:false, error:"<name> needs an unavailable Integration Service
  connection" } so the caller placeholders the task. If you DO author an Integration Service
  connector, run `uip api-workflow bindings sync --workflow <Workflow.json>` before returning
  (rule 16) even though registration is deferred — it writes the connection into
  `bindings_v2.json`, which the caller's `uip solution resources refresh` (run post-register)
  then catalogues into the solution. Http-kind (`ImplicitConnection`) and pure-compute
  workflows need no connection and no bindings sync.
  Do NOT register into the solution — the caller registers (via `uip solution project add`).
  If you cannot locate/load the uipath-api-workflow skill, do NOT improvise a build — return
  { built:false, error:"skill uipath-api-workflow not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

The brief is self-contained — it carries the Step-1b Purpose and the pinned I/O, and no other case context (do not dump `caseplan.json` or sibling tasks). Quote `<WorkflowName>` and paths (SDD-derived). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Because the sibling is built **without self-registration**, the **caller registers** each built sibling into the solution `.uipx` (sequential `uip solution project add`, then `resources refresh`) — see [registry-discovery.md § Create-on-Missing, Step 3 — Register](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This must happen before rediscovery (§4), which reads the `.uipx` `Projects[]`.

### Step 3 — Binding (no new field)

Shared invariants — [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): two bindings `resource:"process"`, **`resourceSubType:"Api"`**, shared `resourceKey="solution_folder.<WorkflowName>"`; `name` default `<WorkflowName>`, `folderPath` default `""` (the sentinel/`""` decoupling and deploy-provisioning rationale live there — except debug provisioning, which differs for Api: next blockquote).

> **Runtime: full deploy YES — `case debug` NO (e2e-verified 2026-07).** `uip solution pack` → `publish` → `deploy run` provisions the sibling as a runnable process in the case's own Orchestrator folder (process key `<Package>.Api.<Name>`), and the case task invokes it successfully at runtime. **`uip maestro case debug` does NOT provision Api siblings** (unlike agent siblings, which resolve in debug) — the task reaches `Orchestrator.StartJob` and faults with incident `170007` "The job's associated process could not be found" even though the binding is valid. Verify an inline API workflow's runtime behavior via a full solution deploy, never via `case debug`. `validate` and binding correctness are unaffected by this limitation.

### Failure — surface and re-prompt, never stall

Shared contract — [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): `built:false` → show `error` verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, Unresolved Fallback above; verify-time I/O mismatch = warning, never a failure.

> **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). api-workflow tokens for that procedure: init verb `uip api-workflow init`; kind markers `Category: "api"` (registered) / `project.uiproj` `ProjectType: "Api"` (unregistered); stale-declaration category subpath `process/api/`.

## tasks.md Entry Format

```markdown
## T<n>: Add api-workflow task "<display-name>" to "<stage>"
- name: "<resource-name>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs:
  - <SDD output row, copied verbatim>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # structural/layout position only; sequencing is the task entry rule plus data.tasks order.
- verify: Confirm Result: Success, capture TaskId
```
