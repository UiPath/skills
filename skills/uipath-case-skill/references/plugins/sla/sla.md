# SLA Setup

SLA rules define time-based deadlines and escalation notifications for a case or individual stage.

## Where to Add SLA

| Scope | Location |
|---|---|
| Entire case | `root.data.slaRules` |
| Individual stage | `stage.data.slaRules` |

Both use the same structure. Stage SLA overrides case SLA for that stage's duration.

## Quick Reference

| Field | Values | Notes |
|---|---|---|
| `expression` | `"=js:true"` (unconditional), `"=js:vars.<id> === 'x'"` (conditional) | First matching rule wins — put conditional rules before the default |
| `count` + `unit` | `"h"` hours, `"d"` days, `"w"` weeks, `"m"` months | Deadline duration |
| `triggerInfo.type` | `"at-risk"` or `"sla-breached"` | `at-risk` requires `atRiskPercentage` (0–100) |
| `recipients[].scope` | `"User"` (target=UUID, value=email) or `"UserGroup"` (target=UUID, value=group name) | |

## Full Example — Unconditional with Both Escalation Types

```json
"slaRules": [
  {
    "expression": "=js:true",
    "count": 5,
    "unit": "d",
    "escalationRule": [
      {
        "id": "esc_<6chars>",
        "displayName": "At-Risk 80% — Notify Manager",
        "action": {
          "type": "notification",
          "recipients": [{ "scope": "User", "target": "<user-uuid>", "value": "manager@company.com" }]
        },
        "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 }
      },
      {
        "id": "esc_<6chars>",
        "displayName": "SLA Breached — Notify Director",
        "action": {
          "type": "notification",
          "recipients": [{ "scope": "UserGroup", "target": "<group-uuid>", "value": "directors-group" }]
        },
        "triggerInfo": { "type": "sla-breached" }
      }
    ]
  }
]
```

## Conditional SLA — Multiple Rules

Multiple rules with different deadlines. First matching `expression` wins:

```json
"slaRules": [
  {
    "expression": "=js:vars.priority === 'high'",
    "count": 1, "unit": "d",
    "escalationRule": [ { "id": "esc_<6chars>", "displayName": "High-Priority At-Risk 80%", "action": { "type": "notification", "recipients": [{ "scope": "User", "target": "<uuid>", "value": "urgent@company.com" }] }, "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 } } ]
  },
  {
    "expression": "=js:vars.priority !== 'high'",
    "count": 5, "unit": "d",
    "escalationRule": [ { "id": "esc_<6chars>", "displayName": "Standard At-Risk 80%", "action": { "type": "notification", "recipients": [{ "scope": "User", "target": "<uuid>", "value": "manager@company.com" }] }, "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 } } ]
  }
]
```

## Minimal SLA (No Escalation)

Deadline only — no notifications:

```json
"slaRules": [
  { "expression": "=js:true", "count": 2, "unit": "d", "escalationRule": [] }
]
```
