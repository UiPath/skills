# Debugging Workflows with `uip rpa run-file`

The `uip rpa run-file` command provides full interactive debugging capabilities for both XAML workflows and coded (.cs) files. Beyond simple execution (`StartExecution`), it supports breakpoints, step-by-step execution, exception handling, isolated activity testing, and runtime state inspection — all from the CLI.

This is a powerful complement to `get-errors` (static validation). While `get-errors` catches structural and type issues at design time, the debugger catches runtime problems: wrong API responses, null references, logic errors, failed deserialization, and more. Use both together for comprehensive workflow validation.

---

## Command Reference

All commands share these base parameters:

```bash
uip rpa run-file --file-path <relative-path> --command <Command> [--input-arguments '<json>'] [--input-variables '<json>'] [--log-level <level>] [--format json]
```

| Parameter | Description |
|-----------|-------------|
| `--file-path` | File path of the workflow to run (relative to project root) |
| `--command` | The debug command to execute (see table below). Defaults to `StartExecution` |
| `--input-arguments` | JSON object with project-level input arguments. Only for `StartExecution`, `StartDebugging`, `TestActivity`, and `StartDebuggingFromHere` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--input-variables` | JSON object with workflow-level variable values. Only for `TestActivity` and `StartDebuggingFromHere` (see [Input Variables vs Input Arguments](#input-variables-vs-input-arguments)) |
| `--log-level` | Minimum log level: `Verbose`, `Trace`, `Information` (default), `Warning`, `Error`, `Critical` |
| `--output` | Output format: `json` (recommended), `table`, `yaml`, `plain` |

### Debug Commands

| Command | When to Use | What It Does |
|---------|-------------|--------------|
| `StartExecution` | Run without debugging | Executes the workflow to completion. Default if `--command` is omitted |
| `StartDebugging` | Begin a debug session | Starts execution in debug mode. Pauses at the first breakpoint (or at the first activity if a breakpoint is set on the workflow itself). Returns current execution state |
| `TestActivity` | Test one activity in isolation | Isolates the currently focused activity and executes it in a temporary test workflow. **Requires `focus-activity` first.** Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `StartDebuggingFromHere` | Debug from a specific activity | Starts a debugging session from the currently focused activity, skipping all preceding activities. **Requires `focus-activity` first.** Use `--input-variables` to set variable values and `--input-arguments` to set argument values |
| `ToggleBreakpoint` | Set/remove breakpoints | Toggles a breakpoint on the currently focused activity (XAML) or line (.cs). Use `uip rpa focus-activity` to focus beforehand. For XAML, cycles through 3 states: **enabled → disabled → no breakpoint**. For .cs, cycles through 2 states: **breakpoint → no breakpoint**. If no activity/line is focused, toggles on the entire workflow |
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

Debug commands return a JSON response with this structure:

```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "Output": [ ... ],
    "Errors": [ ... ],
    "LogEntries": [ ... ]
  }
}
```

### Output Array

When the debugger pauses (at a breakpoint, after a step, or on an exception), `Output` contains an array of state inspection objects. Each object has:

| Field | Description |
|-------|-------------|
| `Category` | The source process that emitted this entry (see categories below) |
| `Type` | The .NET type (e.g., `String`, `DataTable`, `String[]`, `HttpResponseSummary`) |
| `Name` | Property or variable name |
| `Value` | Current value — can be a simple string, null, or complex JSON |

#### Categories

The `Category` field indicates which process produced the output entry:

| Category | Meaning |
|----------|---------|
| `General` | General-purpose output from the workflow runtime |
| `Debug` | Output from the debug engine (step events, breakpoint hits, exception notifications) |
| `Compile` | Output from the compilation/build process |
| `Tests` | Output from test execution |

### Errors Array

Validation warnings or errors encountered during execution:

```json
{
  "ErrorCode": "WARNING",
  "ErrorMessage": "UiPath recommends using \"Use Excel File\" inside an \"Excel Process Scope\"",
  "LineNumber": ""
}
```

### LogEntries Array

Log messages emitted during execution:

```json
{
  "Source": "Debug",
  "Level": "Information",
  "Message": "Fetching price for: AAPL"
}
```

Log entries accumulate between debug steps — each step returns only the new log entries since the last command. Use `--log-level` to control verbosity.

### Non-Debug Commands

For `StartExecution` (non-debug run), `TestActivity` (when no breakpoints are hit), `Stop`, and `ForceSessionEnded`, `Output` is a simple string indicating the session state. LogEntries still contain any log messages produced during execution:

```json
{
  "Output": "Session ended",
  "Errors": [],
  "LogEntries": [
    { "Source": "Debug", "Level": "Information", "Message": "Workflow execution started" },
    { "Source": "Debug", "Level": "Information", "Message": "Current temperature: 9.6°C" },
    { "Source": "Debug", "Level": "Information", "Message": "Workflow execution ended in: 00:00:01" }
  ]
}
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

