# Global Variables — Planning

Case-level data lives in the variables block (v19: `root.data.uipath.variables`; v20: top-level `variables` — see Rule 17). The key distinction is **variables** vs **arguments**:

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

### Fallback signals (when Trigger "Initial Variable Mapping" is unusable)

The "Initial Variable Mapping" column sometimes carries an aggregate phrase (e.g., `"trigger payload -> case variables"`) instead of explicit per-field rows. In that case rule #1 yields no entries — DO NOT default every variable to plain Variable. Apply this fallback chain:

1. **Cross-read the Case Variables table.** Any row with `Produced By: trigger` is an **In argument** even when the trigger row's mapping is aggregate. This is the strongest secondary signal. (Requires `Produced By` column. Canonical per `assets/templates/sdd-template.md`. If absent, skip to step 3.)
2. **Cross-read Out signal.** A variable consumed only by `case-exit-condition` (Consumed By column) AND not produced by any task may be an **Out argument**. Ambiguous on its own — confirm via AskUserQuestion. (Requires `Consumed By` column. Canonical per `assets/templates/sdd-template.md`. If absent, skip to step 3.)
3. **Still ambiguous → AskUserQuestion.** Present the variable name + its Produced By / Consumed By cells (or whatever columns the sdd.md provides) + 4 options: `In argument` / `Out argument` / `Variable` / `Skeleton — resolve later`. Never silently default.

### Completeness obligation

Per [planning.md §4.0](../../../planning.md), every row in the Case Variables table emits exactly one T-entry. Skipping rows because their category cannot be determined is forbidden — invoke AskUserQuestion instead. The pre-approval cross-check counts variable-table rows against emitted variable T-entries; mismatch is a defect.

## tasks.md Entry Format

One T-entry per variable/argument. Place after the case file (T01) and **all** trigger T-entries (T02+), before stages. The first variable lands at `T03` only when there is exactly one trigger; in multi-trigger cases it lands at `T0<last-trigger>+1`. The example below assumes a single trigger at T02:

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
- verify: Confirm entry exists in the variables block (per schema)
```

Task-output variables are wired automatically during task creation (§4.6) — no T-entry needed here.

## Types

`"string"` | `"number"` | `"boolean"` | `"date"` | `"object"` | `"array"` | `"jsonSchema"`

## Naming

camelCase IDs (`=vars.claimId`). See [impl-json.md](impl-json.md) for uniqueness rules and ID generation.
