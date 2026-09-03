# Debug a Low-Code Agent

Run a low-code autonomous agent end-to-end on Studio Web and stream its result without publishing it to Orchestrator. `uip agent debug` uploads the agent's enclosing solution, starts it on the serverless debug runtime, polls to completion, and returns the agent's output. Debug is unsupported for conversational agents.

## Pre-flight

1. Confirm login by running:

   ```bash
   uip login status --output json
   ```

   It must return success.

2. If the agent has solution-level bindings—external process/IS tools, index contexts, memory spaces, or escalations—run:

   ```bash
   uip solution resources refresh --solution-folder <SOLUTION_DIR> --output json
   ```

   Agents using only built-in tools, or no resources, do not need this (see [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 20).

## Consent gate

Before running debug, obtain user confirmation. `uip agent debug` executes the agent for real, calling tools, escalations, and external APIs and consuming model tokens; it also overwrites the agent's Studio Web solution. Because debug uploads, follow [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 8 (consent before upload/publish/deploy — debug uploads).

## Debug — controlled end-to-end run

Run:

```bash
uip agent debug <AGENT_PROJECT_DIR> --inputs '<json>' --output json
```

`<AGENT_PROJECT_DIR>` is the agent project directory containing `agent.json` / `project.uiproj`, inside its solution. This command uploads the enclosing solution and runs the agent; do not run a separate `uip solution upload` step.

- `--inputs '<json>'` supplies the input object matching `inputSchema`; omit it for empty input.
- `--timeout <seconds>` sets the wait budget.
- `--poll-interval <ms>` sets the polling cadence.

The command polls until a terminal state and streams state changes (`Pending → Running → Successful`) to stderr. Every run re-uploads the local solution, so the debugged copy reflects local edits. There is no mode for debugging the cloud version; run `uip solution download` first if the agent is not local.

## Report the result

On success, return the envelope with `Code: "AgentDebug"` and `Data` containing:

| Field | Meaning |
|---|---|
| `State` | terminal job state (`Successful`) |
| `Output` | the agent's output object |
| `TraceId` | execution trace id for inspecting the run |
| `JobKey` | debug job key |

Show the user `Output` and `TraceId`.

If the run ends `Faulted` / `Stopped`, it returns `Result: "Failure"` (exit 1). The terminal state often lacks the reason; inspect the trace by running:

```bash
uip traces spans get <TraceId> --output json
```

## Anti-patterns

- Never use `uip agent debug` for validation. Run `uip agent validate` for correctness; use debug for end-to-end execution.
- Do not skip `uip solution resources refresh` before debug when the agent has solution-level bindings (external tools, IS, indexes, memory spaces, or escalations). Stale declarations can cause runtime binding failures even when `agent.json` is correct. Agents using only built-in tools do not need it.
- Never run `uip agent debug` for low-code conversational agents; conversational-agent debug is not supported.
