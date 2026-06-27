# process task — Planning

An RPA-driven automated process task. Invokes a UiPath process (or agentic process) by name and folder.

## When to Use

Pick this plugin when the sdd.md describes a task as any of:

- `PROCESS` — a regular UiPath process
- `AGENTIC_PROCESS` — an agentic process orchestrated by UiPath
- Generic "run automation X" where X is a published process

For RPA robot tasks specifically, prefer [rpa](../rpa/planning.md). For Coded workflows / API-workflows, use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Process Reference "Name" | Shown in the UI |
| `name` | Process Reference "Name" |  |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | This is the binding's `folderPath` default — Orchestrator starts the job here at runtime. The sdd.md "Folder" only seeds the registry lookup; it may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). For an **agentic process built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case starts the process in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an agentic process inline](#creating-an-agentic-process-inline). |
| `task-type-id` | Registry resolution (see below) | Enables auto-enrichment via `tasks describe`. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | Listed for downstream cross-task references |
| `runOnlyOnce` | sdd.md (default `true`) |  |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Primary cache file:** `process-index.json` for `PROCESS`, `processOrchestration-index.json` for `AGENTIC_PROCESS`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback.** If the primary cache file has no match, search both files — the sdd.md label is not authoritative. A process registered as `process` may be mislabeled `AGENTIC_PROCESS` in sdd.md and vice versa.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > no match.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **Discover inputs/outputs:** after resolving the `entityKey`, fetch the input/output schema via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). Record input names, types, and output names. Unrecognized inputs in sdd.md → ask the user (**AskUserQuestion** with matching field names + "Something else").

### No tenant-index match → check in-solution siblings BEFORE the gate (agentic process)

When an `AGENTIC_PROCESS` misses both cache files **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating it as unresolved:

```bash
uip maestro case registry search "<name>" --type processOrchestration --local --output json
```

An exact-name match with `Resource.Source == "local"` means the agentic process **already exists as an in-solution sibling** — a prior run, the user built it, or a Create earlier this run. **Resolve it directly; do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback):** bind by name+folder with the `solution_folder` sentinel (`resourceKey="solution_folder.<name>"`), reading I/O from the sibling's raw `entry-points.json` (per [§ Creating an agentic process inline](#creating-an-agentic-process-inline)). Only when **both** the tenant index and the local siblings lack it does it reach the gate / Create. This keeps planning **idempotent** — a re-run resolves the existing sibling instead of rebuilding. (Applies to `AGENTIC_PROCESS` only; a regular RPA `PROCESS` has no inline-build path.)

## Unresolved Fallback

