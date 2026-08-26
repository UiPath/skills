# Run a Performance Scenario End-to-End

End-to-end pipeline: take a Test Manager test case that is already linked to
an Orchestrator package, wrap it in a performance scenario as a load group,
run a dry run, and write a persona-tailored perf report from the cumulative
results. Copy-paste safe. Defaults are dry-run-friendly so the first run is
cheap.

## Pipeline

```
uip tm perf-scenario create            → ScenarioKey
uip tm perf-scenario load-groups add   → load group attached
uip tm perf-scenario execute --wait    → polls until terminal, returns results
(optional) perf-scenario results get   → full data bundle (incl. time series)
write report → ./test-report-<persona>-<YYYY-MM-DD>.md
```

All load-group verbs hang off one parent: `load-groups add` / `list` / `update` /
`remove`. There is no `perf-scenario add-testcase` and no
`perf-scenario update-loadgroup` — both exit with `unknown command`.

## Reuse vs. create — pick the right starting step

The three steps above are **idempotent and independent**. Don't blindly
run all three every time the user asks for a perf run. Pick the entry
point based on what the user actually said:

| What the user asked for | Where to start |
|---|---|
| *"Create a perf scenario for SP1:602 and run it"* | Step 2 (create) → Step 3 (`load-groups add`) → Step 4 (execute) |
| *"Run a perf test on SP1:1276"* (gave a `<SCENARIO_KEY>`) | Step 4 only — first `perf-scenario get --scenario-key SP1:1276` to confirm it exists and has at least one load group; skip create + `load-groups add` |
| *"Run the same scenario again with a full execution"* | Step 4 only — reuse the scenario from earlier in the conversation; **do not create a new one** |
| *"Run a perf test on our login test case"* (no scenario-key) | Ask the user: "Do you want me to reuse an existing scenario for this test case, or create a new one?" Then act on the answer. |

> **Never create + `load-groups add` on a scenario that already has load
> groups.** Call `perf-scenario get --scenario-key <KEY>` first — if
> `Data.LoadGroups` is non-empty, the scenario is ready to execute as-is.

> **Never create a new scenario when the user has already given you a
> `SP1:NNNN` key.** That key IS the scenario; jump straight to step 4.

If the user supplies a scenario key but `perf-scenario get` returns "not
found" → that's the only case where you go back and create.

### Picking dry-run vs full when a scenario already exists

If the scenario already exists AND the user asks for a full
`--execution-type performanceTesting` run:

1. **First** check whether a dry run has already passed for this scenario.
   - If you (the agent) executed a successful dry run earlier in this
     session, you know it has → skip the dry-run step.
   - If you don't know, run a dry run first (it's cheap, ~1–2 min).
2. **Then** run `--execution-type performanceTesting --wait`.

If the Perf Service rejects the full run with *"No dry run reports found"*
or similar, fall back to running a dry run, then retry.
`uip tm perf-scenario list-dry-run-reports --scenario-key <KEY>` is the
programmatic source of truth — `Data.HasPassingDryRun: true` means a full
run can go ahead without burning a fresh dry run.

## Prerequisites

- Logged in: `uip login status --output json`. If not, `uip login`.
- Token has the perf scopes: `TM.PerformanceScenarios`,
  `TM.PerformanceScenarioExecutions`, `PerfService` (in addition to
  `TestmanagerApiUserAccess`). If `uip login` was performed before these
  were added to the CLI, run `uip logout && uip login` to refresh.
- A Test Manager project (e.g. `SP1`).
- A test case in that project (e.g. `SP1:602`) **already linked** to an
  Orchestrator package — see [publish-and-link-guide.md](publish-and-link-guide.md)
  for the link flow if not.
- A Performance Testing runtime allocated to the folder where the package
  lives. Without it `perf-scenario execute` fails with HTTP 400 *Insufficient
  Performance Testing runtimes available*.

## Step 1 — Discover inputs

The discovery commands are shared with the standard test pipeline. **Cross-link**
to [publish-and-link-guide.md](publish-and-link-guide.md) Steps 3–4 — do not
duplicate that material here. The values you need from those steps are:

| Variable | Where to get it |
|---|---|
| `<PROJECT_KEY>` | `uip tm project list --output json` |
| `<TEST_CASE_KEY>` (`PROJECT_KEY:NUMBER`) | `uip tm testcases list --project-key <PROJECT_KEY> --output json` → `ObjKey` |
| `<FOLDER_KEY>` (UUID) | `uip or folders list --output json` → `Key` |
| `<PACKAGE_NAME>` | `uip tm testcases list --project-key <PROJECT_KEY> --output json` → `PackageName` (legacy entry-point links expose it here even when `IsAutomated` is `false`), or `uip tm testcases list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json` → `PackageName` |

## Step 2 — Create the scenario

