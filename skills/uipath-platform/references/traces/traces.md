# Traces (`uip traces`)

> Retrieve LLM execution traces (spans) for agentic automation jobs.

## When to use this

- Debugging an Agent-type process that uses LLM calls
- Inspecting tool calls, LLM interactions, and agent decisions during execution
- Getting detailed observability data beyond what `uip or jobs logs` provides

## Two tools, two levels of detail

| Command | Tool | What it returns |
|---------|------|-----------------|
| `uip or jobs traces <job-key>` | orchestrator-tool | Lists trace IDs attached to a job |
| `uip traces spans get` | traces-tool | Fetches detailed span data for a trace or job |

**Typical flow:** Use `uip or jobs traces` to discover trace IDs, then `uip traces spans get` for the full span tree.

Or skip straight to spans by job key:

```bash
uip traces spans get --job-key <job-key> --output json
```

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
| `-t, --tenant <name>` | Tenant override |

## Related

- [Run Jobs](orchestrator/run-jobs.md) — `uip or jobs traces` for trace discovery
- `uip traces spans get --help` for full option details
