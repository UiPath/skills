# Run a Performance Scenario End-to-End

End-to-end pipeline: take a Test Manager test case that is already linked to
an Orchestrator package, wrap it in a performance scenario as a load group,
run a dry run, and write a persona-tailored perf report from the cumulative
results. Copy-paste safe. Defaults are dry-run-friendly so the first run is
cheap.

## Pipeline

```
uip tm scenario create          → ScenarioKey
uip tm scenario add-testcase    → load group attached
uip tm scenario execute --wait  → polls until terminal, returns results
(optional) scenario execution-results --full   → per-second time series
write report → ./test-report-<persona>-<YYYY-MM-DD>.md
```

## Reuse vs. create — pick the right starting step

The three steps above are **idempotent and independent**. Don't blindly
run all three every time the user asks for a perf run. Pick the entry
point based on what the user actually said:

| What the user asked for | Where to start |
|---|---|
| *"Create a perf scenario for SP1:602 and run it"* | Step 2 (create) → Step 3 (add-testcase) → Step 4 (execute) |
| *"Run a perf test on SP1:1276"* (gave a `<SCENARIO_KEY>`) | Step 4 only — first `scenario get --scenario-key SP1:1276` to confirm it exists and has at least one load group; skip create + add-testcase |
| *"Run the same scenario again with a full execution"* | Step 4 only — reuse the scenario from earlier in the conversation; **do not create a new one** |
| *"Run a perf test on our login test case"* (no scenario-key) | Ask the user: "Do you want me to reuse an existing scenario for this test case, or create a new one?" Then act on the answer. |

> **Never create + add-testcase on a scenario that already has load
> groups.** Call `scenario get --scenario-key <KEY>` first — if the
> response has `LoadGroupCount >= 1`, the scenario is ready to execute as-is.

> **Never create a new scenario when the user has already given you a
> `SP1:NNNN` key.** That key IS the scenario; jump straight to step 4.

If the user supplies a scenario key but `scenario get` returns "not
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
or similar, fall back to running a dry run, then retry. The endpoint
`GET /Execution/RetrieveDryRunReports` is the programmatic source of
truth for whether a passing dry-run report exists (not currently in the
CLI; track via session state).

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
  lives. Without it `scenario execute` fails with HTTP 400 *Insufficient
  Performance Testing runtimes available*.

## Step 1 — Discover inputs

The discovery commands are shared with the standard test pipeline. **Cross-link**
to [publish-and-link-guide.md](publish-and-link-guide.md) Steps 3–4 — do not
duplicate that material here. The values you need from those steps are:

| Variable | Where to get it |
|---|---|
| `<PROJECT_KEY>` | `uip tm project list --output json` |
| `<TEST_CASE_KEY>` (`PROJECT_KEY:NUMBER`) | `uip tm testcase list --project-key <PROJECT_KEY> --output json` → `ObjKey` |
| `<FOLDER_KEY>` (UUID) | `uip or folders list --output json` → `Key` |
| `<PACKAGE_NAME>` | `uip tm testcase list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json` → `PackageName` |

## Step 2 — Create the scenario

```bash
uip tm scenario create \
  --project-key <PROJECT_KEY> \
  --name "<SCENARIO_NAME>" \
  --description "<OPTIONAL_DESCRIPTION>" \
  --version 1.0 \
  --output json
```

Capture `Data.ScenarioKey` from the response (e.g. `SP1:1133`). It is the
handle you'll use for every subsequent scenario command.

Optional metadata flags (all have sensible defaults):

| Flag | Default | Notes |
|---|---|---|
| `--app-type` | `web` | `web` / `desktop` / `api` |
| `--perf-test-type` | `loadTesting` | `loadTesting` / `stressTesting` / `enduranceTesting` |
| `--responsiveness` | `fast` | `fast` / `medium` / `slow` |

## Step 3 — Add the test case as a load group

