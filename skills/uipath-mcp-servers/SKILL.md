---
name: uipath-mcp-servers
description: "Use when a user asks to create or manage a UiPath AgentHub MCP server, or to add an Integration Service connector activity (Jira, Slack, Outlook, Salesforce, Workday, ServiceNow, etc.) as a tool on such a server. Trigger phrases include 'add Jira/Slack/Outlook tool to my MCP server', 'create an MCP server with tools for X', 'I need an MCP tool that reads/lists/creates Y'. Distinct from FastMCP / Python MCP SDK work — `uipath-mcp-python` is a server-implementation SDK, NOT this skill. For low-code agent IS resource.json tools→uipath-agents. For raw IS CLI→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath AgentHub MCP Servers

Wrap an Integration Service connector activity as a tool on a UiPath AgentHub MCP server via `uip agenthub mcp-tools create-is-activity`. Author three stringified blobs (`metadata`, `inputSchema`, `outputSchema`) and supply the connection GUID + server folder.

## Hard Rules

1. **MCP server slug + external SaaS = AgentHub IS-Activity path.** Slugs like `inbox-mcp` / `support-mcp` / `team-helper` name AgentHub servers, not local repos. `uipath-mcp-python` (`@uipath/mcp`) is a server-implementation SDK — different task.

2. **Discover exhaustively before authoring.** Resolve connector key + objectName with `uip agenthub mcp-tools candidates --category is-activity`. Pull field metadata with `uip is resources describe`. For curated / api-type activities (Jira `curated_create_issue`, Salesforce SOQL, Dataservice V3), the first describe shows only cascade-root fields; re-describe with `-f <parent>=<value>` to surface the real schema (see Hard Rule 7). Build schemas only after the cascade is expanded.

3. **Stringify `metadata`, `inputSchema`, `outputSchema`** before passing to `--metadata` / `--input-schema` / `--output-schema`. SDK types them as `string | null`. Empty `--output-schema ""` is rejected with `Unexpected end of JSON input`; pass `"{}"` when the activity has no responseFields.

4. **Required scalars on create / update.** `--mcp <slug>`, `--name <tool name>`, `--description "<1-4000 chars>"`, `--folder-path <server folder>` (or `--folder-key <guid>`), `--target-identifier <connection-guid>`, `--metadata`, `--input-schema`, `--output-schema`. The server rejects empty `description` with HTTP 400 `Errors.Description: ["The Description field is required"]`; `--dry-run` does NOT lint this — supply description on every invocation.

5. **Connection: pass `--target-identifier <connection-guid>`.** Discover via `uip is connections list <connector-key> --output json`, pick a connection in the MCP server's folder, pass its GUID. The CLI derives `targetFolderKey` from the connection itself — no separate target-folder flag exists. Cross-folder surfaces as `Reason: CrossFolderConnection` with a `Data.candidates` array; resolve by moving the connection or picking one in the server's folder. See [connections.md](../uipath-platform/references/integration-service/connections.md) for the full selection algorithm (default folder, `--refresh`, BYOA, name matching, OAuth scopes).

6. **Folder flags follow `uipath-platform` parallel-pair convention.** `--folder-path <name>` resolves a display name via Orchestrator SDK; `--folder-key <guid>` takes a GUID. Personal workspace folders (`"<user>@<tenant>'s workspace"`) do NOT resolve via `--folder-path`; use `--folder-key <guid>`. Discover folder GUIDs once via `uip or folders list --output json`.

