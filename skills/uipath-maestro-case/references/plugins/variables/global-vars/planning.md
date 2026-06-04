# Variables — Planning

Case-level data lives in the variables block (v19: `root.data.uipath.variables`; v20: top-level `variables` — see Rule 18). Three categories:

| Category | Arrays touched | When |
|---|---|---|
| **Variable** | `inputOutputs[]` (declaration) + `triggerNode.outputs[]` (when populated by trigger payload) | Case-internal state, including trigger-payload-sourced state |
| **In** | `inputs[]` + companion `inputOutputs[]` + `triggerNode.outputs[]` bridge | Formal argument supplied by external caller. Manual / timer triggers only. |
| **Out** | `outputs[]` + companion `inputOutputs[]` (ALWAYS — see [`impl-json.md` § Out argument](impl-json.md)) | Formal argument returned to caller at case end |

> **Canonical definition:** [`impl-json.md` § Pattern shapes by category](impl-json.md) is the source of truth for emission shapes (which arrays get written, exact JSON shape, runtime resolution semantics). This table is the Phase 1 routing summary.

## SDD-to-Category Mapping

Read the `Category` column on each Case Variables row. No inference, no fallback chain.

| SDD `Category` cell | Action |
|---|---|
| `In` | Process as In argument |
| `Out` | Process as Out argument |
| `Variable` | Process as plain Variable |
| Empty / missing | **AskUserQuestion** — present row's Name + ask `In` / `Out` / `Variable`. Never silently default. |
| Other value | AskUserQuestion (same) |

The Category column is REQUIRED in the SDD template.

**Pre-flight: when the Category column is entirely absent from the Case Variables table** (legacy SDD authored against the pre-α template), do NOT proceed with inference. Apply the migration prompt:

1. Read the Case Variables table rows.
2. For EACH row, present a single AskUserQuestion: `<rowName>`: `In` / `Out` / `Variable` / `Skip — not a variable`. Multi-select if the harness allows batching; otherwise one prompt per row.
3. Record the user's answer in memory and emit the T-entries as if the Category column had been authored that way.
4. Strongly recommend (via plain-text output before/after the prompts) that the user migrate their SDD to include the column for future regenerate-from-scratch runs.

Never default missing categories to a guess. The pre-α "Listed in Trigger Initial Variable Mapping → In argument" inference rule is removed under α and MUST NOT be re-implemented as a fallback. See [`assets/templates/sdd-template.md`](../../../../assets/templates/sdd-template.md) § Case Variables for the post-α table shape.

## Phase 2 Structural Validation

Validate at planning time (before tasks.md is finalized). All checks operate on SDD content alone — no spec data needed yet.

| Check | Severity | Action |
|---|---|---|
| `Category=Out` row has `sourceTriggers` filled | ERROR | Reject — Out-args flow case→caller, not trigger→case. AskUserQuestion: recategorize or clear sourceTriggers. |
| `Category=In` or `Out` row has missing `Type` | ERROR | Reject — type is required for formal arguments. |
| Two rows share the same `Name` (regardless of which other columns differ) | ERROR | Reject — name collision. Variable names MUST be globally unique. AskUserQuestion to resolve (rename one, or merge into one row). |
| `Category=Variable` row has `sourceTriggers` but no matching `sourceFields` entry per trigger | ERROR | Reject — multi-trigger requires per-trigger sourceField. |
| `sourceTriggers` references a T-number that doesn't exist in tasks.md | ERROR | Reject — orphan reference. |

Phase 3 (implementation) catches spec-dependent issues — see [`impl-json.md`](impl-json.md) § Phase 3 Validation.

## tasks.md Entry Format

One T-entry per Case Variables row. Place after the case file (T01) and all trigger T-entries (T02+), before stages. T-number for the first variable depends on trigger count.

```markdown
## T05: Declare In-argument "applicantName"
- category: In
- type: string
- triggerRef: T02
- default: ""
- verify: inputs[] formal slot + inputOutputs[] companion (elementId=<triggerId>) + triggerNode.outputs[] bridge written.

## T06: Declare Variable "subject"
- category: Variable
- type: string
- sourceTrigger: T02
- sourceField: response.subject
- verify: inputOutputs[] entry (id=subject, elementId="root"); trigger T02's outputs[] carries Pattern C wire (source="=response.subject", var=id="subject"); no inputs[] entry.

## T07: Declare Variable "caseStarter"
- category: Variable
- type: string
- sourceTriggers: T02, T03
- sourceFields:
    T02: response.user
    T03: response.initiator
- verify: one inputOutputs[] companion (elementId="root") shared across triggers; each listed trigger's outputs[] has its own Pattern C wire targeting the companion.

## T08: Declare Variable "caseStatus"
- category: Variable
- type: string
- default: "Open"
- verify: inputOutputs[] entry (id=caseStatus, elementId="root", default="Open"); no trigger output entries.

## T09: Declare Out-argument "finalDecision"
- category: Out
- type: string
- producedBy: T15.outputs.finalDecision   # informational reference to the producing task T-entry
- verify: outputs[] formal entry (var=finalDecision); companion in inputOutputs[] ALWAYS emitted (with default="" when Default empty); io-binding validator confirms producer task output has id=finalDecision.
```

**Field semantics on the T-entry:**

- `category` — required, one of `In`, `Out`, `Variable`
- `type` — required, one of `string`, `integer`, `float`, `double`, `boolean`, `datetime`, `date`, `jsonSchema`, `file`
- `triggerRef` — T-number of the trigger this In-arg is attached to (single-trigger). For In-args only.
- `sourceTrigger` — T-number when the value comes from a single trigger's payload (Variable category)
- `sourceTriggers` — CSV of T-numbers when multiple triggers populate this Variable
- `sourceFields` — per-trigger payload paths. Single-trigger form is `<path>`; multi-trigger form is a YAML-style sub-block with one `T<N>: <path>` per line
- `default` — initial value (string-encoded for non-string types). Drives the `default` field on the companion `inputOutputs[]` entry.
- `producedBy` — informational only (for Out-args). The io-binding validator confirms the named task actually exists with a matching output.

**`verify` text — use exact terms from [`impl-json.md` § Pattern shapes](impl-json.md):**

- "Bridge" = In-arg formal-arg → companion forwarding (manual/timer only, 3-entry shape). NEVER use for Variable rows.
- Variable-row trigger.outputs[] entries are "Pattern C wires" (direct payload extraction, 2-entry shape).
- `sourceField`'s right side IS the connector's spec path (e.g., `response.subject` is the literal field path in `caseShape.outputs[]`), not an alias. SDD-name on the LEFT becomes `var`/`id`; spec path on the RIGHT becomes `source`.
- Spec-vs-SDD drift validation runs in the variables plugin's Phase 3 dispatcher, not in io-binding.

## Types

`"string"` | `"integer"` | `"float"` | `"double"` | `"boolean"` | `"datetime"` | `"date"` | `"jsonSchema"` | `"file"`

## Naming

camelCase IDs (`=vars.claimId`). See [`impl-json.md`](impl-json.md) § Uniqueness rules and ID generation.

## Completeness obligation

Per [planning.md §4.0](../../../planning.md), every row in the Case Variables table emits exactly one T-entry. Skipping rows because their Category cannot be determined is forbidden — invoke AskUserQuestion instead. The pre-approval cross-check counts variable-table rows against emitted variable T-entries; mismatch is a defect.
