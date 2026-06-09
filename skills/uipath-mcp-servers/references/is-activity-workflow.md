# IS-Activity Tool Authoring

Wrap an Integration Service connector activity as an MCP tool via `uip agenthub mcp-tools create-is-activity`. Discovery verb is `uip is resources run` / `describe` (pre-rename `execute` → use `run`).

**Division of labor.** The metadata-*discovery* workflow — `describe`, reference resolution, cascade (`-f`), scope filtering, static-value labeling — lives in the platform IS references below; this file does not restate it. This file owns the MCP-tool layer: turning discovered metadata into the `create-is-activity` payload (`ActivityMetadata`, `inputSchema`, `outputSchema`). **Do not author IS metadata from memory** — a `designTimeLookups` / `-f` / `reference` shape that "looks right from a rule" still gets the wrong shape per connector and fails at runtime after passing `--dry-run`. Read the platform section at the action-trigger below even when confident.

## Platform IS references — read by action

In `../../uipath-platform/references/integration-service/`. Each is small. Do NOT read all upfront — before performing each action, read the named section first. The blind spots are unknown-unknowns, so the trigger is the action, not your sense of certainty.

| Before this action | First read |
|---|---|
| `uip is connections list <key>` for the first time | `connections.md` §`Folder Scoping` (pass `--folder <name-or-key>`) |
| `is resources describe ... -f <parent>=<value>` (any cascade re-run) | `resources.md` §`Parent-Field-Driven Custom Fields` (`-f` shape, `--operation` requirement, `--action` rule, merge semantics) |
| A `staticValues.<bucket>.<field>` whose describe field has a `.reference` block | `reference-resolution.md` §`Static Reference-Value Labeling` (`designTimeLookups` format + cascade-scope edge cases) |
| An `inputSchema.properties.<field>` whose `.reference.path` contains `{otherField}` | `reference-resolution.md` §`Field Dependency Chains` (resolve parent first) |
| An `inputSchema.properties.<field>` whose `.reference.filterPattern` contains `{filter}` | `reference-resolution.md` §`Search References` |
| Resolving a reference where `run list` returns `scope: null` AND `scope.type: "PROJECT"` rows | `reference-resolution.md` §`Scope Filtering` |
| Diagnosing a `describe` server-side failure | `resources.md` §`Describe Failures` |
| Final gate before `create-is-activity --dry-run` | `reference-resolution.md` §`Validate Required Fields Before Executing` |

## Critical rules (extend SKILL.md)

1. **Discover before authoring.** `candidates --category is-activity` resolves connector + activity; `is resources describe` pulls field metadata. Compose `metadata` / `inputSchema` / `outputSchema` from the describe response, never from memory — every connector + operation has its own shape.
2. **Connection is folder-scoped.** `uip is connections list <connector> --folder <name-or-key> --output json` (the unfiltered form silently filters to the current context and may return empty). Pass `--target-identifier <connection-guid>`; the CLI derives `targetFolderKey` — there is **no** `--target-folder-key` for IS-activity tools. `Reason: CrossFolderConnection` → pick from `Data.candidates`. (`connections.md` §`Folder Scoping` / §`Selecting a Connection`)
3. **Cascade api-type ObjectActions.** `describe <key> <objectName> --connection-id <id> --operation <op>`; if `requestFields` is short for the operation, re-run with `-f <parent>=<value>` (repeatable). Omit `--action` for Jira `curated_create_issue` Create (passing it → `No api-type ObjectAction matched`); pass `--action` only when describe reports multiple matches. Cascade examples: Jira `curated_create_issue`, Salesforce `query_records`, Dataservice V3. (`resources.md` §`Parent-Field-Driven Custom Fields`)
4. **Baked static reference values need `designTimeLookups`.** Every `staticValues.<bucket>.<field>` (any bucket — `field` / `query` / `header` / `path`) whose describe field has a `.reference` block MUST emit `designTimeMetadata.designTimeLookups[<dotted-field>] = "<displayName> - <value>"`. Applies to `requestFields[]` and `parameters[]`; NOT to runtime / enum fields — labeling renders only for baked values. (`reference-resolution.md` §`Static Reference-Value Labeling`)
5. **Stringify `metadata` / `inputSchema` / `outputSchema` as scalars** — SDK types them `string | null`. Build each in a file and pass `--metadata "$(jq -c . metadata.json)"`; do not assemble multi-KB JSON inline, and do not mix `--file` with scalar options (`ConflictingInput`). `--output-schema "{}"` when the activity has no `responseFields` (empty string → `Unexpected end of JSON input`).
6. **Ask — don't guess — when a value drives discovery.** Cascade `-f` parents, a search-reference `{filter}`, a dependency-chain parent, or a required reference with no user hint: STOP and ask, even in autonomous mode. **No autonomous fallback exists.** If the user defers ("Other" / "you decide" / silence), re-ask in plain text — do NOT fall back to free runtime, a guessed default, or silently skipping the tool. Bounded set (2–4 candidates) → `AskUserQuestion` (do not add "Other"; it is auto-appended; <2 options errors). Unbounded set (dozens+) → plain text showing the top 5–10 candidates by a real attribute plus the exact format you need (`"<project key> + <issue type>"`). Never filter an unbounded `run list` with a guessed `JMESPath` name — a miss returns `[]` with no signal.