```bash
uip tm perf-scenario create \
  --project-key <PROJECT_KEY> \
  --name "<SCENARIO_NAME>" \
  --description "<OPTIONAL_DESCRIPTION>" \
  --version 1.0 \
  --output json
```

Capture `Data.ScenarioKey` from the response (e.g. `SP1:1133`). It is the
handle you'll use for every subsequent scenario command.

Optional metadata flags (all have sensible defaults):

| Flag | Default | Allowed values |
|---|---|---|
| `--app-type` | `web` | `web` / `apiService` / `ecommerce` / `gaming` / `financial` / `healthcare` / `saaS` / `streaming` / `messaging` / `enterprise` |
| `--perf-test-type` | `loadTesting` | `loadTesting` / `stressTesting` / `enduranceTesting` / `spikeTesting` |
| `--responsiveness` | `fast` | `instant` / `fast` / `moderate` / `slow` / `verySlow` |

These three are scenario **metadata** (they label the workload and set the
service's responsiveness expectation). They do **not** decide which metrics
a run produces — that comes from each load group's system-under-test type
(see Step 5b).

## Step 3 — Add the test case as a load group

```bash
uip tm perf-scenario load-groups add \
  --scenario-key <SCENARIO_KEY> \
  --test-case-key <TEST_CASE_KEY> \
  --folder-key <FOLDER_KEY> \
  --package-name <PACKAGE_NAME> \
  --output json
  # --package-version 14.4   # optional; auto-resolves to the latest published version when omitted
```

**Always omit `--package-version` unless the user explicitly asked to pin
one.** The CLI fetches every published version of the package in the folder
and picks the highest one, log line `Using latest version '14.4'`. Pinning
is a footgun — running yesterday's version against today's APIs hides the
bug you actually want the perf run to expose.

Optional load profile flags (defaults are dry-run-friendly — keep them for
a smoke run and only override when the user wants real load):

| Flag | Default | Server constraint |
|---|---|---|
| `--virtual-users <n>` | `1` | — |
| `--ramp-up-minutes <n>` | `0` | — |
| `--peak-minutes <n>` | `1` | — |
| `--ramp-down-minutes <n>` | `0` | — |
| `--delay-minutes <n>` | `0` | — |
| `--max-response-time-ms <ms>` | `100` | server requires `>= 100` |
| `--max-error-rate <rate>` | `0.0001` | server requires `>= 0.0001` |
| `--robot-type <type>` | `standard` | `standard` / `template` / `elasticRobotPool` / `cloudRobotVm` / `serverless` |

The project is derived from the `--scenario-key` prefix, so `load-groups add`
takes no `--project-key`.

You can call `load-groups add` multiple times per scenario to attach multiple
load groups (e.g. login + checkout + payment). Each call returns
`Data.LoadGroupId` (`Code: LoadGroupAdd`) — the **scenario** load-group UUID
that `load-groups update` and `load-groups remove` take.

### Removing a load group

```bash
uip tm perf-scenario load-groups remove \
  --load-group-id <LOAD_GROUP_ID> \
  --project-key <PROJECT_KEY> \
  --output json
```

Detaches the load group from the scenario; the test case and every past
execution's data stay intact. `--project-key` is REQUIRED here (a bare UUID
carries no project prefix). **Confirm the load group with the user first** —
re-adding it means re-supplying folder, package, and the whole load profile.
A bad id fails on the read before anything is deleted, so a `Success`
envelope means the load group really was removed.

## Step 4 — Run + wait

```bash
uip tm perf-scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --wait \
  --execution-type dryRun \
  --poll-interval-sec 12 \
  --timeout-sec 1800 \
  --output json
```

**Execution modes:**

| `--execution-type` | When to use |
|---|---|
| `dryRun` (default) | Smoke / first-time validation. Fast (~1–2 min). 1 VU regardless of load-profile flags. Server emits a recommended-multiplexing-factor at the end. |
| `performanceTesting` | Full load run that honours every load-profile flag you set on the load groups (`--virtual-users`, `--ramp-up-minutes`, `--peak-minutes`, `--ramp-down-minutes`, etc.). Can take many minutes; bump `--timeout-sec` accordingly. |

> **Default to `dryRun`** unless the user explicitly asks for a full load
> run, OR a previous dry run finished cleanly and they want a real
> measurement. Performance Testing consumes scarce perf runtimes (often
> only 1 per folder) — don't burn one on a smoke check.

