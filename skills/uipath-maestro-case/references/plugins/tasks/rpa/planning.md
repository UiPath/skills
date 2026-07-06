# rpa task — Planning

An RPA robot task. The sdd.md component type is `RPA`. The task node's `type` field is `"rpa"`, but the cached registry entity typically lives in `process-index.json` — the registry does not separate "process" from "rpa" at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation).

If sdd.md is ambiguous between `PROCESS` and `RPA`, default to `process` unless the sdd.md mentions UI automation, desktop apps, or robot-specific concerns. **Exception when the resource is missing:** if the registry lookup for an ambiguous task comes back empty, surface the ambiguity (AskUserQuestion) instead of silently defaulting — an `rpa` reading is creatable at the Rule 17 gate; a `process` reading is placeholder-only.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | from Process Reference |
| `name` | from Process Reference |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` — NOT the sdd.md "Folder" (which may be a parent path). Binds to `data.folderPath`; Orchestrator starts the job here at runtime. See [§ Registry Resolution](#registry-resolution). For an RPA process **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an RPA process inline](#creating-an-rpa-process-inline). |
| `task-type-id` | from registry (`entityKey` in `process-index.json`) |
| `inputs`, `outputs`, `runOnlyOnce`, `isRequired` | see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (yes — RPA tasks share this cache with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set `type: "rpa"` on the task node; the cache `entityKey` is recorded in `registry-resolved.json` (not written to the node — the task references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`).
4. If no match in `process-index.json`, search all other cache files as a fallback.
5. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**, see field table) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 6). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 17 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 6).
6. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
7. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–5 find nothing in the tenant index **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating the task as unresolved:

```bash
uip maestro case registry search "<name>" --type process --local --output json
```

> **Registry token is `process`, not `rpa`.** The local registry has no `rpa` type — an RPA sibling registers and rediscovers as `--type process` (`Resource.Category == "process"`). `rpa` exists only as the task-node `type` / `tasks describe` token.

An exact-name match with `Resource.Source == "local"` means the process **already exists as an in-solution sibling** — built by a prior run, built by the user, or built earlier in this run. **Resolve it directly; do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback):** bind by name+folder with the `solution_folder` sentinel (`resourceKey="solution_folder.<name>"`), reading I/O from the sibling's on-disk `project.json` `entryPoints` (per [§ Creating an RPA process inline](#creating-an-rpa-process-inline)). Only when **both** the tenant index and the local siblings lack the process does it reach the gate / Create. This makes planning **idempotent** — a re-run (or a pre-existing sibling) resolves here instead of triggering a duplicate build.

## Unresolved Fallback

> **Build it inline first (rpa).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing RPA process as an in-solution sibling — see [§ Creating an RPA process inline](#creating-an-rpa-process-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an RPA process inline

When an RPA process is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This section covers the **RPA-specific** parts: what contract to compute and what brief to hand the builder.

**The skill does not run `uip rpa init` itself.** It spawns a sub-agent that invokes the `uipath-rpa` skill — RPA-build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). The build is a **deterministic scaffold** (no LLM-authored workflow logic): the sibling ships with the pinned argument contract and default-value output assignments; the user implements the real workflow logic in Studio afterward (name it in the completion report). **Only processes the user selected at the gate are built — never from SDD content alone.**

### Step 1 — Compute the pinned I/O contract

Same rule as the agent leg — declare to the builder **only the fields the case wires**:

- **Wired to a typed Case Variable** → **required, type pinned** from the variable's `Type` (SDD Case Variables table).
- **Wired but type not knowable at planning** (cross-task ref, literal, `=metadata.*`) → **required, name only**; the builder picks the type.
- **Unwired** → **omit from the contract**.

Pass the case vocabulary through; mapping it onto .NET argument types is `uipath-rpa`'s concern at build. Reconcile back at verify (§ Step 4) via:

| Case vocab | .NET FQN |
|---|---|
| string | `System.String` |
| integer | `System.Int32` |
| float | `System.Single` |
| double | `System.Double` |
| boolean | `System.Boolean` |
| date / datetime | `System.DateTime` |
| jsonSchema | `System.Collections.Generic.Dictionary<System.String,System.Object>` |
| file | *(no .NET mapping — pass name-only; builder picks; reconcile at verify)* |

