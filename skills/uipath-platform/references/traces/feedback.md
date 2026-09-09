# Trace Feedback (`uip traces feedback`)

Annotate traces or spans with sentiment and comments for LLM observability, output-quality review, and evaluation datasets.

## Commands

| Command | Purpose |
|---|---|
| `create` | Add feedback to a trace or span |
| `get <id>` | Fetch feedback |
| `list` | List feedback with filters |
| `list detailed` | List feedback with span context and extra filters (max 200 items) |
| `update <id>` | Change sentiment, comment, metadata, or categories |
| `delete <id>` | Remove feedback |

## create

Run:

```bash
uip traces feedback create \
  --trace-id <TRACE_ID> \
  --positive \
  --comment "Correct summary" \
  --category "Output" \
  --folder-key <folder-key> \
  --output json
```

`--trace-id` is required and accepts a 32-char hex or GUID. Pass exactly one of `--positive` or `--negative`; they are mutually exclusive. `--folder-key` is required. `--span-id` is optional and defaults to the root span. `--comment` (max 1048576 chars) and `--comment-file` are mutually exclusive; `--comment-file` accepts a file path or `-` for stdin. `--category` is repeatable; built-in values are `"Output"`, `"Agent Error"`, and `"Agent Plan Execution"`. `--agent-id` accepts an agent reference GUID, and `--agent-version` accepts at most 100 chars.

Pass `--profile <name>` for a named login profile. For another tenant, run `uip login tenant set <tenant>` first; `--tenant` is deprecated. `create` has no `--metadata`; run `update` after creating to set metadata.

## get

Run:

```bash
uip traces feedback get <feedback-id> --folder-key <folder-key> --output json
```

Positional `<id>` and `--folder-key` are required.

## list

Run:

```bash
uip traces feedback list \
  --trace-id <trace-id> \
  --folder-key <folder-key> \
  --output json
```

Supported flags: `--trace-id` (omit to filter and paginate across all traces), `--span-id`, `--agent-id`, `--agent-version`, `--positive`, `--negative`, `--limit` (default 20, maximum 100), `--offset` (default 0), and optional `--folder-key`. Omit `--trace-id` to filter across traces, including by `--agent-id`, `--agent-version`, or `--negative`; `list detailed` is not required.

## list detailed

Run:

```bash
uip traces feedback list detailed \
  --since 24h \
  --folder-key <folder-key> \
  --output json
```

Each record adds `spanAttributes` containing `agentId`, `agentName`, `userPrompt`, and `output`. Additional flags: `--since <duration>`, `--after <ISO>`, `--before <ISO>`, repeatable `--category-id <guid>`, `--sort-by <createdAt|updatedAt>` (default `createdAt`), and `--sort-order <asc|desc>` (default `desc`). The maximum is 200 items. It is not required for cross-trace filtering.

## update

Run:

```bash
uip traces feedback update <feedback-id> \
  --negative \
  --comment "Wrong output" \
  --folder-key <folder-key> \
  --output json
```

Positional `<id>`, exactly one of `--positive` / `--negative`, and `--folder-key` are required. Supported flags:

- `--positive` / `--negative`: mutually exclusive.
- `--folder-key`: required.
- `--comment`: max 1048576 chars; mutually exclusive with `--comment-file`.
- `--comment-file`: file path or `-` for stdin.
- `--metadata`: valid JSON, max 1048576 chars; mutually exclusive with `--metadata-file`.
- `--metadata-file`: file path or `-` for stdin.
- `--category`: repeatable; replacement, not additive.
- `--profile <name>`: named login profile.

The API replaces the whole record. The CLI reads it before writing and carries over fields not passed by the caller, so updating only `--metadata` preserves the existing comment and categories. Read-modify-write is not atomic; concurrent edits can be lost. The API provides no ETag or PATCH.

Clear fields as follows:

| Field | Clear with |
|---|---|
| Comment | `--comment ""` |
| Metadata | `--metadata ""` |
| Categories | Not possible; `--category ""` stores a tag literally named `""` |

Metadata accepts any JSON value: object, array, string, or number. Non-JSON text is rejected server-side with `INVALID_FEEDBACK_METADATA`; the CLI does not pre-validate. The value passes through verbatim, and length is checked before JSON validity.

Run:

```bash
uip traces feedback update <feedback-id> \
  --positive \
  --metadata '{"reviewer":"qa","round":2}' \
  --folder-key <folder-key> \
  --output json
```

For large or nested payloads, run:

```bash
uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file review.json \
  --folder-key <folder-key> \
  --output json
```

From stdin, run:

```bash
jq -n '{reviewer:"qa"}' | uip traces feedback update <feedback-id> \
  --positive \
  --metadata-file - \
  --folder-key <folder-key> \
  --output json
```

## delete

`-y` is required; the CLI never prompts and rejects deletion without it. Run:

```bash
uip traces feedback delete <feedback-id> \
  --folder-key <folder-key> \
  -y \
  --output json
```

## Choosing a span

Omitting `--span-id` targets the trace's root span. In an orchestrating layer (RPA robot job, Maestro case, parent agent, etc.), the root is the orchestrator's span, so feedback lands on the wrong span and does not appear in the agent review grid.

**Always pass `--span-id` when the agent runs inside any orchestrating layer.**

**Always target the `agentRun` span.**

### Find the agentRun span ID

Run:

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

> **Directly-invoked agents only.** When the agent is the top-level span with no parent orchestrator, the root span is the agent execution and omitting `--span-id` is safe.

## Mutual exclusion rules

1. `--positive` / `--negative` are mutually exclusive on all commands.
2. `--comment` / `--comment-file` are mutually exclusive on `create` and `update`.
3. `--metadata` / `--metadata-file` are mutually exclusive on `update`.
4. `--comment-file -` / `--metadata-file -`: only one source may read stdin. Both as `-` are rejected: `--comment-file and --metadata-file cannot both read stdin`.
5. `--trace-id` is required on `create` and optional as a filter on `list` / `list detailed`.
6. `--folder-key` is required on `create`, `update`, and `delete`, and optional on `get` / `list`.

A flag used with its own `-file` twin is reported before the stdin clash, and both are reported before any file is opened.

## Related

- [Traces — Spans](traces.md) — `uip traces spans get` for span-level observability
- [Run Jobs](../orchestrator/run-jobs.md) — `uip or jobs traces` for trace discovery