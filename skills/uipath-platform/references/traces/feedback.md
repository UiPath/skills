# Trace Feedback (`uip traces feedback`)

Annotate traces or spans with sentiment and comments for LLM observability, agent output review, and evaluation datasets.

## Commands

| Command | Purpose |
|---|---|
| `create` | Add feedback to a trace or span |
| `get <id>` | Fetch feedback |
| `list` | List feedback with filters |
| `list detailed` | List feedback with span context and extra filters; max 200 |
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

`--trace-id` and `--folder-key` are required; `--trace-id` is a 32-char hex or GUID. Pass exactly one of `--positive` and `--negative`. Optional: `--span-id` (defaults to trace root), `--comment` (max 1048576 chars), `--comment-file` (path or `-` for stdin), repeatable `--category` (built-ins: `"Output"`, `"Agent Error"`, `"Agent Plan Execution"`), `--agent-id` (agent reference GUID), `--agent-version` (max 100 chars), and `--profile <name>` (named login profile). `--comment` and `--comment-file` are mutually exclusive. For another tenant, run `uip login tenant set <tenant>` first; `--tenant` is deprecated.

## get

Positional `<id>` and `--folder-key` are required.

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

Optional filters: `--trace-id`, `--span-id`, `--agent-id`, `--agent-version`, `--positive`, `--negative`, `--limit` (default 20, max 100), `--offset` (default 0), and `--folder-key`. Omit `--trace-id` to filter and paginate across all traces, including by `--agent-id`, `--agent-version`, or `--negative`; `list detailed` is not required.

## list detailed

Adds `spanAttributes` per record with `agentId`, `agentName`, `userPrompt`, and `output`; supports time-range, category, sort, and all `list` filters, returning at most 200 items.

```bash
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

Additional flags: `--since <duration>`, `--after <ISO>`, `--before <ISO>`, repeatable `--category-id <guid>`, `--sort-by <createdAt|updatedAt>` (default `createdAt`), and `--sort-order <asc|desc>` (default `desc`). `list detailed` is not required for cross-trace filtering; plain `list` covers it by omitting `--trace-id`.

## update

Positional `<id>`, exactly one of `--positive` / `--negative`, and `--folder-key` are required.

```bash
uip traces feedback update <feedback-id> \
  --negative \
  --comment "Wrong output" \
  --folder-key <folder-key> \
  --output json
```

Optional: `--comment` or `--comment-file` (path or `-` for stdin; max 1048576 chars), `--metadata` or `--metadata-file` (path or `-` for stdin; valid JSON, max 1048576 chars), repeatable `--category` (replacement, not additive), and `--profile <name>`. Each pair is mutually exclusive.

### Omitted fields are preserved

The API replaces the whole record. Before writing, the CLI reads it and carries over every omitted field; updating only `--metadata` therefore preserves the existing comment and categories. Read-modify-write is not atomic: concurrent edits can be lost, and the API offers no ETag or PATCH.

### Clearing fields

| Field | Clear with |
|---|---|
| Comment | `--comment ""` |
| Metadata | `--metadata ""` |
| Categories | Not possible; `--category ""` stores a tag literally named `""` |

### Metadata must be valid JSON

Any JSON value (object, array, string, or number) is accepted. Non-JSON text is rejected server-side with `INVALID_FEEDBACK_METADATA`; the CLI does not pre-validate and passes it verbatim. Length is checked before JSON validity. `create` has no `--metadata`; set it afterward with `update`.

```bash
uip traces feedback update <feedback-id> \
  --positive \
  --metadata '{"reviewer":"qa","round":2}' \
  --folder-key <folder-key> \
  --output json

uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file review.json \
  --folder-key <folder-key> \
  --output json

jq -n '{reviewer:"qa"}' | uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file - \
  --folder-key <folder-key> \
  --output json
```

## delete

`-y` is required; the CLI never prompts and rejects deletion without it.

```bash
uip traces feedback delete <feedback-id> \
  --folder-key <folder-key> \
  -y \
  --output json
```

## Choosing a span

Without `--span-id`, feedback targets the trace root. In an orchestrating layer (RPA robot job, Maestro case, parent agent, etc.), that root is the orchestrator span, so feedback targets the wrong span and does not appear in the agent review grid.

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

> **Directly-invoked agents only.** When the agent is the top-level span with no parent orchestrator, the root is the agent execution and omitting `--span-id` is safe.

## Mutual exclusion rules

1. `--positive` / `--negative` — mutually exclusive on all commands.
2. `--comment` / `--comment-file` — mutually exclusive on `create` and `update`.
3. `--metadata` / `--metadata-file` — mutually exclusive on `update`.
4. `--comment-file -` / `--metadata-file -` — only one source may read stdin; both as `-` are rejected: `--comment-file and --metadata-file cannot both read stdin`.
5. `--trace-id` — required on `create`; optional filter on `list` / `list detailed`.
6. `--folder-key` — required on `create`, `update`, `delete`; optional on `get` / `list`.

A flag used with its own `-file` twin is reported before the stdin clash; both are reported before any file is opened.

## Related

- [Traces — Spans](traces.md) — `uip traces spans get` for span-level observability
- [Run Jobs](../orchestrator/run-jobs.md) — the job lifecycle these traces come from