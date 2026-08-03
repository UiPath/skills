# Triggers

Triggers are event-based activities that fire when something happens in an external system (e.g., a Salesforce record is created, updated, or deleted). Use trigger metadata to discover which objects and fields are available for each event type.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Contents
- [Trigger Discovery Flow](#trigger-discovery-flow)
- [List Trigger Activities](#list-trigger-activities)
- [Trigger Objects](#trigger-objects)
  - [`parameters[]` — event-parameter input fields](#parameters--event-parameter-input-fields)
- [Object Name Resolution](#object-name-resolution)
- [Trigger Metadata (Describe)](#trigger-metadata-describe)
- [CRUD vs Non-CRUD Triggers](#crud-vs-non-crud-triggers)
- [Response Fields](#response-fields)
- [Building Filter Trees from filterFields](#building-filter-trees-from-filterfields)
- [Webhook URL Retrieval](#webhook-url-retrieval)
- [Happy-Path Example](#happy-path-example)

---

## Trigger Discovery Flow

```
[ ] 1. List trigger activities  →  pick one  →  note its **Operation**
[ ] 2. If Operation is CREATED/UPDATED/DELETED  →  get objects  →  resolve object name (ask user if unclear)
[ ] 3. Describe the resolved object + operation  →  field metadata
```

**Decision point at step 2**: CREATED, UPDATED, and DELETED operations require an intermediate "objects" step. For other trigger operations, skip to step 3 using the activity's **ObjectName**.

> **Source of truth — UNION of both calls.** Event-parameter inputs = `triggers objects → parameters[]` **∪** `triggers describe → EventParameters`. A required field can appear in `describe → EventParameters` while absent from `parameters[]`, so configure every field either source marks `required` — never read inputs from one call alone. `triggers describe` also supplies `FilterFields` (filter tree) and `OutputFields` (downstream `$vars`). Run **both** calls; do not invent parameters or fields, and do not substitute metadata from other commands.

---

## List Trigger Activities

```bash
uip is activities list "<connector-key>" --triggers --output json
```

Returns activities where `isTrigger=true`. The **Operation** field indicates the event type.

---

## Trigger Objects

List objects available for a specific trigger operation:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" --output json

# With connection (includes custom objects):
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --output json
```

- `<OPERATION>` must be **uppercase**: CREATED, UPDATED, DELETED
- Use `--connection-id` for custom/connection-specific objects
- Use `--refresh` to bypass cache

---

## Object Name Resolution

`triggers describe` requires an exact object name. Resolve it from the `triggers objects` response (`Data[].Name`):

1. Match the user's intent against each object's `Name` / `DisplayName` (case-insensitive).
2. Exactly one match → use its `Name` verbatim.
3. No match or ambiguous → **ask the user** — present candidate objects by `displayName`. Do NOT guess or fabricate an object name; `triggers describe` with a wrong name returns empty or wrong field metadata.

For non-CRUD operations there is no objects step — use the trigger activity's **ObjectName** field directly.

> Generic CRUD triggers (e.g. Data Fabric `record-created`) carry no objectName in their flow-node manifest — pass the resolved `Name` as `objectName` when configuring the trigger node (Maestro Flow: `node configure --detail.objectName`).

---

## Trigger Metadata (Describe)

Get field metadata for a trigger object:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --output json
```

Returns field definitions with names, types, and descriptions. Always requests `allFields=true` from the API.

- `<object-name>` comes from [Object Name Resolution](#object-name-resolution) above
- Always pass `--connection-id` — without it, results omit custom/connection-specific fields
- The returned fields are the **source of truth** for the trigger's field metadata. Use them verbatim — do not guess field names

---

## CRUD vs Non-CRUD Triggers

| Operation type | Objects step required? | How to get object name |
|---|---|---|
| **CREATED / UPDATED / DELETED** | Yes — run `triggers objects` first | From the objects list response |
| **Other** (custom events) | No — skip objects step | From the trigger activity's **ObjectName** field |

---

## Response Fields

### Trigger Activities (from `activities list --triggers`)

| Field | Description |
|---|---|
| **`Name`** | Activity identifier |
| `DisplayName` | Human-readable name |
| **`ObjectName`** | Object this trigger operates on (use directly for non-CRUD triggers) |
| **`Operation`** | Event type: CREATED, UPDATED, DELETED, or custom |
| `IsCurated` | Whether this is a curated activity |

### Trigger Objects (from `triggers objects`)

Array of objects — each has a **name** to use in the describe command. Also includes:

| Field | Description |
|---|---|
| `name` | Object name (use in describe command) |
| `displayName` | Human-readable name |
| `byoaConnection` | `true` if this event requires a BYOA connection |
| `isWebhookUrlVisible` | `true` if the webhook URL should be shown to the user |
| `eventMode` | `"webhooks"` or `"polling"` — how the trigger receives events |
| **`parameters[]`** | Object/query/path-scoped input fields for this trigger — see below. **Merge with `triggers describe → EventParameters`** for the complete set. |

#### `parameters[]` — event-parameter input fields

One entry per configure-time input field (repo, channel, shared mailbox). **Not complete on its own** — `triggers objects → parameters[]` carries object/query/path-scoped inputs, while event-config inputs come from `triggers describe → EventParameters`. The full input set is the **union**; a field is required if either source marks it `required`. Never read inputs from `parameters[]` alone.

| Field | Description |
|---|---|
| `name` | Field name — pass as a key inside the `--detail` bucket selected by `type` (see below) |
| `displayName` | Human-readable label — use when prompting the user |
| `dataType` | Value type (`string`, `number`, `boolean`, …) |
| `required` | `true` → must be supplied before configure; `false` → optional |
| `description` | Field hint (often suitable to surface verbatim when asking the user) |
| `reference` | Present → field is a lookup ID. Resolve via `uip is resources run list "<connector-key>" "<reference.objectName>" --connection-id "<id>"` before configure (IDs are connection-scoped). |
| `design.position` | `"primary"` → top-level input shown in the trigger card. Other positions are layout hints — ignore for configure. |
| `type` | Bucket selector for `node configure --detail`: `"query"` → `queryParameters`, `"path"` → `pathParameters`, otherwise → `eventParameters`. Each bucket is a JSON object keyed by `name`. |

### Trigger Metadata (from `triggers describe`)

Object with field definitions. Structure varies by connector but typically returns three arrays plus mode flags:

| Field | Description |
|---|---|
| `EventParameters` | Event-config input fields. **First-class event parameters** — merge with `triggers objects → parameters[]`; configure every entry marked `required`. Resolve `reference` fields via `uip is resources run list` before configure. |
| `FilterFields` | Fields usable in the optional `filter` tree |
| `OutputFields` | Event payload schema — field names for downstream `$vars.{triggerId}.output.*` |
| `eventMode` | `"webhooks"` or `"polling"` |
| `byoaConnection` | `true` if this trigger requires a BYOA connection |
| `isWebhookUrlVisible` | `true` if the webhook URL should be shown |

> **`triggers describe → EventParameters` is NOT "output-only" metadata.** It carries required *input* parameters that `triggers objects → parameters[]` frequently omits. Always merge both responses and configure the union — see the Source-of-truth note above. `flow registry get`'s `eventParameters.fields` mirrors `describe` and is the offline fallback.

---

## Building Filter Trees from filterFields

Trigger filters narrow which events fire the trigger (e.g. only emails from a specific sender). They are authored as a **structured tree**, not a JMESPath string — the CLI compiles the tree into the runtime `filterExpression` using the same logic Studio Web does, and writes both forms into the workflow so the trigger round-trips cleanly when re-opened in SW. **Do not pass `filterExpression` directly** — the validator rejects it.

### Steps

These steps assume the consuming skill has already loaded the trigger's `filterFields.fields` array (the source command varies by surface — e.g. maestro-flow uses `flow registry get`).

1. For each user-intent condition, pick a matching `name` from `filterFields.fields` — using an unknown field name will be rejected by the CLI at configure time.
2. Choose an operator based on the user's intent and the field type (see the operator table in the consuming skill — e.g. [uipath-maestro-flow > connector-trigger](../../../uipath-maestro-flow/references/author/references/plugins/connector-trigger/impl.md#supported-operators)).
3. Build one leaf per condition; place multiple conditions under the same `groupOperator` (`0` for AND, `1` for OR).
4. If you need mixed AND/OR logic, use nested `groups` (same shape as the root tree).
5. **Wrap string values in a `value` object** with `value`, `rawString` (verbatim user-entered text including quotes for strings), and `isLiteral: true` — passing a bare string fails validation. Expression values (`isLiteral: false`) are not yet supported by the CLI port.
6. If `filterFields` is empty or absent, the trigger does not support filtering — omit `filter` entirely. Do not invent an "empty" expression.

### Mandatory filter parameters

Some triggers carry **mandatory event-parameter filters** the connector requires for subscription (e.g. Gmail Email Received always filters by folder; Slack message triggers filter by channel). These are **not** authored as freeform `filter` leaves. Set the value through `eventParameters` — the CLI runs it and AND-joins the result into the runtime `filterExpression` written at the **top level of the node's `inputs.detail`**. 

### Array-shaped fields

When `filterFields[].name` contains a `[*]` segment (e.g. `tags[*]`, `ParentFolders[*].ID`), the CLI emits filter-projection JMESPath instead of scalar comparison: `(tags[?@=='urgent'])`, `(ParentFolders[?ID=='INBOX'])`. Reference the field by its full schema name in the leaf `id` — the projection syntax is generated, not authored.

---

## Webhook URL Retrieval

When a trigger uses `eventMode: "webhooks"`, the webhook URL must be retrieved and registered on the customer's external service. Without this step, the trigger will never fire.

### When to retrieve the webhook URL

- `eventMode: "webhooks"` (from `triggers describe` or `triggers objects`)
- `isWebhookUrlVisible: true` for the matching event object. When `false`, **skip retrieval** — the connector manages webhook registration automatically and does not expose a URL.
- Independent of `byoaConnection` — applies whether BYOA is required or not.

### How to retrieve the webhook URL

1. Get the `ElementInstanceId` from the connection:

   ```bash
   uip is connections list "<connector-key>" --connection-id "<id>" --output json
   ```

   Empty `ElementInstanceId` means the connection is the wrong type for webhooks. Check the `byoaConnection` flag on the matching event — if `true`, switch to a BYOA connection.

2. Retrieve the webhook URL:

   ```bash
   uip is webhooks config "<connector-key>" \
     --connection-id "<connection-guid>" \
     --element-instance-id <number> \
     --output json
   ```

3. The response contains the `WebhookUrl`. Present it to the user with registration instructions:
   - **Prefer `design.textBlocks`** from the `triggers objects` response if present — it carries connector-specific text (e.g., "Add this URL to your Slack app's Event Subscriptions"). Substitute `{webhookUrl}` with the actual value.
   - **Otherwise** use a generic message: register the URL in the external service's app settings (e.g., Slack Event Subscriptions, Salesforce Outbound Messages). The trigger does not fire until the URL is registered and verified by the external service.

---

## Happy-Path Example

```bash
# 1. List trigger activities for Salesforce
uip is activities list "uipath-salesforce-sfdc" --triggers --output json
# → Operations: CREATED, UPDATED, DELETED
# → User selects CREATED

# 2. Get objects for CREATED operation
uip is triggers objects "uipath-salesforce-sfdc" CREATED \
  --connection-id "228624" --output json
# → [AccountHistory, Contact, Lead, Opportunity, ...]
# → User picks "AccountHistory"

# 3. Get field metadata for AccountHistory
uip is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" \
  --connection-id "228624" --output json
# → Returns field definitions with types and descriptions
```

### Non-CRUD Trigger Example

```bash
# 1. List trigger activities
uip is activities list "uipath-some-connector" --triggers --output json
# → Name: "custom_event_trigger", Operation: "WEBHOOK", ObjectName: "WebhookPayload"

# 2. Skip objects step — go directly to describe using ObjectName
uip is triggers describe "uipath-some-connector" "WEBHOOK" "WebhookPayload" \
  --connection-id "<id>" --output json
# → Returns field definitions
```
