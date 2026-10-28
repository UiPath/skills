# Traces (`uip traces`)

> Retrieve LLM execution traces (spans) for agentic automation jobs.

## When to use this

- Debugging an Agent-type process that uses LLM calls
- Inspecting tool calls, LLM interactions, and agent decisions during execution
- Getting detailed observability data beyond what `uip or jobs logs` provides

## One command, keyed by job or by trace

```bash
uip traces spans get --job-key <job-key> --output json
```

There is no separate discovery step: `--job-key` resolves the trace itself, so start here when all you have is a job. Pass a trace id positionally when you already have one.

> `uip or jobs traces <job-key>` used to list a job's trace ids. It is removed — the command still parses but only prints a pointer here and exits non-zero. Replace it in any script that still calls it.

## Command: `uip traces spans get`

```bash
# By trace ID (32-char hex or GUID)
uip traces spans get <trace-id> --output json

# By job key (alternative — no trace ID needed)
uip traces spans get --job-key <job-key> --output json
```

**Options:**

| Option | Description |
|--------|-------------|
| `[trace-id]` | Trace ID (32-char hex or GUID format) — optional if `--job-key` provided |
| `--job-key <guid>` | Orchestrator job key — alternative to trace-id |
| `--folder-path <path>` | Folder path for context |
| `--folder-key <guid>` | Folder key for context |
| `--profile <name>` | Named login profile. Other tenant: `uip login tenant set <tenant>` first (`--tenant` is deprecated) |

## Related

- [Run Jobs](../orchestrator/run-jobs.md) — the job lifecycle these traces come from
- [Trace Feedback](feedback.md) — annotate spans with sentiment; includes span selection guidance for nested jobs
- `uip traces spans get --help` for full option details
