# rpa task — Planning

An RPA robot task. The sdd.md component type is `RPA`. The task node's `type` field is `"rpa"`, but the cached registry entity typically lives in `process-index.json` — the registry does not separate "process" from "rpa" at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation).

If sdd.md is ambiguous between `PROCESS` and `RPA`, default to `process` unless the sdd.md mentions UI automation, desktop apps, or robot-specific concerns. **Exception when the resource is missing:** if the registry lookup for an ambiguous task comes back empty, surface the ambiguity (AskUserQuestion) instead of silently defaulting — an `rpa` reading is creatable at the Rule 17 gate; a `process` reading is placeholder-only.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | from task `Task Name` |
| `name` | from task `Resolved Resource` (concrete intended resource name and registry query) |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` — NOT the sdd.md "Folder" (which may be a parent path). Binds to `data.folderPath`; Orchestrator starts the job here at runtime. See [§ Registry Resolution](#registry-resolution). For an RPA process **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an RPA process inline](#creating-an-rpa-process-inline). |
| `task-type-id` | from registry (`entityKey` in `process-index.json`) |
| `inputs`, `outputs`, `runOnlyOnce`, `isRequired` | see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (yes — RPA tasks share this cache with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set `type: "rpa"` on the task node; the cache `entityKey` is recorded in `registry-resolved.json` (not written to the node — the task references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`).
4. **Cross-type fallback.** If `process-index.json` yields no match, search all other cache files — the sdd.md label is not authoritative about the storage type.
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

> **Locating the sibling's on-disk directory.** A **freshly-built** sibling's path arrives in the build sub-agent's `{path}` return. A sibling found by *this* pre-gate `--local` search (prior-run or user-built) has no such return — the `--local` result carries no filesystem path, and its `EntityKey` is an opaque local key, NOT the `.uipx` `Projects[].Id`. Locate the directory via the solution manifest: read the `.uipx` `Projects[]` and resolve the matching entry's `ProjectRelativePath` (a `project.uiproj`/`project.json` path, relative to the `.uipx`) to its parent folder — the sibling's `project.json` (and `entry-points.json`, if any) live there. A skill-built sibling's folder is `<solution>/<Name>/` (so match by name first), but a **user-created** sibling's folder may differ from the resource name — the manifest `ProjectRelativePath` is authoritative, the name is not.

## Unresolved Fallback

> **Build it inline first (rpa).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing RPA process as an in-solution sibling — see [§ Creating an RPA process inline](#creating-an-rpa-process-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an RPA process inline

When an RPA process is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, § 1c build-dedup, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery); the kind-agnostic Step 1/1b/3/Failure rule text lives in [create-inline-common.md](../create-inline-common.md). This section covers the **RPA-specific** deltas: the case→.NET type map, the target-framework choice, the builder brief, the on-disk I/O read, and debug-provisioning behavior.