```bash
uip tm scenario add-testcase \
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

You can call `add-testcase` multiple times per scenario to attach multiple
load groups (e.g. login + checkout + payment). Each call returns a
`LoadGroupId`.

## Step 4 — Run + wait

```bash
uip tm scenario execute \
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
> 3. **If unsure**: call `scenario list-dry-run-reports` to verify a
>    passing dry-run report exists before deciding.
> 4. **Never run a dry run pre-emptively when the user explicitly asked
>    for a full run on an existing scenario** unless step 2's fallback
>    kicks in. The user's intent is the full run; respect it.
>
> The `scenario list-dry-run-reports` subcommand (calls
> `POST /performancetest/Execution/RetrieveDryRunReports`) gives the
> agent a programmatic way to verify a passing dry-run report exists
> without burning a fresh dry run.
>
> ⚠️ **`list-dry-run-reports` only works for test cases that have an
> `automationId` set.** Test cases linked via the older
> `packageEntryPointUniqueId` mechanism (the legacy
> `tm testcase link-automation --package-name X --test-name Y` flow)
> return `automationId: null` and the perf service rejects the request
> with *"Automation Runtime Pairs is missing"*. In that case, the
> agent's correct fallback is the **try-then-fallback** pattern:
> attempt `performanceTesting` directly → if rejected with HTTP 400
> "No dry run reports found", run a dry run, then retry.

### Two-phase rule: dry run ignores the load profile, full run honours it

| Phase | Uses load-group config? | Required precondition |
|---|---|---|
| `dryRun` | **No.** Always 1 VU with a fixed short profile; the server probes the automation and emits a `Recommended multiplexing factor: N`. `--virtual-users`, `--ramp-up-minutes`, `--peak-minutes`, `--ramp-down-minutes`, SLO thresholds — all ignored. | None — can be the first run. |
| `performanceTesting` (full) | **Yes.** Honours every load-profile field on each load group. | At least one successful dry run must exist for this scenario. |

The practical consequences for the agent:

- **Don't ask the user about the load profile *before* the dry run.** Those
  values don't take effect there. Just run the dry run with whatever's
  currently configured (or with one fresh `add-testcase` if no load
  group exists yet) — the actual values don't matter.
- **Don't call `update-loadgroup` *before* the dry run.** Same reason.
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
   uip tm scenario get --scenario-key <SCENARIO_KEY> --output json
   ```
   Read each `LoadGroups[i]` row.

2. **Ask the user** to confirm or override each of these for **every**
   load group:

   | Parameter | Flag on `update-loadgroup` | Typical range |
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
   uip tm scenario update-loadgroup \
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
   `update-loadgroup` is a true partial update — flags you omit are
   preserved from the current server state.

4. **Re-read** to confirm the update landed (optional sanity check):
   ```bash
   uip tm scenario get --scenario-key <SCENARIO_KEY> --output json
   ```

5. **Then** submit the full run.

If the user says *"just use defaults"* — still surface the current
stored values from `scenario get` and ask if they're acceptable. **Do
not silently fire `performanceTesting` against possibly-wrong
parameters.** A full perf run consumes scarce perf runtimes and produces
data that may be useless if the load profile is wrong.

### Concrete sequence — full execution end-to-end

The required 3-call chain when the user asks for a full run on an
**existing scenario with load groups already attached**:

```bash
# 1. Confirm scenario exists + has load groups (skip create/add-testcase)
uip tm scenario get --scenario-key <SCENARIO_KEY> --output json

# 2. Dry run — required precondition for a full run
uip tm scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --execution-type dryRun \
  --wait \
  --output json
# → confirm terminal status 'Finished' in the last application log

# 3. Full performance run — honours load-profile flags on the load groups
uip tm scenario execute \
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
uip tm scenario execute \
  --scenario-key <SCENARIO_KEY> \
  --execution-type dryRun \
  --output json
