# Escalation Capability (Action Center Human-in-the-Loop)

Escalations hand off agent control to a human via a deployed UiPath Action Center app: the agent pauses, creates a task on the app, and resumes when the human picks an outcome. The escalation is a **node in the `.flow` file** wired to the agent node's `escalation` handle; the full config lives in the escalation node's `inputs`. No `resource.json` is authored — the sidecar artifact (including the entire `channels[]` array) derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)).

This capability covers the **App task** escalation (`type: "app-task"`, backed by an Action Center app) — the variant tenant registries expose today. Quick-form escalations (schema authored inline, no app) and document-validation tasks exist as siblings but are typically not tenant-available (§ Node Type).

## When to Use

- Agent needs human approval, review, or input mid-execution
- An Action Center app (`Workflow Action` or `JS Action`) is already deployed in Orchestrator (external) or provisioned inside the same solution (solution-internal)

For a human checkpoint **between** flow nodes (not inside the agent's reasoning loop), use a flow-level HITL node instead — the escalation fires when the *agent* decides to escalate.

## Node Type

Static variants (no per-target key suffix, unlike process tools):

| Node type | Task type | Notes |
|---|---|---|
| `uipath.agent.resource.escalation.coded-action-app` | `app-task` | **This capability.** Backed by an Action Center app. |
| `uipath.agent.resource.escalation.quick-form` | `quick-form` | Inline `schema` (HitlSchema), no app. Often `AvailableOnTenant: false`. |
| `uipath.agent.resource.escalation` (bare) | `app-task` | Legacy OOTB type; may be absent from tenant registries. Prefer `.coded-action-app`. |

Variant availability is per-tenant — confirm before authoring:

```bash
uip maestro flow registry search "escalation" --output json
```

Pick a `Data[]` entry with `AvailableOnTenant: true`, then fetch its manifest (→ `definitions[]` verbatim, [impl.md § 3](../impl.md#3-manifest-and-definitions-contract)):

```bash
uip maestro flow registry get uipath.agent.resource.escalation.coded-action-app --output json
```

Manifest: `model: {"source": true}` (mint `inputs.source` — validator-required, MST-9265); required input `name`; `inputDefaults` carry the empty skeleton (`type: "app-task"`, `app: null`, `recipients: []`, `_additionalProps`, …).

## Discovery — the Action Center App

### 1. Find the app

**External (already deployed in Orchestrator):**

```bash
uip solution resources list --kind App --source remote --search "<APP_NAME>" --output json
```

**Solution-internal (provisioned inside the same solution):**

```bash
# --kind and --search only work with --source remote; list everything, filter .Data[] client-side by Kind == "App".
uip solution resources list --source local --output json
```

Keep only Action app entries — `Type` `"Workflow Action"` or `"JS Action"` (Coded / CodedAction app types cannot back an escalation). Each entry maps into the node's `app` object:

| `resources list` field | Use as |
|---|---|
| `Key` | `app.resourceKey` |
| `Name` | `app.appName` |
| `Folder` | `app.folderName` — **literal value**. External apps: the Orchestrator folder (e.g. `"Shared/Approvals"`); solution-internal apps: `"solution_folder"`. |

### 2. Fetch the app's action schema

```bash
uip solution resources get <APP_KEY> --output json
```

Works for both external and solution-internal apps, from the solution directory (or `--solution-folder <path>`). `Data.Spec.ActionSchema` is a JSON **string** — parse it to get `inputs` / `inOuts` / `outputs` / `outcomes`:

```jsonc
{
  "version": 1,
  "inputs":   [{ "name": "Content", "type": "System.String", "description": "..." }],
  "outputs":  [],
  "inOuts":   [{ "name": "Comment", "type": "System.String" }],
  "outcomes": [{ "name": "approve" }, { "name": "reject" }]
}
```

`app.appVersion` = the parsed `ActionSchema`'s `version` (integer) — NOT `Spec.Version` (the package semver).

### 3. Build the `app` schemas

From the parsed `ActionSchema`:

- `app.inputSchema.properties` = every `inputs[]` entry + every `inOuts[]` entry (what the human sees in the task form)
- `app.outputSchema.properties` = every `inOuts[]` entry + every `outputs[]` entry (what the agent receives back)
- Per property: map the dotnet type (`System.String` → `"string"`, `System.Int32`/`Int64`/`Decimal`/`Double` → `"number"`, `System.Boolean` → `"boolean"`, other → `"string"`); copy `description` verbatim when present
- `app.inputSchemaDotnetTypeMapping` / `.outputSchemaDotnetTypeMapping` = flat object keyed by arg name, value = the raw dotnet type string
- `outcomeMapping` (node input, not inside `app`) = one key per `outcomes[].name`, value `"continue"` (agent resumes) or `"end"` (agent stops); default every outcome to `"continue"` unless the user says otherwise

> A bare `app` of `{appName, resourceKey, folderName}` passes `flow validate` — but the derived channel then carries **empty schemas**, so the human's task form shows no data and the agent gets nothing back. Always build the full object.

## Recipients

**Mandatory** — `flow validate` rejects an empty list (`ESCALATION_RECIPIENT_REQUIRED`). Default to email recipients (`type: 3`), the simplest form:

```json
"recipients": [{ "type": 3, "value": "user@example.com" }]
```

Ask the user who should receive the task. "Me" / unspecified → the current user's email from the JWT `email` claim:

```bash
bash -c 'A="$HOME/.uipath/.auth"; [ -f "$A" ] || A="/.uipath/.auth"; set -a; source "$A"; set +a; echo "$UIPATH_ACCESS_TOKEN" | python3 -c "
import sys, base64, json
tok = sys.stdin.read().strip()
payload = tok.split(\".\")[1]
payload += \"=\" * (-len(payload) % 4)
print(json.loads(base64.urlsafe_b64decode(payload)).get(\"email\"))
"'
```

Other `type` values (1=UserId, 2=GroupId, 4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName) only when the user explicitly asks — they need extra lookups (user/group GUID, asset name). Do NOT set `displayName` for `type: 3`.

## Escalation Node Shape

Node `inputs` (authoring surface — everything else derives):

| Field | Required | Notes |
|---|---|---|
| `source` | Yes | Lowercase UUIDv4 **you mint** ([planning.md § Identity](../planning.md#identity--mint-the-uuids-yourself)). Validator-enforced (MST-9265). Becomes the derived `resources/<source>/resource.json` id. |
| `name` | Yes | Escalation name the prompt refers to (`ESCALATION_NAME_REQUIRED`). **Name authority: `inputs.name` only** — projection ignores `display.label` for the derived resource name. |
| `description` | No | When the agent should escalate — the LLM decides by this + the system prompt. |
| `type` | No | `"app-task"` (the `inputDefaults` value; also the resolver default). `"quick-form"` / `"document-validation-task"` switch variant semantics — do not set them on a `.coded-action-app` node. |
| `app` | Yes | `{appName, resourceKey, folderName, appVersion, inputSchema, outputSchema, inputSchemaDotnetTypeMapping, outputSchemaDotnetTypeMapping}` — built per § Discovery. Validate enforces presence (`ESCALATION_APP_REQUIRED`); schema completeness is on you. |
| `recipients` | Yes | ≥ 1 entry with a non-empty `value` (`ESCALATION_RECIPIENT_REQUIRED`) — § Recipients. |
| `outcomeMapping` | No | `{"<outcome>": "continue"\|"end"}`, one key per app outcome. `null` in `inputDefaults`; author it (§ Discovery step 3). |
| `_additionalProps` | No | `{taskTitle, priority, labels}`. `taskTitle`: short human-readable label (e.g. `"Approval request"`; `{{ $vars.* }}` tokens allowed). `priority`: `low`\|`medium`\|`high`\|`critical` (anything else falls back to `medium` at projection). `labels`: string tags, `[]` default. |
| `_notifications` | No | Boolean, default `false` → derived channel `properties.isActionableMessageEnabled`. |
| `_appInputs` | No | Author `null` — canvas-UI prefill state, never projected. |

No instance `outputs`, no instance `model` block, **no top-level `bindings[]` rows** (the manifest has no `model.bindings`; escalation app resolution is a packaging concern).

Example (solution-internal app):

```json
{
  "id": "humanReview",
  "type": "uipath.agent.resource.escalation.coded-action-app",
  "typeVersion": "1.1",
  "display": { "label": "HumanReview", "shape": "circle" },
  "inputs": {
    "source": "b4f0d2c8-6a1e-4f7b-9c3d-2e5a8b0d4f61",
    "name": "HumanReview",
    "description": "Escalate uncertain moderation cases to a human reviewer",
    "type": "app-task",
    "app": {
      "appName": "HumanReviewEscalation",
      "resourceKey": "1f2e3d4c-5b6a-4978-8899-aabbccddeeff",
      "folderName": "solution_folder",
      "appVersion": 1,
      "inputSchema": { "type": "object", "properties": { "Content": { "type": "string", "description": "The content under review" }, "Comment": { "type": "string" } } },
      "outputSchema": { "type": "object", "properties": { "Comment": { "type": "string" } } },
      "inputSchemaDotnetTypeMapping": { "Content": "System.String", "Comment": "System.String" },
      "outputSchemaDotnetTypeMapping": { "Comment": "System.String" }
    },
    "recipients": [{ "type": 3, "value": "reviewer@example.com" }],
    "outcomeMapping": { "approve": "continue", "reject": "continue" },
    "_additionalProps": { "taskTitle": "Content review request", "priority": "medium", "labels": [] },
    "_notifications": false,
    "_appInputs": null
  }
}
```

Wire exactly ONE artifact edge — agent `escalation` handle → escalation node `input` (only the agent's `escalation` handle may connect; max 1 connection):

```json
{ "id": "e_agent_esc", "sourceNodeId": "moderator", "sourcePort": "escalation", "targetNodeId": "humanReview", "targetPort": "input" }
```

No sequence edges to/from an escalation node — it is not on the trigger→end path.

## Derived Fields — Never Author

Projection builds the entire delivery layer from the flat node `inputs`; these are not node inputs:

- `channels[]` — the whole array: one `actionCenter` channel assembled from `app` (name = `appName`, schemas, dotnet mappings, channel `properties {appName, resourceKey, folderName, appVersion, isActionableMessageEnabled, actionableMessageMetaData}`), `recipients`, `outcomeMapping`, `_additionalProps` — channel `id` minted at projection
- `taskTitleV2` — contentTokens derived from `_additionalProps.taskTitle`
- `$resourceType: "escalation"`, `escalationType: 0`, `isEnabled`, `isAgentMemoryEnabled`, `governanceProperties`, `referenceKey`, `folderPath`

## Walkthrough

```bash
# 1. Variant availability + node type
uip maestro flow registry search "escalation" --output json

# 2. Manifest — definitions entry (+ inputDefaults skeleton)
uip maestro flow registry get uipath.agent.resource.escalation.coded-action-app --output json

# 3. App identity (external: --kind App --source remote --search; solution-internal: --source local, filter client-side)
uip solution resources list --kind App --source remote --search "<APP_NAME>" --output json

# 4. Action schema (inputs/inOuts/outputs/outcomes; appVersion)
uip solution resources get <APP_KEY> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

5. Add the escalation node per § Escalation Node Shape (mint `inputs.source`; build the full `app` object; collect recipients; map outcomes).
6. Copy the manifest **verbatim** into `definitions[]`.
7. Wire the artifact edge: agent `escalation` → escalation `input`.
8. Update the agent's system prompt: name the escalation by `inputs.name`, state WHEN to escalate (the trigger condition), at most once per run, and what to do with the human's response ([prompting guide](../prompting/autonomous-agent-prompting-guide.md)).

```bash
# 9. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## Gotchas

1. **Definitions-or-nothing law** ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)): an escalation node without its `(type, typeVersion)`-matched `definitions[]` entry fails validate and silently vanishes from the derived agent and the package.
2. **`app.folderName` is the literal `Folder` from `uip solution resources list`** — external apps: the Orchestrator folder (e.g. `"Shared/Approvals"`); solution-internal apps: `"solution_folder"`. Never invent it.
3. **Validate checks app presence, not app completeness.** `{appName, resourceKey, folderName}` alone passes — with empty derived schemas the task form carries no data. Build the full object (§ Discovery step 3).
4. **An escalation the prompt never mentions never fires.** Wiring the node is not enough — the system prompt must state the escalation trigger condition and cap it (at most once per run), or the agent either ignores the human path or loops on it.
5. **`priority` values are `low`/`medium`/`high`/`critical`** — any other string silently falls back to `medium` at projection; validate does not catch it.
6. **`_notifications` IS projected** (→ `isActionableMessageEnabled`), `_appInputs` is NOT (UI-only). Don't confuse the two underscore fields.
7. **Sidecar-era fields are contamination**: `channels`, `$resourceType`, `escalationType`, `isEnabled`, `taskTitleV2` in node `inputs` mark a ported resource.json — the flow form is flat (§ Escalation Node Shape).
8. **The prompt names the escalation by `inputs.name`** — renaming it means updating the prompt.

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [impl.md § Worked Example](../impl.md#8-worked-example--trigger--agent--end--rpa-tool--context) — full flow skeleton to extend
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — escalation trigger conditions + stop criteria
