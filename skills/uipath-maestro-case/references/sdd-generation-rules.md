# SDD Generation Rules

Content-quality contract for Phase 0's `sdd.md`. The interview in [phase-0-interview.md](phase-0-interview.md) owns the **conversation flow** (Listen / Sketch / Ask / Resolve / Approve). This file owns the **content rules** every generated `sdd.md` must satisfy before Approve renames the draft.

Phase 1 trusts `sdd.md` as written (SKILL.md Rule 2). These rules make that trust safe.

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
| SLA Type | conditional | `Calendar` / `BusinessHours` | Default `BusinessHours` when Case SLA set. |

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

≥ 1 trigger required. One row per triggering event.

| Field | Required? | Value |
|---|---|---|
| Type | yes | `Manual` / `Timer` / `Connector Event` |
| Source | conditional | Connector key for `Connector Event`; schedule expression for `Timer`; `—` for `Manual` |
| Config | conditional | Concrete configuration block (connector trigger config / cron / `—`). `Connector Event` MUST have concrete `Config`. |
| Initial Mapping | optional | Variable bindings populated from the trigger payload at case start |

Unresolved `Connector Event` config (`connectionId` / `activityTypeId` missing) → `high`-severity review item.

### 1.3a Trigger Filter (conditional)

Renders ONLY when ≥1 trigger declares a filter. AND/OR tree.

Operators (case-sensitive PascalCase): `Equals`, `NotEquals`, `Contains`, `NotContains`, `StartsWith`, `EndsWith`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `In`, `NotIn`, `IsNull`, `IsNotNull`.

| Field | Operator | Value | Literal? |
|---|---|---|---|
| `<payload field>` | `<operator>` | `<value>` | `Yes` / `No` |

Nested `{op, clauses}` groups flatten in the rendered table. Avoid `Literal: No` for unverified runtime expressions — it forces Phase 1 into JMESPath fallback (lossy). Prefer literal values or open a review item.

### 1.4 Case Completion Conditions

≥ 1 row required. `Marks Case Complete: Yes`.

| WHEN | IF | Marks Case Complete | Exit Type |
|---|---|---|---|
| `required-stages-completed` / `wait-for-connector` | optional `conditionExpression` | `Yes` | `exit-only` |

**Allowed WHEN:** `required-stages-completed`, `wait-for-connector`.
**Forbidden WHEN:** `selected-stage-completed`, `selected-stage-exited` (sdd-template Key Rule 4 — `Yes` + `selected-stage-*` is a schema-pairing error → block Approve).

### 1.4a Case Exit Conditions (alternate disposition)

Optional. `Marks Case Complete: No`. Used for ExceptionStage terminals (Withdrawn / Rejected / Cancelled).

| WHEN | IF | Marks Case Complete | Exit Type |
|---|---|---|---|
| `selected-stage-completed("<Stage Name>")` / `selected-stage-exited("<Stage Name>")` / `wait-for-connector` | optional | `No` | `exit-only` / `wait-for-user` |

**When the case has ≥ 1 ExceptionStage AND Section 1.4a is empty** → emit a `high`-severity review item (`Alt-disposition exits missing`). The case cannot exit non-happy paths cleanly.

### 1.5 Case Variables

Every variable used anywhere in the plan (task inputs/outputs, conditions, mappings, exit rules) appears in this table.

| Column | Required? | Notes |
|---|---|---|
| Variable | yes | camelCase, no role suffix |
| Category | yes | `In` / `Out` / `Variable` — NEVER `—` |
| Type | yes | Platform enum from [case-schema.md § Variables](case-schema.md): `string`, `boolean`, `number`, `entity`, `array`, `object`. Use `string` for JSON-shaped values; never emit `json` or `jsonSchema`. |
| Default | optional | Concrete default or `—` |
| Description | yes | One-line meaning |
| Produced By | yes | `trigger`, `system`, or `"<Stage Name>"."<Task Name>".<outputName>`. NEVER blank. |
| Consumed By | yes | Every consumer task + `case-exit-condition` when used in exit rules. List ALL — never abbreviate. |

Lineage closure rules in §Variable lineage closure.

## Stage content rules

Defines what each stage in Section 2 must contain. Same rules apply to primary stages (`Stage`) and exception stages (`ExceptionStage`) unless noted.

