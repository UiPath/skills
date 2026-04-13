# Wait-for-Connector Task — Planning

Pauses a stage until an external connector event fires (e.g., wait for a Salesforce record update, a ServiceNow ticket status change).

## When to Use

| Situation | Use wait-for-connector? |
|---|---|
| Stage should pause until an external system event occurs | Yes |
| Execute an action on an external system | No — use [execute-connector-activity](../execute-connector-activity/planning.md) |
| Trigger the entire case on an external event | No — use [connector-trigger](../../triggers/connector-trigger/planning.md) |

## Prerequisites

- `uip login` required
- A healthy IS connection must exist for the connector

## What You Need

| Info | How to find it |
|---|---|
| Connector trigger type ID | `uip case registry search "<service name> trigger"` |
| Connection ID | `uip case registry get-connection --key <connectorKey>` |
| Event parameters | `uip case tasks describe --type connector-trigger --id <typeId> --connection-id <id>` |

## Discovery

```bash
uip case registry search "<service name> trigger" --output json
uip case registry get-connection --key <connectorKey> --output json
```
