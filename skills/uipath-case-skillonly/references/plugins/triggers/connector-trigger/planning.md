# Connector Trigger — Planning

A connector trigger starts a case automatically when an external event fires (e.g., a new Salesforce record, a ServiceNow ticket update, a webhook from Jira).

## When to Use

| Situation | Use connector trigger? |
|---|---|
| Case starts when an external system event occurs | Yes |
| Case starts on a schedule | No — use [timer trigger](../timer/planning.md) |
| Case starts manually by a user | No — use [manual trigger](../manual/impl.md) |

## Decision Order

| Tier | Trigger type | When to use |
|---|---|---|
| 1 | IS connector trigger (this plugin) | A connector exists and supports the event you need |
| 2 | Timer trigger + polling process | No event trigger exists, but you can poll on a schedule |
| 3 | Manual trigger | Case started on demand by user or API call |

## Prerequisites

- `uip login` required — connector trigger types only appear after authentication
- A healthy IS connection must exist for the connector. If none exists, the user must create one before proceeding.
- The connector must support event triggers (not all connectors do)

## What You Need Before Building

| Info | How to find it |
|---|---|
| Connector trigger type ID (`uiPathActivityTypeId`) | `uip case registry search "<keyword> trigger"` |
| Connection ID | `uip case registry get-connection --key <connectorKey>` |
| Event parameters (if any) | Shown by `uip case tasks describe --type connector-trigger` |
| Filter expression (optional) | JMESPath filter to limit which events fire the trigger |

## Discovery

```bash
uip case registry pull
uip case registry search "<service name> trigger" --output json
uip case registry get-connection --key "<connectorKey>" --output json
```

## Event Modes

Connectors operate in one of two modes, determined by the connector (not configurable):

| Mode | Behaviour |
|---|---|
| `polling` | Runtime polls the service on an interval — slight delay between event and trigger |
| `webhooks` | Connector registers a webhook — events fire in near-real-time |

Note the event mode in the plan for the user's awareness.

## Planning Annotation

In the plan, annotate as:
- `trigger: <service> — <event>` (e.g., "trigger: Jira — issue created")
- If no connector trigger exists for the event, fall back to timer trigger + polling or flag in open questions
