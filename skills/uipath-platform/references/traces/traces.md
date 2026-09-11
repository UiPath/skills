# Traces (`uip traces`)

> Retrieve LLM execution traces (spans) for agentic automation jobs.

## When to use this

- Debug an Agent-type process that uses LLM calls.
- Inspect tool calls, LLM interactions, and agent decisions.
- Get observability data beyond `uip or jobs logs`.

## Retrieval levels

| Command | Tool | Returns |
|---------|------|---------|
| `uip or jobs traces <job-key>` | orchestrator-tool | Trace IDs attached to a job |
| `uip traces spans get` | traces-tool | Detailed span data for a trace or job |

Run `uip or jobs traces <job-key>` to discover trace IDs, then run `uip traces spans get` for the full span tree. Alternatively, run `uip traces spans get --job-key <job-key> --output json` directly.

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

- [Run Jobs](../orchestrator/run-jobs.md) — `uip or jobs traces` for trace discovery
- [Trace Feedback](feedback.md) — annotate spans with sentiment; includes span selection guidance for nested jobs
- `uip traces spans get --help` for full option details