# External Agent Task — Planning

Invokes an **AI agent hosted on an external platform** via a UiPath Integration Service connector (e.g., an agent running on Azure, AWS Bedrock, or a third-party AI platform).

## When to Use

| Situation | Use external-agent? |
|---|---|
| Invoke an AI agent hosted outside UiPath via a connector | Yes |
| Run a UiPath-published AI agent | No — use [agent](../agent/planning.md) |
| Execute a non-AI action on an external system | No — use [execute-connector-activity](../execute-connector-activity/planning.md) |

## Prerequisites

- `uip login` required
- A healthy IS connection must exist for the external agent connector

## What You Need

| Info | How to find it |
|---|---|
| External agent connector type ID | `uip case registry search "<agent name>"` |
| Connection ID | `uip case registry get-connection --key <connectorKey>` |
| Input/output schema | `uip case tasks describe --type connector-activity --id <typeId> --connection-id <id>` |

## Discovery

```bash
uip case registry search "<external agent service>" --output json
uip case registry get-connection --key <connectorKey> --output json
```
