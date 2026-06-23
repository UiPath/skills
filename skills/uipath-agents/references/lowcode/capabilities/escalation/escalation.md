# Action Center Escalation (Human-in-the-Loop)

Walkthrough for adding an escalation resource that hands off agent control to a human via a deployed UiPath Action Center app (a web app of kind `workflow Action`). The agent pauses, creates a task on the app, and resumes when the human picks an outcome.

The only channel type currently supported end-to-end by `uip solution resources refresh` is `actionCenter`. Other channel types (`email`, `slack`, `teams`) are recognised by the runtime but have no automatic solution-level resource generation and are out of scope for this skill.

## When to Use

- Agent needs human approval, review, or input mid-execution
- A UiPath Action Center app of kind `Workflow Action` is already deployed in Orchestrator (external) or provisioned inside the same solution (solution-internal)

**Key pattern:** the skill writes only the agent-level `resources/{EscalationName}/resource.json`. `uip solution resources refresh` emits an App binding into `bindings_v2.json` and then hand-writes the four solution-level files (`app/workflow Action/`, `appVersion/`, `package/`, `process/webApp/`) plus two `debug_overwrites.json` entries (`kind: "app"`, `kind: "process"`) automatically. No manual solution-level authoring is required for `actionCenter` channels.

**Inline agents (escalation inside a flow):** still run the full discovery below (including `uip solution resources list --kind App`) and author the `resource.json` the same way — then **also** wire a `uipath.agent.resource.escalation` flow node (see Step 6b). Without the node the escalation is never reached at runtime.

## Discovery

### Step 1 — Scaffold solution and agent (if not already done)

