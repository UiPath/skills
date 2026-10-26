# Traces (`uip traces`)

> Retrieve LLM execution traces (spans) for agentic automation jobs.

## When to use this

Use for debugging Agent-type processes using LLM calls, inspecting tool calls, LLM interactions, agent decisions, or observability beyond `uip or jobs logs`.

## One command, keyed by job or by trace

With only a job key, run:

```bash
uip traces spans get --job-key <job-key> --output json
```

`--job-key` resolves the trace; no discovery step is needed. With a trace ID, pass it positionally:

```bash
uip traces spans get <trace-id> --output json
```

`uip or jobs traces <job-key>` is removed: it still parses, prints only a pointer here, and exits non-zero. Replace it in scripts.

## Command: `uip traces spans get`

**Options:**

| Option | Description |
|--------|-------------|
| `[trace-id]` | Trace ID (32-char hex or GUID format); optional when `--job-key` is provided |
| `--job-key <guid>` | Orchestrator job key; alternative to trace-id |
| `--folder-path <path>` | Folder path for context |
| `--folder-key <guid>` | Folder key for context |
| `--profile <name>` | Named login profile. For another tenant, first run `uip login tenant set <tenant>` (`--tenant` is deprecated) |

Run `uip traces spans get --help` for full option details.

## Related

- [Run Jobs](../orchestrator/run-jobs.md) — the job lifecycle these traces come from
- [Trace Feedback](feedback.md) — annotate spans with sentiment; includes span selection guidance for nested jobs