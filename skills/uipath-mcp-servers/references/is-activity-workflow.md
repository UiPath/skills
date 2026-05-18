# IS-Activity Tool Authoring

Full workflow for `uip agenthub mcp-tools create-is-activity` — wrapping an Integration Service connector activity as a tool on a `uipath`-type AgentHub MCP server. The parent SKILL.md keeps the generic server + tool-kind surface; this file owns the IS-activity-specific rules, pre-flight, workflow, and `ActivityMetadata` shape.

Read this end-to-end before authoring an IS-activity tool. Pair it with the cross-skill IS references it points at.

## IS-Activity-Specific Critical Rules

These extend the generic Critical Rules in SKILL.md.

1. **Discover before authoring.** `mcp-tools candidates` resolves connector + activity. `is resources describe` pulls field metadata. Curated / api-type activities (Jira `curated_create_issue`, Salesforce SOQL, Dataservice V3) need the `-f` cascade (Rule 4) to surface the real schema — base describe shows only cascade-root fields.

2. **Stringify `metadata` / `inputSchema` / `outputSchema`** before passing to `--metadata` / `--input-schema` / `--output-schema`. SDK types them as `string | null`. Empty `--output-schema ""` is rejected with `Unexpected end of JSON input` — pass `"{}"` when the activity has no responseFields.

3. **Connection: pass `--target-identifier <connection-guid>`.** `uip is connections list <connector-key> --output json` → pick a connection in the MCP server's folder → pass its GUID. CLI derives `targetFolderKey` from the connection; no separate flag. Cross-folder surfaces as `Reason: CrossFolderConnection` with `Data.candidates` — pick from candidates or move the connection. Full selection algorithm: `../../uipath-platform/references/integration-service/connections.md`.

4. **Operation discovery + cascade.** Run `is resources describe` WITHOUT `--operation` first → read `Data.availableOperations[].{name, path, method}`. `Data.object` is `null` on curated activities — use `availableOperations` entries. For api-type ObjectActions (Jira `curated_create_issue` Create, Salesforce SOQL `GenerateQuerySchema`, Dataservice V3 `FetchObjectMetadataTenant`), the base describe returns only cascade-root fields (e.g. `fields.project.key`, `fields.issuetype.id`); re-run with `-f field=value` to expand the full schema. **Omit `--action` for `curated_create_issue` Create** — passing it causes `No api-type ObjectAction matched for fields [...]`. Pass `--action <name>` only when describe reports multiple matching actions.

5. **Static reference values need `designTimeLookups`.** Every `staticValues.<bucket>.<field>` (any bucket — `field`, `query`, `header`, `path`) whose describe field has a `.reference` block must also emit `designTimeMetadata.designTimeLookups[<field>] = "<displayName> - <value>"` so the edit-UI renders the label. Applies to `requestFields[]` AND `parameters[]`. Runtime fields in `inputSchema.properties` do NOT need lookups — labeling only applies to baked values. Resolver runs at Workflow Step 3d; cascade-scoped edge cases in `../../uipath-platform/references/integration-service/reference-resolution.md § Static Reference-Value Labeling`.

## Pre-flight

Walk these checks before writing `--metadata`. Use AskUserQuestion (one option per choice + "Something else"). Autonomous mode: still resolve every reference (pick the first/most-recently-used entry from `execute list`), log the choice, and surface it back to the user ("I baked `project=OR` — change with `mcp-tools update`").

