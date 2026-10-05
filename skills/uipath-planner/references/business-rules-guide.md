# Business Rules Guide

How an SDD specifies business rules: deterministic rules as DMN-style decision tables, and rules that need reasoning as a list naming who applies them. Load when filling a template's business-rules section (RPA §4, BPMN §5).

## 1. Classify every rule

| Type | Test | Lands in |
|---|---|---|
| **Deterministic** | Explicit logic over structured data decides it: thresholds, lists, lookups, dates, calculations. The same inputs always give the same output. | A decision table (§2) |
| **Reasoning: agent** | It takes interpretation or unstructured input (free text, a document, a judgment call), and an agent can apply it from its inputs. | The reasoning list (§3), applied by an agent |
| **Reasoning: person** | It needs a person's authority or accountability, or knowledge the inputs don't carry. | The reasoning list (§3), applied by a person (HITL) |

- **Take the type from the PDD.** A PDD may type each rule in its Business Rules table (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, possibly in the document's language) and give its inputs and output as `inputs → output`. Keep that type. Never move a `Reasoning: person` rule to an agent on your own: that is an `[SME REVIEW]` item.
- **Classify untyped rules with the test above.** When agent or person is unclear, choose person and raise an `[SME REVIEW]` item.
- **Extraction is a separate step.** A rule on an amount read from an email is still deterministic once the amount is extracted. The extraction (IXP, agent) is a step of its own; the rule is a decision table over its output.
- **One rule, one outcome.** Split a PDD rule that decides two things before tabling it. Tiers ("under 1,000 … up to 10,000 … above") are rows of one decision table.

## 2. Decision tables (deterministic rules)

Group deterministic rules that read the same inputs to decide the same output into one decision: one table, one row per rule or tier. Number decisions `D1`, `D2`, …

```markdown
#### D1 — Approval route
**Hit policy:** UNIQUE
**Inputs:** `invoiceAmount` (number), `vendorStatus` (string: "new", "active", "blocked")
**Output:** `approvalRoute` (string: "auto", "manager", "director", "reject")
**Runs in:** <the step, node or task that evaluates it>

| # | invoiceAmount | vendorStatus | → approvalRoute | Rule |
|---|---|---|---|---|
| 1 | - | "blocked" | "reject" | BR-02 |
| 2 | < 1000 | "active" | "auto" | BR-03 |
| 3 | [1000..10000) | not("blocked") | "manager" | BR-04 |
| 4 | >= 10000 | not("blocked") | "director" | BR-05 |
| 5 | < 1000 | "new" | "manager" | BR-06 |
```

Cell syntax is a subset of DMN's FEEL unary tests:

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
- **Complete.** Every combination of inputs matches a row. Under `UNIQUE`, cover the remaining combinations with rows of their own (`not(...)`, open ranges), because an all-`-` row would overlap every other row. A last all-`-` default row is valid only under `FIRST`, where order makes it the fallback. Either way, cite where a default outcome comes from: a PDD rule, or `[DEFAULT]`/`[SME REVIEW]`.
- **Traceable.** Every row cites its BR, and every deterministic BR appears in at least one row. Each row is a test oracle: §Testing gets one case per row.
- **Where it runs** follows the Product Selection Guide: DMN lives inside Maestro (a `businessRuleTask`) or as an agent's rule logic. In an RPA process it is coded logic, or a lookup the process reads.

## 3. Rules that need reasoning

List every `Reasoning` rule, so the reader sees what the decision tables leave out and who decides it:

```markdown
| ID | Rule | Applied by | Inputs → Output | Where it runs |
|---|---|---|---|---|
| BR-07 | A refund request citing a defect qualifies when the description matches a known defect. | Agent | Request text, defect catalogue → qualifies (yes/no), reason | Agent `RefundTriage`, step 4 |
| BR-08 | A write-off above the controller's limit needs the controller's approval. | Person | Write-off request, ledger extract → approved / rejected | Action Center task, step 6 |
```

- **Applied by an agent:** name its output as a typed value, and the path to a person when the agent can't decide.
- **Applied by a person:** name the task and the role.
- **Zero reasoning rules:** write `None. Every rule is deterministic.` Don't leave the section out.

## 4. Coverage

Every BR in the SDD lands in exactly one place:
- a validation row (RPA §4's table), for a rule on a value's form: regex, range, type, allowed values;
- one or more decision-table rows (§2), for a deterministic rule that decides an outcome;
- the reasoning list (§3).

Before closing the section, check that each BR lands somewhere, and in one place only.