# → { "Result": "Success", "Data": { "ExecutionId": "<uuid>", "ExecutionType": "dryRun", "Status": "pending" } }
```

You can then either:

- **Poll yourself** at intervals: `uip tm scenario execution-results --execution-id <uuid> --project-key <KEY> --output json` and scan `Data.ApplicationLogs[]` for `ended with the status`.
- **Or rejoin the wait later**: re-invoke `execute --wait` is **not** the right rejoin — it'd start a *new* execution. Use `execution-results` polling for rejoining.

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
> uip tm scenario execute \
>   --scenario-key <SCENARIO_KEY> \
>   --execution-type performanceTesting \
>   --output json
> # → captures ExecutionId from the response
>
> # 2. Hand the ExecutionId back to the user, plus the two follow-up commands:
> #
> #    Check progress at any time:
> #      uip tm scenario execution-results \
> #        --execution-id <EXECUTION_ID> --project-key <KEY> --output json
> #
> #    Cancel the run (from THIS terminal or any other):
> #      uip tm scenario stop \
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
and exits when the run reaches a terminal state (`Finished` / `Cancelled` /
`Faulted`) or `--timeout-sec` (default `1800`, i.e. 30 min) elapses.

**Prefer `--wait` over a hand-rolled poll loop.** The CLI:

- Dedupes status-change application logs (only prints each new message once).
- Tolerates transient 5xx during long polls.
- Uses the same response shape `execution-results` would return when the
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

`scenario execute --wait` and `scenario execution-results` emit the
**same shape**. Default (`~6 KB`):

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
| `Data.ExecutionId` | UUID for the run; pass back to `execution-results` to re-fetch later. |
| `LoadGroupCount` | Count of load groups attached to the scenario. |
| `LoadGroups[].StartedAt` | ISO-8601 start of this load group (UTC). |
| `LoadGroups[].CumulativeResponseTimeMs` | Mean response time across every successful workflow in the group. |
| `LoadGroups[].MaxResponseTimeMs` | Worst single-workflow response time. |
| `LoadGroups[].SuccessfulWorkflowCount` / `FailedWorkflowCount` | Workflow-level pass/fail. |
| `LoadGroups[].HttpErrorRate` / `AutomationErrorRate` | Fractions in `[0,1]`, not percentages. |
| `LoadGroups[].SloViolationReasons[]` | Human-readable strings explaining each SLO breach. **The agent's job is to surface these to the user, not to re-derive them.** |
| `LogCount` | Total application log entries. |
| `ApplicationLogs[]` | Status-change events ordered chronologically; the last one carries the terminal status. |

Add `--full` (~50 KB) to also include per-load-group time series:

```bash
uip tm scenario execute --scenario-key <SCENARIO_KEY> --wait --full --output json
# or, after the fact:
uip tm scenario execution-results --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --full --output json
```

`--full` adds two arrays per load group:

- `AggregatedData[]` — typically 60 entries with per-time-bucket
  `cpu`, `ram`, `vUserCount`, `avgResponseTimeMs`,
  `p50ResponseTimeMs`, `p90ResponseTimeMs`, `p95ResponseTimeMs`,
  `p99ResponseTimeMs`, `stepTimeMs`, etc. Use this for percentile and
  resource analysis.
- `AggregatedDataWithTransaction[]` — same shape grouped by transaction;
  empty in dry runs that have no per-transaction breakdown.

> Default ~6 KB vs. `--full` ~50 KB is a meaningful difference if you're
> piping the JSON to an LLM. Only request `--full` for personas that need
> percentile or time-series detail (Performance Engineer, Developer
> drill-down). Skip it for Release Manager summaries.

## Step 5b — Per-transaction (per-API) metrics (`scenario transaction-metrics`)

The cumulative `LoadGroups[].CumulativeResponseTimeMs` rolls every
transaction together. For a Performance Engineer or Developer who needs to
know *which API call* is slow, fetch the per-transaction breakdown:

```bash
uip tm scenario transaction-metrics \
  --load-group-id <LOAD_GROUP_ID> \
  --project-key <PROJECT_KEY> \
  --output json