0. **Scoping (multi-tool builds).** Restate: server slug, folder, exact tool list (one bullet per `<connector> · <activity> · <op>`), baked statics. Ambiguous asks ("Jira and Slack tools") → pick the canonical set and confirm, or proceed-and-flag in autonomous mode.
   - **Folder pick.** If the user didn't name a folder, run `uip or folders list --output json` and choose: `Shared` (org-level default — preferred when teammates may share the server) OR personal workspace (`<email>'s workspace`, type `Personal` — preferred for personal-use tools). Personal workspaces require `--folder-key <guid>` (name lookup fails). Surface: `"server folder: Shared (default — change with --folder-path <name>)"`.
   - **Existing tool inventory.** Run `uip agenthub mcp-tools list --mcp <slug> --folder-path <name> --output json` before drafting. Catches duplicates and reveals naming conventions. Same name + connector + objectName already exists → surface and ask update vs add-new.
   - **Activity named, binding not.** "Create a Jira issue tool" names the activity, not project/issue-type/etc. For api-type connectors (Jira `curated_create_issue`, Salesforce SOQL, …) with required references at create-time, STOP and ask — even in autonomous mode. Cascade `-f` (Rule 4) depends on these values; guessing propagates errors.
1. **Connection** — `uip is connections list <connector> --output json` returns N>1 → ask "Which connection?" with one option per `<Name> in <Folder>` + "Something else".
2. **Activity disambiguation** — `candidates --connector <key>` returns ≥ 2 entries with overlapping descriptions (`send_message_to_channel` vs `send_message_to_user`, `curated_get_issue` Retrieve vs `search_issues_with_fields`) → ask. GET tie-break: `Get …`/`Find …` without ID → `List`; `Get … by …` or path `{id}`/`{key}` → `Retrieve`. When in doubt, describe without `--operation`.
3. **Reference fields — discover, then present a 3-way choice (never default).** For every `requestFields[name].reference` OR `parameters[name].reference`:
   - Run `uip is resources execute list <connector> <referenced-object> --connection-id <id>` and capture the top N candidates.
   - Present three options:
     - **(a) Bake one value** — `staticValues.<bucket>.<field> = <value>` + `designTimeMetadata.designTimeLookups[<field>] = "<displayName> - <value>"`. Pick when one value applies to every call.
     - **(b) Constrain at runtime** — `inputSchema.properties.<field> = {type: string, enum: [<discovered values>]}`. LLM picks from a known-valid set. No lookup needed.
     - **(c) Free runtime** — `inputSchema.properties.<field> = {type: string}`, no enum. Pick when the set is large, changes frequently, or new values appear at runtime (issue IDs, message text).
   - **Required** reference parameters: forcing question — do not skip. "LLM picks the channel" usually doesn't distinguish (b) from (c); confirm.
   - Autonomous-mode default: (b) constrained when the discovered set is bounded (≤ 50 entries). Surface the choice and enum size.
4. **Enum fields the user didn't specify** — if `enum` has ≥ 2 values, ask. ≤ 1 value or an explicit user value → bake into `staticValues` silently.
5. **Cascade `-f` parents** — for api-type ObjectAction connectors, collect parent values from the user before cascade (IS-Activity Rule 4).
6. **Required scalar with no enum / no reference / no description** — STOP. Ask. Do not bake a guess (e.g., Slack `UsersByEmail.By` is a required string with no enum — valid values are connector-specific).

Asking once produces the right tool. Guessing produces wrong tools.

## Workflow

```bash
# Pre-step 0 — discover folders (once per machine)
uip or folders list --output json
# Read .[].Key + .[].DisplayName. Personal workspace folder requires --folder-key (not --folder-path).

# Pre-step 1 — confirm or create the MCP server
uip agenthub mcp list --folder-path <folder-name> --output json
# Read Data.items[].slug. --folder-path / --folder-key is required.

# If missing — `uipath` is the server-type literal (not the server name).
# --name is the display name; --slug is the canonical id (^[a-z0-9-]+$, 3-50):
uip agenthub mcp create uipath --name "<display>" --slug <slug> --folder-path <folder-name> --output json
# Alternate payload: --file <path> or --body <json>. Schema via `uip agenthub mcp create uipath --print-schema`.

# Step 1 — find the connector key
uip agenthub mcp-tools candidates --category is-activity --name <vendor> --output json
# Read Data.items[].connectorKey (also .id). Vendor name ≠ connector key (e.g. Slack → uipath-salesforce-slack).

# Step 2 — find the activity (objectName, methodName, operation)
uip agenthub mcp-tools candidates --category is-activity --connector <key> --output json
# Read Data.items[].{objectName, methodName, displayName}. Multi-candidate → Pre-flight #2.

