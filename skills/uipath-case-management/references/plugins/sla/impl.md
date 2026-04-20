# sla — Implementation

Three CLI sub-operations cover SLA authoring: `set`, `escalation`, `rules`. Run each per the entries in `tasks.md §4.8`.

## Units

| Unit | Meaning |
|------|---------|
| `h` | hours |
| `d` | days |
| `w` | weeks |
| `m` | months |

## Default SLA — `sla set`

### CLI

```bash
# Root-level
uip maestro case sla set <file> --count <n> --unit <h|d|w|m> --output json

# Per-stage
uip maestro case sla set <file> --count <n> --unit <h|d|w|m> --stage-id <stage-id> --output json
```

### Example

```bash
uip maestro case sla set caseplan.json --count 5 --unit d --output json
uip maestro case sla set caseplan.json --count 2 --unit w --stage-id stg00000001 --output json
```

### Resulting JSON

Root: `root.data.sla = { count: 5, unit: "d" }`.
Stage: `nodes[].data.sla = { count: 2, unit: "w" }` on the matching stage.

## Conditional SLA Rule — `sla rules add` (root only)

### CLI

```bash
uip maestro case sla rules add <file> \
  --expression "<expr>" \
  --count <n> \
  --unit <h|d|w|m> \
  --output json
```

### Example

```bash
uip maestro case sla rules add caseplan.json \
  --expression "=js:vars.priority === 'Urgent'" \
  --count 30 \
  --unit m \
  --output json
```

### Resulting JSON

Root: `root.data.slaRules[]` gains an entry:

```json
{ "expression": "=js:vars.priority === 'Urgent'", "count": 30, "unit": "m" }
```

Rules are evaluated in array order — first truthy expression wins. The default SLA (from `sla set`) acts as the fallback.

### Expression Translation

The `tasks.md` entry has `condition: "<natural-language>"`. Translate at execution time:

| sdd.md phrase | Expression |
|---------------|-----------|
| "when priority is Urgent" | `=js:vars.priority === 'Urgent'` |
| "when amount exceeds 10000" | `=js:vars.amount > 10000` |
| "when customer is a VIP" | `=js:vars.customerTier === 'VIP'` |

If the translation is not obvious, ask the user with **AskUserQuestion** including 2–3 candidate expressions + "Something else".

## Escalation Rule — `sla escalation add`

### CLI

```bash
uip maestro case sla escalation add <file> \
  --trigger-type <at-risk|sla-breached> \
  --at-risk-percentage <1-99> \
  --recipient-scope <User|UserGroup> \
  --recipient-target "<target>" \
  --recipient-value "<value>" \
  --display-name "<name>" \
  --stage-id "<stage-id>" \
  --output json
```

`--at-risk-percentage` is required only when `--trigger-type at-risk`. Omit `--stage-id` for root-level escalation.

### Example — Notify manager at 80% SLA risk

```bash
uip maestro case sla escalation add caseplan.json \
  --trigger-type at-risk \
  --at-risk-percentage 80 \
  --recipient-scope User \
  --recipient-target "manager@corp.com" \
  --recipient-value "manager@corp.com" \
  --display-name "Notify Manager" \
  --output json
```

### Example — Notify group on breach, stage-scoped

```bash
uip maestro case sla escalation add caseplan.json \
  --trigger-type sla-breached \
  --recipient-scope UserGroup \
  --recipient-target "OrderMgmt" \
  --recipient-value "Order Management Team" \
  --stage-id stg00000001 \
  --output json
```

### Resulting JSON

Root (or stage) `sla.escalationRule[]` gains:

```json
{
  "id": "<escalationId>",
  "displayName": "Notify Manager",
  "action": {
    "type": "notification",
    "recipients": [
      { "scope": "User", "target": "manager@corp.com", "value": "manager@corp.com" }
    ]
  },
  "triggerInfo": { "type": "at-risk", "atRiskPercentage": 80 }
}
```

### Multiple Recipients

If the `tasks.md` entry lists multiple recipients, run `sla escalation add` **once per recipient** (the CLI accepts one recipient per call). Each call returns an `EscalationRuleId` — capture all.

## Listing and Removing

```bash
# List
uip maestro case sla get <file>
uip maestro case sla get <file> --stage-id <id>
uip maestro case sla escalation list <file> [--stage-id <id>]
uip maestro case sla rules list <file>

# Remove
uip maestro case sla remove <file> [--stage-id <id>]
uip maestro case sla escalation remove <file> <escalation-id> [--stage-id <id>]
uip maestro case sla rules remove <file> <index>    # 0-based index
```

## Post-Add Validation

After each `sla *` command, capture any returned IDs. Confirm in `caseplan.json`:

- Root SLA: `root.data.sla` set
- Stage SLA: target stage node's `data.sla` set
- Conditional rules: `root.data.slaRules` array in the expected order
- Escalation: `sla.escalationRule` array on the correct target (root or stage) contains the new rule

## Anti-Patterns

- **Do not attempt `sla rules add --stage-id`.** The CLI does not support conditional SLA rules at the stage level. Flag to the user when sdd.md describes one.
- **Do not combine multiple recipients into one `--recipient-*` call.** One call per recipient.
- **Do not set stage SLA before the stage is created.** `sla set --stage-id` requires the stage to exist.