> ⚠️ **Full execution requires a prior successful dry run** — but the
> agent's behaviour depends on whether the scenario / load group is new
> or pre-existing. **Don't pre-emptively dry-run an existing scenario
> the user expects to be ready.**
>
> Decision tree when the user asks for a full / `performanceTesting`
> run:
>
> 1. **You just created the scenario this turn**, OR you just attached
>    the load group this turn → **a dry run cannot exist yet**. Run dry
>    run first (`--execution-type dryRun --wait`), then confirm load
>    profile, then full.
> 2. **The user supplied an existing `<SCENARIO_KEY>` or the scenario
>    has load groups already attached** → **assume a dry run already
>    exists**. Confirm load profile, then attempt full directly. If the
>    server returns HTTP 400 *"No dry run reports found"* (or similar)
>    → fall back to dry run + full retry, only then.
> 3. **If unsure**: call `perf-scenario list-dry-run-reports` to verify a
>    passing dry-run report exists before deciding.
> 4. **Never run a dry run pre-emptively when the user explicitly asked
>    for a full run on an existing scenario** unless step 2's fallback
>    kicks in. The user's intent is the full run; respect it.
>
> `uip tm perf-scenario list-dry-run-reports --scenario-key <KEY>` gives the
> agent a programmatic way to verify a passing dry-run report exists
> without burning a fresh dry run. Read `Data.HasPassingDryRun` (and
> `Data.Reports[].RecommendedMultiplexingFactor` for the on-prem scaling
> hint). It fails outright when the scenario has no load groups — attach
> one via `load-groups add` first.
>
> ⚠️ **`list-dry-run-reports` only works for test cases that have an
> `automationId` set.** Test cases linked via the older
> `packageEntryPointUniqueId` mechanism (the legacy
> `tm testcases link-automation --package-name X --test-name Y` flow)
> return `automationId: null` and the perf service rejects the request
> with *"Automation Runtime Pairs is missing"*. In that case, the
> agent's correct fallback is the **try-then-fallback** pattern:
> attempt `performanceTesting` directly → if rejected with HTTP 400
> "No dry run reports found", run a dry run, then retry.

### ⚠️ `IsAutomated: false` does NOT mean "no automation linked"

Test cases can be linked to a package two ways: the modern `automationId` link
(shows `IsAutomated: true`) or the **legacy entry-point link** (`packageIdentifier`
+ `packageEntryPointName` stored on the record). Legacy-linked test cases show
`IsAutomated: false` but still carry their package — **read `PackageName` and
`PackageEntryPoint` from the `testcases list` output** (the same values the TM UI
shows as "Package Name") and use that package for the load group without asking.
**Never tell the user a test case "has no automation" based on `IsAutomated: false`
alone.** Only ask for a package when `PackageName` is genuinely empty; if the user
names one, trust it — do not re-link.

### ⚠️ Two landmines: package version and multiplexing factor

- **Never pin the Orchestrator/NuGet build number as `--package-version`** (e.g.
  `1.0.234622513`). Test Manager registers perf entry points under the package's
  **app version** (e.g. `1.0`); pinning the NuGet build makes the perf service's
  entry-point lookup 404 at execution time. Omit `--package-version` (auto-resolve
  picks the right app version) or pass the app version only. If the user supplies a
  long build-style version, treat it as the build of the app version — do not pin it.
- **Never set `--multiplexing-factor` on serverless load groups.** The dry run's
  `Recommended multiplexing factor: N` applies to on-prem/machine robots ONLY;
  serverless scales by virtual users directly. The server rejects any value > 0
  ("on prem only") AND rejects 0 ("must be greater than 0"), and
  `load-groups update` re-sends the stored value — so once set, the load group
  cannot be un-poisoned; remove it (`load-groups remove`) and add it back.
  Only mention the recommended factor to the user if they run on-prem robots.

### Two-phase rule: dry run ignores the load profile, full run honours it

| Phase | Uses load-group config? | Required precondition |
|---|---|---|
| `dryRun` | **No.** Always 1 VU with a fixed short profile; the server probes the automation and emits a `Recommended multiplexing factor: N`. `--virtual-users`, `--ramp-up-minutes`, `--peak-minutes`, `--ramp-down-minutes`, SLO thresholds — all ignored. | None — can be the first run. |
| `performanceTesting` (full) | **Yes.** Honours every load-profile field on each load group. | At least one successful dry run must exist for this scenario. |

The practical consequences for the agent:

- **Don't ask the user about the load profile *before* the dry run.** Those
  values don't take effect there. Just run the dry run with whatever's
  currently configured (or with one fresh `load-groups add` if no load
  group exists yet) — the actual values don't matter.
- **Don't call `load-groups update` *before* the dry run.** Same reason.
- **DO ask the user about the load profile AFTER the dry run, BEFORE the
  full run.** That's the moment the values matter.

### ⚠️ Confirm the load profile with the user BEFORE the full run (not before dry run)

