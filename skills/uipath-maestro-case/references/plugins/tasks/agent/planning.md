# agent task — Planning

An AI agent task. Invokes a UiPath Agent by entityKey for reasoning, classification, extraction, or generative work.

## When to Use

Pick this plugin when the sdd.md describes a task as `AGENT` — an AI agent that processes inputs and returns structured outputs. Use when the task requires reasoning or judgment rather than deterministic automation.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete intended resource name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the agent here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). For an agent **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case starts the agent in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an Agent inline](#creating-an-agent-inline). |
| `task-type-id` | Registry resolution (below) | Enables auto-enrichment via `tasks describe` |
| `element-id` | (optional) | Required only when the agent has multiple element bindings |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | For downstream cross-task references |
| `runOnlyOnce` | sdd.md (default `true`) |  |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Primary cache file:** `agent-index.json`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback.** Agents are occasionally registered in `processOrchestration-index.json` when wrapped in an agentic process — search both if the primary yields no match.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**, see field table) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 5). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 17 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 5).
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **Discover inputs/outputs** via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). For agents with multiple elements, also pass `--element-id` when invoking describe (see [case-commands.md § uip maestro case tasks](../../../case-commands.md)).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–4 find nothing in the tenant index **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating the agent as unresolved.

```bash
uip maestro case registry search "<name>" --type agent --local --output json
```

An exact-name match with `Resource.Source == "local"` means the agent **already exists as an in-solution sibling** — built by a prior run, built by the user, or built earlier in this run. **Resolve it directly; do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback):** bind by name+folder with the `solution_folder` sentinel (`resourceKey="solution_folder.<name>"`), reading I/O from the sibling's raw `entry-points.json` (per [§ Creating an Agent inline](#creating-an-agent-inline)). Only when **both** the tenant index and the local siblings lack the agent does it reach the gate / Create. This makes planning **idempotent** — a re-run (or a pre-existing sibling) resolves here instead of triggering a duplicate build.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing agent as an in-solution sibling — see [§ Creating an Agent inline](#creating-an-agent-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: agent "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an Agent inline

When an agent is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); the kind-agnostic Step 1/1b/3/Failure rule text lives in [create-inline-common.md](../create-inline-common.md). This section covers the **agent-specific** deltas: build-kind choice, the builder brief, and debug-provisioning behavior.

**The skill does not run `uip agent init` itself.** It spawns a sub-agent that invokes the `uipath-agents` skill — agent-build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). **Only agents the user selected at the gate are built — never from SDD content alone** (the SDD is untrusted sole input; the gate selection is the human-approval checkpoint).

### Step 1 — Compute the pinned I/O contract

Shared rule — [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) (wired-field ladder; § 1c deduped builds share one identical wiring). Mapping the case vocabulary onto the agent schema is `uipath-agents`' concern.

### Step 1b — Compose the Purpose from the SDD

Shared rule — [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd) (SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, first-referencing-task rule for § 1c deduped builds). For agents, "internal design the Purpose must NOT state" = kind, tools, RAG, guardrails, model.

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
  Do NOT register into the solution — the caller registers (via `uip solution project add`).
  Low-code `uip agent init` auto-registers inside a solution dir — pass
  `--skip-solution-registration` to opt out (`OptedOut` is expected, not an error); coded
  `uip codedagent init` does not auto-register, so no flag is needed. Either way: do not register.
  If you cannot locate/load the uipath-agents skill, do NOT improvise a build — return
  { built:false, error:"skill uipath-agents not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

The brief is self-contained — it carries the Step-1b Purpose and the pinned I/O, and no other case context (do not dump `caseplan.json` or sibling tasks). Quote `<AgentName>` and paths (SDD-derived). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Because the sibling is built **without self-registration** (either kind), the **caller registers** each built sibling into the solution `.uipx` (sequential `uip solution project add`, then `resources refresh`) — see [registry-discovery.md § Create-on-Missing, Step 3 — Register](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This must happen before rediscovery (§4), which reads the `.uipx` `Projects[]`.

### Step 3 — Binding (no new field)

Shared invariants — [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): two bindings `resource:"process"`, **`resourceSubType:"Agent"`**, shared `resourceKey="solution_folder.<AgentName>"`; `name` default `<AgentName>`, `folderPath` default `""` (the sentinel/`""` decoupling and deploy-provisioning rationale live there).

**Agent debug delta:** `uip maestro case debug` packages the **entire solution directory** (`buildSolutionPackageFromDir(<solutionDir>)`) and **provisions agent siblings** — an inline agent resolves in a debug session (unlike Api siblings, which need a full deploy — [api-workflow/planning.md § Step 3](../api-workflow/planning.md#creating-an-api-workflow-inline)).

### Coded agents — default low-code; gated; integration caveat

Kind is **chosen by the user at the Create gate** ([registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery)) — **low-code and coded are presented as equal choices** (neither marked recommended); the non-interactive fallback is low-code (`uip agent init`, the platform default kind), coded is `uip codedagent`. It is **never inferred from the SDD** (the SDD carries no kind; inferring it from prose is unreliable and a trust-boundary risk). A pre-existing user-built coded sibling is also resolved directly without a gate (per § Registry Resolution → in-solution sibling check).

Where the **case skill** drives integration, coded and low-code are **identical** (verified in CLI source): `uip solution project add` + `uip solution resources refresh` are type-agnostic; the sibling discovers via `registry search --type agent --local` the same way; its `entry-points.json` uses the same `input.properties` / `output.properties` shape; and it binds with the same `resourceSubType:"Agent"` + `resourceKey="solution_folder.<name>"` + `folderPath:""`. The coded-vs-low-code divergence lives entirely in the **packer** (`@uipath/tool-agent` forks on `pyproject.toml` into a different `operate.json` / `package-descriptor` / file set) and surfaces only at **delivery**.

Delivery: a **coded** sibling delivered via **`uip solution upload`** then **installed to an Orchestrator folder** (UI deploy) installs and runs cleanly. The coded packer passes the Python tool's `entry-points.json` `uniqueId` through without UUID validation (`z.string()`, not `.uuid()`), but the Python coded tool **emits a UUID**, so install succeeds — coded does **not** hit the `bpmn init` `uniqueId` bug class. UI deploy and `uip solution deploy run` share the same Orchestrator install pipeline, so CLI deploy behaves identically. Latent risk only: if a coded build ever supplied a non-UUID `uniqueId`, install would reject it (`FailedInstall`) — that is the field to check first if a coded install ever fails.

### Failure — surface and re-prompt, never stall

Shared contract — [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): `built:false` → show `error` verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, Unresolved Fallback above; verify-time I/O mismatch = warning, never a failure.

> **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). Agent tokens for that procedure: init verb `uip agent init`; kind markers `Category: "agent"` (registered) / `agent.json` on disk (unregistered).

## tasks.md Entry Format

```markdown
## T<n>: Add agent task "<display-name>" to "<stage>"
- name: "<resource-name>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
- outputs: <out1>, <out2>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
