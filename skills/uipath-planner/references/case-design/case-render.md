# Case Render — SDD Section 1 content rules

What Section 1 (Case Definition) must contain before the model may render. Shared facts: cite, don't
restate — [K-TYP](../case-knowledge/facts/types.yaml), [K-PAIR](../case-knowledge/facts/pairing.yaml),
[K-NAME](../case-knowledge/facts/naming.yaml), [K-SLA](../case-knowledge/facts/sla.yaml),
[K-VAR](../case-knowledge/semantics/variables-io.md).

## 1.1 Case Metadata

| Field | Required? | Value shape | If missing |
|---|---|---|---|
| Case Name | yes | PascalCase identifier (`MortgageLoanOrigination`) | Block Approve. Ask. |
| Description | optional | One sentence | `—` |
| Identifier prefix | yes | UPPER, 2–4 chars (K-NAME-4) | Default mechanically; record in ledger |
| Case SLA | conditional | Duration (`5 business days`) | `—` when no SLA; else block Approve |
| SLA Type | conditional | `time-based` / `condition-based` | Default `time-based` when Case SLA set with no overrides. FE persists `condition-based` whenever ≥ 1 `slaRules[]` entry carries a non-empty `conditionExpression` (PO.Frontend `CaseManagementSlaProperties.tsx:27-30`). `condition-based` requires the Variable SLA Rules table; `time-based` omits it |
| SLA Title | conditional | Non-empty root-unique title (K-SLA-2, K-NAME-3) | Omit the row when Case SLA is `—` (never `—` here); else default `SLA Rule 1` + ledger. A title referenced by `sla-status-change` must be concrete |
| Case App | optional | `Enabled` / `Disabled` (`metadata.caseAppEnabled`) | Default `Disabled`; ledger |
| Task-output passing | optional | `Direct` / `Shared` (`metadata.caseDirectlyPassTaskOutputs`) | Default `Direct` |

**Pre-Approve validation parity.** Before Approve, apply the platform's own name/SLA checks — safe display
characters, mechanical repair, uniqueness scopes (K-NAME-1/2/3), SLA entry requirements and bounds
(K-SLA-2) — to everything the skill generates or carries into display/title fields. These are blocking
authoring errors, not style warnings. Never normalize external lookup names (K-NAME-2); never silently
clamp numeric violations (K-NAME-5) — surface and Ask.

## 1.2 Case-level SLA escalation

Required when Case SLA is set. Both rows always render; no `—` in any cell.

| Threshold | Trigger | Recipient | Display Name |
|---|---|---|---|
| At-risk | `<pct>%` of case SLA (defaults: K-SLA-6) | `UserGroup: <owner-group>` / `User: <name>` | Non-empty root-unique title (K-NAME-3) |
| Breached | 100% | One tier up — leadership; Compliance for regulation-driven cases (K-SLA-6) | Non-empty root-unique title |

`Display Name` defaults to `Escalation Rule {N}` only when no `sla-status-change` row references it.
Default substitutions → ledger (`default applied — user did not name recipient`).

## 1.2b SLA Response Map

Required whenever ANY SLA is configured (case, stage, or `action` task). One row per `(Scope, SLA,
Status)`. Columns: `Scope | SLA | Status | Response | Target | Interrupting | Rationale`.

| Field | Value |
|---|---|
| Scope | `case`, `stage: <StageName>`, or `task: <TaskName>` |
| SLA | the target's SLA Title (or a Variable SLA Rules Display Name) |
| Status | `At-Risk` / `Breached` — one row each |
| Response | closed set + selection test: K-SLA-4/5 |
| Target | `—` for `notify-only`; task name for `start-task` (task lives in the breached stage); stage name for `enter-stage`; the produced exit row for `exit-stage`/`exit-case` |
| Interrupting | `—` for `notify-only` AND for every `start-task` (a task entry interrupts nothing — never `Yes`/`No`); otherwise `Yes`/`No` matching the produced stage-entry row (K-STG-3) |
| Rationale | why this response fits the source |

**Closure both ways (blocking):** every non-`notify-only` row has its matching rule elsewhere in the SDD
(an `sla-status-change` task-entry row for `start-task`, stage-entry row for `enter-stage`, a stage-exit
row, or a §1.4a row), and every `sla-status-change` row in the SDD has a row here. An Interrupting mismatch
between map cell and produced row is blocking. **Default:** no stated response → both statuses
`notify-only`, Target and Interrupting `—`; never invent a stage/task/routing for a notification (K-SLA-4).

## 1.3 Triggers

≥ 1 trigger. One row per triggering event, numbered sequentially from **T02** (T01 = the case file). The
T-number keys §1.5 trigger-payload rows (K-VAR-3).

| Field | Required? | Value |
|---|---|---|
| T# | yes | `T<N>`, starts at `T02` |
| Trigger Type | yes | `Manual` / `Intsvc.TimerTrigger` / `Intsvc.EventTrigger` — author tokens; on-disk mapping K-TYP-4 (`Manual` is shorthand: serviceType is ABSENT on disk) |
| Source | conditional | Connector/system for event; schedule expression for timer; `Manual` literal |
| Configuration | conditional | User intent only, business terms. `Intsvc.EventTrigger` MUST have a concrete operation phrase |