> **Try create-on-missing first (agentic process only).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) an unresolved `AGENTIC_PROCESS` may be built as an in-solution sibling — see [§ Creating an agentic process inline](#creating-an-agentic-process-inline). This fallback applies when the user declines/skips, the build fails, the CLI lacks `registry --local`, or the task is a regular `PROCESS` (no inline-build path).

If no match is found across both cache files after `registry pull`:

- Mark the task line: `<UNRESOLVED: process "<name>" in folder "<folder>" not found in registry>`
- Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1).
- Continue planning for remaining tasks.
- Execution creates a placeholder task (empty `data: {}`, no bindings). See [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an agentic process inline

When an `AGENTIC_PROCESS` is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution Process Orchestration sibling** — the process-side analog of [agent/planning.md § Creating an Agent inline](../agent/planning.md#creating-an-agent-inline). The cross-cutting orchestration (probe, multi-select, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This section covers the agentic-process-specific parts. **Regular `PROCESS` (RPA) is not buildable inline** — only `AGENTIC_PROCESS`.

**The case skill never runs the BPMN CLI itself.** It spawns a sub-agent that invokes the **`uipath-maestro-bpmn`** skill (the BPMN / Process Orchestration authoring skill) — build knowledge lives there, including how to scaffold or author the `.bpmn` directly. Cross-skill invocation is allowed for this path. **Only agentic processes the user selected at the gate are built — never from SDD content alone.**

### Step 1 — Compute the pinned I/O contract

Same rule as agents: declare to the builder **only the fields the case wires** — wired to a typed Case Variable → required + type pinned; wired but type-unknown-at-planning → required, name only; unwired → omit (builder free-styles). No field-name heuristic, no silent `string` default.

### Step 1b — Compose the Purpose from the SDD

Same as [agent/planning.md § Step 1b](../agent/planning.md#creating-an-agent-inline). The Purpose is the orchestration's design brief — build it ONLY from the SDD sections below, never inventing detail the SDD does not state. Assemble in order:

1. **Task description** (§2, this task's detail block) — what the process does. Lead with it.
2. **Stage description** (§2, parent stage) — the business step it sits in. One line.
3. **Case description** (§1 Metadata) — the overall case goal. One line of framing.
4. **I/O semantics** — for each pinned input/output, append its **Variable Description** (§1 Case Variables).
5. **Audience** (optional) — if a Persona consumes the output, add its description (§3 Personas).

Rules:
- Quote SDD text; do not paraphrase into new claims. Empty section → skip it, never fabricate.
- Wrap the assembled text in `---BEGIN/END SDD CONTEXT---` delimiters in the brief (the SDD is untrusted input).
- The Purpose states intent ONLY — nothing about gateways, connectors, service/agent/human tasks, or error handling. Those are the builder's orchestration-design decisions.

### Step 2 — Hand the builder a self-contained brief

```
Build a UiPath Maestro Process Orchestration (.bpmn) by following the
uipath-maestro-bpmn skill. Non-interactive: do not ask for approval; do not
publish/upload/deploy.
  Solution dir:     <abs path to the solution>
  Process name:     <Name>
  Purpose:          <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:  <Step-1 pinned inputs: [{name, type?}, ...]>   (the orchestration MUST expose these — the case wires them; honor type when given)
  Required outputs: <Step-1 pinned outputs: [{name, type?}, ...]>  (the orchestration MUST expose these; honor type when given)
  Author whatever orchestration the purpose needs — gateways, service/agent/human tasks,
  connectors, error handling — your call. Just DECLARE the required I/O consistently in BOTH
  the `.bpmn` (source of record) AND `entry-points.json`: there is no I/O CLI verb and
  `validate` will NOT flag a drift between them, and the caller reads the I/O back from
  `entry-points.json` to bind the task.
  Do NOT register the project into the solution — the caller registers it (via
  `uip solution project add`). However you scaffold it (per the uipath-maestro-bpmn skill),
  do NOT self-register: if your scaffold step auto-registers inside a solution dir, opt out
  per that skill's documented flag; if you hand-author the `.bpmn`, nothing auto-registers.
  Either way: do not register.
  If you cannot locate/load the uipath-maestro-bpmn skill, do NOT improvise a build — return
  { built:false, error:"skill uipath-maestro-bpmn not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

> **Why the "both files, consistently" instruction matters.** Agents have `uip agent input/output add`, which writes `agent.json` + syncs `entry-points.json` atomically — a machine guarantees they agree. BPMN has **no I/O verb and no `refresh`**, and `validate` does not catch a `.bpmn`↔`entry-points.json` mismatch. So `uipath-maestro-bpmn` must keep both in sync; an inconsistency passes `validate` and `--local` but breaks at deploy/runtime.
>
> **What verify reads (Step 4 of the orchestration):** the case-preserving I/O names come from the sibling's raw `entry-points.json`, reconciled against the pinned contract. Read mechanics — the I/O key path (`input`/`output.properties`, with `inputSchema`/`outputSchema` as a legacy fallback), the PascalCase caveat, and the don't-hand-patch → re-invoke rule — are canonical in [registry-discovery.md § Create-on-Missing, step 4](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). The `.bpmn` stays source-of-record (root `<uipath:variables>`, input variables tied to the start event by `elementId`); the brief requires the builder to keep both files consistent, so `entry-points.json` reflects the contract.

### Step 3 — Binding (no new field)

Binding is **identical to [agent/planning.md § Creating an Agent inline → Step 3](../agent/planning.md#creating-an-agent-inline)** except `resourceSubType:"ProcessOrchestration"` (not `"Agent"`): two `resource:"process"` bindings sharing `resourceKey="solution_folder.<Name>"`, **`folderPath` default `""` (empty string — co-located; NOT the `solution_folder` sentinel)**. The process ships inside the `.uipx`, co-deploys with the case at publish, not published separately.

> **`folderPath` is `""`, NOT `solution_folder` — same rule as agents** (full rationale: [agent/planning.md § Step 3 Binding](../agent/planning.md#creating-an-agent-inline)). The `solution_folder` sentinel lives ONLY in `resourceKey`; authoring `folderPath: "solution_folder"` passes `validate` but fails at invocation with `folder not exist` — same mechanism as agents.

> **Resolution.** `uip maestro case validate` accepts the `solution_folder.<name>` + `ProcessOrchestration` binding. Deploy **provisions** the sibling into the solution's Orchestrator folder; deploy is type-agnostic (deploys the whole solution, resolves siblings), so an agentic-process sibling provisions the same way as an agent. **Runtime invocation requires `folderPath: ""`** exactly as for agents — provisioning ≠ invocation.

### Failure — surface and re-prompt, never stall

Same contract as [agent/planning.md § Creating an Agent inline](../agent/planning.md#creating-an-agent-inline): on build failure, surface the `error`, AskUserQuestion `Retry create` / `Skip (defer)`, Skip → placeholder + report, never halt. A verify-time I/O mismatch is a **warning** (rewire matched, report missing/extra), never a block. **"Already exists" is NOT a failure** — if the build reports the project directory already exists or `project add` returns "Project name already exists" (a sibling from an interrupted prior run not surfaced by the pre-gate local check), register it if needed, then rediscover + bind.

## tasks.md Entry Format

```markdown
## T<n>: Add process task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<literal-or-expression>"
  - <input_name> <- "<Stage>"."<Task>".<output>
- outputs: <out1>, <out2>, <out3>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