Server-side stored defaults for `virtualUsers`, `rampUpTimeMinutes`,
`peakTimeMinutes`, `rampDownTimeMinutes`,
`maximumResponseTimeMilliseconds`, and `maximumErrorRate` cannot be
trusted to match what the user wants. Different add paths set different
defaults; the perf service has been observed storing values like `VU=20`
or `MaxErrorRate=1.0` regardless of what the CLI sent.

Once the dry run is done (or already on file), the sequence for the
full run is:

1. **Inspect** the current load profile:
   ```bash
   uip tm perf-scenario get --scenario-key <SCENARIO_KEY> --output json
   ```
   Read each `Data.LoadGroups[i]` row — `LoadGroupId` there is the id
   `load-groups update` takes.

2. **Ask the user** to confirm or override each of these for **every**
   load group:

   | Parameter | Flag on `load-groups update` | Typical range |
   |---|---|---|
   | Virtual users | `--virtual-users <n>` | 1 (dry-run) → many (full) |
   | Ramp-up minutes | `--ramp-up-minutes <n>` | 0 → 5+ |
   | Peak minutes | `--peak-minutes <n>` | 1 → 60+ |
   | Ramp-down minutes | `--ramp-down-minutes <n>` | 0 → 5+ |
   | Delay minutes | `--delay-minutes <n>` | 0 |
   | Max response time (ms) | `--max-response-time-ms <ms>` | server min: 100 |
   | Max error rate | `--max-error-rate <rate>` | server min: 0.0001 |
   | Multiplexing factor | `--multiplexing-factor <n>` | use the value the dry run recommended |
   | Robot type | `--robot-type <type>` | `standard` / `template` / `elasticRobotPool` / `cloudRobotVm` / `serverless` |

   Use the multiplexing factor the dry run printed in
   `Recommended multiplexing factor: N` — that's the server's own
   guidance on a safe scaling factor.

3. **Apply** any user-requested changes:
   ```bash
   uip tm perf-scenario load-groups update \
     --load-group-id <LG_UUID> \
     --project-key <PROJECT_KEY> \
     --virtual-users <n> \
     --ramp-up-minutes <n> \
     --peak-minutes <n> \
     --ramp-down-minutes <n> \
     --max-response-time-ms <ms> \
     --max-error-rate <rate> \
     --multiplexing-factor <n> \
     --output json
   ```
   `load-groups update` is a true partial update — flags you omit are
   preserved from the current server state. `--project-key` is REQUIRED
   (the load-group UUID has no prefix to derive it from). Pass the
   scenario load-group UUID, **not** the per-execution id from
   `load-groups list`.

4. **Re-read** to confirm the update landed (optional sanity check):
   ```bash
   uip tm perf-scenario get --scenario-key <SCENARIO_KEY> --output json
   ```

5. **Then** submit the full run.

If the user says *"just use defaults"* — still surface the current
stored values from `perf-scenario get` and ask if they're acceptable. **Do
not silently fire `performanceTesting` against possibly-wrong
parameters.** A full perf run consumes scarce perf runtimes and produces
data that may be useless if the load profile is wrong.

### Concrete sequence — full execution end-to-end

The required 3-call chain when the user asks for a full run on an
**existing scenario with load groups already attached**:

```bash
# 1. Confirm scenario exists + has load groups (skip create / load-groups add)
uip tm perf-scenario get --scenario-key <SCENARIO_KEY> --output json

# 2. Dry run — required precondition for a full run
uip tm perf-scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --execution-type dryRun \
  --wait \
  --output json
# → confirm the 'ended with the status' application log reports 'Finished'

# 3. Full performance run — honours load-profile flags on the load groups
uip tm perf-scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --execution-type performanceTesting \
  --wait \
  --timeout-sec 3600 \
  --output json
```

The full run typically takes 5–30 min depending on load-profile (virtual
users, ramp-up, peak duration). Bump `--timeout-sec` accordingly — the
default `1800` (30 min) is usually fine, but a 1 hr peak-time scenario
needs ~3600.

### Running without `--wait` (kick-and-poll-later)

`--wait` is **optional**. If you only need the `ExecutionId` to track the
run elsewhere — UI, CI step boundary, another script — omit it. The
command returns immediately:

```bash
uip tm perf-scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --execution-type dryRun \
  --output json
# → { "Result": "Success", "Data": { "ExecutionId": "<uuid>", "ExecutionType": "dryRun", "Status": "pending" } }
```

You can then either:

- **Poll yourself** at intervals: `uip tm perf-scenario executions list --project-key <KEY> --scenario-id <SCENARIO_UUID> --output json` and read the execution's `Status` field (values are lower-camel: `pendingAllocation`, `pending`, `running`, `cancelling`, and the terminal `finished` / `cancelled`). Do NOT poll `results get --completed false` for completion — the live payload is cleared when the run finishes, so a grep on live logs never sees the end. Once terminal, fetch the final bundle with `results get --completed true`.
- **Or rejoin the wait later**: re-invoke `execute --wait` is **not** the right rejoin — it'd start a *new* execution. Use `results get` polling for rejoining.