**Configuration cell — write:** event → the operation in business terms (`Record created`, `Email received
in Inbox; filter: subject contains "URGENT"`); tenant case-entity starts keep the object name in Source and
the business event in Configuration; timer → cycle/duration (`daily at 09:00 UTC`); manual → `N/A`.
**Forbidden in Configuration** (resolved at planning time): CLI enum values (`CALENDAR_CREATED`), default
modes (`polling`/`webhook`), meta notes (`No required event parameters`), activity slugs/HTTP
methods/spec-discovered detail.

Payload-field → variable mapping lives ONLY in §1.5 (`sourceTriggers`/`sourceFields`) — never in this
table. **Tenant object starts are not Manual:** a record-created start is an `Intsvc.EventTrigger` row even
when tenant provisioning is missing — unresolved detail becomes a placeholder later, never a trigger-type
downgrade. Unresolved event resolution (`connectionId`/`activityTypeId`) → `high` review item.

## 1.3a Trigger Filter (conditional)

Renders only when ≥ 1 trigger declares a filter. AND/OR tree; nested `{op, clauses}` groups flatten in the
rendered table. Operators (PascalCase, case-sensitive): `Equals`, `NotEquals`, `Contains`, `NotContains`,
`StartsWith`, `EndsWith`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `In`,
`NotIn`, `IsNull`, `IsNotNull`. Columns: `Field | Operator | Value | Literal?`. Avoid `Literal: No` for
unverified runtime expressions — it forces lossy JMESPath fallback; prefer literals or a review item.

## 1.4 Case Completion Conditions

≥ 1 row, `Marks Case Complete: Yes`. Columns `WHEN | IF | Marks Case Complete | Exit Type | Display Name`.
Legal WHEN: K-PAIR-1 case-completion set; `Yes` + `selected-stage-*` blocks Approve (K-PAIR-2). Exit type
`exit-only`. **Display Name defaulting (all condition tables):** carry the author's value verbatim; blank →
skill defaults (`Entry Rule {N}` for entry/task-entry; `Complete Rule {N}` / `Exit Rule {N}` for
exit tables by Marks-Complete), `N` = 1-based within the same label kind; never invent a label otherwise.

## 1.4a Case Exit Conditions (alternate disposition)

Optional, `Marks Case Complete: No` — secondary-stage terminals (Withdrawn / Rejected / Cancelled)
(K-PAIR-6, K-STG-4). Legal WHEN: K-PAIR-1 case-exit set; exit type `exit-only` / `wait-for-user`. When the
case has ≥ 1 secondary stage AND §1.4a is empty → `high` review item (`Alt-disposition exits missing`).

## 1.5 Case Variables

**Declare-vs-xref decision per candidate value: K-VAR-1/2/3.** Only `In`/`Out` args, trigger-payload
`Variable`s, and case-level state read by a condition or ≥ 2 places get a row; one task's output feeding
one consumer is referenced directly — the case-var relay is the anti-pattern (K-VAR-2). Authoring is
declarative: `Category` + `sourceTriggers` + `sourceFields` drive build-time classification — no inference
from prose.

| Column | Required? | Notes |
|---|---|---|
| Name | yes | camelCase, no role suffix (K-NAME-4) |
| Category | yes | `In` / `Out` / `Variable` — never `—` (K-TYP-6, semantics K-VAR-8) |
| Type | yes | K-TYP-5 enum; `jsonSchema` vs `string` per K-TYP-5; `file` = JobAttachment |
| sourceTriggers | conditional | `Variable`: single `T<N>` or CSV; `In`: optional single `T<N>` (blank = primary T02, never CSV); empty for pure state and `Out` (K-VAR-8) |
| sourceFields | conditional | `Variable` only. Single trigger → bare path (`response.subject`); CSV → keyed `T<N>: <path>; T<M>: <path>`, one entry per T-number, strict. Always empty on `In`. Dot-paths only — no array indexing |
| Default | optional | Concrete default or empty |
| Description | yes | One line |

- **Out-arg producer rule:** every `Out` row has a `Default` OR a task Outputs row targeting it
  (`-> {name}` / `{name} = {expr}`) — pre-checked at the Approve gate (K-VAR-7).
- **Config-as-In:** runtime business rules (priority bands, thresholds, taxonomies) ride ONE `In` variable
  — `Type: string` with a JSON `Default` for opaque blobs, `Type: jsonSchema` + `body` when the FE picker
  must navigate sub-fields (K-TYP-5). Overridable at case start, consumed by agents.
- **File In-args** carry the caller pre-upload obligation (K-VAR-8) — surfaced via the Caller-obligation
  block at review.
- **Outputs operators** (`->` extract with verbatim runtime path; `caseVar = expr` set/compute/copy;
  one writer per target per task): K-VAR-5/6. Worked patterns: [case-sdd-examples.md](../../assets/templates/case-sdd-examples.md).

<!-- END: case-render.md -->