# Step 3a — enumerate operations  (Read first: resources.md § Describe Response)
uip is resources describe <key> <objectName> --connection-id <id> --output json
# Read Data.availableOperations[].{name, path, method}. Data.object is null on curated activities — use availableOperations entries.

# Step 3b — field metadata + cascade if api-type  (Read first: resources.md § Parent-Field-Driven Custom Fields)
uip is resources describe <key> <objectName> --connection-id <id> --operation <name-from-3a> --output json
# Read Data.requestFields[] (body), Data.parameters[] (query/path/header), Data.responseFields[] (output).
# For api-type ObjectActions (curated_create_issue, GenerateQuerySchema, FetchObjectMetadataTenant): rerun with
#   -f <parent>=<value> ... --action <name>   to expand the full schema (IS-Activity Rule 4).
# If requestFields looks short for the operation (e.g. Create Issue without summary), the connector is curated —
# the cascade is required, not optional.

# Step 3c — find the connection in the right folder
uip is connections list <connector-key> --output json
# Read Data.items[].{id, name, folder.key}. Pick the connection whose folder.key matches the MCP server's folder.
# Personal workspace folder: see generic Critical Rule on --folder-key (SKILL.md).

# Step 3d — resolve labels for every static reference value  (Read first: reference-resolution.md § Static Reference-Value Labeling)
# Run the 4-step resolver (IS-Activity Rule 5) per baked staticValues entry.

# Step 3e — preview the POST body
uip agenthub mcp-tools create-is-activity ... --description "<one-line>" --dry-run --output json
# Inspect Data.resolved.{metadata,inputSchema,outputSchema}. --dry-run skips some server-side validation
# (description, designTimeLookups), so it can pass while the real POST fails.

# Step 4 — create the tool
uip agenthub mcp-tools create-is-activity \
  --mcp <slug> \
  --name "<tool name>" \
  --description "<one-line, 1-4000 chars — surfaces in the AgentHub UI>" \
  --folder-path "<server folder>" \
  --target-identifier <connection-guid> \
  --metadata     "$(jq -c . metadata.json)" \
  --input-schema "$(jq -c . input-schema.json)" \
  --output-schema "$(jq -c . output-schema.json)" \
  --output json
# Read Data.id (the created tool ID).

# Step 5 — verify (do NOT claim done before this passes)
uip agenthub mcp-tools list --mcp <slug> --folder-path <folder-name> --output json
# Re-list tools. Confirm the new tool's id, name, description, mcpName are present.
# For high-value tools, also smoke-test via `uip is resources execute` with realistic inputs against a sandbox.
```

Update an existing tool when metadata or schemas change:

```bash
uip agenthub mcp-tools update <tool-id> \
  --mcp <slug> \
  --description "<one-line>" \
  --folder-path "<server folder>" \
  --metadata     "$(jq -c . metadata.json)" \
  --input-schema "$(jq -c . input-schema.json)" \
  --output-schema "$(jq -c . output-schema.json)" \
  --output json
