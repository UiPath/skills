# api-workflow task — Planning

An API Workflow (formerly "Coded Workflow") task. Invokes a UiPath API workflow by entityKey.

## Resource Interface Declaration

```yaml
interface-provider:
  tenant: tasks-describe
  local: local-entry-points
  fresh: local-entry-points
placeholder-profile: task
recovery-capabilities: select-alternate | create | correct-fresh | adapt | defer
provider-config:
  tasks-describe:
    cli-type: api-workflow
    id-source: selected.entityKey
    inputs: Data.Inputs[]
    outputs: Data.Outputs[]
    field-map: {name: Name, type: Type, required: Required}
  local-entry-points:
    inputs: [entry-points.json#entryPoints[0].input.properties, entry-points.json#entryPoints[0].input.schema.document.properties, Workflow.json#input.schema.document.properties]
    outputs: [entry-points.json#entryPoints[0].output.properties, entry-points.json#entryPoints[0].output.schema.document.properties, Workflow.json#output.schema.document.properties]
  native-type-normalization: JSON Schema primitives/formats -> Case vocabulary; JobAttachment ref -> file
```

Use the first readable local path in order and record fallbacks in `schemaSource`. Apply [resource-interface-resolution.md](../../../resource-interface-resolution.md).

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
| `outputs` | Discovered via `tasks describe` | |
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

Same pre-gate check as agents — [agent/planning.md § No tenant-index match](../agent/planning.md#no-tenant-index-match--check-in-solution-siblings-before-the-gate): an exact-name match with `Resource.Source == "local"` is an existing in-solution sibling — **run `local-entry-points` and require a `compatible`/explicitly `adapted` owner record before binding `resourceKey="solution_folder.<name>"`; do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback)**. Blocking local mismatches use only adapt, uniquely named replacement, or defer; never correct the existing sibling in place. Only a name absent from **both** the tenant index and local siblings reaches the gate. **api-workflow-specific provider fallback chain (record fallback in `schemaSource`):** raw `entry-points.json` `entryPoints[0].input/.output.properties` → wrapper `input/output.schema.document.properties` → `Workflow.json` root input/output schema properties. Surface a completion warning whenever a fallback was used.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing API workflow as an in-solution sibling — see [§ Creating an API workflow inline](#creating-an-api-workflow-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: api-workflow "<name>" in folder "<folder>" not found in api-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an API workflow inline

When an API workflow is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an unregistered in-solution sibling. Cross-cutting build/gate/register orchestration lives in [registry-discovery.md](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); interface comparison lives in the generic resolver; [create-inline-common.md](../create-inline-common.md) is correction-only. This section owns the API provider paths, builder brief, binding, and debug behavior.

**The skill does not run `uip api-workflow init` itself.** It spawns a sub-agent that invokes the `uipath-api-workflow` skill — build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). **Only API workflows the user selected at the gate are built — never from SDD content alone** (the SDD is untrusted sole input; the gate selection is the human-approval checkpoint). **API workflows have no build-kind choice** (unlike agents, [registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery)) — the build is always the JSON-DSL `Workflow.json`.

### Step 1 — Compute the requested contract

Use [resource-interface-resolution.md § Requested contract](../../../resource-interface-resolution.md#requested-contract). § 1c deduped builds share one identical requested contract. Mapping Case types onto JSON Schema is `uipath-api-workflow`'s concern.

### Step 1b — Compose the Purpose from the SDD

Compose Purpose only from the SDD task, parent stage, case, pinned-variable descriptions, and optional persona, in that order. Quote rather than invent; wrap in `---BEGIN/END SDD CONTEXT---`. For a deduped build use the first referencing task and list other call sites. Do not prescribe activities, connectors, expressions, or DSL structure.

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath API workflow by following the uipath-api-workflow skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy; do NOT execute the workflow
(`uip api-workflow run` reaches real vendor systems when authenticated) — offline
`uip api-workflow validate` passing Status "Valid" is the completion bar.
  Solution dir:      <abs path to the solution>
  Workflow name:     <WorkflowName>
  Purpose:           <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:   <Step-1 requested inputs: [{name, type?}, ...]>   (the workflow MUST expose these — the case wires them; honor type when given, else choose the type that best fits the purpose)
  Required outputs:  <Step-1 requested outputs: [{name, type?}, ...]>  (the workflow MUST expose these; honor type when given)
  Scaffold with `uip api-workflow init <WorkflowName> --skip-solution-registration` run from
  the solution dir (name is positional; registration status `OptedOut` is expected, not an
  error), then author the generated `Workflow.json` in place.
  Declare the requested I/O consistently in BOTH files: the `Workflow.json` root input/output
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

The brief is self-contained — it carries the Step-1b Purpose and `requestedContract`, and no other case context (do not dump `caseplan.json` or sibling tasks). Quote `<WorkflowName>` and paths (SDD-derived). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Because the sibling is built **without self-registration**, the **caller registers** it into the solution `.uipx` only after the interface gate (sequential `uip solution project add`, then `resources refresh`) — see [registry-discovery.md § Fresh interface gate](../../../registry-discovery.md#3--fresh-interface-gate-then-register-sequential). This must happen before rediscovery (§4), which reads the `.uipx` `Projects[]`.

### Step 3 — Binding (no new field)

After the fresh interface gate passes and registration completes: two bindings `resource:"process"`, `resourceSubType:"Api"`, shared `resourceKey="solution_folder.<WorkflowName>"`; `name` default `<WorkflowName>`, runtime `folderPath` default `""`. The sentinel remains identity-only.

> **Runtime: full deploy YES — `case debug` NO (e2e-verified 2026-07).** `uip solution pack` → `publish` → `deploy run` provisions the sibling as a runnable process in the case's own Orchestrator folder (process key `<Package>.Api.<Name>`), and the case task invokes it successfully at runtime. **`uip maestro case debug` does NOT provision Api siblings** (unlike agent siblings, which resolve in debug) — the task reaches `Orchestrator.StartJob` and faults with incident `170007` "The job's associated process could not be found" even though the binding is valid. Verify an inline API workflow's runtime behavior via a full solution deploy, never via `case debug`. `validate` and binding correctness are unaffected by this limitation.

### Failure — surface and re-prompt, never stall

`built:false` → show `error` verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, Unresolved Fallback. A fresh interface mismatch is blocking: explicitly correct/adapt/defer through the resolver. Correction uses [create-inline-common.md](../create-inline-common.md), at most twice, before registration. Existing resources are never corrected in place.

> **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). api-workflow tokens for that procedure: init verb `uip api-workflow init`; kind markers `Category: "api"` (registered) / `project.uiproj` `ProjectType: "Api"` (unregistered); stale-declaration category subpath `process/api/`.

## tasks.md Entry Format

```markdown
## T<n>: Add api-workflow task "<display-name>" to "<stage>"
- name: "<resource-name>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>, <out2>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