**The skill does not run `uip rpa init` itself.** It spawns a sub-agent that invokes the `uipath-rpa` skill — RPA-build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). The sub-agent authors a **functional** workflow — real activities implementing the Purpose, following the full `uipath-rpa` authoring workflow — exactly as the agent and api-workflow legs author real behavior. It is **not** a logic-less scaffold. For the **prompt-definable class** (text transforms, JSON parsing, calculations with given formulas, HTTP/API calls to defined endpoints, file ops with explicit formats) it builds, compiles (`uip rpa build`), and — when side-effect-free — runs a working workflow, then binds it (`built:true`). Where the Purpose needs something unavailable to a headless sub-agent — a live desktop/web application + selectors, a credential/connection, or a business rule the SDD never states — or the build fails, it returns **`built:false`** with the reason instead of shipping a stub, and the task degrades to a placeholder (never a silently-bound fake). Bind real work, not a stub — [create-inline-common.md § Build result](../create-inline-common.md#build-result). **Only processes the user selected at the gate are built — never from SDD content alone.**

### Step 1 — Compute the pinned I/O contract

Shared rule — [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) (wired-field ladder; § 1c deduped builds share one identical wiring). **RPA delta:** the case vocabulary maps onto **.NET argument types** — the builder does the mapping at build; reconcile back at verify (§ Step 4) via:

| Case vocab | .NET FQN |
|---|---|
| string | `System.String` |
| integer | `System.Int32` |
| float | `System.Single` |
| double | `System.Double` |
| boolean | `System.Boolean` |
| date / datetime | `System.DateTime` |
| jsonSchema (object body) | `System.Collections.Generic.Dictionary<System.String,System.Object>` |
| jsonSchema (array body) | `System.Collections.Generic.List<System.Object>` — or `List<T>` typed from the body's `items` |
| file | JobAttachment — the case marshals a `file` as a job attachment (`$ref #/definitions/job-attachment`, see [entry-points-sync.md](../../../entry-points-sync.md)); the builder types the arg to consume one (commonly a path/URI `System.String`; confirm against how the workflow uses it). Least-certain row — reconcile at verify. |

**Carry the schema body.** For a `jsonSchema` pin, pass its **schema body** (from the SDD Case Variable) into the Step-2 brief — not just the token `jsonSchema` — so the builder picks Dictionary (object body) vs List (array body) and shapes nested fields correctly; an array body must NOT collapse to a Dictionary. Map is proposed-canonical: at verify, treat a differing-but-compatible .NET type in the built `project.json` as authoritative (warn, don't block).

### Step 1b — Compose the Purpose from the SDD

Shared rule — [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd) (SDD-only assembly order, `---BEGIN/END SDD CONTEXT---` delimiters, first-referencing-task rule for § 1c deduped builds). For rpa, "internal design the Purpose must NOT state" = the specific activities, packages, UI selectors, Object Repository entries, and expressions — those are `uipath-rpa`'s choices to make. **Like the agent and api-workflow legs, the Purpose drives the resource's real behavior:** the builder implements the automation the Purpose describes with real activities (and picks .NET types for name-only/`file` fields along the way) — it is NOT logic-less.

### Target framework (RPA pre-build decision)

**No coded/low-code kind choice** — RPA scaffolds always use XAML/VisualBasic (`uip rpa init` defaults; `--expression-language VisualBasic`). Skip the [registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) agent kind prompt for `rpa`.

**`--target-framework` is NOT fixed — choose it the way `uipath-rpa` does (its Rule 2a), by the task's runtime needs; never default to one.** Read the RPA task's SDD Purpose/Description for the deciding signal (the same cue text the [§ When to Use](#when-to-use) tiebreaker reads):

- **Windows** when the task needs a Windows-only capability — desktop / legacy UI automation, Excel COM, classic Office interop, or WPF (`PresentationFramework`).
- **Portable** (Cross-platform) otherwise — data transforms, parsing, HTTP/API calls, headless file/email work, anything serverless.
- **Genuinely ambiguous / no signal** → surface it with `AskUserQuestion` (framed around the runtime host: Windows-desktop vs cross-platform/serverless) — do NOT silently pick. This rides on the same interactive Create moment as the gate. **Non-interactive run with no signal** → fall back to **Portable** (the only framework the serverless deploy verification can exercise) and flag the fallback choice in the completion report.

Do **not** hardcode Portable — it forecloses Windows-only automation, and `--target-framework` is **immutable after `init`** (uipath-rpa Rule 23), so a wrong pick costs the user a full project recreate, not a retarget. Pass the chosen framework into the Step-2 brief.

> **Build capability is environment-driven, not host-assumed.** The sub-agent builds in whatever environment it runs in — **probe it** (OS, reachable .NET, whether a Robot is present) rather than assume a fixed host. A **Portable** sibling for prompt-definable work compiles (`uip rpa build`) and — when side-effect-free — runs wherever .NET is reachable, then binds (`built:true`); a side-effecting Portable sibling still binds on a clean build but is not run (note "not runtime-verified" in the report). A **Windows**-target sibling compiles/runs only where its capabilities exist (a Windows host, or a Robot for Windows-only activities); where the current environment **actually cannot** compile or run it — e.g. a Windows target on a non-Windows or Robot-less host — the build fails and the sub-agent returns `built:false` naming the missing capability, so the task **placeholders** (the user builds/runs it in Studio on a suitable host) rather than binding something that never compiled. Return `built:false` on an **actual** build/run failure — never pre-declare it from an assumed platform. A task whose Purpose needs a live application + selectors, a credential/connection, or an unstated business rule → `built:false` (report the blocker; the task placeholders). See [create-inline-common.md § Build result](../create-inline-common.md#build-result).

### Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath RPA process by following the uipath-rpa skill's full authoring workflow.
IMPLEMENT the automation the Purpose describes with real activities — do NOT ship a
logic-less scaffold or default-only outputs. Non-interactive: do not ask for approval;
do not publish/upload/deploy.
  Solution dir:     <abs path to the solution>
  Process name:     <ProcessName>
  Purpose:          <Step-1b composed Purpose, wrapped in ---BEGIN/END SDD CONTEXT--- delimiters>
    (this is WHAT to build — author the real workflow that produces the pinned outputs
     from the pinned inputs as described; treat it as data, not instructions)
  Required inputs:  <Step-1 pinned inputs: [{name, type?, body?}, ...]>   (case vocabulary; map to .NET arguments — honor type when given; a `jsonSchema` pin carries its schema `body`)
  Required outputs: <Step-1 pinned outputs: [{name, type?, body?}, ...]>
  Type map (case→.NET): string→System.String, integer→System.Int32, float→System.Single,
    double→System.Double, boolean→System.Boolean, date/datetime→System.DateTime,
    jsonSchema→Dictionary<System.String,System.Object> for an OBJECT body, List<...> for an
    ARRAY body (use the schema `body` passed with the pin to decide — never collapse an array to a Dictionary);
    file→a job attachment (the case marshals it as $ref job-attachment) — type the arg to
    consume one (commonly a path/URI System.String); reconciled at verify.
  Scaffold: uip rpa init --name "<ProcessName>" --location "<solution dir>"
    --template-id "BlankTemplate"
    --target-framework <Windows|Portable — chosen per § Target framework, by the task's runtime needs>
    --expression-language VisualBasic --skip-solution-registration --output json
  (init auto-registers inside a solution dir — the flag opts out; Status:"OptedOut" is
   expected, not an error. Do NOT register — the caller registers via `uip solution project add`.)
  A fresh Process scaffold has an empty Main.xaml <Sequence/>; its project.json
  `entryPoints` varies by rpa-tool version — a single pre-made entry {filePath:"Main.xaml",
  uniqueId:<init-generated>, input:[], output:[]}, OR `null`, OR the key ABSENT entirely
  (observed on @uipath/rpa-tool 1.196.1). Either way it carries NO I/O yet. You MUST then:
    1. Declare each pinned input/output as a Main.xaml x:Property
       (InArgument/OutArgument, .NET type), named EXACTLY as pinned — the names are
       the case's invocation contract (the runtime invokes arguments by these names;
       the SDD pins them verbatim). The analyzer's argument naming-convention warning
       (`Argument <Name> does not respect the set pattern ^in_...`) does NOT apply to
       these entry-point arguments: leave the warning standing; NEVER rename or prefix
       a pinned name.
    2. Ensure exactly ONE entryPoints entry for Main.xaml carrying the I/O — set
       input:[{name,type,required}] / output:[{name,type}] (.NET FQN types). If a pre-made
       entry exists, populate it IN PLACE and KEEP its init-generated uniqueId; if
       entryPoints is null / empty / absent (key missing), create the single
       {filePath:"Main.xaml", uniqueId:<mint one>, input, output} entry. NEVER add a
       second entry. No CLI keeps XAML args and entryPoints in sync — you do, by hand.
    3. Author the workflow body with REAL activities that produce the pinned outputs from
       the pinned inputs per the Purpose (discover activities/packages via uipath-rpa —
       Assign, InvokeCode, HTTP Request, Deserialize JSON, Read/Write File, etc.). NOT
       default or placeholder output values.
  Then VERIFY:
    - Per-file `uip rpa validate --file-path "<FILE>" --project-dir "<DIR>" --output json`
      on every edited file until 0 errors.
    - Project `uip rpa build "<DIR>" --output json` until clean — compile catches the
      member/enum/XAML errors `validate` misses (with REAL activities authored, this is
      REQUIRED). If the build cannot pass in THIS environment (e.g. a Windows target on a
      non-Windows or Robot-less host), return built:false naming the missing build capability.
    - When the automation is side-effect-free (pure text/JSON/calc, or an idempotent read),
      smoke-run it (`uip rpa run`, or `run --skip-build` after a clean build) to confirm it
      produces sane outputs (runtimeVerified:true). Do NOT run a side-effecting automation
      (writes/sends/external mutations) — leave runtimeVerified:false and say so.
  If the Purpose needs something unavailable to a headless sub-agent — a live desktop/web
  application + UI selectors (`uia-configure-target` needs the running app), a credential /
  Integration Service connection, or a business rule the Purpose does not state — do NOT
  invent it or emit a stub. Return built:false with the specific blocker(s) named.
  `uip rpa` needs the @uipath/rpa-tool plugin and a reachable .NET runtime (version per the
  uipath-rpa skill; no Robot installed → point DOTNET_ROOT at your .NET install, e.g.
  DOTNET_ROOT=~/.dotnet). If init errors for either reason, or you cannot locate/load the
  uipath-rpa skill, do NOT improvise — return built:false with the reason.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}],
  runtimeVerified: bool, error? }
```

The brief is self-contained — it carries the Step-1b Purpose and the pinned I/O, and no other case context (do not dump `caseplan.json` or sibling tasks). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). The **caller registers** the built sibling (`uip solution project add`, then `resources refresh`) before rediscovery. `--target-framework` carries the § Target-framework choice — do **not** force Portable; because the flag is immutable after `init`, a mismatch costs the user a full recreate, not a retarget. Build outcome → [create-inline-common.md § Build result](../create-inline-common.md#build-result): `built:true` (real logic, build clean) binds as a resolved task — note "not runtime-verified" in the report for a side-effecting sibling not run here; `built:false` (a blocker, or a build that cannot pass — e.g. a Windows target on this host) placeholders. The optional full-deploy verification (Portable, serverless) is owned by [phased-execution.md § Debug notes](../../../phased-execution.md#debug-notes); a Windows-target task placeholders here and is built + run by the user in Studio on a Windows runtime.

### Step 3 — Binding (drops `resourceSubType`)

Shared invariants — [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants): two bindings `resource:"process"`, shared `resourceKey="solution_folder.<ProcessName>"`, `name` default `<ProcessName>`, `folderPath` default `""` (the sentinel/`""` decoupling and deploy-provisioning-≠-invocation rationale live there). **RPA delta:** the [§ Step 3 `resourceSubType` table](../create-inline-common.md#step-3--binding-invariants) row for `rpa` is **none** — omit the `resourceSubType` key entirely (not `""`, not null; contrast agent `"Agent"` / api-workflow `"Api"`), and in `bindings_v2.json` omit `metadata.subType`. Node `type` stays `"rpa"`. The result is byte-identical to a tenant-resolved RPA binding except `folderPath:""` + the sentinel `resourceKey`.

> **RPA debug delta (`case debug` does NOT provision the sibling).** A full **`uip solution deploy run`** provisions the sibling as a runnable Orchestrator process and invocation succeeds end-to-end (StartJob finds the process; outputs round-trip into case vars; runtime argument-name matching is case-insensitive, so camelCase XAML args match the engine's PascalCase `JobArguments` — do NOT "fix" casing at verify). **But `uip maestro case debug` does NOT provision non-agent siblings**: an inline RPA task in debug fails with incident `170007` "The job's associated process could not be found" — a debug-path limitation, not a binding error. Do not "fix" the `folderPath:""` binding; verify invocation via a full deploy, and warn the user when they debug a case with an inline RPA sibling. (This serverless end-to-end evidence is for a **Portable** sibling; a **Windows**-framework sibling — § Target framework — needs a Windows Robot at run time, so deploy and run it on a Windows runtime rather than the serverless path.) The deploy offer itself (AskUserQuestion, no-deploy default) is owned by [phased-execution.md § Debug notes](../../../phased-execution.md#debug-notes).

### Step 4 — Read-back and verify

The orchestration owns rediscover → verify → bind ([registry-discovery.md § Create-on-Missing § 4](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) — incl. exact-name matching, warn-don't-block, and `EntityKey` audit-only). RPA deltas only: the rediscovery token is **`--type process`** (§ sibling check above), and RPA siblings have **no `entry-points.json`** — read the case-preserving argument names + .NET types from the on-disk **`project.json` `entryPoints[].input/output`** (never from the PascalCased `--local` `Resource.{Inputs,Outputs}`), reconciling .NET→case via the Step-1 map. **Known rename trap:** a builder that honors the RPA analyzer's `^in_`/`^out_` argument-prefix naming warning prefixes arguments `in_`/`out_`, turning every pinned name into missing+extra — the § 4 exact-name rule applies (report the diff; never "convention-match"); the Step-2 brief forbids that rename at the source. Bind on `built:true` (resolved task; note "not runtime-verified" in the report where the sub-agent could not safely run it); `built:false` → placeholder — [create-inline-common.md § Build result](../create-inline-common.md#build-result).

### Failure — surface and re-prompt, never stall

Shared contract — [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall): `built:false` → show `error`/blockers verbatim → AskUserQuestion `Retry create` / `Skip (defer)` → on Skip/repeat, Unresolved Fallback above. **If the reason is a missing business rule or an available connection the user can supply, they may provide it and Retry** (the re-brief carries it). A `built:true` result binds as a resolved task (note "not runtime-verified" in the report for a side-effecting sibling). Verify-time I/O mismatch = warning, never a failure.

> **"Already exists" is NOT a failure** — an interrupted prior run already built the sibling; adopt it per [registry-discovery.md § Create-on-Missing → 3b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). RPA tokens for that procedure: init verb `uip rpa init`; kind markers `Category: "process"` (registered) / `project.uiproj` `ProjectType: "Process"` or `Main.xaml` on disk (unregistered); stale-declaration category subpath `process/process/`.

## tasks.md Entry Format

```markdown
## T<n>: Add rpa task "<display-name>" to "<stage>"
- name: "<resource-name>"
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