```bash
# 1. Focus the activity you want to break at (optional — skip if you want to break at the workflow level)
uip rpa focus-activity --activity-id "Assign_1"

# 2. Toggle a breakpoint on the focused activity
uip rpa run-file --file-path "GetStockPrices.xaml" --command ToggleBreakpoint --format json

# 3. Start debugging — execution pauses at the breakpoint
uip rpa run-file --file-path "GetStockPrices.xaml" --command StartDebugging --format json

# 4. Inspect the Output entries (variable values, activity properties, execution state)
# Then step through or continue:
uip rpa run-file --file-path "GetStockPrices.xaml" --command StepOver --format json

# 5. When done, stop the session
uip rpa run-file --file-path "GetStockPrices.xaml" --command Stop --format json
```

### 2. Test a Single Activity in Isolation

Use `TestActivity` to run just the currently focused activity without executing the entire workflow. Useful for verifying an activity works with specific inputs.

```bash
# 1. Focus the activity to test
uip rpa focus-activity --activity-id "DeserializeJson_1"

# 2. Run it in isolation, pre-setting any variables it reads from
uip rpa run-file --file-path "GetBucharestTemperature.xaml" \
  --command TestActivity \
  --input-variables '{"temperature": "\"200\""}' \
  --format json

# 3. Check the output:
#    - errors array → validation/compilation issues (e.g., wrong expression syntax)
#    - logEntries → runtime log messages from the activity
#    - Output → "Session ended" on success, or local variables if paused
```

### 3. Debug From a Specific Activity

Use `StartDebuggingFromHere` to skip straight to the activity you care about, avoiding stepping through earlier activities.

```bash
# 1. Focus the activity to start from
uip rpa focus-activity --activity-id "HttpRequest_1"

# 2. Start debugging from that point, pre-setting variables
uip rpa run-file --file-path "GetBucharestTemperature.xaml" \
  --command StartDebuggingFromHere \
  --input-variables '{"apiUrl": "\"https://api.example.com/weather\""}' \
  --format json

# 3. The debugger runs from the focused activity — step through or continue
uip rpa run-file --file-path "GetBucharestTemperature.xaml" --command StepOver --format json

# 4. Stop when done
uip rpa run-file --file-path "GetBucharestTemperature.xaml" --command Stop --format json
```

### 4. Exception Investigation

When `Continue` or a step command hits an exception, the debugger pauses and returns the exception details. You can inspect the state, then decide how to proceed.

```bash
# Start debugging and continue to let it run
uip rpa run-file --file-path "MyWorkflow.xaml" --command StartDebugging --format json
uip rpa run-file --file-path "MyWorkflow.xaml" --command Continue --format json

# If an exception occurs, the debugger pauses. Inspect the Output entries:
# - Look for entries with error/exception details in the Name and Value fields
# - Check LogEntries for error-level messages with stack traces
# - Examine variable values at the point of failure

# Then choose how to proceed:
# Option A: Retry the failed activity (e.g., transient network error)
uip rpa run-file --file-path "MyWorkflow.xaml" --command ContinueRetry --format json

# Option B: Ignore the exception and continue past it
uip rpa run-file --file-path "MyWorkflow.xaml" --command ContinueIgnore --format json

# Option C: Stop and fix the root cause
uip rpa run-file --file-path "MyWorkflow.xaml" --command Stop --format json
```

### 5. Runtime Validation After Edits

Use debugging to verify that a fix actually works at runtime, beyond what `get-errors` (static validation) can check.