## Reference fields — the 3-way choice

For every `requestFields[name].reference` or `parameters[name].reference` (`reference-resolution.md` §`Reference Fields`), run `uip is resources run list <connector> <reference.objectName> --connection-id <id> --output json`, then pick per field:

- **(a) Bake** — `staticValues.<bucket>.<field> = <value>` + a `designTimeLookups` entry (Rule 4). When one value applies to every call (user named it).
- **(b) Constrained runtime** — `inputSchema.properties.<field> = {type: string, enum: [<discovered values>]}`. When the set is bounded (≤ 20–50), stable, known now. No lookup needed.
- **(c) Free runtime** (default) — `inputSchema.properties.<field> = {type: string}`, no enum. When the set is large / volatile (IDs, free text, search inputs). The `description` is the prompt the consuming LLM reads: noun phrase + format (e.g. `"IANA timezone like 'UTC'"`) + omission behavior + constraints.

Cascade roots and search references with no user-supplied filter = **hard ask** (Rule 6) — no "pick first" / "most-recent" default. Non-cascade required references default to (c) in autonomous mode; use (b) only when the set is genuinely small and stable.

## Pre-flight (walk before drafting `--metadata`)

0. **Scope.** Restate server slug, folder, exact tool list (one bullet per `<connector> · <activity> · <op>`), baked statics. Folder: if unnamed, `uip or folders list --output json` → `Shared` (org-default) or `<email>'s workspace` (personal needs `--folder-key <guid>`). Run `mcp-tools list --mcp <slug> --folder-path <name>` first — same name + connector + objectName exists → ask update vs add-new.
1. **Connection** — Rule 2. Confirm even on a single match (present name / owner / folder, never UUIDs, per `connections.md` §`Selecting a Connection`). N>1 → ASK. Zero → retry `--refresh`, then surface a create-connection hint and STOP.
2. **Activity disambiguation.** `candidates --category is-activity --connector <key>` returns ≥2 overlapping entries (`send_message_to_channel` vs `_to_user`) → ASK. GET tie-break: `Get…` / `Find…` without an id → `List`; `Get … by …` or path `{id}`/`{key}` → `Retrieve`; unsure → describe without `--operation`, present `Data.availableOperations[]`.
3. **Reference fields** — the 3-way choice above, per field.
4. **Required scalar with no enum / reference / description** → STOP, ask (e.g. Slack `UsersByEmail.By`). Do not bake a guess.

Multi-tool builds ("server with tools for X and Y"): re-walk Pre-flight + the command steps per tool — by tool 3 you drift toward tool 1's model.

## `ActivityMetadata` (the object to stringify into `--metadata`)

```jsonc
{
  "connector":   { "key": "<connector-key>" },              // from candidates
  "object": {
    "path":        "<availableOperations[chosen].path — e.g. /issue/{issueKey}/comment/{commentId}>",
    "objectName":  "<the describe argument, e.g. issue_comment>",
    "method":      "<GET|POST|PATCH|PUT|DELETE — from availableOperations[chosen].method>",
    "contentType": "application/json"
  },
  "mapping": {
    "path":   ["issueKey", "commentId"],   // property names filling {placeholder} tokens in object.path
    "query":  ["maxResults", "startAt"],   // parameters[i] where .type === "query"
    "header": [],                           // parameters[i] where .type === "header"
    "field":  []                            // body fields (typically requestFields[])
  },
  "staticValues": {
    "query":  { /* field-name: literal value the LLM cannot override */ },
    "header": { },
    "path":   { },
    "field":  { /* body fields the LLM cannot override */ }
  },
  "designTimeMetadata": {
    "designTimeLookups": {
      // one entry per staticValues.* field whose describe field has .reference
      // value format: "<displayName> - <baked-value>"  e.g. "fields.project.key": "Orchestrator - OR"
      // see Critical Rule 4
    },
    "manageProperties": []
  },
  "metadataVersion": 1
}
```

`staticValues` holds only values the LLM cannot override (`processType`, baked enum choices, baked reference IDs); runtime values belong in `inputSchema.properties`. Emit flat dotted keys (`"fields.project.key": "OR"`); the FE may persist them nested on save — both round-trip through `ParameterMappingService`'s four-bucket iteration (`Query` / `Path` / `Header` / `Field`).

`inputSchema.properties` = `requestFields ∪ parameters` not covered by `staticValues`. Per entry: name = `parameters[i].name` / `requestFields[j].name`; `title` = `displayName ?? name`; `description`; `type` from `dataType` / field shape; add to `required[]` when `.required === true`; honor `enum` / `.reference` (the 3-way choice). Curated activities often have empty `requestFields[]` before cascade — `parameters` is then the input source. Set `additionalProperties: false`. `mapping.path` must list every `{token}` in `object.path` by property name (CLI validates client-side).

