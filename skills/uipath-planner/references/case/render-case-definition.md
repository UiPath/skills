# Render — Section 1: Case Definition

What each Section 1 cell of a case `sdd.md` must contain before the model may render. Semantics live in
[model.md](model.md), [variables.md](variables.md), and [slas.md](slas.md) — this file defines cells, not
rules. Render shape: [case-sdd-template.md](../../assets/templates/case-sdd-template.md).

## 1.1 Case Metadata

| Field | Required? | Value shape | If missing |
|---|---|---|---|
| Case Name | yes | PascalCase identifier (`MortgageLoanOrigination`) | Block approval. Ask. |
| Description | optional | One sentence | `—` |
| Identifier prefix | yes | UPPER, 2–4 chars | Default mechanically from the PascalCase name; record provenance |
| Case SLA | conditional | `<count> <unit>`, unit ∈ `min h d w m` — bounds in [slas.md](slas.md) | `—` when the case has no SLA; otherwise block approval |
| SLA Type | conditional | `time-based` / `condition-based`. The platform persists `condition-based` whenever ≥ 1 SLA rule carries a non-empty condition expression. `condition-based` requires the Variable SLA Rules table; `time-based` omits it | Default `time-based` when Case SLA is set with no overrides |
| SLA Title | conditional | Non-empty root-unique title, no `:` | Omit the row when Case SLA is `—` (never render `—` here); else default `SLA Rule 1` + provenance. A title referenced by `sla-status-change` must be concrete |
| Case App | optional | `Enabled` / `Disabled` | Default `Disabled`; record provenance |
| Task-output passing | optional | `Direct` / `Shared` | Default `Direct` |