**When to use which mode:**

| Mode | When |
|---|---|
| `--wait` (default flow) | Short interactive runs (dry runs, ≤5 min peak). The CLI handles the poll loop + dedup + post-terminal-log scan for you. |
| No `--wait` (fire-and-forget) | **Long full-load runs (any `performanceTesting` with `peak-minutes > 5` or expected total > 10 min).** Also CI pipelines where the perf run is monitored elsewhere, and multi-scenario parallel kickoffs. |

> ⚠️ **The synchronous-tool-call trap — important for agent-driven flows.**
> `--wait` is a single blocking Bash call from the agent's perspective.
> While it polls (up to `--timeout-sec`, default `1800`), the agent
> **cannot read new user input** — your "cancel that", "wait, change
> X", or any other message is queued and only seen when the command
> exits. For runs longer than ~5 min, this is the wrong pattern.
>
> **Long-run pattern instead (kick + tell + return control):**
>
> ```bash
> # 1. Kick off WITHOUT --wait — returns immediately
> uip tm perf-scenario execute \
>   --scenario-key <SCENARIO_KEY> \
>   --execution-type performanceTesting \
>   --output json
> # → captures ExecutionId from the response
>
> # 2. Hand the ExecutionId back to the user, plus the two follow-up commands:
> #
> #    Check progress at any time (perf-service command — no --project-key):
> #      uip tm perf-scenario executions list \
> #        --project-key <KEY> --scenario-id <SCENARIO_UUID> --output json
> #      uip tm perf-scenario results get \
> #        --execution-id <EXECUTION_ID> --completed false --output json
> #
> #    Cancel the run (from THIS terminal or any other):
> #      uip tm perf-scenario stop \
> #        --execution-id <EXECUTION_ID> --project-key <KEY>
> #
> # 3. Optionally offer to poll periodically on the user's behalf
> #    (e.g. every 60–120s) — but only if the user asks. Each agent
> #    poll is a separate fast Bash call, so the agent remains responsive
> #    to interrupts between polls.
> ```
>
> **Always prefer no-wait for `performanceTesting`** unless the user
> explicitly says "block until done" or the configured peak is very
> short. Use `--wait` for `dryRun` (short by definition).

`--wait` polls the perf service every `--poll-interval-sec` (default `12`)
and exits when an application log reports the run ended (terminal status
`Finished` / `Cancelled`) or `--timeout-sec` (default `1800`, i.e. 30 min;
`0` = wait forever) elapses. On timeout the command exits `2` and names the
`results get` follow-up — the run itself keeps going server-side.

**Prefer `--wait` over a hand-rolled poll loop.** The CLI:

- Dedupes status-change application logs (only prints each new message once).
- Tolerates transient 5xx during long polls.
- Uses the same formatted response shape (`LoadGroups[]` rows) when the
  run finishes — so the consumer of the JSON doesn't need to special-case it.

You'll see a stream like:

```
Resolving scenario 'SP1:1133'
Starting dry-run for scenario 'SP1:1133' (2a1d71d4-…)
Polling execution '141ae747-…' every 12s (timeout 1800s)
[2 logs]  Virtual user provisioning has started. Please wait, this may take some time.
[5 logs]  A virtual user with the index 0 returned with the status 'Running'.
[6 logs]  The 'Response Time' metric has surpassed its defined threshold of 300ms.
[14 logs] A virtual user with the index 0 returned with the status 'Completed'.
[19 logs] The scenario execution has ended with the status 'Finished'.
```

The terminal status is in the application log whose message starts with
`The scenario execution has ended with the status`. **Don't read just the
last entry** — the server appends additional advisory logs after the
terminal status fires (`Recommended multiplexing factor: N` and
`Dry run details: [...]`). Scan `Data.ApplicationLogs[]` for the
`ended with the status` entry to determine the run outcome.

## Step 5 — Read the response

`perf-scenario execute --wait` emits `Code: ScenarioExecutionResults`.
Default (`~6 KB`):

```json
{
  "Result": "Success",
  "Code": "ScenarioExecutionResults",
  "Data": {
    "ExecutionId": "141ae747-1136-0000-071f-0b499e6cd24f",
    "LoadGroupCount": 1,
    "LoadGroups": [
      {
        "LoadGroupId": "a8663d6c-013f-0000-97ba-0b499e6cd267",
        "StartedAt": "2026-05-07T13:00:10.455Z",
        "CumulativeResponseTimeMs": 519.04,
        "MaxResponseTimeMs": 3437,
        "SuccessfulWorkflowCount": 5,
        "FailedWorkflowCount": 0,
        "HttpErrorCount": 0,
        "HttpErrorRate": 0,
        "AutomationErrorCount": 0,
        "AutomationErrorRate": 0,
        "SloViolationReasons": [
          "Response Time has reached 3437ms with the limit of 300ms."
        ]
      }
    ],
    "LogCount": 19,
    "ApplicationLogs": [
      { "CreatedAt": "...", "LogLevel": 1, "ExecutionId": "...", "Message": "..." }
    ]
  }
}
```

