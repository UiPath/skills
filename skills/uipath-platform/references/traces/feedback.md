# Trace Feedback (`uip traces feedback`)

Annotate traces or spans with sentiment and comments for LLM observability.
Use for agent output quality review and building evaluation datasets.

## Commands

| Command | Purpose |
|---------|---------|
| `create` | Add feedback to a trace (or specific span) |
| `get <id>` | Fetch one feedback record |
| `list` | List feedback with filters |
| `list detailed` | Cross-trace feedback with span context (max 200 items) |
| `update <id>` | Change sentiment, comment, or categories |
| `delete <id>` | Remove feedback |

## create

```bash
uip traces feedback create \
  --trace-id <TRACE_ID> \
  --positive \
  --comment "Correct summary" \
  --category "Output" \
  --folder-key <folder-key> \
  --output json
```

| Flag | Required | Notes |
|------|----------|-------|
| `--trace-id` | Yes | 32-char hex or GUID |
| `--positive` / `--negative` | One required | Mutually exclusive |
| `--folder-key` | Yes | |
| `--span-id` | No | Defaults to root span of trace |
| `--comment` | No | Max 4000 chars; mutually exclusive with `--comment-file` |
| `--comment-file` | No | Path to file; use `-` to read from stdin |
| `--category` | No | Repeatable. Built-in values: `"Output"`, `"Agent Error"`, `"Agent Plan Execution"` |
| `--agent-id` | No | Agent reference GUID |
| `--agent-version` | No | Max 100 chars |
| `--tenant` | No | Defaults to authenticated tenant |

## get

`--folder-key` is optional. Positional `<id>` required.

```bash
uip traces feedback get <feedback-id> --output json
```

## list

```bash
uip traces feedback list \
  --trace-id <trace-id> \
  --folder-key <folder-key> \
  --output json
```

| Flag | Notes |
|------|-------|
| `--trace-id` | Filter by trace |
| `--span-id` | Filter by span |
| `--agent-id` / `--agent-version` | Filter by agent |
| `--positive` / `--negative` | Filter by sentiment |
| `--limit` | Default 20, max 100 |
| `--offset` | Pagination offset, default 0 |
| `--folder-key` | Optional |

## list detailed

Returns `spanAttributes` per record (`agentId`, `agentName`, `userPrompt`, `output`). No `--trace-id` needed — designed for cross-trace bulk review.

```bash
# Last 24 hours
uip traces feedback list detailed \
  --since 24h \
  --folder-key <folder-key> \
  --output json

# Explicit date range
uip traces feedback list detailed \
  --after 2026-05-01T00:00:00Z \
  --before 2026-05-07T00:00:00Z \
  --positive \
  --folder-key <folder-key> \
  --output json
```

Additional flags over `list`: `--since <duration>`, `--after <ISO>`, `--before <ISO>`, `--category-id <guid>`, `--sortBy`, `--sortDir`. Max 200 items.

## update

`--category` tags are **replacement**, not additive — passing `--category` replaces all existing tags.

```bash
uip traces feedback update <feedback-id> \
  --negative \
  --comment "Wrong output" \
  --folder-key <folder-key> \
  --output json
```

## delete

```bash
uip traces feedback delete <feedback-id> \
  --folder-key <folder-key> \
  --yes \
  --output json
```

## Choosing a span

Omitting `--span-id` resolves to the root span of the trace. When an agent runs inside any orchestrating layer (RPA robot job, Maestro case, parent agent, etc.) the root is the **orchestrator's** span — feedback lands on the wrong span and won't surface in the agent review grid.

**Always pass `--span-id` when the agent runs inside any orchestrating layer.**

**Always target the `agentRun` span.**

### Find the agentRun span ID

```bash
SPAN_ID=$(uip traces spans get --job-key <JOB_KEY> --output json \
  | jq -r '.Data[] | select(try (.Attributes | fromjson | .type == "agentRun") catch false) | .Id')
uip traces feedback create \
  --trace-id <TRACE_ID> \
  --span-id "$SPAN_ID" \
  --positive \
  --folder-key <FOLDER_KEY> \
  --output json
```

> **Directly-invoked agents only.** When the agent is the top-level span (no parent orchestrator), the root span is the agent execution — omitting `--span-id` is safe.

## Mutual exclusion rules

1. `--positive` / `--negative` — mutually exclusive on all commands
2. `--comment` / `--comment-file` — mutually exclusive on `create` and `update`
3. `--trace-id` — required on `create`; optional filter on `list` / `list detailed`
4. `--folder-key` — required on `create`, `update`, `delete`; optional on `get` / `list`

## Related

- [Traces — Spans](traces.md) — `uip traces spans get` for span-level observability
- [Run Jobs](../orchestrator/run-jobs.md) — `uip or jobs traces` for trace discovery
