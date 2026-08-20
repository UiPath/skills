# Case SDD Spec & Validator

The normative render contract for a case `sdd.md`: document skeleton, per-cell rules, markers, and the checks that gate the confirmation and the write. Design semantics live in [case-design-layers-guide.md](case-design-layers-guide.md); conversation flow in [case-design-lane-guide.md](case-design-lane-guide.md); the render shape is [case-sdd-template.md](../assets/templates/case-sdd-template.md).

**Template shape is part of the contract.** A valid in-memory model is not enough: the rendered `sdd.md` preserves the full template structure. A prose summary is never an SDD; the compact confirmation is never an SDD substitute.

**The validator** mechanizes the deterministic checks: run `python3 "<this skill's folder>/scripts/audit_sdd.py" <sdd path> [--draft <draft path>]` — RUN it and act on findings; never open the script source. It parses the canonical tables in the layers guide (task types, lifecycle gates — per gate slot) and this file (naming rules), so those tables are load-bearing.

What it enforces (prose elsewhere defers to this list instead of restating it):

1. Document skeleton — the § Template conformance gate: scaffold order + `planner-handoff:v1` marker, section/stage/task headings and numbering, per-block markers, per-type detail blocks, summary-only sections, literal `\n`, plain-text `<UNRESOLVED>`, the Case Variables header.
2. Closed enums and pairing — task-type enum; WHEN legality per gate slot (stage entry, task entry); WHEN × Marks-Complete pairing inside exit tables; Exit Type × Marks-Complete legality; `return-to-origin` banned from case exits.
3. Names — § Naming rules charset on stage/task names; stage-label and task-name uniqueness case-wide.
4. SLA references — `sla-status-change` arity (2 = breach, 3 = at-risk), target is `root` or an exact stage name, title matches an SLA declared on that target.
5. Data closure — consumed `=vars.X` declared + produced (lineage); `Out` rows carry a Default or a producing Outputs row; Buttons `Maps To` identifiers that occur nowhere else are flagged as dead routes.
6. Cells — `Recipient` typed prefixes; empty task Entry Condition tables; forbidden skill-internal vocabulary.
7. Structure — ≥ 1 `Marks Case Complete: Yes` row; `wait-for-user` ↔ `user-selected-stage` pairing both ways.
8. Draft parity (`--draft`) — ordered stage/task inventory preserved; every draft `=js:` expression present; comparator thresholds encoded executably, not prose-only.

If `python3` is unavailable, verify this list manually — every item must hold before the `ready` flip.

## Template conformance gate

The exact rendered SDD text must pass this gate before it leaves the lane — in every mode against the **on-disk file assembled by the write-early cadence, before the `Status: ready` flip**. The gate is mechanized end-to-end by the validator — run it instead of eyeballing; one structural Read is allowed to repair findings. This is a render check, not a second design review. Do not use the read to redesign the case.

Required shape:

- First heading: `# SDD — {Case Name}`.
- `## Document History`, then the `## Planner Handoff` header + `<!-- planner-handoff:v1 -->` marker, then `## Table of Contents` — the universal planner scaffold (Rule 5); the case body follows.
- Exact section headings: `## Section 1: Case Definition`, `## Section 2: Stages & Tasks`, `## Section 3: Personas & App Views`, `## Section 4: Integrations`.
- Section 1 contains `### Case Metadata`, `### Case Triggers`, `### Case Exit Conditions`, and `### Case Variables`.
- Every modeled primary stage has `### Stage {N}: {Stage Name}`; every modeled secondary stage has `### Secondary Stage: {Stage Name}`.
- Every stage block contains `**Type:**`, `**Design Rationale:**`, `#### Stage Entry Conditions`, `#### Stage Exit Conditions`, and `#### Tasks`.
- Every modeled primary-stage task has `##### Task {N}.{M}: {Task Name}`; every modeled secondary-stage task has numeric secondary numbering `##### Task S{K}.{M}: {Task Name}` where `K` is the secondary-stage order. Do not preserve letter prefixes such as `R.1`, `W.1`, `CC.1`, or `ESC.1`. Each task block contains `**Type:**`, `**Activation Mode:**`, `**Design Rationale:**`, `**Entry Condition:**`, exact marker `**Task envelope**` (no colon), and the matching type-specific detail block.
- Every `<UNRESOLVED>` marker renders as plain text, exactly `<UNRESOLVED>` — never backtick-wrapped, never annotated inside the cell (build-phase checkers and Phase 1 discovery match the plain marker).
- Section 3 contains `### Personas` and `### Process App Views`.
- Section 4 contains the integration/resource family headings needed by the modeled task types, or an explicit `> None.` for empty families.

