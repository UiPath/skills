# IS-Activity Tool Authoring

Wrap an Integration Service connector activity as an MCP tool via `uip agenthub mcp-tools create-is-activity`.

The CLI verb is `uip is resources execute` (with `execute list`, `execute create`, etc.). Platform IS references show `uip is resources run list` in some examples — that wording is stale; use `execute`.

## Platform IS references — required reads tied to actions

These files in `../../uipath-platform/references/integration-service/` carry the load-bearing IS concepts. Each is small. Do NOT read all four upfront. Instead, before performing each of the actions below, read the named section first — even if you feel you know the format. The blind spots in IS metadata authoring are unknown-unknowns, so the trigger is the action you are about to take, not your sense of certainty.

| Before this action | First read |
|---|---|
| Calling `uip is connections list <key>` for the first time in this task | `connections.md` §`Folder Scoping` (so you pass `--folder <name-or-key>`) |
| Running `is resources describe ... -f <parent>=<value>` (any cascade re-run) | `resources.md` §`Parent-Field-Driven Custom Fields` (exact `-f` shape, `--operation` requirement, `--action` rule, merge semantics) |
| Writing a `staticValues.<bucket>.<field>` entry where the describe field has a `.reference` block | `reference-resolution.md` §`Static Reference-Value Labeling` (exact `designTimeLookups` format + cascade-scope edge cases) |
| Writing an `inputSchema.properties.<field>` entry where the describe field has a `.reference` block with `path` containing `{otherField}` | `reference-resolution.md` §`Field Dependency Chains` (resolve parent first; check whether the field interacts with siblings) |
| Writing an `inputSchema.properties.<field>` entry where the describe field has a `.reference` block with `filterPattern` containing `{filter}` | `reference-resolution.md` §`Search References` (free-runtime needs the user's input to drive the search) |
| Resolving a reference value where `execute list` returns rows with `scope: null` AND `scope.type: "PROJECT"` | `reference-resolution.md` §`Scope Filtering` |
| Diagnosing a `describe` server-side failure | `resources.md` §`Describe Failures` |
| Final gate before `mcp-tools create-is-activity --dry-run` | `reference-resolution.md` §`Validate Required Fields Before Executing` |

Section pointers later in this file (e.g. `resources.md §Parent-Field-Driven Custom Fields`) refer to the files above.

**Do not author IS metadata from memory.** A `designTimeLookups` entry that "looks right from the Critical Rule" still gets the wrong shape when the connector's `lookupValue` differs from what you remember. A `-f` cascade re-run from memory still hits `Missing required option '--operation'`. A `reference` field treated as a plain string still mis-handles dependency chains. The platform sections above are the only source of truth — read them at the action-trigger above even if confident.

## When to ask the user

Ask only for values whose answer changes what `uip is resources describe` returns — the cascade-`-f` parents on api-type ObjectActions. Everything else is a runtime input.

Detection:

1. Run `uip is resources describe <key> <objectName> --connection-id <id> --operation <op> --output json`.
2. Look at `Data.requestFields[]`. If it is empty, or contains only fields whose names look like parent selectors (dotted identifiers ending in `.key`, `.id`, `.name`, or a single body-token like `query` / `tenantEntityName`) — the connector is curated and the operation runs a cascade.
3. Read `Data.connectorMethodInfo.design.actions[]` (or top-level `Data.objectActions[]` for older shapes) to see what `-f` parents each registered action requires.
4. Ask the user for those values, then re-run describe with `-f <parent>=<value>` per `resources.md §Parent-Field-Driven Custom Fields` to expand the real `requestFields`.

Heuristic: if `requestFields` for a Create-type operation has fewer than 3 fields, or is missing the obvious body field (no `summary`-equivalent for an issue, no body for a message, no name for a record), suspect cascade. Verify via step 3.

If `requestFields` returns a plausible, full body schema after base describe — no cascade is needed. Proceed without asking.

### How to ask — pick the mechanism by candidate-set size

- **Bounded set (2-4 likely candidates from `execute list` or from the user's earlier hint):** `AskUserQuestion`. Tool requires 2-4 options; do NOT add "Other" yourself — it is appended automatically. Single-option asks fail with `InputValidationError: array must have >=2 items`.
- **Unbounded set (`execute list` returned dozens or hundreds — Jira projects, Salesforce custom objects, large reference tables):** do NOT enumerate in `AskUserQuestion`. Ask in a plain text response. Show the user the top 5–10 most likely candidates by display name (recent / popular / closest match to any hint they gave) AND name the format you need (`"<project key> + <issue type>"`, `"<SObject API name>"`, …) so they can type the answer. Do not invent a filter and hope it narrows the set — `JMESPath` filters with guessed names usually return empty.

### What if the user defers

Cascade roots have NO autonomous fallback. If the user picks "Other" / "Type the values" / dismisses / says "you decide" — re-ask in plain text. Do NOT proceed with:

- **Free runtime** as a substitute — running `describe` without the cascade values returns a stub schema; `inputSchema.properties` will be missing the connector's actual body fields. The tool will pass `--dry-run` and fail at runtime.
- **A guessed default** ("`OR` is probably a real project") — guessing here propagates wrong `staticValues` and wrong `designTimeLookups`.
- **Skipping the tool** silently — surface the block to the user instead: "I need a project key + issue type to author this tool — without them the schema will be empty."

Re-asking is cheap. Authoring a broken tool and discovering it at consumer-call time is expensive.

## What goes into `inputSchema.properties` (runtime inputs)

Every required field that is NOT cascade-driving belongs in `inputSchema.properties`. Do not bake by default and do not ask at authoring time. The consuming LLM picks per call using the field's `description`.

Pre-flight #3's 3-way choice:

- **(a) Bake** + `designTimeLookups` — when the user named one specific value that applies to every call.
- **(b) Constrained runtime** with `enum` — when the set is bounded (≤ 20-50), stable, and known at authoring time.
- **(c) Free runtime** — default. The field's `description` carries the prompt the consuming LLM will read.

A good runtime `description` includes:

- A short noun phrase naming the field.
- The format — concrete shape (e.g. `"ISO 8601 timestamp"`, `"3-letter ISO currency code"`, `"IANA timezone like 'UTC' or 'Europe/Bucharest'"`).
- Default behavior on omission — if the connector handles omission gracefully, say so (`"Omit to use the user's primary <thing>"`); if it doesn't, name a safe value (`"Use 'UTC' when the caller has no preference"`).
- Constraints — required co-fields, valid ranges, allowed substring patterns.

If the field has a `.reference` block in the describe response, also run `uip is resources execute list <connector> <reference.objectName> --connection-id <id>` and either populate `enum` from the result (option b) or mention representative values in the `description` (option c).

## IS-Activity-Specific Critical Rules

These extend the generic Critical Rules in SKILL.md.

1. **Discover before authoring.** `uip agenthub mcp-tools candidates --category is-activity` resolves connector + activity. `uip is resources describe` pulls field metadata. Never compose `metadata` / `inputSchema` / `outputSchema` from memory or examples — every connector + operation has its own shape.

2. **Stringify `metadata` / `inputSchema` / `outputSchema`** before passing to `--metadata` / `--input-schema` / `--output-schema`. SDK types them as `string | null`. Empty `--output-schema ""` is rejected with `Unexpected end of JSON input` — pass `"{}"` when the activity has no `responseFields`.

3. **Connection picked per server's folder.** Use `uip is connections list <connector-key> --folder <name-or-key> --output json` (NOT the unfiltered form — connections are folder-scoped, see platform `connections.md` §`Folder Scoping`). Pass `--target-identifier <connection-guid>`. The CLI derives `targetFolderKey` from the connection — do not pass `--target-folder-key` for IS-activity tools. Cross-folder mismatch surfaces as `Reason: CrossFolderConnection` with `Data.candidates`; pick from candidates.

4. **Cascade for api-type ObjectActions.** Run `uip is resources describe <key> <objectName> --connection-id <id> --operation <op>` first. If the connector is curated and `requestFields` looks short for the operation, re-run with `-f <parent>=<value>` per `resources.md` §`Parent-Field-Driven Custom Fields`. Examples that REQUIRE the cascade: Jira `curated_create_issue` (Create), Salesforce SOQL `query_records`, Dataservice V3. **Omit `--action` for Jira `curated_create_issue` Create** — passing it triggers `No api-type ObjectAction matched for fields [...]`. Pass `--action <name>` only when describe reports multiple matching actions for the supplied `-f` set.

5. **Static reference values need `designTimeLookups`.** Every `staticValues.<bucket>.<field>` (any bucket — `field`, `query`, `header`, `path`) whose describe field has a `.reference` block MUST also emit `designTimeMetadata.designTimeLookups[<field>] = "<displayName> - <value>"`. Applies to `requestFields[]` AND `parameters[]`. Runtime fields in `inputSchema.properties` do NOT need lookups — labeling only renders for baked values. Resolver per `reference-resolution.md` §`Static Reference-Value Labeling`.

6. **Ask, do not guess, when discovery is conditional.** If a value drives downstream discovery — cascade `-f` parents, a search-reference `filterPattern`, a dependency-chain parent (Rule 7 in `reference-resolution.md` §`Field Dependency Chains`), or a required reference with no user-supplied hint — STOP and ask. Even in autonomous mode. **No autonomous fallback exists for these values.** If the user defers (clicks "Other" / "Type the values" / does not type / says "you decide"), re-ask in plain text; do NOT fall back to free runtime, a guessed default, or skipping the tool. See "How to ask" + "What if the user defers" above.

7. **Do not filter unbounded `execute list` results with guessed names.** When `execute list` returns more rows than the user can scan (Jira projects, Salesforce custom objects, large reference tables), do NOT compose a `JMESPath --output-filter` against a list of names you invented or pattern-matched. If a real name doesn't match, the filter returns `[]` and you have no signal whether the project / object exists. Either: (a) show the top N rows by a real-data attribute (most-recently-updated, most-issues, alphabetical, etc. — whatever the connector exposes) and ask the user, or (b) ask the user for the exact key/name and skip filtering.

## Pre-flight

Walk before drafting `--metadata`. Use AskUserQuestion only for bounded ≤4-option choices (see "How to ask" above) — for unbounded sets like Jira projects, ask in plain text. The autonomous defaults below apply ONLY to choices with no downstream-discovery effect — never to cascade roots or required references (Rule 6).

0. **Scope (multi-tool builds).** Restate: server slug, folder, exact tool list (one bullet per `<connector> · <activity> · <op>`), baked statics. Ambiguous asks ("Jira and Slack tools") → pick the canonical set and confirm.
   - **Folder pick.** If the user didn't name a folder, run `uip or folders list --output json` and choose `Shared` (org-default) OR `<email>'s workspace` (personal). Personal workspace requires `--folder-key <guid>`. Surface: `"server folder: <name> — change with --folder-path"`.
   - **Existing tool inventory.** Run `uip agenthub mcp-tools list --mcp <slug> --folder-path <name> --output json` before drafting. Same name + connector + objectName already exists → ask update vs add-new.
   - **Activity named, binding not.** "Create a Jira issue tool" names the activity, not project / issue-type / etc. STOP and ask for cascade-parent values (Rule 6).
1. **Connection.** `uip is connections list <connector> --folder <folder-name-or-key> --output json`. Refer to platform `connections.md` §`Selecting a Connection` for the presentation rule (name, owner, folder — never UUIDs; recommend default, always confirm).
   - N>1 enabled connections → ASK with one option per `<Name> by <Owner> in <Folder>` + "Something else".
   - Exactly one → still confirm per `connections.md`: "Use **<Name>** by <Owner> in <Folder>?"
   - Zero → retry with `--refresh`; if still empty, surface a create-connection hint and STOP.
2. **Activity disambiguation.** `candidates --category is-activity --connector <key>` returns ≥ 2 entries with overlapping descriptions (`send_message_to_channel` vs `send_message_to_user`, `curated_get_issue` Retrieve vs `search_issues_with_fields` List) → ASK. GET tie-break: `Get …` / `Find …` without ID → `List`; `Get … by …` or path `{id}` / `{key}` → `Retrieve`. When uncertain, describe without `--operation` and present `Data.availableOperations[]` to the user.
3. **Reference fields — 3-way choice per field. ASK by default.** For every `requestFields[name].reference` OR `parameters[name].reference` (per `reference-resolution.md` §`Reference Fields`):
   - Run `uip is resources execute list <connector> <reference.objectName> --connection-id <id> --output json` and capture top candidates. Honor `filterPattern` (search reference) and dependency `{parent}` substitution (`reference-resolution.md` §`Search References` + §`Field Dependency Chains`).
   - Present three options:
     - **(a) Bake one value** — `staticValues.<bucket>.<field> = <value>` + `designTimeLookups[<field>] = "<displayName> - <value>"`. Pick when the same value applies to every call.
     - **(b) Constrain at runtime** — `inputSchema.properties.<field> = {type: string, enum: [<discovered values>]}`. LLM picks from a known-valid set. No lookup needed.
     - **(c) Free runtime** — `inputSchema.properties.<field> = {type: string}`, no enum. Pick when the set is large / volatile / unknowable at design time (issue IDs, message text, search inputs).
   - **Cascade roots and search references with no user-supplied filter: HARD ASK (Rule 6 / STOP CHECK).** No autonomous default — do not "pick first" or "pick most-recently-used". Skipping the ask here changes what `describe` returns.
   - **Non-cascade required reference fields** (calendar, folder, send_as, channel, recipient, timezone, etc.): autonomous-mode default = **free runtime (c)** with a description written for the consuming LLM. Use bounded (b) only when the set is genuinely small (≤ 20) and stable. Bake (a) only when the user named one specific value.
   - **Non-cascade bounded enums** (≤ 50, stable): autonomous default = (b). Surface the choice + enum size.
4. **Enum fields the user didn't specify.** `enum.length ≥ 2` AND the field is required AND drives no downstream discovery → ASK. Otherwise (no downstream effect, or user gave an explicit value) → bake into `staticValues` silently.
5. **Scope filtering on cascade-root reference lookups.** `reference-resolution.md` §`Scope Filtering`. Many references return both `scope: null` and `scope.type: "PROJECT"` rows with the same display name (concrete: Jira issuetype "Task" id=3 global vs id=10659 project-scoped). When baking a cascade-root value, filter by `scope == null OR scope.<parentType>.<id> == <baked-parent-value>`. Note the Jira-issuetype caveat in §`Cascade-scoped references` (Jira flattens scope — verify candidate id via cascade-describe round-trip).
6. **Required scalar with no enum / no reference / no description.** STOP. Ask. Do not bake a guess (e.g., Slack `UsersByEmail.By` is a required string with no enum — valid values are connector-specific).

Asking once produces the right tool. Guessing produces wrong tools.

## Workflow

```bash
# Pre-step 0 — discover folders (once per machine)
uip or folders list --output json
# Read .[].Key + .[].DisplayName. Personal workspace folder requires --folder-key (not --folder-path).

# Pre-step 1 — confirm or create the MCP server
uip agenthub mcp list --folder-path <folder-name> --output-filter "Data.items[].slug" --output json

# If missing — `uipath` is the server-type literal (not the server name). Slug regex ^[a-z0-9-]+$, length 3-50:
uip agenthub mcp create uipath --name "<display>" --slug <slug> --folder-path <folder-name> --output json
# Alternate payload: --file <path> or --body <json>. Schema via `uip agenthub mcp create uipath --print-schema`.

# Step 1 — find the connector key
uip agenthub mcp-tools candidates --category is-activity --name <vendor> --output json
# Read Data.items[].connectorKey (also .id). Vendor name ≠ connector key (e.g. Slack → uipath-salesforce-slack).

# Step 2 — find the activity (objectName, methodName, operation)
uip agenthub mcp-tools candidates --category is-activity --connector <key> --output json
# Read Data.items[].{objectName, methodName, displayName}. Multi-candidate → Pre-flight #2.

# Step 3a — enumerate operations
uip is resources describe <key> <objectName> --connection-id <id> --output json
# Read Data.availableOperations[].{name, path, method}. Data.object is null on curated activities — use availableOperations entries.
# Describe error (server-side metadata gap) → read resources.md §Describe Failures (skip describe, infer fields, attempt execute).

# Step 3b — field metadata (base describe)
uip is resources describe <key> <objectName> --connection-id <id> --operation <name-from-3a> --output json
# --operation is required here. The -f cascade in Step 3c also requires --operation (CLI rule).
# Read Data.requestFields[] (body), Data.parameters[] (path/query/header), Data.responseFields[] (output).
#
# If requestFields looks short for the operation (e.g. Create Issue without summary), connector is curated — proceed to 3c.
# If requestFields looks complete — skip 3c.
# For api-type ObjectActions (curated_create_issue, GenerateQuerySchema, FetchObjectMetadataTenant):
#   1. Collect parent values FROM THE USER (Rule 6 — ASK; do not guess).
#   2. Re-run with -f <parent>=<value> (repeatable). Omit --action for curated_create_issue Create; pass --action only when describe reports multiple matches.
#   3. The cascade response replaces/augments requestFields per remapConfiguration.input.

# Step 3c — pick a connection in the server's folder  [REQUIRED READ: connections.md §Selecting a Connection + §Folder Scoping]
uip is connections list <connector-key> --folder <server-folder-name-or-key> --output json
# Default form (no --folder) silently filters to the current folder context and may return empty even when connections exist.
# Read Data.items[].{id, name, owner, folder, state, isDefault}. Present per connections.md rules; ASK to confirm even if one match.

# Step 3d — resolve labels for every static reference value  [REQUIRED READ: reference-resolution.md §Static Reference-Value Labeling]
uip is resources execute list <connector> <reference.objectName> --connection-id <id> --output json
# Match baked value against reference.lookupValue → take reference.lookupNames[0] as displayName.
# For cascade-scoped references (path contains {parent.field}) — drop the trailing 's' from the path's leaf segment, list, filter by scope (§Cascade-scoped references). Jira-issuetype caveat applies.
# Persist as designTimeMetadata.designTimeLookups[<dotted-field>] = "<displayName> - <baked-value>".

# Step 3e — preview the POST body
uip agenthub mcp-tools create-is-activity ... --dry-run --output json
# Inspect Data.resolved.{metadata,inputSchema,outputSchema}.
# --dry-run skips some server-side validation (description length, designTimeLookups completeness); it can pass while the real POST fails.

# Step 4 — create the tool
uip agenthub mcp-tools create-is-activity \
  --mcp <slug> \
  --name "<tool name>" \
  --description "<1-4000 chars; surfaces in the AgentHub UI>" \
  --folder-path "<server folder>" \
  --target-identifier <connection-guid> \
  --metadata     "$(jq -c . metadata.json)" \
  --input-schema "$(jq -c . input-schema.json)" \
  --output-schema "$(jq -c . output-schema.json)" \
  --output json
# Read Data.id (the created tool ID).

# Step 5 — verify (do NOT claim done before this passes)
uip agenthub mcp-tools list --mcp <slug> --folder-path <folder-name> --output json
# Confirm new tool's id, name, description, mcpName present.
# High-value tools: smoke-test via `uip is resources execute <verb>` with realistic inputs against a sandbox.
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

Pass `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`). Pass `--output-schema "{}"` when the underlying activity has no `responseFields`.

Delete a tool:

```bash
uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --output json
```

Skeleton for `--file`:

```bash
uip agenthub mcp-tools template is-activity --output json
```

Multi-tool builds ("server with tools for X and Y"): walk Pre-flight + Steps 1–5 per tool. Re-walk Pre-flight 1–6 before each tool — by tool 3 you are working from a mental model of tool 1, which drifts.

## `ActivityMetadata` (the object to stringify into `--metadata`)

```jsonc
{
  "connector":   { "key": "<connector-key>" },              // from Step 1
  "object": {
    "path":        "<from Data.availableOperations[chosen].path — e.g. /issue/{issueKey}/comment/{commentId}>",
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
      // see Critical Rule 5 + reference-resolution.md §Static Reference-Value Labeling
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
For each requestFields[j]: same mapping; type from field shape; honor `enum`/`reference` per resources.md §Key field properties.
Set additionalProperties: false.
```

`outputSchema` is a real JSON Schema built from `Data.responseFields`. Do not ship `{"type":"object","additionalProperties":true}` as a placeholder — extract `responseFields[]` from the Step 3b describe response and walk them the same way as `inputSchema.properties`. If the activity genuinely has no response body, pass `--output-schema "{}"`.

## IS-Activity Troubleshooting

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **404 at runtime** — `metadata.mapping.path` likely missing a `{token}` from `object.path`. List every `{placeholder}` in `mapping.path` and retry. CLI validates this client-side before POST.
- **`Reason: CrossFolderConnection`** — connection is in a different folder than the server. Inspect `Data.candidates` for connections visible in the server's folder. Fix: pick a candidate via `--target-identifier <guid>`, or move the connection / server.
- **`"Operation 'X' not found. Available: <Y>"`** — curated activity exposes only `Y`. Re-run `describe` without `--operation` and pick from `Data.availableOperations[]`.
- **`No api-type ObjectAction matched for fields [...]`** — cascade discovery failed because (a) the `-f` set doesn't match any registered action, or (b) `--action` was passed when it should have been omitted (Jira `curated_create_issue` Create). Drop `--action` first; if still failing, inspect `connectorMethodInfo.design.actions[]` / top-level `objectActions[]` in the base describe response to see required `-f` shapes.
- **Form renders raw scalar (`OR`, `3`, `bot`) instead of a labeled value** — `designTimeLookups[<field>]` missing. Rebuild per Rule 5 + Step 3d, then `mcp-tools update <tool-id>`.
- **`mcp-tools update` → `ConflictingInput: Use exactly one of --file, --body, or scalar options.`** — pass `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`).
- **`Unexpected end of JSON input` on `--output-schema`** — empty string rejected; pass `"{}"` for no-response-body activities.
- **`uip is connections list <key>` returns empty in one folder but a connection exists elsewhere** — connections are folder-scoped (platform `connections.md` §`Folder Scoping`). Re-run with `--folder <name-or-key>` set to the server's folder before concluding "no connection exists".
- **403 Forbidden at runtime** — likely scope mismatch on the connection. Platform `connections.md` §`Scope-Related Errors`: re-authorize via `uip is connections edit <id>` with broader scopes.

For generic AgentHub-MCP issues (slug regex, folder context, refresh-tools async/sync, `mcp delete` lookup), see SKILL.md §Troubleshooting.
