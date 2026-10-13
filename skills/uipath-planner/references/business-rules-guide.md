# Business Rules Guide

Business rules in an SDD: validation rules, DMN-style decision tables, and rules that need reasoning.

## 1. Classify every rule

| Type | Test | Lands in |
|---|---|---|
| **Deterministic: validation** | Checks a value's form: regex, range, type, allowed values. | RPA §4 validation table; BPMN §7 Data Objects & Variables |
| **Deterministic: decision** | Explicit logic over structured data decides an outcome: thresholds, lists, lookups, dates, calculations. The same inputs always give the same output. | A decision table ([Decision tables](#2-decision-tables)) |
| **Reasoning: agent** | It takes interpretation or unstructured input (free text, a document, a judgment call), and an agent can apply it from its inputs. | The reasoning list ([Rules that need reasoning](#3-rules-that-need-reasoning)), applied by an agent |
| **Reasoning: person** | It needs a person's authority or accountability, or knowledge the inputs don't carry. | The reasoning list, applied by a person (HITL) |

- **Take the type from the PDD.** A PDD may type each rule in its Business Rules table (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, possibly in the document's language) and give its inputs and output as `inputs → output`. Keep that type. Never move a `Reasoning: person` rule to an agent on your own: that is an `[SME REVIEW]` item.
- **Classify untyped rules with the test above.** When agent or person is unclear, choose person and raise an `[SME REVIEW]` item.
- **Extraction is a separate step.** A rule on an amount read from an email is still deterministic once the amount is extracted. The extraction (IXP, agent) is a step of its own; the rule is a decision table over its output.
- **One rule, one outcome.** Split a PDD rule that decides two things before tabling it. Tiers ("under 1,000 … up to 10,000 … above") are rows of one decision table.

## 2. Decision tables

One decision per output decided from the same inputs: one table, one row per rule or tier, numbered `D1`, `D2`, … Example:

```markdown
#### D1 — Approval route
**Hit policy:** UNIQUE
**Inputs:** `invoiceAmount` (number), `vendorStatus` (string: "new", "active", "blocked")
**Output:** `approvalRoute` (string: "auto", "manager", "director", "reject")
**Runs in:** <RUNS_IN>

| # | invoiceAmount | vendorStatus | → approvalRoute | Rule |
|---|---|---|---|---|
| 1 | - | "blocked" | "reject" | BR-02 |
| 2 | < 1000 | "active" | "auto" | BR-03 |
| 3 | [1000..10000) | not("blocked") | "manager" | BR-04 |
| 4 | >= 10000 | not("blocked") | "director" | BR-05 |
| 5 | < 1000 | "new" | "manager" | BR-06 |
```

Cells (FEEL unary-test subset):

| Cell | Meaning |
|---|---|
| `-` | Any value |
| `"active"`, `42`, `true` | Equals |
| `< 1000`, `>= 10000` | Comparison |
| `[1000..10000)` | Range; `[` `]` include the bound, `(` `)` exclude it |
| `"Gold", "Silver"` | Any of these |
| `not("blocked")` | Anything except these |
| `date("<CUTOFF_DATE>")`, `< date("<CUTOFF_DATE>")` | Dates, written ISO 8601 `YYYY-MM-DD` |

- **Types** are `string`, `number`, `boolean` or `date`. Name inputs and outputs in camelCase, as the solution's variables or arguments name them. A string input or output lists its allowed values.
- **Outputs** are literals, or a simple expression over the inputs (`invoiceAmount * 0.02`).
- **Hit policy.** `UNIQUE` (default): exactly one row matches any input, so rows must not overlap. `FIRST`: rows are checked in order and the first match wins; use it only when the order is the rule. `COLLECT`: every matching row applies, for example a list of checks.
- **Complete.** Every combination of inputs matches a row. Under `UNIQUE`, cover the remaining combinations with rows of their own (`not(...)`, open ranges), because an all-`-` row would overlap every other row. A last all-`-` default row is valid only under `FIRST`, where order makes it the fallback.
- **Traceable.** Every row cites its BR in `Rule`; a row that only completes the table cites `[DEFAULT]` or `[SME REVIEW]` instead. Every decision BR appears in at least one row. Each row is a test oracle: one test case per row in the Testing Strategy (RPA §17; BPMN §13 Gateway / Branch Coverage).
- **Runs in.** BPMN: the `businessRuleTask` node key; gateways route on its output. RPA: the step, and the coded logic or lookup that evaluates it. Placement: [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step).
- **No decision rules:** write `None. No rule decides an outcome.`

## 3. Rules that need reasoning

List every `Reasoning` rule. Example:

```markdown
| ID | Rule | Applied by | Inputs → Output | Where it runs |
|---|---|---|---|---|
| BR-07 | A refund request citing a defect qualifies when the description matches a known defect. | Agent | Request text, defect catalogue → qualifies (yes/no), reason | Agent `RefundTriage`, step 4; undecided → Action Center review |
| BR-08 | A write-off above the controller's limit needs the controller's approval. | Person | Write-off request, ledger extract → approved / rejected | Action Center task, Controller role, step 6 |
```

- **Applied by an agent:** give its output as a typed value. In `Where it runs`, name the path to a person when the agent can't decide.
- **Applied by a person:** in `Where it runs`, name the task and the role. In BPMN the task is a `userTask`, also listed in §9 HITL Touchpoints.
- **No reasoning rules:** write `None. Every rule is deterministic.` Don't leave the section out.

## 4. Coverage

Number BRs `BR-01`, `BR-02`, … across every home. A decision-table row or reasoning row is the rule's definition; no separate register repeats it. In BPMN, a validation rule goes in the variable's `Description` in §7, prefixed with its BR ID.

Before closing the section, check that each BR lands in exactly one home from the [§1 table](#1-classify-every-rule). Several rows of decision tables count as one home.