Field-by-field (read these directly — **do not recompute from `AggregatedData`**):

| Field | What it means |
|---|---|
| `Data.ExecutionId` | UUID for the run; pass back to `results get` to re-fetch later. |
| `LoadGroupCount` | Count of load groups reported by this execution. |
| `LoadGroups[].LoadGroupId` | The **per-execution** load-group id (the `ExecutionsData` key). Feed it to the errors/metrics commands — **not** to `load-groups update` / `remove`, which want the scenario load-group UUID from `perf-scenario get`. |
| `LoadGroups[].StartedAt` | ISO-8601 start of this load group (UTC). |
| `LoadGroups[].CumulativeResponseTimeMs` | Mean response time across every successful workflow in the group. |
| `LoadGroups[].MaxResponseTimeMs` | Worst single-workflow response time. |
| `LoadGroups[].SuccessfulWorkflowCount` / `FailedWorkflowCount` | Workflow-level pass/fail. |
| `LoadGroups[].HttpErrorRate` / `AutomationErrorRate` | Fractions in `[0,1]`, not percentages. |
| `LoadGroups[].SloViolationReasons[]` | Human-readable strings explaining each SLO breach. **The agent's job is to surface these to the user, not to re-derive them.** |
| `LogCount` | Total application log entries. |
| `ApplicationLogs[]` | Status-change events ordered chronologically. The terminal status is the `ended with the status` entry — **not** necessarily the last one. |

Add `--full` (~50 KB) to `execute --wait` to also include per-load-group
time series:

```bash
uip tm perf-scenario execute --scenario-key <SCENARIO_KEY> --wait --full --output json
```

`--full` adds two arrays per load group:

- `AggregatedData[]` — typically 60 entries with per-time-bucket
  `Cpu`, `Ram`, `VUserCount`, `AvgResponseTimeMs`,
  `P50ResponseTimeMs`, `P90ResponseTimeMs`, `P95ResponseTimeMs`,
  `P99ResponseTimeMs`, `StepTimeMs`, `RequestsPerSecond`, `MilliSeconds`
  (offset from run start), plus the dashed `ExecutionId` of the load group.
  Use this for resource analysis and spike timing.
- `AggregatedDataWithTransaction[]` — per-transaction aggregates; empty for
  runs with no per-transaction breakdown.

> Default ~6 KB vs. `--full` ~50 KB is a meaningful difference if you're
> piping the JSON to an LLM. Only request `--full` for personas that need
> percentile or time-series detail (Performance Engineer, Developer
> drill-down). Skip it for Release Manager summaries.

### Re-fetching after the fact (`results get`)

```bash
uip tm perf-scenario results get \
  --execution-id <EXECUTION_ID> \
  --completed true \
  --output json \
  --query '<JQ_EXPR>'
```

`results get` has **no `--project-key`** and **no `--full`** — it always
returns the raw perf-service bundle, and it is large (hundreds of KB). The
shape differs from `execute --wait`: `Data.ExecutionsData` is a **map** keyed
by per-execution load-group id, each entry carrying `AggregatedData[]`,
`CumulatedValues`, `SloViolationReasons[]`, `AggregatedDataWithTransaction[]`,
plus a top-level `Data.ApplicationLogs[]`. `--completed true` (default) reads
the finished run from the database; `--completed false` reads a live run from
the cache and is cleared once the run ends — never poll it for completion.

**Never print the bundle whole.** Slim it with `--query` (jq expression
applied to `Data`), or write it to a temp file once and extract with a few
targeted `jq` passes. Take each load group's downstream id from the dashed
`ExecutionId` field *inside* its `AggregatedData` entries — the
`ExecutionsData` map key is rendered un-dashed and re-cased.

## Step 5b — Per-transaction (per-API) metrics (`transaction-metrics list`)

The cumulative `LoadGroups[].CumulativeResponseTimeMs` rolls every
transaction together. For a Performance Engineer or Developer who needs to
know *which API call* is slow, fetch the per-transaction breakdown:

```bash
uip tm perf-scenario transaction-metrics list \
  --load-group-id <LOAD_GROUP_ID> \
  --start-time-ms 0 --end-time-ms <RUN_DURATION_MS> \
  --output json
# --start-time-ms / --end-time-ms are REQUIRED (ms offsets from run start);
# a [0,0] window returns no data — use 0 .. run duration for the whole run
```