### Stage heading

- Primary: `` ### Stage {N}: {Stage Name} (`{stage_id}`) `` — N is 1-based sequence number
- Exception: `` ### Exception Stage: {Stage Name} (`{stage_id}`) ``

The trailing `` `{stage_id}` `` (e.g., `` `stage-intake` ``) MUST appear so readers can grep cross-references. Anywhere a stage is referenced by name in a table cell (`Selected Stage`, `Required Stages`, `Exit-To Stage`, case-exit selected stage), append the stage id in code-formatted parens.

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

| WHEN | IF |
|---|---|
| `case-entered` (root only) / `selected-stage-completed("<Stage>")` / `selected-stage-exited("<Stage>")` / `wait-for-connector` / `adhoc` | optional `conditionExpression` |

### Stage Completion Conditions table (`Marks Stage Complete: Yes`)

≥ 1 row required.

| WHEN | IF | Marks Stage Complete | Exit Type |
|---|---|---|---|
| `required-tasks-completed` / `wait-for-connector` | optional | `Yes` | `exit-only` / `return-to-origin` |

**Allowed WHEN:** `required-tasks-completed`, `wait-for-connector`.
**Forbidden WHEN:** `selected-tasks-completed` (Key Rule 4 — `Yes` + `selected-tasks-completed` is a schema-pairing error → block Approve).

### Stage Exit Conditions table (`Marks Stage Complete: No`)

Optional. Used for early hand-offs / routing.

| WHEN | IF | Marks Stage Complete | Exit Type | Exit-To Stage |
|---|---|---|---|---|
| `selected-tasks-completed("<Task>")` / `wait-for-connector` | optional | `No` | `exit-only` / `wait-for-user` | `` <Target Stage> (`<stage_id>`) `` |

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

| WHEN | IF |
|---|---|
| {rule} | {conditionExpression or "—"} |
```

| Rule | When to use |
|---|---|
| `current-stage-entered` | First task in stage (REQUIRED; emit explicitly, never imply). Connector tasks auto-inject this — render it first even when explicit rows follow. |
| `selected-tasks-completed("<Task>")` | Sibling-gated task (e.g., after upstream task in same stage). Multiple tasks comma-separated inside the parens. |
| `wait-for-connector` | Async connector callback. Pair with `conditionExpression` for inbound payload shape. |
| `adhoc` | Manual fire from the case app. Optional gating expression. |
| `runs-sequentially` | Tasks in a lane that should run top-to-bottom in declaration order. |

Multiple entry conditions render as multiple rows (DNF outer-OR). Connector tasks always render auto-injected `current-stage-entered` first.

### `action` task — required cells

| Cell | Value |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>` (v1) OR `JSON Schema` (v2). Never paraphrase, never `—`. |
| Action App ID | v1 only — concrete deployment id from `action-apps-index.json` |
| Deployment Folder | v1 only — `deploymentFolder.fullyQualifiedName` |
| Recipient | Typed prefix (see table below). NEVER a bare string. |
| Priority | `Low` / `Medium` / `High` / `Critical` |
| Task Title | One-line user-visible question/instruction (REQUIRED — Action Center displays it) |
| Labels | Comma-separated when set; otherwise `—` |
| Run Only Once | `Yes` / `No` |
| Required | `Yes` / `No` |
| Input Schema | Table: `Field | Type | Binding | Required` |
| Output Schema | Table: `Field | Type | Binding` (arrow form `-> =vars.<id>`) |
| Buttons | Table only when `is_decision: Yes`: `Button | Maps To | Behavior` |

**HITL Implementation modes:**

| Version | Pick when | Cells required |
|---|---|---|
| v1 | Tenant has a deployed Custom Action App | Action App ID + Deployment Folder |
| v2 | No deployed Action App; simple structured form | Render Context table for form fields; omit App ID / Folder |

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

`Maps To` LHS MUST reference a declared case variable from Section 1.5 OR the conventional `taskOutcome` handle. NEVER an undeclared identifier.

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
| Inputs | Table: `Field | Type | Binding` — `Field` MUST match IS activity schema verbatim |
| Outputs | Table: `Field | Type | Binding` (arrow form) |

