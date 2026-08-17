# Task render contracts

Per-task-type render rules for SDD Section 2 task detail blocks. Rule semantics live in
[case-knowledge](../case-knowledge/INDEX.md) — cite, never restate. Slot legality: K-PAIR-1.

## Every task

1. **Entry Condition block** (≥ 1 row; multiple rows = DNF outer-OR; render `current-stage-entered` first when present):

```
**Entry Condition**

| WHEN | IF | Display Name |
|---|---|---|
| {rule} | {conditionExpression or "—"} | optional |
```

2. **Design Rationale** — one concrete sentence: why the type fits the actor/work, why the activation mode fits the timing (sequential: name the ordering evidence; parallel: state independence). Persisted into the matching `tasks.md` T-entries.

## Which WHEN to write (task entry)

| Rule | Write when the source says |
|---|---|
| `current-stage-entered` | Ungated stage-started task. Never alongside event/adhoc/sequential rules (K-SEQ-1). |
| `runs-sequentially` | Ordered run — `then` / `after` / `before` / dependency; EVERY task in the run incl. the first (K-SEQ-2). |
| `selected-tasks-completed("<Task>")` | True fan-in, branch convergence, condition-result routing, non-immediate dependency (K-SEQ-3). Never for simple next-step order; never select `adhoc` or cross-stage tasks. |
| `wait-for-connector` | Async connector callback. `IF` gates case state only (K-EXPR-2). |
| `sla-status-change(...)` | The `start-task` SLA response — task fires on the SLA event, referencing the containing stage's own SLA or `root` (K-SLA-5). Never also `current-stage-entered`. |
| `adhoc` | Manual fire from the Case App; `Required: No` (K-SEQ-4). |

**Activation Mode cell** (per task): `sequential` \| `parallel` \| `parallel-after-predecessor` \| `event-triggered` \| `adhoc`. Sequential runs and parallel-after-predecessor siblings per K-SEQ-2; downstream plans preserve the confirmed mode and rule exactly.

## `action` task — required cells

| Cell | Value |
|---|---|
| HITL Implementation | `Action App: <deploymentTitle>` — concrete intended app name (registry-canonical when resolved, else user-requested). NEVER `<UNRESOLVED>`, never paraphrased. |
| Action App ID | Concrete id from `action-apps-index.json`, or `<UNRESOLVED>` |
| Deployment Folder | `deploymentFolder.fullyQualifiedName`, or `<UNRESOLVED>` when App ID unresolved |
| Recipient | Typed prefix only (K-TYP-7): `Email:` / `User:` / `UserGroup:` / `Role:` / `Expression:` — never bare strings |
| Priority | `Low` / `Medium` / `High` / `Critical` |
| Task Title | One-line user-visible instruction (REQUIRED — Action Center displays it) |
| Labels | CSV or `—` |
| Run Only Once | `Yes` / `No` (re-entry classification: K-SEQ-7) |
| Required | `Yes` / `No` |
| Input Schema | Table `Field \| Type \| Binding \| Required` |
| Output Schema | Table `Field \| Type \| Binding` (arrow form `-> =vars.<id>`) |
| Buttons | Only when `is_decision: Yes`: `Button \| Maps To \| Behavior` |

- **Portable name:** the Action App title is the Phase 0 → Phase 1 lookup key — establish before registry lookup, preserve when unresolved (+ `high` review item + placeholder fallback). Action Apps are never created inline.
- **Schema fidelity:** Input/Output `Field` cells MUST be a subset of the resolved app's schema (`tasks describe --type action`). A user-described field the app lacks → Ask (deploy task-specific app / drop / placeholder), never silently author.
- **Code-switched app (sanctioned):** ONE deployed app across many `action` tasks is correct when each task carries a distinct `actionType` dispatch value AND declared fields ⊆ app schema. Flag `rev_substitute_app` (high) only without distinct `actionType` or with non-bindable fields.
- **Decision flag:** `is_decision: Yes` only when the task forks the case path; requires ≥ 2 buttons. `Maps To` LHS references a declared §1.5 variable Name or `taskOutcome` — never an undeclared identifier. Non-decision actions render no Buttons table.
- No recipient and no role/email known → drop the cell + `high` review item.

## `wait-for-connector` / `execute-connector-activity` task — required cells

| Cell | Source |
|---|---|
| Connector (key), Connection (display name), Connection ID | IS catalog / connection cache |
| Activity Type ID, Service Type, Auth Method, Account / Endpoint | IS typecache / catalog / connection cache |
| Operation / Trigger, Operation Configuration (`=jsonString:<json>` carry-through) | IS catalog / typecache |
| Inputs | `Field \| Type \| Binding` — `Field` matches IS activity schema verbatim |
| Outputs | `Field \| Binding / Value` (K-VAR-5) |

Stage-started connector tasks declare `current-stage-entered` as the first entry row like any other task — no task-type auto-injection. Missing `connectionId` / `activityTypeId` → `high` review item (Phase 1 cannot resolve without them).

## `wait-for-timer` task — required cells

| Cell | Value |
|---|---|
| Timer Type | `timeDuration` (relative) / `dateTime` (absolute) |
| Duration / Until | ISO-8601 duration (`P30D`) or date-time — NEVER `<UNRESOLVED>` (timer cannot fire; block Approve) |
| Business Calendar | Optional; `—` |

