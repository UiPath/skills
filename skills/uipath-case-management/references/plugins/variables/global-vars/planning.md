# Global Variables — Planning

Case-level data lives in `root.data.uipath.variables`. The key distinction is **variables** vs **arguments**:

| Concept | Arrays | When |
|---|---|---|
| **Variable** | `inputOutputs[]` only | Internal data shared between stages |
| **In argument** | `inputs[]` + companion `inputOutputs[]` + trigger output mapping | Data passed into the case at start |
| **Out argument** | `outputs[]` + companion `inputOutputs[]` | Data returned to caller when case ends |

## SDD-to-Category Mapping

From the SDD "Case Variables" table:

1. Listed in Trigger "Initial Variable Mapping" → **In argument**
2. Marked as returned to caller → **Out argument**
3. Everything else → **Variable**

## tasks.md Entry Format

One T-entry per variable/argument. Place after case file (T01) and trigger (T02), before stages:

```markdown
## T03: Declare In argument "employeeName"
- category: In
- type: string
- triggerId: <trigger-node-id>

## T04: Declare variable "caseStatus"
- category: Variable
- type: string
- default: "Open"

## T05: Declare Out argument "finalDecision"
- category: Out
- type: string
- verify: Confirm entry exists in root.data.uipath.variables
```

Task-output variables are wired automatically during task creation (§4.6) — no T-entry needed here.

## Types

`"string"` | `"number"` | `"boolean"` | `"date"` | `"object"` | `"array"` | `"jsonSchema"`

## Naming

camelCase IDs (`=vars.claimId`). See [impl-json.md](impl-json.md) for uniqueness rules and ID generation.
