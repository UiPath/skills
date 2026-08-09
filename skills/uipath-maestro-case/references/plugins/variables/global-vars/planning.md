# Variables — Planning

Case-level data lives in the top-level `variables` block. Three categories:

| Category | Arrays touched | When |
|---|---|---|
| **Variable** | `inputOutputs[]` (declaration) + `triggerNode.outputs[]` (when populated by trigger payload) | Case-internal state, including trigger-payload-sourced state |
| **In** | `inputs[]` + companion `inputOutputs[]` + `triggerNode.outputs[]` bridge | Formal argument supplied by external caller. Binds to the trigger named by `sourceTriggers` (single `T<N>`; blank → primary trigger T02). Any trigger type (manual, timer, or event). |
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
| `Category=In` row has CSV `sourceTriggers` (more than one T-number) | ERROR | Reject — an In-arg binds to exactly one trigger; CSV is the multi-trigger `Variable` form. |
| `Category=In` row has non-empty `sourceFields` | ERROR | Reject — In-args select a trigger but extract no payload field; use `Category=Variable` for extraction. |
| `sourceTriggers` references a T-number that doesn't exist in tasks.md (any category) | ERROR | Reject — orphan reference. |

Phase 3 (implementation) catches spec-dependent issues — see [`impl-json.md`](impl-json.md) § Phase 3 Validation.

## tasks.md Entry Format

One T-entry per Case Variables row, serialized as one row in a single variables table — NOT one H2 block per variable. Each row keeps its own T-number; the §4.0 completeness contract (one T-entry per declaration, never group, never omit) applies row-by-row. Place the table after the case file (T01) and all trigger T-entries (T02+), before stages. T-number for the first variable depends on trigger count.

```markdown
### Variables and arguments (one T-entry per row)

| T# | name | category | type | sourceTriggers | sourceFields | default | producedBy |
|---|---|---|---|---|---|---|---|
| T05 | applicantName | In | string | T03 | | "" | |
| T06 | subject | Variable | string | T02 | response.subject | | |
| T07 | caseStarter | Variable | string | T02, T03 | T02: response.user; T03: response.initiator | | |
| T08 | caseStatus | Variable | string | | | "Open" | |
| T09 | finalDecision | Out | string | | | | T15.outputs.finalDecision |
```

**Column semantics:**

- `category` — required, one of `In`, `Out`, `Variable`
- `type` — required, one of `string`, `integer`, `float`, `double`, `boolean`, `datetime`, `date`, `jsonSchema`, `file`
- `sourceTriggers` — for a `Variable`: CSV of T-numbers when one or more triggers populate it. For an `In`-arg: a single `T<N>` selecting the trigger it binds to (blank → primary trigger T02; never a CSV). Replaces the legacy `triggerRef` field.
- `sourceFields` — per-trigger payload paths (Variable only). Single-trigger form is `<path>`; multi-trigger form is `T<N>: <path>` pairs separated by `; `. Empty on `In` rows.
- `default` — initial value (string-encoded for non-string types). Drives the `default` field on the companion `inputOutputs[]` entry.
- `producedBy` — informational only (for Out-args). The io-binding validator confirms the named task actually exists with a matching output.

**Verify contract — per category, stated ONCE after the table, never repeated per row.** Emit one `verify:` line per category present, using exact terms from [`impl-json.md` § Pattern shapes](impl-json.md):

- `In` → inputs[] formal slot + inputOutputs[] companion (elementId = id-map[source trigger].id) + that trigger node's outputs[] bridge.
- `Variable` with source-triggers → inputOutputs[] companion (elementId="root"); each listed trigger's outputs[] carries its own Pattern C wire targeting the companion; no inputs[] entry.
- `Variable` without source-triggers → inputOutputs[] entry (elementId="root", default carried); no trigger output entries.
- `Out` → outputs[] formal entry; companion in inputOutputs[] ALWAYS emitted (default="" when Default empty); io-binding validator confirms producer task output id.

**Verify-term glossary — use exact terms from [`impl-json.md` § Pattern shapes](impl-json.md):**

- "Bridge" = In-arg formal-arg → companion forwarding (any trigger type; 3-entry shape) on the trigger named by the In row's `sourceTriggers` (blank → primary). NEVER use for Variable rows.
- Variable-row trigger.outputs[] entries are "Pattern C wires" (direct payload extraction, 2-entry shape).
- `sourceField`'s right side IS the connector's spec path (e.g., `response.subject` is the literal field path in `caseShape.outputs[]`), not an alias. SDD-name on the LEFT becomes `var`/`id`; spec path on the RIGHT becomes `source`.
- Spec-vs-SDD drift validation runs in the variables plugin's Phase 3 dispatcher, not in io-binding.

## Types

`"string"` | `"integer"` | `"float"` | `"double"` | `"boolean"` | `"datetime"` | `"date"` | `"jsonSchema"` | `"file"`

## Naming

camelCase IDs (`=vars.claimId`). See [`impl-json.md`](impl-json.md) § Uniqueness rules and ID generation.

## Completeness obligation

Per [planning.md §4.0](../../../planning.md), every row in the Case Variables table emits exactly one T-entry. Skipping rows because their Category cannot be determined is forbidden — invoke AskUserQuestion instead. The pre-approval cross-check counts variable-table rows against emitted variable T-entries; mismatch is a defect.
