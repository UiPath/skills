# Debug a Low-Code Agent

Run a low-code agent end-to-end on Studio Web and stream the result — without publishing it to Orchestrator. Use this to test an agent against real inputs during iteration. `uip agent debug` **uploads the agent's enclosing solution** to Studio Web, starts it on the serverless debug runtime, polls to completion, and returns the agent's output.

## Pre-flight

1. **Logged in.** `uip login status --output json` returns success.
2. **Solution resources refreshed — only if the agent has solution-level bindings.** If it uses external process/IS tools, index contexts, memory spaces, or escalations, refresh first so those declarations stay in sync with its bindings. Agents with only built-in tools (or no resources) don't need this (see [critical-rules.md](critical-rules.md) Rule 21):

   ```bash
   uip solution resources refresh --solution-folder <SOLUTION_DIR> --output json
   ```

## Consent gate

`uip agent debug` **executes the agent for real** — it calls its tools, escalations, and external APIs, and consumes model tokens. It also overwrites the agent's Studio Web solution. Per [critical-rules.md](critical-rules.md) Rule 8 (consent before upload/publish/deploy — debug uploads), confirm with the user before running it.

## Debug — controlled end-to-end run

```bash
uip agent debug <AGENT_PROJECT_DIR> --inputs '<json>' --output json
```

The argument is the agent **project directory** (the folder with `agent.json` / `project.uiproj`), inside its solution. The command uploads the enclosing solution and runs it — there is **no separate `uip solution upload` step**.

- `--inputs '<json>'` — the agent's input object, matching its `inputSchema` (e.g. `'{"input":"What is 2+2?"}'`). Omit for empty input.
- `--timeout <seconds>` / `--poll-interval <ms>` — wait budget and polling cadence; the command polls until a terminal state.

State changes (`Pending → Running → Successful`) stream to stderr while it waits.

Every debug run re-uploads the local solution, so the debugged copy always reflects your local edits — there is no "debug the cloud version" mode (if you don't have it locally, `uip solution download` first).

## Report the result

On success the envelope is `Code: "AgentDebug"` with `Data`:

| Field | Meaning |
|---|---|
| `State` | terminal job state (`Successful`) |
| `Output` | the agent's output object |
| `TraceId` | execution trace id — use to inspect the run |
| `JobKey` | the debug job key |

Show the user the `Output` and the `TraceId`.

A run that ends `Faulted` / `Stopped` returns `Result: "Failure"` (exit 1). The terminal state alone often lacks a reason — inspect the trace:

```bash
uip traces spans get <TraceId> --output json
```

## Anti-patterns

- **Never use `uip agent debug` as a validation step.** Use `uip agent validate` for correctness; debug is for end-to-end execution.
- **Don't skip `uip solution resources refresh` before debug when the agent has solution-level bindings** (external tools, IS, indexes, memory spaces, escalations). Stale declarations cause runtime binding failures even when `agent.json` is correct. Agents with only built-in tools don't need it.
