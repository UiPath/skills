# agent task — Planning

An AI agent task invoking a UiPath Agent by `entityKey` for reasoning, classification, extraction, or generative work.

## When to Use

Use when `sdd.md` describes an `AGENT`: an AI agent that processes inputs and returns structured outputs requiring reasoning or judgment rather than deterministic automation.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete resource name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT sdd.md `Folder`) | Binds to `data.folderPath`; Orchestrator starts the agent here. `Folder` only seeds lookup and may be parent/truncated. See [§ Registry Resolution](#registry-resolution). For an agent **built inline** as an in-solution sibling, use runtime `folder-path` `""` (co-located case starts it in its deployed folder); keep `resourceKey` as `solution_folder.<name>` and never put the `solution_folder` sentinel in `folder-path` (`runtime folder not exist`). See [§ Creating an Agent inline](#creating-an-agent-inline). |
| `task-type-id` | Registry resolution below | Enables auto-enrichment via `tasks describe` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not task type |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. Search `agent-index.json` first, using `entityKey`.
2. If unmatched, search `processOrchestration-index.json`; agents wrapped in an agentic process may be registered there.
3. Select by priority: exact name + exact folder > exact name with multiple folders (pick matching) > exact name only > no match. An exact-name entry in another folder, including an sdd.md-folder child, is **exact name only**: resolve it and bind `folder-path` to its full registry path. Do not treat folder differences as no-match or enter the Create gate; that gate applies only when no registry entry carries the name. A true no-match first runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate), then the Rule 18 gate; only a task unresolved after that gate falls back to the sdd.md folder.
4. Set `folder-path` to the selected entry's `folders[0].fullyQualifiedName`, never sdd.md `Folder`; use sdd.md `Folder` only for an unmatched task (Unresolved path).
5. Run `tasks describe` to discover inputs/outputs; see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