## `case-management` task — required cells

| Cell | Value |
|---|---|
| Child Case | Concrete intended child-case `name` — portable lookup key; NEVER `<UNRESOLVED>`, never the parent task's display name |
| Folder Path | Exact `folders[0].fullyQualifiedName`, or `<UNRESOLVED>` when identity unresolved |
| Resource Identity | Selected `entityKey` from `caseManagement-index.json`, or `<UNRESOLVED>` (+ `high` review item, placeholder-only) |
| Child Case Identifier | Child's identifier prefix |
| Data Passed | Table `Parent Variable \| Child Variable` |
| Wait for Completion | `Yes` / `No` |
| Data Returned | Table `Child Variable \| Parent Variable` — only when `Wait for Completion: Yes` |

## `process` / `agent` / `rpa` / `api-workflow` — shared block

| Cell | Required? | Value |
|---|---|---|
| Resolved Resource | yes | Concrete intended resource `name` (registry-canonical when resolved, else user-requested). NEVER `<UNRESOLVED>`. |
| Folder Path | yes | Resolved `folders[0].fullyQualifiedName` (exact resource folder, never a parent), or `<UNRESOLVED>` when identity unresolved |
| Resource Identity | yes | `apiWorkflowId` / `agentId` (+version) / `processOrchestrationId`, or `<UNRESOLVED>` |
| Binding Sub-Type | yes | `Api` (api-workflow) / `Agent` (agent) / `ProcessOrchestration` (process) / `—` (rpa). Omitting it → Studio Web "resource not found". |
| Dispatch / Operation | conditional | Façade selector + value (`requestSource = "RegisterCaseShell"`); `—` for single-purpose. Also an Inputs row (literal binding). |
| Inputs | yes | `Field \| Type \| Binding` — `Field` matches the runnable's In-argument name verbatim |
| Outputs | yes | `Field \| Binding / Value` — `Field` matches the Out-argument name verbatim for `->` rows (K-VAR-5) |

**Deep metadata stays out of the SDD** (K-LEDG-4). Identity source per type:

| Task type | Registry source | Identity field |
|---|---|---|
| `process` | `processOrchestration-index.json` | `processOrchestrationId` |
| `agent` | `agent-index.json` | `agentId` (+ version) |
| `rpa` | `process-index.json` | `processOrchestrationId` |
| `api-workflow` | `api-index.json` | `apiWorkflowId` (+ endpoint) |

Unresolved identity → `high` review item. **No SLA cells on these types** — SLA is case / stage / `action` only (K-SLA-1). Externally-hosted AI agents (CrewAI, Einstein, Databricks…) model as `api-workflow` or `execute-connector-activity` — never `external-agent` (K-TYP-2).

## Binding cell — allowed forms (Inputs)

Semantics: K-EXPR-1; xref doctrine: K-VAR-1.

| Form | Meaning |
|---|---|
| `<literal>` | Plain string / number / boolean |
| `=vars.<id>` / `=vars.<id>.<sub>` | §1.5 variable, or an upstream task output referenced directly (K-VAR-1) |
| `=bindings.<id>` | Registered resource |
| `=metadata.<key>` / `=metadata.ExternalId` | Case metadata / the platform case identity — canonical `caseId` binding, never a `->` extraction |
| `=trigger.<field>` | Trigger payload field |
| `=js:<expr>` | Inline JS (required when operators are involved) |
| `=jsonString:<json>` | JSON-as-string (connector `essentialConfiguration` only) |
| `=datafabric.<path>` / `=orchestrator.JobAttachments` | Data Fabric / file slot |
| `=response` / `=result` / `=Error` | Conventional response handles |
| `"<Stage>"."<Task>".<outputName>` (whole-value `<-`) / `vars.$xref('Stage','Task','out')` | Cross-task output reference → `=vars.<outputId>` at build (K-VAR-1) |

**Bare field-name lists are FORBIDDEN** (`**Inputs:** loanId, borrower`) — they force name-match inference; use the table.

## Outputs rows

Operators, one-writer-per-target, self-binding ban: K-VAR-5 / K-VAR-6. Targets pre-declared per K-VAR-2 (declare-vs-xref).

## Resolved-resource I/O completeness

When a task resolves to a live resource (contract in `tasks/registry-resolved.json`), coverage is two-directional — enforced at build (Phase 1 discovery + Phase 3 io-binding); apply at design only when a contract is already in memory:

1. **Inputs — required coverage:** every required declared input has a non-empty `Binding` row (any form above, incl. an upstream-output xref — which needs NO §1.5 row, K-VAR-1) OR `<UNRESOLVED>` + `high` review item (`rev_unbound_input_<task>_<field>`). Optional inputs may be omitted (user-described but unmapped → `medium`). Never invent a `Default` to suppress an unmapped required input.
2. **Outputs — field fidelity:** every `-> caseVar` row's `Field` (top-level leaf) exists verbatim in the resolved output contract; a phantom field → `high` (`rev_phantom_output_<task>_<field>`). Selective consumption is fine — only referenced outputs need rows.

Tasks with `<UNRESOLVED>` type-specific identity have no contract and are skipped; their portable names stay concrete.

<!-- END: task-render.md -->
