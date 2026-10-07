# Escalation Guardrails (`escalate` Action)

Creates a task in an Action Center app for human review. The `escalate` action is available on both `builtInValidator` and `custom` guardrails. Base guardrail fields, selector scoping, validator discovery, and the other actions (`block`, `log`, `filter`) are in [guardrails.md](guardrails.md) — read its Overview and Walkthrough first. This guide owns the escalate action schema, the step-by-step workflow, and the worked example.

## escalate action schema

**Minimum required from user:** app name + recipient (email is the simplest form).

```json
"action": {
  "$actionType": "escalate",
  "app": {
    "id": "<Key from uip solution resources list --kind App>",
    "name": "<app Name>",
    "version": "0",
    "folderName": "<Folder from uip solution resources list --kind App>"
  },
  "recipient": {
    "type": 3,
    "value": "reviewer@example.com"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"escalate"` | Yes | Action discriminator |
| `app.id` | string | Yes | App deployment ID — the `Key` field from `uip solution resources list --kind App` |
| `app.name` | string | Yes | Action Center app name — the `Name` field from `uip solution resources list --kind App` |
| `app.version` | string | Yes | Always `"0"` for solution-embedded apps |
| `app.folderId` | string | No | Omit — not used by validate |
| `app.folderName` | string | Yes | Literal Orchestrator folder — the `Folder` field from `uip solution resources list --kind App` (e.g., `"Shared"`, `"Shared/Approvals"`). `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. |
| `app.appProcessKey` | string | No | Omit — only used in advanced scenarios |
| `recipient.type` | integer | Yes | Recipient kind — see shapes below: 1=UserId, 2=GroupId, 3=UserEmail, 4=AssetUserEmail, 5=GroupName, 6=AssetGroupName, 7=ArgumentEmail, 8=ArgumentGroupName |
| `recipient.*` | — | — | Remaining fields depend on `type` — see recipient shapes below |

**Recipient shapes (discriminated by `type`):**

**Types 1, 2, 3, 5 — StandardRecipient** (UserId, GroupId, UserEmail, GroupName)

```json
{ "type": 3, "value": "reviewer@example.com" }
{ "type": 1, "value": "<user-guid>", "displayName": "Jane Doe" }
{ "type": 5, "value": "ReviewersGroup" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `value` | Yes | User GUID (type 1), group GUID (type 2), email address (type 3), group name string (type 5) |
| `displayName` | No | Recommended for type 1 (UserId); omit for types 2, 3, 5 |

**Types 4, 6 — AssetRecipient** (AssetUserEmail, AssetGroupName)

Resolves the email or group name from an Orchestrator asset at runtime — do NOT use `value`.

```json
{ "type": 4, "assetName": "ReviewerEmailAsset", "folderPath": "Shared" }
{ "type": 6, "assetName": "ReviewGroupAsset", "folderPath": "Shared/MyTeam" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `assetName` | Yes | Name of the Orchestrator asset holding the email or group value |
| `folderPath` | Yes | Fully-qualified Orchestrator folder path where the asset lives |

**Types 7, 8 — ArgumentRecipient** (ArgumentEmail, ArgumentGroupName)

Resolves the email or group name from the agent's input arguments at runtime — do NOT use `value`.

```json
{ "type": 7, "argumentName": "user.email" }
{ "type": 8, "argumentName": "team.groupName" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `argumentName` | Yes | Dot-path into the agent's input schema (e.g. `"user.email"`, `"reviewerEmail"`) |

Prefer `type: 3` (UserEmail) when adding manually — it requires no GUID or asset lookup. Studio Web uses `type: 1` (UserId) when a user is selected via the UI.

## Adding an escalation guardrail — step-by-step

<!--skill-flavor:scaffolding-gate:start-->
**Scaffolding gate (MANDATORY):** when the request includes creating a solution
or agent, run both `uip solution init` and `uip agent init` before app discovery.
An incompatible or missing escalation app rejects only the guardrail; it does
not cancel the requested local solution and agent scaffolding.
<!--skill-flavor:scaffolding-gate:end-->

**Step 0 — Discover available validators (MANDATORY — do not skip even when validator type is already known):**

```bash
uip agent guardrails list --output json
```

Confirm the target validator is listed. Record the exact parameter `id` values and `$parameterType` tags from the output — these must match precisely in the guardrail JSON. Skipping this step leads to invalid parameter shapes.

**Step 1 — Discover the app** using `--kind App` from the solution root:

```bash
uip solution resources list --kind App --source remote --search "<app-name>" --output json
```

Filter results for `"Type": "Workflow Action"`. Use these three fields from the result:

| Resource list field | Maps to `app.*` field |
|---------------------|----------------------|
| `Key` | `app.id` |
| `Name` | `app.name` |
| `Folder` | `app.folderName` (literal, e.g., `"Shared"`) |

`app.version` is always `"0"` — that's a fixed value, not derived from the `resource list` row. `app.folderName` carries the literal `Folder` and `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. Do not use `FolderKey` for any `app.*` field.

If multiple entries share the same name in different folders, ask the user which deployment to use.

Example entry:
```json
{
  "Source": "Remote",
  "Key": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
  "Name": "Tool.Guardrail.Escalation.Action.App",
  "Kind": "app",
  "Type": "Workflow Action",
  "Folder": "Shared",
  "FolderKey": "627fe423-5c73-464a-abff-41fdaad6ac19"
}
```

> **Important:** Do NOT use `--kind Process` with `Type: "webApp"` to find Action Center apps. Those entries are the code-behind processes — their `Key` values are process release GUIDs, not app deployment IDs. Using them as `app.id` will cause runtime resolution failures.

**Step 1 completion gate — both branches MUST run `resources get`:**

- Exact app row found: immediately run
  `uip solution resources get "<Key from the row>" --output json`.
- No exact app row/key found: immediately run
  `uip solution resources get "<requested app name>" --output json` once and
  treat its failure as `GET_ERROR`.

Do not edit files, refresh, validate, or respond to the user between
`resources list` and this required `resources get` attempt. A missing catalog
row is not a completed schema check and is never permission to skip the
command.

**Step 2 — Verify the app exposes the guardrail action-schema contract** (do this **before** writing the guardrail JSON — an incompatible app must be rejected, not authored).

**Required command gate:** execute
`uip solution resources get "<Key from Step 1>" --output json` for the selected
app before deciding whether it is compatible. The `resources list` row is not
an action schema and cannot replace this command. Do not write or reject the
guardrail until the returned action schema has been checked.

A guardrail escalation app must expose a specific action-schema contract. If verification fails, stop and report to the user: `<APP_NAME> does not have the required action schema configuration for tool guardrails.` (replace `<APP_NAME>` with the app's `Name` from Step 1). Do NOT write the guardrail.

`uip solution resources get` returns the app's action schema in one CLI-native call — no auth handling, no Apps API endpoints. Pipe its output into a verifier that confirms every required argument name. The CLI handles authentication, so Claude never touches the auth file or the token.

```bash
cat > /tmp/verify_escalation_app.py <<'PY'
import sys, json
data = json.load(sys.stdin)
if data.get("Result") != "Success":
    sys.exit("GET_ERROR: uip solution resources get failed: " + str(data.get("Message", "unknown error")))
raw = data.get("Data", {}).get("Spec", {}).get("ActionSchema")
if not raw:
    sys.exit("NO_SCHEMA: app spec has no ActionSchema — not a deployed Workflow Action app")
sch = json.loads(raw)
need = {"inputs": {"GuardrailName", "GuardrailDescription", "TenantName", "AgentTrace", "Tool", "ExecutionStage", "ToolInputs", "ToolOutputs"},
        "outputs": {"ReviewedInputs", "ReviewedOutputs", "Reason"},
        "outcomes": {"Approve", "Reject"}}
miss = {k: sorted(v - {x["name"] for x in sch.get(k, [])}) for k, v in need.items() if v - {x["name"] for x in sch.get(k, [])}}
print("OK" if not miss else "MISSING: " + json.dumps(miss))
sys.exit(0 if not miss else 1)
PY
uip solution resources get "<Key from Step 1>" --output json | python3 /tmp/verify_escalation_app.py
```

Decision rule — the verifier exits 0 (`OK`) or 1 (with a tagged reason). All exit-1 cases mean **do NOT write the guardrail**:

| Verifier output | Meaning | Action |
|-----------------|---------|--------|
| exit 0, `OK` | Contract satisfied | Proceed to Step 3 |
| exit 1, `MISSING: {...}` | App exists but its action schema is missing required argument names | Stop. Report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` |
| exit 1, `NO_SCHEMA: ...` | The resource has no action schema — not a deployed Workflow Action app | Stop. Report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` |
| exit 1, `GET_ERROR: ...` | `uip solution resources get` failed (app not found, no access, or CLI error) | Stop. Report `<APP_NAME> could not be verified for the required action schema configuration.` **Do NOT re-authenticate or try alternate endpoints** — a single failed verifier call is terminal for this run |

The check is **name-only** (types, `required` flags, `isList` are not checked); the app may carry extra arguments beyond these:

| Category | Required names |
|----------|---------------|
| `inputs` (8) | `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`, `ToolInputs`, `ToolOutputs` |
| `outputs` (3) | `ReviewedInputs`, `ReviewedOutputs`, `Reason` |
| `outcomes` (2) | `Approve`, `Reject` |

**Step 3 — Construct and add the escalate action** in `agent.json`'s `guardrails` array (only after Step 2 passed):

```json
{
  "$actionType": "escalate",
  "app": {
    "id": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
    "name": "Tool.Guardrail.Escalation.Action.App",
    "version": "0",
    "folderName": "Shared"
  },
  "recipient": { "type": 3, "value": "reviewer@example.com" }
}
```

`app.id`, `app.name`, and `app.folderName` come from Step 1 (`Key`, `Name`, `Folder` respectively). `app.version` is always `"0"` — fixed value for solution-embedded apps.

**Step 4 — Generate solution resource files**

Run from the solution root:

```bash
uip agent refresh   <AgentName> --output json
uip agent validate  <AgentName> --output json
uip solution resources refresh   --output json
```

- `refresh` regenerates `entry-points.json` and `bindings_v2.json` with a `resource: "app"` binding for the escalation app. The binding carries both `name` (from `app.name`) and `folderPath` (translated from `app.folderName`).
- `validate` is a read-only check. Fails with `AgentValidationOutdated` if refresh is needed.
- `solution resources refresh` reads `bindings_v2.json`, fetches the app from the Resource Catalog Service using the joint `(name, folderPath)` key, and generates all 4 solution-level resource files (`app/workflow Action/`, `appVersion/`, `package/`, `process/webApp/`) plus the `debug_overwrites.json` entries for both the app and its code-behind process.

**Step 5 — Upload:**

```bash
uip solution upload . --output json
```

## Example: Escalate PII Violations to Action Center — Multiple Tool Targets

Escalates to an Action Center app when email or credit card PII is detected at the agent level. `app.id`, `app.name`, and `app.folderName` come from `uip solution resources list --kind App`.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "10d5f10f-da4e-4bf1-ace9-dd880e33d9be",
  "name": "PII Email and Credit Card escalation guardrail",
  "description": "Detects email addresses and credit card numbers, escalates to human review",
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "CreditCardNumber"]
    },
    {
      "$parameterType": "map-enum",
      "id": "entityThresholds",
      "value": {
        "Email": 0.5,
        "CreditCardNumber": 0.5
      }
    }
  ],
  "action": {
    "$actionType": "escalate",
    "app": {
      "id": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
      "name": "Tool.Guardrail.Escalation.Action.App",
      "version": "0",
      "folderName": "Shared"
    },
    "recipient": {
      "type": 3,
      "value": "reviewer@example.com"
    }
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent"]
  }
}
```

`app.id`, `app.name`, and `app.folderName` are sourced from Step 1 (`resource list` → `Key`, `Name`, `Folder`). `app.version` is always `"0"`.

## References

- [guardrails.md](guardrails.md) — base guardrail schema, selector scoping, built-in validators, walkthrough
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical low-code rules and guardrail anti-patterns