7. **Operation discovery + cascade rules.** Run `uip is resources describe` WITHOUT `--operation` first to enumerate `Data.availableOperations[].name`. Each entry also carries its own `path` and `method` (e.g., `GETBYID`, `POST`) — read them from `Data.availableOperations[i]`, NOT from a top-level `Data.object` which is `null` on curated activities. For api-type ObjectActions (Jira `curated_create_issue` Create, Salesforce SOQL `GenerateQuerySchema`, Dataservice V3 `FetchObjectMetadataTenant`), the base describe returns only cascade-root fields (e.g. `fields.project.key`, `fields.issuetype.id`). Populate parents with `-f field=value` to expand the full schema (which surfaces `fields.summary`, `fields.description`, etc.). **Pass `--action <name>` only when describe reports multiple matching actions; for `curated_create_issue` Create, omit `--action` — passing it causes `No api-type ObjectAction matched for fields [...]`.** See [resources.md § Describe Response](../uipath-platform/references/integration-service/resources.md#describe-response).

8. **Static reference values require `designTimeLookups`.** For every `staticValues.<bucket>.<field>` (any bucket — `field`, `query`, `header`, `path`) whose describe field has a `.reference` block, emit `designTimeMetadata.designTimeLookups[<field>] = "<displayName> - <value>"` so the edit-UI renders the label. Reference fields on `requestFields[]` AND on `parameters[]` qualify. Reference fields exposed in `inputSchema.properties` for the LLM to fill at runtime do NOT need lookups — labeling only applies to baked values. Resolver:
   1. List the reference object: `uip is resources execute list <connector> <leaf-object> --connection-id <id> --output json`. Leaf-object = `reference.objectName` for flat references, or the singularized last segment of `reference.path` for cascade-scoped ones.
   2. Match the row where `row[reference.lookupValue] === <baked-value>`. For connectors that mix global + parent-scoped rows (Jira issuetype), filter by `scope` first.
   3. Take `row[reference.lookupNames[0]]` as `displayName`.
   4. Write `"<displayName> - <baked-value>"` to `designTimeMetadata.designTimeLookups[<dotted-field>]`.

   See [reference-resolution.md § Static Reference-Value Labeling](../uipath-platform/references/integration-service/reference-resolution.md#static-reference-value-labeling) for cascade-scoped edge cases.

## Pre-flight (READ BEFORE THE WORKFLOW BLOCK)

Walk these checks before writing `--metadata`. Use AskUserQuestion (one option per choice + "Something else"). In autonomous mode where no human is available, still resolve every reference: pick the first/most-recently-used entry from `execute list`, log the choice in your output, and surface it back to the user ("I baked `project=OR` — change with `mcp-tools update`").

0. **Scoping (multi-tool builds).** Before authoring any tool, restate: server slug, folder, exact list of tools (one bullet each: `<connector> · <activity> · <op>`), and any baked statics. For ambiguous user asks ("Jira and Slack tools"), pick the canonical set and confirm or proceed-and-flag in autonomous mode.
   - **Folder pick.** If the user didn't name a folder, run `uip or folders list --output json` and choose: `Shared` (org-level default — preferred when teammates may share the server) OR the user's personal workspace (`<email>'s workspace`, type `Personal` — preferred for personal-use tools). Pass personal workspaces by `--folder-key <guid>` only (name lookup fails). Surface the choice in your output: `"server folder: Shared (default — change with --folder-path <name>)"`.
   - **Existing tool inventory.** Run `uip agenthub mcp-tools list --mcp <slug> --folder-path <name> --output json` BEFORE drafting. Catches duplicates ("another Create Issue tool — what's different?") and reveals naming conventions to match. Don't author a tool when one with the same name + connector + objectName already exists; surface the duplicate and ask whether to update vs add-new.
   - **Scope decisions when user names an activity but not the binding.** "Create a Jira issue tool" names the activity but not which project, issue type, or other reference values. For api-type connectors (Jira `curated_create_issue`, Salesforce SOQL, …) with required references at create-time, STOP and ask — even in autonomous mode. The cascade `-f` expansion (Hard Rule 7) depends on these values; guessing them propagates errors through every subsequent step.
1. **Connection** — `uip is connections list <connector> --output json` returns N>1 connections → ask "Which connection?" with one option per `<Name> in <Folder>` + "Something else".
2. **Activity disambiguation** — `candidates --connector <key>` returns ≥ 2 entries with overlapping descriptions (e.g. `send_message_to_channel` vs `send_message_to_user`, `curated_get_issue` Retrieve vs `search_issues_with_fields`) → ask. Tie-break for the GET case: name `Get …` / `Find …` without ID → `List`; `Get … by …` or path `{id}`/`{key}` → `Retrieve`. When in doubt, describe without `--operation`.
3. **Reference fields — discover, then present a 3-way choice (never default).** For every `requestFields[name].reference` OR `parameters[name].reference`:
   - Run `uip is resources execute list <connector> <referenced-object> --connection-id <id>` and capture the top N candidates.
   - Present three options (not two):
     - **(a) Bake one specific value** — `staticValues.<bucket>.<field> = <value>` + `designTimeMetadata.designTimeLookups[<field>] = "<displayName> - <value>"`. Pick when one value applies to every call (e.g., always file in project `OR`).
     - **(b) Constrain at runtime** — `inputSchema.properties.<field> = {type: string, enum: [<discovered values>]}`. The LLM picks from a known-valid set. No lookup needed (labeling only applies to baked values).
     - **(c) Free runtime** — `inputSchema.properties.<field> = {type: string}` with no enum. Pick when the set is large, changes frequently, or new values appear at runtime (e.g., issue IDs).
   - For **required** reference parameters, this question is forcing — do not skip even if the user said "LLM picks the channel". User phrasing like that often doesn't distinguish (b) from (c); confirm.
   - Autonomous-mode default: (b) constrained — safest middle ground when the discovered set is bounded (≤ 50 entries). Surface the choice and enum size in your output.
4. **Enum fields the user didn't specify** — if `enum` has ≥ 2 values, ask. With ≤ 1 value or an explicit user value, bake into `staticValues` silently.
5. **Cascade `-f` parents** — for api-type ObjectAction connectors, collect parent values from the user before running cascade (Hard Rule 7).
6. **Required scalar with no enum / no reference / no description** — STOP. Ask the user; do not bake a guess (e.g., Slack `UsersByEmail.By` is a required string with no enum — its valid values are connector-specific).

Asking once produces the right tool. Guessing produces wrong tools.

## Workflow

```bash
# Pre-step 0 — discover folders (once per machine)
uip or folders list --output json
# Read .[].Key + .[].DisplayName. Personal workspace folder requires --folder-key (not --folder-path).

# Pre-step 1 — confirm or create the MCP server
uip agenthub mcp list --folder-path <folder-name> --output json
# Read Data.items[].slug. --folder-path / --folder-key is required.

# If missing — `uipath` is a literal subcommand here, NOT the server name; slug goes in --name:
uip agenthub mcp create uipath --name <slug> --folder-path <folder-name> --output json
# Alternate payload modes: --file <path> or --body <json>. With no input, CLI prints:
#   Run `uip agenthub mcp create uipath --print-schema` to see the expected payload.

# Step 1 — find the connector key
uip agenthub mcp-tools candidates --category is-activity --name <vendor> --output json
# Read Data.items[].connectorKey (also .id). Vendor name ≠ connector key (e.g. Slack → uipath-salesforce-slack).

# Step 2 — find the activity (objectName, methodName, operation)
uip agenthub mcp-tools candidates --category is-activity --connector <key> --output json
# Read Data.items[].{objectName, methodName, displayName}. Multi-candidate → Pre-flight #2.

# Step 3a — enumerate operations
#   PREREQUISITE: Read the section first via the Read tool (don't skim from memory):
#     Read uipath-platform/references/integration-service/resources.md (§ Describe Response)
uip is resources describe <key> <objectName> --connection-id <id> --output json
# Read Data.availableOperations[].{name, path, method}. Data.object is null on curated activities — use availableOperations entries.

# Step 3b — pull field metadata + cascade if api-type (READ FIRST: resources.md § Parent-Field-Driven Custom Fields)
uip is resources describe <key> <objectName> --connection-id <id> --operation <name-from-3a> --output json
# Read Data.requestFields[] (body), Data.parameters[] (query/path/header), Data.responseFields[] (output).
# For api-type ObjectActions (curated_create_issue, GenerateQuerySchema, FetchObjectMetadataTenant): rerun with
#   -f <parent>=<value> ... --action <name>   to expand the full schema (Hard Rule 7).
# If requestFields looks short for the operation (e.g. Create Issue without summary), the connector is curated —
# the cascade is required, not optional.

# Step 3c — find the connection in the right folder
uip is connections list <connector-key> --output json
# Read Data.items[].{id, name, folder.key}. Pick the connection whose folder.key matches the MCP server's folder.
# Personal workspace folder: see Hard Rule 6.

# Step 3d — resolve labels for every static reference value (Hard Rule 8 § Resolver)
#   PREREQUISITE: Read the section first via the Read tool (don't skim from memory):
#     Read uipath-platform/references/integration-service/reference-resolution.md (§ Static Reference-Value Labeling)
# Run the 4-step resolver per baked staticValues entry.

# Step 3e — preview the POST body
uip agenthub mcp-tools create-is-activity ... --description "<one-line>" --dry-run --output json
# Inspect Data.resolved.{metadata,inputSchema,outputSchema}. --dry-run skips some server-side validation
# (description, designTimeLookups), so it can pass while the real POST fails.

# Step 4 — create the tool
uip agenthub mcp-tools create-is-activity \
  --mcp <slug> \
  --name "<tool name>" \
  --description "<one-line, required, 1-4000 chars>" \
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

Delete a tool when it's no longer needed:

```bash
uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --output json
```

Delete an MCP server (lookup by slug, not by GUID):

```bash
uip agenthub mcp delete <slug> --folder-key <guid> --output json
```

Need the body shape for `--file`?

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
      // see Hard Rule 8
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

## Troubleshooting

- **HTTP 400 `Errors.Description: ["The Description field is required"]`** — `--description` flag omitted or empty. Pass `--description "<one-line>"` on every create/update. Note: `--dry-run` does not catch this.
- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. The CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **404 at runtime** — `metadata.mapping.path` likely missing a `{token}` from `object.path`. Re-list every `{placeholder}` in `mapping.path` and retry. The CLI validates this before POST.
- **`Reason: CrossFolderConnection`** — connection lives in a folder different from the server's. Inspect `Data.candidates` for visible connections in the server's folder. Fix: pick a connection in the same folder via `--target-identifier <guid>`, or move the connection/server.
- **`"Operation 'X' not found. Available: <Y>"`** — curated activity exposes only `Y`. Re-run `describe` without `--operation` to read `Data.availableOperations[]`, then pick from that list.
- **`InvalidFolderKey: "--folder-key requires a GUID; use --folder-path for folder names"`** — switch to `--folder-path <name>`.
- **`No folder named '<personal workspace name>' was found. Did you mean: Shared?`** — personal workspaces are unresolvable by name; pass `--folder-key <guid>` instead.
- **`ConflictingInput: "Pass either --folder-path or --folder-key, not both."`** — drop one. See Hard Rule 6.
- **Form renders raw scalar (e.g. `OR`, `3`, `bot`) instead of a labeled value** — `designTimeMetadata.designTimeLookups[<field>]` missing for that static reference value. Rebuild metadata with the lookup entry per Hard Rule 8 + Step 3d and `mcp-tools update <tool-id>`.
- **`mcp-tools update` returns `ConflictingInput: Use exactly one of --file, --body, or scalar options.`** — pass `--metadata "<json>"` / `--input-schema "<json>"` / `--output-schema "<json>"` as scalars instead of `--file <path>`.
- **`Unexpected end of JSON input` on `--output-schema`** — empty string is rejected; pass `"{}"` when the activity has no responseFields.
- **`mcp delete <guid>` returns 404** — `mcp delete` looks up by slug, not by id. Pass the slug.

## Reference Navigation

- [agent-workflow.md](../uipath-platform/references/integration-service/agent-workflow.md) — IS discovery (connector → connection → ping → describe). Skim before authoring the first tool on a new connector or stale connection.
- [connections.md](../uipath-platform/references/integration-service/connections.md) — connection selection algorithm, default folder, `--refresh`, BYOA, OAuth scopes.
- [resources.md](../uipath-platform/references/integration-service/resources.md) — `describe` response shape + cascade `-f field=value` for api-type ObjectActions (canonical for Step 3 — read before the bash block).
- [reference-resolution.md](../uipath-platform/references/integration-service/reference-resolution.md) — resolving reference / search-reference / dependent fields + static-value labeling.

## Appendix — Worked example: Jira Create Issue, zero to created

This walks Steps 1–5 against a real tenant. **Adjust every project key, issue type id, connection GUID, and folder key to the user's environment — do NOT copy the example values as defaults.** The values below are illustrative; picking `OR` / `3` without asking is the most common drift on this activity.

```bash
# 0. Folders
uip or folders list --output json
# → Shared = 2eda4f27-...; personal workspace = 1222144b-...

# 1. Connector
uip agenthub mcp-tools candidates --category is-activity --name jira --output json
# → uipath-atlassian-jira (real) + uipath-mock-jira (mock — skip)

# 2. Activity
uip agenthub mcp-tools candidates --category is-activity --connector uipath-atlassian-jira --output json
# → curated_create_issue (curated, "Create Issue")

# 3a. Operations
uip is resources describe uipath-atlassian-jira curated_create_issue --connection-id 9c6edfbd-... --output json
# → availableOperations[].name = ["Create"]; .path = "/curated_create_issue"; .method = "POST"

# 3b. Base describe (only cascade roots)
uip is resources describe uipath-atlassian-jira curated_create_issue --connection-id 9c6edfbd-... --operation Create --output json
# → requestFields = [fields.project.key (ref→project), fields.issuetype.id (ref→project path-scoped)]

# 3b'. Cascade (the everyday case for curated activities — REQUIRED)
# Replace OR / 3 with the project key and issuetype id the user named. The example values are
# NOT defaults — picking them silently is the most common drift on this activity.
uip is resources describe uipath-atlassian-jira curated_create_issue --connection-id 9c6edfbd-... \
  --operation Create \
  -f fields.project.key=<USER_PROJECT_KEY> -f fields.issuetype.id=<USER_ISSUETYPE_ID> --output json
# Note: do NOT pass --action Create — the matcher rejects it for curated_create_issue. The cascade
# resolves from the -f field values alone.
# → requestFields now includes fields.summary, fields.description, plus project-specific custom fields

# 3c. Connection
uip is connections list uipath-atlassian-jira --folder-key 1222144b-... --output json
# → id=9c6edfbd-...

# 3d. Resolve labels (Hard Rule 8 resolver)
uip is resources execute list uipath-atlassian-jira project --connection-id 9c6edfbd-... --output json
# → row where key=OR has name=Orchestrator → "Orchestrator - OR"
uip is resources execute list uipath-atlassian-jira issuetype --connection-id 9c6edfbd-... --output json
# → row where id=3 has name=Task, scope=null (global) → "Task - 3"

# 3e. Dry-run (note --description is required even for dry-run sanity)
uip agenthub mcp-tools create-is-activity --mcp test-mcp-skill --name "Create Issue" \
  --description "Create a Jira issue in project OR with type Task. LLM provides summary and optional description." \
  --folder-key 2eda4f27-... --target-identifier 9c6edfbd-... \
  --metadata "$(jq -c . metadata.json)" --input-schema "$(jq -c . input-schema.json)" --output-schema "$(jq -c . output-schema.json)" \
  --dry-run --output json
# → Result: Success, Code: DryRun

# 4. Create
# (same as 3e without --dry-run)

# 5. Verify
uip agenthub mcp-tools list --mcp test-mcp-skill --folder-path Shared --output json
# → new tool present with id, designTimeLookups populated, mapping.field includes fields.summary/fields.description
```
