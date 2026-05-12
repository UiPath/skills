# Debugging Workflows with `uip rpa run-file`

The `uip rpa run-file` command provides full interactive debugging capabilities for both XAML workflows and coded (.cs) files. Beyond simple execution (`StartExecution`), it supports breakpoints, step-by-step execution, exception handling, isolated activity testing, and runtime state inspection — all from the CLI.

This is a powerful complement to `get-errors` (static validation). While `get-errors` catches structural and type issues at design time, the debugger catches runtime problems: wrong API responses, null references, logic errors, failed deserialization, and more. Use both together for comprehensive workflow validation.

## Studio Desktop vs headless

Most debugging works on **headless Studio** with no Studio Desktop install: `StartExecution`, `StartDebugging` (with workflow-level breakpoint), all stepping commands (`StepOver`, `StepInto`, `StepOut`), `Continue`, `Break`, `Resume`, `ContinueRetry`, `ContinueIgnore`, `Stop`, `RestartFromTop`, `ForceSessionEnded`.

**Studio Desktop is required** for any flow that targets a specific activity, because activity targeting goes through `uip rpa focus-activity` and that tool only runs against Studio Desktop:

| Command | Why it needs Studio Desktop |
|---------|------------------------------|
| `TestActivity` | Operates on the focused activity — requires `focus-activity` first |
| `StartDebuggingFromHere` | Operates on the focused activity — requires `focus-activity` first |
| `ToggleBreakpoint` *targeted to a specific activity* | Targeting requires `focus-activity` first. Without focusing, the breakpoint toggles on the whole workflow (still works headless) |

Before invoking any of the above, run `uip rpa start-studio --project-dir "<PROJECT_DIR>" --output json` and ensure the project is open in Studio Desktop. See [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop).

---

## Command Reference

All commands share these base parameters:

```bash
uip rpa run-file --file-path <relative-path> --command <Command> [--input-arguments '<json>'] [--input-variables '<json>'] [--log-level <level>] [--output json]
```

