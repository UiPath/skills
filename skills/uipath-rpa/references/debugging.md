# Debugging Workflows with the `debug` group

The `uip rpa debug` group (plus `uip rpa run` and `uip rpa execution cancel`) provides full interactive debugging for both XAML workflows and coded (.cs) files. Beyond simple execution (`run`), it supports breakpoints, step-by-step execution, exception handling, isolated activity testing, and runtime state inspection — all from the CLI.

This is a powerful complement to `validate` (static validation). While `validate` catches structural and type issues at design time, the debugger catches runtime problems: wrong API responses, null references, logic errors, failed deserialization, and more. Use both together for comprehensive workflow validation.

## Studio Desktop vs headless

Most debugging works on **headless Studio** with no Studio Desktop install: `run`, `debug start` (with workflow-level breakpoint), all stepping verbs (`debug step-over`, `debug step-into`, `debug step-out`), `debug continue`, `debug break`, `debug resume`, `debug continue-retry`, `debug continue-ignore`, `execution cancel`, `debug restart-from-top`.

**Studio Desktop is required** for any flow that targets a specific activity, because activity targeting goes through `uip rpa focus-activity` and that tool only runs against Studio Desktop:

| Command | Why it needs Studio Desktop |
|---------|------------------------------|
| `debug test-activity` | Operates on the focused activity — requires `focus-activity` first |
| `debug start-from-here` | Operates on the focused activity — requires `focus-activity` first |
| `debug toggle-breakpoint` *targeted to a specific activity* | Targeting requires `focus-activity` first. Without focusing, the breakpoint toggles on the whole workflow (still works headless) |

Before invoking any of the above, run `uip rpa studio start --project-dir "<PROJECT_DIR>" --output json` and ensure the project is open in Studio Desktop. See [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop).

---

## Command Reference

`run` and `debug start` take a file path and optional inputs:

```bash
uip rpa run         --file-path <relative-path> [--input-arguments '<json>'] [--log-level <level>] [--skip-build] [--output json]
uip rpa debug start --file-path <relative-path> [--input-arguments '<json>'] [--log-level <level>] [--skip-build] [--output json]
```

`debug test-activity` and `debug start-from-here` operate on the currently focused activity (no `--file-path`):

```bash
uip rpa debug test-activity     [--input-arguments '<json>'] [--input-variables '<json>'] [--log-level <level>] [--output json]
uip rpa debug start-from-here   [--input-arguments '<json>'] [--input-variables '<json>'] [--log-level <level>] [--output json]
```

All other `debug` verbs (`break`, `continue`, `resume`, `continue-retry`, `continue-ignore`, `step-into`, `step-over`, `step-out`, `toggle-breakpoint`, `restart-from-top`) take no parameters — they operate on the active debug session.

