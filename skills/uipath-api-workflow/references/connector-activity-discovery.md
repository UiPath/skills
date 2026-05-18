# Connector Activity Discovery

How to author an Integration Service connector activity (HTTP Request, Gmail, Outlook, GitHub, Slack, Salesforce, etc.) so it **renders cleanly in StudioWeb's designer** AND **runs from the CLI**. The flow uses `uip api-workflow registry` to resolve a keyword to an activity-type GUID, then build a ready-to-paste activity object with the right shape — `metadata.configuration` (with `unifiedTypesCompatible: true` + `savedJitInputFieldId` so StudioWeb renders the unified activity card), full endpoint path, multipart declarations, camelCase export bucket — all derived from StudioWeb's TypeCache + Integration Service Elements metadata.

> The `registry` subcommand ships with `@uipath/cli`'s api-workflow tool. No separate install. Both calls require `uip login` (TypeCache + IS Elements are tenant-scoped, served live).

## Why this is needed

`uip is activities list <connector-key>` returns 7 fields per operation: `Name`, `DisplayName`, `Description`, `ObjectName`, `MethodName`, `Operation`, `IsCurated`. Enough to *call* the operation at runtime, but missing two things StudioWeb's designer requires to render the activity card:

- **`uiPathActivityTypeId`** — the GUID identifying which activity card to render
- **`metadata.configuration`** — a JSON blob describing the activity's essential parameters (the "InstanceParameters")

Without both, the designer renders the activity as a "block / forbidden" card and StudioWeb cloud runs fail (the runtime path is mediated by the designer). With both — and the right field-shape rules below — the activity card renders correctly and the workflow roundtrips cleanly.

## The discovery flow

```
1. uip api-workflow registry resolve "<keyword>" --output json     → candidate GUIDs
2. (IntSvc kind only) uip is connections list <connector-key>           → connection UUID
   uip is connections ping <uuid>                                  → REQUIRED — verify it works
3. uip api-workflow registry stub <activity-type-id> \             → ready-to-paste activity
     [--connection-id <uuid>] [--inputs '<json>'] --output json
   uip is resources describe <connector-key> <object-name> \       → REQUIRED cross-check —
     --operation <op> --connection-id <uuid> --output json           stub omits required fields
4. Drop the Activity payload into the root sequence, fill any missing required fields, replace placeholders.
5. (Solutions-mode / IntSvc kind only) Write the Solution connection-resource file at
   Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json.
6. Validate.
```