| Parameter | Description |
|-----------|-------------|
| `--file-path` | File path of the workflow to run (relative to project root) |
| `--command` | The debug command to execute (see table below). Defaults to `StartExecution` |
| `--input-arguments` | JSON object with project-level input arguments. Only for `StartExecution`, `StartDebugging`, `TestActivity`, and `StartDebuggingFromHere` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--input-variables` | JSON object with workflow-level variable values. Only for `TestActivity` and `StartDebuggingFromHere` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--log-level` | Minimum log level: `Verbose`, `Trace`, `Information` (default), `Warning`, `Error`, `Critical` |
| `--profiling` | Collect per-activity timings. Only effective on start commands (`StartExecution`, `StartDebugging`, `TestActivity`, `StartDebuggingFromHere`); ignored on stepping / breakpoint commands. Defaults to `false`. See [Profiling Workflow Performance](#profiling-workflow-performance). |
| `--output` | Output format: `json` (recommended), `table`, `yaml`, `plain` |

### Debug Commands

| Command | When to Use | What It Does |
|---------|-------------|--------------|
| `StartExecution` | Run without debugging | Executes the workflow to completion. Default if `--command` is omitted |
| `StartDebugging` | Begin a debug session | Starts execution in debug mode. Pauses at the first breakpoint (or at the first activity if a breakpoint is set on the workflow itself). Returns current execution state |
| `TestActivity` | Test one activity in isolation | Isolates the currently focused activity and executes it in a temporary test workflow. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `StartDebuggingFromHere` | Debug from a specific activity | Starts a debugging session from the currently focused activity, skipping all preceding activities. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `ToggleBreakpoint` | Set/remove breakpoints | Toggles a breakpoint on the currently focused activity (XAML) or line (.cs). Use `uip rpa focus-activity` to focus beforehand — **activity-targeted toggling requires Studio Desktop**. For XAML, cycles through 3 states: **enabled → disabled → no breakpoint**. For .cs, cycles through 2 states: **breakpoint → no breakpoint**. If no activity/line is focused, toggles on the entire workflow (works on Helm) |
| `StepOver` | Execute one activity and pause | Executes the current activity, then pauses at the next sibling activity. Does not enter child scopes (e.g., stays at the For Each level, doesn't step into its body) |
| `StepInto` | Drill into child activities | Executes and pauses at the first child activity inside the current scope. Use to enter loops, sequences, Try-Catch blocks, etc. |
| `StepOut` | Exit the current scope | Continues execution until the current scope completes, then pauses at the parent level. Use to leave a loop body or nested sequence |
| `Continue` | Run to next breakpoint | Resumes execution until the next breakpoint is hit or an exception occurs |
| `Break` | Pause execution | Pauses a running debug session at the current point of execution |
| `Resume` | Resume from suspended state | Resumes execution when the workflow is in a suspended (not just paused) state |
| `ContinueRetry` | Retry after exception | Resumes execution and **retries the current activity** that caused the exception. Use when you've fixed the underlying issue (e.g., network timeout) and want to try again |
| `ContinueIgnore` | Skip past exception | Resumes execution and **ignores the exception** on the current activity. Use when the error is non-critical and you want to proceed |
| `Stop` | End the session | Stops the current debugging or execution session |
| `RestartFromTop` | Start over | Restarts execution from the beginning of the workflow without ending the debug session. Breakpoints are preserved |
| `ForceSessionEnded` | Force-kill the session | Forces the session to end immediately. Use as a last resort when `Stop` doesn't respond |

---

## Input Variables vs Input Arguments

These serve different purposes and apply to different scopes:

- **Arguments** (`--input-arguments`) are **project-level In/Out/InOut parameters** defined in the project's argument list. They are the workflow's public interface — how callers pass data in and receive data back. Applicable for `StartExecution`, `StartDebugging`, `TestActivity`, and `StartDebuggingFromHere`.

- **Variables** (`--input-variables`) are **workflow-level local state** declared inside the workflow and scoped to specific activities or containers (e.g., a Sequence, a For Each body). They are internal to the workflow and not visible from outside. Only applicable for `TestActivity` and `StartDebuggingFromHere` — these commands execute from a specific activity's context, so you can pre-set the variables that activity reads from.

| | `--input-arguments` | `--input-variables` |
|---|---|---|
| **What they are** | Project-level parameters (In/Out/InOut) | Workflow-internal variables scoped to activities |
| **Where defined** | Project argument list (visible in Studio's Arguments panel) | Inside the workflow (visible in Studio's Variables panel) |
| **Applicable commands** | `StartExecution`, `StartDebugging`, `TestActivity`, `StartDebuggingFromHere` | `TestActivity`, `StartDebuggingFromHere` only |
| **Value format (StartExecution/StartDebugging)** | Plain JSON values: `{"name":"John","age":30}` | N/A |
| **Value format (TestActivity/StartDebuggingFromHere)** | VB.NET or C# expressions | VB.NET or C# expressions |

### Expression Value Examples

For `TestActivity` and `StartDebuggingFromHere`, both `--input-arguments` and `--input-variables` values must be **VB.NET or C# expressions** matching the project language.

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

`run-file` returns a JSON envelope with `Data.runResult` as a JSON-encoded string. Parse `runResult` separately. It has exactly three fields:

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
| `Output` | `string` | Workflow's serialized output arguments JSON. `""` for non-`Start*` commands and on debug-command responses (`StepOver`, `Continue`, etc.). **Carries the workflow's data, not a verdict.** |
| `HasErrors` | `bool` | `true` iff execution did not complete with `Succeeded` (compile failure, validation failure, unhandled exception, cancellation, timeout). `false` otherwise. |
| `ErrorMessage` | `string?` | Formatted error chain when `HasErrors: true`; `null` otherwise. |
| `Profiling` | `object?` | Present only when `--profiling` was passed on a start command and collection succeeded. Single field `OutputDirectory` — absolute path to the run's `*.uistat` folder. `null` / omitted otherwise. See [Profiling Workflow Performance](#profiling-workflow-performance). |

Workflow log output (`Log Message` activity, system traces) is **streamed in real time** during execution on a separate channel. It is NOT embedded in `runResult`.

> **`Result` (outer) — equivalently `HasErrors` (inner) — is the only success/failure signal.** `Result: "Success"` already accounts for compile failures, validation failures, and unhandled runtime exceptions. **Do NOT use streamed log entries' `Level` as a failure signal** — workflow `Log Message` activities emit at any level, and successful runs commonly include `Error` / `Warning` entries from the workflow's own logging. Treating log levels as a verdict flips green runs to "failed".

Examples:

```jsonc
// Successful run — workflow logged a warning, but HasErrors is false
{ "Output": "{\"resultCode\":\"OK\"}", "HasErrors": false, "ErrorMessage": null }

// Failed run — compile or runtime failure
{ "Output": "", "HasErrors": true, "ErrorMessage": "Source: HttpRequest_1\nMessage: ..." }

// Debug-command response (StepOver / Continue / etc.) — empty success
{ "Output": "", "HasErrors": false, "ErrorMessage": null }
```

---

## Choosing the Right Command

| Situation | Command | Why |
|-----------|---------|-----|
| "Run the whole workflow and check the result" | `StartExecution` | Full run, no debugging overhead |
| "This one activity isn't working — test it with specific inputs" | `TestActivity` | Isolates the activity, fastest feedback loop |
| "The bug is in activity X but I need the debug session to step through from there" | `StartDebuggingFromHere` | Skips everything before X, gives full debug control from that point |
| "I need to step through the entire workflow from the start" | `StartDebugging` | Full debug session with breakpoints, stepping, variable inspection |
| "I want to verify the fix works at runtime after editing" | `StartExecution` or `TestActivity` | Quick validation — use TestActivity if you only changed one activity |

---

## Common Debugging Workflows

### 1. Quick Breakpoint Debug Session

The most common pattern: set a breakpoint on the focused activity, start debugging, inspect state, then continue or step through.

> **Studio Desktop required** for activity-targeted breakpoints (the `focus-activity` step). Skip step 1 to set a workflow-level breakpoint instead — that path runs headless.

```bash
# 1. Focus the activity you want to break at (Studio Desktop only — skip to break at the workflow level)
uip rpa focus-activity --activity-id "Assign_1"

# 2. Toggle a breakpoint on the focused activity
uip rpa run-file --file-path "GetStockPrices.xaml" --command ToggleBreakpoint --output json

# 3. Start debugging — execution pauses at the breakpoint
uip rpa run-file --file-path "GetStockPrices.xaml" --command StartDebugging --output json

# 4. Inspect the response: HasErrors / ErrorMessage / Output (workflow output args).
#    Variable values seen during the run are observed via streamed log entries.
# Then step through or continue:
uip rpa run-file --file-path "GetStockPrices.xaml" --command StepOver --output json

# 5. When done, stop the session
uip rpa run-file --file-path "GetStockPrices.xaml" --command Stop --output json
```

### 2. Test a Single Activity in Isolation

Use `TestActivity` to run just the currently focused activity without executing the entire workflow. Useful for verifying an activity works with specific inputs.

> **Studio Desktop required** — `focus-activity` and `TestActivity` both rely on it. On a headless-only setup, fall back to a workflow-level `StartDebugging` with a breakpoint placed earlier in the file.

```bash
# 1. Focus the activity to test (Studio Desktop required)
uip rpa focus-activity --activity-id "DeserializeJson_1"

# 2. Run it in isolation, pre-setting any variables it reads from
uip rpa run-file --file-path "GetBucharestTemperature.xaml" \
  --command TestActivity \
  --input-variables '{"temperature": "\"200\""}' \
  --output json

# 3. Check the output:
#    - HasErrors / ErrorMessage → compile/validation issues, unhandled exceptions
#    - Streamed log entries → runtime messages from the activity (observability, not a verdict)
#    - Output → workflow's serialized output args on success
```

### 3. Debug From a Specific Activity

Use `StartDebuggingFromHere` to skip straight to the activity you care about, avoiding stepping through earlier activities.

> **Studio Desktop required** — `focus-activity` and `StartDebuggingFromHere` both rely on it. On a headless-only setup, use plain `StartDebugging` with a workflow-level breakpoint near the activity instead.

```bash
# 1. Focus the activity to start from (Studio Desktop required)
uip rpa focus-activity --activity-id "HttpRequest_1"

# 2. Start debugging from that point, pre-setting variables
uip rpa run-file --file-path "GetBucharestTemperature.xaml" \
  --command StartDebuggingFromHere \
  --input-variables '{"apiUrl": "\"https://api.example.com/weather\""}' \
  --output json

# 3. The debugger runs from the focused activity — step through or continue
uip rpa run-file --file-path "GetBucharestTemperature.xaml" --command StepOver --output json

# 4. Stop when done
uip rpa run-file --file-path "GetBucharestTemperature.xaml" --command Stop --output json
```

### 4. Exception Investigation

When `Continue` or a step command hits an exception, the debugger pauses and returns the exception details. You can inspect the state, then decide how to proceed.

```bash
# Start debugging and continue to let it run
uip rpa run-file --file-path "MyWorkflow.xaml" --command StartDebugging --output json
uip rpa run-file --file-path "MyWorkflow.xaml" --command Continue --output json

# If an unhandled exception occurs, HasErrors flips to true and ErrorMessage carries
# the formatted exception chain (source activity, type, message, stack trace).
# - Read ErrorMessage for the canonical failure diagnostic
# - Cross-reference streamed log entries for variable state and trace context
#   leading up to the failure

# Then choose how to proceed:
# Option A: Retry the failed activity (e.g., transient network error)
uip rpa run-file --file-path "MyWorkflow.xaml" --command ContinueRetry --output json

# Option B: Ignore the exception and continue past it
uip rpa run-file --file-path "MyWorkflow.xaml" --command ContinueIgnore --output json

# Option C: Stop and fix the root cause
uip rpa run-file --file-path "MyWorkflow.xaml" --command Stop --output json
```

### 5. Runtime Validation After Edits

Use debugging to verify that a fix actually works at runtime, beyond what `get-errors` (static validation) can check.

```bash
# 1. Run static validation first
uip rpa get-errors --file-path "MyWorkflow.xaml" --output json

# 2. If 0 static errors, start a debug session to validate runtime behavior
uip rpa run-file --file-path "MyWorkflow.xaml" --command StartDebugging --output json

# 3. Continue past the fixed area and inspect variable state
uip rpa run-file --file-path "MyWorkflow.xaml" --command Continue --output json

# 4. Check the response for:
#    - Outer Result is "Success" (HasErrors: false) — the canonical pass/fail signal
#    - Output (workflow's serialized output args) carries the expected values
#    - Streamed log entries during the run are diagnostic context, NOT a failure signal —
#      Error/Warning levels there are workflow-emitted observability, not CLI failures

# 5. Stop
uip rpa run-file --file-path "MyWorkflow.xaml" --command Stop --output json
```

### 6. Debugging with Input Arguments

Pass input arguments when the workflow has In arguments that need values:

```bash
# Start debugging with input arguments (plain JSON values)
uip rpa run-file --file-path "ProcessOrder.xaml" \
  --command StartDebugging \
  --input-arguments '{"orderId": "ORD-12345", "customerEmail": "test@example.com"}' \
  --output json
```

`--input-arguments` is valid with `StartExecution`, `StartDebugging`, `TestActivity`, and `StartDebuggingFromHere`. For `StartExecution`/`StartDebugging`, values are plain JSON. For `TestActivity`/`StartDebuggingFromHere`, values must be VB/C# expressions.

---

## Profiling Workflow Performance

Use `--profiling` on a start command to collect per-activity timings — the same data Studio's **Profile Execution** tool surfaces. The executor writes `*.uistat` files into `%LOCALAPPDATA%\UiPath\ProfiledRuns\HHmmss_yyyy-MM-dd_<entryPoint>_<projectName>\` and the response carries the absolute path on `runResult.Profiling.OutputDirectory`. Same folder layout as Studio's own profiling history, so agent-triggered and Studio-triggered runs land side by side.

### When to enable profiling

| Situation | Why |
|-----------|-----|
| User reports a slow workflow ("X takes 5 min, was 30 s last week") | Profiling localizes the regression to specific activities instead of the whole workflow |
| Choosing between two implementations of the same logic | Compare cumulative time across the activities each version uses |
| A loop body looks expensive but the cost is not obvious | `*.uistat` reports execution count + min/max/avg per activity — flags hot iterations |
| Pre-production sanity check on a long-running automation | Catches an activity whose individual time looks fine but whose cumulative share is dominant |

Do **not** enable profiling by default. It is opt-in for performance investigations — a normal smoke test (`uip rpa run-file --command StartExecution`) is faster and produces no `.uistat` files to clean up.

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

The directory contains `*.uistat` files — one per workflow file executed in the run (top-level entry point plus every invoked workflow). Each row reports an activity with execution count, min / max / average / cumulative duration, and the cumulative percentage of total run time. Focus on:

1. **Activities with the largest cumulative percentage** — the dominant time sinks. Optimize these first.
2. **High execution count × moderate average duration** — typically loop bodies. Consider batching, caching, or hoisting work out of the loop.
3. **Wide min/max spread on a UI activity** — flaky selectors or variable target-element resolution; cross-check with the healing-agent log.

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
3. **`Output` (when `HasErrors: false`)** — workflow's serialized output arguments JSON for `StartExecution` / `StartDebugging` completions. Empty string `""` for debug-command responses (step / continue / stop) and on failure.
4. **Streamed log entries** — diagnostic context emitted live during execution on a separate channel. Use them to read variable values logged by the workflow, trace ordering, or correlate context with an `ErrorMessage` that already failed the run. **Do NOT use log-entry `Level` as a failure signal.**

> **Anti-pattern: treating a streamed log entry's `Level == "Error"` or `"Warning"` as a run-file failure.** Workflows routinely emit `Log Message` at `Error` / `Warning` to record handled exceptions, validation results, or business outcomes. The run completes successfully and `HasErrors` stays `false`. Reading log levels as a failure signal flips successful runs to "failed" and burns retries on a green workflow.

### Identifying the Root Cause from Debug Output

A practical example — a workflow makes an HTTP request and tries to deserialize the response as JSON, but fails:

- **`HasErrors: true`** with `ErrorMessage` carrying `JsonReaderException: Unexpected character encountered while parsing value: T` — the deserializer tried to parse a non-JSON response
- **Streamed log entries** (or workflow `Log Message` activities) reveal the HTTP response variable had `StatusCode: "TooManyRequests"` and `TextContent: "Too Many Requests\r\n"` — the API returned a 429, not JSON
- **Fix**: Add status code checking before deserialization, or add retry logic with backoff to the HTTP request

---

## Best Practices

- **Always use `--output json`** for debug commands when you need to parse the output programmatically. The structured output makes it easy to inspect variables and identify exceptions.
- **Set breakpoints strategically** — place them just before the activity you suspect is failing, not at the very start. This avoids stepping through dozens of unrelated activities.
- **Use `focus-activity` before `ToggleBreakpoint`** to target a specific activity by its IdRef — Studio Desktop required. Without focusing first, the breakpoint is set on whatever activity or workflow is currently focused, which on a headless-only run means the entire workflow.
- **Use `TestActivity` for quick feedback** — it runs a single activity in isolation, which is faster than debugging the entire workflow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` so the activity has the data it needs.
- **Use `StartDebuggingFromHere` to skip setup** — when the bug is deep in the workflow, skip straight to the relevant activity instead of stepping through the entire flow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` to simulate the state the activity would have received from preceding activities.
- **Prefer `StepOver` for quick inspection** — it moves one activity at a time without descending into scopes. Use `StepInto` only when you need to examine what happens inside a loop iteration or nested sequence.
- **Check variables after each step** — read the streamed log entries (and workflow `Log Message` output) to see the current state of in-scope variables. The runResult itself only carries `Output` (workflow output args), `HasErrors`, and `ErrorMessage`.
- **Use `ContinueRetry` for transient errors** — if the exception is a network timeout or rate limit, retrying may succeed without any code changes.
- **Use `ContinueIgnore` cautiously** — it skips the exception, which may leave variables in an unexpected state for downstream activities.
- **Stop the session when done** — always issue a `Stop` command to cleanly end the debug session. If `Stop` doesn't respond, use `ForceSessionEnded` as a fallback.
- **Use `--log-level Verbose`** when you need maximum detail about what the workflow is doing between steps.
- **Remember expression syntax for variables** — when using `TestActivity` or `StartDebuggingFromHere`, string values need VB/C# string literal quotes inside the JSON value (e.g., `"\"hello\""` not `"hello"`).
- **Reach for `--profiling true` only when investigating performance** — pair it with `StartExecution` for production-like numbers (the debugger adds overhead). Read the response's `Profiling.OutputDirectory`, open the `*.uistat` files, and start with activities holding the largest cumulative percentage. See [Profiling Workflow Performance](#profiling-workflow-performance).
