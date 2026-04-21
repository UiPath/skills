# SLA Golden — SDD Fragment

Minimal sdd fragment exercising the CLI-expressible subset of the `sla` plugin. Used to generate both the CLI output and the direct-JSON-write output for compatibility diffing. Gap-fill scenarios (per-conditional-rule escalation, ExceptionStage SLA, multi-recipient) live under `gap-fill/` as JSON-only probe fixtures — no CLI counterpart.

## Case

- **Name:** SlaProbe
- **Case identifier:** SlaProbe (constant)
- **Case App Enabled:** false

## Stages

1. **Review** (regular stage)
   - Description: Review stage

## SLA

### Root (case-level)

- **Default SLA:** 5 days
- **Conditional rule:** when `vars.priority === 'Urgent'`, SLA = 30 minutes (prepended before default)
- **Escalation on default rule:** notify `manager@corp.com` at 80% SLA risk
  - Display name: `Notify Manager`
  - Trigger type: `at-risk`
  - at-risk-percentage: 80

### Stage: Review

- **Default SLA:** 2 days
- **Escalation on default rule:** notify `Order Mgmt` user-group on SLA breach
  - Trigger type: `sla-breached`

## Not covered by this fragment

Pushed to `gap-fill/` (JSON-only):
- Per-conditional-rule escalation — attaching an escalation to a conditional `slaRules[]` entry rather than the default
- SLA on `case-management:ExceptionStage` — CLI rejects it
- One escalation rule with multiple recipients — CLI emits one rule per recipient

## Equivalent CLI invocation

```bash
uip maestro case cases add --name "SlaProbe" --file caseplan.json --output json

uip maestro case stages add caseplan.json \
  --label "Review" \
  --description "Review stage" \
  --output json

# Root-level SLA
uip maestro case sla set caseplan.json --count 5 --unit d --output json
uip maestro case sla rules add caseplan.json \
  --expression "=js:vars.priority === 'Urgent'" \
  --count 30 --unit min --output json
uip maestro case sla escalation add caseplan.json \
  --trigger-type at-risk --at-risk-percentage 80 \
  --recipient-scope User \
  --recipient-target "79570334-ed71-439e-b172-d9fc780fd61b" \
  --recipient-value "manager@corp.com" \
  --display-name "Notify Manager" \
  --output json

# Stage-level SLA
uip maestro case sla set caseplan.json \
  --stage-id <ReviewStageId> --count 2 --unit d --output json
uip maestro case sla escalation add caseplan.json \
  --stage-id <ReviewStageId> \
  --trigger-type sla-breached \
  --recipient-scope UserGroup \
  --recipient-target "00000000-0000-0000-0000-000000000001" \
  --recipient-value "Order Mgmt" \
  --output json
```

## Equivalent direct-JSON-write outcome

Same outcome, starting from the CLI-scaffolded `caseplan.json` (the `case` plugin and `stages` plugin run first — `stages` is migrated to JSON per the matrix; `case` remains CLI). SLA composes `slaRules[]` per target in a single write per [`plugins/sla/impl-json.md`](../../../skills/uipath-case-management/references/plugins/sla/impl-json.md).
