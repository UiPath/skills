# SDD Generation Rules

Content-quality contract for Phase 0's `sdd.md`. The interview in [phase-0-interview.md](phase-0-interview.md) owns the **conversation flow** (Listen / Sketch / Ask / Resolve / Approve). This file owns the **content rules** every generated `sdd.md` must satisfy before Approve renames the draft.

Phase 1 trusts `sdd.md` as written (SKILL.md Rule 2). These rules make that trust safe.

## Mental model: stages, secondary stages, tasks

Reason the case shape from the process the user describes — **do not reach for the template first.** The template renders a shape you already decided; it does not decide it for you. Build the model in this order: stages → tasks → types → pull exceptions out. Each concept below is a question to ask of the user's process, not a slot to fill.

**Stage** — a phase the case works through: a bounded milestone with an *entry* (when it starts), *tasks* (the work done inside it), and a *completion/exit* (when it's done and where the case goes next). Stages are the backbone; they run in sequence (or parallel), wired by **entry/exit conditions** (the case has no edges — transitions are condition-driven). Derive one stage per milestone the user names ("intake", "underwriting", "funding"). Ask: *what is the case working toward right now, and what makes that done?* A stage that "marks the case complete" is on the main flow (`isRequired: true`).

**Secondary stage** (a `case-management:Stage` node carrying `data.stageType: "secondary"` — the `case-management:ExceptionStage` node type is removed at v22) — work that is **not a fixed step on the line**: it can fire at many points and only under a condition. Errors, escalations, rejections, rework loops, cancellations. Three rules define it, all CLI-enforced:

- **No edges** — reached and exited purely by conditions, never wired by an edge. (True of every stage now that edges are retired; the legacy `CASE_MGMT_SECONDARY_STAGE_EDGES` validator that flagged secondary-stage edges is moot.) It is detached from any flow graph.
- **Entered by its own condition**, never by an edge — but the entry shape depends on the lane's trigger:
  - **(a) Mid-stage interrupt** — user-launched (`user-selected-stage`, paired with a `wait-for-user` exit) or external (`wait-for-connector`). Fires *while the origin is still active* and genuinely interrupts it.
  - **(b) Decision/signal divert** — the **origin** stage carries a **gated diverting exit** (`Marks Stage Complete: No`, `IF` on the decision/signal, `exitToStageId` → this lane), and this lane's `selected-stage-exited(origin) + IF` entry **matches** it. Fires when the origin *exits* — a divert-and-return, NOT a true mid-stage interrupt. A variable-driven mid-stage interrupt is not expressible without a connector, so a decision- or signal-gated lane MUST use shape (b). See [§ Logical integrity step 5](#logical-integrity--stage-graph).
- **Exits via `return-to-origin`** — routes the case back to the origin stage, through the exit rule, not a new edge. Requires `Interrupting: Yes`.

Ask: *does this work belong at one fixed point (regular stage), or could it happen at several points / only on a condition (secondary stage)?* "Handle rejected application", "escalate on SLA breach", "rework loop" → secondary. Pull these out of the main flow; do not string them inline as ordinary stages.

**Task** — one unit of work inside a stage, owned by a *persona* (a human role) or by the *system* (automation / AI / API). It has an entry condition (when it runs within the stage), inputs, outputs, and a **type** that says *how* the work gets done. One verb in the user's description ≈ one task. Ask: *who or what performs this, and how?* The "how" answer is the task type — see [§ Choosing the task type](#choosing-the-task-type).

Once stages, secondary stages, and tasks are reasoned, the [§ Render contract](#render-contract) below turns each decision into exact cells. Reason first; render second.

### Lifecycle rules — entry / completion / exit

The case, each stage, and each task move through a lifecycle gated by **rules** (DNF — an OR of AND-clauses). The CLI fixes exactly which rule types are legal at each gate (`packages/case-tool/src/utils/schema-helpers.ts` → the `VALID_*_RULE_TYPES` sets; mirrored in [case-schema.md § Rules](case-schema.md)). **Pick from the set for the gate — never invent a rule type, never use a rule type from the wrong gate.**

| Gate | What it answers | Legal rule types (CLI) |
|---|---|---|
| **Case entry** | how does a case instance begin? | No case-entry condition object — a **trigger** starts the case; the root stage carries `case-entered`. |
| **Stage entry** | when does this stage activate? | `case-entered` (root only) · `selected-stage-completed` · `selected-stage-exited` · `wait-for-connector` · `user-selected-stage` |
| **Stage completion** (`Marks Stage Complete: Yes`) | when is the stage done, on the main flow? | `required-tasks-completed` · `wait-for-connector` |
| **Stage exit** (`Marks Stage Complete: No`) | early hand-off / route without completing | `selected-tasks-completed` · `wait-for-connector`; exit `type`: `exit-only` / `wait-for-user` / `return-to-origin` |
| **Task entry** | when does this task start inside its stage? | `current-stage-entered` (first task — required) · `selected-tasks-completed` · `wait-for-connector` · `adhoc` · `runs-sequentially` |
| **Task completion / exit** | — | A task has **no** exit/completion condition. It completes when its own work finishes; downstream stages/tasks key off that via `required-tasks-completed` / `selected-tasks-completed`. |
| **Case completion** (`Marks Case Complete: Yes`) | when does the case close successfully? | `required-stages-completed` · `wait-for-connector` |
| **Case exit** (`Marks Case Complete: No`) | alternate disposition (cancel / route out) | `selected-stage-completed` · `selected-stage-exited` · `wait-for-connector` |

How to reason with these:

- **`required-*` vs `selected-*`.** `required-tasks-completed` / `required-stages-completed` = "all items flagged required are done" (the `isRequired` flow). `selected-tasks-completed` / `selected-stage-completed` / `selected-stage-exited` = "these *specific named* items." Pairing rule (Key Rule 4): `Marks Complete: Yes` pairs only with `required-*`; `selected-*` is for `No` (routing / early exit / alternate disposition). A `Yes` + `selected-*` pair is a schema error.
- **Secondary stage** uses **stage-entry + stage-exit rules only, never edges** (true of every stage now — edges are retired). Its entry rule is typically *interrupting* (`isInterrupting: true`); its exit uses `return-to-origin` to rejoin the flow it left. **For a decision/signal-routed lane, the routing lives on the *origin* stage:** a gated diverting exit (`Marks Stage Complete: No`, `IF` on the decision/signal, `exitToStageId` → the lane), with the origin's completion exit gated by the inverse `IF` so the two paths are mutually exclusive — see [§ Logical integrity step 5](#logical-integrity--stage-graph).
- **First event-driven task in a stage** must carry `current-stage-entered` (emit it explicitly). A sequential chain is the exception: the first sequential task carries only `runs-sequentially`, which the frontend interprets as current-stage-entered; later sequential tasks carry only `runs-sequentially`, which the frontend interprets as the preceding task completing. `wait-for-connector` makes a gate pause for an inbound connector callback — its `conditionExpression` gates on **case state** only (no `event` payload; in-rule extract-then-gate is unsupported at runtime — gate a downstream condition instead); `adhoc` lets a *task* fire manually from the case app (task-entry only — never a stage-entry rule).

**Frontend task-mode mapping.** The UI's `sequential`, `event-triggered`, and `manually-triggered` choices are not interchangeable: sequential means the task-only `runs-sequentially` rule; event-triggered means an explicit event/condition rule (use `wait-for-connector` for an external connector callback); manually-triggered means an `adhoc`-only task with `isRequired: false`. Do not infer one mode from `data.tasks` lanes, and do not add a second entry rule that changes the selected mode.
- **`user-selected-stage`** (stage entry) starts a stage on demand by a user rather than by flow. The CLI validator requires it to pair with a `wait-for-user` stage exit elsewhere: a `wait-for-user` exit with no `user-selected-stage` entry — or a `user-selected-stage` entry with no `wait-for-user` exit — fails `validate`.

Exact cell formats live in [§ Stage content rules](#stage-content-rules) and [§ Task content rules](#task-content-rules) — this table is the conceptual map of *which rule belongs where*.

### Triggers, connectors, variables — how the case meets the world

**Trigger** — how a case instance is *born* (`TriggerNode`, `case-management:Trigger`, field `data.uipath.serviceType`):

- `None` → **Manual**: a user or API call starts the case.
- `Intsvc.TimerTrigger` → **Timer**: a schedule starts it.
- `Intsvc.EventTrigger` → **Connector Event**: an external system fires it.

One trigger is the root; additional triggers are secondary. Ask: *what makes a new case appear?* A portal signup, inbound form, or schedule is NEVER Manual — trigger type is Always-Ask the moment such a source is named.

**Connector** — the case's hands into an external system (an Integration Service connection). It surfaces three ways: an `execute-connector-activity` task (perform one operation — push), a `wait-for-connector` task/rule (pause for an inbound event — pull), or an `Intsvc.EventTrigger` (start on an event). Identity (`typeId` + `connectionId`) resolves from the registry — never fabricate IDs (SKILL.md Rule 8). Ask: *which system, and does the case call it (push) or wait for it (pull)?*

**Variable** — the case's memory; data flowing across tasks and stages (`UiPathVariable` / `UiPathAllVariables`). Two axes:

- **Category** = its role: `In` = supplied at case start (caller / trigger), `Out` = returned at case end, `Variable` = internal state (including trigger-payload extraction via `sourceTriggers` + `sourceFields`).
- **Type** ∈ `string` · `integer` · `float` · `double` · `boolean` · `date` · `datetime` · `jsonSchema` · `file` (a `file` is a JobAttachment record). Use `string` for JSON-shaped values; never emit `json`.

A task Output *produces* a variable (`-> =vars.<id>`); a task Input *consumes* one (binds from a variable or an upstream task's output). Ask: *where does each piece of data come from, and who consumes it?* Never introduce a variable whose only producer runs after its consumer — that breaks lineage closure (§Variable lineage closure).

### Worked reasoning (one pass)

> *"Vendors sign up through our portal. We screen them, run a compliance check, set them up in our finance system, then activate. If compliance fails it goes back for remediation."*

Reason the shape; do not template it:

- **Milestones → stages:** Intake → Screening → Compliance → Finance Setup → Activation — regular stages on the main flow.
- **"goes back for remediation" → secondary stage.** Remediation fires only on a condition (compliance failed) and routes back — model it as a secondary stage (condition-entered, `return-to-origin`), **not** a sixth inline primary stage.
- **"sign up through portal" → trigger.** A portal signup is an inbound event, not Manual — Always-Ask the trigger type.
- **Tasks + types** (read verb + actor, ask the [§ Choosing](#choosing-the-task-type) question):
  - *screen them* → AI judges unstructured docs → `agent`
  - *compliance check* → ambiguous: a connector call (`execute-connector-activity`) vs human sign-off (`action`); the verb is Always-Ask, and a "licensed officer signs off" phrase forces `action`.
  - *set them up in finance system* → SAP connector operation → `execute-connector-activity`; if a deployed process packages it → `process`.
  - *activate* → one connector op or a human flip → confirm with the user.

The shape fell out of the process. The template then renders it.

## Inputs

| Input | Purpose |
|---|---|
| User chat messages | Primary source — verbatim values, types, exits, SLAs |
| User-supplied docs (paths, paste, attachments) | Secondary — read on Listen, parsed for case shape |
| [`assets/templates/sdd-template.md`](../assets/templates/sdd-template.md) | Structural mold for the rendered `sdd.md` |
| [`references/case-schema.md`](case-schema.md) | Platform schema — what `caseplan.json` accepts downstream |
| [`references/registry-discovery.md`](registry-discovery.md) | Cache file map for Resolve |
| Tenant registry (`~/.uip/case-resources/`) | Resolves deployed processes / agents / actions / connectors |
| Tenant IS cache (`~/.uipath/cache/integrationservice/`) | Resolves connector identity, connections, activities, triggers |

`case-schema.md` is platform-truth. Choices conflicting with it are schema-invalid regardless of source — see §Content authority hierarchy.

## Content authority hierarchy

When signals conflict, apply this priority — top wins:

1. **Platform schema constraints** ([case-schema.md](case-schema.md)) — schema-invalid values never ship, regardless of source. Examples: task `type` outside the 9-value enum (SKILL.md Rule 16); `Marks Stage Complete: Yes` paired with `selected-tasks-completed` (sdd-template Key Rule 4).
2. **Regulatory / compliance constraint** stated or implied by the user (ECOA, NCQA, GDPR, HIPAA, SOC 2, FCRA, FINRA, etc.). Forces specific types — see §Task-type override priority.
3. **Tenant evidence** from the registry cache — a deployed Action App, process, agent, or API workflow that already matches the task. Prefer that resource's type.
4. **User-stated preference** in chat (verbatim "set the task to agent", "trigger = portal event").
5. **Doc-extracted values** from user-shared docs.
6. **Inferred defaults** per the high-confidence test in [phase-0-interview.md § When to Ask vs Default](phase-0-interview.md#when-to-ask-vs-default).
7. **General-practice fallback.**

When a higher tier overrides a lower one, narrate the override in chat AND surface it in the Approve summary's `Inferred / defaulted` block with provenance `(source: <higher-tier>-override)`.

## Choosing the task type

The `type` says **how the work gets done**, not what it's about. Read the verb + the actor in the user's description, ask the matching question, pick the type. The enum is closed — 9 values (SKILL.md Rule 16). Pick the baseline here; [§ Task-type override priority](#task-type-override-priority) then resolves conflicts (compliance, tenant evidence) on top of this pick.

| Type | Pick when the work is… | The question that selects it |
|---|---|---|
| `action` | a **person** must do, decide, approve, review, or sign off — in a form (human-in-the-loop) | Does a human need to act or judge here? |
| `agent` | an **AI agent** reasons over unstructured input: classify, extract, summarize, draft, score | Is this judgment over unstructured content an AI can do unattended? |
| `rpa` | deterministic **UI / desktop** automation of a legacy app with no API (an existing RPA process) | Is this clicking through a UI / legacy system that has no API? |
| `process` | invoking a **deployed orchestration process** that already packages this automation | Is there a deployed process that already does this end-to-end? |
| `api-workflow` | calling a **coded / API workflow** directly (HTTP, serverless business logic) | Is this an API / coded workflow we call directly? |
| `execute-connector-activity` | one **operation on an Integration Service connector** (e.g. Salesforce create record, send email) | Is this a single connector operation against a SaaS system? |
| `wait-for-connector` | the case **pauses until an external system calls back** (webhook, inbound message, event) | Is the case waiting for an external system to respond? |
| `wait-for-timer` | the case **pauses for a duration or until a datetime** | Is the case just waiting on time? |
| `case-management` | the step **launches / coordinates a child case** | Does this spin up a sub-case? |

**Tie-breakers:** SaaS integration with a tenant connector → `execute-connector-activity` over `api-workflow`. "Approve / review / decide" verbs are ambiguous between `action` (human) and `agent` (AI) — these are Always-Ask ([phase-0-interview.md § When to Ask vs Default](phase-0-interview.md#when-to-ask-vs-default)); never guess. A compliance trigger phrase forces `action` regardless of the pick above (see below).

## Task-type override priority

Extends the Always-Ask gate. Apply in this order when picking task `type`:

1. **User decision pinned to a type** — honor unless schema-invalid (Rule 16) or conflicting with (2).
2. **Regulatory constraint requiring human sign-off** — task MUST be `action`. Trigger phrases that force `action` (regardless of user preference):
   - "only a licensed X may decide / sign off / certify / approve"
   - "regulation requires human review"
   - "ECOA adverse-action notice" / "FCRA adverse action"
   - "NCQA UM 3 adverse determination"
   - "HIPAA-protected approval"
   - "SOC 2 attestation"
   - any `<role>-licensed` or `<role>-credentialed` gate ("licensed underwriter", "credentialed clinician")
   - "fiduciary review", "legal sign-off", "auditor review"

   If the user proposes any non-`action` type AND any of the above appears in the conversation → Ask to confirm; do not silently accept. The Ask phrasing: name the regulation and propose `action` with the LLM/agent work bound to the action's form/recipient.

3. **Tenant evidence** — if the registry cache resolves a deployed Action App / process / agent / api-workflow / RPA that fits, prefer that resource's type and surface the match.
4. **Connector availability** — when an IS connector matches the integration, choose `execute-connector-activity` over `api-workflow`.
5. **Verb signal** — fall through to the Always-Ask table in [phase-0-interview.md § When to Ask vs Default](phase-0-interview.md#when-to-ask-vs-default).
6. **Fallback** — keep the user's stated value if any; otherwise emit a placeholder per SKILL.md Rule 8 and pair it with a high-severity review item (§Review items).

**Worked examples:**

| Case context | User stated | Override fires | Final type |
|---|---|---|---|
| Adverse-action notice (lending) — "ECOA mandates licensed compliance officer signs off" | `agent` (LLM drafts notice) | Yes — tier 2 | `action` (Compliance Officer recipient; LLM-drafted body bound to the action's form context) |
| Vendor scoring on intake | `agent` (LLM scores docs) | No — no regulation, no licensed role | `agent` |
| Underwriting decision on mortgage | `agent` (LLM applies criteria) | Maybe — depends on jurisdiction; verb `decision` Always-Ask + tier-2 trigger phrase absent → Ask user | Ask |
| Inbound webhook from Salesforce | `api-workflow` | No — but tier 4 says prefer connector | `execute-connector-activity` if Salesforce connector exists in tenant; else `api-workflow` |
| Process orchestration call | `process` | No | `process` |

**Compliance trigger detection.** Scan the entire Listen + Ask transcript for the trigger phrases above before recording any non-`action` task type. If a phrase is detected after a non-`action` type was already provisionally recorded, re-Ask the user before continuing to Resolve.

## Render contract

Reason the shape first — [§ Mental model](#mental-model-stages-secondary-stages-tasks) — then apply this contract; it governs *how* a decided stage / secondary stage / task is written, not *whether* it should exist.

Phase 1 reads `sdd.md` as written (Rule 2). The following three sections define **what each case / stage / task element MUST contain** before Approve renames the draft. Every block specifies required vs optional cells, allowed values, source of truth, and the fallback when a value is missing.

**Allowed `—`** (cells the user did not touch and Phase 1 can default safely): case-level Description, variable defaults, persona scope notes, app-view detail, secondary-stage description, optional `IF` conditionExpressions, business calendars on timers.

**Allowed `<UNRESOLVED>`** (gaps Phase 1 / post-build can resolve): registry IDs (`taskTypeId`, `connectionId`, `actionAppId`, `agentId`, `processOrchestrationId`) when Resolve was skipped or returned 0 matches. Pair every `<UNRESOLVED>` with a review item (§Review items).

**Banned `—` or `<UNRESOLVED>`** on every required cell named in the rules below. Either populate with a concrete value, emit a placeholder per Rule 8, or Ask the user.

## Case content rules

Defines what `sdd.md` Section 1 (Case Definition) must contain.

### 1.1 Case Metadata

| Field | Required? | Value shape | If missing |
|---|---|---|---|
| Case Name | yes | PascalCase identifier (e.g., `MortgageLoanOrigination`) | Block Approve. Ask. |
| Description | optional | One prose sentence | `—` |
| Identifier prefix | yes | UPPER, 2-4 chars (e.g., `MLO`) | Default mechanically from PascalCase first letters; record in source ledger. |
| Priority | optional | `Low` / `Medium` / `High` / `Critical` | Default `Medium`; record in source ledger. |
| Case SLA | conditional | Duration (e.g., `5 business days`) | `—` when case has no SLA; otherwise block Approve. |
| SLA Type | conditional | `time-based` (single unconditional duration) / `condition-based` (one or more conditionExpression-keyed overrides + a default time-based row) | Default `time-based` when Case SLA set with no per-condition overrides. The FE persists `condition-based` whenever ≥ 1 `slaRules[]` entry carries a non-empty `conditionExpression` (see PO.Frontend `CaseManagementSlaProperties.tsx:27-30`). `condition-based` requires populating the §Variable SLA Rules table; `time-based` omits it. |
| Case App | optional | `Enabled` / `Disabled` — whether the in-product Case App UI is on (`metadata.caseAppEnabled`). | Default `Disabled`; record in source ledger. |
| Task-output passing | optional | `Direct` / `Shared` — `metadata.caseDirectlyPassTaskOutputs`. `Direct` passes a task's outputs straight to downstream tasks (default). | Default `Direct`. |

**PO.Frontend validation parity.** Before Approve, apply the same name and SLA checks that the Case App applies:

| Surface | Required checks |
|---|---|
| Stage label | Non-empty; unique across stages; no `:`. A non-Case-Manager stage also cannot reuse the reserved default Case Manager stage label when a Case Manager stage exists. |
| Task display name | No `:` for materialized tasks. |
| SLA rule title (`displayName`) | Non-empty; unique within the root or stage target; no `:`. |
| Escalation title (`displayName`) | Non-empty; unique across escalations on the target; no `:`. |
| SLA duration | `count > 0`; when `unit: min`, `15 ≤ count ≤ 1000`. Supported units are `min`, `h`, `d`, `w`, and `m`. |
| Conditional SLA | Every non-default SLA rule has a non-empty expression/condition. |
| Escalation payload | Every escalation has at least one recipient; an `at-risk` escalation has an `atRiskPercentage` value. |

These are blocking authoring errors, not optional style warnings. Preserve the user's wording when repairing a name, but ask for a replacement when uniqueness or a reserved delimiter is violated; never silently suffix or truncate it.

### 1.2 Case-level SLA escalation

Required when Case SLA is set. Always renders with both rows; no `—` allowed in any cell.

| Threshold | Trigger | Recipient |
|---|---|---|
| At-risk | `<pct>%` of case SLA (defaults below) | `UserGroup: <owner-group>` or `User: <name>` |
| Breached | 100% of case SLA | One tier up — leadership group; Compliance for regulation-driven cases |

**Default thresholds** when user did not name them:

- SLA ≤ 3 days → 75% at-risk
- 3 days < SLA ≤ 10 days → 70% at-risk
- SLA > 10 days → 80% at-risk

**Default recipients:** at-risk → stage/case owner persona's user group; breached → leadership group. Record substitutions in source ledger with reason `default applied — user did not name recipient`.

### 1.3 Triggers

≥ 1 trigger required. One row per triggering event. Number triggers sequentially starting at **T02** (T01 reserved for the case file). The T-number is the reference key used by Case Variables rows whose value comes from this trigger's payload (§1.5).

| Field | Required? | Value |
|---|---|---|
| T# | yes | `T<N>` — sequential, starts at `T02` |
| Trigger Type | yes | `Manual` / `Intsvc.TimerTrigger` / `Intsvc.EventTrigger` (`Manual` is author shorthand — see note) |
| Source | conditional | Connector or system for `Intsvc.EventTrigger`; schedule expression for `Intsvc.TimerTrigger`; `Manual` literal for `Manual` |
| Configuration | conditional | User-stated intent only — see Configuration rules below. `Intsvc.EventTrigger` MUST have a concrete operation phrase. |

> **`Manual` is not a `serviceType`.** The CLI serviceType enum is `None` / `Intsvc.EventTrigger` / `Intsvc.TimerTrigger`. A manual trigger carries **no** `serviceType` in `caseplan.json` (absence = manual — see [`plugins/triggers/manual/impl-json.md`](plugins/triggers/manual/impl-json.md)). Author `Manual` in the SDD; never emit `serviceType: "Manual"`.

**Configuration cell — what to write (user intent only, business terms):**

| Trigger type | Write |
|---|---|
| Event | The operation in business terms (`Calendar created`, `Email received`, `Record created`). For tenant case-entity / business data-object starts, preserve the object name in Source (`expense_requests`) and write the business event in Configuration (`Record created`). Append a filter clause when the user wants filtering (`Email received in Inbox; filter: subject contains "URGENT"`). Append a required event-param ONLY when the user supplies it (`Email received in folder "<folder name>"`). |
| Timer | Cycle or duration (`every 24 hours`, `daily at 09:00 UTC`). |
| Manual | `N/A` or omit. |

**Forbidden in Configuration** (skill resolves these at planning time — not author surface):

- CLI enum values like `CALENDAR_CREATED`, `createdRecord`.
- Default modes (`polling` vs `webhook`).
- Meta notes like `No required event parameters` or `No user filter` (absence IS the default).
- Connector activity slug, HTTP method, spec-discovered detail.

> Variable mapping (which trigger payload field populates which case variable) is declared in **§1.5 Case Variables** via the `sourceTriggers` / `sourceFields` columns — NOT in this table. The Triggers table only identifies and configures each trigger; payload extraction is owned by Case Variables.

> **Tenant object starts are not Manual.** If the user says a case starts when a
> tenant case-entity / data-object record is created, record an
> `Intsvc.EventTrigger` row with the object name as Source. Missing tenant
> provisioning, absent local registry data, or unresolved connection details
> become an unresolved event trigger / placeholder later; they are never a reason
> to change the SDD trigger type to `Manual`.

Unresolved `Intsvc.EventTrigger` resolution (`connectionId` / `activityTypeId` missing) → `high`-severity review item.

### 1.3a Trigger Filter (conditional)

Renders ONLY when ≥1 trigger declares a filter. AND/OR tree.

Operators (case-sensitive PascalCase): `Equals`, `NotEquals`, `Contains`, `NotContains`, `StartsWith`, `EndsWith`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `In`, `NotIn`, `IsNull`, `IsNotNull`.

| Field | Operator | Value | Literal? |
|---|---|---|---|
| `<payload field>` | `<operator>` | `<value>` | `Yes` / `No` |

Nested `{op, clauses}` groups flatten in the rendered table. Avoid `Literal: No` for unverified runtime expressions — it forces Phase 1 into JMESPath fallback (lossy). Prefer literal values or open a review item.

### 1.4 Case Completion Conditions

≥ 1 row required. `Marks Case Complete: Yes`.

| WHEN | IF | Marks Case Complete | Exit Type | Display Name |
|---|---|---|---|---|
| `required-stages-completed` / `wait-for-connector` | optional `conditionExpression` | `Yes` | `exit-only` | optional |

> **Display Name** (optional, every condition table — entry, exit, task-entry, case-exit): human-readable label. Carry the author's value verbatim; leave blank / `—` to let the skill default it: entry / task-entry → `Entry Rule {N}`; stage-exit / case-exit → `Complete Rule {N}` (Marks Complete `Yes`) / `Exit Rule {N}` (`No`). `N` = 1-based index within the same label kind in the container. Never invent a label when the cell is blank.

**Allowed WHEN:** `required-stages-completed`, `wait-for-connector`.
**Forbidden WHEN:** `selected-stage-completed`, `selected-stage-exited` (sdd-template Key Rule 4 — `Yes` + `selected-stage-*` is a schema-pairing error → block Approve).

### 1.4a Case Exit Conditions (alternate disposition)

Optional. `Marks Case Complete: No`. Used for secondary-stage terminals (Withdrawn / Rejected / Cancelled).

| WHEN | IF | Marks Case Complete | Exit Type | Display Name |
|---|---|---|---|---|
| `selected-stage-completed("<Stage Name>")` / `selected-stage-exited("<Stage Name>")` / `wait-for-connector` | optional | `No` | `exit-only` / `wait-for-user` | optional |

**When the case has ≥ 1 secondary stage AND Section 1.4a is empty** → emit a `high`-severity review item (`Alt-disposition exits missing`). The case cannot exit non-happy paths cleanly.

### 1.5 Case Variables

**What goes in §1.5 (the declare-vs-xref decision — apply per candidate value):** ONLY (a) `In` / `Out` arguments, (b) trigger-payload `Variable`s (`sourceTriggers` + `sourceFields`), and (c) case-level state read by a condition (`IF`) or consumed in **≥ 2 places**. **An input that is just one upstream task's output is NOT a §1.5 variable** — reference it directly (whole-value `<- "Stage"."Task".out`, or in-expression `vars.$xref('Stage','Task','out')`); the emitting task self-declares the output and is its own producer (see [§ Variable lineage closure → Task-output direct reference](#variable-lineage-closure) and [§ Resolved-resource I/O completeness → xref carve-out](#resolved-resource-io-completeness)). Minting a row to relay one task's output into one downstream consumer is the **case-var relay anti-pattern** — declare a row for an output only to rename it, set a custom `Default` / `Type` / `Description`, or expose it as case-level state read in multiple places.

A variable used anywhere in the plan that meets the test above appears in this table. Authoring is **declarative** — the row's `Category` + `sourceTriggers` + `sourceFields` columns drive build-time classification. Inference from prose or other columns is no longer supported.

| Column | Required? | Notes |
|---|---|---|
| Name | yes | camelCase, no role suffix |
| Category | yes | `In` / `Out` / `Variable` — NEVER `—`. Drives the [`global-vars` plugin's](plugins/variables/global-vars/impl-json.md) pattern shape. |
| Type | yes | Platform type enum (see [case-schema.md](case-schema.md)): `string`, `integer`, `float`, `double`, `boolean`, `datetime`, `date`, `jsonSchema`, `file`. **`file`** is a JobAttachment record (`{ID, FullName, MimeType, Metadata}`) — see `[sdd-template-examples.md](../assets/templates/sdd-template-examples.md)` Use Cases 9–11 for caller-pre-upload, connector-download, and multipart-send patterns. File-typed In-args carry an implicit caller obligation (see §1.5 In semantics + Approve summary reminder). Use `string` for JSON-shaped values; never emit `json` or `jsonSchema`. |
| sourceTriggers | conditional | `Variable`: single `T<N>` or comma-separated CSV (`T02, T03`) when multiple triggers feed the same slot. `In`: optional single `T<N>` selecting the bound trigger (blank = primary trigger T02; never a CSV). Empty for pure state and `Out`. |
| sourceFields | conditional | `Variable` only: single bare payload path when one trigger; **keyed format** `T<N>: <path>; T<M>: <path>` when `sourceTriggers` is CSV. Empty on `In` rows even when `sourceTriggers` names a trigger (`In` selects a trigger, extracts no field). Dot-paths only — no array indexing in v1. |
| Default | optional | Concrete default or empty. |
| Description | yes | One-line meaning. |

**Category semantics** (canonical definition in [`global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md)):

- **`In`** — caller-supplied case argument (manual trigger via API) OR `Default`-initialized (event / timer triggers, which have no caller). `sourceTriggers`: blank → binds the primary trigger (T02; default); a single `T<N>` → binds that trigger — never a CSV (one trigger only). `sourceFields` MUST stay empty — an In-arg selects a trigger but does not extract a payload field; for payload-extraction use `Variable` + `sourceTriggers` + `sourceFields` (see Use Case 2 in [sdd-template-examples.md](../assets/templates/sdd-template-examples.md)). **`In` of `Type: file`** — programmatic caller must pre-create a JobAttachment (`POST /odata/Attachments` then `PUT` bytes) and pass `{ID, FullName, MimeType, Metadata}` plus `StartProcessDto.Attachments[]`. Maestro Studio Web's "Start case" dialog does this automatically; non-Studio callers do it themselves. Surface this obligation in the Approve summary whenever any file-In-arg exists; see §Finalization step 11.
- **`Out`** — case argument returned to caller. Value comes from a producer (a task's Outputs row that targets this Name via `-> {name}` or `{name} = {expr}`) OR from `Default` when no producer fires. `sourceTriggers` MUST be empty (direction mismatch: trigger → case is forbidden for `Out`).
- **`Variable`** — case-internal state. Populated by one trigger's payload (`T<N>` + single path), multiple triggers sharing the same slot (CSV + keyed `T<N>: <path>` format), a task's Outputs row, or `Default` only.

**Config-as-`In` pattern.** Business rules the case needs at runtime — priority bands, approval thresholds, exception taxonomy, payment controls — can be carried as a single `In` variable of `Type: string` whose `Default` is a JSON object, overridable at case start and consumed by agents (e.g. `businessRulesJson`). This gives business logic a first-class, replicable home in the SDD instead of scattering it across prose. Use `string` for the JSON-shaped value (never `json`). For a genuinely structured payload that the FE picker must navigate, use `Type: jsonSchema` and carry its schema in the variable's `body` — a `jsonSchema`/`file` variable without a `body` cannot have its sub-fields picked.

**`sourceFields` notation:**

- **Single-trigger:** bare path. `response.subject`, `response.user.id`, `Error.code`.
- **Multi-trigger:** keyed `T<N>: <path>; T<M>: <path>` — every T-number listed in `sourceTriggers` MUST have a matching keyed entry. Mismatch = Phase 2 validator error. Example: `T02: response.user; T03: response.initiator`.

**Out-arg producer rule.** Every `Out` row MUST have at least one of:

1. A `Default` value, OR
2. A task whose Outputs table has a row that targets this Out-arg's Name via `-> {name}` or `{name} = {expr}`.

If neither, the io-binding validator surfaces the misalignment at end of Phase 3. Phase 0's Approve gate pre-checks this — see §Variable lineage closure.

**`->` vs `=` operators in Outputs rows** (used by every task's Outputs table — defined in §Task content rules):

| Operator | Meaning | `Field` column |
|---|---|---|
| `-> caseVar` | Extract: value at the runtime path in `Field` is written to `vars.<caseVar>`. The skill emits `source: "=<Field>"` verbatim — no envelope inference. | Non-empty full runtime path (`response.status`, `Action`, `Error.code`). |
| `caseVar = <expr>` | Set / compute / copy: case variable receives the expression result at task completion. Expression may be a literal (`"InReview"`, `5`), computed (`=js:(vars.count + 1)`), or copy (`=vars.X.Y`). | `—` |

For worked patterns by Category and operator (single-trigger, multi-trigger, `In` / `Out` / `Variable`, sub-field consumer, Out-arg with Default fallback), see [`sdd-template-examples.md`](../assets/templates/sdd-template-examples.md).

Lineage closure rules in §Variable lineage closure.

## Stage content rules

Defines what each stage in Section 2 must contain. Same rules apply to primary and secondary stages — both are `Stage` nodes; a secondary stage carries `data.stageType: "secondary"` — unless noted.

### Stage heading

- Primary: `` ### Stage {N}: {Stage Name} (`{stage_id}`) `` — N is 1-based sequence number
- Secondary: `` ### Secondary Stage: {Stage Name} (`{stage_id}`) `` — renders a `Stage` node + `Stage Kind: secondary`

The trailing `` `{stage_id}` `` (e.g., `` `stage-intake` ``) MUST appear so readers can grep cross-references. Anywhere a stage is referenced by name in a table cell (`Selected Stage`, `Required Stages`, case-exit selected stage), append the stage id in code-formatted parens.

### Stage fields (per stage)

| Field | Required? | Value |
|---|---|---|
| Type | yes | `Stage` |
| Stage Kind | optional | `primary` (default — omit the line) / `secondary` (emits `data.stageType: "secondary"`; replaces the old `ExceptionStage` type) |
| Description | yes (primary) / optional (secondary) | One prose sentence |
| Required for case completion | yes | `Yes` (primary, default) / `No` (secondary stages always `No`) |
| Interrupting | secondary stages only | `Yes` / `No` — does this stage interrupt active stages on activation? |
| Stage SLA | yes when stage has SLA | Duration + type, plus escalation table |

### Stage Entry Conditions table

≥ 1 row required.

| WHEN | IF | Display Name |
|---|---|---|
| `case-entered` (root only) / `selected-stage-completed("<Stage>")` / `selected-stage-exited("<Stage>")` / `wait-for-connector` / `user-selected-stage` | optional `conditionExpression` | optional |

### Stage Completion Conditions table (`Marks Stage Complete: Yes`)

Completion (`Yes`) rows and the §Stage Exit Conditions (`No`) rows below render **together** as the single **Stage Exit Conditions** table in `sdd.md` (per [sdd-template.md](../assets/templates/sdd-template.md)). Shared columns, in order: `WHEN | IF | Exit Type | Marks Stage Complete | Display Name`. ≥ 1 completion row required. **Regular stage-to-stage routing is NOT carried here** — each destination stage declares the link via its own Entry Condition (`selected-stage-completed("This Stage")` / `selected-stage-exited("This Stage")`), so one stage can fan out to N stages.

> **Carve-out — routing INTO a decision/signal-routed exception lane IS carried here.** This is the one case where the origin stage carries the route: add a **gated diverting exit row** (`Marks Stage Complete: No`, WHEN `selected-tasks-completed("<decider task>")`, `IF` on the decision/signal, `Exit Type: exit-only`, `exitToStageId` → the secondary stage) AND gate this stage's completion row with the **inverse `IF`** so completion and divert are mutually exclusive. Without the diverting exit, the decision path either dual-fires (ungated completion → both the next stage and the lane enter) or deadlocks (gated completion with no alternative exit). See [§ Logical integrity step 5](#logical-integrity--stage-graph) and the worked example below.

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` / `wait-for-connector` | optional | `exit-only` / `return-to-origin` | `Yes` | optional |

**Allowed WHEN:** `required-tasks-completed`, `wait-for-connector`.
**Forbidden WHEN:** `selected-tasks-completed` (Key Rule 4 — `Yes` + `selected-tasks-completed` is a schema-pairing error → block Approve).

### Stage Exit Conditions table (`Marks Stage Complete: No`)

Optional. Used for early hand-offs / routing. Same columns and order as the completion rows above — one rendered table. The destination of a routing exit is set by the destination stage's Entry Condition, not here.

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `selected-tasks-completed("<Task>")` / `wait-for-connector` | optional | `exit-only` / `wait-for-user` | `No` | optional |

### Stage SLA escalation table

Always rendered when Stage SLA is set. Concrete cells in both rows; never `—`.

| Threshold | Trigger | Recipient |
|---|---|---|
| At-risk | `<pct>%` of stage SLA (defaults below) | `UserGroup: <owner-group>` / `User: <name>` |
| Breached | 100% of stage SLA | Leadership group; Compliance for regulation-driven stages |

**Defaults** when user did not name them (mirror §1.2):

- 75% at-risk for SLA ≤ 3d; 70% for 3-10d; 80% for >10d.
- At-risk recipient = stage owner persona's user group; breached = leadership tier (Compliance for regulation-driven stages).

Defaults record in source ledger with reason `default applied — user did not name recipient`.

### Stage Task Summary table

In plan order. ≥ 1 task per stage.

| Column | Value |
|---|---|
| `#` | 1-based row index |
| `Task ID` | `` `{source_task_id}` `` (e.g., `` `t11` ``) — code-formatted, greppable |
| `Task` | Task display name |
| `Type` | One of the 9-value enum (Rule 16) |
| `Owner` | Persona name OR `system` |

Required-Tasks cells in completion / exit conditions use the bare task ids (`t10, t12, t13`) so readers grep across the document.

### Deterministic stage completion (conditional-branch & re-entered stages)

When a stage's real work is split across **mutually-exclusive conditional tasks** (e.g. one `action` per reason code, each entered via `current-stage-entered` + an `IF`), those tasks MUST be `Required: No` — only one runs per case, so none can be the stage's required completer (a `required-tasks-completed` exit over only-conditional tasks is the §Finalization step 17 footgun). Add a **single required convergence task** (typically an `api-workflow` that persists the resolution) whose entry condition is a DNF OR covering every path:

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | `=js:(<none of the conditional guards hold>)` | No specialist branch |
| `selected-tasks-completed("<Conditional Task A>")` | — | — |
| `selected-tasks-completed("<Conditional Task B>")` | — | — |

The convergence task is the stage's only `Required: Yes` task, so `required-tasks-completed` resolves deterministically whichever branch ran — including the no-branch case. (Worked example from a shipping SDD: an Exception-Resolution stage with per-reason-code action tasks + a `Persist exception resolution` api-workflow convergence task carrying exactly the three rows above.)

**Re-entry safety (`return-to-origin` loops).** A task in a stage that an exception lane returns to via `return-to-origin` **re-runs on re-entry** unless flagged `Run Only Once: Yes`. Set `Run Only Once: Yes` on any such task whose re-execution would clobber a decision made during the exception (e.g. an AP-review task whose decision variable the escalation lane just overwrote) — the returning stage then re-evaluates its exit against the lane's decision without re-prompting the original actor. This is the one case where `Run Only Once` is load-bearing rather than cosmetic.

## Task content rules

Defines per-task detail blocks. Every task opens with an **Entry Condition** block. Additional blocks depend on task type.

### Entry Condition block (every task)

```
**Entry Condition**

| WHEN | IF | Display Name |
|---|---|---|
| {rule} | {conditionExpression or "—"} | optional |
```

| Rule | When to use |
|---|---|
| `current-stage-entered` | First event-driven task in stage, or any ungated task (including connector tasks) that should start when its stage is entered. A first task in a sequential chain uses `runs-sequentially` instead. When a task has multiple entry rows, render this one first. |
| `selected-tasks-completed("<Task>")` | Sibling-gated task (e.g., after upstream task in same stage). Multiple tasks comma-separated inside the parens. |
| `wait-for-connector` | Async connector callback. Pair with `conditionExpression` to gate on **case state** (`vars.X`); the event payload is not accessible (no `event` namespace). **In-rule extract-then-gate (extract + same-rule `=js:vars.caseVar` gate) does NOT work at runtime** — case-backend evaluates the gate before the extract populates the case var. To condition on payload content: extract `response.field -> caseVar` on the connector rule and place the case-state gate on a DOWNSTREAM stage-entry / task-entry condition. |
| `adhoc` | Manual fire from the case app. Optional gating expression. |
| `runs-sequentially` | Tasks that should run top-to-bottom in their stage declaration order. The frontend toggle writes this as the task's only entry rule; it is not represented by a lane. |

Multiple entry conditions render as multiple rows (DNF outer-OR). When `current-stage-entered` is among them, render it first.

### `action` task — required cells

| Cell | Value |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>`, where `<deploymentTitle>` is the concrete intended app name. Use the selected registry entry's canonical title when resolved; otherwise retain the user-requested title. NEVER `<UNRESOLVED>`, never paraphrase, never `—`. |
| Action App ID | Concrete deployment id from `action-apps-index.json`, or `<UNRESOLVED>` when no live app was selected |
| Deployment Folder | `deploymentFolder.fullyQualifiedName`, or `<UNRESOLVED>` when Action App ID is unresolved |
| Recipient | Typed prefix (see table below). NEVER a bare string. |
| Priority | `Low` / `Medium` / `High` / `Critical` |
| Task Title | One-line user-visible question/instruction (REQUIRED — Action Center displays it) |
| Labels | Comma-separated when set; otherwise `—` |
| Run Only Once | `Yes` / `No` |
| Required | `Yes` / `No` |
| Input Schema | Table: `Field | Type | Binding | Required` |
| Output Schema | Table: `Field | Type | Binding` (arrow form `-> =vars.<id>`) |
| Buttons | Table only when `is_decision: Yes`: `Button | Maps To | Behavior` |

**HITL Implementation:** the Action App title is the portable Phase 0 → Phase 1 lookup name. Establish it before registry lookup and preserve it when the app is unresolved so a different machine can retry discovery without `tasks/registry-resolved.json`. The action plugin still requires a deployed Action App from `action-apps-index.json` to build a resolved task; when no matching app exists, keep the title, set Action App ID + Deployment Folder to `<UNRESOLVED>`, emit a `high` review item, and fall back to a Rule-8 placeholder. Action Apps are not created inline.

**Input/Output Schema fidelity.** The Input Schema and Output Schema `Field` cells MUST be a subset of the resolved app's actual schema (from `uip maestro case tasks describe --type action --id <actionAppId>`, fetched at Resolve and persisted in `tasks/registry-resolved.json`). Never author a field the deployed app does not expose — it cannot bind (the io-binding plugin has no `data.inputs[]` slot to write into). A field the user described but the app lacks → Ask (deploy a task-specific app / drop the field / placeholder), never silently author it. **Code-switched app (sanctioned — do NOT flag):** reusing ONE deployed app across many `action` tasks is correct and expected when each task carries a **distinct `actionType`** dispatch value and its declared fields are a **subset of the app's schema**. This is the normalized human-decision-app pattern — a single app whose code-behind switches on `actionType` and renders the right form; a full case routes every human decision through it (the working aged-invoice case uses one app across all 7 of its action tasks). It is the generic-substitute anti-pattern ONLY when tasks reuse the app **without** a distinct `actionType`, or declare a field the app does not expose (won't bind) — see §Architect's lens `rev_substitute_app` and §Finalization step 16.

**Recipient encoding** (typed prefix is the only allowed format):

| Prefix | Resolved as |
|---|---|
| `Email: x@y.com` | `{scope: "User", target: <email>, value: <email>}` |
| `User: <uuid>` | Resolved tenant user UUID |
| `UserGroup: <uuid>` | Resolved tenant group UUID |
| `Role: <name>` | Persona / role name — Phase 1 maps role → group at build time |
| `Expression: =vars.<id>` | Runtime expression bound at execution |

No recipient and no role/email known → drop the cell, emit a `high`-severity review item; Phase 1 will prompt.

**Decision flag.** Set `is_decision: Yes` only when the task forks the case path on outcome. `Yes` requires `actions[]` with ≥ 2 buttons; single-button "decisions" are validation errors. Non-decision actions (`Acknowledge`, `Confirm Receipt`) keep `is_decision: No` and render without a Buttons table.

**Buttons table** (decision actions only):

| Button | Maps To | Behavior |
|---|---|---|
| `<label>` (e.g., `Approve`) | `<varName> = "<value>"` | One sentence describing what the button does |

`Maps To` LHS MUST reference a declared case variable from §1.5 (matching a row's `Name` cell) OR the conventional `taskOutcome` handle. NEVER an undeclared identifier.

### `wait-for-connector` / `execute-connector-activity` task — required cells

| Cell | Value | Source |
|---|---|---|
| Connector | Connector key (`salesforce`, `slack`) | IS catalog |
| Connection | Display name | IS connection cache |
| Connection ID | Concrete `connectionId` | IS connection cache |
| Activity Type ID | Concrete `activityTypeId` | IS activity/trigger typecache |
| Service Type | `serviceType` value | IS catalog |
| Auth Method | `defaultAuthenticationType` | IS catalog |
| Account / Endpoint | Connection account/endpoint identifier | IS connection cache |
| Operation / Trigger | Operation or trigger name | IS catalog |
| Operation Configuration | `essentialConfiguration` carry-through as `=jsonString:<json>` literal | IS activity/trigger typecache |
| Inputs | Table: `Field | Type | Binding` — `Field` MUST match IS activity schema verbatim; `Binding` per §Binding cell |
| Outputs | Table: `Field | Binding / Value` — see §Outputs cell operators |

**Entry condition.** A connector task that should start when its stage is entered declares `current-stage-entered` as its first entry row, exactly like any other ungated task; additional rules APPEND as further rows. The skill writes these via the task-entry-conditions plugin (Step 10) — there is no task-type auto-injection.

**Unresolved IDs.** Missing `connectionId` or `activityTypeId` → `high`-severity review item — Phase 1 cannot resolve the connector at build time without them.

### `wait-for-timer` task — required cells

| Cell | Value |
|---|---|
| Timer Type | `timeDuration` (relative) / `dateTime` (absolute) |
| Duration / Until | ISO-8601 duration (e.g., `P30D`) or ISO date-time |
| Business Calendar | Optional — name of business calendar; otherwise `—` |

No `<UNRESOLVED>` on Duration / Until — timer cannot fire without it. Block Approve.

### `case-management` task — required cells

| Cell | Value |
|---|---|
| Child Case | Concrete intended child-case resource `name`. Use the selected registry entry's canonical name when resolved; otherwise retain the user-requested name. NEVER `<UNRESOLVED>`. |
| Folder Path | Exact selected `folders[0].fullyQualifiedName`, or `<UNRESOLVED>` when Resource Identity is unresolved |
| Resource Identity | Selected `entityKey` from `caseManagement-index.json`, or `<UNRESOLVED>` when no live child case was selected |
| Child Case Identifier | Identifier prefix of the child case |
| Data Passed (parent → child) | Table: `Parent Variable | Child Variable` |
| Wait for Completion | `Yes` / `No` |
| Data Returned (child → parent) | Table: `Child Variable | Parent Variable` — render only when `Wait for Completion: Yes` |

`Child Case` is the portable Phase 0 → Phase 1 lookup name. Establish it before registry lookup and preserve it when unresolved; never substitute the parent task's display name. A missing live child case yields unresolved identity/folder fields + a `high` review item and remains placeholder-only.

### `process` / `agent` / `rpa` / `api-workflow` task — required cells

These four runnable types share a single render block. The SDD surfaces both portable resource intent and resolution state. `Resolved Resource` is always a concrete intended name; `Resource Identity` alone says whether Resolve selected a live resource. This keeps the document usable when Phase 0 and Phase 1 run on different machines and `tasks/registry-resolved.json` is not transferred.

| Cell | Required? | Value |
|---|---|---|
| Resolved Resource | yes | A concrete intended resource `name` (the `name`-binding default) — e.g. `AgedInvoiceMockIntegrationApi`, `InvoiceTriageAgent`. Use the selected registry entry's canonical name when resolved; otherwise retain the user-requested name. NEVER write `<UNRESOLVED>` in this cell. |
| Folder Path | yes | Resolved `folders[0].fullyQualifiedName` (the `folderPath`-binding default), or `<UNRESOLVED>` when `Resource Identity` is unresolved. A concrete value must be the exact resource folder, never a parent path. |
| Resource Identity | yes | The resolution-status cell. Write the resolved id (+version): `apiWorkflowId` / `agentId` / `processOrchestrationId`, or `<UNRESOLVED>` when no live resource was selected. Also carry it in `tasks/registry-resolved.json` when that optional cache exists. |
| Binding Sub-Type | yes | `resourceSubType` on the bindings: `Api` (api-workflow) / `Agent` (agent) / `ProcessOrchestration` (process) / `—` (rpa). Omitting it makes Studio Web report the resource as not found. |
| Dispatch / Operation | conditional | When the resource is a shared façade dispatched by a parameter (e.g. one mock-integration api selected by `requestSource`, one code-switched action app), name the selector + value (`requestSource = "RegisterCaseShell"`). `—` for single-purpose resources. Also appears as an Inputs row (literal binding). |
| Inputs | yes | Table: `Field | Type | Binding` — `Field` MUST match the runnable's declared In argument name verbatim; `Binding` per §Binding cell |
| Outputs | yes | Table: `Field | Binding / Value` — `Field` MUST match the runnable's declared Out argument name verbatim for `->` rows (or `—` for `=` rows); see §Outputs cell operators |

**Where the rest of the metadata lives.** Deep per-type runtime metadata that does NOT affect replication of the case plan (agent system prompt, RPA package version, api-workflow endpoint URL, process release tag) stays out of the SDD body — it is resolved during §Resolve in [phase-0-interview.md](phase-0-interview.md#resolve) and persisted in `tasks/registry-resolved.json` under the task's resolution entry (per SKILL.md Rule 9 shape). The SDD carries the resource **name + folder + id + sub-type** (above). Phase 1 may reuse deeper metadata only after the cached type/name/folder/identity matches the current SDD per [planning.md § Phase 0 carryover](planning.md#step-2--locate-and-parse-the-design-document); otherwise it re-runs discovery from the SDD and replaces the stale entry. Mapping:

| Task type | Registry source | Identity field in `registry-resolved.json` |
|---|---|---|
| `process` | `process-index.json` | `processOrchestrationId` |
| `agent` | `agent-index.json` | `agentId` (+ version) |
| `rpa` | (registry per RPA convention) | `processOrchestrationId` for RPA processes |
| `api-workflow` | `api-index.json` | `apiWorkflowId` (+ endpoint) |

Unresolved registry identity → `high`-severity review item (§Review items). The SDD shows the runnable name + In/Out bindings; the identity flows through the audit trail.

**No task SLA.** Per [sdd-template.md](../assets/templates/sdd-template.md) Key Rule 1, SLA is supported on the case, on stages, and on `action` tasks ONLY. Do NOT emit SLA cells on `process`, `agent`, `rpa`, `api-workflow`, `wait-for-timer`, `wait-for-connector`, `execute-connector-activity`, or `case-management` tasks.

**Externally-hosted AI agents** (CrewAI, Salesforce Einstein, Databricks, LangChain, etc.) are NOT first-class. Model them as `api-workflow` (system-to-system) or `execute-connector-activity` when a connector exists. Never invent `external-agent`.

### Binding cell — allowed expressions (Inputs)

Every Inputs `Binding` cell carries one of (case-sensitive):

| Form | Meaning |
|---|---|
| `<literal>` | Plain string / number / boolean (`"50"`, `0`, `true`) |
| `=vars.<id>` | Case variable from §1.5 (`<id>` matches a §1.5 row's `Name`), or an upstream task's auto-emitted output field referenced directly (see §Variable lineage closure) |
| `=vars.<id>.<subfield>` | Sub-field of a structured case variable (dot-path) |
| `=bindings.<id>` | Registered resource (action app, process, connection) |
| `=metadata.<key>` | Case metadata |
| `=metadata.ExternalId` | **The platform-generated case identity** — the canonical binding for any task input named `caseId`. The case external id is minted by the platform (constant prefix or external expression) and exposed as `metadata.ExternalId`; it is **NOT** a task output. Bind `caseId` to `=metadata.ExternalId`; **never** add a `-> caseId` extraction on a workflow whose `data` payload has no `caseId` key — that extraction resolves to runtime null (a documented v4→v5 fix on a working case). Agents, the case mirror, and all write-backs key off `=metadata.ExternalId`. |
| `=trigger.<field>` | Trigger payload field |
| `=js:<expr>` | Inline JavaScript (REQUIRED when operators are involved) |
| `=jsonString:<json>` | JSON literal as string (used for `essentialConfiguration` carry-through) |
| `=datafabric.<path>` | Data Fabric reference |
| `=orchestrator.JobAttachments` | File slot |
| `=response` / `=result` / `=Error` | Conventional handles for connector / agent / process responses |
| `"<Stage Name>"."<Task Name>".<outputName>` | Cross-task output reference — Phase 1 resolves to `=vars.<id>` at build time |

**Bare field-name lists** (`**Inputs:** loanId, borrowerLegalEntity`) are FORBIDDEN. They force Phase 1 into name-match inference — the exact failure mode the table form prevents.

### Outputs cell operators

Every Outputs `Binding / Value` cell carries one of two operators (case-sensitive). The `Field` column rule differs by operator:

| Operator | Cell form | `Field` cell | Purpose |
|---|---|---|---|
| Extract | `-> <caseVar>` | **Non-empty** — full runtime path relative to task root (`response.status`, `Action`, `Error.code`). Skill emits `source: "=<Field>"` verbatim. | Capture a runtime response field into a case variable. |
| Set / compute / copy | `<caseVar> = <expr>` | `—` (em-dash literal) | Assign a literal, computed (`=js:(...)`), or copied (`=vars.X.Y`) value at task completion. |

**Authoring rules:**

- The LHS case variable (after `->` or before `=`) MUST already be declared in §1.5 Case Variables. Outputs rows DO NOT declare new variables — they wire existing ones.
- Per task: each target case variable appears in at most one Outputs row. No double-binding. Mixing `->` and `=` for the same target in the same task is rejected.
- A single task may carry both `->` rows (extract) AND `=` rows (literal / computed) targeting different variables.

**Example (any task's Outputs table):**

```
| Field           | Binding / Value                          |
|-----------------|-------------------------------------------|
| response.status | -> sendStatus                             |
| Action          | -> userDecision                           |
| —               | caseStatus = "InReview"                   |
| —               | reviewCount = =js:(vars.reviewCount + 1)  |
```

For worked patterns by Category and operator, see [`sdd-template-examples.md`](../assets/templates/sdd-template-examples.md).

### Resolved-resource I/O completeness

When a task resolves to a **live** resource (`process` / `agent` / `rpa` / `api-workflow` / `action` / `execute-connector-activity` / `wait-for-connector` / `case-management`), the SDD's binding contract MUST cover that resource's declared I/O — not merely match names verbatim where rows exist (§Binding cell, §Outputs cell). The declared contract is the one pulled at §Resolve in [phase-0-interview.md](phase-0-interview.md#resolve) (`tasks describe` for runnables, `spec` for connectors) and persisted — including each input's `required` flag and the full output-field list — in `tasks/registry-resolved.json`. Coverage is two-directional:

**Inputs — required-coverage.** Every **required** declared input has an Inputs row whose `Binding` is non-empty (any allowed form in §Binding cell), OR is explicitly `<UNRESOLVED>` paired with a `high` review item (`rev_unbound_input_<task>_<field>`). A required input silently absent from the Inputs table is the defect this rule catches — it resolves to runtime null and faults the job. **Optional** declared inputs MAY be omitted; an optional input the user described but did not map → `medium` review item (existing §Resolve behavior). Never invent a `Default` to suppress an unmapped required input.

**Outputs — field fidelity.** Every Outputs `-> caseVar` (extract) row's `Field` (its top-level leaf) MUST exist verbatim in the resolved output contract. A `Field` the resource does not emit → `high` review item (`rev_phantom_output_<task>_<field>`); it cannot bind. The case still binds outputs **selectively** — only the outputs it consumes need rows; this rule forbids referencing outputs the resource never produces, not under-consuming. (This generalizes the action-app-only fidelity rule, §Finalization step 16, to all runnable/connector types.)

**xref carve-out — an upstream-output-fed input is *defined*, NOT a case variable.** When a required input is satisfied by an upstream task's output — whole-value `<- "Stage"."Task".out` (resolves to `=vars.<outputId>`) or in-expression `vars.$xref('Stage','Task','out')` — it counts as covered: do **NOT** raise a "missing variable" finding for it. The emitting task self-declares the output and is its own producer; declare a §1.5 row for it only per the [§ 1.5 declare-vs-xref test](#15-case-variables) (rename / custom `Default` / `Type` / `Description` / case-level state read in ≥ 2 places). See also [§ Variable lineage closure → Task-output direct reference](#variable-lineage-closure).

Enforced at the Approve gate (§Variable lineage closure audit checklist + §Finalization step 19) and re-verified at build (Phase 3 io-binding Check 5, [`io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness)). A task whose type-specific identity (`Resource Identity` or `Action App ID`) is `<UNRESOLVED>` has no resolved contract and is skipped by this rule. Its type-specific portable name remains concrete.

## Integrations content rules (Section 4)

Section 4 is the **de-duplicated resource roll-up** — one subsection per rendered resource family, so the case's integration/resource footprint is replicable from the SDD alone. An unresolved row keeps its concrete intended resource name and writes `<UNRESOLVED>` only for folder and identity. Render only the families whose task type appears; render `> None.` for an absent family when its absence is meaningful (e.g. "no IS connectors — all system calls go through an API workflow").

| Subsection | Render when the case has… | Required columns |
|---|---|---|
| Integration Service Connectors | `execute-connector-activity` / `wait-for-connector` tasks | Connector, Connector Key, System, Connection (ID), Auth Method, Operations Used, Used By Tasks (+ per-connector Operations: Activity Type ID, Method, I/O fields) |
| API Workflows | `api-workflow` tasks | Workflow, Folder, Resource ID (+version), Inputs → Outputs, Used By Tasks |
| Agents | first-class `agent` tasks | Agent, Folder, Resource ID (+version), Inputs → Outputs (or "shared agent contract"), Used By Tasks |
| Processes & RPA | `process` / `rpa` tasks | Resource, Type, Folder, Resource ID (+version), Used By Tasks |
| Child Cases | `case-management` tasks | Child Case, Folder, Resource ID, Identifier Prefix, Wait for Completion, Used By Tasks |
| External Agents | externally-hosted agents modeled as `api-workflow` / `execute-connector-activity` | Agent, Service Type, Endpoint, Used By Tasks |

**De-dup rule.** One row per **distinct** resource, not per task. When a façade resource backs many tasks (one mock-integration API selected by `requestSource`, one code-switched action app by `actionType`), list the distinct selector values next to the task names in `Used By Tasks` (e.g. `Start case (requestSource=StartAgedInvoiceCase), Register shell (requestSource=RegisterCaseShell)`). Action apps render in their per-task Action blocks (Section 2), not as a Section 4 subsection — they are HITL surfaces, not system integrations — but the same de-dup + `actionType`-selector discipline applies there.

**Resource identity is mandatory.** Every Section 4 row carries the resource's **folder + id** (`<UNRESOLVED>` + a `high` review item when Resolve could not bind it). A reader / coding-agent replicates from these, not from I/O contracts alone (§Finalization step 18).

## Variable lineage closure

Every variable referenced in `sdd.md` must close — every consumer must have a producer that fires before it, OR the variable must carry a `Default` value that holds at case start.

The new SDD shape carries producer / consumer signal across three places (NOT a `Produced By` / `Consumed By` pair of cells — those columns were retired):

| Producer signal | Where it lives |
|---|---|
| Trigger payload extraction | §1.5 row's `sourceTriggers` (T-number) + `sourceFields` (payload path) |
| Task-output extraction | Producing task's Outputs row → `-> <caseVar>` |
| Task-output set / compute / copy | Producing task's Outputs row → `<caseVar> = <expr>` |
| Case-start default | §1.5 row's `Default` |

| Consumer signal | Where it lives |
|---|---|
| Task input reads variable | Task's Inputs row `Binding` cell → `=vars.<caseVar>` or `=vars.<caseVar>.<subfield>` |
| Condition / exit rule reads variable | `IF` column `conditionExpression` → `=vars.<caseVar>` or `=js:` expression referencing `vars.<caseVar>` |
| Action button writes variable | `Maps To` cell → `<caseVar> = "<value>"` (the button IS a producer for that variable) |

**Closure rule.** For every consumer of `vars.<caseVar>`, at least one of these must hold:

1. There is a producer earlier in stage order (or earlier in same-stage task order).
2. The §1.5 row for `<caseVar>` declares `Category: In` (caller-supplied — closure satisfied at case start).
3. The §1.5 row for `<caseVar>` carries a non-empty `Default` value (closure satisfied at case start, even if no producer fires).

Otherwise the variable is open-lineage and Phase 0 cannot Approve.

**Task-output direct reference.** A `=vars.<name>` where `<name>` is an upstream task's auto-emitted output field is NOT a §1.5 variable — exempt from closure. The emitting task self-declares it (resolver matches any `task.data.outputs[].id`) and is its own producer; only ordering applies (emitting task before consumer). Declare a §1.5 row only to rename, set custom `Default` / `Type`, or expose case-level state. Unresolvable refs (typo, or a field the task does not emit) are caught later by the io-binding validator (Check 1), not here. See [sdd-template-examples.md § Task-local-only variables](../assets/templates/sdd-template-examples.md).

**Self-binding rule.** An Outputs row of the form `caseVar = =vars.caseVar` or `caseVar = =js:vars.caseVar` (LHS and only-referenced-RHS variable are the same `caseVar`) is FORBIDDEN — it's a no-op that masks a missing producer. Phase 0 strips such rows from the draft, narrates the strip, and emits a `high`-severity review item asking the user whether they meant to (a) wire a different producer, (b) drop the row entirely, or (c) initialize via §1.5 `Default`. Computed self-references like `caseVar = =js:(vars.caseVar + 1)` are allowed (incrementers / accumulators) — the RHS expression mutates the value.

**Output-naming consistency rule.** An Outputs `-> <caseVar>` row whose `Field` leaf name (the produced datum's natural name, e.g. `complianceStatus`) has NO matching §1.5 variable AND is mapped into a differently-named existing variable (e.g. `titleReviewStatus`) → emit a `medium` review item (`rev_aliased_output_<task>`): "task output `<field>` aliased into unrelated variable `<caseVar>`; declare a dedicated §1.5 variable for the datum or confirm the reuse is intentional." Aliasing a produced datum into an unrelated variable closes lineage mechanically while corrupting meaning — a variable named for one thing silently carries another, and a multi-stage variable ends up double-purposed.

**Stage exit pattern — XOR terminal stages.** When the user describes mutually-exclusive happy-path terminals (e.g., "Funding on approve, Adverse Action Notice on decline"), the case has two valid endings but only one fires per run. Key Rule 4 forbids `selected-stage-*` on case-exit `Yes` rows, so the XOR is modeled at the stage-entry level, not the case-exit level. Two sanctioned patterns:

**Pattern X1 — gated entry + required terminal closes** (default — works on every tenant, no connector emission needed):

- Both terminal stages declared with `Required for case completion: Yes`.
- Each terminal stage's Entry Condition: `selected-stage-completed("<DecisionStage>")` + `IF` = the condition guarding its lane (e.g., `IF: =vars.decision == "Approve"` for Funding, `IF: =vars.decision == "Decline"` for AAN).
- **Stage Completion Conditions on each terminal stage:** `required-tasks-completed` (`Marks Stage Complete: Yes`) — the terminal closes normally when its tasks finish.
- **Stage-skip rule** (Phase 1 validator):  the runtime evaluates Entry Condition `IF` at stage activation time; a terminal whose `IF` is false at activation is auto-completed (`status = "Skipped"`) so `required-stages-completed` still resolves cleanly across the case. This is documented FE behavior — see PO.Frontend stage validation rules. The skipped stage counts as "completed" for required-stages closure.
- Case Exit §1.4: ONE row, `Marks Case Complete: Yes`, WHEN = `required-stages-completed` (default form), `IF: —`.

**Pattern X2 — connector-event close** (use when both terminals end by emitting a common case-done event):

- Both terminal stages: `Required for case completion: No`.
- Each terminal stage Entry Condition: as in X1.
- Each terminal's last task is a `wait-for-connector` or `execute-connector-activity` that emits a shared case-completion event (e.g., funding-confirmed AND aan-sent both fire `caseDone`).
- Case Exit §1.4: ONE row, `Marks Case Complete: Yes`, WHEN = `wait-for-connector` keyed on `caseDone`.

Pattern X1 is preferred unless an actual connector emits the close event. When the pattern is detected at Sketch time (multiple terminal candidates AND a branching decision earlier in the case), narrate the choice and surface BOTH patterns to the user via AskUserQuestion before drafting the rows.

**Audit checklist** (run before Approve renames the draft):

1. Every variable referenced by any `=vars.<name>` (or `=vars.<name>.<sub>`) anywhere in `sdd.md` (task Inputs, IF columns, exit rules, button `Maps To`, SLA expressions) has a matching §1.5 row whose `Name` equals `<name>` — OR `<name>` is an upstream task's auto-emitted output field (see §Variable lineage closure → Task-output direct reference; never add a §1.5 row to back such a ref).
2. Every §1.5 row's `Category` is exactly one of `In` / `Out` / `Variable` — never blank, never `—`.
3. **`In` row consistency:** `sourceFields` is empty. `sourceTriggers` is empty (binds the primary trigger) OR a single `T<N>` that exists in tasks.md (binds that trigger) — never a CSV. A CSV `sourceTriggers`, or any non-empty `sourceFields`, on an `In` row is an error.
4. **`Out` row consistency:** `sourceTriggers` is empty. Closure requires either (a) non-empty `Default`, OR (b) a task Outputs row in the case plan targeting this Name via `-> {name}` or `{name} = {expr}`. (PR 860 added a Phase 2 validator: `Out` + non-empty `sourceTriggers` → reject.)
5. **`Variable` row consistency:** if `sourceTriggers` is non-empty, `sourceFields` MUST have a matching entry for every T-number listed. For CSV `sourceTriggers`, `sourceFields` MUST use keyed `T<N>: <path>; T<M>: <path>` format with one keyed entry per T-number — strict, no defaults. Single-T-number rows use a bare path.
6. **Stage-order closure.** For each consumer of `vars.<caseVar>`, identify producers (trigger-extraction, task Outputs row `->` or `=`). At least one producer's stage index ≤ consumer's stage index AND (same stage) task index < consumer's task index. If no producer exists, the §1.5 row MUST satisfy the `Category: In` or non-empty `Default` escape.
7. **`->` row payload path present.** Every Outputs `-> {caseVar}` row has a non-empty `Field` cell (the runtime path). Every `=` row has `Field` exactly `—`.
8. **Forbidden body vocabulary.** No occurrence in any narrative cell of: `Pattern C`, `bridge`, `companion`, `inputOutputs[]`, `=jsonString:` (outside connector `Operation Configuration` cells), `groupOperator`, `essentialConfiguration` (as prose), `savedFilterTrees`, `dispatcher`, `Phase 2 validator`, `Phase 3 dispatcher`, `Q10 II`, `Finding #N`, `io-binding`, `aliased into / from / back into`, `reassign`, `originalVar`, `auto-mint`. These are skill-internal terms — see [sdd-template.md § Output Rules](../assets/templates/sdd-template.md).
9. **Resolved-resource I/O completeness** (§Resolved-resource I/O completeness). For each task resolved to a live resource (contract present in `tasks/registry-resolved.json`): every **required** declared input has a non-empty `Binding` row OR `<UNRESOLVED>` + a paired `high` review item; every Outputs `-> caseVar` row's `Field` exists verbatim in the resolved output contract. An upstream-output-fed input (whole-value `<-` or `vars.$xref(...)`) satisfies coverage with NO §1.5 row — do not flag it as a missing variable. Skip tasks whose type-specific identity (`Resource Identity` or `Action App ID`) is `<UNRESOLVED>` (no contract).

Any failure → Phase 0 cannot Approve. Surface in edit-validation errors. AskUserQuestion `Re-edit` / `Restart` / `Abort`.

## Review items

A review item is a structured gap escalation. Phase 0 emits one whenever a field could not be fully resolved but Phase 1 needs the context. Review items live in `tasks/registry-resolved.json` under the matching task's `review_items[]` array and surface in the Approve summary — never in the `sdd.md` body (per [sdd-template.md § Output Rules](../assets/templates/sdd-template.md): review items belong in the summary, not the document).

Shape:

```jsonc
{
  "id": "rev_<short-slug>",
  "target": "<sdd.md section path or task name>",
  "issue": "<one-sentence problem>",
  "severity": "high" | "medium" | "low",
  "next_step": "<what the user must do to resolve>"
}
```

Severity:

| Level | Definition | Examples |
|---|---|---|
| **high** | Blocks Phase 1 / `caseplan.json` build until resolved. | Missing `connectionId` for a resolved connector task; missing `actionAppId` for an `action` task; missing deployed `process` / `agent` / `api-workflow` for a runnable task; a resolved resource's **required** input left unbound (`rev_unbound_input_<task>_<field>`); an extract output naming a field the resource does not emit (`rev_phantom_output_<task>_<field>`); unresolved variable lineage; missing trigger config; compliance-override conflict the user has not reconciled. |
| **medium** | Phase 1 can default with a prompt. | Missing SLA escalation recipient (default = owner group); missing variable default; ambiguous recipient (persona name without group resolution). |
| **low** | Cosmetic. | Missing case-level description; missing secondary-stage description; stylistic placeholder. |

**Approve gate behavior.** When any `high` review items exist, Approve adds an explicit follow-up: `Approve despite N high-severity items` (with the count populated). User must opt in — silent approval is forbidden. Medium and low items show in the Approve summary count but do not require explicit acknowledgment.

## Domain fidelity

Phase 0's narrative cells (Description, persona names, stage names, task names, button labels, prose under §Section 3 personas, §Section 4 integrations) MUST preserve the user's domain vocabulary verbatim. The skill is a transcription layer for business terms, not a paraphraser.

**Preserve verbatim** (do NOT swap to a synonym, even if it sounds more "standard"):

- Customer-named roles (`CFO`, `Underwriter II`, `Compliance Officer`, `Triage Nurse`, `Onboarding Specialist`). Do NOT substitute `Approver`, `Reviewer`, `Manager` unless the user used that exact term.
- Customer-named domain nouns (`Vendor`, `Supplier`, `Partner`, `Claim`, `Application`, `Loan File`, `PO`, `Ticket`, `Member`, `Patient`). Pick the one the user used. Do NOT homogenize to `Record` or `Item`.
- Customer-named stage labels (`Triage`, `Underwriting`, `Adverse Action Notice`). Use the user's casing and word choice. Prefix-pad to PascalCase only at the Case Name level (e.g., `MortgageLoanOrigination`).
- Customer-named decision outcomes (`Approve` / `Decline` / `Needs Info` not `Approve` / `Reject` / `Pending`).
- Customer-named integration shortnames (if user said `Workday`, never write `the HR system`).

**Allowed normalization** (mechanical, narrate in ledger as `mechanical:<derivation>`):

- PascalCase Case Name from a spaced phrase (`vendor onboarding` → `VendorOnboarding`).
- 2-4 char identifier prefix from the PascalCase name.
- camelCase variable names from spaced phrases (`loan amount` → `loanAmount`).

**Detection — when user writes a term once, surface it in the source ledger** as `verbatim:"<quoted exact phrase>"` (see §Source ledger). On Approve, the user is asked to confirm spelling/casing for every customer-named entity.

**Anti-paraphrase rule.** When the agent feels the urge to write `the manager approves the request` and the user said `the senior underwriter signs off`, the agent MUST use `the senior underwriter signs off`. Synonyms are a fidelity bug, not a polish improvement.

## Logical integrity — stage graph

Beyond schema-pairing checks (§Finalization step 1), the case must be a connected graph. **Edges are retired — these condition-based checks are the SOLE reachability guard; there is no edge graph to fall back on.** A malformed or missing entry condition is the only thing that can orphan a stage, so this walk is load-bearing.

1. **Every stage reachable from a trigger.** Walk forward from each trigger row through Stage Entry Conditions (`case-entered` from root, `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`) — condition-only, no edges. Every primary stage's id must be reached. Unreachable stage → blocking error (orphan stage).
2. **Every stage exits.** Every primary stage must have either (a) a completion row (`Marks Stage Complete: Yes`) whose completion is consumed by a downstream stage's Entry Condition or a case-exit, OR (b) another primary stage whose Entry Condition references it (`selected-stage-completed`/`selected-stage-exited`), OR (c) feed a secondary stage. A stage no other stage (or case-exit) keys off → blocking error (terminal-loop stage).
3. **Every case-exit row references a stage that exists.** No dangling `Required Stages` references.
4. **Every `Required Stages` cell in §1.4 names ≥ 1 primary stage with `Required for case completion: Yes`.** Otherwise the case can never complete.
5. **Secondary stages must have ≥1 entry condition, each DISTINCT, chosen by trigger source.** Map the lane's *trigger* to the rule: a gate decision → `selected-stage-completed` / `selected-stage-exited` (+ `IF` on the decision var); a person launches it → `user-selected-stage`; an external event → `wait-for-connector`. `adhoc` is task-entry only — never a stage entry. Two secondary stages whose entry rules are identical (same rule type + `selectedStageId` + `conditionExpression`) fail `validate` (`CASE_MGMT_SECONDARY_STAGE_ENTRY_RULES_DUPLICATE`) — give each a distinct `selectedStageId` or `conditionExpression` guard. Set `Interrupting: Yes` for lanes that fire mid-stage (escalation, comms, withdrawal). Terminal lanes (Rejected / Withdrawn) exit `exit-only` and declare a §1.4a case-exit (`marks-case-complete: false`); return lanes (Escalation / Customer Comms) exit `return-to-origin`. **Decision-reachable lanes:** when any decision button's Behavior (or the user's stated intent) names a secondary stage as a destination ("route to / send to / escalate via the X lane"), that lane's entry conditions MUST include a `selected-stage-completed` / `selected-stage-exited` rule with an `IF` on the deciding variable's value. A lane described as decision-reachable but entered ONLY via `wait-for-connector` (no decision-keyed entry) is unreachable from its stated source → blocking error. A `wait-for-connector` entry may coexist as a separate trigger, but cannot be the lane's only entry when a decision is supposed to reach it. **A `selected-stage-completed`/`selected-stage-exited` lane entry REQUIRES a matching origin diverting exit — the entry alone is not enough.** On the *origin* stage add a **gated diverting exit** (`Marks Stage Complete: No`, WHEN `selected-tasks-completed("<decider task>")`, `IF =js:(<signal> === <exception-value>)`, `exit-only`, `exitToStageId` → the lane) **and** gate the origin's completion exit with the inverse `IF` (`=js:(<signal> !== <exception-value>)`) so the two are mutually exclusive. Without the diverting exit the decision path either **dual-fires** (ungated completion → the next stage *and* the lane both enter) or **deadlocks** (gated completion with no alternative exit). `selected-stage-exited` fires *after* the origin exits, so this is a **divert-and-return, not a true mid-stage interrupt** — a genuine mid-stage interrupt needs `user-selected-stage` or `wait-for-connector` (mental-model shape (a)). Missing origin diverting exit, or a completion exit not mutually exclusive with it → blocking error.
6. **Classify each secondary stage's `Interrupting` flag by whether it must halt active work.** `Interrupting: Yes` pauses the active stage(s) when the lane fires; `Interrupting: No` runs alongside them in parallel while the main flow continues. Choose the value from the lane's intent — does handling it require stopping the rest of the case, or can it proceed concurrently? Interrupting is independent of whether the lane is terminal or returning. The one hard rule: a `return-to-origin` exit **requires `Interrupting: Yes`** — the case can only return to a stage it interrupted, so a non-interrupting `return-to-origin` lane is incoherent → blocking error.

**Worked example — decision/signal-routed return exception (AP Review → SLA Escalation).** The origin "AP Review" routes to the exception lane "SLA Escalation" on a `requiresEscalation` decision, then returns:

| Stage | Condition | WHEN | IF | Exit Type | Marks Complete |
|---|---|---|---|---|---|
| AP Review | exit (complete) | `required-tasks-completed` | `=js:(vars.requiresEscalation !== true)` | `exit-only` | Yes |
| AP Review | exit (divert) | `selected-tasks-completed("AP ownership review")` | `=js:(vars.requiresEscalation === true)` | `exit-only` (`exitToStageId` → SLA Escalation) | No |
| SLA Escalation | entry | `selected-stage-exited("AP Review")` | `=js:(vars.requiresEscalation === true)` | — | — (`Interrupting: Yes`) |
| SLA Escalation | exit | `required-tasks-completed` | — | `return-to-origin` | Yes |

On escalate: the divert exit fires (completion's inverse `IF` is false), the case enters SLA Escalation, then `return-to-origin` re-activates AP Review for re-decision. On non-escalate: the completion exit fires and the next regular stage enters via its own `selected-stage-completed("AP Review")` entry. The decision (`requiresEscalation`) is read directly from the producing action's output — never relayed through a §1.5 variable.

Failure on any step → blocking error in Finalization. AskUserQuestion `Re-edit` / `Restart` / `Abort`.

## Architect's lens

Phase 0's job is to surface execution-readiness gaps, not just schema validity. Run these advisory checks at Finalization and emit `medium` review items (not blocking, but visible to the user) whenever they fire:

| Check | Trigger | Review item |
|---|---|---|
| **Single-recipient bottleneck** | An `action` task's `Recipient` is `User: <single uuid>` or `Email: <single>` AND the stage runs on every case AND the case has no documented volume limit | `rev_bottleneck_<task>`: "Single named recipient for an always-on `action` task — confirm volume or change to UserGroup / Role." |
| **No escalation when SLA exists** | Stage has SLA AND escalation table absent or omitted | `rev_escalation_<stage>`: "Stage SLA defined but no escalation recipients — leadership will not be paged on breach." |
| **Escalation routes to same group already breaching** | Stage SLA escalation Recipient equals the stage's primary recipient | `rev_escalation_loop_<stage>`: "Escalation recipient is the same actor already missing the SLA — pick a tier-up group or skip-level recipient." |
| **Synchronous child case in critical path** | `case-management` task `Wait for Completion: Yes` AND the parent has SLA AND no exception-path stage covers child-case timeouts | `rev_childcase_<task>`: "Synchronous child case in SLA-bound parent — consider Wait for Completion: No + completion connector, or an exception path on timeout." |
| **All-`action` stage** | A stage's tasks are 100% `action` AND stage has > 2 tasks | `rev_human_only_<stage>`: "All tasks in this stage are HITL — consider whether agent / process / api-workflow can pre-fill or pre-screen before human review." |
| **Missing happy-path exit on first stage** | The first primary stage has only routing exits (`Marks Stage Complete: No`) and no `required-tasks-completed` row | `rev_no_happy_path_<stage>`: "First stage has no happy-path completion — the case may not reach Stage 2 cleanly." |
| **Decision-button outcome unread** | An `action` task with `is_decision: Yes` writes a case variable in its `Maps To` cell AND that variable is NOT consumed by any downstream condition / stage entry / task input / case exit | `rev_orphan_decision_<task>`: "Decision button writes `<var>` but no downstream rule reads it — branching has no effect on case path. Either consume the variable or downgrade `is_decision` to No." |
| **Connector-task failure has no exception path** | `execute-connector-activity` / `wait-for-connector` task in a primary stage AND no secondary stage entered via `wait-for-connector` failure or task failure rule | `rev_no_failure_path_<task>` (`medium`; **`high`** when ≥ 2 connector tasks share a primary critical path with zero exception cover): "Connector activity in critical path with no secondary-stage cover — runtime failure halts the case." |
| **Generic action app reused as a substitute** | ONE resolved Action App ID bound to ≥ 2 `action` tasks **that do NOT each carry a distinct `actionType`**, OR where a declared field is absent from the app's schema (won't bind). **Exempt:** a code-switched app — distinct `actionType` per task **and** every declared field ⊆ the app schema — is the sanctioned normalized-action-app pattern, NOT flagged. | `rev_substitute_app_<app>` (`high`): "Action app reused across N tasks without a code-switching `actionType` (or with fields the app does not expose) — declared fields will not bind. Make it a code-switched app (distinct `actionType` per task, fields ⊆ the app schema) or deploy task-specific apps." |
| **Multiple parallel single-recipient bottlenecks** | ≥ 2 stages have single-recipient bottleneck check fire AND they fan-in to the same downstream stage | `rev_multi_bottleneck_<stages>`: "Multiple single-recipient bottlenecks gate a downstream stage — fan-in stalls cascade." |
| **Case-var relay (over-declaration)** | A §1.5 `Variable` row whose **only** producer is one task's Outputs `->` row AND whose **only** consumer is one downstream binding (one task Input `=vars.X`, OR one `=js:` expression / `IF`) — i.e., it carries a single output to a single consumer and is neither `In`/`Out` nor read in ≥ 2 places. **Exempt:** rows that rename, set a custom `Default` / `Type` / `Description`, or are read by ≥ 2 consumers / a condition. | `rev_relay_var_<name>`: "Variable `<name>` relays one task's output to a single consumer — reference the output directly (`<- \"Stage\".\"Task\".out` or `vars.$xref('Stage','Task','out')`) and drop the §1.5 row (see § 1.5 declare-vs-xref test)." |

`medium` items DO NOT block Approve. They surface in the Approve summary's `Review items` count (not in the `sdd.md` body) — `medium` requires no acknowledgment but should not be silently buried. The **`high` variants above** (`rev_substitute_app`, and `rev_no_failure_path` at the ≥ 2-connector threshold) gate Approve like any other `high` item: the user can only `Approve despite N high-severity items`.

## Source ledger (provenance)

When Phase 0 defaults or infers a value, record provenance so Phase 1 and downstream auditors can trace it. The ledger has two surfaces:

1. **Inline in `sdd.md`** — italic source attribution after the value: `Manual _(source: user-stated)_`. Omit attribution when the kind is `user-stated`.
2. **Approve summary `Inferred / defaulted` block** — see [phase-0-interview.md § Approve](phase-0-interview.md#approve).

Provenance kinds:

| Kind | When |
|---|---|
| `user-stated` | User wrote the value in chat (no annotation needed). Paraphrased rendition acceptable. |
| `verbatim:"<quote>"` | User wrote the value AND the rendered cell is exactly that phrase (no paraphrase). Strongest grounding signal — preferred over `user-stated` for any customer-named entity (role, stage, domain noun, outcome label). Quote is truncated at 40 chars in the ledger; full quote stays in the agent's working memory for Phase 1. |
| `user-doc:<filename>` | Lifted from a user-shared doc |
| `mechanical:<derivation>` | One-step derivation (e.g., `mechanical:PascalCase→prefix`) |
| `compliance-override:<rule>` | Regulatory constraint forced this value (e.g., `compliance-override:ECOA→action`) |
| `tenant-registry:<resource-name>` | Resolved from the registry cache |
| `connector-priority:<connector>` | Hierarchy tier 4 selected `execute-connector-activity` over `api-workflow` |
| `inferred-default:<reason>` | Defaulted because no source matched (used sparingly — most defaults should be Ask) |

A non-`user-stated` and non-`verbatim` field without provenance is a validation error. Approve blocks until annotated.

## Finalization

Before Approve atomic-renames `sdd.draft.md` → `sdd.md`, Phase 0 runs these checks in order. Failure at any step blocks the rename; the draft is preserved.

1. **Schema check.** Every task `type` ∈ 9-value enum (Rule 16). Every WHEN ↔ Marks-complete pair valid per sdd-template Key Rule 4:
   - Case-exit `Yes` + `selected-stage-*` → error
   - Stage-exit `Yes` + `selected-tasks-completed` → error
2. **Render-contract check.** Every required cell in §Case content rules, §Stage content rules, §Task content rules has a concrete value (no banned `—` / `<UNRESOLVED>`).
3. **Decision-task button check.** Every `action` task with `is_decision: Yes` has ≥ 2 buttons; every button's `Maps To` LHS references a declared §1.5 variable (by `Name`) or `taskOutcome`.
4. **Recipient encoding check.** Every `action` task recipient uses one of the five typed prefixes (`Email:` / `User:` / `UserGroup:` / `Role:` / `Expression:`) — no bare strings.
5. **Connector-id check.** Every `wait-for-connector` / `execute-connector-activity` **task** has concrete `Connection ID` AND `Activity Type ID`. Every `wait-for-connector` **condition rule** (in any scope — stage-entry / stage-exit / case-exit / task-entry) has a `Connector Rule Detail` block resolving to a concrete `Connector Key` AND `Event Operation` (and `Connection ID` when not a tenant-default). Missing identity → paired `high`-severity review item.
6. **Variable-lineage check.** Every variable closes (producer before consumer; no orphans).
7. **Override-conflict check.** No compliance trigger phrase paired with a non-`action` task type without explicit user reconciliation in the transcript.
8. **Alt-disposition coverage.** If ≥ 1 secondary stage exists, Section 1.4a is non-empty OR a `high`-severity review item is open.
9. **Review-items high-severity acknowledgment.** Approve adds the explicit follow-up when `high` items exist.
10. **Source-ledger check.** Every non-`user-stated` and non-`verbatim` field has provenance.
11. **File-In-arg caller-obligation surfacing.** When ≥ 1 §1.5 row has `Category: In` AND `Type: file`, the Approve summary MUST include a `Caller obligation` block:

    ```
    Caller obligation (file In-arg detected):
      File In-args:  <comma-separated names>
      Programmatic callers must pre-create each JobAttachment via POST /odata/Attachments,
      PUT bytes to the returned blob URI, then pass {ID,FullName,MimeType,Metadata} as the
      In-arg value AND include the attachment ID in StartProcessDto.Attachments[].
      Maestro Studio Web's "Start case" dialog does this automatically.
    ```

    This is informational, not blocking. But missing it suppresses a known integration gotcha.

12. **Stage-graph connectivity check.** Run the §Logical integrity stage-graph checks (every stage reachable, every stage exits, every Required Stages cell points to existing primary stages, every secondary stage has ≥ 1 entry condition, and each secondary stage's Interrupting flag matches its exit — `return-to-origin` ⟹ `Interrupting: Yes`). Any failure → blocking error.
13. **Domain-fidelity scan.** Run a single pass over every narrative cell (Description, persona name, stage name, task name, button label, app-view purpose). For each customer-named entity surfaced in §Source ledger as `verbatim:"..."`, confirm the rendered cell still uses the verbatim phrase (no synonym drift). Mismatch → list and offer `Re-edit` with the verbatim phrase pre-filled.
14. **Architect's-lens advisory pass.** Run the §Architect's lens checks. Emit `medium` review items for each trigger (the `high` variants — `rev_substitute_app`, and `rev_no_failure_path` at the ≥ 2-connector threshold — emit `high` and gate via the opt-in). `medium` is non-blocking; Approve summary surfaces the count.
15. **Decision-routing closure.** For every `action` task with `is_decision: Yes`, each button's `Maps To` variable+value MUST be consumed by ≥ 1 downstream rule (stage-entry `IF`, task-entry `IF`, stage-exit, or case-exit) OR the button's Behavior MUST declare it terminal (no routing claim). When a button's Behavior names a destination stage / lane ("route to / send to / via the X lane") and no entry condition keys off that variable+value, the branch is dead → **blocking error**. Pair with §Logical integrity step 5 (lane reachability). A fully-orphaned decision variable (produced by a button, read by nothing) on an `is_decision: Yes` task is blocking; the `medium` `rev_orphan_decision` variant in §Architect's lens applies only when the variable IS read but not for branching.
16. **Action-app schema fidelity.** For every `action` task whose HITL Implementation resolves to a concrete deployed app, every declared Input Schema and Output Schema `Field` MUST exist in that app's schema (from `tasks describe`, persisted in `tasks/registry-resolved.json` at Resolve). A declared field absent from the app → `high` review item (`rev_action_schema_<task>`); it cannot bind. One app bound to ≥ 2 tasks trips `rev_substitute_app` (§Architect's lens) **only** when the tasks lack distinct `actionType` dispatch values or declare fields outside the app schema; a code-switched app (distinct `actionType` per task, fields ⊆ app schema) is the sanctioned normalized-action-app pattern and does NOT trip it.
17. **Required-task presence.** Every primary stage whose completion exit uses `required-tasks-completed` MUST contain ≥ 1 task with `Required: Yes`. A `required-tasks-completed` exit over a stage where no task is required is vacuous — the runtime resolves it without gating on real work (and the CLI flags it as `CASE_MGMT_..._NO_REQUIRED_TASK` at `validate`). Catch it at the Approve gate: zero `Required: Yes` tasks in such a stage → blocking error (offer `Re-edit` to mark the stage's terminal/primary task required). Tasks default to `Required: Yes` unless the SDD says otherwise, so this fires only when the author explicitly cleared every task's Required flag.
18. **Resolved-resource presence (standalone replicability).** Every process/agent/rpa/api-workflow task has a concrete `Resolved Resource`; every action has a concrete Action App title in `HITL Implementation`; every case-management task has a concrete `Child Case`. These portable names are never `<UNRESOLVED>`. Each task also has its required type-specific identity + folder pair (`Resource Identity` + `Folder Path`, or `Action App ID` + `Deployment Folder`): a concrete identity requires the exact concrete folder; an unresolved identity permits an unresolved folder and requires a paired `high` review item. Every connector task has `Connection ID` + `Activity Type ID`. Missing portable intent, or unresolved identity with no review item, is a blocking error.
19. **Resolved-resource I/O completeness** (§Resolved-resource I/O completeness; audit-checklist item 9). For every task resolved to a live resource (contract in `tasks/registry-resolved.json`): every **required** declared input is bound (any §Binding cell form, incl. an upstream-output ref — which needs NO §1.5 row) OR `<UNRESOLVED>` + a paired `high` review item (`rev_unbound_input_<task>_<field>`); every Outputs `-> caseVar` row's `Field` exists verbatim in the resolved output contract (a phantom field → `high` `rev_phantom_output_<task>_<field>`). Unbound required input with no review item → blocking error. Step 16 is the `action`-app instance of the output-fidelity direction; this step extends both directions to all runnable/connector types. Tasks whose type-specific identity (`Resource Identity` or `Action App ID`) is `<UNRESOLVED>` (no contract) are skipped.

On pass: atomic rename `sdd.draft.md` → `sdd.md`, print Approve summary (with Inferred / defaulted block + Caller obligation block when applicable + review-items count), run Approve AskUserQuestion.

On fail: list the specific failing checks, return to AskUserQuestion `Re-edit` / `Restart` / `Abort`. On `Re-edit`, fix the cited rows and **re-run only the checks that failed** (plus any whose inputs changed) — not the full suite, and without re-reading the whole document. No Approve until the cited checks pass.

## Anti-patterns

- **Do NOT silently accept a user-proposed type when a compliance trigger phrase is in the transcript.** Tier 2 of the authority hierarchy overrides user preference; Ask before recording.
- **Do NOT ship `sdd.md` with a banned `—` or `<UNRESOLVED>` on a render-required field.** Emit a placeholder + review item, or Ask.
- **Do NOT pair `Marks Stage Complete: Yes` with `selected-tasks-completed` or `Marks Case Complete: Yes` with `selected-stage-*`.** Both are schema-pairing errors (Key Rule 4).
- **Do NOT emit an `action` task without typed recipient prefix.** Bare strings (`"the underwriter"`) force Phase 1 to guess.
- **Do NOT emit a decision `action` task with fewer than 2 buttons.** `is_decision: Yes` requires ≥ 2 buttons; downgrade to `is_decision: No` if the task does not fork the case path.
- **Do NOT emit a `wait-for-timer` task with `<UNRESOLVED>` duration.** Timer cannot fire — block Approve.
- **Do NOT emit SLA cells on `process` / `agent` / `rpa` / `api-workflow` / timer / connector / `case-management` tasks.** SLA supports case, stage, and `action` tasks ONLY (sdd-template Key Rule 1).
- **Do NOT emit `external-agent`, `external-workflow`, `document-extraction`, `flow-process`, `connector-activity`, `connector-trigger`, or `wait-for-event` as task types.** This skill generates 9 of the CLI's 10 types (Rule 16). `external-agent`, `external-workflow`, `document-extraction`, and `flow-process` are **not supported yet**. The rest are not CLI task types at all.
- **Do NOT author task inputs as bare field-name lists** (`**Inputs:** a, b, c`). Use the `Field | Type | Binding` table — bare lists force Phase 1 into name-match inference.
- **Do NOT close variable lineage by guessing producers.** If no producer fires before a consumer AND the §1.5 row has no `Default`, that is an open-lineage error — surface it. Never silently retag the row's `Category` to `In` or invent a `Default` to suppress the failure.
- **Do NOT populate `sourceTriggers` on `Out` rows.** PR 860's Phase 2 validator rejects `Out` + non-empty `sourceTriggers` (direction mismatch). An `In` row MAY carry a single `T<N>` to bind to a specific trigger (blank = primary), but its `sourceFields` MUST stay empty and a CSV is forbidden. For trigger-payload extraction, use `Category: Variable` (see §1.5 and [sdd-template-examples.md](../assets/templates/sdd-template-examples.md) Use Case 2).
- **Do NOT use bare `sourceFields` paths when `sourceTriggers` is CSV.** Multi-trigger rows MUST use keyed `T<N>: <path>; T<M>: <path>` format with one entry per T-number. Mismatch is a Phase 2 validator error.
- **Do NOT mix `->` and `=` operators on the same target case variable within one task's Outputs.** Each target appears in at most one row per task — no double-binding.
- **Do NOT leak skill-internal vocabulary into SDD narrative cells.** `Pattern C`, `bridge`, `companion`, `io-binding`, `dispatcher`, `Finding #N`, `aliased into`, `auto-mint`, etc. belong inside skill references — not in `sdd.md` Descriptions or notes. See [sdd-template.md § Output Rules](../assets/templates/sdd-template.md).
- **Do NOT downgrade a `high` review item to `medium` to pass the Approve gate.** The severity ladder is mechanical; downgrade only when the underlying issue actually resolves.
- **Do NOT omit provenance on inferred values.** Silent inference reaches Phase 1 under Rule 2 trust — provenance is the audit trail.
- **Do NOT alias a task output into an unrelated existing variable to satisfy lineage.** If a task produces a new datum, declare a §1.5 variable for it. Aliasing (`complianceStatus -> titleReviewStatus` with no `complianceStatus` row) closes lineage mechanically but corrupts meaning — see §Variable lineage closure output-naming rule.
- **Do NOT emit a decision `action` button whose Behavior names a destination lane the case graph cannot reach.** Every routing button's variable+value must be keyed by a downstream entry / exit condition (§Finalization step 15, §Logical integrity step 5). A button that "routes to the X lane" while X is entered only by an external connector event is a dead branch.
- **Do NOT author an `action` Input Schema field the resolved app does not expose.** Fields outside the app's `tasks describe` schema cannot bind (§Finalization step 16). Reusing one app across many tasks is correct **when it is code-switched** (distinct `actionType` per task, fields ⊆ the app schema — the normalized-action-app pattern a full case relies on); it is the substitute anti-pattern (`rev_substitute_app`) only without a distinct `actionType` or with non-bindable fields.
- **Do NOT leave a resolved resource's required input unbound, and do NOT bind an output the resource never emits.** Once a task resolves to a live resource, every required declared input needs a `Binding` row (or `<UNRESOLVED>` + `high` review item) and every `-> caseVar` extract `Field` must exist in the resolved contract (§Resolved-resource I/O completeness, §Finalization step 19). A silently-missing required input faults the job at runtime.
- **Do NOT declare a §1.5 Case Variable for an input that is just an upstream task's output.** Reference it directly — whole-value `<- "Stage"."Task".out` or in-expression `vars.$xref('Stage','Task','out')`. The emitting task is its own producer; a §1.5 row is only for renaming, custom `Default` / `Type`, or case-level state (§Variable lineage closure → Task-output direct reference).