Forbidden summary-only replacement sections at top level: `## Source`, `## Case Objective`, `## Actors And Systems`, `## Case Trigger`, `## Stages`, `## Business Rules`, `## Task Plan`, `## Resource Resolution`, `## Acceptance Scenarios`. Their presence as the main document structure means the SDD is a summary, not a template render. Also forbid source/build-mode/path narration such as `Source: /...`, `Build mode`, `output folder`, validation-command checklists, or "generated from requirements file" prose in the SDD body.

If the gate fails, rewrite from the model and template before shipping. Do not write a summary SDD, even if a later `caseplan.json` would validate.

### Naming rules

Safe display characters for stage labels, task display names, and condition/SLA/escalation titles:

```
^[A-Za-z0-9 _-]+$
```

Never `:` — case-execution events are colon-delimited, so a colon in a name breaks routing. The safe charset governs names being MINTED or first carried into a design: repair those mechanically — replace runs of disallowed characters with one space, collapse spaces, trim; keep words and casing; on an empty result or a collision, add a safe qualifier or numeric suffix and disclose the change. A name read from an existing draft or SDD during finalization is preserved verbatim, punctuation included — finalization normalizes structure, never names. The one exception is `:` (the structural ban): surface it and ask, never silently keep or repair it.

| Name | Unique across |
|---|---|
| Task display name | The whole case — every stage, one pool |
| Stage label | All node labels in the case; never the reserved Case Manager stage label |
| SLA rule title | Its target (root or that stage) |
| Escalation title | All SLAs on the element |

Comparison is exact — case-sensitive, untrimmed. Never normalize external lookup names (Action App titles, process/connector names — they are matching keys); keep a separate safe display name instead. Never silently clamp a numeric violation (for example an out-of-range SLA duration) to pass validation — surface it and ask.

## Markers & vocabulary

- **Allowed `—`** (user left it untouched; the build defaults safely): case-level Description, variable defaults, persona scope notes, app-view detail, secondary-stage description, optional `IF` expressions, business calendars on timers.
- **Allowed `<UNRESOLVED>`** (a later run resolves): registry identity ids (`taskTypeId`, `connectionId`, `actionAppId`, `agentId`, `processOrchestrationId`) when resolution was skipped, deferred at the gate, or returned zero matches. Pair every `<UNRESOLVED>` with a review item.
- **Banned on required cells** (the cell rules below name them): populate concretely, keep only the identity `<UNRESOLVED>` (the build emits a placeholder), or ask the user.
- **Forbidden SDD-body vocabulary.** Narrative cells (descriptions, rationales, notes) never carry skill-internal terms: `Pattern C`, `bridge`, `companion`, `inputOutputs[]`, `=jsonString:` (outside connector `Operation Configuration` cells), `groupOperator`, `essentialConfiguration` (as prose), `savedFilterTrees`, `dispatcher`, `io-binding`, `aliased into/from`, `reassign`, `originalVar`, `auto-mint`. These belong in skill references, never in `sdd.md`.
- **Call forms with complete args appear ONLY in table rows; prose uses bare rule names.** `sla-status-change` arg forms: `sla-status-change("<target>","<SLA Title>")` for breach; `sla-status-change("<target>","<SLA Title>","<At-Risk Escalation Display Name>")` for at-risk. Target is the literal `root` (case scope) or the exact stage display name — never the case name or a synonym. Never a partial call form with placeholder args in prose — build-side checkers scan every call-form occurrence and reject wrong arity wherever it appears.

## Section 1 cell contracts

### 1.1 Case Metadata