| Parameter | Description |
|-----------|-------------|
| `--file-path` | Workflow file to run (relative to project root). Applies to `run` and `debug start` only |
| `--input-arguments` | JSON object with project-level input arguments. Only for `run`, `debug start`, `debug test-activity`, and `debug start-from-here` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--input-variables` | JSON object with workflow-level variable values. Only for `debug test-activity` and `debug start-from-here` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--log-level` | Minimum log level: `Verbose`, `Trace`, `Information` (default), `Warning`, `Error`, `Critical` |
| `--skip-build` | Skip the pre-run build step (use only when you've just built) |
| `--output` | Output format: `json` (recommended), `table`, `yaml`, `plain` |
| `--profiling` | Collect per-activity timings and runtime screenshots — verifies UI automation correctness and workflow performance. Only effective on start commands (`StartExecution`, `StartDebugging`, `TestActivity`, `StartDebuggingFromHere`); ignored on stepping / breakpoint commands. Defaults to `false`. See [Profiling Workflow Performance](#profiling-workflow-performance). |

### Debug Verbs

| Verb | When to Use | What It Does |
|------|-------------|--------------|
| `run` | Run without debugging | Executes the workflow to completion. The default authoring loop verb |
| `debug start` | Begin a debug session | Starts execution in debug mode. Pauses at the first breakpoint (or at the first activity if a breakpoint is set on the workflow itself). Returns current execution state |
| `debug test-activity` | Test one activity in isolation | Isolates the currently focused activity and executes it in a temporary test workflow. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `debug start-from-here` | Debug from a specific activity | Starts a debugging session from the currently focused activity, skipping all preceding activities. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `debug toggle-breakpoint` | Set/remove breakpoints | Toggles a breakpoint on the currently focused activity (XAML) or line (.cs). Use `uip rpa focus-activity` to focus beforehand — **activity-targeted toggling requires Studio Desktop**. For XAML, cycles through 3 states: **enabled → disabled → no breakpoint**. For .cs, cycles through 2 states: **breakpoint → no breakpoint**. If no activity/line is focused, toggles on the entire workflow (works on Helm) |
| `debug step-over` | Execute one activity and pause | Executes the current activity, then pauses at the next sibling activity. Does not enter child scopes (e.g., stays at the For Each level, doesn't step into its body) |
| `debug step-into` | Drill into child activities | Executes and pauses at the first child activity inside the current scope. Use to enter loops, sequences, Try-Catch blocks, etc. |
| `debug step-out` | Exit the current scope | Continues execution until the current scope completes, then pauses at the parent level. Use to leave a loop body or nested sequence |
| `debug continue` | Run to next breakpoint | Resumes execution until the next breakpoint is hit or an exception occurs |
| `debug break` | Pause execution | Pauses a running debug session at the current point of execution |
| `debug resume` | Resume from suspended state | Resumes execution when the workflow is in a suspended (not just paused) state |
| `debug continue-retry` | Retry after exception | Resumes execution and **retries the current activity** that caused the exception. Use when you've fixed the underlying issue (e.g., network timeout) and want to try again |
| `debug continue-ignore` | Skip past exception | Resumes execution and **ignores the exception** on the current activity. Use when the error is non-critical and you want to proceed |
| `execution cancel` | End the session | Cancels the currently active execution — works for both `run` and `debug start` |
| `debug restart-from-top` | Start over | Restarts execution from the beginning of the workflow without ending the debug session. Breakpoints are preserved |

---

## Input Variables vs Input Arguments

These serve different purposes and apply to different scopes:

- **Arguments** (`--input-arguments`) are **project-level In/Out/InOut parameters** defined in the project's argument list. They are the workflow's public interface — how callers pass data in and receive data back. Applicable for `run`, `debug start`, `debug test-activity`, and `debug start-from-here`.

- **Variables** (`--input-variables`) are **workflow-level local state** declared inside the workflow and scoped to specific activities or containers (e.g., a Sequence, a For Each body). They are internal to the workflow and not visible from outside. Only applicable for `debug test-activity` and `debug start-from-here` — these verbs execute from a specific activity's context, so you can pre-set the variables that activity reads from.

| | `--input-arguments` | `--input-variables` |
|---|---|---|
| **What they are** | Project-level parameters (In/Out/InOut) | Workflow-internal variables scoped to activities |
| **Where defined** | Project argument list (visible in Studio's Arguments panel) | Inside the workflow (visible in Studio's Variables panel) |
| **Applicable verbs** | `run`, `debug start`, `debug test-activity`, `debug start-from-here` | `debug test-activity`, `debug start-from-here` only |
| **Value format (`run` / `debug start`)** | Plain JSON values: `{"name":"John","age":30}` | N/A |
| **Value format (`debug test-activity` / `debug start-from-here`)** | VB.NET or C# expressions | VB.NET or C# expressions |

### Expression Value Examples

For `debug test-activity` and `debug start-from-here`, both `--input-arguments` and `--input-variables` values must be **VB.NET or C# expressions** matching the project language.

**VB.NET projects:**
```bash
# String variable — VB string literal with escaped quotes
--input-variables '{"greeting": "\"Hello World\""}'

# Integer variable
--input-variables '{"count": "42"}'

# Boolean variable (VB uses True/False, capitalized)
--input-variables '{"isActive": "True"}'

# Null / unset (VB keyword)
--input-variables '{"result": "Nothing"}'

# New object
--input-variables '{"config": "New Dictionary(Of String, Object)"}'

# Multiple variables at once
--input-variables '{"name": "\"John\"", "age": "30", "isActive": "True"}'
```

**C# projects:**
```bash
# String variable
--input-variables '{"greeting": "\"Hello World\""}'

# Boolean variable (C# uses true/false, lowercase)
--input-variables '{"isActive": "true"}'

# Null / unset (C# keyword)
--input-variables '{"result": "null"}'

# New object
--input-variables '{"config": "new Dictionary<string, object>()"}'
```

> **Important:** String values require the VB/C# string literal quotes *inside* the JSON value. A JSON string `"200"` becomes the expression `200` (an integer literal), not the string `"200"`. To pass the string `"200"`, use `"\"200\""`.

---

## Output Format

`run` and `debug start` return a JSON envelope with `Data.runResult` as a JSON-encoded string. Parse `runResult` separately. It has exactly three fields:

```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "runResult": "{\"Output\":\"...\",\"HasErrors\":false,\"ErrorMessage\":null}"
  }
}
```

Inside `runResult`:

| Field | Type | Meaning |
|-------|------|---------|
| `Output` | `string` | Workflow's serialized output arguments JSON. `""` for non-`Start*` commands and on debug-command responses (`debug step-over`, `debug continue`, etc.). **Carries the workflow's data, not a verdict.** |
| `HasErrors` | `bool` | `true` iff execution did not complete with `Succeeded` (compile failure, validation failure, unhandled exception, cancellation, timeout). `false` otherwise. |
| `ErrorMessage` | `string?` | Formatted error chain when `HasErrors: true`; `null` otherwise. |
| `Profiling` | `object?` | Present only when `--profiling` was passed on a start command and collection succeeded. Single field `OutputDirectory` — absolute path to the run's `*.uistat` and screenshot folder (verifies UI automation correctness and workflow performance). `null` / omitted otherwise. See [Profiling Workflow Performance](#profiling-workflow-performance). |

Workflow log output (`Log Message` activity, system traces) is **streamed in real time** during execution on a separate channel. It is NOT embedded in `runResult`.

> **`Result` (outer) — equivalently `HasErrors` (inner) — is the only success/failure signal.** `Result: "Success"` already accounts for compile failures, validation failures, and unhandled runtime exceptions. **Do NOT use streamed log entries' `Level` as a failure signal** — workflow `Log Message` activities emit at any level, and successful runs commonly include `Error` / `Warning` entries from the workflow's own logging. Treating log levels as a verdict flips green runs to "failed".

Examples:

```jsonc
// Successful run — workflow logged a warning, but HasErrors is false
{ "Output": "{\"resultCode\":\"OK\"}", "HasErrors": false, "ErrorMessage": null }

// Failed run — compile or runtime failure
{ "Output": "", "HasErrors": true, "ErrorMessage": "Source: HttpRequest_1\nMessage: ..." }

// Debug-command response (`debug step-over` / `debug continue` / etc.) — empty success
{ "Output": "", "HasErrors": false, "ErrorMessage": null }
```

---

## Choosing the Right Verb

| Situation | Verb | Why |
|-----------|------|-----|
| "Run the whole workflow and check the result" | `run` | Full run, no debugging overhead |
| "This one activity isn't working — test it with specific inputs" | `debug test-activity` | Isolates the activity, fastest feedback loop |
| "The bug is in activity X but I need the debug session to step through from there" | `debug start-from-here` | Skips everything before X, gives full debug control from that point |
| "I need to step through the entire workflow from the start" | `debug start` | Full debug session with breakpoints, stepping, variable inspection |
| "I want to verify the fix works at runtime after editing" | `run` or `debug test-activity` | Quick validation — use `debug test-activity` if you only changed one activity |

---

## Common Debugging Workflows

### 1. Quick Breakpoint Debug Session

The most common pattern: set a breakpoint on the focused activity, start debugging, inspect state, then continue or step through.

> **Studio Desktop required** for activity-targeted breakpoints (the `focus-activity` step). Skip step 1 to set a workflow-level breakpoint instead — that path runs headless.

```bash
# 1. Focus the activity you want to break at (Studio Desktop only — skip to break at the workflow level)
uip rpa focus-activity --activity-id "Assign_1"

# 2. Toggle a breakpoint on the focused activity
uip rpa debug toggle-breakpoint --output json

# 3. Start debugging — execution pauses at the breakpoint
uip rpa debug start --file-path "GetStockPrices.xaml" --output json

# 4. Inspect the response: HasErrors / ErrorMessage / Output (workflow output args).
#    Variable values seen during the run are observed via streamed log entries.
# Then step through or continue:
uip rpa debug step-over --output json

# 5. When done, cancel the session
uip rpa execution cancel --output json
```

### 2. Test a Single Activity in Isolation

Use `debug test-activity` to run just the currently focused activity without executing the entire workflow. Useful for verifying an activity works with specific inputs.

> **Studio Desktop required** — `focus-activity` and `debug test-activity` both rely on it. On a headless-only setup, fall back to a workflow-level `debug start` with a breakpoint placed earlier in the file.

```bash
# 1. Focus the activity to test (Studio Desktop required)
uip rpa focus-activity --activity-id "DeserializeJson_1"

# 2. Run it in isolation, pre-setting any variables it reads from
uip rpa debug test-activity \
  --input-variables '{"temperature": "\"200\""}' \
  --output json

# 3. Check the output:
#    - HasErrors / ErrorMessage → compile/validation issues, unhandled exceptions
#    - Streamed log entries → runtime messages from the activity (observability, not a verdict)
#    - Output → workflow's serialized output args on success
```

### 3. Debug From a Specific Activity

Use `debug start-from-here` to skip straight to the activity you care about, avoiding stepping through earlier activities.

> **Studio Desktop required** — `focus-activity` and `debug start-from-here` both rely on it. On a headless-only setup, use plain `debug start` with a workflow-level breakpoint near the activity instead.

```bash
# 1. Focus the activity to start from (Studio Desktop required)
uip rpa focus-activity --activity-id "HttpRequest_1"

# 2. Start debugging from that point, pre-setting variables
uip rpa debug start-from-here \
  --input-variables '{"apiUrl": "\"https://api.example.com/weather\""}' \
  --output json

# 3. The debugger runs from the focused activity — step through or continue
uip rpa debug step-over --output json

# 4. Cancel when done
uip rpa execution cancel --output json
```

### 4. Exception Investigation

When `debug continue` or a step verb hits an exception, the debugger pauses and returns the exception details. You can inspect the state, then decide how to proceed.

```bash
# Start debugging and continue to let it run
uip rpa debug start --file-path "MyWorkflow.xaml" --output json
uip rpa debug continue --output json

# If an unhandled exception occurs, HasErrors flips to true and ErrorMessage carries
# the formatted exception chain (source activity, type, message, stack trace).
# - Read ErrorMessage for the canonical failure diagnostic
# - Cross-reference streamed log entries for variable state and trace context
#   leading up to the failure

# Then choose how to proceed:
# Option A: Retry the failed activity (e.g., transient network error)
uip rpa debug continue-retry --output json

# Option B: Ignore the exception and continue past it
uip rpa debug continue-ignore --output json

# Option C: Cancel and fix the root cause
uip rpa execution cancel --output json
```

### 5. Runtime Validation After Edits

Use debugging to verify that a fix actually works at runtime, beyond what `validate` (static validation) can check.

```bash
# 1. Run static validation first
uip rpa validate --file-path "MyWorkflow.xaml" --output json

# 2. If 0 static errors, start a debug session to validate runtime behavior
uip rpa debug start --file-path "MyWorkflow.xaml" --output json

# 3. Continue past the fixed area and inspect variable state
uip rpa debug continue --output json

# 4. Check the response for:
#    - Outer Result is "Success" (HasErrors: false) — the canonical pass/fail signal
#    - Output (workflow's serialized output args) carries the expected values
#    - Streamed log entries during the run are diagnostic context, NOT a failure signal —
#      Error/Warning levels there are workflow-emitted observability, not CLI failures

# 5. Cancel
uip rpa execution cancel --output json
```

### 6. Debugging with Input Arguments

Pass input arguments when the workflow has In arguments that need values:

```bash
# Start debugging with input arguments (plain JSON values)
uip rpa debug start --file-path "ProcessOrder.xaml" \
  --input-arguments '{"orderId": "ORD-12345", "customerEmail": "test@example.com"}' \
  --output json
```

`--input-arguments` is valid with `run`, `debug start`, `debug test-activity`, and `debug start-from-here`. For `run` / `debug start`, values are plain JSON. For `debug test-activity` / `debug start-from-here`, values must be VB/C# expressions.

---

## Profiling Workflow Performance

Use `--profiling` on a start command to collect per-activity timings **and runtime screenshots** — the same data Studio's **Profile Execution** tool surfaces. Profiling serves two purposes that can be addressed in a single run: **verifying UI automation correctness** (via the captured screenshots — confirm clicks landed on the right element, forms filled as expected, screens transitioned correctly) **and verifying workflow performance** (via the per-activity timings). The executor writes `*.uistat` files plus screenshots into `%LOCALAPPDATA%\UiPath\ProfiledRuns\HHmmss_yyyy-MM-dd_<entryPoint>_<projectName>\` and the response carries the absolute path on `runResult.Profiling.OutputDirectory`. Same folder layout as Studio's own profiling history, so agent-triggered and Studio-triggered runs land side by side.

### When to enable profiling

| Situation | Why |
|-----------|-----|
| User reports a slow workflow ("X takes 5 min, was 30 s last week") | Profiling localizes the regression to specific activities instead of the whole workflow |
| Choosing between two implementations of the same logic | Compare cumulative time across the activities each version uses |
| A loop body looks expensive but the cost is not obvious | `*.uistat` reports execution count + min/max/avg per activity — flags hot iterations |
| Pre-production sanity check on a long-running automation | Catches an activity whose individual time looks fine but whose cumulative share is dominant |
| Verifying a UI automation ran correctly without re-running it interactively | Captured screenshots show what the workflow actually saw at each UI activity — confirms clicks landed, forms filled, screens transitioned |
| Diagnosing "the workflow succeeded but the wrong thing happened" | Cross-check screenshots against expected screens; cheaper than rerunning with a debugger attached |

Do **not** enable profiling by default. It is opt-in for performance investigations and UI correctness checks — a normal smoke test (`uip rpa run-file --command StartExecution`) is faster and produces no `.uistat` files or screenshots to clean up.

### Where the flag is effective

Only start commands collect profiling — `--profiling true` is silently ignored on stepping/breakpoint commands:

| Command | `--profiling` effect |
|---------|---------------------|
| `StartExecution` | Collects |
| `StartDebugging` | Collects |
| `TestActivity` | Collects (single-activity scope; useful for tuning one activity) |
| `StartDebuggingFromHere` | Collects (partial workflow from the focused activity onward) |
| `StepOver` / `StepInto` / `StepOut` / `Continue` / `Break` / `Stop` / `ContinueRetry` / `ContinueIgnore` / `RestartFromTop` / `ToggleBreakpoint` / `ForceSessionEnded` / `Resume` | No-op |

### Reading the result

```bash
uip rpa run-file --file-path "ProcessOrders.xaml" --command StartExecution --profiling true --output json
```

Parse `Data.runResult` then inspect:

```jsonc
{
  "Output": "{\"orderCount\":42}",
  "HasErrors": false,
  "ErrorMessage": null,
  "Profiling": {
    "OutputDirectory": "C:\\Users\\<user>\\AppData\\Local\\UiPath\\ProfiledRuns\\142305_2026-05-12_Main.xaml_ProcessOrders"
  }
}
```

The directory contains `*.uistat` files — one per workflow file executed in the run (top-level entry point plus every invoked workflow) — alongside runtime screenshots captured at UI activity boundaries. Each `*.uistat` row reports an activity with execution count, min / max / average / cumulative duration, and the cumulative percentage of total run time. Focus on:

1. **Activities with the largest cumulative percentage** — the dominant time sinks. Optimize these first.
2. **High execution count × moderate average duration** — typically loop bodies. Consider batching, caching, or hoisting work out of the loop.
3. **Wide min/max spread on a UI activity** — flaky selectors or variable target-element resolution; cross-check with the healing-agent log and the screenshot for that activity to confirm the element actually rendered.
4. **Screenshots for UI correctness** — open the screenshot folder to verify each UI interaction targeted the expected screen / element. Useful when the workflow reports `Success` but downstream data looks wrong.

### Caveats

- `Profiling` field is **absent** if the run did not reach the executor (compile failure surfaces in `ErrorMessage` instead) or if the Studio profile is missing the `EnableProfiling` flag. Treat the field as optional — never assume it is populated.
- Numbers from a `StartDebugging` profile run differ from `StartExecution` — the debugger adds tracking overhead. For perf comparisons, always use `StartExecution`.
- Files are not auto-cleaned. After an investigation, manually clear `%LOCALAPPDATA%\UiPath\ProfiledRuns\` if disk usage matters.
- Profiling is per run, not aggregated across runs. To compare two implementations, run each with `--profiling true` separately and diff the `*.uistat` reports.

> **Activity-targeted profiling needs Studio Desktop.** `TestActivity` and `StartDebuggingFromHere` collect profiling fine, but they depend on `focus-activity` — which only runs against Studio Desktop. See [Studio Desktop vs headless](#studio-desktop-vs-headless).

---

## Reading Debug Output Effectively

Read `runResult` fields in this order. **Verdict comes from the outer `Result` envelope (equivalently inner `HasErrors`) — never from log-entry levels.**

1. **Outer `Result` / inner `HasErrors`** — the only success/failure signal. Compile failures, validation failures, and unhandled runtime exceptions all flip these. If `Result: "Success"` (`HasErrors: false`), the run succeeded — even if log entries streamed during the run contain `Error` / `Warning` levels.
2. **`ErrorMessage` (when `HasErrors: true`)** — formatted chain with the source activity, exception type, message, and stack trace. This is the canonical failure diagnostic.
3. **`Output` (when `HasErrors: false`)** — workflow's serialized output arguments JSON for `run` / `debug start` completions. Empty string `""` for debug-command responses (step / continue / cancel) and on failure.
4. **Streamed log entries** — diagnostic context emitted live during execution on a separate channel. Use them to read variable values logged by the workflow, trace ordering, or correlate context with an `ErrorMessage` that already failed the run. **Do NOT use log-entry `Level` as a failure signal.**

> **Anti-pattern: treating a streamed log entry's `Level == "Error"` or `"Warning"` as a `run` / `debug start` failure.** Workflows routinely emit `Log Message` at `Error` / `Warning` to record handled exceptions, validation results, or business outcomes. The run completes successfully and `HasErrors` stays `false`. Reading log levels as a failure signal flips successful runs to "failed" and burns retries on a green workflow.

### Identifying the Root Cause from Debug Output

A practical example — a workflow makes an HTTP request and tries to deserialize the response as JSON, but fails:

- **`HasErrors: true`** with `ErrorMessage` carrying `JsonReaderException: Unexpected character encountered while parsing value: T` — the deserializer tried to parse a non-JSON response
- **Streamed log entries** (or workflow `Log Message` activities) reveal the HTTP response variable had `StatusCode: "TooManyRequests"` and `TextContent: "Too Many Requests\r\n"` — the API returned a 429, not JSON
- **Fix**: Add status code checking before deserialization, or add retry logic with backoff to the HTTP request

---

## Best Practices

- **Always use `--output json`** for debug verbs when you need to parse the output programmatically. The structured output makes it easy to inspect variables and identify exceptions.
- **Set breakpoints strategically** — place them just before the activity you suspect is failing, not at the very start. This avoids stepping through dozens of unrelated activities.
- **Use `focus-activity` before `debug toggle-breakpoint`** to target a specific activity by its IdRef — Studio Desktop required. Without focusing first, the breakpoint is set on whatever activity or workflow is currently focused, which on a headless-only run means the entire workflow.
- **Use `debug test-activity` for quick feedback** — it runs a single activity in isolation, which is faster than debugging the entire workflow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` so the activity has the data it needs.
- **Use `debug start-from-here` to skip setup** — when the bug is deep in the workflow, skip straight to the relevant activity instead of stepping through the entire flow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` to simulate the state the activity would have received from preceding activities.
- **Prefer `debug step-over` for quick inspection** — it moves one activity at a time without descending into scopes. Use `debug step-into` only when you need to examine what happens inside a loop iteration or nested sequence.
- **Check variables after each step** — read the streamed log entries (and workflow `Log Message` output) to see the current state of in-scope variables. The runResult itself only carries `Output` (workflow output args), `HasErrors`, and `ErrorMessage`.
- **Use `debug continue-retry` for transient errors** — if the exception is a network timeout or rate limit, retrying may succeed without any code changes.
- **Use `debug continue-ignore` cautiously** — it skips the exception, which may leave variables in an unexpected state for downstream activities.
- **Cancel the session when done** — always issue `execution cancel` to cleanly end the run or debug session.
- **Use `--log-level Verbose`** when you need maximum detail about what the workflow is doing between steps.
- **Remember expression syntax for variables** — when using `debug test-activity` or `debug start-from-here`, string values need VB/C# string literal quotes inside the JSON value (e.g., `"\"hello\""` not `"hello"`).
- **Reach for `--profiling true` when investigating performance or verifying UI automation correctness** — pair it with `StartExecution` for production-like numbers (the debugger adds overhead). Read the response's `Profiling.OutputDirectory`: open the `*.uistat` files starting with activities holding the largest cumulative percentage, and inspect the captured screenshots to confirm each UI interaction landed on the expected screen / element. See [Profiling Workflow Performance](#profiling-workflow-performance).
