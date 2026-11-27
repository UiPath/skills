# Debug a Low-Code Agent

Run a low-code autonomous agent end-to-end on Studio Web and stream the result — without publishing it to Orchestrator. Use this to test an agent against real inputs during iteration. `uip agent debug` **uploads the agent's enclosing solution** to Studio Web, starts it on the serverless debug runtime, polls to completion, and returns the agent's output.

> The debug command is currently not supported for conversational agents, so only attempt to debug autonomous agents.

## Pre-flight

1. **Logged in.** `uip login status --output json` returns success.
2. **Solution resources refreshed — only if the agent has solution-level bindings.** If it uses external process/IS tools, index contexts, memory spaces, or escalations, refresh first so those declarations stay in sync with its bindings. Agents with only built-in tools (or no resources) don't need this (see [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 20):

   ```bash
   uip solution resources refresh --solution-folder <SOLUTION_DIR> --output json
   ```

## Consent gate

`uip agent debug` **executes the agent for real** — it calls its tools, escalations, and external APIs, and consumes model tokens. It also overwrites the agent's Studio Web solution. Per [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 8 (consent before upload/publish/deploy — debug uploads), confirm with the user before running it.

## Debug — controlled end-to-end run

```bash
uip agent debug <AGENT_PROJECT_DIR> --inputs '<json>' [--attachment <FIELD>=<FILE_PATH>] --output json
```

The argument is the agent **project directory** (the folder with `agent.json` / `project.uiproj`), inside its solution. The command uploads the enclosing solution and runs it — there is **no separate `uip solution upload` step**.

- `--inputs '<json>'` — the agent's input object, matching its `inputSchema` (e.g. `'{"input":"What is 2+2?"}'`). Omit for empty input.
- `--attachment <FIELD>=<FILE_PATH>` — upload a local file into a `job-attachment` input field (repeatable). See § Attachments.
- `--timeout <seconds>` / `--poll-interval <ms>` — wait budget and polling cadence; the command polls until a terminal state.

State changes (`Pending → Running → Successful`) stream to stderr while it waits.

Every debug run re-uploads the local solution, so the debugged copy always reflects your local edits — there is no "debug the cloud version" mode (if you don't have it locally, `uip solution download` first).

## Attachments

Bind a local file to a `job-attachment` input with `--attachment <FIELD>=<FILE_PATH>`. The CLI uploads the file to Orchestrator and binds the full reference `{ ID, FullName, MimeType, Metadata }` into the job input under `<FIELD>` — never build that object by hand.

```bash
uip agent debug <AGENT_PROJECT_DIR> --attachment fileIn=<FILE_PATH> --inputs '{"question":"..."}' --output json
```

1. `<FIELD>` must be declared in `agent.json` → `inputSchema` as a job-attachment (`$ref: "#/definitions/job-attachment"`, or a schema carrying `x-uipath-resource-kind: "JobAttachment"`) — see [agent-definition.md](agent-definition.md) § File Attachments. Repeat the flag for an array of job-attachments. A field of any other type fails with `ErrorCode: invalid_argument`.
2. Local checks run first, with zero network calls. A spec without `=`, an undeclared or non-attachment field, or a missing file exits 1 (`ErrorCode: invalid_argument` or `not_found`) with `Instructions` ending "Nothing was uploaded." Fix the flag and re-run; nothing needs cleanup.
3. The upload runs after the Studio Web solution import and before the job starts. A refused upload (for example 403 → `ErrorCode: permission_denied`) fails the command before any debug job is started.
4. `MimeType` is inferred from the file extension (`.pdf` → `application/pdf`). An unknown or missing extension falls back to `application/octet-stream`, which the model provider behind `analyze-attachments` rejects — keep the real extension on the file.
5. To reuse an attachment the CLI already uploaded, pass its reference in `--inputs` instead of re-uploading: `--inputs '{"<FIELD>":{"ID":"<ATTACHMENT_ID>"}}'`. Take the ID from `Data.Attachments` of the earlier run.

## Report the result

On success the envelope is `Code: "AgentDebug"` with `Data`:

| Field | Meaning |
|---|---|
| `State` | terminal job state (`Successful`) |
| `Output` | the agent's output object |
| `TraceId` | execution trace id — use to inspect the run |
| `JobKey` | the debug job key |
| `Attachments` | one row per `--attachment`: `Field`, `AttachmentId`, `FileName`, `MimeType`, `Size` — also present on a `Faulted` run |

Show the user the `Output` and the `TraceId`. When `--attachment` was used, also show `Attachments` so the IDs can be reused.

A run that ends `Faulted` / `Stopped` returns `Result: "Failure"` (exit 1). The terminal state alone often lacks a reason — inspect the trace:

```bash
uip traces spans get <TraceId> --output json
```

## Anti-patterns

- **Never use `uip agent debug` as a validation step.** Use `uip agent validate` for correctness; debug is for end-to-end execution.
- **Don't skip `uip solution resources refresh` before debug when the agent has solution-level bindings** (external tools, IS, indexes, memory spaces, escalations). Stale declarations cause runtime binding failures even when `agent.json` is correct. Agents with only built-in tools don't need it.
- **Never attempt `uip agent debug` for low-code conversational agents.** The debug command for conversational agents is not yet supported.