| Field | Required? | Value shape | If missing |
|---|---|---|---|
| Case Name | yes | PascalCase identifier (`MortgageLoanOrigination`) | Block approval. Ask. |
| Description | optional | One sentence | `—` |
| Identifier prefix | yes | UPPER, 2–4 chars | Default mechanically from the PascalCase name; record provenance |
| Case SLA | conditional | `<count> <unit>`, unit ∈ `min h d w m` — bounds in [layers § SLA rule entries](case-design-layers-guide.md#sla-rule-entries) | `—` when the case has no SLA; otherwise block approval |
| SLA Type | conditional | `time-based` / `condition-based`. The platform persists `condition-based` whenever ≥ 1 SLA rule carries a non-empty condition expression. `condition-based` requires the Variable SLA Rules table; `time-based` omits it | Default `time-based` when Case SLA is set with no overrides |
| SLA Title | conditional | Non-empty root-unique title, no `:` | Omit the row when Case SLA is `—` (never render `—` here); else default `SLA Rule 1` + provenance. A title referenced by `sla-status-change` must be concrete |
| Case App | optional | `Enabled` / `Disabled` | Default `Disabled`; record provenance |
| Task-output passing | optional | `Direct` / `Shared` | Default `Direct` |

**Pre-approval validation parity.** Before approval, apply the § Naming rules and SLA-entry checks to every generated or carried display/title field — blocking authoring errors.

### 1.2 Case-Level SLA Escalation

Required when Case SLA is set. Both rows always render with concrete cells — no `—`.

| Threshold | Trigger | Recipient | Display Name |
|---|---|---|---|
| At-Risk | `<pct>%` of case SLA (defaults: [layers § Defaults](case-design-layers-guide.md#defaults-when-the-source-is-silent)) | `UserGroup: <owner group>` / `User: <name>` | Non-empty root-unique title, no `:` |
| Breached | 100% | One tier up — leadership; Compliance for regulation-driven cases | Non-empty root-unique title, no `:` |

`Display Name` defaults to `Escalation Rule {N}` only when no `sla-status-change` row references it. Defaulted recipients get provenance `default applied — user did not name recipient`.

### 1.2b SLA Response Map

Required whenever ANY SLA is configured (case, stage, or `action` task). One row per `(Scope, SLA, Status)`.

| Column | Cell rule |
|---|---|
| Scope | `case`, `stage: <StageName>`, or `task: <TaskName>` |
| SLA | The target's SLA Title (or a Variable SLA Rules Display Name) |
| Status | `At-Risk` or `Breached` — one row each |
| Response | `notify-only` \| `start-task` \| `enter-stage` \| `exit-stage` \| `exit-case` |
| Target | `—` for `notify-only`; the task name for `start-task` (the task lives in the breached stage); the stage name for `enter-stage`; the produced exit row for `exit-stage` / `exit-case` |
| Interrupting | `—` for `notify-only` AND for every `start-task` — a task entry interrupts nothing, never `Yes`/`No`. Otherwise `Yes`/`No`, matching the produced stage-entry row |
| Rationale | Why this response fits the source |

**Closure both ways (blocking):** every non-`notify-only` row has its matching rule elsewhere in the SDD (an `sla-status-change` task-entry row for `start-task`, a stage-entry row for `enter-stage`, a stage-exit row, or a §1.4a row), and every `sla-status-change` row in the SDD has a row here. An Interrupting mismatch between the map cell and the produced row is blocking. **Default:** no stated response → both statuses `notify-only` with Target and Interrupting `—`; never invent a stage, task, or routing change for a notification. Per-stage SLA tables stay consistent with this map: the breach cell reads `enter-stage: <Secondary Stage Name>` (the `sla-status-change`-entered interrupting stage), never `Notify: <role>`; notify-only cells are for at-risk warnings.

### 1.3 Triggers

≥ 1 trigger. One row per triggering event, numbered from **T02** (T01 is the case file). The T-number keys §1.5 trigger-payload rows.

| Field | Required? | Value |
|---|---|---|
| T# | yes | `T<N>`, sequential from `T02` |
| Trigger Type | yes | `Manual` / `Intsvc.TimerTrigger` / `Intsvc.EventTrigger` — author tokens ([layers § Triggers](case-design-layers-guide.md#triggers)) |
| Source | conditional | Connector or system for event; schedule expression for timer; `Manual` literal |
| Configuration | conditional | User intent in business terms. An event trigger MUST have a concrete operation phrase |

**Configuration cell:** event → the operation in business terms (`Record created`, `Email received in Inbox; filter: subject contains "URGENT"`); tenant case-entity starts keep the object name in Source and the business event in Configuration; timer → cycle or duration (`daily at 09:00 UTC`); manual → `N/A`. **Forbidden in Configuration** (resolved at build time): CLI enum values (`CALENDAR_CREATED`), delivery modes (`polling` / `webhook`), meta notes (`No required event parameters`), activity slugs, HTTP methods.

Payload-field → variable mapping lives ONLY in §1.5 — never in this table. A case that starts when a tenant record is created is an `Intsvc.EventTrigger` row even when the object is not provisioned — unresolved detail becomes a placeholder later, never a downgrade to `Manual`. Unresolved event resolution (`connectionId` / `activityTypeId`) → high review item.

### 1.3a Trigger Filter (conditional)

Renders only when ≥ 1 trigger declares a filter. AND/OR tree; nested `{op, clauses}` groups flatten in the rendered table. Columns: `Field | Operator | Value | Literal?`. Operators (PascalCase, case-sensitive): `Equals`, `NotEquals`, `Contains`, `NotContains`, `StartsWith`, `EndsWith`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `In`, `NotIn`, `IsNull`, `IsNotNull`. Avoid `Literal: No` for unverified runtime expressions — it forces a lossy fallback; prefer literal values or a review item.

### 1.4 Case Completion Conditions · 1.4a Case Exit Conditions

Columns: `WHEN | IF | Marks Case Complete | Exit Type | Display Name`. §1.4 = `Yes` rows (≥ 1 required); §1.4a = `No` rows (alternate dispositions: Withdrawn / Rejected / Cancelled). Legal WHEN and exit types per [layers § Lifecycle gates](case-design-layers-guide.md#lifecycle-gates) / [§ Exit types](case-design-layers-guide.md#exit-types).

**Display Name defaulting (every condition table):** carry the author's value verbatim; blank → default `Entry Rule {N}` (entry / task-entry) or `Complete Rule {N}` / `Exit Rule {N}` (exit tables, by Marks-Complete), `N` = 1-based within the same label kind. Never invent a label otherwise.

When the case has ≥ 1 secondary stage AND §1.4a is empty → high review item (`Alt-disposition exits missing`) — the case cannot exit non-happy paths cleanly.

### 1.5 Case Variables

Declare a row ONLY per the declare-vs-direct-reference test in [layers § Layer 3](case-design-layers-guide.md#when-to-declare-a-case-variables-row) — one task's output feeding one consumer is referenced directly, never declared. Authoring is declarative: `Category` + `sourceTriggers` + `sourceFields` drive build-time classification; nothing is inferred from prose.

| Column | Required? | Cell rule |
|---|---|---|
| Name | yes | camelCase, no role suffix |
| Category | yes | `In` / `Out` / `Variable` — never blank |
| Type | yes | `string` `integer` `float` `double` `boolean` `date` `datetime` `jsonSchema` `file` |
| sourceTriggers | conditional | `Variable`: single `T<N>` or CSV. `In`: optional single `T<N>` (blank = primary trigger, never CSV). Empty for pure state and `Out` |
| sourceFields | conditional | `Variable` only. One trigger → bare payload path (`response.subject`); CSV → keyed `T<N>: <path>; T<M>: <path>`, one entry per listed T-number. Always empty on `In`. Dot-paths only — no array indexing |
| Default | optional | Concrete default or blank |
| Description | yes | One line |

- **Out-arg producer rule:** every `Out` row has a `Default` OR a task Outputs row targeting it (`-> {name}` / `{name} = {expr}`) — pre-checked at the approval gate.
- **File In-args** carry the caller pre-upload obligation — surfaced via the Caller-obligation block ([case-design-lane-guide.md § Confirm](case-design-lane-guide.md#confirm--the-single-checkpoint)).

## Section 2 cell contracts

### Stage headings & fields

- Primary: `### Stage {N}: {Stage Name} (\`{stage_id}\`)` — N is 1-based flow order. Secondary: `### Secondary Stage: {Stage Name} (\`{stage_id}\`)`.
- The trailing code-formatted `{stage_id}` MUST appear, and every cell that names a stage appends the id in code-formatted parens — cross-references stay greppable.

| Field | Required? | Cell rule |
|---|---|---|
| Type | yes | The literal `Stage` |
| Stage Kind | conditional | Omitted for primary; `secondary` for exception lanes |
| Design Rationale | yes | One concrete sentence: why primary/secondary, why the entry/exit behavior fits. A global-event lane names the event and states that one interrupting entry replaces per-stage duplication; an SLA lane names the SLA, the response, and why it interrupts or not |
| Description | yes (primary) / optional (secondary) | One sentence |
| Required for Case Completion | yes | Explicit `Yes`/`No` — design default: primary `Yes`, secondary always `No`. Never leave it implicit |
| Interrupting | secondary only | Per [layers § Secondary stages](case-design-layers-guide.md#secondary-stages) |
| Stage SLA | when the stage has an SLA | The `#### Stage SLA` block below |

### Stage SLA block

When the source gives every primary stage an SLA target, every named primary stage renders its own `#### Stage SLA` block. Deterministic titles when unnamed: `**SLA Title:** <Stage Name> SLA`, at-risk display name `<Stage Name> SLA at risk`, breach `<Stage Name> SLA breached`; every `sla-status-change` reference uses those exact strings. Render `**SLA Type:**` and `**SLA Title:**` as two separate lines — a collapsed single line hides the title from line-start tooling and `sla-status-change` references stop resolving. Duration, thresholds, recipients, escalations: [layers § Layer 4](case-design-layers-guide.md#layer-4--time-slas--escalations).

### Stage condition tables

- **Entry:** `WHEN | IF | Interrupting | Display Name`. ≥ 1 row per stage.
- **Exit (completion `Yes` + exit `No` rows in ONE table):** `WHEN | IF | Exit Type | Marks Stage Complete | Display Name`. ≥ 1 completion row per primary stage.
- Legal WHEN per slot and exit-type legality: [layers § Lifecycle gates](case-design-layers-guide.md#lifecycle-gates) / [§ Exit types](case-design-layers-guide.md#exit-types).

### Stage Task Summary

In plan order, ≥ 1 task per stage: `# | Task ID | Task | Type | Owner`. `Task ID` is code-formatted (`` `t11` ``); Required-Tasks cells elsewhere use those bare ids. Owner = persona name or `system`.

### Task detail blocks

Headings: `##### Task {N}.{M}: {Task Name}` (primary) / `##### Task S{K}.{M}: {Task Name}` (secondary, K = secondary-stage order) — never letter prefixes. Every block carries, in order:

1. `**Type:**` — one of the nine values in [layers § Task types](case-design-layers-guide.md#task-types)
2. `**Activation Mode:**` — `sequential` \| `parallel` \| `parallel-after-predecessor` \| `event-triggered` \| `adhoc` \| `fan-in` \| `conditional-gate`
3. `**Design Rationale:**` — why the type fits the actor/work and why the mode fits the timing (sequential names the ordering evidence; parallel states independence)
4. `**Entry Condition:**` + its `WHEN | IF | Display Name` table (≥ 1 row; multiple rows = OR; render `current-stage-entered` first when present). Never collapse an executable task gate into inline prose on the heading line — doing so drops the condition from the later planning handoff
5. Exact marker `**Task envelope**` (no colon) + the `Required | Run Only Once | Skip Condition` table
6. The type-specific detail block below

Which WHEN to write per described timing: [layers § Sequencing & activation](case-design-layers-guide.md#sequencing--activation).

### Per-type required cells

#### `action`

| Cell | Rule |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>` — concrete intended name (registry-canonical when resolved, else user-requested). NEVER `<UNRESOLVED>`, never paraphrased |
| Action App ID / Deployment Folder | Concrete when resolved; `<UNRESOLVED>` + high review item when not |
| Recipient | Typed prefix only: `Email:` / `User:` / `UserGroup:` / `Role:` / `Expression:` — never a bare string. None known → drop the cell + high review item |
| Priority · Task Title · Labels | `Low/Medium/High/Critical` · one-line user-visible instruction (required — Action Center displays it) · CSV or `—` |
| Run Only Once · Required | Explicit `Yes`/`No` each |
| Input / Output Schema | Tables `Field | Type | Binding (| Required)`. Declared fields MUST be a subset of the resolved app's schema; a field the app lacks → Ask (task-specific app / drop / placeholder), never silently author |
| Buttons | Only when `is_decision: Yes` — then ≥ 2 rows, each `Maps To` LHS a declared §1.5 `Name`, `taskOutcome`, or the task's own output (read downstream via a direct producer reference); never an identifier that occurs nowhere else |

Reusing ONE deployed app across several `action` tasks is sanctioned when each task carries a distinct `actionType` dispatch value AND its declared fields ⊆ the app schema (the code-switched app); without a distinct `actionType`, or with non-bindable fields, it is the substitute-app defect (§ Architect's lens).

#### `wait-for-connector` / `execute-connector-activity`

Connector key · Connection (name + ID) · Activity Type ID · Service Type · Auth Method · Account/Endpoint · Operation (and Trigger/Event for waits) · `Operation Configuration` carry-through · Inputs table (`Field` verbatim to the IS activity schema) · Outputs table. Missing `Connection ID` / `Activity Type ID` → high review item.

#### `wait-for-timer`

Timer Type (`timeDuration` relative / `timeDate` absolute) · Duration/Until (ISO-8601 — NEVER `<UNRESOLVED>`: a timer cannot fire without it; block approval) · Business Calendar optional (`—`).

#### `case-management`

Child Case (concrete intended name — NEVER `<UNRESOLVED>`, never the parent task's display name) · Folder Path / Resource Identity (`entityKey`; `<UNRESOLVED>` + high review item when unresolved) · Child Case Identifier prefix · Data Passed table (`Parent Variable | Child Variable`) · Wait for Completion `Yes`/`No` · Data Returned table only when waiting.

#### `process` / `agent` / `rpa` / `api-workflow` (shared block)

| Cell | Rule |
|---|---|
| Resolved Resource | Concrete intended resource name — NEVER `<UNRESOLVED>` |
| Folder Path | The exact resource folder (never a parent), or `<UNRESOLVED>` when identity is unresolved |
| Resource Identity | `apiWorkflowId` / `agentId` (+version) / `processOrchestrationId`, or `<UNRESOLVED>` + high review item |
| Binding Sub-Type | `Api` (api-workflow) / `Agent` (agent) / `ProcessOrchestration` (process) / `—` (rpa). Omitting it makes Studio Web report the resource as not found |
| Dispatch / Operation | Selector + value for shared façades (`requestSource = "RegisterCaseShell"`), also an Inputs row; `—` for single-purpose resources |
| Inputs / Outputs | Tables; `Field` verbatim to the declared In/Out argument names |

No task-level SLA on any non-`action` type. Deep runtime metadata (agent prompts, package versions, endpoints) stays out of the SDD — it belongs to build-time discovery (§ Resolution record carries identities only).

### I/O completeness (resolved resources)

When a task resolves to a live resource: every REQUIRED declared input has a non-empty `Binding` (any form in [layers § Binding-cell forms](case-design-layers-guide.md#binding-cell-forms-task-inputs), including a direct upstream-output reference — which needs no §1.5 row) OR `<UNRESOLVED>` + a high review item; every Outputs `->` row's `Field` exists verbatim in the resolved output contract (a phantom field → high review item). Optional inputs may be omitted. Tasks whose identity is `<UNRESOLVED>` have no contract and are skipped — their portable names stay concrete. **Bare field-name input lists are forbidden** (`**Inputs:** loanId, borrower`) — table form only.

## Review items

Structured gap escalations, emitted whenever a field could not be fully resolved but the downstream build needs the context. They live in the in-memory model and surface ONLY as `Review Flags` rows in the confirmation — never in the `sdd.md` body. The build persists them under the matching task's `review_items[]` in its resolution audit file.

```jsonc
{
  "id": "rev_<short-slug>",
  "target": "<sdd.md section path or task name>",
  "issue": "<one-sentence problem>",
  "severity": "high" | "medium" | "low",
  "next_step": "<what the user must do to resolve>"
}
```

| Level | Definition | Examples |
|---|---|---|
| **high** | Blocks the downstream build until resolved | Missing `connectionId` / `actionAppId` / deployed runnable; a resolved resource's required input unbound (`rev_unbound_input_<task>_<field>`); an extract naming a field the resource never emits (`rev_phantom_output_<task>_<field>`); open variable lineage; missing trigger config; unreconciled compliance override |
| **medium** | Build defaults with a prompt | Missing escalation recipient (default = owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | Missing case description; missing secondary-stage description; stylistic placeholder |

**Gate behavior:** any open `high` item relabels the confirmation's Build option `Build despite N flagged items` — the user must pick it; silently building past `high` is forbidden. `medium`/`low` surface as advisory rows, no acknowledgment needed. Never downgrade a severity to pass the gate — it moves only when the underlying issue actually resolves.

## Resolution record

One record per resolved or attempted registry lookup, kept in memory by the lane ([case-design-lane-guide.md § Tenant grounding](case-design-lane-guide.md#tenant-grounding--full-resolution-at-design-time)); the build later persists the set verbatim as `tasks/registry-resolved.json`:

```jsonc
{
  "stage": "<SDD stage name>",
  "task": "<SDD task name>",
  "taskType": "<task type>",
  "cacheFile": "<index basename actually searched>",
  "searchQuery": "<lookup string>",
  "matches": [ /* FULL exact-name match set from the refreshed cache — never a summary */ ],
  "selected": { /* adopted entry */ },        // null after a genuine empty lookup
  "rationale": "<why>",
  "gateDecision": "pick:<name>" | "resolve-at-build" | "create-during-build"  // only when the user answered
}
```

1. `gateDecision` present = the user answered the gate for that item; the build executes it without re-asking. A defaulted deferral (no session, failed or pending pull, non-interactive run) carries NO `gateDecision` — the build's own gate re-asks it.
2. Cache-state rule: before a successful pull this session, a missing cache file is a failed precondition — never a zero-match result. Only after a successful pull may an empty match set enter the empty-lookup flow.
3. Deep runtime metadata (agent prompts, package versions, endpoints, release tags) stays out of the SDD — the SDD carries name + folder + identity + sub-type; everything else rides this record.

## Logical integrity — the stage-graph walk

Reachability is condition-only (the case has no edges), so this walk is the sole guard. Any failure is blocking; offer `Re-edit` / `Restart` / `Abort`.

1. **Every stage reachable from a trigger** — walk entry conditions forward from each trigger and SLA source. An unreachable primary stage is an orphan.
2. **Every stage exits** — each primary stage has a completion consumed downstream, or another stage's entry references it, or it feeds a secondary lane. A stage nothing keys off is a terminal loop.
3. **Every case-exit row references a stage that exists** — no dangling selectors.
4. **The §1.4 path can complete** — ≥ 1 primary stage is `Required: Yes`; otherwise the case can never complete.
5. **Secondary-lane entries: ≥ 1 interrupting entry each, DISTINCT, chosen by the lane's trigger source** ([layers § Secondary-lane entry shapes](case-design-layers-guide.md#secondary-lane-entry-shapes)). Two lanes with identical entries (same rule + selectors + expression) are ambiguous routing — a design requirement to differentiate, not validate-enforced (as of uip 1.198.0-preview.102). A decision-reachable lane MUST carry a `selected-stage-exited(origin)` + `IF` entry matching the origin's gated diverting exit, with the origin's completion gated by the inverse `IF`; a missing divert dual-fires or deadlocks. A lane described as decision-reachable but entered only via `wait-for-connector` is unreachable from its stated source. `adhoc` is never a stage entry.
6. **Every `sla-status-change` entry resolves** — the target is `root` or an existing stage, that target declares the SLA, and every supplied title matches a row on THAT target; a two-arg breach row is complete as written. Any real miss leaves the lane unreachable.
7. **Every secondary stage is interrupting except a non-diverting SLA oversight row.** Wrong classification is blocking; never promote the lane to a regular stage.
8. **No gate reads a variable its own trigger writes** — for every condition whose WHEN names a task, the `IF` references that task's output, not a case variable the task's Outputs row feeds ([layers § Gate on the producer](case-design-layers-guide.md#gate-on-the-producer-never-on-the-variable-it-writes)).

Worked example — a decision-routed return lane (AP Review → SLA Escalation on `requiresEscalation`):

| Stage | Condition | WHEN | IF | Exit Type | Marks Complete |
|---|---|---|---|---|---|
| AP Review | exit (complete) | `required-tasks-completed` | `=js:(vars.requiresEscalation !== true)` | `exit-only` | Yes |
| AP Review | exit (divert) | `selected-tasks-completed("AP ownership review")` | `=js:(vars.requiresEscalation === true)` | `exit-only` (exit target → SLA Escalation) | No |
| SLA Escalation | entry (`Interrupting: Yes`) | `selected-stage-exited("AP Review")` | `=js:(vars.requiresEscalation === true)` | — | — |
| SLA Escalation | exit | `required-tasks-completed` | — | `return-to-origin` | Yes |

On escalate the divert fires (completion's inverse `IF` is false), the lane runs, `return-to-origin` re-activates AP Review; on non-escalate the completion fires and the next stage enters via its own `selected-stage-completed("AP Review")`. The decision is read directly from the producing action's output — never relayed through a §1.5 variable.

## Architect's lens — advisory pass

Emit medium review items when these fire; the noted high variants gate like any high item.

| Check | Trigger | Review item |
|---|---|---|
| Single-recipient bottleneck | An `action` recipient is one `User:`/`Email:` AND the stage runs on every case AND no documented volume limit | `rev_bottleneck_<task>`: confirm volume or use UserGroup/Role |
| No escalation on SLA | Stage SLA set, escalation absent | `rev_escalation_<stage>`: no one is paged on breach |
| Escalation loops to the breacher | Escalation recipient = the stage's primary recipient | `rev_escalation_loop_<stage>`: pick a tier-up recipient |
| Sync child case in the critical path | `Wait for Completion: Yes` + parent SLA + no timeout cover | `rev_childcase_<task>`: consider async + completion event, or an exception path |
| All-human stage | 100% `action` tasks, > 2 tasks | `rev_human_only_<stage>`: consider agent/process pre-screening |
| No happy path on the first stage | Only `No` exits, no `required-tasks-completed` completion | `rev_no_happy_path_<stage>` |
| Decision outcome unread | `is_decision: Yes` writes a variable no downstream rule reads | `rev_orphan_decision_<task>`: consume it or downgrade `is_decision` |
| Connector failure uncovered | Connector task in a primary stage, no failure lane (HIGH when ≥ 2 connector tasks share a critical path with zero cover) | `rev_no_failure_path_<task>` |
| Substitute app (HIGH) | One Action App on ≥ 2 tasks WITHOUT a distinct `actionType` each, or declared fields outside the app schema. Exempt: the code-switched app (§ Per-type required cells) | `rev_substitute_app_<app>`: code-switch or deploy task-specific apps |
| Parallel bottleneck fan-in | ≥ 2 bottleneck stages fan into one downstream stage | `rev_multi_bottleneck_<stages>` |
| Relay variable | A §1.5 `Variable` whose only producer is one task output and only consumer is one binding (exemptions in [layers § Layer 3](case-design-layers-guide.md#when-to-declare-a-case-variables-row)) | `rev_relay_var_<name>`: reference the output directly, drop the row |
| Aliased output | An Outputs `->` row whose `Field` leaf has no matching §1.5 row and lands in a differently-named variable | `rev_aliased_output_<task>`: declare a dedicated variable or confirm the reuse |

## Finalization checklist

Run ONCE against the in-memory model before presenting the review. Checks 16 and 19 need resolved I/O contracts, which design-time resolution does not pull — they are enforced at build; run them here only when a contract is already in memory.

1. **Schema** — every task type is one of the nine ([layers § Task types](case-design-layers-guide.md#task-types)); every WHEN ↔ Marks-Complete pair and gate-slot rule is legal ([layers § Lifecycle gates](case-design-layers-guide.md#lifecycle-gates)). `[audit]`
2. **Render contract** — every required cell concrete (§ Section 1 / § Section 2 above); no banned `—`/`<UNRESOLVED>` (§ Markers).
   2a. **Template shape** — § Template conformance gate on disk, before the `Status: ready` flip. `[audit]`
   2b. **Safe display names** — § Naming rules charset + repair on every generated or carried display field. `[audit]`
3. **Decision buttons** — `is_decision: Yes` ⟹ ≥ 2 buttons; every `Maps To` LHS is a §1.5 `Name`, `taskOutcome`, or the task's own output. `[audit: dead routes]`
4. **Recipient encoding** — typed prefixes only. `[audit]`
5. **Connector ids** — every connector task has `Connection ID` + `Activity Type ID`; every `wait-for-connector` rule (any scope) resolves connector key + event operation (+ connection when not tenant-default). Missing → paired high review item.
6. **Variable lineage** — every consumer closes ([layers § Lineage closure](case-design-layers-guide.md#lineage-closure)). `[audit]`
7. **Override conflict** — no compliance trigger phrase paired with a non-`action` type without explicit user reconciliation ([layers § Task-type override priority](case-design-layers-guide.md#task-type-override-priority)).
8. **Alt-disposition coverage** — ≥ 1 secondary stage ⟹ §1.4a non-empty OR an open high item.
9. **High-severity acknowledgment** — open high items force the `Build despite N flagged items` pick.
10. **Provenance** — every non-user-stated, non-verbatim value carries a provenance kind ([case-design-lane-guide.md § Authoring policy](case-design-lane-guide.md#authoring-policy)).
    10a. **Design rationale** — every stage (kind + routing), task (type + activation), and configured SLA (thresholds, recipients, response) carries durable rationale — blocking when missing.
    10b. **SLA Response Map closure** — one row per `(Scope, SLA, Status)`, closure both ways, Interrupting cells agree (§ 1.2b); a `notify-only` row that minted a stage or task, or a bare SLA with no row, is blocking.
11. **File-In-arg caller obligation** — the Caller-obligation block whenever an `In` + `file` row exists.
12. **Stage-graph connectivity** — the § Logical integrity walk, all eight checks.
    12a. **Entry producer** — every non-start entry names a concrete producer (source stage, task, connector event, paired `wait-for-user` exit, or a declared SLA reference); at-risk rows name the escalation, breach rows the SLA alone.
13. **Domain fidelity** — every verbatim-captured entity renders exactly ([case-design-lane-guide.md § Authoring policy](case-design-lane-guide.md#authoring-policy)); drift → `Re-edit` with the phrase pre-filled.
14. **Architect's lens** — the advisory table above; medium rows are non-blocking, high variants gate.
15. **Decision-routing closure** — every routing button's variable + value is consumed by a downstream rule or declared terminal; a named destination lane with no keyed entry is a dead branch — blocking. A fully-orphaned decision variable on an `is_decision: Yes` task is blocking.
16. **Action-app schema fidelity** — declared Input/Output fields ⊆ the resolved app's schema; a violation → high item `rev_action_schema_<task>`; code-switched reuse is sanctioned.
17. **Required-task presence** — a `required-tasks-completed` completion over a stage with zero `Required: Yes` tasks is vacuous and fails validation with `Stage exit rule '<name>' has no task(s) marked as required` (verified on uip 1.198.0-preview.102) — blocking; offer marking the stage's terminal task required.
18. **Resolved-resource presence** — concrete portable names everywhere (`Resolved Resource`, Action App title, `Child Case` — never `<UNRESOLVED>`); identity + folder pairs concrete together, or unresolved with a paired high item.
19. **Resolved-resource I/O completeness** — required inputs bound, extract fields exist verbatim (§ I/O completeness); an unbound required input with no review item is blocking.
20. **Re-entry attempt check** — classify every `return-to-origin` / rework loop per [layers § Sequencing & activation](case-design-layers-guide.md#sequencing--activation); new-attempt loops keep producer tasks rerunnable and reset or attempt-scope routing variables; re-evaluate loops document the re-read fact.

**On pass:** present the Case Review (the Build/Save answer is the consent; explicit sign-off adds one prompt; design-only and draft requests save and stop). Corrections update the model and re-run only the affected checks. **On fail:** fix the model and re-run the failed checks plus any whose inputs changed — never the full suite; never present the review or render `sdd.md` while a fixable check is failing; only unfixable items surface, as ⚠ flags.
