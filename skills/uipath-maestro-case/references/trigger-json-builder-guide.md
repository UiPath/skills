# Trigger JSON Builder Guide

This reference describes how to build the trigger node JSON data for each supported trigger type in a case management JSON file. The parent skill invokes this procedure when adding triggers to a case.

## Overview

Building a trigger involves:

1. **Generate trigger node** — Create the base node with ID, position, and label
2. **Populate `data.uipath`** — Set the trigger-type-specific data body (timer config, event enrichment, or empty for manual)
3. **Register outputs as root variables** — For event triggers, push outputs to `root.data.uipath.variables.inputOutputs[]`

## Trigger Types

| Type | CLI command | `serviceType` | Description |
|---|---|---|---|
| Manual | `add-manual` | None (no `uipath` block) | Started manually, no automation |
| Timer | `add-timer` | `Intsvc.TimerTrigger` | Fires on a time schedule |
| Event | `add-event` | `Intsvc.EventTrigger` | Fires when a connector event occurs |

---

## Base Trigger Node

All trigger types share this base structure:

```json
{
  "id": "trigger_<6-random-chars>",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 200 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "<display name>"
  }
}
```

### ID Generation

- Trigger ID: `trigger_` prefix + 6 random alphanumeric chars (e.g., `trigger_3WkF0Q`)

### Positioning

- First trigger: `{ x: -100, y: 200 }`
- Each additional trigger: same x, y incremented by 140 (e.g., 200, 340, 480, ...)

### Display Name

- If provided, use it as `data.label`
- If not provided, auto-generate as `"Trigger N"` where N = existing trigger count + 1

---

## Manual Trigger

No `data.uipath` block. The base node is the complete trigger.

```json
{
  "id": "trigger_AbCdEf",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 200 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "Trigger 1"
  }
}
```

---

## Timer Trigger

Set `data.uipath` with timer configuration:

```json
{
  "id": "trigger_AbCdEf",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 200 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "Every 5 minutes",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeCycle",
      "timeCycle": "R/PT5M"
    }
  }
}
```

### Time Cycle Format

ISO 8601 repeating interval: `R[count]/[start]/duration`

| Example | Meaning |
|---|---|
| `R/PT1S` | Every 1 second, infinite |
| `R/PT5M` | Every 5 minutes, infinite |
| `R/PT1H` | Every 1 hour, infinite |
| `R3/PT10S` | Every 10 seconds, 3 times |
| `R/2026-04-26T10:40:00.000-07:00/PT1H` | Every hour starting at a specific time |

Duration units: `S` (seconds), `M` (minutes), `H` (hours), `D` (days), `W` (weeks).

No bindings or outputs. No enrichment needed.

---

## Event Trigger (Connector)

The most complex trigger type. Requires enrichment from the connector API.

### Build Procedure

1. Generate base trigger node
2. Fetch enrichment via `uip case tasks describe --type connector-trigger --id <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> --output json`
3. Build `data.uipath` with context, inputs, and outputs
4. Root variable registration is handled by `global-variable-guide.md`

### Trigger Node JSON Structure

```json
{
  "id": "trigger_3WkF0Q",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 200 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "Jira Issue Created",
    "uipath": {
      "serviceType": "Intsvc.EventTrigger",
      "context": [
        { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
        { "name": "connection", "value": "=bindings.bYrtrMEvs", "type": "string" },
        { "name": "resourceKey", "value": "0d93ddc9-a512-4b60-8483-4a3a8fbee20e", "type": "string" },
        { "name": "folderKey", "value": "=bindings.bePaAIvP8", "type": "string" },
        { "name": "operation", "value": "ISSUE_CREATED", "type": "string" },
        { "name": "objectName", "value": "curated_get_issue", "type": "string" },
        { "name": "method", "type": "string" },
        { "name": "path", "type": "string" },
        {
          "name": "metadata",
          "type": "json",
          "body": {
            "activityMetadata": { "activity": { "...TypeCache entry..." } },
            "designTimeMetadata": {
              "connectorLogoUrl": "icons/...",
              "activityConfig": { "isCurated": true, "operation": "ISSUE_CREATED" }
            },
            "telemetryData": {
              "connectorKey": "uipath-atlassian-jira",
              "connectorName": "Jira",
              "operationType": "",
              "objectName": "curated_get_issue",
              "objectDisplayName": "curated get issue",
              "primaryKeyName": ""
            },
            "inputMetadata": {},
            "errorState": { "hasError": false },
            "activityPropertyConfiguration": {
              "objectName": "curated_get_issue",
              "eventType": "ISSUE_CREATED",
              "eventMode": "polling",
              "configuration": "=jsonString:{...}",
              "uiPathActivityTypeId": "<uuid>",
              "errorState": { "issues": [] }
            }
          }
        }
      ],
      "inputs": [
        {
          "name": "body",
          "type": "json",
          "target": "body",
          "body": {
            "filters": { "expression": "" },
            "parameters": { "project": "", "issuetype": "" }
          },
          "var": "vRaNdOmId",
          "id": "vRaNdOmId"
        }
      ],
      "outputs": [
        {
          "name": "response",
          "displayName": "Issue Created",
          "type": "jsonSchema",
          "source": "=response",
          "_jsonSchema": null,
          "var": "response",
          "value": "response"
        },
        {
          "name": "Error",
          "displayName": "Error",
          "type": "jsonSchema",
          "source": "=Error",
          "_jsonSchema": null,
          "var": "error",
          "value": "error"
        }
      ],
      "bindings": []
    }
  }
}
```

### Key Differences from Connector Tasks in Stages

Trigger node outputs are **simplified** compared to task outputs:
- No `body` — the JSON schema lives in root `inputOutputs`, not on the trigger node
- No `elementId` — trigger inputs/outputs don't carry elementId
- No `id` or `target` on outputs
- `_jsonSchema` is always `null` on the trigger node (schema is on the root variable instead)

### Trigger Inputs

- Inputs strip `elementId` (present on task inputs, absent on trigger inputs)
- Single `body` input with `filters.expression` and `parameters` from event params

### Connector Binding Construction

Same pattern as connector tasks in `task-json-builder-guide.md`. Dedup against existing `root.data.uipath.bindings[]`.

1. Check dedup: does a ConnectionId binding with the same (`default`, `resource: "Connection"`, `resourceKey`) already exist?
2. If found, reuse the existing binding ID. If not, create a new ConnectionId binding and push to root
3. Same dedup check for FolderKey binding
4. Set context `connection` and `folderKey` to `=bindings.<id>` references

The trigger node itself has `bindings: []` (trigger-level, always empty — bindings go to root).
