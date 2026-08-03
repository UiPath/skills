# Debugging Workflows with the `debug` group

The `uip rpa debug` group (plus `uip rpa run` and `uip rpa execution cancel`) provides full interactive debugging for both XAML workflows and coded (.cs) files. Beyond simple execution (`run`), it supports breakpoints, step-by-step execution, exception handling, isolated activity testing, and runtime state inspection — all from the CLI.

This is a powerful complement to `validate` (static validation). While `validate` catches structural and type issues at design time, the debugger catches runtime problems: wrong API responses, null references, logic errors, failed deserialization, and more. Use both together for comprehensive workflow validation.

## Studio Desktop vs headless

Most debugging works on **headless Studio** with no Studio Desktop install: `run`, `debug start` (including **activity-targeted breakpoints via `--breakpoints`**), all stepping verbs (`debug step-over`, `debug step-into`, `debug step-out`), `debug continue`, `debug break`, `debug resume`, `debug continue-retry`, `debug continue-ignore`, `debug state`, `debug set-breakpoints`, `execution cancel`, `debug restart-from-top`.

On the headless backend, every debug command **returns at the next stable state** — paused at an activity, suspended on an exception, or completed — carrying `DebugState` / `DebugDetails` in the result, so you always learn where execution stands from the command's own response. See [The stable-state debug loop](#the-stable-state-debug-loop-headless).

**Studio Desktop is required** for any flow that targets the *focused* activity, because focusing goes through `uip rpa focus-activity` and only Studio Desktop has a designer to focus:

| Command | Why it needs Studio Desktop |
|---------|------------------------------|
| `debug test-activity` | Operates on the focused activity — requires `focus-activity` first. Headless rejects the command |
| `debug start-from-here` | Operates on the focused activity — requires `focus-activity` first. Headless rejects the command |
| `debug toggle-breakpoint` | Toggles on the focused activity/line — requires `focus-activity` first. Headless rejects the command; set headless breakpoints with `--breakpoints` on `debug start` (or `debug set-breakpoints` mid-session), which target activities by IdRef with no focusing step |

> **`focus-activity` on headless is a silent no-op** — it returns `success: true` but focuses nothing (there is no designer). Do NOT use it to "target" an activity for a headless debug flow and do not treat its success as confirmation: on headless, the focus-dependent verbs above fail with `Unknown command` regardless, and activity targeting goes through `--breakpoints` instead.

Before invoking any of the above, run `uip rpa studio start --project-dir "<PROJECT_DIR>" --output json` and ensure the project is open in Studio Desktop. See [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop).

---

## Command Reference

`run` and `debug start` take a file path and optional inputs:

```bash
uip rpa run         --file-path <relative-path> [--input-arguments key=value]... [--log-level <level>] [--skip-build] [--output json]
uip rpa debug start --file-path <relative-path> [--input-arguments key=value]... [--breakpoints item]... [--log-level <level>] [--skip-build] [--output json]
```

`debug test-activity` and `debug start-from-here` operate on the currently focused activity (no `--file-path`):

```bash
uip rpa debug test-activity     [--input-arguments key=value]... [--input-variables key=value]... [--log-level <level>] [--output json]
uip rpa debug start-from-here   [--input-arguments key=value]... [--input-variables key=value]... [--log-level <level>] [--output json]
```

The mid-session verbs (`break`, `continue`, `resume`, `continue-retry`, `continue-ignore`, `step-into`, `step-over`, `step-out`, `state`) operate on the active debug session and take only the optional `--wait-timeout-seconds`. `debug set-breakpoints` takes `--breakpoints`. `debug toggle-breakpoint` and `debug restart-from-top` take no parameters.

