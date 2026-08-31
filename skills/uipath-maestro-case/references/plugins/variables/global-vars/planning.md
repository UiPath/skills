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
3. Record the user's answer in memory and emit the rows as if the Category column had been authored that way.
4. Strongly recommend (via plain-text output before/after the prompts) that the user migrate their SDD to include the column for future regenerate-from-scratch runs.

Never default missing categories to a guess. The pre-α "Listed in Trigger Initial Variable Mapping → In argument" inference rule is removed under α and MUST NOT be re-implemented as a fallback. The post-α table shape is defined by the case SDD template (authored by `uipath-planner`); canonical Category semantics live in [impl-json.md](impl-json.md).

## Phase 2 Structural Validation

Validate at resolution time (before Phase 2 begins). All checks operate on SDD content alone — no spec data needed yet.

| Check | Severity | Action |
|---|---|---|
| `Category=Out` row has `sourceTriggers` filled | ERROR | Reject — Out-args flow case→caller, not trigger→case. AskUserQuestion: recategorize or clear sourceTriggers. |
| `Category=In` or `Out` row has missing `Type` | ERROR | Reject — type is required for formal arguments. |
| Two rows share the same `Name` (regardless of which other columns differ) | ERROR | Reject — name collision. Variable names MUST be globally unique. AskUserQuestion to resolve (rename one, or merge into one row). |
| `Category=Variable` row has `sourceTriggers` but no matching `sourceFields` entry per trigger | ERROR | Reject — multi-trigger requires per-trigger sourceField. |
| `Category=In` row has CSV `sourceTriggers` (more than one T-number) | ERROR | Reject — an In-arg binds to exactly one trigger; CSV is the multi-trigger `Variable` form. |
| `Category=In` row has non-empty `sourceFields` | ERROR | Reject — In-args select a trigger but extract no payload field; use `Category=Variable` for extraction. |
| `sourceTriggers` references a trigger that doesn't exist in the SDD (any category) | ERROR | Reject — orphan reference. |

Phase 3 (implementation) catches spec-dependent issues — see [`impl-json.md`](impl-json.md) § Phase 3 Validation.

## Fields to Resolve

One caseplan variable per Case Variables row. Place after the case file (T01) and all trigger rows (T02+), before stages. T-number for the first variable depends on trigger count.

```text
# In-argument "applicantName"
- category: In
- type: string
- sourceTriggers: T03            # single T-number; omit to bind the primary trigger (T02)
- default: ""
- verify: inputs[] formal slot + inputOutputs[] companion (elementId = id-map[T03].id) + that trigger node's outputs[] bridge written.

# Variable "subject"
- category: Variable
- type: string
- sourceTrigger: T02
- sourceField: response.subject
- verify: inputOutputs[] entry (id=subject, elementId="root"); trigger T02's outputs[] carries Pattern C wire (source="=response.subject", var=id="subject"); no inputs[] entry.

# Variable "caseStarter"
- category: Variable
- type: string
- sourceTriggers: T02, T03
- sourceFields:
    T02: response.user
    T03: response.initiator
- verify: one inputOutputs[] companion (elementId="root") shared across triggers; each listed trigger's outputs[] has its own Pattern C wire targeting the companion.

# Variable "caseStatus"
- category: Variable
- type: string
- default: "Open"
- verify: inputOutputs[] entry (id=caseStatus, elementId="root", default="Open"); no trigger output entries.

# Out-argument "finalDecision"
- category: Out
- type: string
- producedBy: T15.outputs.finalDecision   # informational reference to the producing task
- verify: outputs[] formal entry (var=finalDecision); companion in inputOutputs[] ALWAYS emitted (with default="" when Default empty); io-binding validator confirms producer task output has id=finalDecision.
```

**Field semantics:**

- `category` — required, one of `In`, `Out`, `Variable`
- `type` — required, one of `string`, `number`, `integer`, `float`, `double`, `boolean`, `datetime`, `date`, `jsonSchema`, `file`. **Emit the SDD's declared type verbatim — never substitute a near-equivalent.** `number` and `integer` are distinct and both valid; rewriting an SDD `number` as `integer` (or `float`/`double` as `number`) produces a caseplan that validates but no longer matches the declared contract, and downstream extract rows inherit the wrong type. If the SDD names a type not listed here, keep it as written and record it as a Review Flag rather than mapping it onto the nearest listed value.
- `sourceTrigger` — T-number when the value comes from a single trigger's payload (Variable category)
- `sourceTriggers` — for a `Variable`: CSV of T-numbers when multiple triggers populate it. For an `In`-arg: a single `T<N>` selecting the trigger it binds to (blank → primary trigger T02; never a CSV). Replaces the legacy `triggerRef` field.
- `sourceFields` — per-trigger payload paths (Variable only). Single-trigger form is `<path>`; multi-trigger form is a YAML-style sub-block with one `T<N>: <path>` per line. Empty on `In` rows.
- `default` — initial value, **always written as a quoted string, for every `type`**. Drives the `default` field on the companion `inputOutputs[]` entry. This is the one field where **string-encoding overrides losslessness**: an SDD Default cell holding a bare JSON object, number, or boolean is re-encoded here rather than copied verbatim, because the downstream field is string-typed and a non-primitive value is silently deleted at BPMN serialization (see [`impl-json.md` § `default` encoding](impl-json.md#default-encoding-every-type-mandatory)). Record the re-encoding — it is the only Rule 6 exception in this plugin.

  | SDD Default cell | caseplan variable `default` |
  |---|---|
  | `{"amount":125.5}` | `"{\"amount\":125.5}"` |
  | `5` | `"5"` |
  | `true` | `"true"` |
  | `Open` | `"Open"` |
  | (blank) | omit the line |
- `producedBy` — informational only (for Out-args). The io-binding validator confirms the named task actually exists with a matching output.

**`verify` text — use exact terms from [`impl-json.md` § Pattern shapes](impl-json.md):**

- "Bridge" = In-arg formal-arg → companion forwarding (any trigger type; 3-entry shape) on the trigger named by the In row's `sourceTriggers` (blank → primary). NEVER use for Variable rows.
- Variable-row trigger.outputs[] entries are "Pattern C wires" (direct payload extraction, 2-entry shape).
- `sourceField`'s right side IS the connector's spec path (e.g., `response.subject` is the literal field path in `caseShape.outputs[]`), not an alias. SDD-name on the LEFT becomes `var`/`id`; spec path on the RIGHT becomes `source`.
- Spec-vs-SDD drift validation runs in the variables plugin's Phase 3 dispatcher, not in io-binding.

## Types

`"string"` | `"number"` | `"integer"` | `"float"` | `"double"` | `"boolean"` | `"datetime"` | `"date"` | `"jsonSchema"` | `"file"`

This list is not a normalisation target. Carry the SDD's type across unchanged; `number` -> `integer` is the substitution that has actually shipped and it silently breaks the extract rows typed from that variable.

## Naming

camelCase IDs (`=vars.claimId`). See [`impl-json.md`](impl-json.md) § Uniqueness rules and ID generation.

## Completeness obligation

Per the completeness principle in [implementation.md](../../../implementation.md), every row in the Case Variables table emits exactly one caseplan variable. Skipping rows because their Category cannot be determined is forbidden — invoke AskUserQuestion instead. The pre-approval cross-check counts variable-table rows against emitted variable elements; mismatch is a defect.

<!-- END: planning.md -->