`outputSchema` is a real JSON Schema built from `Data.responseFields` (walk like `inputSchema.properties`). Do not ship `{"type":"object","additionalProperties":true}`. `"{}"` only when the activity genuinely has no response body.

## Workflow (commands)

```bash
# 0 — folders (once per machine); personal workspace needs --folder-key, not --folder-path
uip or folders list --output json

# 1 — confirm / create the `uipath`-type server (slug ^[a-z0-9-]+$, len 3-50)
uip agenthub mcp list --folder-path <folder> --output-filter "Data.items[].slug" --output json
uip agenthub mcp create uipath --name "<display>" --slug <slug> --folder-path <folder> --output json

# 2 — connector key + activity (vendor name ≠ connector key; e.g. Slack → uipath-salesforce-slack)
uip agenthub mcp-tools candidates --category is-activity --name <vendor> --output json
uip agenthub mcp-tools candidates --category is-activity --connector <key> --output json
# Read Data.items[].{connectorKey, objectName, methodName, displayName}. Multi-candidate → Pre-flight 2.

# 3 — describe: operations, then field metadata  (cascade/reference mechanics → platform refs)
uip is resources describe <key> <objectName> --connection-id <id> --output json            # Data.availableOperations[]
uip is resources describe <key> <objectName> --connection-id <id> --operation <op> --output json
# requestFields[] (body), parameters[] (path/query/header), responseFields[] (output).
# Short requestFields → curated: cascade with -f per resources.md §Parent-Field-Driven Custom Fields.

# 4 — connection in the server's folder        [READ: connections.md §Selecting a Connection + §Folder Scoping]
uip is connections list <connector-key> --folder <server-folder-name-or-key> --output json

# 5 — label every baked static reference value  [READ: reference-resolution.md §Static Reference-Value Labeling]
uip is resources run list <connector> <reference.objectName> --connection-id <id> --output json

# 6 — dry-run preview (skips some server-side checks; can pass while the real POST fails)
uip agenthub mcp-tools create-is-activity ... --dry-run --output json   # inspect Data.resolved.{metadata,inputSchema,outputSchema}

# 7 — create
uip agenthub mcp-tools create-is-activity \
  --mcp <slug> --name "<tool name>" --description "<1-4000 chars; shown in AgentHub UI>" \
  --folder-path "<server folder>" --target-identifier <connection-guid> \
  --metadata "$(jq -c . metadata.json)" --input-schema "$(jq -c . input-schema.json)" \
  --output-schema "$(jq -c . output-schema.json)" --output json   # Data.id = created tool ID

# 8 — verify (do NOT claim done before this passes)
uip agenthub mcp-tools list --mcp <slug> --folder-path <folder> --output json
# Confirm id/name/description/mcpName. High-value tools: smoke-test via `uip is resources run <verb>`.
```

Update (metadata/schemas changed) — scalars only, `--output-schema "{}"` for no response body:

```bash
uip agenthub mcp-tools update <tool-id> --mcp <slug> --folder-path "<folder>" \
  --metadata "$(jq -c . metadata.json)" --input-schema "$(jq -c . input-schema.json)" \
  --output-schema "$(jq -c . output-schema.json)" --output json
```

Delete: `uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --yes --output json`.
Skeleton for `--file`: `uip agenthub mcp-tools template is-activity --output json`.

## IS-Activity Troubleshooting

- **HTTP 400, no detail** — re-run `--dry-run`; CLI surfaces ASP.NET ProblemDetails as an `Errors` field of per-field failures.
- **404 at runtime** — `metadata.mapping.path` missing a `{token}` from `object.path`. List every placeholder and retry.
- **`Reason: CrossFolderConnection`** — connection in a different folder than the server. Pick a `Data.candidates` entry via `--target-identifier <guid>`, or move the connection / server.
- **`Operation 'X' not found. Available: <Y>`** — curated activity exposes only `Y`. Re-run `describe` without `--operation`, pick from `Data.availableOperations[]`.
- **`No api-type ObjectAction matched for fields [...]`** — `-f` set matches no registered action, or `--action` was passed when it should be omitted (Jira `curated_create_issue` Create). Drop `--action` first; else inspect `connectorMethodInfo.design.actions[]` / `objectActions[]` for required `-f` shapes.
- **Form renders raw scalar (`OR`, `3`) instead of a labeled value** — `designTimeLookups[<field>]` missing (Rule 4 / Step 5), then `mcp-tools update <tool-id>`.
- **`ConflictingInput: Use exactly one of --file, --body, or scalar options.`** — pass schemas as scalars, not `--file`.
- **`Unexpected end of JSON input` on `--output-schema`** — pass `"{}"` for no-response-body activities.
- **`connections list <key>` empty in one folder, connection exists elsewhere** — folder-scoped; re-run with `--folder <name-or-key>` of the server's folder (`connections.md` §`Folder Scoping`).
- **403 Forbidden at runtime** — connection scope mismatch; re-authorize via `uip is connections edit <id>` with broader scopes (`connections.md` §`Scope-Related Errors`).

For generic AgentHub-MCP issues (slug regex, folder context, refresh-tools async/sync, `mcp delete` lookup), see SKILL.md §Troubleshooting.
