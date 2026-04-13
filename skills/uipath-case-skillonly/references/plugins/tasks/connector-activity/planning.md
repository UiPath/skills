# Connector Activity Tasks — Planning

Covers three task types that integrate with external services via UiPath Integration Service connectors.

## When to Use Each Type

| Situation | Task type |
|---|---|
| Execute an action on an external system (create record, send message, update ticket) | `execute-connector-activity` |
| Pause and wait until an external event fires (e.g., webhook, polling event) | `wait-for-connector` |
| Invoke an AI agent hosted on an external platform via a connector | `external-agent` |
| Standard UiPath process, agent, or RPA | No — use [standard-io](../standard-io/planning.md) |
| Human approval or review | No — use [action](../action/planning.md) |

## Decision Order

Prefer higher tiers when calling external services:

| Tier | Approach | When to use |
|---|---|---|
| 1 | IS connector activity (`execute-connector-activity`) | A connector exists and its activities cover the use case |
| 2 | Standard-io process that wraps an HTTP call | Connector exists but lacks the specific activity — build a process instead |
| 3 | No connector support | Use a standard-io task calling an API Workflow |

## Prerequisites

- `uip login` required — connector resources only appear in the registry after authentication
- A healthy IS connection must exist for the connector. If none exists, the user must create one in the IS portal before you can proceed.

## What You Need Before Building

| Info | How to find it |
|---|---|
| Connector type ID (`uiPathActivityTypeId`) | `uip case registry search "<keyword>"` — look for connector entries |
| Connection ID | `uip case registry get-connection --key <connectorKey>` |
| Input values (body fields, query params) | Shown by `uip case tasks describe` in Step 2 of impl.md |

## Discovery

```bash
uip case registry pull
uip case registry search "<service name>" --output json
```

Confirm the entry has a connector category. If the connector key fails, list all connectors:

```bash
uip case registry get-connector --key "<connectorKey>" --output json
```

Keys are often prefixed — e.g., `uipath-salesforce-slack` not `slack`.

## Planning Annotation

In the plan, annotate connector tasks as:
- `connector: <service> — <operation>` (e.g., "connector: Jira — create issue")
- If no connector exists, flag in open questions — alternative approaches needed