```bash
# 1. Run static validation first
uip rpa get-errors --file-path "MyWorkflow.xaml" --format json

# 2. If 0 static errors, start a debug session to validate runtime behavior
uip rpa run-file --file-path "MyWorkflow.xaml" --command StartDebugging --format json

# 3. Continue past the fixed area and inspect variable state
uip rpa run-file --file-path "MyWorkflow.xaml" --command Continue --format json

# 4. Check the response for:
#    - Output entries show expected variable values
#    - No error-level LogEntries
#    - Errors array is empty or contains only warnings

# 5. Stop
uip rpa run-file --file-path "MyWorkflow.xaml" --command Stop --format json
```

### 6. Debugging with Input Arguments

Pass input arguments when the workflow has In arguments that need values:

```bash
# Start debugging with input arguments (plain JSON values)
uip rpa run-file --file-path "ProcessOrder.xaml" \
  --command StartDebugging \
  --input-arguments '{"orderId": "ORD-12345", "customerEmail": "test@example.com"}' \
  --format json
```

`--input-arguments` is valid with `StartExecution`, `StartDebugging`, `TestActivity`, and `StartDebuggingFromHere`. For `StartExecution`/`StartDebugging`, values are plain JSON. For `TestActivity`/`StartDebuggingFromHere`, values must be VB/C# expressions.

---

## Reading Debug Output Effectively

When a debug step returns, focus on these elements in order:

1. **Errors array** — Check for any `ERROR`-level entries that indicate compilation or validation failures
2. **LogEntries array** — Look for error-level log messages that reveal runtime failures, exception messages, and stack traces. The `Source` field tells you the origin (`Debug`, `General`, etc.) and `Level` indicates severity
3. **Output array** — Inspect the `Name` and `Value` fields of each entry to understand the current state: variable values, activity properties, and execution context. The `Category` field (`General`, `Debug`, `Compile`, `Tests`) tells you which process emitted the entry

### Identifying the Root Cause from Debug Output

A practical example — a workflow makes an HTTP request and tries to deserialize the response as JSON, but fails:

- **LogEntries** contain an error-level message with `JsonReaderException: Unexpected character encountered while parsing value: T` — the deserializer tried to parse a non-JSON response
- **Output entries** show the HTTP response variable has `StatusCode: "TooManyRequests"` and `TextContent: "Too Many Requests\r\n"` — the API returned a 429, not JSON
- **Fix**: Add status code checking before deserialization, or add retry logic with backoff to the HTTP request

---

## Best Practices

- **Always use `--format json`** for debug commands when you need to parse the output programmatically. The structured output makes it easy to inspect variables and identify exceptions.
- **Set breakpoints strategically** — place them just before the activity you suspect is failing, not at the very start. This avoids stepping through dozens of unrelated activities.
- **Use `focus-activity` before `ToggleBreakpoint`** to target a specific activity by its IdRef. Without focusing first, the breakpoint is set on whatever activity or workflow is currently focused in Studio.
- **Use `TestActivity` for quick feedback** — it runs a single activity in isolation, which is faster than debugging the entire workflow. Pre-set variables with `--input-variables` so the activity has the data it needs.
- **Use `StartDebuggingFromHere` to skip setup** — when the bug is deep in the workflow, skip straight to the relevant activity instead of stepping through the entire flow. Pre-set variables with `--input-variables` to simulate the state the activity would have received from preceding activities.
- **Prefer `StepOver` for quick inspection** — it moves one activity at a time without descending into scopes. Use `StepInto` only when you need to examine what happens inside a loop iteration or nested sequence.
- **Check variables after each step** — inspect the Output entries after each step to see the current state of in-scope variables. This is the most direct way to verify that each activity produced the expected result.
- **Use `ContinueRetry` for transient errors** — if the exception is a network timeout or rate limit, retrying may succeed without any code changes.
- **Use `ContinueIgnore` cautiously** — it skips the exception, which may leave variables in an unexpected state for downstream activities.
- **Stop the session when done** — always issue a `Stop` command to cleanly end the debug session. If `Stop` doesn't respond, use `ForceSessionEnded` as a fallback.
- **Use `--log-level Verbose`** when you need maximum detail about what the workflow is doing between steps.
- **Remember expression syntax for variables** — when using `TestActivity` or `StartDebuggingFromHere`, string values need VB/C# string literal quotes inside the JSON value (e.g., `"\"hello\""` not `"hello"`).