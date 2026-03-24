# Triggers

Triggers are event-based activities that fire when something happens in an external system (e.g., a Salesforce record is created, updated, or deleted). Use trigger metadata to discover which objects and fields are available for each event type.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Contents
- [Trigger Discovery Flow](#trigger-discovery-flow)
- [List Trigger Activities](#list-trigger-activities)
- [Trigger Objects](#trigger-objects)
- [Trigger Metadata (Describe)](#trigger-metadata-describe)
- [CRUD vs Non-CRUD Triggers](#crud-vs-non-crud-triggers)
- [Response Fields](#response-fields)
- [Happy-Path Example](#happy-path-example)

---

## Trigger Discovery Flow

```
[ ] 1. List trigger activities  →  pick one  →  note its **Operation**
[ ] 2. If Operation is CREATED/UPDATED/DELETED  →  get objects  →  pick one
[ ] 3. Get metadata (fields) for the chosen object + operation
```

**Decision point at step 2**: CREATED, UPDATED, and DELETED operations require an intermediate "objects" step. For other trigger operations, skip to step 3 using the activity's **ObjectName**.

---

## List Trigger Activities

```bash
uip is activities list "<connector-key>" --triggers --format json
```

Returns activities where `isTrigger=true`. The **Operation** field indicates the event type.

---

## Trigger Objects

List objects available for a specific trigger operation:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" --format json

# With connection (includes custom objects):
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --format json
```

- `<OPERATION>` must be **uppercase**: CREATED, UPDATED, DELETED
- Use `--connection-id` for custom/connection-specific objects
- Use `--refresh` to bypass cache

---

## Trigger Metadata (Describe)

Get field metadata for a trigger object:

```bash
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" --format json

# With connection (includes custom fields):
uip is triggers describe "<connector-key>" "<OPERATION>" "<object-name>" \
  --connection-id "<id>" --format json
```

Returns field definitions with names, types, and descriptions. Always requests `allFields=true` from the API.

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

Array of objects — each has a **name** to use in the describe command.

### Trigger Metadata (from `triggers describe`)

Object with field definitions. Structure varies by connector but typically includes field names, types, display names, and descriptions.

---

## Happy-Path Example

```bash
# 1. List trigger activities for Salesforce
uip is activities list "uipath-salesforce-sfdc" --triggers --format json
# → Operations: CREATED, UPDATED, DELETED
# → User selects CREATED

# 2. Get objects for CREATED operation
uip is triggers objects "uipath-salesforce-sfdc" CREATED \
  --connection-id "228624" --format json
# → [AccountHistory, Contact, Lead, Opportunity, ...]
# → User picks "AccountHistory"

# 3. Get field metadata for AccountHistory
uip is triggers describe "uipath-salesforce-sfdc" CREATED "AccountHistory" \
  --connection-id "228624" --format json
# → Returns field definitions with types and descriptions
```

### Non-CRUD Trigger Example

```bash
# 1. List trigger activities
uip is activities list "uipath-some-connector" --triggers --format json
# → Name: "custom_event_trigger", Operation: "WEBHOOK", ObjectName: "WebhookPayload"

# 2. Skip objects step — go directly to describe using ObjectName
uip is triggers describe "uipath-some-connector" "WEBHOOK" "WebhookPayload" \
  --connection-id "<id>" --format json
# → Returns field definitions
```
