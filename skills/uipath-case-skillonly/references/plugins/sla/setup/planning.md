# SLA Setup — Planning

SLA rules define time-based deadlines and escalation notifications for a case or individual stage.

## Where to Add SLA

| Scope | Location in JSON |
|---|---|
| Entire case (default deadline) | `root.data.slaRules` |
| Individual stage | `stage.data.slaRules` |

Both use the same structure. Stage SLA overrides case SLA for that stage's duration.

## Single vs Conditional SLA

| Situation | Expression | Use |
|---|---|---|
| One deadline applies to all cases | `"=js:true"` | Single unconditional rule |
| Different deadlines based on case data | `"=js:vars.priority === 'high'"` | Multiple conditional rules |

Multiple rules are evaluated; **all matching rules apply simultaneously**.

## Escalation Type Decision

| Escalation point | `triggerInfo.type` | Extra field |
|---|---|---|
| When SLA is approaching (not yet breached) | `"at-risk"` | `atRiskPercentage` (0–100) |
| When SLA deadline has passed | `"sla-breached"` | none |

Typical pattern: add both — at-risk at 80% to warn, sla-breached to escalate urgently.

## Recipient Scope

| `scope` | `target` | `value` |
|---|---|---|
| `"User"` | User UUID | Email address |
| `"UserGroup"` | Group UUID | Group name |
