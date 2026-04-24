# sla — CLI Implementation

Three CLI sub-operations cover SLA authoring: `set`, `escalation`, `rules`. Run each per the entries in `tasks.md §4.8`.

> **Target schema.** All SLA data lives in a single `slaRules[]` array on either `root.data` or `stageNode.data`. The default SLA occupies the last entry with `expression: "=js:true"`. Conditional rules are prepended before the default. Escalations attach inside the default rule's `escalationRule[]`. There is no separate `data.sla` object at runtime — any reference to that shape in older docs is stale. See [`case-schema.md § SLA`](../../case-schema.md#6-sla-and-escalation) for the current schema.

## Units

| Unit | Meaning |
|------|---------|
| `min` | minutes |
| `h` | hours |
| `d` | days |
| `w` | weeks |
| `m` | months |

## Default SLA — `sla set`

### CLI

```bash
# Root-level
uip maestro case sla set <file> --count <n> --unit <min|h|d|w|m> --output json

# Per-stage
uip maestro case sla set <file> --count <n> --unit <min|h|d|w|m> --stage-id <stage-id> --output json
```

### Example

```bash
uip maestro case sla set caseplan.json --count 5 --unit d --output json
uip maestro case sla set caseplan.json --count 2 --unit w --stage-id stg00000001 --output json
```

### Resulting JSON

Writes a single entry into `slaRules[]` on the target (root or stage), with the sentinel expression `"=js:true"` kept as the **last** element of the array. Re-running `sla set` against the same target updates the count/unit on the existing default entry in place.

```json
// root.data (or node.data for --stage-id) after `sla set --count 5 --unit d`
"slaRules": [
  { "expression": "=js:true", "count": 5, "unit": "d" }
]
```

Stage SLA targets only `case-management:Stage`. ExceptionStage is rejected by the CLI — use the JSON strategy for that case.

## Conditional SLA Rule — `sla rules add` (root only)

### CLI

```bash
uip maestro case sla rules add <file> \
  --expression "<expr>" \
  --count <n> \
  --unit <min|h|d|w|m> \
  --output json
```

### Example

```bash
uip maestro case sla rules add caseplan.json \
  --expression "=js:vars.priority === 'Urgent'" \
  --count 30 \
  --unit min \
  --output json
```

### Resulting JSON

Prepends the new rule **before** the default `=js:true` entry in `root.data.slaRules[]`:

```json
"slaRules": [
  { "expression": "=js:vars.priority === 'Urgent'", "count": 30, "unit": "min" },
  { "expression": "=js:true", "count": 5, "unit": "d" }
]
```

Rules are evaluated in array order — first truthy expression wins. The default SLA (from `sla set`) stays last and acts as the fallback.

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

Pushes a new entry into the default rule's `escalationRule[]` — i.e., the entry with `expression: "=js:true"` inside `slaRules[]` on the target. If the default rule doesn't exist yet, the CLI creates a bare one (`{expression:"=js:true"}`) with no `count`/`unit` and attaches the escalation to it. CLI can **only** attach escalations to the default rule; per-conditional-rule escalations require the JSON strategy.

```json
"slaRules": [
  {
    "expression": "=js:true",
    "count": 5, "unit": "d",
    "escalationRule": [
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
    ]
  }
]
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

- Root SLA: trailing `slaRules[]` entry on `root.data.slaRules` has `expression: "=js:true"` with the expected `count`/`unit`
- Stage SLA: same, on `node.data.slaRules` for the target stage node
- Conditional rules: prepended before the default entry on `root.data.slaRules` in priority order
- Escalation: inside the default rule's `escalationRule[]` on the target

## Anti-Patterns

- **Do not attempt `sla rules add --stage-id`.** The CLI does not support conditional SLA rules at the stage level. Flag to the user when sdd.md describes one.
- **Do not combine multiple recipients into one `--recipient-*` call.** One call per recipient.
- **Do not set stage SLA before the stage is created.** `sla set --stage-id` requires the stage to exist.
- **Do not attempt `sla set --stage-id <id>` on an ExceptionStage.** CLI rejects it (`requireStageForSla` guards for `case-management:Stage` only). Use the JSON strategy.
- **Do not attempt to attach an escalation to a conditional SLA rule via CLI.** `sla escalation add` always writes to the default `=js:true` rule. Use the JSON strategy.