`<LOAD_GROUP_ID>` is the **per-execution** load-group id — the dashed
`ExecutionId` inside a load group's `AggregatedData` entries (or the `Id`
column of `load-groups list`). It is NOT the scenario load-group UUID that
`load-groups update` / `remove` take. There is no `--project-key` on this
command.

`Data` is a **bare array**, one entry per distinct transaction:

```json
{
  "Result": "Success",
  "Code": "PerfTransactionMetricsList",
  "Data": [
    {
      "TransactionName": "POST /api/login",
      "RequestCount": 42,
      "AvgResponseTimeMs": 187.5,
      "MinResponseTimeMs": 110,
      "MaxResponseTimeMs": 1067,
      "P50ResponseTimeMs": 175,
      "P90ResponseTimeMs": 320,
      "P95ResponseTimeMs": 540,
      "P99ResponseTimeMs": 1010,
      "HttpErrorCount": 0,
      "HttpErrorRate": 0
    }
  ]
}
```

No throughput field is returned — take requests/sec from
`AggregatedData[].RequestsPerSecond` in the bundle instead.

Use this when:

- The cumulative summary shows an SLO violation but you don't know which
  API call is the offender.
- The Performance Engineer report needs per-endpoint p95/p99 — much
  more actionable than the load-group-level rollup.
- You're narrowing down a specific time window inside a long run (pass
  `--start-time-ms` / `--end-time-ms`).

> One row per distinct `TransactionName` observed during the load-group
> execution. No transactions instrumented in the automation → empty
> `Data: []`. If empty, surface that fact to the user rather than
> fabricating per-call metrics from `AggregatedData[]`.

> ⚠️ **`transaction-metrics` only returns rows for load groups whose
> system under test is an API.** Browser and desktop load groups drive the
> application through the UI (browser automation / Windows UIA selectors),
> not by issuing HTTP calls the perf service can intercept — so there are
> no per-API transactions to report. The endpoint returns `200 OK` with
> `Data: []` in that case, **not** an error.
>
> Decision tree before calling `transaction-metrics`:
>
> 1. Run `uip tm perf-scenario load-groups list --project-key <KEY> --execution-id <EXECUTION_ID> --output json`.
> 2. Read each row's `SystemUnderTestType`:
>    - `api` → call `transaction-metrics` for that load group, expect
>      populated rows.
>    - `windowsApplication` (Desktop) or `chrome` / `edge` /
>      `internetExplorer` / `safari` / `opera` / `firefox` / `netscape`
>      (Browser) → **skip `transaction-metrics`** for that load group. Use
>      the `AggregatedData[]` time series from `results get`
>      (`ExecutionsData[*].AggregatedData`) instead (it has `StepTimeMs`,
>      `P95StepTimeMs`, etc. — per-step, not per-API, but the right
>      granularity for UI-driven runs).
>    - `undefined` / `default` → treat as unknown; try the call and expect
>      it may return `[]`.
> 3. The scenario's own `AppType` (`apiService`, `web`, …) from
>    `perf-scenario get` is **metadata, not the determinant** — a scenario
>    labelled `apiService` can still hold browser load groups. Don't decide
>    off `AppType` alone.
> 4. If a Test Manager endpoint (`load-groups list`) is unavailable (e.g.
>    403), call `transaction-metrics` anyway and tell the user upfront that
>    an empty `Data: []` is expected for non-API load groups, not a
>    missing-data bug.

## Step 6 — Generate a perf report

The run is complete and you hold its `ExecutionId` — hand off to the report
workflow, which owns ALL report rules (personas, data rules, markdown/HTML
constraints, chart placeholders, rendering):

**Follow [references/perf-report-guide.md](perf-report-guide.md)**, passing the
`ExecutionId` from Step 4/5. Do not author report content from this guide —
the report guide is the single source of truth for report structure and rules.

Quick mapping of what you already have:
- `ExecutionId` (scenario execution) → the report guide's `--execution-id`.
- Each load group's dashed `ExecutionId` (from `results get`'s
  `ExecutionsData` entries) → the report guide's `--load-group-id`.
- Percentiles → `transaction-metrics list` (never recomputed from time series).

## Analyse More

