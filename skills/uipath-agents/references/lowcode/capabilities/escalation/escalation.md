# Action Center Escalation (Human-in-the-Loop)

Walkthrough for adding an escalation resource that hands off agent control to a human via a deployed UiPath Action Center app (a web app of kind `workflow Action`). The agent pauses, creates a task on the app, and resumes when the human picks an outcome.

The only channel type currently supported end-to-end by `uip solution resource refresh` is `actionCenter`. Other channel types (`email`, `slack`, `teams`) are recognised by the runtime but have no automatic solution-level resource generation and are out of scope for this skill.

## When to Use

- Agent needs human approval, review, or input mid-execution
- A UiPath Action Center app of kind `Workflow Action` is already deployed in Orchestrator

**Key pattern:** the skill writes only the agent-level `resources/{EscalationName}/resource.json`. `uip solution resource refresh` emits an App binding into `bindings_v2.json` and then hand-writes the four solution-level files (`app/workflow Action/`, `appVersion/`, `package/`, `process/webApp/`) plus two `debug_overwrites.json` entries (`kind: "app"`, `kind: "process"`) automatically. No manual solution-level authoring is required for `actionCenter` channels.

## Discovery

### Step 1 — Scaffold solution and agent (if not already done)

Scaffold per [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Find the deployed Action Center app

```bash
uip solution resource list --kind App --source remote --search "<APP_NAME>" --output json
```

Filter the result for entries whose `Type` is `"Workflow Action"` (Coded / CodedAction types cannot back an escalation today). Each entry carries:

| `resource list` field | Use as |
|-----------------------|--------|
| `Key` | `channel.properties.resourceKey` (also becomes the app resource's `key`) |
| `Name` | `channel.properties.appName` (also propagates as binding `name`) |
| `Folder` | `channel.properties.folderPath` — literal Orchestrator folder (e.g., `"Shared/Approvals"`). Propagates verbatim as `folderPath` in the App binding inside `bindings_v2.json`. |
| `FolderKey` | folder reference (informational — escalations set `channel.properties.folderName: null`; `FolderKey` is still used in `debug_overwrites.json`) |

`Key` gives you everything you need to identify the backing app, but `resource list` does not return `systemName` or `deployVersion` — both are required to fetch the action schema in Step 3. Query the Apps API once, filtered client-side by `id == <KEY>`, to extract them:

```bash
# SECURITY: Never read ~/.uipath/.auth directly. Keep the token inside the shell.
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-apps?state=deployed&pageNumber=0&limit=100" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-Uipath-Tenantid: $UIPATH_TENANT_ID" \
  -H "Accept: application/json"'
```

From the matching entry in `.deployed[]`, extract:

| Field | Use as |
|-------|--------|
| `systemName` | `appSystemName` query parameter for action-schema (Step 3) |
| `deployVersion` | `channel.properties.appVersion` (integer) AND `version` query parameter for action-schema |

### Step 3 — Fetch the app's action schema

Use `systemName` and `deployVersion` from Step 2.

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-schema?appSystemName=<SYSTEM_NAME>&version=<DEPLOY_VERSION>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-Uipath-Tenantid: $UIPATH_TENANT_ID" \
  -H "Accept: application/json"'
```

Response shape:

```jsonc
{
  "inputs":   [{ "name": "Content", "type": "System.String", ... }],
  "outputs":  [],
  "inOuts":   [{ "name": "Comment", "type": "System.String", "description": "..." }],
  "outcomes": [{ "name": "approve", "description": "..." }, { "name": "reject", ... }]
}
```

### Step 4 — Build the channel schemas

From the action-schema response, construct the channel fields:

- `channel.inputSchema` — object whose `properties` combine every `inputs[]` entry + every `inOuts[]` entry. Map each dotnet `type` to a JSON Schema type using the same rules as external RPA tools (`System.String` → `"string"`, `System.Int32`/`Int64`/`Decimal`/`Double` → `"number"`, `System.Boolean` → `"boolean"`, other → `"string"`). Preserve `description` when present.
- `channel.outputSchema` — object whose `properties` combine every `inOuts[]` entry + every `outputs[]` entry. Same mapping rules.
- `channel.inputSchemaDotnetTypeMapping` / `outputSchemaDotnetTypeMapping` — flat object keyed by arg `name`, value = the raw dotnet type string.
- `channel.outcomeMapping` — one key per `outcomes[].name`, value defaults to `"continue"`. Ask the user which outcomes should `"end"` the agent run.

### Step 5 — Ask for recipients and task title

**Recipients are mandatory.** An escalation with an empty `recipients: []` uploads cleanly but Studio Web shows the escalation with no assignee and the runtime task will not route. Always collect at least one recipient.

**Default to email recipients (`type: 3`).** This is the simplest form — you don't need to look up user GUIDs or display names:

```jsonc
"recipients": [
  { "type": 3, "value": "user@example.com" }
]
```

Ask the user who should receive the task. If they say "me" or don't specify, fall back to the current user's email from the JWT `email` claim:

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && echo "$UIPATH_ACCESS_TOKEN" | python3 -c "
import sys, base64, json
tok = sys.stdin.read().strip()
payload = tok.split(\".\")[1]
payload += \"=\" * (-len(payload) % 4)
print(json.loads(base64.urlsafe_b64decode(payload)).get(\"email\"))
"'
```

Use other `type` values (1=UserId, 2=GroupId, 4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName) only when the user explicitly asks for a GUID-based recipient or an asset-backed one — they require additional inputs (user/group GUID from the Identity API, or an asset name).

> **Do not set `displayName` for `type: 3`.** The reference solution omits it; leaving it out results in cleaner rendering in Studio Web.

**`channel.properties.folderName` must be `null`.** Do NOT set it to `"solution_folder"` or any other string — that causes Studio Web to report "Resource provisioning failed (#100)" on solution import. The runtime resolves the folder from the app resource at deploy time.

Default `taskTitle` / `taskTitleV2` to a short human-readable label — e.g., `"Approval request"`. `taskTitle` is a string; `taskTitleV2` is a `contentTokens`-style object (see [../../agent-definition.md](../../agent-definition.md) § Messages).

## Agent-Level Resource Shape

**Path:** `<AGENT_NAME>/resources/<EscalationName>/resource.json`

Escalations hand off agent control to a human via a channel. Generate fresh UUIDs for the top-level `id` AND the channel `id` — do not reuse.

```jsonc
{
  "$resourceType": "escalation",
  "id": "<uuid-v4>",                                // stable; generate once, never change
  "name": "MyEscalation",                           // folder name & resource name must match
  "description": "Escalate to a human assistant for approval",
  "escalationType": 0,                              // 0 = Escalation, 1 = VsEscalation
  "isAgentMemoryEnabled": false,
  "ixpToolId": null,                                // only used when escalationType = 1
  "storageBucketName": null,                        // only used when escalationType = 1
  "properties": {},
  "governanceProperties": { "isEscalatedAtRuntime": false },
  "channels": [
    {
      "id": "<uuid-v4>",                            // channel id — generate a new one per channel
      "name": "Channel",
      "description": "Channel description",
      "type": "actionCenter",                       // lowercase. Other values: "email", "slack", "teams"
      "inputSchema": {                              // derived from action-schema.inputs + action-schema.inOuts
        "type": "object",
        "properties": {
          "<argName>": { "type": "<jsonSchemaType>", "description": "<desc>" }
        }
      },
      "inputSchemaDotnetTypeMapping": {             // { argName: "System.String" | "System.Int32" | ... }
        "<argName>": "System.String"
      },
      "outputSchema": {                             // derived from action-schema.inOuts + action-schema.outputs
        "type": "object",
        "properties": {
          "<argName>": { "type": "<jsonSchemaType>", "description": "<desc>" }
        }
      },
      "outputSchemaDotnetTypeMapping": {
        "<argName>": "System.String"
      },
      "outcomeMapping": {                           // one key per action-schema.outcomes[].name
        "<outcomeName>": "continue"                 // "continue" (agent resumes) | "end" (agent stops)
      },
      "properties": {
        "resourceKey": "<appId-guid>",              // from `action-apps?state=deployed` → `id`
        "appName": "<deploymentTitle>",             // from the same response → `deploymentTitle`
        "folderName": null,                         // MUST be null — setting "solution_folder" or anything else causes Studio Web "Resource provisioning failed (#100)" on solution import
        "folderPath": "Shared/Approvals",           // literal Folder from `uip solution resource list --kind App`. Propagates into bindings_v2.json App binding.
        "appVersion": 1,                            // from the same response → `deployVersion` (integer)
        "isActionableMessageEnabled": false,
        "actionableMessageMetaData": null
      },
      "recipients": [                               // REQUIRED — at least one. Empty array uploads but Studio Web shows the escalation with no assignee.
        {
          "type": 3,                                // RecipientType: 1=UserId, 2=GroupId, 3=UserEmail (preferred — simplest),
                                                    //   4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName
          "value": "user@example.com"               // for type 3, the email string. For type 1/2, a user/group GUID.
                                                    // `displayName` is NOT required for type 3 — omit it.
        }
      ],
      "taskTitle": "Approval request",              // deprecated but still written for back-compat
      "taskTitleV2": {
        "type": "textBuilder",                      // or "dynamic" (single string) — see contentTokens rules
        "tokens": [
          { "type": "simpleText", "rawString": "Approval request" }
        ]
      },
      "labels": []                                  // optional string tags
    }
  ]
}
```

**`outcomeMapping` rules:**
- One entry per outcome returned by the app's `action-schema` (e.g., `approve`, `reject`).
- Each value is `"continue"` (agent processes the outcome and continues) or `"end"` (agent stops when the outcome fires).
- Default every outcome to `"continue"` unless the user has specified otherwise.

**`inputSchema` / `outputSchema` derivation from the action schema response:**
- `channel.inputSchema.properties` = union of `action-schema.inputs[].name` and `action-schema.inOuts[].name` — these are what the human sees in the task form.
- `channel.outputSchema.properties` = union of `action-schema.inOuts[].name` and `action-schema.outputs[].name` — these are what the agent receives back.
- For each property, set `type` by mapping the dotnet type string in the same way as external RPA process tools (`System.String` → `"string"`, `System.Int32`/`Int64`/`Decimal`/`Double` → `"number"`, `System.Boolean` → `"boolean"`, everything else → `"string"`).
- Copy each arg's `description` verbatim when present.
- `inputSchemaDotnetTypeMapping` / `outputSchemaDotnetTypeMapping` preserve the raw dotnet type names keyed by arg name — Studio Web uses these when serialising task payloads.

## Solution-Level Files

**Solution-level files for Action Center escalations are auto-generated.** Unlike external process tools, you do NOT hand-write any solution-level files for an escalation. `uip solution resource refresh` scans agent projects for escalation resources, resolves each `properties.resourceKey` against the Apps API + `publish/versions` + Orchestrator `/odata/Releases` + `GetPackageEntryPointsV2`, and writes all four required files itself:

- `resources/solution_folder/app/workflow Action/<deploymentTitle>.json`
- `resources/solution_folder/appVersion/<title>.json`
- `resources/solution_folder/package/<title>.json`
- `resources/solution_folder/process/webApp/<deploymentTitle>.json`

The fourth file (`process/webApp/...`) backs the app resource's `dependencies[1]: {kind: "Process"}` — without it, Studio Web reports "Resource provisioning failed (#100)" on solution import.

## Walkthrough

### Step 6 — Write the agent-level resource.json

**File:** `<AGENT_NAME>/resources/<EscalationName>/resource.json`

Use the full shape from § Agent-Level Resource Shape above. Generate fresh UUIDs for the top-level `id` AND the channel `id` — do not reuse.

### Step 7 — Validate and refresh solution resources

```bash
# Validate — checks the agent and resource.json, migrates schema if needed
uip agent validate "<AGENT_NAME>" --output json

# Refresh — imports the App binding from bindings_v2.json into the solution.
uip solution resource refresh --output json
```

After refresh, confirm the four solution-level app files exist under `resources/solution_folder/`:

- `app/workflow Action/<AppName>.json`
- `appVersion/<PkgName>.json`
- `package/<PkgName>.json`
- `process/webApp/<AppName>.json`

If any are missing, hand-author them using the templates above and the Apps API + `publish/versions` + Orchestrator `/odata/Releases` data. The `process/webApp/<AppName>.json` file is the one most commonly missing and its absence causes "Resource provisioning failed (#100)" on solution import.

### Step 8 — Bundle and upload

```bash
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules. Escalation-specific gotchas:

- `properties.folderName` MUST be `null` (any string causes "Resource provisioning failed (#100)"). This is a separate field from `properties.folderPath` — they coexist on the channel: `folderName` stays `null`, `folderPath` carries the literal `Folder`.
- `properties.folderPath` MUST be the literal `Folder` from `uip solution resource list --kind App` (e.g., `"Shared/Approvals"`). `uip agent validate` rejects `"solution_folder"` here — escalation apps are always external. See [../../critical-rules.md](../../critical-rules.md) Rule 11 and Anti-pattern 18.
- `recipients` array MUST have at least one entry. Empty uploads but routes nowhere.
- For `type: 3` (email) recipients, do NOT set `displayName`.
- Generate fresh UUIDs for the top-level `id` AND each channel `id`.
- `channel.type` is lowercase `"actionCenter"`.
- Other channel types (`email`, `slack`, `teams`) are runtime-recognized but require manual solution authoring — out of scope today.

## References

- [../../agent-definition.md](../../agent-definition.md) § Messages, § contentTokens (for `taskTitleV2`)
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