```

Pass `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`). Pass `--output-schema "{}"` when the underlying activity has no responseFields.

Delete a tool:

```bash
uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --output json
```

Body shape for `--file`:

```bash
uip agenthub mcp-tools template is-activity --output json
```

Multi-tool requests ("server with tools for X and Y"): walk Pre-flight + Steps 1–5 per tool. Re-walk Pre-flight 1–6 before each tool — by tool 3 you are working from a mental model of tool 1, which drifts.

## `ActivityMetadata` (the object to stringify into `--metadata`)

```jsonc
{
  "connector":   { "key": "<connector-key>" },              // from Step 1
  "object": {
    "path":        "<from Data.availableOperations[chosen].path — e.g. /issue/{issueKey}/comment/{commentId}>",
    "objectName":  "<the describe argument, e.g. issue_comment>",
    "method":      "<GET|POST|PATCH|PUT|DELETE — from availableOperations[chosen].method, mapped if needed>",
    "contentType": "application/json"
  },
  "mapping": {
    "path":   ["issueKey", "commentId"],   // property names filling {placeholder} tokens in object.path
    "query":  ["maxResults", "startAt"],   // property names for parameters[i] where .type === "query"
    "header": [],                           // property names for parameters[i] where .type === "header"
    "field":  []                            // property names that go into the request body (typically requestFields[])
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
      // see IS-Activity Rule 5
    },
    "manageProperties": []
  },
  "metadataVersion": 1
}
```

`staticValues` shape: emit flat dotted keys (`"fields.project.key": "OR"`). The FE may persist them as nested objects on save (`"fields": {"project": {"key": "OR"}}`); both round-trip through `ParameterMappingService`'s four-bucket iteration.

`staticValues` only holds values the LLM cannot override (`processType`, baked enum choices, baked reference IDs). Values the user provides at runtime belong in `inputSchema.properties` — either as plain types (free runtime) or with an `enum` populated from `execute list` (constrained runtime). `designTimeLookups` are NOT needed for enum-constrained runtime values; labeling only renders for baked values.

`mapping.path` lists every `{placeholder}` token in `object.path` by property name. Values come from `inputSchema.properties.<name>` at runtime. The CLI validates this client-side before POST.

`mapping.query` / `mapping.header` list parameter names the connector accepts; values flow from `inputSchema.properties.<name>` at runtime. Every `parameters[i]` belongs in `mapping[parameters[i].type]` by name — backend `ParameterMappingService.cs` iterates exactly these four buckets (`Query, Path, Header, Field`) for both `Mapping` and `StaticValues`.

`inputSchema` construction:

```
inputSchema.properties = (requestFields ∪ parameters where staticValues do NOT cover them)
For each parameters[i] (curated activities often have empty requestFields[] before cascade — parameters is the input source):
  - property name = parameters[i].name
  - title         = parameters[i].displayName ?? parameters[i].name
  - description   = parameters[i].description
  - type          = parameters[i].dataType   (string → "string", etc.)
  - required[]   += name when parameters[i].required === true
For each requestFields[j]: same mapping; type from field shape; honor `enum`/`reference` per resources.md.
Set additionalProperties: false.
```

`outputSchema` is a real JSON Schema built from `Data.responseFields`. Do not ship `{"type":"object","additionalProperties":true}` as a placeholder — extract `responseFields[]` from the Step 3b describe response and walk them the same way as `inputSchema.properties`. If the activity genuinely has no response body, pass `--output-schema "{}"`.

## IS-Activity Troubleshooting

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. The CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **404 at runtime** — `metadata.mapping.path` likely missing a `{token}` from `object.path`. Re-list every `{placeholder}` in `mapping.path` and retry. The CLI validates this before POST.
- **`Reason: CrossFolderConnection`** — connection lives in a folder different from the server's. Inspect `Data.candidates` for visible connections in the server's folder. Fix: pick a connection in the same folder via `--target-identifier <guid>`, or move the connection/server.
- **`"Operation 'X' not found. Available: <Y>"`** — curated activity exposes only `Y`. Re-run `describe` without `--operation` to read `Data.availableOperations[]`, then pick from that list.
- **Form renders raw scalar (e.g. `OR`, `3`, `bot`) instead of a labeled value** — `designTimeMetadata.designTimeLookups[<field>]` missing for that static reference value. Rebuild metadata with the lookup entry per IS-Activity Rule 5 + Step 3d and `mcp-tools update <tool-id>`.
- **`mcp-tools update` returns `ConflictingInput: Use exactly one of --file, --body, or scalar options.`** — pass `--metadata "<json>"` / `--input-schema "<json>"` / `--output-schema "<json>"` as scalars instead of `--file <path>`.
- **`Unexpected end of JSON input` on `--output-schema`** — empty string is rejected; pass `"{}"` when the activity has no responseFields.

## Cross-skill IS references (read on demand)

Two sections in the IS reference docs are load-bearing — read them via the Read tool when the workflow points at them, not from memory:

- `../../uipath-platform/references/integration-service/resources.md § Describe Response` + `§ Parent-Field-Driven Custom Fields` — describe response shape + cascade `-f` for api-type ObjectActions. Read before Workflow Step 3.
- `../../uipath-platform/references/integration-service/reference-resolution.md § Static Reference-Value Labeling` — `designTimeLookups` resolver + cascade-scoped edge cases. Read before Workflow Step 3d.
