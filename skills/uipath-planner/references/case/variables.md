# Variables & Data Flow

How data moves between triggers, tasks, conditions, and the caller. Lifecycle gates, naming, and stage
semantics: [model.md](model.md). SDD cell rendering: [render-case-definition.md](render-case-definition.md)
(Case Variables table) and [render-stages-tasks.md](render-stages-tasks.md) (task Inputs/Outputs).

## Reference producers directly

A downstream input or condition that consumes one upstream task's output references the output
directly — the emitting task's output entry is its own declaration, and no Case Variables row exists:

| Where the value is used | SDD spelling |
|---|---|
| The output IS the whole input value | `<- "Stage"."Task".out` — the bare `"<Stage>"."<Task>".<outputName>` cell form is equivalent |
| One term inside a larger `=js:` expression | `vars.$xref('Stage','Task','out')` |

The build resolves both spellings to the output's reference id. Direct references close lineage by
ordering alone (producer task before consumer).

## When to declare a Case Variables row

Declare a Case Variables row ONLY when one of these holds:

1. `In` / `Out` argument (the case boundary).
2. Trigger-payload extraction (see below — the only way a trigger field becomes referenceable).
3. Case-level state read by a condition (`IF`) or by ≥ 2 consumers.
4. The value needs a rename or a custom `Default` / `Type` / `Description`.

A row that relays one task's output to one consumer is the relay anti-pattern —
[review.md](review.md) flags it (`rev_relay_var`).

Declaring a row does not make the value readable earlier — see below.

## Gate on the producer, never on the variable it writes

A rule is evaluated **before** the extract of the task that triggered it. So a gate keyed on a task's
completion that reads the case variable that task's Outputs row feeds sees the value from the previous
pass — `null` on the first one. The branch silently never fires, the stage stalls, and nothing errors.

| Gate | `IF` reads | At gate time |
|---|---|---|
| `selected-tasks-completed("Decide")` + `=js:vars.decision === "reject"`, where `Decide` declares `Action -> decision` | the case variable `Decide` writes | ✗ stale / `null` |
| `selected-tasks-completed("Decide")` + `=js:vars.action === "reject"`, where `action` is `Decide`'s own output | the producing output | ✓ populated |

**Rule:** when a condition's WHEN names a task, its `IF` MUST read that task's own output. Keep the `->`
extract whenever the value must persist (Case App, audit, a later stage reads it) — the extract is not
what the gate reads.

Applies wherever the WHEN names the producer: stage-exit `selected-tasks-completed`, task-entry
`selected-tasks-completed`, and the `selected-stage-exited` lane entry paired with a diverting exit —
that entry repeats the origin exit's guard, so it repeats the producer reference too. Guard pairs stay
exact inverses of each other. (Verified on uip 1.198.0-preview.102, 2026-08-18.)

## Trigger payloads

Validation never reads trigger-node outputs (verified on uip 1.198.0-preview.102). A trigger payload
field is referenceable as `=vars.<name>` ONLY through a Case Variables `Variable` row carrying
`sourceTriggers` (the trigger's T-number) + `sourceFields` (the payload path).

## Category semantics

| Category | Meaning | sourceTriggers | sourceFields | Closure |
|---|---|---|---|---|
| `In` | Caller-supplied at start; `Default`-initialized for event/timer triggers (no caller) | blank = primary trigger; a single `T<N>` selects another — never CSV | always empty (an In-arg selects a trigger, extracts nothing) | closed at case start |
| `Out` | Returned to the caller | forbidden | empty | needs a producer Outputs row or a `Default` |
| `Variable` | Internal state | single `T<N>`, or CSV for multi-trigger | bare path for one trigger; keyed `T<N>: <path>; T<M>: <path>` for CSV — one entry per listed T-number | producer or `Default` |

**Types:** `string`, `integer`, `float`, `double`, `boolean`, `date`, `datetime`, `jsonSchema`,
`file`. `json` is not a type. Use `jsonSchema` (with `body`) when downstream picks sub-fields;
`string` for opaque JSON blobs nothing dereferences. `file` is a JobAttachment record — a file `In`
argument carries the caller pre-upload obligation ([review.md](review.md) surfaces it).

## Outputs rows

| Operator | Cell form | `Field` cell | Purpose |
|---|---|---|---|
| Extract | `-> caseVar` | Non-empty runtime path (`response.status`, `Action`, `Error.code`) — emitted as the source verbatim | Capture a response field into a declared variable |
| Set / compute / copy | `caseVar = <expr>` | `—` | Assign a literal, `=js:(...)`, or `=vars.X.Y` copy at task completion |

1. The target variable is already declared per the rules above; a `->` to a new name is valid only as
   the task's own self-declaring output.
2. One row per target per task; never mix `->` and `=` on the same target in one task.
3. Self-binding no-ops (`x = =vars.x`) are forbidden — they mask a missing producer. Computed
   self-references (`x = =js:(vars.x + 1)`) are fine.
4. Never alias a produced datum into an unrelated existing variable to close lineage — declare a
   dedicated row or confirm the reuse.

## Lineage closure

Every consumer of `vars.X` needs a producer that fires earlier — stage order first, then task order
within the stage: a trigger extraction, a task Outputs row, an action button's `Maps To`,
`Category: In`, or a non-empty `Default`. [review.md](review.md) checks closure before the
confirmation.

## Expressions

- `=js:`-prefixed JavaScript. Namespaces available to `=js:` evaluation: `vars`, `response`,
  `bindings`, `iterator`, `metadata`. Assignment operators are forbidden in every case expression.
- A rule's `conditionExpression` gates CASE STATE only (`vars.*`, `metadata.*`) — there is no `event`
  namespace. In-rule extract-then-gate does not work at runtime (the gate evaluates before the
  extract writes): extract `response.field -> caseVar` on the connector rule and gate a DOWNSTREAM
  condition instead.
- Use strict equality (`===` / `!==`); write mutually exclusive branch guards as exact inverses so
  completion and divert rows cannot dual-fire.
- Thresholded policy ("Credit Analyst only over $5M") lands in an executable cell — owner/recipient,
  WHEN/IF, or a task input — with the numeral written out (`5000000`), actor and attribute on one
  line. Prose or a persona-table mention alone is a render failure ([review.md](review.md)).

## Binding-cell forms (task Inputs)

| Form | Meaning |
|---|---|
| `<literal>` | Plain string / number / boolean |
| `=vars.<id>` / `=vars.<id>.<sub>` | Declared variable or upstream output; dot-path into structured values |
| `<- "Stage"."Task".out` / `vars.$xref('Stage','Task','out')` | Direct output references (above) |
| `=bindings.<id>` | Registered resource (app, process, connection) |
| `=metadata.<key>` | Case metadata |
| `=metadata.ExternalId` | The platform-minted case identity — the canonical `caseId` binding; NOT a task output, never a `->` extraction |
| `=trigger.<field>` | Trigger payload field |
| `=js:<expr>` | Inline JavaScript (required when operators are involved) |
| `=jsonString:<json>` | JSON-as-string — connector `essentialConfiguration` carry-through only |
| `=datafabric.<path>` | Data Fabric reference |
| `=orchestrator.JobAttachments` | File slot |
| `=response` / `=result` / `=Error` | Conventional response handles |

Bare field-name lists (`**Inputs:** a, b, c`) are forbidden — use the table with one form per cell.
