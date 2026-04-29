# Execute Connector Activity Task — Planning

Executes an action on an external system via a UiPath Integration Service connector (e.g., create a Jira issue, send a Slack message, update a Salesforce record).

## When to Use

| Situation | Use execute-connector-activity? |
|---|---|
| Execute an action on an external system with a pre-built IS connector | Yes |
| Wait for an inbound event from an external system | No — use [wait-for-connector](../wait-for-connector/planning.md) |
| Invoke an AI agent on an external platform | No — use [external-agent](../external-agent/planning.md) |
| External system has no IS connector | No — wrap an HTTP call in an api-workflow process instead |

## Prerequisites

- `uip login` required
- A healthy IS connection must exist for the connector

## What You Need

| Info | How to find it |
|---|---|
| Connector type ID | `uip case registry search "<service name>"` |
| Connection ID | `uip case registry get-connection --key <connectorKey>` |
| Required input fields | `uip case tasks describe --type connector-activity --id <typeId> --connection-id <id>` |

## Discovery

```bash
uip case registry search "<service name>" --output json
uip case registry get-connection --key <connectorKey> --output json
```
