# Variables & I/O — the doctrine

Single source for how data flows through a case. Emit-side entry shapes stay in the maestro-case
variables plugins; SDD cell grammar stays in the planner render rules — both cite these IDs.

## The doctrine: reference producers directly; declare only what has no producer

**[K-VAR-1] Task-output xref is the DEFAULT wiring.** A downstream input or condition that consumes one
upstream task's output references it directly — SDD forms: whole-value `<- "Stage"."Task".out` (the bare
`"<Stage>"."<Task>".<outputName>` cell spelling is equivalent) or in-expression
`vars.$xref('Stage','Task','out')`; emitted form `=vars.<outputId>`. The emitting task
self-declares the output (its `data.outputs[]` entry IS the declaration — no root companion, no case
variable). Validate-verified: a full bare-mint output entry resolves from downstream inputs, conditions,
and interrupting stage entries with zero root declarations (probes p11b/p07c, as of 1.198.0-preview.102).

**[K-VAR-2] Declare a case variable (§1.5 row / root `inputOutputs[]`) ONLY for:** (a) `In`/`Out`
arguments; (b) trigger-payload extraction (K-VAR-3); (c) case-level state read by a condition or ≥ 2
consumers; (d) renaming or custom `Default`/`Type`/`Description` on an output. Minting a row to relay one
task's output to one consumer is the **case-var relay anti-pattern** — reference it directly and drop the
row.

**[K-VAR-3] Trigger outputs REQUIRE a root companion.** Validation never scans trigger-node outputs
(FE `ValidateCaseManagementFlowVariableUtils.ts` collects task/rule/root arrays only; probes p12/p12b): a
trigger payload field is referenceable as `=vars.<name>` only through a root `inputOutputs[]` entry. In the
SDD this is exactly a §1.5 `Variable` row with `sourceTriggers` (T-number) + `sourceFields` (payload path)
— the sanctioned "case variable" use, not a relay.

**[K-VAR-4] Full-shape output entries or nothing.** An emitted task output carries the complete bare-mint
shape — `name, type, id, var, value, source, target, elementId` — a partial entry (missing
source/target/elementId) is invisible to the resolver: `Variable 'vars.X' does not exist` (probe p11).
`type` is required on every output entry. The resolver matches on `id` alone, case-sensitive.

## Outputs grammar (every task's Outputs rows)

**[K-VAR-5] Two operators.** Extract `-> caseVar`: `Field` = non-empty runtime path (`response.status`,
`Action`, `Error.code`), emitted `source` is `=<Field>` verbatim. Set/compute/copy `caseVar = <expr>`:
`Field` = `—`; expr is a literal, `=js:(...)`, or `=vars.X.Y` copy. The target case variable must already
be declared (K-VAR-2 rows only — a `->` to a brand-new name is a declaration bug, unless it is the
self-declaring bare output of K-VAR-1).

**[K-VAR-6] One writer per target per task.** Each target variable appears in at most one Outputs row per
task; mixing `->` and `=` on the same target in one task is rejected. Self-binding no-ops
(`caseVar = =vars.caseVar`) are forbidden — they mask a missing producer; computed self-references
(`=js:(vars.x + 1)`) are fine.

**[K-VAR-7] Lineage closure.** Every consumer of `vars.X` needs a producer that fires earlier (stage
order, then task order) — a trigger extraction (K-VAR-3), a task Outputs row, an action button's
`Maps To`, an `In` category, or a non-empty `Default`. Direct xrefs (K-VAR-1) close by ordering alone.
Never close lineage by aliasing a produced datum into an unrelated existing variable, guessing producers,
or silently retagging `Category`/inventing a `Default`.

**[K-VAR-8] Category semantics.** `In` = caller-supplied at start (or `Default`-initialized for
event/timer triggers); `sourceFields` always empty; single optional `T<N>` selects a non-primary trigger.
`Out` = returned to caller; needs a producer row or `Default`; `sourceTriggers` forbidden. `Variable` =
internal state; trigger-fed rows per K-VAR-3 (CSV `sourceTriggers` requires keyed
`T<N>: <path>; T<M>: <path>` — one entry per T-number). A `file` variable is a JobAttachment record; a
file-typed `In` carries the caller pre-upload obligation.

<!-- END: variables-io.md -->
