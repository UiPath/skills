# Task Execution Trace and Feedback

Covers the two Agent/Maestro-only capabilities ported from Action Center's legacy
in-app Autopilot tools (`GetExecutionTraceContext`, `SubmitTraceFeedback`). Both
require an explicit task ID from the user or from `tasks list`/`tasks get`. The
legacy tools read an ambient "currently open task" from the browser; a CLI agent
has no such context and must be given or resolve the task first.

**Scope:** `Agent` and `Maestro` sourced tasks only (`TaskSource.SourceName`).
Other task sources (`Workflow`, `CaseManagement`, `Other`) have no execution
trace. Tell the user trace summarization does not apply rather than attempting
a lookup.

## Step 1: resolve the task's trace identifiers

```bash
uip tasks get <task-id> --task-type ExternalTask --folder-id <folder-id> --output json
```

Read `Data.TaskSource`:

| Field | Meaning |
|---|---|
| `TaskSource.SourceName` | `Agent`, `Maestro`, `Workflow`, `CaseManagement`, or `Other` |
| `TaskSource.SourceId` | The job key for `uip traces` lookups |
| `TaskSource.TaskSourceMetadata.InstanceId` | Trace ID for an **Agent** task |
| `TaskSource.TaskSourceMetadata.TraceId` | Trace ID for a **Maestro** task |

If `TaskSource` is `null`, or `SourceName` is not `Agent`/`Maestro`, stop: there
is no execution trace to fetch.

## Step 2: fetch the trace (`GetExecutionTraceContext` equivalent)

```bash
uip traces spans get <trace-id> --output json
# or, when only the job key is known (Maestro/RPA sources):
uip traces spans get --job-key <source-id> --output json
```

`trace-id` is a positional argument, not a flag. Summarize the returned spans
for the user: what ran, in what order, and the result of each step. If the
command returns no spans, say the trace may have expired rather than
reporting a generic failure.

## Step 3: submit feedback on a trace or span (`SubmitTraceFeedback` equivalent)

```bash
uip traces feedback create \
  --trace-id <trace-id> \
  --folder-key <folder-key> \
  --positive \
  --comment "<comment>" \
  --output json
```

`--folder-key` is required for this write operation. Feedback is positive or
negative (`--positive` / `--negative`), set as separate flags rather than a
single boolean field. `--span-id` is optional and defaults to the trace's root
span. The legacy tool's `isOutput` / `isAgentError` / `isAgentPlanExecution`
flags map to `--category` (repeatable; built-in tags are `Output`, `Agent
Error`, `Agent Plan Execution`): pass `--category "Agent Error"` for that
flag. Use `--agent-id`/`--agent-version` when the task's `TaskSource.SourceId`
and version are known. Check `uip traces feedback list --trace-id <trace-id>`
for existing feedback before creating a duplicate, and `uip traces feedback
update` to revise it instead of creating a new entry.

## OKF evidence synthesis

The legacy `GetOkfEvidence` tool had two halves. Neither is a skill capability
here:

1. It searched Observability Knowledge Fabric notes for the current task
   (`POST {baseUrl}/{account}/{tenant}/llmopstenant_/api/Okf/search`). The
   `uip` CLI has no command against this endpoint today; this half needs new
   CLI work before it can become a skill capability.
2. It published the synthesized decision and reasons into the Action Center
   decision-capture widget rendered in the user's open browser tab
   (`publishDecisionAnalysis`). That writes directly into live, open-tab UI
   state with no corresponding API, so it stays a registered Action Center
   tool.