What the `stub` command does internally (you don't need to call any of these by hand):

- Re-fetches the TypeCache entry → parses `Config` (`connectorKey`, `objectName`, `httpMethod`, `activityType`, `version`)
- Calls IS Elements `getObjectMetadata` (or `getInstanceObjectMetadata` if `--connection-id` is given) → extracts full path, request fields, response fields, parameters, multipart signal
- Picks Http kind vs IntSvc kind by `connectorKey === "uipath-uipath-http"`
- Builds `metadata.configuration` (essential-only) with the full path
- Derives the camelCase export-bucket key from `objectName`
- Declares `multipartParameters` when the operation requires multipart
- Stuffs `--inputs` values into the right `bodyParameters` / `queryParameters` / `pathParameters` / `multipartParameters` slots based on each field's `location` in the IS schema

### Step 1 — Resolve the activity by keyword

```bash
uip api-workflow registry resolve "<keyword>" --output json
```

Substring-matches `keyword` against `displayName`, `connectorKey`, `objectName`, and `fullName` of every activity in the Api-compatible TypeCache (`projectType=Api`). Returns up to 20 candidates by default; raise with `--limit <n>`.

```json
{
  "Result": "Success",
  "Code": "ActivityResolveSuccess",
  "Data": {
    "Keyword": "newest email",
    "ResultCount": 1,
    "Matches": [
      {
        "uiPathActivityTypeId": "b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a",
        "displayName": "Get Newest Email",
        "description": "Retrieves the newest email from a folder.",
        "connectorKey": "uipath-microsoft-outlook365",
        "objectName": "getNewestEmail",
        "httpMethod": "GET",
        "activityType": "Curated"
      }
    ]
  }
}
```

If multiple connectors offer the same operation (e.g. Gmail "Send Email" vs Outlook "Send Mail"), narrow by connector name instead of operation name: `resolve "outlook send"` vs `resolve "gmail send"`.

If `ResultCount` is 0, try a different keyword. Connector activity names can differ from the vendor's marketing name — Outlook calls it "Get Newest Email", Gmail calls it "Get Latest Message".

### Step 2 — Verify a vendor connection (IntSvc kind only)

Skip this step if `connectorKey === "uipath-uipath-http"` — the HTTP connector uses `connectionId: "ImplicitConnection"` and needs no real connection.

```bash
uip is connections list <connector-key> --output json
```

Returns connections for that connector. Pick the `Id` of an `Enabled` connection (prefer `IsDefault: "Yes"` if multiple). If none exist, the user must create one in Integration Service before authoring can complete.

```bash
uip is connections ping <connection-uuid> --output json
```

This is **not optional**. A connection that exists in the listing can still be in a broken state (expired upstream OAuth token, never authorized, deleted upstream element, wrong tenant) and produce `401 "Invalid Organization or User secret, or invalid Element token provided"` at run time. Pinging up front catches the problem before the workflow is authored.

- `Code: "ConnectionPing"` (success) → connection is healthy, proceed to Step 3.
- `Code: "ConnectionNotEnabled"` or 404 `"Connection [<uuid>] is invalid or you do not have access to it"` → **DO NOT proceed**. The connection is broken. Run the fallback below before aborting.

**Fallback — unfiltered listing.** Filtered `uip is connections list <connector-key>` can return orphaned records that don't appear in the unfiltered list (and vice versa). When the filtered listing's UUID fails to ping, run:

```bash
uip is connections list --output json
```

(no connector argument) and search the result for entries whose `ConnectorKey` matches the one you need. If a different UUID exists for the same connector, ping that one. Often the working connection is only visible in the unfiltered listing.

Only after both the filtered AND unfiltered listings have been exhausted (no UUID for that `ConnectorKey` pings cleanly) should you abort and tell the user to either re-authenticate (`uip is connections edit <connection-uuid>` opens a browser for OAuth) or create a fresh connection in the StudioWeb UI. **Do NOT author a workflow against a connection that hasn't pinged successfully** — it will 401 in cloud regardless of how correct the workflow JSON is.

### Step 3 — Stub the activity

```bash
uip api-workflow registry stub <activity-type-id> \
  [--connection-id <uuid>] \
  [--inputs '<json>'] \
  [--instance <n>] \
  [--slot-key <PascalCase>] \
  --output json
```

| Flag | Required | Default | Purpose |
|------|----------|---------|---------|
| `<activity-type-id>` | yes | — | The `uiPathActivityTypeId` from Step 1 |
| `--connection-id <uuid>` | IntSvc kind only | (none) | Pinged vendor connection UUID. IntSvc kind leaves placeholders if omitted. Ignored for Http kind. |
| `--inputs <json>` | no | `{}` | JSON object mapping field names to values. Field names match the IS schema (flat dotted keys — `"message.subject"`, not `{message:{subject:…}}`). Pass bare strings for literals; `${...}` for expression references (see field-shape rule (b)). |
| `--instance <n>` | no | `1` | Suffix for the slot/export bucket key. `--instance 2` → `GetNewestEmail_2` / `getNewestEmail_2`. |
| `--slot-key <PascalCase>` | no | derived from `objectName` | Override the auto-derived PascalCase slot key. Export bucket key always derives from `objectName + "_<n>"` regardless. |

Sample output for Outlook GetNewestEmail:

```json
{
  "Result": "Success",
  "Code": "ActivityStubSuccess",
  "Data": {
    "Kind": "IntSvc",
    "SlotKey": "GetNewestEmail_1",
    "ExportBucketKey": "getNewestEmail_1",
    "Activity": {
      "GetNewestEmail_1": {
        "call": "UiPath.IntSvc",
        "with": {
          "connector": "uipath-microsoft-outlook365",
          "connectionId": "a8e592a5-76bb-4062-b712-3c364e4a1128",
          "connectionResourceId": "a8e592a5-76bb-4062-b712-3c364e4a1128",
          "method": "GET",
          "endpoint": "/getNewestEmail",
          "queryParameters": { "parentFolderId": "Inbox" }
        },
        "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"getNewestEmail_1\": $output } }" },
        "metadata": {
          "fullName": "Connector",
          "activityType": "Connector",
          "displayName": "Get Newest Email",
          "uiPathActivityTypeId": "b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a",
          "configuration": "{\"essentialConfiguration\":{...}}"
        }
      }
    },
    "ResponseFields": [
      { "name": "subject", "type": "string", "required": false },
      { "name": "from.emailAddress.address", "type": "string", "required": false },
      { "name": "body.content", "type": "string", "required": false }
    ],
    "IsEnrichmentAvailable": true
  }
}
```

`Data.Activity` is the single-key object you drop into the root sequence's `do` array. `Data.ExportBucketKey` is what `$context.outputs.<X>` reads as downstream — bind expressions against this, NOT against `Data.SlotKey`. `Data.ResponseFields` lists the fields the IS schema says will be present on the output (under `.content.<field>` for IntSvc kind — see [Vendor curated activity response shape](#vendor-curated-activity-response-shape--contentx-not-x)).

`Data.Warnings` (when present):
- `"IS Elements metadata could not be fetched…"` → IS schema lookup failed (network / auth / connector unavailable). The stub uses fallback path `/<objectName>` and ships no `requestFields`. May still run for simple operations, but won't have the hub prefix or multipart declarations.
- `"No --connection-id provided…"` → IntSvc kind stub has `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholders — replace before running.

#### How `--inputs` maps to the activity

The stub looks at the IS schema for the operation and routes each input to its correct slot:

| IS schema location | Routes to | Example |
|--|--|--|
| `parameters[].type === "query"` | `with.queryParameters` | `parentFolderId` for getNewestEmail |
| `parameters[].type === "path"` | `with.pathParameters` | `repo` for `/repos/{repo}/issues` |
| `parameters[].type === "multipart"` | (declares `multipartParameters` automatically) | `body`, `file` for send-mail-v2 |
| `requestFields[]` (body schema) | `with.bodyParameters` | `message.subject`, `message.toRecipients` |

Fields not provided in `--inputs` get an empty-string default. Fields you provide in `--inputs` that don't match any schema field are dropped silently — verify against `Data.ResponseFields` and the IS schema if a value seems missing.

#### Required-field cross-check — the stub drops `required: true` request fields

**The stub omits required request fields from `queryParameters` / `pathParameters` / `bodyParameters` even when IS Elements knows they exist.** Verified case: Outlook `getNewestEmail` requires `parentFolderId` (`"required": true`, `"fieldLocation": "query"`), but `registry stub` returns `queryParameters: {}` unless that field was passed via `--inputs`. The runtime then 400s on a request the agent thought was complete.

The required-field metadata IS in the stub's response — it's just buried inside `Data.Activity.<SlotKey>.metadata.configuration`, which is a JSON-encoded string. Parse it (or use the simpler fallback below) before declaring the activity done.

**Cross-check option A — read `metadata.configuration.optionalConfiguration.fieldsContainer.inputFields`** from the stub output. Each entry has `name`, `required`, `fieldLocation` (`"query"` / `"path"` / `"body"`), and `defaultValue`. Anything with `required: true` whose `name` doesn't appear in the matching `<location>Parameters` block must be filled in.

**Cross-check option B (simpler) — call `uip is resources describe`** for the same operation. This returns the request fields in a clean shape, with `required` clearly marked:

```bash
uip is resources describe <connector-key> <object-name> \
  --operation <operation> \
  --connection-id <pinged-uuid> \
  --output json
```

`<operation>` matches what IS Elements calls the operation (`List`, `Create`, `Get`, etc.) — the first call without `--operation` lists the available operations.

Sample for Outlook `getNewestEmail`:

```json
{
  "Data": {
    "queryParameters": [
      { "name": "parentFolderId", "required": true,  "displayName": "Email folder",     "defaultValue": null },
      { "name": "filter",         "required": false, "displayName": "Additional filters" },
      { "name": "unReadOnly",     "required": false, "defaultValue": false },
      { "name": "withAttachmentsOnly", "required": false, "defaultValue": false },
      { "name": "importance",     "required": false, "defaultValue": "any" },
      { "name": "markAsRead",     "required": false, "defaultValue": false },
      { "name": "orderBy",        "required": false, "defaultValue": "receivedDateTime desc" },
      { "name": "top",            "required": false, "defaultValue": "1" }
    ]
  }
}
```

**Decision rule:** after `registry stub` returns, list every `required: true` field from either source (A or B). For each one, confirm there's a value in the matching `<location>Parameters` block of `Data.Activity`. If a value is missing, either:

- Re-run the stub with `--inputs '{"<field>": "<value>"}'`, or
- Hand-edit the activity to add the field — bare literal (rule b), flat dotted key (rule a).

**Heuristic:** when the stub returns empty `queryParameters`, `pathParameters`, or `bodyParameters` for a non-trivial vendor operation, it's almost certainly the bug — verified-real endpoints (CRUD operations on real objects) very rarely have zero required inputs.

Well-known folder-name shortcuts (e.g. MS Graph's `"inbox"`, `"sentitems"`, `"drafts"`) work for `parentFolderId`-style fields at runtime, but the StudioWeb FolderPicker only displays the friendly name if the value matches a real folder ID from the lookup cache. For exact UI fidelity, fetch the real ID once via `uip is resources execute <connector-key> list <object-name> --connection-id <uuid>` against the `lookup.path` (e.g. `/MailFolders`).

### Step 4 — Drop into the workflow, replace placeholders, validate

Drop `Data.Activity` into the root sequence after `WorkflowStart`. Replace any of these placeholders the stub may have emitted:

| Placeholder | When it appears | Replace with |
|--|--|--|
| `<REPLACE_WITH_TARGET_URL>` | Http kind, in `bodyParameters.url` | The target API URL — literal `"https://api.example.com/x"` or expression `"${$workflow.input.url}"` |
| `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` | IntSvc kind, in `with.connectionId` and `with.connectionResourceId` | The pinged UUID from Step 2 (rerun stub with `--connection-id` to avoid the placeholder) |

Before validating, run the **Required-field cross-check** above — if any `required: true` field is missing from `queryParameters` / `pathParameters` / `bodyParameters`, the workflow will run locally but fail in cloud (or worse — the StudioWeb FolderPicker / lookup picker will mark the field as invalid without a clear error).

Then validate:

```bash
uip api-workflow run ./my-workflow.json --output json
# (omit --no-auth — connector activities need IS auth)
```

For HTTP Request with `connectionId: "ImplicitConnection"` and a public API, `--no-auth` works. For any vendor connector (IntSvc kind), `uip login` is required because the IS proxy needs the bearer token.

### Step 5 — (Solutions-mode, IntSvc kind) declare the connection as a Solution resource

If the workflow lives in a **Solution** (the project's folder layout is `Solution/<ProjectName>/Workflow.json` + `Solution/resources/solution_folder/`), every vendor connection used by an activity MUST also be declared as a Solution resource. Without this declaration, StudioWeb's properties panel renders the connection as broken with the message **"to debug this resource, select a connection for it from the resource definition page"** — even though the workflow runs cleanly via `uip api-workflow run` and via "Run" in StudioWeb. The runtime resolves connections from `Workflow.json`; the panel resolves them from the Solution resource tree.

The CLI does not write this file. The agent must.

**Where to write.** `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`.

- `<connector-key>` is the same value as `connectorKey` in the stub output (`uipath-microsoft-outlook365`, `uipath-google-gmail`, etc.).
- `<connection-name>` matches the connection's `Name` from `uip is connections list` — typically the user's email or a friendly label. Spaces and special characters survive in the filename; `.json` suffix required.
- `solution_folder` is the default Solution folder name. Reuse whatever name appears in any existing `Solution/resources/<folder>/package/<workflow>.json` file's `folders[0].fullyQualifiedName` — that's the project's own resource declaration and the source of truth for the folder name.

**File shape.** Start from [assets/templates/solution-connection-resource-template.json](../assets/templates/solution-connection-resource-template.json) and fill in every `<REPLACE_WITH_…>` placeholder:

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<connection name — same as Name in `uip is connections list`>",
    "kind": "connection",
    "type": "<connector key — uipath-microsoft-outlook365 etc.>",
    "apiVersion": "integrationservice.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": {
      "connectorName": "<friendly name — Microsoft Outlook 365 etc.>",
      "name": "<same connection name>",
      "authenticationType": "AuthenticateAfterDeployment",
      "connectorVersion": "<version from stub config — e.g. 1.38.5>",
      "connectorKey": "<connector key>",
      "pollingInterval": 5
    },
    "locks": [],
    "key": "<connection UUID — MUST equal connectionId / connectionResourceId in Workflow.json>",
    "files": []
  }
}
```

**Where each value comes from:**

| Field | Source |
|--|--|
| `resource.name` / `resource.spec.name` | `Data[i].Name` from `uip is connections list <connector-key> --output json` |
| `resource.type` / `resource.spec.connectorKey` | `Data[i].ConnectorKey` (same value used in `Workflow.json` `with.connector`) |
| `resource.spec.connectorName` | `Data[i].ConnectorName` |
| `resource.spec.connectorVersion` | `essentialConfiguration.connectorVersion` inside the stub's `metadata.configuration` JSON-string. If unparseable, use `"1.0.0"` — the file is accepted regardless; the version is informational |
| `resource.key` | The pinged connection UUID — MUST match `with.connectionId` and `with.connectionResourceId` in the activity, and `key` in `bindings_v2.json` |
| `resource.folders[0].fullyQualifiedName` | Read any existing `Solution/resources/<folder>/package/<workflow>.json` and copy its `folders[0].fullyQualifiedName`. Default: `"solution_folder"` |

**Idempotency.** One file per unique connection UUID. If multiple activities in the workflow reuse the same connection, you only need one resource file. If two activities use different connections (e.g. Gmail + Outlook), write two files — one per `<connector-key>/<connection-name>.json`.

**What StudioWeb generates separately (you don't author these).** When the user opens the project in StudioWeb, StudioWeb writes `Solution/<ProjectName>/bindings_v2.json` (per-activity connection bindings) and `Solution/userProfile/<guid>/debug_overwrites.json` (debug-time resource→runtime-connection map). The CLI's `uip solution pack` regenerates `bindings_v2.json` from the workflow contents at pack time, and `debug_overwrites.json` is per-user state. Neither needs to be authored by the agent. **Only the connection-resource file** under `Solution/resources/solution_folder/connection/...` requires explicit authoring.

**Non-Solutions projects (a `project.json` at the top level, no `Solution/` wrapper).** Skip this step — the file structure has no `Solution/resources/` tree to write into, and the properties-panel error doesn't fire because StudioWeb knows there's no Solution to consult.

## Http vs IntSvc — what `stub` chose and why

The stub's decision rule:

| If `connectorKey` is… | Kind | `call` | `with.connector` | `with.endpoint` |
|--|--|--|--|--|
| `"uipath-uipath-http"` (HTTP Request) | **Http** | `"UiPath.Http"` | `"uipath-uipath-http"` | `"/http-request"` (always) |
| Any vendor (`"uipath-microsoft-outlook365"`, `"uipath-google-gmail"`, …) | **IntSvc** | `"UiPath.IntSvc"` | the vendor key | the curated path from IS Elements (often hub-prefixed) |

You don't pick the form — `connectorKey` does. Trying to use Http kind with a vendor connection UUID produces a misleading 401 "Invalid Element token" in cloud, because the IS proxy URL becomes `/elements_/v3/element/instances/{vendorConnId}/http-request` — which is not a real operation on the vendor element.

The HTTP-passthrough variant (`UiPath.Http` with `bodyParameters.targetConnector` pointing at a vendor) is **NOT generally available** — it requires a special UiPath HTTP-connector connection that's been authorized for the vendor. Don't use it unless you know you have such a connection.

### Http kind — `call: "UiPath.Http"` (HTTP Request curated activity)

The Http kind has a fixed shape: `with.method` is always `"POST"` (the outer wrapper), `with.endpoint` is always `"/http-request"`. The actual HTTP call lives in `bodyParameters`:

| `bodyParameters.X` | Value |
|--|--|
| `authentication` | `"manual"` (inline credentials) or `"connector"` (HTTP-connector connection) |
| `method` | The actual HTTP verb — `GET`, `POST`, `PUT`, `DELETE`, etc. |
| `url` | The target URL. The stub leaves `<REPLACE_WITH_TARGET_URL>` here unless passed via `--inputs`. |
| `headers` | Object mapping header name → value |
| `body` | Request body for POST/PUT/PATCH (object or string) |
| (other) | Anything you pass via `--inputs` is merged in here |

**Reading the response.** Http kind output is wrapped: `{ statusCode, content, headers }`. The parsed response body is in `.content`. Read via the camelCase export bucket key `http_request_1`:

```javascript
${$context.outputs.http_request_1.statusCode}              // 200
${$context.outputs.http_request_1.content}                 // parsed JSON body
${$context.outputs.http_request_1.content.fact}            // catfact field
```

### IntSvc kind — `call: "UiPath.IntSvc"` (vendor curated activity)

The IntSvc kind speaks directly to the vendor connector's curated operation:

| `with.X` | Value |
|--|--|
| `connector` | The vendor connector key (`"uipath-microsoft-outlook365"`, …) |
| `connectionId` | The pinged vendor UUID |
| `connectionResourceId` | Same as `connectionId` |
| `method` | The IS-schema HTTP verb |
| `endpoint` | The full curated operation path from IS Elements (often hub-prefixed) |
| `queryParameters` | Operation-specific query params (often `{}` if none) |
| `pathParameters` | Operation-specific path placeholders (rare; only for endpoints like `/repos/{repo}/issues`) |
| `bodyParameters` | Operation-specific body fields (POST/PUT only) |
| `multipartParameters` | Declared automatically when IS schema's `parameters` shows `"type": "multipart"` |

The IS proxy URL for a IntSvc kind call to Outlook GetNewestEmail becomes `/elements_/v3/element/instances/{outlookConnId}/getNewestEmail?parentFolderId=Inbox` — a real curated endpoint on the Outlook connector. The connector itself adds the Microsoft Graph OAuth at the proxy layer. **You don't supply a Graph URL; the connector knows where the Outlook API lives.**

## Vendor curated activity response shape — `content.X`, not `X`

The output of a IntSvc kind (`UiPath.IntSvc`) call is wrapped: the actual vendor payload lives under `.content`, not at the root of the activity output. Reading the payload as `$context.outputs.<Activity>.X` returns `undefined`; the correct path is `$context.outputs.<Activity>.content.X` (or `.content.value[0].X` for list-shaped vendor responses).

| Activity output (IntSvc kind) | What you get | What you want |
|--|--|--|
| `$context.outputs.getNewestEmail_1` | `{ statusCode: 200, content: { subject: "...", from: { ... }, body: "..." }, headers: { ... } }` | the `.content.X` field |
| `$context.outputs.getNewestEmail_1.subject` | `undefined` (wrong path) | — |
| `$context.outputs.getNewestEmail_1.content.subject` | `"Welcome to UiPath"` | ✓ |

> **The export-bucket key is `getNewestEmail_1`, not `GetNewestEmail_1`.** Connector activities have a slot/export divergence — see field-shape rule (c) below. The stub emits both keys; bind against `Data.ExportBucketKey`, not `Data.SlotKey`.

Examples:

```javascript
// In an If when:
"when": "${$context.outputs.getNewestEmail_1?.content?.subject?.length > 15}"

// In a JsInvoke script body — handle both string and parsed forms defensively
// because the local CLI runtime sometimes returns content as a JSON string and
// the cloud returns it pre-parsed:
const out = $context.outputs.getNewestEmail_1;
const raw = out && (out.content !== undefined ? out.content : out);
const body = (typeof raw === 'string') ? JSON.parse(raw) : raw;
const item = body && Array.isArray(body.value) ? body.value[0] : body;
return { subject: (item && (item.subject || item.Subject)) || '' };
```

This wrapping is universal for `UiPath.IntSvc` calls — it's how the IS proxy returns its envelope. Http kind (`UiPath.Http`) calls have their own wrapping (`statusCode`, `content`, `headers`) that follows the same pattern. Always assume `.content.<field>` first; if that's undefined, log the full output once to confirm the actual shape.

## Field-shape rules (flat keys, bare literals, renamed export, hub prefix)

The stub emits these correctly. They matter when you **edit** an activity after stubbing — adding a field, changing a value, or copy-pasting between activities. Violating any rule causes silent data loss on the next StudioWeb save.

### Rule (a) — `bodyParameters` / `queryParameters` / `pathParameters` use FLAT DOTTED KEYS

The connector schema lists fields like `message.toRecipients`, `message.subject`, `message.body.content`. The dot is a **literal character in the field name**, not a path separator. StudioWeb's deserializer (`buildConnectorProperties` in `connector-translator-utils.ts`) scans `bodyParameters` for keys that match the connector's input-field names verbatim — it does NOT recurse into nested objects.

```json
// ✗ WRONG — StudioWeb's deserializer can't find any of these on save,
//   so the message block disappears the next time the file is saved:
"bodyParameters": {
  "message": {
    "toRecipients": "andrei.hodoroaga@uipath.com",
    "subject": "this is a test",
    "body": { "content": "<p>hi</p>", "contentType": "Html" }
  },
  "saveToSentItems": true
}

// ✓ CORRECT — flat dotted keys match the connector's field names verbatim:
"bodyParameters": {
  "message.toRecipients": "andrei.hodoroaga@uipath.com",
  "message.subject": "this is a test",
  "message.body.content": "<p>hi</p>",
  "message.body.contentType": "Html",
  "saveToSentItems": true
}
```

Same rule applies to `queryParameters` and `pathParameters`. The IS proxy unflattens the dotted keys back into a nested wire payload before forwarding to the vendor, so the over-the-wire JSON is identical — but the on-disk shape must be flat.

### Rule (b) — Literals in connector params are BARE, NOT `${'literal'}`-wrapped

The Assign / Response literal-wrap rule (SKILL.md rule 5) does NOT apply here. The opposite is true. StudioWeb's connector deserializer treats `${'foo'}` as a non-literal expression and refuses to bind it as a field value — the field becomes empty after save.

```json
// ✗ WRONG — designer reads "${'andrei...'}" as an expression, not a literal,
//   and clears the field on save:
"bodyParameters": {
  "message.toRecipients": "${'andrei.hodoroaga@uipath.com'}",
  "message.subject": "${'this is a claude skill test'}"
}

// ✓ CORRECT — bare literals:
"bodyParameters": {
  "message.toRecipients": "andrei.hodoroaga@uipath.com",
  "message.subject": "this is a claude skill test"
}
```

References stay wrapped: `"message.body.content": "${$context.variables.titleLabel}"` is correct — that's a real expression, not a literal.

| Where | Literal style |
|--|--|
| `Assign.set` value | `"${'literal'}"` (rule 5) |
| `Response` payload literal | `"${'literal'}"` (rule 5) |
| If `when` literal | `"${'literal'}"` (rule 5) |
| Connector `bodyParameters` / `queryParameters` / `pathParameters` literal | `"literal"` (bare — opposite rule) |

When passing literals via `--inputs` to `stub`, pass bare strings: `--inputs '{"message.subject": "hi"}'`, NOT `'{"message.subject": "${'hi'}"}'`.

### Rule (c) — Slot key (PascalCase) ≠ export bucket key (camelCase `objectName + "_N"`)

Every other activity type in this skill (Assign, JsInvoke, If, ForEach, DoWhile, TryCatch, Wait, Response) keeps the same key in the slot AND in the export bucket. Connector activities are the **single exception**: StudioWeb's serializer renames the export bucket to a camelCase form derived from the connector's `objectName`.

```json
// Slot key — PascalCase, what's in the do array:
{ "GetNewestEmail_1": { ... } }

// Export bucket key — camelCase, what StudioWeb writes for the export
// AND what $context.outputs reads as:
"export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"getNewestEmail_1\": $output } }" }

// Downstream reads also use camelCase:
"when": "${$context.outputs.getNewestEmail_1?.content?.subject?.length > 15}"
"response": "${{ subject: $context.outputs.getNewestEmail_1.content.subject }}"
```

**Derivation rule.** Take `objectName` from the resolve output, replace any non-identifier character (e.g. `-`) with `_`, append `_<N>` where N is the activity's instance number:

| `objectName` | Slot key (stub emits) | Export bucket key (stub emits) |
|--|--|--|
| `getNewestEmail` | `GetNewestEmail_1` | `getNewestEmail_1` |
| `send-mail-v2` | `SendMailV2_1` (or `--slot-key` override) | `send_mail_v2_1` |
| `http-request` | `HttpRequest_1` (or `--slot-key` override) | `http_request_1` |
| `search_issues` | `SearchIssues_1` | `search_issues_1` |

The stub returns both as `Data.SlotKey` and `Data.ExportBucketKey`. Bind downstream `$context.outputs.<X>` against `ExportBucketKey`. The TypeScript linter flag `TS2551: Property 'GetNewestEmail_1' does not exist on type 'typeof outputs'. Did you mean 'getNewestEmail_1'?` is the symptom of binding against the wrong one.

### Rule (d) — `endpoint` may include a hub prefix beyond `/<objectName>`

Some curated operations live under a hub path: Outlook `send-mail-v2` is `/hubs/productivity/send-mail-v2`, not `/send-mail-v2`. The hub prefix lives in IS Elements, not in the TypeCache.

The stub fills the full path from IS Elements automatically. The fallback path `/<objectName>` is only used if `IsEnrichmentAvailable` is `false` (network / auth / connector access issue). When you see the warning `"IS Elements metadata could not be fetched…"`, the endpoint may be wrong — re-run the stub once IS access is restored, or look up the path manually via `uip is resources describe <connector-key> <object-name>`.

## Multipart endpoints — `multipartParameters` declaration (handled by `stub`)

Some curated operations require `multipart/form-data` instead of `application/json` — typically endpoints that allow file attachments (Outlook `send-mail-v2`, Gmail `sendEmail` with attachments, GitHub `upload-release-asset`, etc.). The stub detects multipart from the IS schema's `parameters` section and declares `multipartParameters` on the activity automatically.

A multipart endpoint shows up in IS Elements with a `body`-named parameter of `"type": "multipart"`:

```json
{
  "parameters": [
    { "name": "file", "type": "file", "location": "multipart" },
    { "name": "body", "type": "multipart", "location": "multipart" }
  ],
  "requestFields": [
    { "name": "message.toRecipients", ... },
    { "name": "message.subject", ... }
  ]
}
```

The stub emits both `bodyParameters` (with the flat dotted keys per rule (a)) AND `multipartParameters`:

```json
"with": {
  ...
  "endpoint": "/hubs/productivity/send-mail-v2",
  "bodyParameters": {
    "message.toRecipients": "andrei.hodoroaga@uipath.com",
    "message.subject": "...",
    "message.body.content": "...",
    "message.body.contentType": "Text",
    "saveToSentItems": true
  },
  "queryParameters": { "saveAsDraft": false },
  "multipartParameters": [
    { "name": "file", "dataType": "file" },
    { "name": "body", "dataType": "string" }
  ]
}
```

What the executor does with it (`constructMultipartFormData` in `node_modules/@uipath/api-workflow-commons/dist/activities/is/utils/is-utils.js`):

- `dataType: "string"` → executor JSON-stringifies the **entire `bodyParameters` object** and stuffs the resulting string into the multipart part of that name. So `bodyParameters` becomes the JSON payload inside the `body` part.
- `dataType: "file"` → executor expects a file reference (currently leave the part empty for "no attachment" — the vendor accepts an empty `file` part for attachment-less emails).

Without `multipartParameters` you get `400 "Unable to parse multipart body"`. The stub authors both fields together; do not remove `multipartParameters` even when sending an attachment-less email.

## Worked example — HTTP Request to a public API (Http kind)

```bash
# 1. Resolve the GUID
uip api-workflow registry resolve "http request" --output json
# → match: { uiPathActivityTypeId: "5c4cc855-b42a-37e6-b910-de8588998fce",
#            displayName: "HTTP Request", connectorKey: "uipath-uipath-http",
#            objectName: "http-request", httpMethod: "POST" }

# 2. (skipped — Http kind uses ImplicitConnection)

# 3. Stub the activity — pass the URL via --inputs to skip placeholder replacement
uip api-workflow registry stub 5c4cc855-b42a-37e6-b910-de8588998fce \
  --inputs '{"method":"GET","url":"https://catfact.ninja/fact"}' \
  --output json
# → Data.Activity with the HttpRequest_1 key, ready to drop in
```

The resulting workflow activity (drop into the root sequence):

```json
{
  "HttpRequest_1": {
    "call": "UiPath.Http",
    "with": {
      "connector": "uipath-uipath-http",
      "connectionId": "ImplicitConnection",
      "connectionResourceId": "ImplicitConnection",
      "method": "POST",
      "endpoint": "/http-request",
      "bodyParameters": {
        "authentication": "manual",
        "method": "GET",
        "url": "https://catfact.ninja/fact",
        "headers": {}
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"http_request_1\": $output } }" },
    "metadata": {
      "fullName": "Connector",
      "activityType": "Connector",
      "displayName": "HTTP Request",
      "uiPathActivityTypeId": "5c4cc855-b42a-37e6-b910-de8588998fce",
      "configuration": "{\"essentialConfiguration\":{ … ,\"unifiedTypesCompatible\":true,\"savedJitInputFieldId\":\"in_http-request\"}}"
    }
  }
}
```

The `unifiedTypesCompatible: true` + `savedJitInputFieldId: "in_http-request"` flags inside `essentialConfiguration` are what tell StudioWeb to render the unified HTTP card.

Verified end-to-end: `uip api-workflow run --no-auth` on the resulting workflow returns `statusCode: 200`, `content.fact: "..."`. StudioWeb's designer renders the activity as the unified HTTP Request card. See [../assets/templates/connector-call-example.json](../assets/templates/connector-call-example.json) for a complete stub-generated workflow.

## Worked example — Outlook Get Newest Email (IntSvc kind)

```bash
# 1. Resolve
uip api-workflow registry resolve "outlook newest email" --output json
# → { uiPathActivityTypeId: "b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a",
#     connectorKey: "uipath-microsoft-outlook365", objectName: "getNewestEmail",
#     httpMethod: "GET" }

# 2a. Find a vendor connection (filtered)
uip is connections list uipath-microsoft-outlook365 --output json
# → Data: [{ Id: "a8e592a5-76bb-4062-b712-3c364e4a1128", ... }]

# 2b. Verify the connection is actually working — REQUIRED
uip is connections ping a8e592a5-76bb-4062-b712-3c364e4a1128 --output json
# → Code: "ConnectionPing" → proceed
# → 404 / ConnectionNotEnabled → orphan, try the unfiltered fallback before aborting:
uip is connections list --output json
# → search Data for entries with ConnectorKey == "uipath-microsoft-outlook365",
#   take a different Id, and re-ping it. Only abort if no UUID pings.

# 3a. Stub the activity (note: without --inputs the stub emits queryParameters: {})
uip api-workflow registry stub b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a \
  --connection-id a8e592a5-76bb-4062-b712-3c364e4a1128 \
  --inputs '{"parentFolderId":"Inbox"}' \
  --output json
# → Kind: "IntSvc", SlotKey: "GetNewestEmail_1", ExportBucketKey: "getNewestEmail_1",
#   Activity: { GetNewestEmail_1: { ... } }, ResponseFields: [...]

# 3b. Cross-check required request fields — stub silently drops them
uip is resources describe uipath-microsoft-outlook365 getNewestEmail \
  --operation List \
  --connection-id a8e592a5-76bb-4062-b712-3c364e4a1128 \
  --output json
# → Data.queryParameters[] has parentFolderId with required: true.
# If --inputs was omitted in Step 3a, re-run with --inputs '{"parentFolderId":"inbox"}'
# (or edit the activity by hand) before continuing.

# 5. Write the Solution connection-resource file (required for Solutions-mode projects):
#    Solution/resources/solution_folder/connection/uipath-microsoft-outlook365/<connection-name>.json
#    with "key" = a8e592a5-76bb-4062-b712-3c364e4a1128.
```

Drop `Data.Activity` into the root sequence after `WorkflowStart`. Bind downstream:

```json
"when": "${$context.outputs.getNewestEmail_1?.content?.subject?.length > 15}"
"response": "${{ subject: $context.outputs.getNewestEmail_1.content.subject }}"
```

## Worked example — Outlook send-mail-v2 (IntSvc kind, multipart)

```bash
# 1. Resolve
uip api-workflow registry resolve "send mail v2" --output json
# → { uiPathActivityTypeId: "<send-mail-v2 GUID>",
#     connectorKey: "uipath-microsoft-outlook365", objectName: "send-mail-v2",
#     httpMethod: "POST" }

# 2. (use the same pinged connection from above)

# 3. Stub — body fields passed via --inputs as flat dotted keys
uip api-workflow registry stub <send-mail-v2-guid> \
  --connection-id a8e592a5-76bb-4062-b712-3c364e4a1128 \
  --inputs '{
    "message.toRecipients": "andrei.hodoroaga@uipath.com",
    "message.subject": "this is a claude skill test",
    "message.body.content": "${$context.variables.titleLabel}",
    "message.body.contentType": "Text",
    "saveToSentItems": true,
    "saveAsDraft": false
  }' \
  --output json
```

The stub detects multipart from IS Elements (`parameters[].type === "multipart"`) and emits:

```json
{
  "SendMailV2_1": {
    "call": "UiPath.IntSvc",
    "with": {
      "connector": "uipath-microsoft-outlook365",
      "connectionId": "a8e592a5-76bb-4062-b712-3c364e4a1128",
      "connectionResourceId": "a8e592a5-76bb-4062-b712-3c364e4a1128",
      "method": "POST",
      "endpoint": "/hubs/productivity/send-mail-v2",
      "bodyParameters": {
        "message.toRecipients": "andrei.hodoroaga@uipath.com",
        "message.subject": "this is a claude skill test",
        "message.body.content": "${$context.variables.titleLabel}",
        "message.body.contentType": "Text",
        "saveToSentItems": true
      },
      "queryParameters": { "saveAsDraft": false },
      "multipartParameters": [
        { "name": "file", "dataType": "file" },
        { "name": "body", "dataType": "string" }
      ]
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"send_mail_v2_1\": $output } }" },
    "metadata": { ... }
  }
}
```

Note all four field-shape rules in action: flat dotted keys (a), bare literals + `${...}` only for actual references (b), `send_mail_v2_1` export bucket from `send-mail-v2` objectName with `-`→`_` (c), `/hubs/productivity/send-mail-v2` endpoint with hub prefix (d).

## Editing connector activities after stubbing

When the user asks to change a value, add a field, or copy a stubbed activity to a new instance:

- **Adding a field to `bodyParameters` / `queryParameters` / `pathParameters`** → use the exact field name from `Data.ResponseFields` or the IS schema. Flat dotted (rule a). Bare literal or `${$context...}` reference (rule b).
- **Changing the connection** → re-ping the new UUID before pasting it in. Update both `connectionId` and `connectionResourceId`.
- **Renaming the slot key** (e.g. `GetNewestEmail_1` → `GetNewestEmail_Inbox`) → DO NOT also rename the export bucket key. The export key stays `getNewestEmail_1` (or whatever camelCase form the stub emitted). Downstream `$context.outputs.<X>` references must continue to use the camelCase key.
- **Adding a second instance of the same activity** → re-stub with `--instance 2` instead of copy-pasting. The stub re-derives `_2`-suffixed slot and export bucket keys correctly.

## Limits of this approach

1. **`activityType` values other than `"Curated"`** (e.g. `"Generic"`, `"GenericTrigger"`, `"CuratedTrigger"`) need different `metadata.configuration` shapes — Generic activities require an explicit `operation` (`"list"`, `"create"`, etc.), Triggers require event-related fields. The current `stub` rejects non-Curated activities with `Activity type 'X' is not supported in v1`. For those, escalate to manual authoring or wait for a `stub` extension.

2. **Stub doesn't validate `--inputs` against the IS schema.** Field names not in `requestFields` / `parameters` are silently dropped on the way through `pickFields`. Check `Data.ResponseFields` and the IS schema if a value goes missing.

3. **Subsequent designer saves can re-introduce mangling** of the Response activity (issue **SW-28452** / [UiPath/cli#1537](https://github.com/UiPath/cli/issues/1537)). See [troubleshooting.md](troubleshooting.md#object-valued-response-gets-corrupted-fields-evaluate-to-literal-expression-text-sw-28452--cli1537) — defending against the Response corruption is independent of the connector-activity discovery flow.

4. **Login is required for `resolve` and `stub`.** Both hit live tenant endpoints (TypeCache and IS Elements). `uip api-workflow run --no-auth` still works for the resulting workflow if it only uses Http kind with `ImplicitConnection`; IntSvc kind always needs auth at run time.

## Anti-patterns

- **Do NOT invent a `uiPathActivityTypeId`.** It must come from `registry resolve`. Hand-authoring or reusing a fallback default produces a generic/wrong card.
- **Do NOT hand-write the `metadata.configuration` blob.** `registry stub` builds it from the TypeCache `Config` + IS Elements path. Any other shape risks the "block icon" rendering.
- **Do NOT skip `uip is connections ping` for IntSvc kind.** A connection in the listing can still be in a broken state. Always ping after listing.
- **Do NOT proceed past a failed ping** — not even with a "I'll flag this and continue" note. A 404 / `ConnectionNotEnabled` ping result means the workflow WILL 401 in cloud. Run the unfiltered-listing fallback (Step 2) before aborting; if that also fails, stop authoring and tell the user to re-auth or create a fresh connection.
- **Do NOT trust the filtered `uip is connections list <connector-key>` as the only source of UUIDs.** Filtered listings can return stale orphan records. If the filtered UUID fails to ping, re-list **without** the connector argument and look for a different `Id` with the same `ConnectorKey`.
- **Do NOT read IntSvc kind output at the root.** Vendor curated responses wrap the payload in `.content` — read `.content.<field>`, not `.<field>`.
- **Do NOT use Http kind (`UiPath.Http`) for vendor activities.** Mixing the HTTP connector's routing with a vendor connection UUID produces a 401 in cloud. Stub picks the form by `connectorKey`; trust it.
- **Do NOT mix `call: "http"` and `call: "UiPath.Http"`.** The simple `call: "http"` form won't render in StudioWeb's designer. The stub always emits `UiPath.Http` (Http kind) or `UiPath.IntSvc` (IntSvc kind).
- **Do NOT nest `bodyParameters` fields when editing.** Connector schema's dotted names (`message.toRecipients`) are literal keys. Nested `{ message: { toRecipients: ... } }` is silently dropped by StudioWeb's deserializer on save.
- **Do NOT wrap `bodyParameters` / `queryParameters` literals as `${'literal'}` when editing.** Connector params take BARE literals — `${'foo'}` is read as an expression and cleared on save.
- **Do NOT rename the export bucket key.** Connector activities use camelCase `objectName + "_<N>"` for the export — the stub gets this right; renaming it breaks every downstream `$context.outputs.<X>` read.
- **Do NOT remove `multipartParameters` from a multipart endpoint** — even for an attachment-less email. The executor's multipart wrapper depends on the declaration; without it, the vendor returns `400 "Unable to parse multipart body"`.
- **Do NOT trust `registry stub`'s `queryParameters` / `pathParameters` / `bodyParameters` as complete.** The stub drops `required: true` fields. After every stub call, cross-check via `uip is resources describe <connector-key> <object-name> --operation <op> --connection-id <uuid> --output json` (or parse `metadata.configuration.optionalConfiguration.fieldsContainer.inputFields` from the stub output itself) and fill in anything required that's missing. Symptom of skipping: workflow runs locally on stale defaults, fails in cloud with a 4xx, or the StudioWeb properties panel marks the field invalid without a clear error.
- **Do NOT leave `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` (or any `<REPLACE_WITH_*>` placeholder) in a generated workflow.** StudioWeb's properties panel renders the literal placeholder string as if it were a real connection name — the connection pill shows `<REPLACE_WITH_VENDOR_C...>` with a red error, and any subsequent run 401s in cloud. The placeholder is meaningful **only** in the template file under `assets/templates/`; the moment you copy the stub's `Data.Activity` into the user's workflow, every placeholder MUST become a real value (UUID from `uip is connections ping`, URL from `--inputs` or the user's request). If you don't have a working UUID, **stop authoring** and ask the user — do not write the sentinel to disk. Re-stubbing with `--connection-id <uuid>` is the cleanest way to avoid the placeholder ever existing in the output.
- **Do NOT skip the Solution connection-resource file in Solutions-mode projects.** Even when `bindings_v2.json` is correct and the workflow runs, the StudioWeb properties panel reads connection definitions from `Solution/resources/solution_folder/connection/<connector-key>/<name>.json` and flags the activity with "to debug this resource, select a connection for it from the resource definition page" without it. The CLI does not write this file — the agent must, with `resource.key` equal to the connection UUID. See [Step 5](#step-5--solutions-mode-intsvc-kind-declare-the-connection-as-a-solution-resource).
