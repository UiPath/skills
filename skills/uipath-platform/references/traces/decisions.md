# Trace Decisions (`uip traces decisions`)

Record who decided what on a trace, field by field, and read it back. A decision holds the accepted outcome, the decided fields (proposed value, final value, disposition, proposer), the actor, and optional process context.

## Commands

| Command | Purpose |
|---------|---------|
| `create` | Write one or more decisions to a trace. Writing an existing `decisionId` replaces it |
| `get <id>` | Read one decision by decision ID |
| `list` | Query decisions by trace, process, instance, element, platform, actor, outcome, origin, or time |

Output keeps the API's camelCase keys, so `get` output is valid `create --input` data.

## Critical rules

1. `create` always needs `--trace-id` (32-char hex or GUID) and `--folder-key`. Take the folder key from the user or from `uip or folders get`; never invent one.
2. Every field in a decision needs `proposedBy` (`identity` + `kind`). Without it the API returns HTTP 400.
3. `decisionId` is 16 lowercase hex characters (an OTEL span ID). Omit `--id` to get a generated one. Any other format returns HTTP 400.
4. Pass `--input <file>` for batches or decisions with `sourceAsset`, `implicitSignals`, or dispositions that differ per field. Use flags only for one decision whose fields share a disposition and proposer. The two forms cannot be mixed.
5. Reuse a `decisionId` only to replace that decision. A second write with the same ID overwrites the first.
6. Read the `create` result: it returns one `{ decisionId, feedbackId }` per decision. Confirm with `get` or `list` before reporting success.
7. On HTTP 500 repeat the identical command once. A write is idempotent per `decisionId`, so a repeat does not duplicate.
8. Use only the logged-in session. Never ask for, paste, or echo a token.

## create

From a file (one decision object or an array; `-` reads stdin):

```bash
uip traces decisions create \
  --trace-id <TRACE_ID> \
  --input <DECISIONS_FILE> \
  --folder-key <FOLDER_KEY> \
  --output json
```

From flags (one decision; every `--field` shares the disposition and proposer):

```bash
uip traces decisions create \
  --trace-id <TRACE_ID> \
  --outcome "<ACCEPTED_OUTCOME>" \
  --actor <ACTOR_IDENTITY> \
  --field <FIELD_NAME>=<VALUE> \
  --folder-key <FOLDER_KEY> \
  --output json
```

| Flag | Required | Notes |
|------|----------|-------|
| `--trace-id` | Yes | 32-char hex or GUID |
| `--folder-key` | Yes | |
| `--input` | One of `--input` or flags | JSON file; `-` for stdin |
| `--outcome` | With flags | Accepted outcome |
| `--actor` | With flags | Identity of whoever decided |
| `--field name=value` | With flags, repeatable | Value read as JSON when valid (`1065` is a number), else text |
| `--id` | No | Decision ID, 16 lowercase hex characters. Default: generated |
| `--actor-kind` | No | `Automation`, `Human`, `Rule`, `Agent`. Default `Human` |
| `--platform` | No | `ActionCenter`, `CodedApp`, `VerticalUi`. Default `ActionCenter` |
| `--disposition` | No | `Accepted`, `LightlyEdited`, `Rewritten`, `Rejected`, `Ignored`. Default `Accepted` |
| `--proposed-by` | No | Who proposed the `--field` values. Default: the actor |
| `--proposed-by-kind` | No | `Automation`, `Person`, `Agent`, `Team`. Default `Person` |
| `--rejected-outcome` | No | Repeatable |
| `--evidence` | No | Repeatable explicit evidence line |
| `--timestamp` | No | ISO 8601. Default: now |
| `--process-key` / `--process-version` / `--instance-id` / `--element-id` | No | Process context |
| `--profile <name>` | No | Named login profile |

## Input file shape

```json
[
  {
    "decisionId": "<DECISION_ID>",
    "data": {
      "<FIELD_NAME>": {
        "proposedValue": "<PROPOSED>",
        "finalValue": "<FINAL>",
        "disposition": "Rewritten",
        "proposedBy": { "identity": "<PROPOSER>", "kind": "Agent" },
        "sourceAsset": { "kind": "Process", "id": "<ASSET_ID>", "version": "<VERSION>" }
      }
    },
    "actor": { "identity": "<ACTOR_IDENTITY>", "kind": "Human" },
    "acceptedOutcome": "<ACCEPTED_OUTCOME>",
    "rejectedOutcomes": ["<REJECTED_OUTCOME>"],
    "decisionTimestamp": "<ISO_8601_TIMESTAMP>",
    "explicitEvidences": ["<EVIDENCE>"],
    "implicitSignals": { "<KEY>": "<VALUE>" },
    "processInstanceMetadata": {
      "processKey": "<PROCESS_KEY>",
      "processVersion": "<PROCESS_VERSION>",
      "instanceId": "<INSTANCE_ID>",
      "elementId": "<ELEMENT_ID>"
    },
    "platform": "ActionCenter"
  }
]
```

Required per decision: `decisionId`, `data`, `actor`, `acceptedOutcome`, `decisionTimestamp`, `platform`. Required per field: `disposition`, `proposedBy`. `sourceAsset.kind` is one of `Agent`, `Automation`, `Process`, `Rule`, `Ontology`, `Knowledge`.

Field names under `data` are the caller's; the CLI never changes their casing.

## get

```bash
uip traces decisions get <DECISION_ID> --folder-key <FOLDER_KEY> --output json
```

`--include-spans` adds the span that carries the decision. An unknown ID exits 1 with `Decision <id> not found.`.

## list

```bash
uip traces decisions list \
  --trace-id <TRACE_ID> \
  --folder-key <FOLDER_KEY> \
  --output json
```

| Flag | Notes |
|------|-------|
| `--trace-id` | 32-char hex or GUID |
| `--process-key` / `--process-version` / `--instance-id` / `--element-id` | Process context filters |
| `--platform` | `ActionCenter`, `CodedApp`, `VerticalUi` |
| `--actor` / `--actor-kind` | Identity and kind (`Automation`, `Human`, `Rule`, `Agent`) |
| `--outcome` | Accepted outcome |
| `--origin` | Origin value |
| `--from` / `--to` | ISO 8601 time bounds |
| `--include-spans` | Include the carrying span |
| `--limit` | Default 20 |
| `--offset` | Row offset, default 0 |

`Data` is an array (empty when nothing matches). `Pagination.Total` is the match count; page with `--offset` while `Pagination.HasMore` is true.

## Error handling

| Symptom | Action |
|---------|--------|
| `--trace-id is required` / `--folder-key is required` | Add the flag. Take the folder key from the user |
| `Invalid trace ID format` | Pass 32 hex characters or a GUID |
| HTTP 400 naming `proposedBy` | Add `proposedBy` to every field in `data` |
| HTTP 400 naming `OTEL SpanId` | Use a 16-char lowercase hex `decisionId` |
| `Not authenticated` | Run `uip login --authority <AUTHORITY> --organization <ORG> --tenant <TENANT>`; never ask for a token |
| `Insufficient permissions` | The user needs Logs permissions on the folder; stop and report |

## Anti-patterns

- Reusing one `decisionId` for different decisions in the same trace; the second replaces the first.
- Building the JSON by string concatenation. Write the file with a JSON-aware tool.
- Putting a token in a command, file, or message.