Skip this check when `sdd resolve` reports `Data.Scope.siblingsChecked: true`; resolve already searched solution projects ([registry-discovery.md § Resolve with the CLI first](../../../registry-discovery.md#resolve-with-the-cli-first)). Otherwise, when steps 1–3 find no tenant-index entry and the CLI supports `registry --local`, run:

```bash
uip maestro case registry search "<name>" --type agent --local --output json
```

An exact-name result with `Resource.Source == "local"` is an existing in-solution sibling (built by a prior run, the user, or this run). Resolve it directly; do **not** enter the [Rule 18 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback). Bind by name and folder with `resourceKey="solution_folder.<name>"`, reading I/O from the sibling's raw `entry-points.json` per [§ Creating an Agent inline](#creating-an-agent-inline). Reach the gate/Create only when both tenant index and local siblings lack the agent. This makes planning idempotent.

## Unresolved Fallback

At the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback), the user may choose **Create** to build the missing agent as an in-solution sibling; see [§ Creating an Agent inline](#creating-an-agent-inline). Apply this fallback only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: agent "<name>" in folder "<folder>" not found in registry>`. Omit resolved-schema keys `inputs` / `outputs`; put intended wiring in the entry's `wiringNotes` string array. Execution creates a placeholder task; see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an Agent inline

When unresolved at the [Rule 18 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects **Create**, build an **in-solution sibling**. Use [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) for capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, and rediscover/verify/bind; use [create-inline-common.md](../create-inline-common.md) for kind-agnostic Step 1/1b/3/Failure. This section supplies agent-specific build kind, brief, and debug provisioning.

Do not run `uip agent init` directly. Spawn a sub-agent invoking the `uipath-agents` skill; cross-skill invocation is allowed here despite `SKILL.md § Non-negotiable prohibitions`. Build only agents selected by the user at the gate, never from SDD content alone; the gate is the human-approval checkpoint.

### Step 1 — Compute the pinned I/O contract

Follow [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract): use the wired-field ladder and make § 1c deduped builds share identical wiring. Mapping case vocabulary to the agent schema is `uipath-agents`' concern.

### Step 1b — Compose the Purpose from the SDD

Follow [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd): SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, and first-referencing-task rule for § 1c deduped builds. For agents, Purpose must not state kind, tools, RAG, guardrails, or model.

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath agent by following the uipath-agents skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy.
  Solution dir:     <abs path to the solution>
  Agent name:       <AgentName>
  Kind:             <low-code | coded>   (the kind the user chose at the Create gate — registry-discovery.md § 1b; equal user choice, low-code is the non-interactive fallback — see § Coded agents)
  Purpose:          <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:  <Step-1 pinned inputs: [{name, type?}, ...]>   (the agent MUST expose these — the case wires them; honor type when given, else choose the type that best fits the purpose)
  Required outputs: <Step-1 pinned outputs: [{name, type?}, ...]>  (the agent MUST expose these; honor type when given)
  Design everything else — tools, knowledge/RAG, guardrails, model, and any additional
  I/O — as the purpose needs.
  Do NOT register into the solution — the caller registers (via `uip solution projects add`).
  Low-code `uip agent init` auto-registers inside a solution dir — pass
  `--skip-solution-registration` to opt out (`OptedOut` is expected, not an error); coded
  `uip codedagent init` does not auto-register, so no flag is needed. Either way: do not register.
  If you cannot locate/load the uipath-agents skill, do NOT improvise a build — return
  { built:false, error:"skill uipath-agents not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

Include only the Step-1b Purpose and pinned I/O, not `caseplan.case` or sibling tasks. Build in a sub-agent; follow [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) for orchestration/parallelism. Because either kind is built without self-registration, register each sibling into the solution `.uipx` with sequential `uip solution projects add`, then `resources refresh`, before rediscovery (§4), which reads `.uipx` `Projects[]`; see [registry-discovery.md § Create-on-Missing, Step 3 — Register](../../../registry-discovery.md#create-on-missing-build-and-rediscovery).

### Step 3 — Binding (no new field)

Follow [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): create two bindings with `resource:"process"`, **`resourceSubType:"Agent"`**, and shared `resourceKey="solution_folder.<AgentName>"`; default `name` to `<AgentName>` and `folderPath` to `""`. The sentinel/`""` decoupling and deploy-provisioning rationale are there.

For debug, `uip maestro case debug` packages the entire solution directory (`buildSolutionPackageFromDir(<solutionDir>)`) but does not provision agent siblings; the task faults with incident `170007` (verified 2026-10-12), as Api siblings do ([api-workflow/planning.md § Step 3](../api-workflow/planning.md#creating-an-api-workflow-inline)). Verify inline-agent runtime only through a full solution deploy, never `case debug`.

### Coded agents — default low-code; gated; integration caveat

The user chooses kind at the Create gate ([registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery)); present **low-code and coded as equal choices**, neither recommended. The non-interactive fallback is low-code (`uip agent init`, platform default); coded is `uip codedagent`. Never infer kind from the SDD. Resolve a pre-existing user-built coded sibling directly without a gate per the in-solution sibling check.

For case integration, coded and low-code are identical: `uip solution projects add` + `uip solution resources refresh` are type-agnostic; discovery uses `registry search --type agent --local`; `entry-points.json` has the same `input.properties` / `output.properties` shape; binding uses `resourceSubType:"Agent"`, `resourceKey="solution_folder.<name>"`, and `folderPath:""`. Differences are only in the packer (`@uipath/tool-agent` forks on `pyproject.toml` into different `operate.json` / `package-descriptor` / file set) and appear at delivery.

A coded sibling delivered with **`uip solution upload`** and installed to an Orchestrator folder (UI deploy) runs cleanly. The coded packer passes the Python tool's `entry-points.json` `uniqueId` without UUID validation (`z.string()`, not `.uuid()`); Python emits a UUID, so install succeeds and coded does not hit the `bpmn init` `uniqueId` bug class. UI deploy and `uip solution deploy run` share the Orchestrator install pipeline. If a coded build ever supplies a non-UUID `uniqueId`, install rejects it (`FailedInstall`); check that field first if installation fails.

### Failure — surface and re-prompt, never stall

Follow [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): for `built:false`, show `error` verbatim and ask via AskUserQuestion: `Retry create` / `Skip (defer)`. On Skip/repeat, use Unresolved Fallback. Verify-time I/O mismatch is a warning, never a failure.

**"Already exists" is NOT a failure**: adopt the interrupted prior build per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Agent tokens: init verb `uip agent init`; kind markers `Category: "agent"` (registered) / `agent.json` on disk (unregistered).

## Fields to Resolve

Record the ledger entry in `tasks/registry-resolved.json` using Rule 10's keys plus:

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "agent",
  "cacheFile": "agent-index.json",
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

Keep all other SDD declarations—inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text—in `sdd.md`. The ledger stores only registry lookup results; Phase 2 reads the contract from the SDD ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->