Same drill-down loop as
[test-result-report-guide.md § Analyse More](test-result-report-guide.md#analyse-more):

1. **Explore** — `uip tm perf-scenario --help` / `uip tm perf-scenario <sub> --help` to
   confirm the right subcommand and its flags.
2. **Execute** — run the command using IDs from the previous response, always
   with `--output json`.
3. **Validate** — if the response is empty or errors, diagnose before
   retrying (max 3 attempts).
4. **Repeat** — if the user asks for deeper detail, identify the next
   command and repeat.

Perf-specific drill-down candidates:

- **Per-transaction (per-API) metrics** when the rollup hides which call
  is slow: `uip tm perf-scenario transaction-metrics list --load-group-id <UUID> --start-time-ms 0 --end-time-ms <durMs>`.
  Returns p50/p90/p95/p99 + request count + HTTP error count *per
  `TransactionName`*. Narrow `--start-time-ms` / `--end-time-ms` to zoom
  into a specific window.
- **Errors for one load group**: `uip tm perf-scenario http-errors list` (per
  request: URL, method, status code, count, response body) and
  `uip tm perf-scenario automation-errors list` — both take the scenario
  `--execution-id`, the load group's `--load-group-id`, and the window flags.
- Re-fetch the same execution's raw bundle: `uip tm perf-scenario results get
  --execution-id <UUID> --completed true --query '<JQ_EXPR>'`.
- Inspect scenario metadata + configured load groups:
  `uip tm perf-scenario get --scenario-key <KEY>` (project is derived from the
  scenario-key prefix — no `--project-key` flag).
- List a scenario's past runs to compare: `uip tm perf-scenario executions
  list --project-key <KEY> --scenario-id <SCENARIO_UUID> --execution-type
  performanceTesting`.
- Cross-reference the linked test case's functional executions:
  `uip tm executions list --project-key <KEY> --test-set-id <ID>` — useful
  when comparing functional vs. perf runs of the same test case.

Stop when: the user is satisfied, the response has no more data, or 3
retries have failed.

## Common pitfalls

- **Kicking off `--execution-type performanceTesting` without a prior
  successful dry run.** The Perf Service refuses the request — the
  scenario must have a passing dry-run report on file first. See Step 4
  for the required sequence (dry-run → confirm Finished → full run).
- **Treating `Data.ApplicationLogs[-1].Message` as the terminal status.**
  The server appends `Recommended multiplexing factor: N` and a `Dry run
  details: […]` summary **after** the `ended with the status` log, so the
  last entry is almost never the one carrying the outcome. Scan for the
  `ended with the status` substring across the array.
- **Running `perf-scenario execute` without first attaching a load group.**
  `perf-scenario create` alone is just metadata; the perf service responds
  with HTTP 404 *Performance Testing Scenario Test Case Configurations does
  not exist* until you've called `load-groups add` at least once.
- **Calling the retired dashed verbs.** `perf-scenario add-testcase` and
  `perf-scenario update-loadgroup` never shipped — they are
  `load-groups add` and `load-groups update`. A dashed call exits non-zero
  with commander's `unknown command`.
- **Passing `--project-key` to a perf-service command.** `results get`,
  `http-errors list`, `automation-errors list`, and `transaction-metrics
  list` don't accept it; `report generate` / `report compare` take it only
  to build the in-app link.
- **Mixing the two load-group id spaces.** `load-groups update` / `remove`
  want the scenario load-group UUID (`perf-scenario get` →
  `LoadGroups[].LoadGroupId`, or `load-groups add` → `Data.LoadGroupId`).
  The errors/metrics commands want the per-execution id (`load-groups list`
  → `Id`, or the dashed `ExecutionId` inside `AggregatedData`).
- **Pinning `--package-version` when the user didn't ask.** The CLI's
  auto-resolve picks the highest published version in the folder — that is
  almost always what you want. Pinning is for the rare reproducer case.
- **Using `execute --wait --full` for a Release Manager report.** The
  60-entry time series is noise for a go/no-go audience. Default payload only.
- **Recomputing cumulative metrics from `AggregatedData[]`.** The server
  already aggregates; reading the per-second buckets and re-summing is
  slower, less accurate, and risks contradicting the server's own values.
  Read `LoadGroups[].CumulativeResponseTimeMs` etc. directly.
- **Fabricating numbers.** Every metric in the report must trace to the
  JSON payload. If a field is missing or empty, say so — do not guess.

## Anti-patterns

- **Do NOT generate a report without asking for the persona** — a Release
  Manager getting raw p99 timelines is noise; a Performance Engineer
  getting only a go/no-go is missing the data they need.
- **Do NOT hand-roll a `while sleep N; do …; done` loop instead of `--wait`.**
  See [SKILL.md § Performance Scenario Commands](../SKILL.md#performance-scenario-commands-perf-scenario).
- **Do NOT fabricate metrics.** Every number in the report must trace to a
  field in the JSON payload. If `Data.LoadGroups[]` is empty, the report
  says "no data returned" — full stop.
- **Do NOT delete the scenario after the run.** Scenarios are reusable;
  the user may want to re-run later or compare across runs. Only delete
  on explicit user request.
- **Do NOT call `load-groups remove` to "clean up" after a run.** Removing a
  load group throws away its folder, package, and load profile; past
  execution data stays but the scenario can no longer be re-run as-is.
  Remove only when the user asks.