**Pre-approval validation parity.** Before approval, apply the display-name and SLA-entry checks from
[model.md § Naming rules](model.md#naming-rules) and [slas.md](slas.md) to every generated or carried
display/title field. These are blocking authoring errors. Never normalize external lookup names; never
silently clamp an out-of-range value — surface it and Ask, naming the original value.

## 1.2 Case-Level SLA Escalation

Required when Case SLA is set. Both rows always render with concrete cells — no `—`.

| Threshold | Trigger | Recipient | Display Name |
|---|---|---|---|
| At-Risk | `<pct>%` of case SLA (defaults: [slas.md](slas.md)) | `UserGroup: <owner group>` / `User: <name>` | Non-empty root-unique title, no `:` |
| Breached | 100% | One tier up — leadership; Compliance for regulation-driven cases | Non-empty root-unique title, no `:` |

`Display Name` defaults to `Escalation Rule {N}` only when no `sla-status-change` row references it.
Defaulted recipients get provenance `default applied — user did not name recipient`.

## 1.2b SLA Response Map

Required whenever ANY SLA is configured (case, stage, or `action` task). One row per
`(Scope, SLA, Status)`. Response selection: [slas.md](slas.md).

| Column | Cell rule |
|---|---|
| Scope | `case`, `stage: <StageName>`, or `task: <TaskName>` |
| SLA | The target's SLA Title (or a Variable SLA Rules Display Name) |
| Status | `At-Risk` or `Breached` — one row each |
| Response | `notify-only` \| `start-task` \| `enter-stage` \| `exit-stage` \| `exit-case` |
| Target | `—` for `notify-only`; the task name for `start-task` (the task lives in the breached stage); the stage name for `enter-stage`; the produced exit row for `exit-stage` / `exit-case` |
| Interrupting | `—` for `notify-only` AND for every `start-task` — a task entry interrupts nothing, never `Yes`/`No`. Otherwise `Yes`/`No`, matching the produced stage-entry row |
| Rationale | Why this response fits the source |

**Closure both ways (blocking):** every non-`notify-only` row has its matching rule elsewhere in the SDD
(an `sla-status-change` task-entry row for `start-task`, a stage-entry row for `enter-stage`, a stage-exit
row, or a §1.4a row), and every `sla-status-change` row in the SDD has a row here. An Interrupting mismatch
between the map cell and the produced row is blocking. **Default:** no stated response → both statuses
`notify-only` with Target and Interrupting `—`; never invent a stage, task, or routing change for a
notification.

## 1.3 Triggers

≥ 1 trigger. One row per triggering event, numbered from **T02** (T01 is the case file). The T-number keys
§1.5 trigger-payload rows.

| Field | Required? | Value |
|---|---|---|
| T# | yes | `T<N>`, sequential from `T02` |
| Trigger Type | yes | `Manual` / `Intsvc.TimerTrigger` / `Intsvc.EventTrigger` — author tokens; on-disk mapping in [model.md](model.md) |
| Source | conditional | Connector or system for event; schedule expression for timer; `Manual` literal |
| Configuration | conditional | User intent in business terms. An event trigger MUST have a concrete operation phrase |

**Configuration cell:** event → the operation in business terms (`Record created`, `Email received in
Inbox; filter: subject contains "URGENT"`); tenant case-entity starts keep the object name in Source and
the business event in Configuration; timer → cycle or duration (`daily at 09:00 UTC`); manual → `N/A`.
**Forbidden in Configuration** (resolved at build time): CLI enum values (`CALENDAR_CREATED`), delivery
modes (`polling` / `webhook`), meta notes (`No required event parameters`), activity slugs, HTTP methods.

Payload-field → variable mapping lives ONLY in §1.5 ([variables.md](variables.md)) — never in this table.
A case that starts when a tenant record is created is an `Intsvc.EventTrigger` row even when the object is
not provisioned — unresolved detail becomes a placeholder later, never a downgrade to `Manual`. Unresolved
event resolution (`connectionId` / `activityTypeId`) → high review item.

## 1.3a Trigger Filter (conditional)

Renders only when ≥ 1 trigger declares a filter. AND/OR tree; nested `{op, clauses}` groups flatten in the
rendered table. Columns: `Field | Operator | Value | Literal?`. Operators (PascalCase, case-sensitive):
`Equals`, `NotEquals`, `Contains`, `NotContains`, `StartsWith`, `EndsWith`, `GreaterThan`,
`GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `In`, `NotIn`, `IsNull`, `IsNotNull`. Avoid
`Literal: No` for unverified runtime expressions — it forces a lossy fallback; prefer literal values or a
review item.

## 1.4 Case Completion Conditions · 1.4a Case Exit Conditions

Columns: `WHEN | IF | Marks Case Complete | Exit Type | Display Name`. §1.4 = `Yes` rows (≥ 1 required);
§1.4a = `No` rows (alternate dispositions: Withdrawn / Rejected / Cancelled). Legal WHEN per
[model.md § Lifecycle gates](model.md#lifecycle-gates); exit types per
[model.md § Exit types](model.md#exit-types).

**Display Name defaulting (every condition table):** carry the author's value verbatim; blank → default
`Entry Rule {N}` (entry / task-entry) or `Complete Rule {N}` / `Exit Rule {N}` (exit tables, by
Marks-Complete), `N` = 1-based within the same label kind. Never invent a label otherwise.

When the case has ≥ 1 secondary stage AND §1.4a is empty → high review item (`Alt-disposition exits
missing`) — the case cannot exit non-happy paths cleanly.

## 1.5 Case Variables

Declare a row ONLY per the declare-vs-direct-reference test in [variables.md](variables.md) — one task's
output feeding one consumer is referenced directly, never declared. Authoring is declarative: `Category` +
`sourceTriggers` + `sourceFields` drive build-time classification; nothing is inferred from prose.

| Column | Required? | Cell rule |
|---|---|---|
| Name | yes | camelCase, no role suffix |
| Category | yes | `In` / `Out` / `Variable` — never blank ([variables.md](variables.md)) |
| Type | yes | `string` `integer` `float` `double` `boolean` `date` `datetime` `jsonSchema` `file` |
| sourceTriggers | conditional | `Variable`: single `T<N>` or CSV. `In`: optional single `T<N>` (blank = primary trigger, never CSV). Empty for pure state and `Out` |
| sourceFields | conditional | `Variable` only. One trigger → bare payload path (`response.subject`); CSV → keyed `T<N>: <path>; T<M>: <path>`, one entry per listed T-number. Always empty on `In`. Dot-paths only — no array indexing |
| Default | optional | Concrete default or blank |
| Description | yes | One line |

- **Out-arg producer rule:** every `Out` row has a `Default` OR a task Outputs row targeting it
  (`-> {name}` / `{name} = {expr}`) — pre-checked at the approval gate.
- **Config-as-In:** runtime business rules (priority bands, thresholds, taxonomies) ride ONE `In` variable —
  `string` with a JSON `Default` for opaque rule-sets; `jsonSchema` + `body` when the picker must navigate
  sub-fields.
- **File In-args** carry the caller pre-upload obligation — surfaced via the Caller-obligation block in
  [review.md](review.md).