**Auto-injected entry condition.** These two task types auto-receive `current-stage-entered` at consumer-side creation. Render explicitly as the first row; explicit additional rules APPEND, never replace.

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
| Inputs | Table: `Variable | Type | Binding` — `Variable` MUST match the runnable's declared In argument name verbatim |
| Outputs | Table: `Variable | Type | Binding` (arrow form) — `Variable` MUST match the runnable's declared Out argument name verbatim |

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

### Binding cell — allowed expressions

Every `Binding` cell carries one of (case-sensitive):

| Form | Meaning |
|---|---|
| `<literal>` | Plain string / number / boolean |
| `=vars.<id>` | Case variable from Section 1.5 (`<id>` must match a Section 1.5 row's `Variable` cell) |
| `=bindings.<id>` | Registered resource (action app, process, connection) |
| `=metadata.<key>` | Case metadata |
| `=trigger.<field>` | Trigger payload field |
| `=js:<expr>` | Inline JavaScript (REQUIRED when operators are involved) |
| `=jsonString:<json>` | JSON literal as string (used for `essentialConfiguration` carry-through) |
| `=datafabric.<path>` | Data Fabric reference |
| `=orchestrator.JobAttachments` | File slot |
| `=response` / `=result` / `=Error` | Conventional handles for connector / agent / process responses |
| `"<Stage Name>"."<Task Name>".<outputName>` | Cross-task output reference — Phase 1 resolves to `=vars.<id>` at build time |

Output `Binding` cells use the `-> <case variable>` arrow form.

**Bare field-name lists** (`**Inputs:** loanId, borrowerLegalEntity`) are FORBIDDEN. They force Phase 1 into name-match inference — the exact failure mode the table form prevents.

## Variable lineage closure

Every variable referenced in `sdd.md` must close — there must be a producer earlier in stage order, or it must be `In`-scoped (set by trigger or parent case).

For each variable in Section 1.5:

- **Produced By** — `trigger` (set by trigger payload), `system` (set by case framework), or the producing task as `"<Stage Name>"."<Task Name>".<outputName>`.
- **Consumed By** — every task that reads the variable, plus `case-exit-condition` when used in case exit rules. List ALL — never abbreviate or use "etc."

**Closure rule.** For every `Consumed By` entry, the producer must fire before the consumer in stage order. A consumer reading a variable whose producer is in a later stage is an open-lineage error and blocks Approve.

**Audit checklist** (run before Approve renames the draft):

1. Every variable used in a task input has an entry in Section 1.5.
2. Every variable used in an exit condition or stage entry rule has `Consumed By: case-exit-condition` (or the consuming stage's entry).
3. Every variable has a non-blank `Produced By` value.
4. Producer's stage index < min(Consumer's stage indices). If producer and consumer are in the same stage, producer's task index < consumer's task index.

Any failure → Phase 0 cannot Approve. Surface in edit-validation errors. AskUserQuestion `Re-edit` / `Restart` / `Abort`.

## Review items

A review item is a structured gap escalation. Phase 0 emits one whenever a field could not be fully resolved but Phase 1 needs the context. Review items appear in `sdd.md` Section 5 (Implementation Readiness) AND mirror into `tasks/registry-resolved.json` under the matching task's `review_items[]` array.

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

## Source ledger (provenance)

When Phase 0 defaults or infers a value, record provenance so Phase 1 and downstream auditors can trace it. The ledger has two surfaces:

1. **Inline in `sdd.md`** — italic source attribution after the value: `Manual _(source: user-stated)_`. Omit attribution when the kind is `user-stated`.
2. **Approve summary `Inferred / defaulted` block** — see [phase-0-interview.md § Approve](phase-0-interview.md#approve).

Provenance kinds:

| Kind | When |
|---|---|
| `user-stated` | User wrote the value verbatim in chat (no annotation needed) |
| `user-doc:<filename>` | Lifted from a user-shared doc |
| `mechanical:<derivation>` | One-step derivation (e.g., `mechanical:PascalCase→prefix`) |
| `compliance-override:<rule>` | Regulatory constraint forced this value (e.g., `compliance-override:ECOA→action`) |
| `tenant-registry:<resource-name>` | Resolved from the registry cache |
| `connector-priority:<connector>` | Hierarchy tier 4 selected `execute-connector-activity` over `api-workflow` |
| `inferred-default:<reason>` | Defaulted because no source matched (used sparingly — most defaults should be Ask) |

A non-`user-stated` field without provenance is a validation error. Approve blocks until annotated.

## Finalization

Before Approve atomic-renames `sdd.draft.md` → `sdd.md`, Phase 0 runs these checks in order. Failure at any step blocks the rename; the draft is preserved.

1. **Schema check.** Every task `type` ∈ 9-value enum (Rule 16). Every WHEN ↔ Marks-complete pair valid per sdd-template Key Rule 4:
   - Case-exit `Yes` + `selected-stage-*` → error
   - Stage-exit `Yes` + `selected-tasks-completed` → error
2. **Render-contract check.** Every required cell in §Case content rules, §Stage content rules, §Task content rules has a concrete value (no banned `—` / `<UNRESOLVED>`).
3. **Decision-task button check.** Every `action` task with `is_decision: Yes` has ≥ 2 buttons; every button's `Maps To` LHS references a declared Section 1.5 variable or `taskOutcome`.
4. **Recipient encoding check.** Every `action` task recipient uses one of the five typed prefixes (`Email:` / `User:` / `UserGroup:` / `Role:` / `Expression:`) — no bare strings.
5. **Connector-id check.** Every `wait-for-connector` / `execute-connector-activity` task has concrete `Connection ID` AND `Activity Type ID`, OR a paired `high`-severity review item.
6. **Variable-lineage check.** Every variable closes (producer before consumer; no orphans).
7. **Override-conflict check.** No compliance trigger phrase paired with a non-`action` task type without explicit user reconciliation in the transcript.
8. **Alt-disposition coverage.** If ≥ 1 ExceptionStage exists, Section 1.4a is non-empty OR a `high`-severity review item is open.
9. **Review-items high-severity acknowledgment.** Approve adds the explicit follow-up when `high` items exist.
10. **Source-ledger check.** Every non-`user-stated` field has provenance.

On pass: atomic rename `sdd.draft.md` → `sdd.md`, print Approve summary (with Inferred / defaulted block + review-items count), run Approve AskUserQuestion.

On fail: list specific errors, return to AskUserQuestion `Re-edit` / `Restart` / `Abort`. No Approve until all checks pass.

## Anti-patterns

- **Do NOT silently accept a user-proposed type when a compliance trigger phrase is in the transcript.** Tier 2 of the authority hierarchy overrides user preference; Ask before recording.
- **Do NOT ship `sdd.md` with a banned `—` or `<UNRESOLVED>` on a render-required field.** Emit a placeholder + review item, or Ask.
- **Do NOT pair `Marks Stage Complete: Yes` with `selected-tasks-completed` or `Marks Case Complete: Yes` with `selected-stage-*`.** Both are schema-pairing errors (Key Rule 4).
- **Do NOT emit an `action` task without typed recipient prefix.** Bare strings (`"the underwriter"`) force Phase 1 to guess.
- **Do NOT emit a decision `action` task with fewer than 2 buttons.** `is_decision: Yes` requires ≥ 2 buttons; downgrade to `is_decision: No` if the task does not fork the case path.
- **Do NOT emit a `wait-for-timer` task with `<UNRESOLVED>` duration.** Timer cannot fire — block Approve.
- **Do NOT emit SLA cells on `process` / `agent` / `rpa` / `api-workflow` / timer / connector / `case-management` tasks.** SLA supports case, stage, and `action` tasks ONLY (sdd-template Key Rule 1).
- **Do NOT invent `external-agent`, `connector-activity`, `connector-trigger`, or `wait-for-event` as task types.** Closed enum of 9 (Rule 16).
- **Do NOT author task inputs as bare field-name lists** (`**Inputs:** a, b, c`). Use the `Field | Type | Binding` table — bare lists force Phase 1 into name-match inference.
- **Do NOT close variable lineage by guessing producers.** If no producer fires before a consumer, that is an error — surface it, do not silently mark the variable `In`.
- **Do NOT downgrade a `high` review item to `medium` to pass the Approve gate.** The severity ladder is mechanical; downgrade only when the underlying issue actually resolves.
- **Do NOT omit provenance on inferred values.** Silent inference reaches Phase 1 under Rule 2 trust — provenance is the audit trail.
