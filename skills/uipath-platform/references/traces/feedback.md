# Trace Feedback (`uip traces feedback`)

Annotate traces or spans with sentiment and comments for LLM observability.
Use for agent output quality review and building evaluation datasets.

## Commands

| Command | Purpose |
|---------|---------|
| `create` | Add feedback to a trace (or specific span) |
| `get <id>` | Fetch one feedback record |
| `list` | List feedback with filters |
| `list detailed` | List feedback with span context, plus extra filters (max 200 items) |
| `update <id>` | Change sentiment, comment, metadata, or categories |
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
| `--comment` | No | Max 1048576 chars; mutually exclusive with `--comment-file` |
| `--comment-file` | No | Path to file; use `-` to read from stdin |
| `--category` | No | Repeatable. Built-in values: `"Output"`, `"Agent Error"`, `"Agent Plan Execution"` |
| `--agent-id` | No | Agent reference GUID |
| `--agent-version` | No | Max 100 chars |
| `--profile <name>` | No | Named login profile. Other tenant: `uip login tenant set <tenant>` first (`--tenant` is deprecated) |

## get

Positional `<id>` and `--folder-key` required.

```bash
uip traces feedback get <feedback-id> --folder-key <folder-key> --output json
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

`--trace-id` is optional — omit it to filter and paginate across all traces (e.g. by `--agent-id`/`--agent-version`/`--negative`) without needing `list detailed`.

## list detailed

Adds span context per record (`spanAttributes`: `agentId`, `agentName`, `userPrompt`, `output`) plus time-range/category/sort filters over `list`. Not required for cross-trace filtering — plain `list` already covers that by omitting `--trace-id`.

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

Additional flags over `list`: `--since <duration>`, `--after <ISO>`, `--before <ISO>`, `--category-id <guid>` (repeatable), `--sort-by <createdAt|updatedAt>` (default `createdAt`), `--sort-order <asc|desc>` (default `desc`). Max 200 items.

## update

Positional `<id>`, one of `--positive` / `--negative`, and `--folder-key` required.

```bash
uip traces feedback update <feedback-id> \
  --negative \
  --comment "Wrong output" \
  --folder-key <folder-key> \
  --output json
```

| Flag | Required | Notes |
|------|----------|-------|
| `--positive` / `--negative` | One required | Mutually exclusive |
| `--folder-key` | Yes | |
| `--comment` | No | Max 1048576 chars; mutually exclusive with `--comment-file` |
| `--comment-file` | No | Path to file; use `-` to read from stdin |
| `--metadata` | No | Must be valid JSON. Max 1048576 chars; mutually exclusive with `--metadata-file` |
| `--metadata-file` | No | Path to file; use `-` to read from stdin |
| `--category` | No | Repeatable. **Replacement**, not additive |
| `--profile <name>` | No | Named login profile |

### Omitted fields are preserved

The API replaces the whole record, so the CLI reads it before it writes and carries over every field the caller did not pass. Updating only `--metadata` keeps the existing comment and categories.

Read-modify-write is not atomic: a concurrent edit between the read and the write is lost. The API offers no ETag or PATCH.

### Clearing fields

| Field | Clear with |
|-------|-----------|
| Comment | `--comment ""` |
| Metadata | `--metadata ""` |
| Categories | Not possible — `--category ""` stores a tag literally named `""` |

### Metadata must be valid JSON

Any JSON value is accepted — object, array, string, number. Non-JSON text is rejected server-side with `INVALID_FEEDBACK_METADATA`. The CLI does not pre-validate; the value passes through verbatim. Length is checked before JSON validity.

```bash
uip traces feedback update <feedback-id> \
  --positive \
  --metadata '{"reviewer":"qa","round":2}' \
  --folder-key <folder-key> \
  --output json

# From a file (large or nested payloads)
uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file review.json \
  --folder-key <folder-key> \
  --output json

# From stdin
jq -n '{reviewer:"qa"}' | uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file - \
  --folder-key <folder-key> \
  --output json
```

`create` has no `--metadata` — set metadata with `update` after creating.

## delete

`-y` is required — the CLI never prompts, so a delete without it is rejected.

```bash
uip traces feedback delete <feedback-id> \
  --folder-key <folder-key> \
  -y \
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
3. `--metadata` / `--metadata-file` — mutually exclusive on `update`
4. `--comment-file -` / `--metadata-file -` — only one source may read stdin. Both as `-` is rejected: `--comment-file and --metadata-file cannot both read stdin`
5. `--trace-id` — required on `create`; optional filter on `list` / `list detailed`
6. `--folder-key` — required on `create`, `update`, `delete`; optional on `get` / `list`

A flag used against its own `-file` twin is reported before the stdin clash, and both before any file is opened.

## Related

- [Traces — Spans](traces.md) — `uip traces spans get` for span-level observability
- [Run Jobs](../orchestrator/run-jobs.md) — `uip or jobs traces` for trace discovery