# optional window:
#   --start-time-ms <N>  (ms since load-group StartedAt)
#   --end-time-ms   <N>
```

`<LOAD_GROUP_ID>` is the `LoadGroupId` field from `scenario execute --wait`
or `scenario execution-results` — one per attached load group.

Response shape:

```json
{
  "Result": "Success",
  "Code": "ScenarioTransactionMetrics",
  "Data": {
    "LoadGroupId": "...",
    "StartTimeMs": null,
    "EndTimeMs": null,
    "TransactionCount": 7,
    "Transactions": [
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
}
```

Use this when:

- The cumulative summary shows an SLO violation but you don't know which
  API call is the offender.
- The Performance Engineer report needs per-endpoint p95/p99 — much
  more actionable than the load-group-level rollup.
- You're narrowing down a specific time window inside a long run (pass
  `--start-time-ms` / `--end-time-ms`).

> The list returned has **one row per distinct `TransactionName` observed
> during the load-group execution.** No transactions instrumented in the
> automation → empty `Transactions: []`. If empty, surface that fact to
> the user rather than fabricating per-call metrics from `AggregatedData[]`.

> ⚠️ **`transaction-metrics` only returns rows when the scenario's
> `AppType` is `api`.** Web and desktop scenarios drive the application
> through the UI (browser automation / Windows UIA selectors), not by
> issuing HTTP calls the perf service can intercept — so the Perf
> Service has no per-API transactions to report. The endpoint
> returns `200 OK` with `Transactions: []` in that case, **not** an
> error.
>
> Decision tree before calling `transaction-metrics`:
>
> 1. Run `uip tm scenario get --scenario-key <KEY> --output json`.
> 2. Read `Data.AppType`.
>    - `api` → call `transaction-metrics`, expect populated rows.
>    - `web` / `desktop` → **skip `transaction-metrics`**. Use the
>      `AggregatedData[]` time series from `execution-results --full`
>      instead (it has `stepTimeMs`, `p95StepTimeMs`, etc. — per-step,
>      not per-API, but it's the right granularity for UI-driven runs).
> 3. If you still want to try `transaction-metrics` on a non-`api`
>    scenario for any reason, tell the user upfront that the empty
>    `Transactions: []` is expected, not a missing-data bug.

## Step 6 — Generate a perf report

Re-uses the persona / output-dir / filename mechanics from
[test-result-report-guide.md](test-result-report-guide.md) — same workflow,
new persona content. **Always ask for the persona before writing.**

### Persona content

**For Performance Engineer reports** (use `--full` *and* `transaction-metrics`):

- Cumulative metrics summary (response time mean / max, success rate, error rates).
- p50 / p90 / p95 / p99 response time from `AggregatedData[]`, with the
  time bucket where the percentile peaked.
- **Per-transaction breakdown from `scenario transaction-metrics`** — one
  row per API call with its avg / min / max / p50–p99 / request count /
  HTTP error count. This is the most actionable section: it pins the
  slowness to a specific endpoint.
- CPU / RAM peaks and the time bucket they occurred in.
- Every entry of `SloViolationReasons[]` reproduced verbatim.
- HTTP errors vs. automation errors broken out separately with rates.
- 2–3 actionable recommendations grounded in the numbers (e.g. "raise
  `--max-response-time-ms` from 100 to 300 — the 3437ms peak is a real
  outlier", "investigate `POST /api/login` — its p99 was 1010ms, 6× the
  rest of the calls").
- Ask if further details are needed → follow [Analyse More](#analyse-more).

**For Release Manager reports** (default payload, no `--full`):

- Single-paragraph **go / no-go** decision with the reason.
- Cumulative success rate from `SuccessfulWorkflowCount /
  (SuccessfulWorkflowCount + FailedWorkflowCount)`.
- The SLO that drives the decision (one line from `SloViolationReasons[]`,
  or "all SLOs met" if empty).
- Risk assessment: if `SloViolationReasons[]` is non-empty or
  `FailedWorkflowCount > 0`, mark as "no-go pending investigation".
- **No raw time series, no per-second tables.** Keep the report ≤ 300 lines.

**For Developer reports** (use `--full`):

- Failing workflows by `LoadGroupId` with timestamps and step times.
- Slowest steps from `AggregatedData[].stepTimeMs` with the time bucket.
- HTTP error count + automation error count, separately, with the
  application log messages from around their timestamps.
- Specific `ApplicationLogs[]` entries by `CreatedAt` for each anomaly.
- Ask if further details are needed → follow [Analyse More](#analyse-more).

**Other persona** — ask the user "What persona is this report for, and what
decisions will it support?" before writing.

### Output format

Default filename is `test-report-<persona>-<YYYY-MM-DD>.md`, where
`<persona>` is `perf` (Performance Engineer), `release` (Release Manager),
`dev` (Developer), or `custom` (anything else). Same convention as
[test-result-report-guide.md § Output Format](test-result-report-guide.md).

Ask the user:

- "Where should the report be saved? (default: current directory)"
- "What should the report be named? (default: `<DEFAULT_FILENAME>`)"

Verify the directory exists before writing. If it doesn't, ask whether to
create it or pick another path. Do not create directories silently.

## Analyse More

Same drill-down loop as
[test-result-report-guide.md § Analyse More](test-result-report-guide.md#analyse-more):

1. **Explore** — `uip tm scenario --help` / `uip tm scenario <sub> --help` to
   confirm the right subcommand and its flags.
2. **Execute** — run the command using IDs from the previous response, always
   with `--output json`.
3. **Validate** — if the response is empty or errors, diagnose before
   retrying (max 3 attempts).
4. **Repeat** — if the user asks for deeper detail, identify the next
   command and repeat.

Perf-specific drill-down candidates:

- **Per-transaction (per-API) metrics** when the rollup hides which call
  is slow: `uip tm scenario transaction-metrics --load-group-id <UUID>
  --project-key <KEY>`. Returns p50/p90/p95/p99 + request count + HTTP
  error count *per `TransactionName`*. Pass `--start-time-ms` /
  `--end-time-ms` to zoom into a specific window.
- Re-fetch the same execution with `--full`: `uip tm scenario execution-results
  --execution-id <UUID> --project-key <KEY> --full`.
- Inspect scenario metadata + load-group settings:
  `uip tm scenario get --scenario-key <KEY>` (project is derived from the
  scenario-key prefix — no `--project-key` flag).
- Cross-reference the linked test case's executions:
  `uip tm execution list --project-key <KEY> --test-set-id <ID>` — useful
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
- **Running `scenario execute` without first attaching a load group.**
  `scenario create` alone is just metadata; the perf service responds with
  HTTP 404 *Performance Testing Scenario Test Case Configurations does not
  exist* until you've called `scenario add-testcase` at least once.
- **Pinning `--package-version` when the user didn't ask.** The CLI's
  auto-resolve picks the highest published version in the folder — that is
  almost always what you want. Pinning is for the rare reproducer case.
- **Using `--full` for a Release Manager report.** The 60-entry time series
  is noise for a go/no-go audience. Default payload only.
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
  See [SKILL.md § Scenario Commands](../SKILL.md#scenario-commands-performance-testing).
- **Do NOT fabricate metrics.** Every number in the report must trace to a
  field in the JSON payload. If `Data.LoadGroups[]` is empty, the report
  says "no data returned" — full stop.
- **Do NOT delete the scenario after the run.** Scenarios are reusable;
  the user may want to re-run later or compare across runs. Only delete
  on explicit user request.
