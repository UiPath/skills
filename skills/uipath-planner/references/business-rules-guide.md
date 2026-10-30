# Business Rules Guide

Business rules in an SDD are validation rules, DMN-style decision tables, or rules requiring reasoning.

## 1. Classify every rule

| Type | Test | Lands in |
|---|---|---|
| **Deterministic: validation** | Regex, range, type, or allowed-value check. | RPA §4 validation table; BPMN §7 Data Objects & Variables |
| **Deterministic: decision** | Explicit logic over structured data (thresholds, lists, lookups, dates, calculations), with the same output for the same inputs. | A decision table ([Decision tables](#2-decision-tables)) |
| **Reasoning: agent** | Interprets unstructured input or makes a judgment applicable from its inputs. | The reasoning list ([Rules that need reasoning](#3-rules-that-need-reasoning)), applied by an agent |
| **Reasoning: person** | Requires a person's authority, accountability, or knowledge absent from the inputs. | The reasoning list, applied by a person (HITL) |

- Take the type from the PDD: it may type each rule in its Business Rules table (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, possibly in the document's language) and give its inputs and output as `inputs → output`. Keep that type. Never move a `Reasoning: person` rule to an agent on your own: that is an `[SME REVIEW]` item.
- Classify untyped rules with the table; when agent versus person is unclear, choose person and raise `[SME REVIEW]`.
- Keep extraction separate: a rule over an amount read from an email remains deterministic; extraction (IXP, agent) is separate, and the rule is a decision table over that output.
- Give each rule one outcome. Split a PDD rule deciding two things before tabling it; tiers such as “under 1,000 … up to 10,000 … above” are rows in one table.

## 2. Decision tables

Create one table per decision/output from the same inputs, with one row per rule or tier, numbered `D1`, `D2`, …. Use:

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

Use this FEEL unary-test subset in cells:

| Cell | Meaning |
|---|---|
| `-` | Any value |
| `"active"`, `42`, `true` | Equals |
| `< 1000`, `>= 10000` | Comparison |
| `[1000..10000)` | Range; `[` and `]` include bounds, `(` and `)` exclude them |
| `"Gold", "Silver"` | Any listed value |
| `not("blocked")` | Anything except these |
| `date("<CUTOFF_DATE>")`, `< date("<CUTOFF_DATE>")` | Dates, written ISO 8601 `YYYY-MM-DD` |

- Use types `string`, `number`, `boolean`, or `date`; name inputs and outputs in camelCase, matching solution variables or arguments. List allowed values for every string input or output.
- Outputs are literals or a simple input expression such as `invoiceAmount * 0.02`.
- **Hit policy:** `UNIQUE` (default) requires exactly one matching row, so rows cannot overlap. `FIRST` checks order and takes the first match; use it only when order is the rule. `COLLECT` applies every matching row, for example as a list of checks.
- **Completeness:** Aim to match every input combination. Under `UNIQUE`, cover remaining combinations with explicit rows (`not(...)`, open ranges); an all-`-` row overlaps every other row. A final all-`-` default is valid only under `FIRST`, where order makes it the fallback.
- Hit policy and completeness state design intent, not proof. Do not certify overlap-freedom or completeness by inspection; the build proves it (see **Proof**).
- **Traceability:** Every row cites its BR in `Rule`; completion-only rows cite `[DEFAULT]` or `[SME REVIEW]`. Every decision BR appears in at least one row.
- **Independent tests:** Add one Testing Strategy case per row (RPA §17; BPMN §13 Gateway / Branch Coverage), using inputs and expected output from a PDD example or SME-confirmed value, never the row itself. If neither supplies an expected value, use `[SME REVIEW]` in its place. A row-derived case can pass when the row is wrong.
- **Proof:** The BPMN or RPA implementation task lists these cases in its `Validate` sub-step ([Plan and Tasks Format](plan-and-tasks-format.md)) and proves the table with tools. For a `.dmn` business rule, run `uip rules validate <PROJECT_DIR> --output json`, then run `uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json` once per test case. For coded RPA logic, write one unit test per case. A failing case is a defect in the row or test-case source; resolve it with the SME, never by editing expected output to match.
- **Runs in:** BPMN: the `businessRuleTask` node key; gateways route on its output. RPA: the step and coded logic or lookup evaluating it. Place it according to [Product Selection Guide → Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step).
- **No decision rules:** write `None. No rule decides an outcome.`

## 3. Rules that need reasoning

List every `Reasoning` rule:

```markdown
| ID | Rule | Applied by | Inputs → Output | Where it runs |
|---|---|---|---|---|
| BR-07 | A refund request citing a defect qualifies when the description matches a known defect. | Agent | Request text, defect catalogue → qualifies (yes/no), reason | Agent `RefundTriage`, step 4; undecided → Action Center review |
| BR-08 | A write-off above the controller's limit needs the controller's approval. | Person | Write-off request, ledger extract → approved / rejected | Action Center task, Controller role, step 6 |
```

- **Agent-applied:** provide a typed output and, in `Where it runs`, the path to a person when the agent cannot decide.
- **Person-applied:** name the task and role in `Where it runs`. In BPMN, the task is a `userTask` and is also listed in §9 HITL Touchpoints.
- **No reasoning rules:** write `None. Every rule is deterministic.` Do not omit the section.

## 4. Coverage

Number BRs `BR-01`, `BR-02`, … across every home. A decision-table row or reasoning row defines the rule; do not duplicate it in a register. In BPMN, put validation rules in the variable's `Description` in §7, prefixed by the BR ID.

Before closing:
1. List BR IDs extracted from the PDD.
2. List BR IDs cited in each home from the [§1 table](#1-classify-every-rule); all decision-table rows together are one home.
3. Confirm every extracted ID appears in exactly one home list and no home cites an ID absent from the extraction.