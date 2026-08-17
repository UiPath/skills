# Expressions — namespaces and gates

**[K-EXPR-1] Expression forms.** Case expressions are `=js:`-prefixed JavaScript over case state
(`vars.<id>`, `metadata.<key>`). Assignment operators are forbidden in every case expression. Reference
forms in bindings: `=vars.<id>` (variable / upstream output — K-VAR), `=vars.<id>.<sub>` (dot-path into a
structured value), `=metadata.<key>`, `=metadata.ExternalId` (the platform-minted case identity — the
canonical `caseId` binding; it is NOT a task output), `=bindings.<id>` (registered resources),
`=trigger.<field>`, `=jsonString:<json>` (connector essentialConfiguration carry-through only).

**[K-EXPR-2] `conditionExpression` gates CASE STATE only.** No `event` namespace exists — a rule's
expression cannot read the incoming event payload. In-rule extract-then-gate (extract `response.X ->
caseVar` and gate `=js:vars.caseVar` on the SAME rule) does NOT work at runtime: the gate evaluates before
the extract writes. To condition on payload content, extract on the connector rule and place the gate on a
DOWNSTREAM stage-entry / task-entry condition.

**[K-EXPR-3] Use strict equality** (`===` / `!==`) in `=js:` guards, and write mutually-exclusive branch
guards as exact inverses (`=== v` / `!== v`) so completion and divert rows cannot dual-fire (K-STG-5).

**[K-EXPR-4] Thresholded policy is executable, not prose.** A source rule tying an actor or step to a
comparator ("Credit Analyst only over $5M") must appear in an executable cell — a guarded WHEN/IF, a
computed owner/recipient (`=js:vars.loanAmount > 5000000 ? "Role:CreditAnalyst" : "Role:Underwriter"`), or
a task-entry gate — with the numeral written out, actor and attribute on one line. Prose or persona-table
mention alone is a render failure.

<!-- END: expressions.md -->
