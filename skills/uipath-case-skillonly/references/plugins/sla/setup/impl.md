# SLA Setup — Implementation

SLA rules go in `root.data.slaRules` (case-level) or `stage.data.slaRules` (stage-level).

## Single Unconditional Rule with Both Escalations

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
          "recipients": [
            {
              "scope": "User",
              "target": "<user-uuid>",
              "value": "manager@company.com"
            }
          ]
        },
        "triggerInfo": {
          "type": "at-risk",
          "atRiskPercentage": 80
        }
      },
      {
        "id": "esc_<6chars>",
        "displayName": "SLA Breached — Notify Director",
        "action": {
          "type": "notification",
          "recipients": [
            {
              "scope": "UserGroup",
              "target": "<group-uuid>",
              "value": "directors-group"
            }
          ]
        },
        "triggerInfo": {
          "type": "sla-breached"
        }
      }
    ]
  }
]
```

## Conditional SLA — Different Deadlines by Priority

```json
"slaRules": [
  {
    "expression": "=js:$vars.priority === 'high'",
    "count": 1,
    "unit": "d",
    "escalationRule": [
      {
        "id": "esc_<6chars>",
        "displayName": "High-Priority At-Risk 80%",
        "action": {
          "type": "notification",
          "recipients": [{ "scope": "User", "target": "<uuid>", "value": "urgent@company.com" }]
        },
        "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 }
      }
    ]
  },
  {
    "expression": "=js:$vars.priority !== 'high'",
    "count": 5,
    "unit": "d",
    "escalationRule": [
      {
        "id": "esc_<6chars>",
        "displayName": "Standard At-Risk 80%",
        "action": {
          "type": "notification",
          "recipients": [{ "scope": "User", "target": "<uuid>", "value": "manager@company.com" }]
        },
        "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 }
      }
    ]
  }
]
```

## Stage-Level SLA (No Escalation)

Minimal SLA without escalation — just defines the deadline:

```json
"slaRules": [
  {
    "expression": "=js:true",
    "count": 2,
    "unit": "d",
    "escalationRule": []
  }
]
```

## Time Unit Reference

| `unit` | Meaning |
|---|---|
| `"h"` | Hours |
| `"d"` | Days |
| `"w"` | Weeks |
| `"m"` | Months |

## conditionExpression in SLA Rules

The `expression` field uses `=js:` prefix and is always evaluated as JavaScript. Access global variables with `$vars.<id>`:

```
=js:true                              // always applies
=js:$vars.priority === 'high'         // only for high-priority cases
=js:$vars.claimAmount > 50000         // only for large claims
=js:$vars.region === 'EU'             // only for EU region
```
