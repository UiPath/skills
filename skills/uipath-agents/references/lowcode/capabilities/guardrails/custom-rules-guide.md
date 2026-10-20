# Custom (Deterministic) Guardrails (`$guardrailType: "custom"`)

Deterministic rules you define — word matching, number comparison, boolean checks, universal triggers. Base guardrail fields, selector scoping, and actions are in [guardrails.md](guardrails.md) — read its Overview and Walkthrough first. Custom guardrails support only `Tool` scope with exactly one tool in `matchNames`, and they are the ONLY guardrail type the conversational runtime executes (see [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1).

Custom guardrails use deterministic rules you define. They have a `rules` array containing one or more rule objects.

> **Rule combination logic is AND.** Multiple rules in a single guardrail are evaluated with AND — all rules must match for the guardrail to trigger. Multiple fields selected within a single rule (via `$selectorType: "specific"` with multiple `fields` entries) are also AND — every listed field must satisfy the operator.
>
> Example with two rules and multi-field selector:
> ```json
> "rules": [
>   {
>     "$ruleType": "word",
>     "fieldSelector": {
>       "$selectorType": "specific",
>       "fields": [
>         { "path": "editPermissions[*].project.archivedBy.applicationRoles.items[*].groups[*]", "source": "output", "title": "Edit permissions project archived by application roles items groups" },
>         { "path": "editPermissions[*].project.archivedBy.applicationRoles.items[*].key", "source": "output", "title": "Edit permissions project archived by application roles items key" }
>       ]
>     },
>     "operator": "doesNotStartWith",
>     "value": "AL"
>   },
>   {
>     "$ruleType": "word",
>     "fieldSelector": {
>       "$selectorType": "specific",
>       "fields": [
>         { "path": "description", "source": "output", "title": "Description" }
>       ]
>     },
>     "operator": "isNotEmpty",
>     "value": ""
>   }
> ]
> ```
> Evaluation: `(groups doesNotStartWith "AL" AND key doesNotStartWith "AL") AND (description isNotEmpty)` — all three conditions must be true for the guardrail to trigger.
>
> **OR logic is not supported.** To achieve OR behavior, create separate guardrails — one per condition branch. Each guardrail triggers independently.

> **Critical discriminator fields:** Every rule needs `$ruleType`. Every field selector needs `$selectorType`. Every action needs `$actionType`. Missing any of these causes validation failure.

```json
{
  "$guardrailType": "custom",
  "id": "<uuid>",
  "name": "Block forbidden terms",
  "description": "Prevents agent from using blacklisted words",
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
  "action": { "$actionType": "block", "reason": "Forbidden term detected" },
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "all"
      },
      "operator": "contains",
      "value": "CONFIDENTIAL"
    }
  ]
}
```

## Rule Types

### Word Rules (`$ruleType: "word"`)

String matching against field values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"word"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector — see [Field Selectors](#field-selectors) |
| `operator` | string | Yes | Match operator |
| `value` | string | Yes | Value to match against |

**Operators:**

| Operator | Behavior |
|----------|----------|
| `contains` | Field value contains the string |
| `equals` | Field value exactly equals the string |
| `startsWith` | Field value starts with the string |
| `endsWith` | Field value ends with the string |
| `matchesRegex` | Field value matches the regular expression |
| `doesNotContain` | Field value does not contain the string |
| `doesNotEqual` | Field value does not equal the string |
| `doesNotStartWith` | Field value does not start with the string |
| `doesNotEndWith` | Field value does not end with the string |
| `isEmpty` | Field value is empty (no `value` needed) |
| `isNotEmpty` | Field value is not empty (no `value` needed) |

### Number Rules (`$ruleType: "number"`)

Numeric comparison against field values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"number"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | string | Yes | Comparison operator |
| `value` | number | Yes | Value to compare against |

**Operators:** `equals`, `doesNotEqual`, `greaterThan`, `greaterThanOrEqual`, `lessThan`, `lessThanOrEqual`

Complete example — log a Warning when a tool's numeric `sum` output exceeds 100:

```json
{
  "$guardrailType": "custom",
  "id": "<uuid>",
  "name": "Warn on high source count",
  "description": "Logs a warning when the sum output exceeds the allowed limit",
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
  "action": { "$actionType": "log", "severityLevel": "Warning" },
  "rules": [
    {
      "$ruleType": "number",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [{ "path": "sum", "source": "output" }]
      },
      "operator": "greaterThan",
      "value": 100
    }
  ]
}
```

### Boolean Rules (`$ruleType: "boolean"`)

Boolean equality check.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"boolean"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | `"equals"` | Yes | Only `equals` is supported |
| `value` | boolean | Yes | `true` or `false` |

Complete example — block a tool call when its boolean `verified` input is `false`:

```json
{
  "$guardrailType": "custom",
  "id": "<uuid>",
  "name": "Block unverified requests",
  "description": "Blocks the tool call when the verified flag is false",
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
  "action": { "$actionType": "block", "reason": "Request is not verified" },
  "rules": [
    {
      "$ruleType": "boolean",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [{ "path": "verified", "source": "input" }]
      },
      "operator": "equals",
      "value": false
    }
  ]
}
```

### Always / Universal Rules (`$ruleType: "always"`)

Fires on every input/output — no condition check. Use `applyTo` to control whether it runs on input, output, or inputAndOutput.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"always"` | Yes | Rule type discriminator |
| `applyTo` | `"input"` \| `"output"` \| `"inputAndOutput"` | Yes | When the rule fires |

## Field Selectors

Each rule (except `always`) has a `fieldSelector` object with a `$selectorType` discriminator.

**All fields:**
```json
"fieldSelector": {
  "$selectorType": "all"
}
```

**Specific fields:**
```json
"fieldSelector": {
  "$selectorType": "specific",
  "fields": [
    { "path": "content", "source": "output" },
    { "path": "email", "source": "input", "title": "Email Address" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|-------------|-------------|
| `$selectorType` | `"all"` \| `"specific"` | Yes | Discriminator — match all fields or named fields |
| `fields` | array | Yes (when `"specific"`) | Array of field references |
| `fields[].path` | string | Yes | Field path from the agent's input/output schema |
| `fields[].source` | `"input"` \| `"output"` | Yes | Which side to inspect |
| `fields[].title` | string | No | Human-readable label |


## Examples

### Example: Custom Word Rule — Block Forbidden Terms in Specific Tool Output

```json
{
  "$guardrailType": "custom",
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "name": "Block forbidden output",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [
          {
            "path": "content",
            "source": "output"
          }
        ]
      },
      "operator": "contains",
      "value": "CONFIDENTIAL"
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "Forbidden term detected in tool output."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example: Custom Word Rule — Log on All Tool Fields

```json
{
  "$guardrailType": "custom",
  "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "name": "Log sensitive terms",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "all"
      },
      "operator": "contains",
      "value": "password"
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Warning"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example: Custom Word Rule — Specific Fields with Titles on a Named Tool

Inspects specific output fields (with human-readable `title`) of an Integration Service tool. Logs a violation when the field value contains a forbidden string.

```json
{
  "$guardrailType": "custom",
  "id": "68005ea0-9d46-4094-8113-d497f53fd17f",
  "name": "Log sensitive URLs in Jira output",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [
          {
            "path": "baseUrl",
            "source": "output",
            "title": "Base url"
          },
          {
            "path": "scmInfo",
            "source": "output",
            "title": "Scm info"
          }
        ]
      },
      "operator": "contains",
      "value": "internal.corp"
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Info"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["Get Instance Details"]
  }
}
```

### Example: Filter — Redact Fields from Tool Output

Redacts specific fields from a tool's output instead of blocking or logging. Use when you want the agent to continue but with sensitive data removed.

```json
{
  "$guardrailType": "custom",
  "id": "f6a7b8c9-d0e1-2345-abcd-678901234567",
  "name": "Redact SSN from output",
  "description": "Removes SSN field from tool output before returning to user",
  "rules": [
    {
      "$ruleType": "always",
      "applyTo": "output"
    }
  ],
  "action": {
    "$actionType": "filter",
    "fields": [
      { "path": "ssn", "source": "output", "title": "SSN" },
      { "path": "taxId", "source": "output", "title": "Tax ID" }
    ]
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["GetCustomerProfile"]
  }
}
```

## References

- [guardrails.md](guardrails.md) — base guardrail schema, selector scoping, actions, walkthrough
- [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) — conversational guardrail restrictions
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical low-code rules and guardrail anti-patterns