Scaffold per [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Find the Action Center app

Discover the app via `uip solution resources list`. Pick the invocation based on where the app lives:

**External (already deployed in Orchestrator):**

```bash
uip solution resources list --kind App --source remote --search "<APP_NAME>" --output json
```

**Solution-internal (provisioned inside the same solution):**

```bash
# --kind and --search only work with --source remote; list everything, filter .Data[] client-side by Kind == "App".
uip solution resources list --source local --output json
```

The row's `Source` field (`"Local"` or `"Remote"`) determines whether the app is solution-internal or external.

Filter the result for entries whose `Type` is `"Workflow Action"` (Coded / CodedAction types cannot back an escalation today). Each entry carries:

| `resource list` field | Use as |
|-----------------------|--------|
| `Source` | `"Local"` → solution-internal app. `"Remote"` → external app. |
| `Key` | `channel.properties.resourceKey` (also becomes the app resource's `key`) |
| `Name` | `channel.properties.appName` (also propagates as binding `name`) |
| `Folder` | `channel.properties.folderName` — literal value from `uip solution resources list`. External apps return the Orchestrator folder (e.g., `"Shared/Approvals"`); solution-internal apps return `"solution_folder"`. `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. |
| `FolderKey` | folder GUID — used in `debug_overwrites.json` |

`Key` identifies the backing app. `resource list` does not return `systemName`, `deployVersion`, or the action schema — fetch those in Step 3 with `uip solution resources get`.

### Step 3 — Fetch the app's action schema

Pass the `Key` from Step 2 to `uip solution resources get` — one CLI-native call returns the app spec, including the action schema. Works for both external (`Source: "Remote"`) and solution-internal (`Source: "Local"`) apps, even before the app is imported into the solution. Run from the solution directory (or pass `--solution-folder <path>`).

```bash
uip solution resources get <APP_KEY> --output json
```

The `Data.Spec` object carries everything needed to build the channel:

| `Spec` field | Use as |
|--------------|--------|
| `AppSystemName` | the app `systemName` |
| `Name` | `channel.properties.appName` (matches the `Name` from `resources list`) |
| `ActionSchema` | a JSON **string** — `json.loads` it to get `inputs` / `inOuts` / `outputs` / `outcomes` (Step 4) |

`channel.properties.appVersion` (the integer deploy version) is the `version` field of the parsed `ActionSchema` — not `Spec.Version`, which is the package semver (e.g. `"1.0.0"`).

Parsed `ActionSchema` shape:

```jsonc
{
  "version": 1,
  "inputs":   [{ "name": "Content", "type": "System.String", ... }],
  "outputs":  [],
  "inOuts":   [{ "name": "Comment", "type": "System.String", "description": "..." }],
  "outcomes": [{ "name": "approve", "description": "..." }, { "name": "reject", ... }]
}
```

### Step 4 — Build the channel schemas

From the parsed `ActionSchema` (Step 3), construct the channel fields:

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
bash -c 'A="$HOME/.uipath/.auth"; [ -f "$A" ] || A="/.uipath/.auth"; set -a; source "$A"; set +a; echo "$UIPATH_ACCESS_TOKEN" | python3 -c "
import sys, base64, json
tok = sys.stdin.read().strip()
payload = tok.split(\".\")[1]
payload += \"=\" * (-len(payload) % 4)
print(json.loads(base64.urlsafe_b64decode(payload)).get(\"email\"))
"'
```

Use other `type` values (1=UserId, 2=GroupId, 4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName) only when the user explicitly asks for a GUID-based recipient or an asset-backed one — they require additional inputs (user/group GUID from the Identity API, or an asset name).

> **Do not set `displayName` for `type: 3`.** The reference solution omits it; leaving it out results in cleaner rendering in Studio Web.

**`channel.properties.folderName` must be the literal `Folder` from `uip solution resources list`** — the same rule for both external and solution-internal apps. External apps return the Orchestrator folder (e.g., `"Shared/Approvals"`); solution-internal apps return `"solution_folder"`. `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Rule 11.

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
  "isEnabled": true,                                // REQUIRED — must be true, or the escalation is inactive (not defaulted; always set it explicitly)
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
        "resourceKey": "<appId-guid>",              // the `Key` from `uip solution resources list` (== the key passed to `resources get`)
        "appName": "<appName>",                     // `Name` from `uip solution resources list` (== `Spec.Name` from `resources get`)
        "folderName": "Shared/Approvals",           // literal Folder from `uip solution resources list`. External: Orchestrator folder (e.g., "Shared/Approvals"). Solution-internal: "solution_folder". uip agent refresh translates this to folderPath in the App binding inside bindings_v2.json.
        "appVersion": 1,                            // integer — the `version` field of the parsed `Spec.ActionSchema` (NOT `Spec.Version`, the package semver)
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

**`inputSchema` / `outputSchema` derivation from the parsed `ActionSchema`:**
- `channel.inputSchema.properties` = union of `action-schema.inputs[].name` and `action-schema.inOuts[].name` — these are what the human sees in the task form.
- `channel.outputSchema.properties` = union of `action-schema.inOuts[].name` and `action-schema.outputs[].name` — these are what the agent receives back.
- For each property, set `type` by mapping the dotnet type string in the same way as external RPA process tools (`System.String` → `"string"`, `System.Int32`/`Int64`/`Decimal`/`Double` → `"number"`, `System.Boolean` → `"boolean"`, everything else → `"string"`).
- Copy each arg's `description` verbatim when present.
- `inputSchemaDotnetTypeMapping` / `outputSchemaDotnetTypeMapping` preserve the raw dotnet type names keyed by arg name — Studio Web uses these when serialising task payloads.

## Solution-Level Files

**Solution-level files for Action Center escalations are auto-generated.** Unlike external process tools, you do NOT hand-write any solution-level files for an escalation. `uip solution resources refresh` scans agent projects for escalation resources, resolves each `properties.resourceKey` against the Apps API + `publish/versions` + Orchestrator `/odata/Releases` + `GetPackageEntryPointsV2`, and writes all four required files itself:

- `resources/solution_folder/app/workflow Action/<deploymentTitle>.json`
- `resources/solution_folder/appVersion/<title>.json`
- `resources/solution_folder/package/<title>.json`
- `resources/solution_folder/process/webApp/<deploymentTitle>.json`

The fourth file (`process/webApp/...`) backs the app resource's `dependencies[1]: {kind: "Process"}` — without it, Studio Web reports "Resource provisioning failed (#100)" on solution import.

## Walkthrough

### Step 6 — Write the agent-level resource.json

**File:** `<AGENT_NAME>/resources/<EscalationName>/resource.json`

Use the full shape from § Agent-Level Resource Shape above. Generate fresh UUIDs for the top-level `id` AND the channel `id` — do not reuse.

### Step 6b — Inline agents only: wire the escalation flow node

**Skip if the agent is standalone.** If the escalation is on an **inline** agent (embedded in a flow), the `resource.json` alone is never reached at runtime — you MUST also add a `uipath.agent.resource.escalation` flow node connected to the autonomous node's `escalation` handle. Fetch its manifest with `uip maestro flow registry get <…uipath.agent.resource.escalation…> --output json`, then hand the node + edge authoring to the `uipath-maestro-flow` skill (Critical Rule 16 — this skill does not author `.flow` graphs directly). Run Step 7's refresh/validate with `--inline-in-flow` plus `--bindings-target <FlowProjectDir>/bindings_v2.json`. See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).

### Step 7 — Refresh, validate, and refresh solution resources

```bash
# Refresh — regenerates entry-points.json and bindings_v2.json.
uip agent refresh "<AGENT_NAME>" --output json

# Validate — read-only check of agent and resource.json.
uip agent validate "<AGENT_NAME>" --output json

# Refresh solution resources — imports the App binding from bindings_v2.json into the solution.
uip solution resources refresh --output json
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

See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules. Escalation-specific gotchas:

- `properties.folderName` MUST be the literal `Folder` from `uip solution resources list` — same rule for both external and solution-internal apps. External apps carry the Orchestrator folder (e.g., `"Shared/Approvals"`); solution-internal apps carry `"solution_folder"`. `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Rule 11.
- `isEnabled` MUST be `true` — it is not defaulted. An escalation written without it (or with `null`) is inactive and fails validation.
- `recipients` array MUST have at least one entry. Empty uploads but routes nowhere.
- For `type: 3` (email) recipients, do NOT set `displayName`.
- Generate fresh UUIDs for the top-level `id` AND each channel `id`.
- `channel.type` is lowercase `"actionCenter"`.
- Other channel types (`email`, `slack`, `teams`) are runtime-recognized but require manual solution authoring — out of scope today.

## References

- [../../agent-definition.md](../../agent-definition.md) § Messages, § contentTokens (for `taskTitleV2`)
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
