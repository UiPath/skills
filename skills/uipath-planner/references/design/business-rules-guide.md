# Business Rules Guide

Business rules in an SDD: validation rules, DMN-style decision tables, and rules that need reasoning.

## 1. Classify every rule

| Type | Test | Lands in |
|---|---|---|
| **Deterministic: validation** | Checks a value's form: regex, range, type, allowed values. | The validation rules ([Homes per template](#homes-per-template)) |
| **Deterministic: decision** | Explicit logic over structured data decides an outcome: thresholds, lists, lookups, dates, calculations. The same inputs always give the same output. | A decision table ([Decision tables](#2-decision-tables)) |
| **Deterministic: behaviour** | When a condition holds, the process does something set: a fallback when a system is down, a deadline or reminder, a route, what a screen shows, what is kept or sent. | The rules applied in the process, each naming the element that applies it |
| **Reasoning: agent** | It takes interpretation or unstructured input (free text, a document, a judgment call), and an agent can apply it from its inputs. | The reasoning list ([Rules that need reasoning](#3-rules-that-need-reasoning)), applied by an agent |
| **Reasoning: person** | It needs a person's authority or accountability, or knowledge the inputs don't carry. | The reasoning list, applied by a person (HITL) |

### Homes per template

Every rule has one home, in the SDD of the template that applies it:

| Template | Validation | Decision | Behaviour | Reasoning |
|---|---|---|---|---|
| RPA | §4 table | §4 Decision Tables | the §3 step or §7 exception row that applies it, opening `BR-12: <the rule>` | §4 Rules That Need Reasoning |
| BPMN | the variable's `Description` in §4 Data | §3 decision tables | the §2 step or gateway, or the §7 error row, that applies it, opening `BR-12: <the rule>` | §3 rules that need reasoning |
| Case | § Business Rules → Validation Rules | § Business Rules → Decision Tables | § Business Rules → Rules Applied in the Case | § Business Rules → Rules That Need Reasoning |
| Flow, API workflow, Coded app | Business Rules → Validation Rules | Business Rules → Decision Tables | Business Rules → Rules Applied in the <Flow \| Workflow \| App> | Business Rules → Rules That Need Reasoning |
| Agent | §2 Business Rules | §2 Business Rules | §2 Business Rules | §2 Business Rules (Applied by: instructions) |

In the Case, Flow, API workflow and Coded app templates, the element that applies a rule (a task, a condition, an SLA rule, a secondary stage, a node, a step, a page) names its ID where it does so — `BR-012` in a Recipient, an entry condition's Description, a step's detail — and the Business Rules row stays the rule's one definition. A rule the source states that this design does not apply goes in Rules Not Carried with the reason: another SDD of the solution applies it (name it), or the source's future state retires it. Any other reason is an `[SME REVIEW]` item, never a silent drop.

- **Take the type from the PDD.** A PDD may type each rule in its Business Rules table (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, possibly in the document's language) and give its inputs and output as `inputs → output`. Keep that type. Never move a `Reasoning: person` rule to an agent on your own: that is an `[SME REVIEW]` item.
- **Classify untyped rules with the test above.** When agent or person is unclear, choose person and raise an `[SME REVIEW]` item.
- **Extraction is a separate step.** A rule on an amount read from an email is still deterministic once the amount is extracted. The extraction (IXP, agent) is a step of its own; the rule is a decision table over its output.
- **One rule, one outcome.** Split a PDD rule that decides two things before tabling it. Tiers ("under 1,000 … up to 10,000 … above") are rows of one decision table.

## 2. Decision tables

One decision per output decided from the same inputs: one table, one row per rule or tier, numbered `DT1`, `DT2`, … (`D<n>` is an open item of Action Required). Example:

```markdown
#### DT1 — Approval route
**Hit policy:** UNIQUE
**Inputs:** `invoiceAmount` (number), `vendorStatus` (string: "new", "active", "blocked")
**Output:** `approvalRoute` (string: "auto", "manager", "director", "reject")
**Runs in:** <RUNS_IN>

| # | invoiceAmount | vendorStatus | → approvalRoute | Rule |
|---|---|---|---|---|
| 1 | - | "blocked" | "reject" | BR-02: a blocked vendor's invoice is rejected |
| 2 | < 1000 | "active" | "auto" | BR-03: an active vendor's invoice under 1,000 is approved automatically |
| 3 | [1000..10000) | not("blocked") | "manager" | BR-04: an invoice from 1,000 up to 10,000 goes to the manager |
| 4 | >= 10000 | not("blocked") | "director" | BR-05: an invoice of 10,000 or more goes to the director |
| 5 | < 1000 | "new" | "manager" | BR-06: a new vendor's invoice under 1,000 goes to the manager |
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
- **Complete.** Aim for every combination of inputs to match a row. Under `UNIQUE`, cover the remaining combinations with rows of their own (`not(...)`, open ranges), because an all-`-` row would overlap every other row. A last all-`-` default row is valid only under `FIRST`, where order makes it the fallback.
- **Design intent, not proof.** Hit policy and completeness describe what the table must do. Do not certify a table overlap-free or complete by reading it: the build proves it (see Proof).
- **Traceable.** Every row cites its BR in `Rule`; a row that only completes the table cites `[DEFAULT]` or `[SME REVIEW]` instead. Every decision BR appears in at least one row.
- **Independent test cases.** Write one test case per row in the Testing Strategy (RPA §17; BPMN §9 Gateway / Branch Coverage; the Testing Strategy of every other template). Take its inputs and expected output from a PDD example or an SME-confirmed value, never from the row itself: a case derived from the row passes even when the row is wrong. When neither source gives one, write the case with `[SME REVIEW]` in place of the expected output.
- **Proof.** The genome component that hosts the decision (the BPMN or RPA component) carries its test cases as acceptance criteria, and the build proves the table with tools. For a `.dmn` business rule: `uip rules validate <PROJECT_DIR> --output json`, then `uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json` once per test case. For coded logic in an RPA process: one unit test per test case. A failing case is a defect in the row or in the test case's source; resolve it with the SME, never by editing the expected output to match.
- **Runs in.** BPMN: the Rule step's node key; gateways route on its output. RPA: the step, and the coded logic or lookup that evaluates it. Case: the `business-rule` task that evaluates it, or the `=js:` condition that routes on it. Flow: the Rule node, its table a Business Rules Projects row. API workflow: the step. Coded app: the page or component. Placement: [Component Placement Guide → Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step).
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
- **Applied by a person:** in `Where it runs`, name the task and the role. In BPMN the task is a Human step, also listed in §5 Human Tasks; in a Case it is an `action` task whose Persona is that role.
- **No reasoning rules:** write `None. Every rule is deterministic.` Don't leave the section out.

## 4. Coverage

**Keep the source's rule IDs.** A source that numbers its rules (`BR-001`, `BR-F01`, `FBR-001`) keeps each ID verbatim, in every SDD that applies the rule. Only a source that numbers none gets `BR-01`, `BR-02`, … in source order across every home. A rule the design adds (a validation the example values imply) takes the next free ID and its `[DEFAULT]` or `[SME REVIEW]` marker. A decision-table row or reasoning row is the rule's definition; no separate register repeats it — so the definition carries the rule itself: the row's `Rule` cell reads `BR-12: a blocked vendor's invoice is rejected`, in the source's words, never the ID alone. A home's IDs skip the ones defined in another home; that gap is expected.

Before the ready flip, run the coverage check on every SDD file of the design, with the source the rules came from:

```bash
node "<SKILL_DIR>/scripts/br-coverage.mjs" --source "<PDD_PATH>" "<SDD_PATH>" [<CHILD_SDD_PATH> ...]
```

It fails a source rule ID no SDD line carries, a rule cited by its ID alone, an ID only the SDD has with no `[DEFAULT]` or `[SME REVIEW]` marker, and an SDD set with no Business Rules section. Repair each `FAIL:` line in its home and run it again until it prints `OK`; the SDD is not `ready` before. A source that is not a text file (a `.docx`, a `.pdf`), or numbers no rules, takes the same check by hand:
1. List the BR IDs extracted from the source.
2. List the BR IDs cited in each home from the [§1 table](#homes-per-template). All decision-table rows together count as one home.
3. Every extracted ID appears in exactly one home list, and no home cites an ID the extraction lacks.
