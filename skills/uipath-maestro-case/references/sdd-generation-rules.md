# SDD Generation Rules

Content-quality contract for Phase 0's `sdd.md`. The interview in [phase-0-interview.md](phase-0-interview.md) owns the **conversation flow** (Listen / Sketch / Ask / Resolve / Approve). This file owns the **content rules** every generated `sdd.md` must satisfy before Approve renames the draft.

Phase 1 trusts `sdd.md` as written (SKILL.md Rule 2). These rules make that trust safe.

## Mental model: stages, secondary stages, tasks

Reason the case shape from the process the user describes — **do not reach for the template first.** The template renders a shape you already decided; it does not decide it for you. Build the model in this order: stages → tasks → types → pull exceptions out. Each concept below is a question to ask of the user's process, not a slot to fill.

**Stage** — a phase the case works through: a bounded milestone with an *entry* (when it starts), *tasks* (the work done inside it), and a *completion/exit* (when it's done and where the case goes next). Stages are the backbone; they run in sequence (or parallel) wired by **edges**. Derive one stage per milestone the user names ("intake", "underwriting", "funding"). Ask: *what is the case working toward right now, and what makes that done?* A stage that "marks the case complete" is on the main flow (`isRequired: true`).

**Secondary stage** (a.k.a. exception stage — `case-management:ExceptionStage`) — work that is **not a fixed step on the line**: it can fire at many points and only under a condition. Errors, escalations, rejections, rework loops, cancellations. Three rules define it, all CLI-enforced:

- **No edges** — never wired in or out by an edge (validator: `CASE_MGMT_SECONDARY_STAGE_EDGES`). It is detached from the flow graph.
- **Entered by its own condition**, evaluated continuously against case state — often *interrupting* (pauses active stages when it fires). It is reached because a condition became true, not because the case traversed an edge.
- **Exits via `return-to-origin`** — routes the case back to the stage it interrupted, through the exit rule, not a new edge.

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
- **Secondary (exception) stage** uses **stage-entry + stage-exit rules only, never edges.** Its entry rule is typically *interrupting* (`isInterrupting: true`); its exit uses `return-to-origin` to rejoin the flow it left.
- **First task in a stage** must carry `current-stage-entered` (emit it explicitly). `wait-for-connector` makes a gate pause for an inbound connector callback — its `conditionExpression` gates on **case state** only (no `event` payload; in-rule extract-then-gate is unsupported at runtime — gate a downstream condition instead); `adhoc` lets a *task* fire manually from the case app (task-entry only — never a stage-entry rule); `runs-sequentially` chains tasks in a lane.
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
- **"goes back for remediation" → secondary stage.** Remediation fires only on a condition (compliance failed) and routes back — model it as an exception stage (condition-entered, `return-to-origin`), **not** a sixth inline stage with edges.
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
| `case-management` | the step **launches / coordinates a child case** | Does this spin up a sub-case? (any child case trips the Phase 0 threshold → soft-redirect) |

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

**Allowed `—`** (cells the user did not touch and Phase 1 can default safely): case-level Description, variable defaults, persona scope notes, app-view detail, exception-stage description, optional `IF` conditionExpressions, business calendars on timers.

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
| Event | The operation in business terms (`Calendar created`, `Email received`). Append a filter clause when the user wants filtering (`Email received in Inbox; filter: subject contains "URGENT"`). Append a required event-param ONLY when the user supplies it (`Email received in folder "<folder name>"`). |
| Timer | Cycle or duration (`every 24 hours`, `daily at 09:00 UTC`). |
| Manual | `N/A` or omit. |

**Forbidden in Configuration** (skill resolves these at planning time — not author surface):

- CLI enum values like `CALENDAR_CREATED`, `createdRecord`.
- Default modes (`polling` vs `webhook`).
- Meta notes like `No required event parameters` or `No user filter` (absence IS the default).
- Connector activity slug, HTTP method, spec-discovered detail.

> Variable mapping (which trigger payload field populates which case variable) is declared in **§1.5 Case Variables** via the `sourceTriggers` / `sourceFields` columns — NOT in this table. The Triggers table only identifies and configures each trigger; payload extraction is owned by Case Variables.

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

Optional. `Marks Case Complete: No`. Used for ExceptionStage terminals (Withdrawn / Rejected / Cancelled).

| WHEN | IF | Marks Case Complete | Exit Type | Display Name |
|---|---|---|---|---|
| `selected-stage-completed("<Stage Name>")` / `selected-stage-exited("<Stage Name>")` / `wait-for-connector` | optional | `No` | `exit-only` / `wait-for-user` | optional |

**When the case has ≥ 1 ExceptionStage AND Section 1.4a is empty** → emit a `high`-severity review item (`Alt-disposition exits missing`). The case cannot exit non-happy paths cleanly.

### 1.5 Case Variables

Every variable used anywhere in the plan (task inputs / outputs, conditions, mappings, exit rules) appears in this table. Authoring is **declarative** — the row's `Category` + `sourceTriggers` + `sourceFields` columns drive build-time classification. Inference from prose or other columns is no longer supported.

| Column | Required? | Notes |
|---|---|---|
| Name | yes | camelCase, no role suffix |
| Category | yes | `In` / `Out` / `Variable` — NEVER `—`. Drives the [`global-vars` plugin's](plugins/variables/global-vars/impl-json.md) pattern shape. |
| Type | yes | Platform enum from [case-schema.md § Variables](case-schema.md): `string`, `integer`, `float`, `double`, `boolean`, `datetime`, `date`, `jsonSchema`, `file`. **`file`** is a JobAttachment record (`{ID, FullName, MimeType, Metadata}`) — see `[sdd-template-examples.md](../assets/templates/sdd-template-examples.md)` Use Cases 9–11 for caller-pre-upload, connector-download, and multipart-send patterns. File-typed In-args carry an implicit caller obligation (see §1.5 In semantics + Approve summary reminder). Use `string` for JSON-shaped values; never emit `json` or `jsonSchema`. |
| sourceTriggers | conditional | T-number(s) — single `T<N>` or comma-separated CSV (`T02, T03`) when multiple triggers feed the same Variable. Empty for pure state, `In`, `Out`. |
| sourceFields | conditional | Single bare payload path when one trigger; **keyed format** `T<N>: <path>; T<M>: <path>` when `sourceTriggers` is CSV. Dot-paths only — no array indexing in v1. |
| Default | optional | Concrete default or empty. |
| Description | yes | One-line meaning. |

**Category semantics** (canonical definition in [`global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md)):

- **`In`** — caller-supplied case argument (manual trigger via API) OR `Default`-initialized (event / timer triggers, which have no caller). `sourceTriggers` MUST be empty. For event-payload-extraction, use `Variable` + `sourceTriggers` + `sourceFields` instead (see Use Case 2 in [sdd-template-examples.md](../assets/templates/sdd-template-examples.md)). **`In` of `Type: file`** — programmatic caller must pre-create a JobAttachment (`POST /odata/Attachments` then `PUT` bytes) and pass `{ID, FullName, MimeType, Metadata}` plus `StartProcessDto.Attachments[]`. Maestro Studio Web's "Start case" dialog does this automatically; non-Studio callers do it themselves. Surface this obligation in the Approve summary whenever any file-In-arg exists; see §Finalization step 11.
- **`Out`** — case argument returned to caller. Value comes from a producer (a task's Outputs row that targets this Name via `-> {name}` or `{name} = {expr}`) OR from `Default` when no producer fires. `sourceTriggers` MUST be empty (direction mismatch: trigger → case is forbidden for `Out`).
- **`Variable`** — case-internal state. Populated by one trigger's payload (`T<N>` + single path), multiple triggers sharing the same slot (CSV + keyed `T<N>: <path>` format), a task's Outputs row, or `Default` only.

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

Defines what each stage in Section 2 must contain. Same rules apply to primary stages (`Stage`) and exception stages (`ExceptionStage`) unless noted.

### Stage heading

- Primary: `` ### Stage {N}: {Stage Name} (`{stage_id}`) `` — N is 1-based sequence number
- Exception: `` ### Exception Stage: {Stage Name} (`{stage_id}`) ``

The trailing `` `{stage_id}` `` (e.g., `` `stage-intake` ``) MUST appear so readers can grep cross-references. Anywhere a stage is referenced by name in a table cell (`Selected Stage`, `Required Stages`, case-exit selected stage), append the stage id in code-formatted parens.

### Stage fields (per stage)

| Field | Required? | Value |
|---|---|---|
| Type | yes | `Stage` / `ExceptionStage` |
| Description | yes (primary) / optional (exception) | One prose sentence |
| Required for case completion | yes | `Yes` (primary, default) / `No` (ExceptionStages always `No`) |
| Interrupting | ExceptionStage only | `Yes` / `No` — does this stage interrupt active stages on activation? |
| Stage SLA | yes when stage has SLA | Duration + type, plus escalation table |

### Stage Entry Conditions table

≥ 1 row required.

| WHEN | IF | Display Name |
|---|---|---|
| `case-entered` (root only) / `selected-stage-completed("<Stage>")` / `selected-stage-exited("<Stage>")` / `wait-for-connector` / `user-selected-stage` | optional `conditionExpression` | optional |

### Stage Completion Conditions table (`Marks Stage Complete: Yes`)

Completion (`Yes`) rows and the §Stage Exit Conditions (`No`) rows below render **together** as the single **Stage Exit Conditions** table in `sdd.md` (per [sdd-template.md](../assets/templates/sdd-template.md)). Shared columns, in order: `WHEN | IF | Exit Type | Marks Stage Complete | Display Name`. ≥ 1 completion row required. **Stage-to-stage routing is NOT carried here** — each destination stage declares the link via its own Entry Condition (`selected-stage-completed("This Stage")` / `selected-stage-exited("This Stage")`), so one stage can fan out to N stages.

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
| `current-stage-entered` | First task in stage, or any ungated task (including connector tasks) that should start when its stage is entered (REQUIRED for the first task; emit explicitly, never imply). When a task has multiple entry rows, render this one first. |
| `selected-tasks-completed("<Task>")` | Sibling-gated task (e.g., after upstream task in same stage). Multiple tasks comma-separated inside the parens. |
| `wait-for-connector` | Async connector callback. Pair with `conditionExpression` to gate on **case state** (`vars.X`); the event payload is not accessible (no `event` namespace). **In-rule extract-then-gate (extract + same-rule `=js:vars.caseVar` gate) does NOT work at runtime** — case-backend evaluates the gate before the extract populates the case var. To condition on payload content: extract `response.field -> caseVar` on the connector rule and place the case-state gate on a DOWNSTREAM stage-entry / task-entry condition. |
| `adhoc` | Manual fire from the case app. Optional gating expression. |
| `runs-sequentially` | Tasks in a lane that should run top-to-bottom in declaration order. |

Multiple entry conditions render as multiple rows (DNF outer-OR). When `current-stage-entered` is among them, render it first.

### `action` task — required cells

| Cell | Value |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>`. The deployed app MUST exist in `action-apps-index.json` — inline JSON-Schema authoring is NOT supported by the action plugin (an unresolved app falls back to a Rule-8 placeholder). Never paraphrase, never `—`. |
| Action App ID | Concrete deployment id from `action-apps-index.json` |
| Deployment Folder | `deploymentFolder.fullyQualifiedName` |
| Recipient | Typed prefix (see table below). NEVER a bare string. |
| Priority | `Low` / `Medium` / `High` / `Critical` |
| Task Title | One-line user-visible question/instruction (REQUIRED — Action Center displays it) |
| Labels | Comma-separated when set; otherwise `—` |
| Run Only Once | `Yes` / `No` |
| Required | `Yes` / `No` |
| Input Schema | Table: `Field | Type | Binding | Required` |
| Output Schema | Table: `Field | Type | Binding` (arrow form `-> =vars.<id>`) |
| Buttons | Table only when `is_decision: Yes`: `Button | Maps To | Behavior` |

**HITL Implementation:** the action plugin requires a deployed Action App from `action-apps-index.json` (Action App ID + Deployment Folder). When no matching deployed app exists, the task falls back to a Rule-8 placeholder — the SDD should either use a deployed app, or use a different task type (`process` / `agent` / `api-workflow`) that doesn't require HITL.

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
| Child Case Display Name | Display name of the child case to launch |
| Child Case Identifier | Identifier prefix of the child case |
| Data Passed (parent → child) | Table: `Parent Variable | Child Variable` |
| Wait for Completion | `Yes` / `No` |
| Data Returned (child → parent) | Table: `Child Variable | Parent Variable` — render only when `Wait for Completion: Yes` |

Every `case-management` task triggers the §Soft redirect during Phase 0 threshold check (child cases ≥ 1 is a threshold breach per [phase-0-interview.md § Thresholds](phase-0-interview.md#thresholds)).

### `process` / `agent` / `rpa` / `api-workflow` task — required cells

These four runnable types share a single render block — the SDD surfaces only the binding contract, not the per-type runtime metadata.

| Cell | Value |
|---|---|
| Inputs | Table: `Field | Type | Binding` — `Field` MUST match the runnable's declared In argument name verbatim; `Binding` per §Binding cell |
| Outputs | Table: `Field | Binding / Value` — `Field` MUST match the runnable's declared Out argument name verbatim for `->` rows (or `—` for `=` rows); see §Outputs cell operators |

**Where per-type metadata lives.** The rendered SDD does NOT carry per-type runtime cells (agent prompt, RPA package version, api-workflow endpoint, process release tag). That metadata is resolved during §Resolve in [phase-0-interview.md](phase-0-interview.md#resolve) and persisted in `tasks/registry-resolved.json` under the task's resolution entry (per SKILL.md Rule 9 shape). Phase 1 reads it from there when emitting `caseplan.json`. Mapping:

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
| `=vars.<id>` | Case variable from §1.5 (`<id>` must match a §1.5 row's `Name` cell) |
| `=vars.<id>.<subfield>` | Sub-field of a structured case variable (dot-path) |
| `=bindings.<id>` | Registered resource (action app, process, connection) |
| `=metadata.<key>` | Case metadata |
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

**Self-binding rule.** An Outputs row of the form `caseVar = =vars.caseVar` or `caseVar = =js:vars.caseVar` (LHS and only-referenced-RHS variable are the same `caseVar`) is FORBIDDEN — it's a no-op that masks a missing producer. Phase 0 strips such rows from the draft, narrates the strip, and emits a `high`-severity review item asking the user whether they meant to (a) wire a different producer, (b) drop the row entirely, or (c) initialize via §1.5 `Default`. Computed self-references like `caseVar = =js:(vars.caseVar + 1)` are allowed (incrementers / accumulators) — the RHS expression mutates the value.

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

1. Every variable referenced by any `=vars.<name>` (or `=vars.<name>.<sub>`) anywhere in `sdd.md` (task Inputs, IF columns, exit rules, button `Maps To`, SLA expressions) has a matching §1.5 row whose `Name` equals `<name>`.
2. Every §1.5 row's `Category` is exactly one of `In` / `Out` / `Variable` — never blank, never `—`.
3. **`In` row consistency:** `sourceTriggers` and `sourceFields` are BOTH empty.
4. **`Out` row consistency:** `sourceTriggers` is empty. Closure requires either (a) non-empty `Default`, OR (b) a task Outputs row in the case plan targeting this Name via `-> {name}` or `{name} = {expr}`. (PR 860 added a Phase 2 validator: `Out` + non-empty `sourceTriggers` → reject.)
5. **`Variable` row consistency:** if `sourceTriggers` is non-empty, `sourceFields` MUST have a matching entry for every T-number listed. For CSV `sourceTriggers`, `sourceFields` MUST use keyed `T<N>: <path>; T<M>: <path>` format with one keyed entry per T-number — strict, no defaults. Single-T-number rows use a bare path.
6. **Stage-order closure.** For each consumer of `vars.<caseVar>`, identify producers (trigger-extraction, task Outputs row `->` or `=`). At least one producer's stage index ≤ consumer's stage index AND (same stage) task index < consumer's task index. If no producer exists, the §1.5 row MUST satisfy the `Category: In` or non-empty `Default` escape.
7. **`->` row payload path present.** Every Outputs `-> {caseVar}` row has a non-empty `Field` cell (the runtime path). Every `=` row has `Field` exactly `—`.
8. **Forbidden body vocabulary.** No occurrence in any narrative cell of: `Pattern C`, `bridge`, `companion`, `inputOutputs[]`, `=jsonString:` (outside connector `Operation Configuration` cells), `groupOperator`, `essentialConfiguration` (as prose), `savedFilterTrees`, `dispatcher`, `Phase 2 validator`, `Phase 3 dispatcher`, `Q10 II`, `Finding #N`, `io-binding`, `aliased into / from / back into`, `reassign`, `originalVar`, `auto-mint`. These are skill-internal terms — see [sdd-template.md § Output Rules](../assets/templates/sdd-template.md).

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
| **high** | Blocks Phase 1 / `caseplan.json` build until resolved. | Missing `connectionId` for a resolved connector task; missing `actionAppId` for an `action` task; missing deployed `process` / `agent` / `api-workflow` for a runnable task; unresolved variable lineage; missing trigger config; compliance-override conflict the user has not reconciled. |
| **medium** | Phase 1 can default with a prompt. | Missing SLA escalation recipient (default = owner group); missing variable default; ambiguous recipient (persona name without group resolution). |
| **low** | Cosmetic. | Missing case-level description; missing exception-stage description; stylistic placeholder. |

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

Beyond schema-pairing checks (§Finalization step 1), the case must be a connected graph:

1. **Every stage reachable from a trigger.** Walk forward from each trigger row through Stage Entry Conditions (`case-entered` from root, `selected-stage-completed`, `selected-stage-exited`, `wait-for-connector`). Every primary stage's id must be reached. Unreachable stage → blocking error (orphan stage).
2. **Every stage exits.** Every primary stage must have either (a) a completion row (`Marks Stage Complete: Yes`) whose completion is consumed by a downstream stage's Entry Condition or a case-exit, OR (b) another primary stage whose Entry Condition references it (`selected-stage-completed`/`selected-stage-exited`), OR (c) feed an ExceptionStage. A stage no other stage (or case-exit) keys off → blocking error (terminal-loop stage).
3. **Every case-exit row references a stage that exists.** No dangling `Required Stages` references.
4. **Every `Required Stages` cell in §1.4 names ≥ 1 primary stage with `Required for case completion: Yes`.** Otherwise the case can never complete.
5. **ExceptionStages must have ≥1 entry condition, each DISTINCT, chosen by trigger source.** Map the lane's *trigger* to the rule: a gate decision → `selected-stage-completed` / `selected-stage-exited` (+ `IF` on the decision var); a person launches it → `user-selected-stage`; an external event → `wait-for-connector`. `adhoc` is task-entry only — never a stage entry. Two ExceptionStages whose entry rules are identical (same rule type + `selectedStageId` + `conditionExpression`) fail `validate` (`CASE_MGMT_SECONDARY_STAGE_ENTRY_RULES_DUPLICATE`) — give each a distinct `selectedStageId` or `conditionExpression` guard. Set `Interrupting: Yes` for lanes that fire mid-stage (escalation, comms, withdrawal). Terminal lanes (Rejected / Withdrawn) exit `exit-only` and declare a §1.4a case-exit (`marks-case-complete: false`); return lanes (Escalation / Customer Comms) exit `return-to-origin`.
6. **Classify each secondary stage's `Interrupting` flag by whether it must halt active work.** `Interrupting: Yes` pauses the active stage(s) when the lane fires; `Interrupting: No` runs alongside them in parallel while the main flow continues. Choose the value from the lane's intent — does handling it require stopping the rest of the case, or can it proceed concurrently? Interrupting is independent of whether the lane is terminal or returning. The one hard rule: a `return-to-origin` exit **requires `Interrupting: Yes`** — the case can only return to a stage it interrupted, so a non-interrupting `return-to-origin` lane is incoherent → blocking error.

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
| **Connector-task failure has no exception path** | `execute-connector-activity` / `wait-for-connector` task in a primary stage AND no ExceptionStage entered via `wait-for-connector` failure or task failure rule | `rev_no_failure_path_<task>`: "Connector activity in critical path with no exception-stage cover — runtime failure halts the case." |
| **Multiple parallel single-recipient bottlenecks** | ≥ 2 stages have single-recipient bottleneck check fire AND they fan-in to the same downstream stage | `rev_multi_bottleneck_<stages>`: "Multiple single-recipient bottlenecks gate a downstream stage — fan-in stalls cascade." |

These items DO NOT block Approve. They surface in the Approve summary's `Review items` count (not in the `sdd.md` body). The user can `Approve despite N high-severity items` only — `medium` requires no acknowledgment but should not be silently buried.

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
8. **Alt-disposition coverage.** If ≥ 1 ExceptionStage exists, Section 1.4a is non-empty OR a `high`-severity review item is open.
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

12. **Stage-graph connectivity check.** Run the §Logical integrity stage-graph checks (every stage reachable, every stage exits, every Required Stages cell points to existing primary stages, every ExceptionStage has ≥ 1 entry condition, and each ExceptionStage's Interrupting flag matches its exit — `return-to-origin` ⟹ `Interrupting: Yes`). Any failure → blocking error.
13. **Domain-fidelity scan.** Run a single pass over every narrative cell (Description, persona name, stage name, task name, button label, app-view purpose). For each customer-named entity surfaced in §Source ledger as `verbatim:"..."`, confirm the rendered cell still uses the verbatim phrase (no synonym drift). Mismatch → list and offer `Re-edit` with the verbatim phrase pre-filled.
14. **Architect's-lens advisory pass.** Run the §Architect's lens checks. Emit `medium` review items for each trigger. Non-blocking; Approve summary surfaces the count.

On pass: atomic rename `sdd.draft.md` → `sdd.md`, print Approve summary (with Inferred / defaulted block + Caller obligation block when applicable + review-items count), run Approve AskUserQuestion.

On fail: list specific errors, return to AskUserQuestion `Re-edit` / `Restart` / `Abort`. No Approve until all checks pass.

## Anti-patterns

- **Do NOT silently accept a user-proposed type when a compliance trigger phrase is in the transcript.** Tier 2 of the authority hierarchy overrides user preference; Ask before recording.
- **Do NOT ship `sdd.md` with a banned `—` or `<UNRESOLVED>` on a render-required field.** Emit a placeholder + review item, or Ask.
- **Do NOT pair `Marks Stage Complete: Yes` with `selected-tasks-completed` or `Marks Case Complete: Yes` with `selected-stage-*`.** Both are schema-pairing errors (Key Rule 4).
- **Do NOT emit an `action` task without typed recipient prefix.** Bare strings (`"the underwriter"`) force Phase 1 to guess.
- **Do NOT emit a decision `action` task with fewer than 2 buttons.** `is_decision: Yes` requires ≥ 2 buttons; downgrade to `is_decision: No` if the task does not fork the case path.
- **Do NOT emit a `wait-for-timer` task with `<UNRESOLVED>` duration.** Timer cannot fire — block Approve.
- **Do NOT emit SLA cells on `process` / `agent` / `rpa` / `api-workflow` / timer / connector / `case-management` tasks.** SLA supports case, stage, and `action` tasks ONLY (sdd-template Key Rule 1).
- **Do NOT emit `external-agent`, `connector-activity`, `connector-trigger`, or `wait-for-event` as task types.** This skill generates 9 of the CLI's 10 types (Rule 16); `external-agent` is a real CLI type but has no generation plugin here (model as `api-workflow` / `execute-connector-activity`), and the rest are not CLI task types at all.
- **Do NOT author task inputs as bare field-name lists** (`**Inputs:** a, b, c`). Use the `Field | Type | Binding` table — bare lists force Phase 1 into name-match inference.
- **Do NOT close variable lineage by guessing producers.** If no producer fires before a consumer AND the §1.5 row has no `Default`, that is an open-lineage error — surface it. Never silently retag the row's `Category` to `In` or invent a `Default` to suppress the failure.
- **Do NOT populate `sourceTriggers` on `In` or `Out` rows.** PR 860 added a Phase 2 validator that rejects `Out` + non-empty `sourceTriggers`. For trigger-payload extraction, use `Category: Variable` (see §1.5 and [sdd-template-examples.md](../assets/templates/sdd-template-examples.md) Use Case 2).
- **Do NOT use bare `sourceFields` paths when `sourceTriggers` is CSV.** Multi-trigger rows MUST use keyed `T<N>: <path>; T<M>: <path>` format with one entry per T-number. Mismatch is a Phase 2 validator error.
- **Do NOT mix `->` and `=` operators on the same target case variable within one task's Outputs.** Each target appears in at most one row per task — no double-binding.
- **Do NOT leak skill-internal vocabulary into SDD narrative cells.** `Pattern C`, `bridge`, `companion`, `io-binding`, `dispatcher`, `Finding #N`, `aliased into`, `auto-mint`, etc. belong inside skill references — not in `sdd.md` Descriptions or notes. See [sdd-template.md § Output Rules](../assets/templates/sdd-template.md).
- **Do NOT downgrade a `high` review item to `medium` to pass the Approve gate.** The severity ladder is mechanical; downgrade only when the underlying issue actually resolves.
- **Do NOT omit provenance on inferred values.** Silent inference reaches Phase 1 under Rule 2 trust — provenance is the audit trail.