Map is proposed-canonical: at verify, treat a differing-but-compatible .NET type in the built `project.json` as authoritative (warn, don't block).

### Step 1b — Build kind (none) + target framework (delegate to uipath-rpa)

**No coded/low-code kind choice** — RPA scaffolds always use XAML/VisualBasic (`uip rpa init` defaults; `--expression-language VisualBasic`). Skip the [registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) agent kind prompt for `rpa`.

**`--target-framework` is NOT fixed — choose it the way `uipath-rpa` does (its Rule 2a), by the task's runtime needs; never default to one.** Read the RPA task's SDD Purpose/Description for the deciding signal (the same cue text the [§ When to Use](#when-to-use) tiebreaker reads):

- **Windows** when the task needs a Windows-only capability — desktop / legacy UI automation, Excel COM, classic Office interop, or WPF (`PresentationFramework`).
- **Portable** (Cross-platform) otherwise — data transforms, parsing, HTTP/API calls, headless file/email work, anything serverless.
- **Genuinely ambiguous / no signal** → surface it with `AskUserQuestion` (framed around the runtime host: Windows-desktop vs cross-platform/serverless) — do NOT silently pick. This rides on the same interactive Create moment as the gate. **Non-interactive run with no signal** → fall back to **Portable** (the only framework the serverless deploy verification can exercise) and flag the fallback choice in the completion report.

Do **not** hardcode Portable — it forecloses Windows-only automation, and `--target-framework` is **immutable after `init`** (uipath-rpa Rule 23), so a wrong pick costs the user a full project recreate, not a retarget. Pass the chosen framework into the Step-2 brief.

> **Headless-build caveat.** The inline build runs in a sub-agent with no Robot. It only *scaffolds* (writes project files + injects I/O) — it never builds or runs the workflow — so a **Windows** scaffold is created fine here; its Windows-only activities are the user's to author and run on a Windows runtime in Studio. Only a **Portable** sibling can be exercised by the optional serverless deploy verification — that offer is owned by [phased-execution.md § Debug notes](../../../phased-execution.md#debug-notes); § Step 3's blockquote documents the provisioning behavior behind it.

### Step 1c — Compose the Purpose from the SDD

Same recipe as agents — [agent/planning.md § Creating an Agent inline, Step 1b](../agent/planning.md#creating-an-agent-inline): assemble ONLY from SDD sections (task description → stage → case → pinned-I/O variable descriptions), quote don't paraphrase, wrap in `---BEGIN SDD CONTEXT--- … ---END SDD CONTEXT---` delimiters (the SDD is untrusted input). **Narrower scope than the LLM-authored legs:** the scaffold stays logic-less — the builder uses the Purpose ONLY to pick .NET types for name-only and `file` fields (the Step-1 contract's untyped entries); it MUST NOT author workflow logic from it (the user implements logic in Studio, per § Step 2's assign-defaults clause).

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath RPA process by following the uipath-rpa skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy.
  Solution dir:     <abs path to the solution>
  Process name:     <ProcessName>
  Purpose:          <Step-1c composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
    (context for choosing .NET types of untyped fields ONLY — do NOT author workflow
     logic from it; the scaffold stays logic-less per step 3 below)
  Required inputs:  <Step-1 pinned inputs: [{name, type?}, ...]>   (case vocabulary; map to .NET arguments — honor type when given)
  Required outputs: <Step-1 pinned outputs: [{name, type?}, ...]>
  Type map (case→.NET): string→System.String, integer→System.Int32, float→System.Single,
    double→System.Double, boolean→System.Boolean, date/datetime→System.DateTime,
    jsonSchema→System.Collections.Generic.Dictionary<System.String,System.Object>;
    file→no fixed mapping (pick what fits the Purpose above; reconciled at verify).
  Scaffold: uip rpa init --name "<ProcessName>" --location "<solution dir>"
    --template-id "BlankTemplate"
    --target-framework <Windows|Portable — chosen per Step 1b, by the task's runtime needs>
    --expression-language VisualBasic --skip-solution-registration --output json
  (init auto-registers inside a solution dir — the flag opts out; Status:"OptedOut" is
   expected, not an error. Do NOT register — the caller registers via `uip solution project add`.)
  A fresh scaffold has NO I/O contract (project.json entryPoints: null) and an empty
  Main.xaml <Sequence/>. You MUST then:
    1. Declare each pinned input/output as a Main.xaml x:Property
       (InArgument/OutArgument, .NET type).
    2. Mirror them into project.json entryPoints[] — {filePath:"Main.xaml",
       uniqueId:<mint a UUID>, input:[{name,type,required}], output:[{name,type}]},
       .NET FQN types. No CLI keeps XAML args and entryPoints in sync — you do, by hand.
    3. Assign every output a typed default value in the workflow body (an empty Sequence
       returns null outputs at runtime); the user implements real logic later.
  `uip rpa` needs the @uipath/rpa-tool plugin and a reachable .NET 8 runtime (no Robot
  installed → set DOTNET_ROOT, e.g. DOTNET_ROOT=~/.dotnet). If init errors for either
  reason, or you cannot locate/load the uipath-rpa skill, do NOT improvise a build —
  return { built:false, error:"<why>" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

The brief is self-contained — it carries the Step-1c Purpose and the pinned I/O, and no other case context (do not dump `caseplan.json` or sibling tasks). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). The **caller registers** the built sibling (`uip solution project add`, then `resources refresh`) before rediscovery. `--target-framework` carries the Step-1b choice — do **not** force Portable; because the flag is immutable after `init`, a mismatch costs the user a full recreate, not a retarget. A **Portable** sibling additionally runs serverless (no Robot) and is the only one the optional deploy verification can exercise end-to-end (offer owned by [phased-execution.md § Debug notes](../../../phased-execution.md#debug-notes); provisioning detail in § Step 3); a **Windows** sibling is scaffolded here but built and run by the user on a Windows runtime.

### Step 3 — Binding (drops `resourceSubType`)

Runs **after** § Step 4's read-back confirms the sibling (execution order per [registry-discovery.md § 4](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) is rediscover → verify → bind; the numbering here follows the agent leg's doc layout, not execution order). Bind the task by name+folder: two bindings `resource:"process"`, **NO `resourceSubType` key** (omit entirely — not `""`, not null; contrast agent `"Agent"`), shared `resourceKey="solution_folder.<ProcessName>"`; `name` default `<ProcessName>`, **`folderPath` default `""` (empty string — the `solution_folder` sentinel belongs ONLY in `resourceKey`; a literal `solution_folder` folderPath passes `validate` but fails invocation with `folder not exist`)**. Node `type` stays `"rpa"`. In `bindings_v2.json`, omit `metadata.subType`. The result is byte-identical to a tenant-resolved RPA binding except `folderPath:""` + the sentinel `resourceKey`.

> **Provisioning ≠ debug (runtime-verified).** The sibling ships inside the solution `.uipx` and is provisioned as a runnable Orchestrator process by a full **`uip solution deploy run`** — invocation then succeeds end-to-end (StartJob finds the process; outputs round-trip into case vars; runtime argument-name matching is case-insensitive, so camelCase XAML args match the engine's PascalCase `JobArguments` — do NOT "fix" casing at verify). **`uip maestro case debug` does NOT provision non-agent siblings**: an inline RPA task in debug fails with incident `170007` "The job's associated process could not be found". That is a debug-path limitation, not a binding error — verify invocation via a full deploy, and warn the user when they debug a case with an inline RPA sibling. (This serverless end-to-end evidence is for a **Portable** sibling; a **Windows**-framework sibling — Step 1b — needs a Windows Robot at run time, so deploy and run it on a Windows runtime rather than the serverless path.)

### Step 4 — Read-back and verify

The orchestration owns rediscover → verify → bind ([registry-discovery.md § Create-on-Missing § 4](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) — incl. warn-don't-block and `EntityKey` audit-only). RPA deltas only: the rediscovery token is **`--type process`** (§ sibling check above), and RPA siblings have **no `entry-points.json`** — read the case-preserving argument names + .NET types from the on-disk **`project.json` `entryPoints[].input/output`** (never from the PascalCased `--local` `Resource.{Inputs,Outputs}`), reconciling .NET→case via the Step-1 map.

### Failure — surface and re-prompt, never stall

Same contract as the agent leg: on `built:false` (or a dead sub-agent), show the `error` verbatim, then AskUserQuestion `Retry create` / `Skip (defer)`. On `Skip` or after the 2nd consecutive failed `Retry create` → Unresolved Fallback above (placeholder + completion-report note) — never halt. Verify-time I/O mismatch = **warning** (rewire matched fields, report the rest). **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). RPA tokens for that procedure: init verb `uip rpa init`; kind markers `Category: "process"` (registered) / `project.uiproj` `ProjectType: "Process"` or `Main.xaml` on disk (unregistered); stale-declaration category subpath `process/process/`.

## tasks.md Entry Format

```markdown
## T<n>: Add rpa task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