| Parameter | Description |
|-----------|-------------|
| `--file-path` | Workflow file to run (relative to project root). Applies to `run` and `debug start` only |
| `--input-arguments` | Project-level input arguments as repeatable `key=value` pairs (`=` string, `:=` raw JSON; see [cli-reference.md § Passing structured inputs](cli-reference.md#passing-structured-inputs)). Only for `run`, `debug start`, `debug test-activity`, and `debug start-from-here` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--input-variables` | Workflow-level variable values as repeatable `key=value` pairs (values are VB/C# expressions — always `=`). Only for `debug test-activity` and `debug start-from-here` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--breakpoints` | Activity breakpoints for XAML debugging (headless backend). One array item per flag occurrence, comma-separated `key=value` inside an item: `--breakpoints 'workflowFile=Main.xaml,activityIdRef=Assign_1'`. Keys: `workflowFile` (required; workflow path relative to the project root), `activityIdRef` (the target activity's `sap2010:WorkflowViewState.IdRef` attribute value from the XAML — the stable way to address an activity you can read straight from the file), optional `condition` (VB/C# expression; breaks only when it evaluates to True), `hitCount:=N` (break only on exactly the Nth hit), `enabled` (defaults to true). Whole payload from a file: `--breakpoints-file breakpoints.json`. Used by `debug start` (initial set) and `debug set-breakpoints` (replaces the running session's whole set) |
| `--wait-timeout-seconds` | Maximum seconds a mid-session verb waits for the next stable state before returning `DebugState: "Running"` instead of hanging. Default 120 (0 for `debug state`, making it an instant probe). Headless backend only |
| `--log-level` | Minimum log level: `Verbose`, `Trace` (default), `Information`, `Warning`, `Error`, `Critical` |
| `--skip-build` | Skip the pre-run build step (use only when you've just built) |
| `--output` | Output format: `json` (recommended), `table`, `yaml`, `plain` |
| `--profiling` | Collect per-activity timings and runtime screenshots — verifies UI automation correctness and workflow performance. Only effective on start verbs (`run`, `debug start`, `debug test-activity`, `debug start-from-here`); ignored on stepping / breakpoint verbs. Boolean flag (no value needed). See [Profiling Workflow Performance](#profiling-workflow-performance). |

### Debug Verbs

| Verb | When to Use | What It Does |
|------|-------------|--------------|
| `run` | Run without debugging | Executes the workflow to completion. The default authoring loop verb |
| `debug start` | Begin a debug session | Starts execution in debug mode and **returns at the first stable state**: `Paused` at a breakpoint (pass `--breakpoints` to set them), `Suspended` on an unhandled exception, or `Completed` if nothing interrupts the run. The response's `DebugState` / `DebugDetails` say where execution stands; the session stays alive for the mid-session verbs |
| `debug test-activity` | Test one activity in isolation | Isolates the currently focused activity and executes it in a temporary test workflow. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `debug start-from-here` | Debug from a specific activity | Starts a debugging session from the currently focused activity, skipping all preceding activities. **Requires `focus-activity` first → Studio Desktop required** (see [Studio Desktop vs headless](#studio-desktop-vs-headless)). Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `debug toggle-breakpoint` | Set/remove breakpoints interactively (Studio Desktop only) | Toggles a breakpoint on the currently focused activity (XAML) or line (.cs). Use `uip rpa focus-activity` to focus beforehand. For XAML, cycles through 3 states: **enabled → disabled → no breakpoint**. For .cs, cycles through 2 states: **breakpoint → no breakpoint**. **Not available headless** (rejected as an unknown command) — use `--breakpoints` on `debug start` or `debug set-breakpoints` instead |
| `debug step-over` | Execute one activity and pause | Executes the current activity, then pauses at the next sibling activity. Does not enter child scopes (e.g., stays at the For Each level, doesn't step into its body). Returns the new paused state with locals |
| `debug step-into` | Drill into child activities | Executes and pauses at the first child activity inside the current scope. Use to enter loops, sequences, Try-Catch blocks, etc. Returns the new paused state with locals |
| `debug step-out` | Exit the current scope | Continues execution until the current scope completes, then pauses at the parent level. Use to leave a loop body or nested sequence. Returns the new paused state with locals |
| `debug continue` | Run to next breakpoint | Resumes execution and returns at the next stable state — the next breakpoint (`Paused`), an exception (`Suspended`), or the end of the run (`Completed`) |
| `debug break` | Pause execution | Pauses a running debug session at the next executed activity and returns the paused state with locals |
| `debug state` | Inspect without side effects | Reports the session's current `DebugState` (`Running`, `Paused`, `Suspended`, `Completed`, or `None` when no session is active) plus the last captured details. Instant by default; pass `--wait-timeout-seconds` to long-poll a running session for its next stable state |
| `debug set-breakpoints` | Change breakpoints mid-session | Replaces the active session's **whole** breakpoint set with the `--breakpoints` payload. For a new session, pass `--breakpoints` on `debug start` instead |
| `debug resume` | Resume from suspended state | Resumes execution when the workflow is in a suspended (not just paused) state |
| `debug continue-retry` | Retry after exception | Resumes execution and **retries the current activity** that caused the exception. Use when you've fixed the underlying issue (e.g., network timeout) and want to try again |
| `debug continue-ignore` | Skip past exception | Resumes execution and **ignores the exception** on the current activity, pausing at the next activity. Use when the error is non-critical and you want to proceed |
| `execution cancel` | End the session | Cancels the currently active execution — works for both `run` and `debug start` |
| `debug restart-from-top` | Start over | Restarts execution from the beginning of the workflow without ending the debug session. Breakpoints are preserved |

---

## The stable-state debug loop (headless)

On the headless backend, debugging is a synchronous request/response loop: **every command returns when execution reaches the next stable state**, and the response tells you exactly where things stand. No command hangs waiting for a human — if nothing stable is reached within `--wait-timeout-seconds`, the response says `Running` and how to proceed.

`DebugState` values in the response:

| `DebugState` | Meaning | What to do next |
|---|---|---|
| `Paused` | Stopped at a breakpoint or after a step/break. `DebugDetails` carries the current activity (name, id, workflow file) and a snapshot of in-scope variables, arguments, and properties | Inspect `DebugDetails`, then `step-over` / `step-into` / `step-out` / `continue`, or `execution cancel` |
| `Suspended` | Stopped on an unhandled exception; the session is still alive. `DebugDetails` carries the exception type, message, faulting activity, and locals | `continue` to propagate the exception, `continue-retry` to re-run the faulted activity, `continue-ignore` to skip it, or `execution cancel` |
| `Completed` | The run finished. The response is the normal run result (`Output`, `HasErrors`, `ErrorMessage`) | Read the run result; the session is gone |
| `Running` | The wait timed out before a stable state was reached — execution is still going | Poll with `debug state`, send `debug break` to pause at the next activity, or `execution cancel` |
| `None` | No debug session is active | Start one with `debug start` |

The canonical loop:

```bash
# Start with breakpoints on the activities you care about — returns Paused at the first hit
uip rpa debug start --file-path Main.xaml \
  --breakpoints 'workflowFile=Main.xaml,activityIdRef=Assign_1' --output json

# Inspect DebugDetails (activity + locals), then advance — each call returns the next state
uip rpa debug step-over --output json
uip rpa debug continue  --output json

# If a response says Suspended, decide on the exception:
uip rpa debug continue-ignore --output json   # or continue-retry / continue / execution cancel

# Not sure what's happening? Probe without side effects:
uip rpa debug state --output json
```

Breakpoints are addressed by `activityIdRef` — the `sap2010:WorkflowViewState.IdRef` attribute you can read directly from the XAML you authored — so no `focus-activity` (and no Studio Desktop) is needed. Conditional breakpoints (`condition`) and hit counts (`hitCount:=N`) are evaluated by the runtime.

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
| **Value format (`run` / `debug start`)** | `key=value` pairs (`=` string, `:=` raw JSON): `name=John`, `age:=30` | N/A |
| **Value format (`debug test-activity` / `debug start-from-here`)** | VB.NET or C# expressions — always `=` | VB.NET or C# expressions — always `=` |

### Expression Value Examples

For `debug test-activity` and `debug start-from-here`, both `--input-arguments` and `--input-variables` values must be **VB.NET or C# expressions** matching the project language. Always use `=` pairs (the expression is a string — `:=` would corrupt it), one variable per flag occurrence. Expressions containing double quotes (string literals) cannot be passed inline on Windows PowerShell 5.1 — write them to a UTF-8 file and use `key=@file`.

**VB.NET projects:**
```bash
# Integer variable — the expression 42
--input-variables count=42

# Boolean variable (VB uses True/False, capitalized)
--input-variables isActive=True

# Null / unset (VB keyword)
--input-variables result=Nothing

# New object — single-quote tokens containing spaces
--input-variables 'config=New Dictionary(Of String, Object)'

# String variable — the expression needs quotes, so pass it from a file.
#   PowerShell: Set-Content -Encoding UTF8 greeting.txt '"Hello World"'
#   bash:       printf '"Hello World"' > greeting.txt
--input-variables greeting=@greeting.txt

# Multiple variables at once — repeat the flag
--input-variables name=@name-expr.txt --input-variables age=30 --input-variables isActive=True
```

**C# projects:**
```bash
# Boolean variable (C# uses true/false, lowercase)
--input-variables isActive=true

# Null / unset (C# keyword)
--input-variables result=null

# New object — single-quote tokens containing spaces
--input-variables 'config=new Dictionary<string, object>()'

# String variable — quoted literal goes through a file
--input-variables greeting=@greeting.txt
```

> **Important:** values are committed as expression text. `count=42` yields the expression `42` (an integer literal). To pass the *string* `"200"`, the expression must contain the quotes — `"200"` — which survives only via the file form: `temperature=@expr.txt` with the file containing `"200"`. Whole payloads can also be loaded from a JSON file: `--input-variables '@vars.json'` (single-quote the `@` token in PowerShell) or `--input-variables-file vars.json`.

---

## Output Format

`run` and `debug start` return a JSON envelope with `Data.runResult` as a JSON-encoded string. Parse `runResult` separately:

```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "runResult": "{\"output\":\"...\",\"hasErrors\":false,\"errorMessage\":null,\"debugState\":\"Completed\",\"debugDetails\":null}"
  }
}
```

Inside `runResult`:

| Field | Type | Meaning |
|-------|------|---------|
| `Output` | `string` | Workflow's serialized output arguments JSON, populated when the run completes. **Carries the workflow's data, not a verdict.** |
| `HasErrors` | `bool` | `true` iff execution finished without `Succeeded` (compile failure, validation failure, unhandled exception that ended the run, cancellation, timeout). `false` otherwise — including while `Suspended` on an exception, because the session is still alive and the outcome undecided. |
| `ErrorMessage` | `string?` | Formatted error chain when `HasErrors: true`. On debug responses it may instead carry **guidance** (e.g. which commands apply in a `Suspended` state) with `HasErrors: false`. `null` otherwise. |
| `DebugState` | `string?` | Debug sessions only (`null` on plain `run`): `Paused`, `Suspended`, `Running`, `Completed`, or `None`. See [The stable-state debug loop](#the-stable-state-debug-loop-headless). |
| `DebugDetails` | `string?` | Debug sessions only: JSON snapshot for the state — current activity + locals when `Paused`; exception type/message/activity + locals when `Suspended`; `null` otherwise. |
| `Profiling` | `object?` | Present only when `--profiling` was passed on a start command and collection succeeded. Single field `OutputDirectory` — absolute path to the run's `*.uistat` and screenshot folder (verifies UI automation correctness and workflow performance). `null` / omitted otherwise. See [Profiling Workflow Performance](#profiling-workflow-performance). |

Workflow log output (`Log Message` activity, system traces) is **streamed in real time** during execution on a separate channel. It is NOT embedded in `runResult`.

> **For completed runs, `Result` (outer) — equivalently `HasErrors` (inner) — is the only success/failure signal.** `Result: "Success"` already accounts for compile failures, validation failures, and unhandled runtime exceptions. **Do NOT use streamed log entries' `Level` as a failure signal** — workflow `Log Message` activities emit at any level, and successful runs commonly include `Error` / `Warning` entries from the workflow's own logging. Treating log levels as a verdict flips green runs to "failed". In an active debug session, check `DebugState` first: `Suspended` means an exception is waiting for your decision even though `HasErrors` is still `false`.

Examples:

```jsonc
// Successful completed run — workflow logged a warning, but hasErrors is false
{ "output": "{\"resultCode\":\"OK\"}", "hasErrors": false, "errorMessage": null, "debugState": "Completed", "debugDetails": null }

// Failed completed run — compile or runtime failure ended the session
{ "output": "", "hasErrors": true, "errorMessage": "Source: HttpRequest_1\nMessage: ...", "debugState": "Completed", "debugDetails": null }

// Paused at a breakpoint — current activity + locals in debugDetails
{ "output": "", "hasErrors": false, "errorMessage": null, "debugState": "Paused",
  "debugDetails": "{\"Activity\":\"Assign x\",\"ActivityId\":\"1.5\",\"WorkflowFile\":\"...\\Main.xaml\",\"Locals\":{...}}" }

// Suspended on an exception — session alive, hasErrors still false, errorMessage carries guidance
{ "output": "", "hasErrors": false,
  "errorMessage": "Execution suspended on an unhandled exception; the session is still alive. Send Continue..., ContinueRetry..., ContinueIgnore..., or Stop...",
  "debugState": "Suspended",
  "debugDetails": "{\"ExceptionType\":\"System.InvalidOperationException\",\"Message\":\"...\",\"Activity\":\"Throw\",\"Locals\":{...}}" }
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

The most common pattern: start debugging with breakpoints on the activities you suspect, inspect the state each pause returns, then step or continue. Runs fully headless — breakpoints are addressed by the activity's `IdRef` straight from the XAML, no focusing step.

```bash
# 1. Start debugging with a breakpoint — returns Paused at the breakpoint,
#    with the current activity and locals in DebugDetails
uip rpa debug start --file-path "GetStockPrices.xaml" \
  --breakpoints 'workflowFile=GetStockPrices.xaml,activityIdRef=Assign_1' \
  --output json

# 2. Read DebugDetails: current activity + variables/arguments/properties snapshot.
#    Then step through — each call returns the next paused state with fresh locals:
uip rpa debug step-over --output json

# 3. Or run to the next breakpoint / completion:
uip rpa debug continue --output json

# 4. When done, cancel the session (skip if the last response was already Completed)
uip rpa execution cancel --output json
```

Conditional breakpoints and hit counts work the same way:

```bash
--breakpoints 'workflowFile=Main.xaml,activityIdRef=Assign_1,condition=count > 3'
--breakpoints 'workflowFile=Main.xaml,activityIdRef=Click_2,hitCount:=3'
```

> On Studio Desktop, the interactive alternative is `focus-activity` + `debug toggle-breakpoint` (see [Studio Desktop vs headless](#studio-desktop-vs-headless)).

### 2. Test a Single Activity in Isolation

Use `debug test-activity` to run just the currently focused activity without executing the entire workflow. Useful for verifying an activity works with specific inputs.

> **Studio Desktop required** — `focus-activity` and `debug test-activity` both rely on it (headless rejects `debug test-activity`, and `focus-activity` silently no-ops). On a headless-only setup, fall back to `debug start --breakpoints 'workflowFile=<file>,activityIdRef=<IdRef>'` — pause right at the activity, inspect its inputs in `DebugDetails`, then step over it and check the result.

```bash
# 1. Focus the activity to test (Studio Desktop required)
uip rpa focus-activity --activity-id "DeserializeJson_1"

# 2. Run it in isolation, pre-setting any variables it reads from.
#    temperature is a String — its expression needs quotes, so pass it from a file:
#    PowerShell: Set-Content -Encoding UTF8 temp-expr.txt '"200"'   bash: printf '"200"' > temp-expr.txt
uip rpa debug test-activity \
  --input-variables temperature=@temp-expr.txt \
  --output json

# 3. Check the output:
#    - HasErrors / ErrorMessage → compile/validation issues, unhandled exceptions
#    - Streamed log entries → runtime messages from the activity (observability, not a verdict)
#    - Output → workflow's serialized output args on success
```

### 3. Debug From a Specific Activity

Use `debug start-from-here` to skip straight to the activity you care about, avoiding stepping through earlier activities.

> **Studio Desktop required** — `focus-activity` and `debug start-from-here` both rely on it (headless rejects `debug start-from-here`, and `focus-activity` silently no-ops). On a headless-only setup, use `debug start --breakpoints 'workflowFile=<file>,activityIdRef=<IdRef>'` — the run starts from the top, but pauses at the activity you care about with locals in hand.

```bash
# 1. Focus the activity to start from (Studio Desktop required)
uip rpa focus-activity --activity-id "HttpRequest_1"

# 2. Start debugging from that point, pre-setting variables.
#    apiUrl is a String — its expression needs quotes, so pass it from a file:
#    PowerShell: Set-Content -Encoding UTF8 api-url.txt '"https://api.example.com/weather"'
uip rpa debug start-from-here \
  --input-variables apiUrl=@api-url.txt \
  --output json

# 3. The debugger runs from the focused activity — step through or continue
uip rpa debug step-over --output json

# 4. Cancel when done
uip rpa execution cancel --output json
```

### 4. Exception Investigation

When execution hits an unhandled exception in a debug session, the command that was running returns `DebugState: "Suspended"` — the session is alive and waiting for your decision. `DebugDetails` carries the exception type, message, faulting activity, and a locals snapshot.

```bash
# Start debugging — if an exception fires, the response comes back Suspended
uip rpa debug start --file-path "MyWorkflow.xaml" --output json

# Inspect the Suspended response:
# - debugDetails → exception type + message + faulting activity + locals at the fault
# - hasErrors stays false — the outcome is not decided yet
# - errorMessage carries the guidance on which commands apply

# Then choose how to proceed:
# Option A: Retry the failed activity (e.g., transient network error)
uip rpa debug continue-retry --output json

# Option B: Ignore the exception and continue past it (pauses at the next activity)
uip rpa debug continue-ignore --output json

# Option C: Propagate the exception (the run fails; response is Completed with hasErrors: true)
uip rpa debug continue --output json

# Option D: Cancel and fix the root cause
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
# Start debugging with input arguments — one key=value pair per flag occurrence
uip rpa debug start --file-path "ProcessOrder.xaml" \
  --input-arguments orderId=ORD-12345 \
  --input-arguments customerEmail=test@example.com \
  --output json
```

`--input-arguments` is valid with `run`, `debug start`, `debug test-activity`, and `debug start-from-here`. For `run` / `debug start`, `=` keeps the value a string and `:=` passes raw JSON (`retries:=3`, `enabled:=true`). For `debug test-activity` / `debug start-from-here`, values must be VB/C# expressions — always `=`. Full grammar (file payloads, quoting rules): [cli-reference.md § Passing structured inputs](cli-reference.md#passing-structured-inputs).

---

## Profiling Workflow Performance

Use `--profiling` on a start verb to collect per-activity timings **and runtime screenshots** — the same data Studio's **Profile Execution** tool surfaces. Profiling serves two purposes that can be addressed in a single run: **verifying UI automation correctness** (via the captured screenshots — confirm clicks landed on the right element, forms filled as expected, screens transitioned correctly) **and verifying workflow performance** (via the per-activity timings). The executor writes `*.uistat` files plus screenshots into `%LOCALAPPDATA%\UiPath\ProfiledRuns\HHmmss_yyyy-MM-dd_<entryPoint>_<projectName>\` and the response carries the absolute path on `runResult.Profiling.OutputDirectory`.

### When to enable profiling

| Situation | Why |
|-----------|-----|
| User reports a slow workflow ("X takes 5 min, was 30 s last week") | Profiling localizes the regression to specific activities instead of the whole workflow |
| Choosing between two implementations of the same logic | Compare cumulative time across the activities each version uses |
| A loop body looks expensive but the cost is not obvious | `*.uistat` reports execution count + min/max/avg per activity — flags hot iterations |
| Pre-production sanity check on a long-running automation | Catches an activity whose individual time looks fine but whose cumulative share is dominant |
| Verifying a UI automation ran correctly without re-running it interactively | Captured screenshots show what the workflow actually saw at each UI activity — confirms clicks landed, forms filled, screens transitioned |
| Diagnosing "the workflow succeeded but the wrong thing happened" | Cross-check screenshots against expected screens; cheaper than rerunning with a debugger attached |

Do **not** enable profiling by default. It is opt-in for performance investigations and UI correctness checks — a normal smoke test (`uip rpa run`) is faster and produces no `.uistat` files or screenshots to clean up.

### Where the flag is effective

Only start verbs collect profiling — `--profiling` is silently ignored on stepping/breakpoint verbs:

| Verb | `--profiling` effect |
|------|---------------------|
| `run` | Collects |
| `debug start` | Collects |
| `debug test-activity` | Collects (single-activity scope; useful for tuning one activity). Studio Desktop required (depends on `focus-activity`). |
| `debug start-from-here` | Collects (partial workflow from the focused activity onward). Studio Desktop required (depends on `focus-activity`). |
| `debug step-over` / `step-into` / `step-out` / `continue` / `break` / `resume` / `continue-retry` / `continue-ignore` / `restart-from-top` / `toggle-breakpoint` / `execution cancel` | No-op |

### Reading the result

```bash
uip rpa run --file-path "ProcessOrders.xaml" --profiling --output json
```

Parse `Data.runResult` then inspect:

```jsonc
{
  "output": "{\"orderCount\":42}",
  "hasErrors": false,
  "errorMessage": null,
  "profiling": {
    "outputDirectory": "C:\\Users\\<user>\\AppData\\Local\\UiPath\\ProfiledRuns\\142305_2026-05-12_Main.xaml_ProcessOrders"
  }
}
```

The directory contains `*.uistat` files — one per workflow file executed in the run (top-level entry point plus every invoked workflow) — alongside runtime screenshots captured at UI activity boundaries. Each `*.uistat` row reports an activity with execution count, min / max / average / cumulative duration, and the cumulative percentage of total run time. Focus on:

1. **Activities with the largest cumulative percentage** — the dominant time sinks. Optimize these first.
2. **High execution count × moderate average duration** — typically loop bodies. Consider batching, caching, or hoisting work out of the loop.
3. **Wide min/max spread on a UI activity** — flaky selectors or variable target-element resolution; cross-check with the healing-agent log and the screenshot for that activity to confirm the element actually rendered.
4. **Screenshots for UI correctness** — open the screenshot folder to verify each UI interaction targeted the expected screen / element. Useful when the workflow reports `Success` but downstream data looks wrong.

### Caveats

- `Profiling` field is **absent** if the run did not reach the executor (compile failure surfaces in `ErrorMessage` instead) or if the active Studio profile does not support profiling (non-Develop profiles register a no-op profiling service). Treat the field as optional — never assume it is populated.
- Numbers from a `debug start` profile run differ from a `run` profile run — the debugger adds tracking overhead. For perf comparisons, always use `run`.
- Files are not auto-cleaned. After an investigation, manually clear `%LOCALAPPDATA%\UiPath\ProfiledRuns\` if disk usage matters.
- Profiling is per run, not aggregated across runs. To compare two implementations, run each with `--profiling` separately and diff the `*.uistat` reports.
- Studio's profiling tool window does **not** auto-focus on agent-triggered runs (intentional — profiling panel and Autopilot pane share a dock slot). Direct the user to `Profiling.OutputDirectory` on disk; do not tell them "open the profiling panel".

> **Activity-targeted profiling needs Studio Desktop.** `debug test-activity` and `debug start-from-here` collect profiling fine, but they depend on `focus-activity` — which only runs against Studio Desktop. `run` and `debug start` profile on both Studio Desktop and headless (Helm). See [Studio Desktop vs headless](#studio-desktop-vs-headless).

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
- **Prefer `--breakpoints` on `debug start`** — it targets specific activities by their XAML `IdRef` with no focusing step and runs headless. Use `focus-activity` + `debug toggle-breakpoint` only for interactive sessions on Studio Desktop.
- **Never let a debug response go unread** — every command returns `DebugState`; branch on it (`Paused` → inspect and step, `Suspended` → decide on the exception, `Running` → poll `debug state` or `break`, `Completed` → read the run result).
- **Use `debug test-activity` for quick feedback** — it runs a single activity in isolation, which is faster than debugging the entire workflow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` so the activity has the data it needs.
- **Use `debug start-from-here` to skip setup** — when the bug is deep in the workflow, skip straight to the relevant activity instead of stepping through the entire flow. Studio Desktop required (depends on `focus-activity`). Pre-set variables with `--input-variables` to simulate the state the activity would have received from preceding activities.
- **Prefer `debug step-over` for quick inspection** — it moves one activity at a time without descending into scopes. Use `debug step-into` only when you need to examine what happens inside a loop iteration or nested sequence.
- **Check variables after each step** — every `Paused`/`Suspended` response carries a locals snapshot (in-scope variables, arguments, current activity properties) in `DebugDetails`; streamed log entries remain useful for values the workflow logged along the way.
- **Use `debug continue-retry` for transient errors** — if the exception is a network timeout or rate limit, retrying may succeed without any code changes.
- **Use `debug continue-ignore` cautiously** — it skips the exception, which may leave variables in an unexpected state for downstream activities.
- **Cancel the session when done** — always issue `execution cancel` to cleanly end the run or debug session.
- **Use `--log-level Verbose`** when you need maximum detail about what the workflow is doing between steps.
- **Remember expression syntax for variables** — when using `debug test-activity` or `debug start-from-here`, string values need VB/C# string literal quotes inside the JSON value (e.g., `"\"hello\""` not `"hello"`).
- **Reach for `--profiling` when investigating performance or verifying UI automation correctness** — pair it with `run` for production-like numbers (the debugger adds overhead). Read the response's `Profiling.OutputDirectory`: open the `*.uistat` files starting with activities holding the largest cumulative percentage, and inspect the captured screenshots to confirm each UI interaction landed on the expected screen / element. See [Profiling Workflow Performance](#profiling-workflow-performance).
