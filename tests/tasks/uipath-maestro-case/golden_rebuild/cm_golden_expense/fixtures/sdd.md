# SDD — Coding-Agent-CM-Golden-Expense-Reporting-Manual-Case

**Case Definition Blueprint.** Expense-reporting case that chains an AI agent, a process orchestration, and an RPA robot to analyze and record an expense request, routes it through human approval with a rework/return-to-origin exception lane, calls an API workflow and a child case, reacts to an inbound HTTP-webhook event, and demonstrates user-selected routing and completion delays. Feature-coverage reference case.

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Stage 1](#stage-1-stage-1) — 3 tasks
   - [Stage 2: Stage 2](#stage-2-stage-2) — 4 tasks
   - [Stage 3: Stage 3](#stage-3-stage-3) — 3 tasks
   - [Secondary Stage: Stage 4 - return to origin](#secondary-stage-stage-4---return-to-origin) — 1 task
   - [Stage 5: Stage 5 - connector entry](#stage-5-stage-5---connector-entry) — 1 task
   - [Stage 6: Stage 6 - to be interrupted](#stage-6-stage-6---to-be-interrupted) — 1 task
   - [Stage 7: Stage 7 - user select](#stage-7-stage-7---user-select) — 1 task
   - [Stage 8: Stage 8 - delay case completion](#stage-8-stage-8---delay-case-completion) — 1 task
3. [Personas & App Views](#section-3-personas--app-views)
4. [Integrations](#section-4-integrations) — IS Connectors, API Workflows, Agents, Processes & RPA, Child Cases

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | Coding-Agent-CM-Golden-Expense-Reporting-Manual-Case |
| Case Description | Manages an employee expense request end to end: automated analysis (agent → process → RPA), manager approval with a rework exception lane, an API-workflow call and a child case, an event-driven stage entered by an inbound HTTP webhook, a user-selected routing stage, and a final completion-delay stage. |
| Case Identifier | Type: constant. Prefix: `EXP` |
| Priority | — |
| Case-Level SLA | 1 h |
| SLA Type | time-based |
| Case App | Enabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` (platform-generated) — every `caseId` task input binds to this |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 70% of SLA duration | Notify: `song.zhao@uipath.com` |
| Breached | 100% of SLA duration | Notify: `song.zhao@uipath.com` |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| `required-stages-completed` | — | Case exited | Yes | Case complete rule |
| `selected-stage-completed("Stage 4 - return to origin")` | — | Case exited | No | Case exit rule 1 |

### Case Variables

> None. This case declares no `In` / `Out` arguments and no case-level state. Every cross-task value flows by direct task-output reference — whole-value `<- "Stage"."Task".output` in an Inputs Binding cell, or `vars.$xref('Stage','Task','output')` inside a `=js:` expression / IF gate. The case's seed input is supplied as a literal on the first task.

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| — | — | — | — | — | — | — |

---

## Section 2: Stages & Tasks

**I/O bindings:** Inputs `Binding` feeds a task input (whole-value `<- "Stage"."Task".out`, a `=js:` expression, or a literal). Outputs `Binding / Value` uses `-> caseVar` (extract) or `caseVar = expr` (set); tasks that only feed downstream via direct reference self-declare their outputs and need no case-variable row.

---

### Stage 1: Stage 1

**Type:** Stage
**Description:** Automated analysis and recording of the expense request: an AI agent normalizes the raw request, a process orchestration processes it, and an RPA robot records the result. Runs as a strict sequential chain.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `case-entered` | — | No | Enter case |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Tasks completed rule |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Analyze Expense Request | agent | Yes | No | — | — |
| 2 | Process Expense Request | process | Yes | No | — | — |
| 3 | Record Expense via RPA | rpa | Yes | No | — | — |

---

##### Task 1.1: Analyze Expense Request

**Type:** agent
**Description:** AI agent that ingests the raw expense-request event and returns a normalized `AgentExpenseRequest` record used by the rest of the case.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** Agent
**Folder Path:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**Resource Identity:** agentId `ccf5793f-54ab-4262-bf44-fcd09a52ed4e` (v1.0.6)
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| expenseRequest | object | `{"CaseId":"ATH-4484403e0059","CaseTitle":"Athena E2E 20260519-015425","EmployeeName":"Athena Tester","EmployeeEmail":"song.zhao@uipath.com","Department":"QA","ExpenseType":1,"Amount":100,"Currency":"USD","Description":"Generated by CMGoldenExpenseReportingTests","SubmittedDate":"2026-05-19T01:54:25Z","Id":"c617a3ad-2553-f111-8ef3-6045bd0a4e20","eventType":"CREATED"}` (literal seed — a sample `CMGoldenExpenseRequest` CREATED event) |

**Outputs:** —

---

##### Task 1.2: Process Expense Request

**Type:** process
**Description:** Process orchestration (agentic BPMN) that processes the normalized expense record and returns `ProcessExpenseRequestOut`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Analyze Expense Request")` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** Agentic Process
**Folder Path:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**Resource Identity:** processOrchestrationId `7d01a11a-c8a3-41b0-b30f-f65c4d7ddbb9` (v1.0.6)
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| ProcessExpenseRequestIn | object | `<- "Stage 1"."Analyze Expense Request".AgentExpenseRequest` |

**Outputs:** —

---

##### Task 1.3: Record Expense via RPA

**Type:** rpa
**Description:** RPA robot that records the processed expense into the legacy system; input is the serialized process output.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Process Expense Request")` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** RPA Workflow
**Folder Path:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**Resource Identity:** processId `0bc08e50-b45a-401c-aec8-a720e1d190e3` (v1.0.6)
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| RPAExpenseRequestIn | string | `=js:JSON.stringify(vars.$xref('Stage 1','Process Expense Request','ProcessExpenseRequestOut'))` |

**Outputs:** —

---

### Stage 2: Stage 2

**Type:** Stage
**Description:** Human approval of the recorded expense with a divergent reject path. A manager reviews via the approval app; an API workflow logs the decision comment; timers demonstrate run-once and ad-hoc entry. A reject decision exits the stage without completing it, opening the rework lane (Stage 4).
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Stage 1")` | — | No | Entry from 'Stage 1' |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Tasks completed rule |
| `selected-tasks-completed("Manager Approval")` | `=js:vars.$xref('Stage 2','Manager Approval','Action') === "reject"` | exit-only | No | Reject Exit1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Manager Approval | action | Yes | No | Reviewer | — |
| 2 | Wait for timer - S2 run once | wait-for-timer | Yes | Yes | — | — |
| 3 | Call Expense API | api-workflow | Yes | No | — | — |
| 4 | Wait for timer - S2 adhoc | wait-for-timer | Yes | No | — | — |

---

##### Task 2.1: Manager Approval

**Type:** action
**Description:** Manager reviews the expense analysis and approves or rejects. Approve continues the case; reject diverts to the rework lane.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: SimpleApprovalApp
**Action App ID:** `d5102769-8bac-4afc-a727-77745c53181e` (actionDefinitionId `7ee15f07-6845-46e9-9388-7eadd30f76b6`, v1.0.6)
**Deployment Folder:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**actionType:** —
**Recipient:** Email: song.zhao@uipath.com
**Priority:** — · **Task Title:** Approve expense · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| Content | String | `` =js:`Hi ${JSON.stringify(vars.$xref('Stage 1','Analyze Expense Request','AgentExpenseRequest'))}` `` | No |
| Comment | String | `=js:JSON.stringify(vars.$xref('Stage 1','Record Expense via RPA','RPAExpenseRequestOut'))` | No |

**Output Schema:** —

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | Action = "approve" | Complete task |
| Reject | Action = "reject" | Complete task; diverts Stage 2 via Reject Exit1 |

---

##### Task 2.2: Wait for timer - S2 run once

**Type:** wait-for-timer
**Description:** Fixed delay demonstrating run-once behavior within the stage.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Timer:** timeDuration
**Value:** PT20S

---

##### Task 2.3: Call Expense API

**Type:** api-workflow
**Description:** API workflow invoked with the approval comment; returns `APIOutput1`.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Manager Approval")` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** API Workflow
**Folder Path:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**Resource Identity:** apiWorkflowId `b9e4f81a-a2c5-4e6d-ab72-a819649c7666` (v1.0.6)
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| APIInput1 | string | `<- "Stage 2"."Manager Approval".Comment` |

**Outputs:** —

---

##### Task 2.4: Wait for timer - S2 adhoc

**Type:** wait-for-timer
**Description:** Ad-hoc delay task — does not auto-start; started on demand from the case app.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `adhoc` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Timer:** timeDuration
**Value:** PT10S

---

### Stage 3: Stage 3

**Type:** Stage
**Description:** External integrations after approval: waits for an inbound HTTP-webhook event, executes a connector activity to list emails, and starts a child case with the approval comment.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Stage 2")` | — | No | Entry from 'Stage 2' |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Tasks completed rule |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Wait for HTTP Webhook | wait-for-connector | Yes | No | — | — |
| 2 | List Emails | execute-connector-activity | Yes | No | — | — |
| 3 | Start Child Case | case-management | Yes | No | — | — |

---

##### Task 3.1: Wait for HTTP Webhook

**Type:** wait-for-connector
**Description:** Pauses the stage until an HTTP-webhook event is received from the bound connection.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Connector:** HTTP Webhook · **Connector Key:** `uipath-http-webhook`
**Connection:** athena-cmgolden-expense-reporting · **Connection ID:** `6a817d24-cbbd-4389-b10d-4329214ffb8d`
**Activity Type ID:** `773cab30-51dc-3eb4-b19d-720dfa151cc9` · **Service Type:** `Intsvc.WaitForEvent`
**Auth Method:** — (AuthenticateAfterDeployment)
**Account / Endpoint:** —
**Operation:** Event (objectName `HTTP_WEBHOOK`, operation `GENERIC`, eventMode `webhooks`)
**Trigger / Event:** HTTP Webhook event

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| body | json | — |

**Outputs:** —

---

##### Task 3.2: List Emails

**Type:** execute-connector-activity
**Description:** Retrieves a capped list of Inbox emails whose subject contains "urgent". The result is not consumed downstream — this task exercises the `execute-connector-activity` step in the flow.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Wait for HTTP Webhook")` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `uipath-microsoft-outlook365`
**Connection:** is-sandboxes-test@uipathsandboxes.onmicrosoft.com · **Connection ID:** `dd657127-91f5-4568-a3a3-c024bc03fb0f`
**Activity Type ID:** `5b154ea8-15bb-30a6-b07d-74a8cd1c1688` · **Service Type:** `Intsvc.ActivityExecution`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Get Email List (objectName `ListEmails`, GET `/ListEmails`)
**Trigger / Event:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| parentFolderId | string | `"Inbox"` |
| limit | string | `"10"` |
| filter | string | `contains(subject,'urgent')` |

**Outputs:** —

---

##### Task 3.3: Start Child Case

**Type:** case-management
**Description:** Launches the "Task agentic case" child case, passing the approval comment as input.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("List Emails")` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Resolved Resource:** Task agentic case
**Folder Path:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**Resource Identity:** caseManagementId `deecae87-ce5a-4351-b777-92348aff3226` (v1.0.6)
**Binding Sub-Type:** CaseManagement
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseInput1 | string | `=js:JSON.stringify(vars.$xref('Stage 2','Manager Approval','Comment'))` |

**Outputs:** —

---

### Secondary Stage: Stage 4 - return to origin

**Type:** Stage
**Stage Kind:** secondary
**Description:** Rework exception lane. Activates when Stage 2 exits (e.g. on reject). A second approval either sends the case back to its origin (approve) or marks the lane complete (reject).
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Stage 2")` | — | No | Entry rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:vars.$xref('Stage 4 - return to origin','Rework Approval','Action') === "reject"` | exit-only | Yes | Stage 6 App Reject |
| `selected-tasks-completed("Rework Approval")` | `=js:vars.$xref('Stage 4 - return to origin','Rework Approval','Action') === "approve"` | return-to-origin | No | Exit rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Rework Approval | action | Yes | No | Reviewer | — |

---

##### Task 4.1: Rework Approval

**Type:** action
**Description:** Second approval on the rework lane. Approve returns the case to origin; reject completes the lane.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: SimpleApprovalApp
**Action App ID:** `d5102769-8bac-4afc-a727-77745c53181e` (actionDefinitionId `7ee15f07-6845-46e9-9388-7eadd30f76b6`, v1.0.6)
**Deployment Folder:** Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106
**actionType:** —
**Recipient:** Email: song.zhao@uipath.com
**Priority:** — · **Task Title:** Rework approval · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| Content | String | "" (empty literal) | No |
| Comment | String | "" (empty literal) | No |

**Output Schema:** —

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | Action = "approve" | Complete task; stage returns to origin |
| Reject | Action = "reject" | Complete task; stage marks complete |

---

### Stage 5: Stage 5 - connector entry

**Type:** Stage
**Description:** Event-driven stage entered when an HTTP-webhook event arrives, independent of the linear flow. On completion it hands off to a user-selected next stage.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `wait-for-connector` (HTTP Webhook event) | — | No | Entry rule 1 |

**Connector Rule Detail:**
- Connector: HTTP Webhook · Connector Key: `uipath-http-webhook`
- Connection: athena-cmgolden-expense-reporting · Connection ID: `6a817d24-cbbd-4389-b10d-4329214ffb8d`
- Activity Type ID: `773cab30-51dc-3eb4-b19d-720dfa151cc9` · Service Type: `Intsvc.WaitForEvent`
- Event: HTTP Webhook event (objectName `HTTP_WEBHOOK`, operation `GENERIC`, eventMode `webhooks`)
- Filter: —
- Event Parameters: —

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | wait-for-user | Yes | Stage complete |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Wait for timer - S5 | wait-for-timer | Yes | No | — | — |

---

##### Task 5.1: Wait for timer - S5

**Type:** wait-for-timer
**Description:** Fixed delay after event entry, before the user-select handoff.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Timer:** timeDuration
**Value:** PT10S

---

### Stage 6: Stage 6 - to be interrupted

**Type:** Stage
**Description:** Long-running timer stage entered after Stage 3, demonstrating a stage that can be interrupted. Not required for case completion.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Stage 3")` | — | No | Entry rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Completion rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Timer to be interrupted | wait-for-timer | Yes | No | — | — |

---

##### Task 6.1: Timer to be interrupted

**Type:** wait-for-timer
**Description:** Long delay that can be interrupted before it elapses.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Timer:** timeDuration
**Value:** PT20M

---

### Stage 7: Stage 7 - user select

**Type:** Stage
**Description:** Entered when a user selects it as the next stage from an upstream `wait-for-user` exit (Stage 5). Runs a short timer before handing to the completion-delay stage.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `user-selected-stage` | — | No | Entry rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Completion rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Wait for timer - S7 | wait-for-timer | Yes | No | — | — |

---

##### Task 7.1: Wait for timer - S7

**Type:** wait-for-timer
**Description:** Fixed delay on the user-selected stage.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Timer:** timeDuration
**Value:** PT10S

---

### Stage 8: Stage 8 - delay case completion

**Type:** Stage
**Description:** Final stage that delays case completion with a short timer after the user-selected stage completes.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Stage 7")` | — | No | Stage entry |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Stage complete |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Wait for timer - S8 | wait-for-timer | Yes | No | — | — |

---

##### Task 8.1: Wait for timer - S8

**Type:** wait-for-timer
**Description:** Short delay before case completion.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `runs-sequentially` | — | Task entry |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**Timer:** timeDuration
**Value:** PT5S

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Reviewer | Stage 2, Stage 4 - return to origin | View, Act | Approves or rejects the expense via the SimpleApprovalApp action app; drives the reject/rework routing. |

### Process App Views

> Case App is Enabled. No custom views are defined in the source; the default case list and case detail views apply.

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| Case App | Case Detail | Reviewer | Review expense and act on approval tasks | Stage timeline, approval action, comment |

---

## Section 4: Integrations

> All deployed resources below are pre-deployed in the **`Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106`** solution folder and must be resolved within it — each name is unique inside this folder. Connections are existing tenant connections bound by Connection ID: the HTTP Webhook connection `athena-cmgolden-expense-reporting` and the Outlook 365 sandbox connection `is-sandboxes-test@uipathsandboxes.onmicrosoft.com` in the parent `Shared/uipath-maestro-case` folder.

### Integration Service Connectors

| Connector | Connector Key | System | Connection (ID) | Auth Method | Operations Used | Used By Tasks |
|-----------|---------------|--------|-----------------|-------------|-----------------|---------------|
| HTTP Webhook | `uipath-http-webhook` | HTTP Webhook | athena-cmgolden-expense-reporting (`6a817d24-cbbd-4389-b10d-4329214ffb8d`) | AuthenticateAfterDeployment | Event (GENERIC) | Wait for HTTP Webhook; Stage 5 entry rule |
| Microsoft Outlook 365 | `uipath-microsoft-outlook365` | Microsoft Outlook 365 | is-sandboxes-test@uipathsandboxes.onmicrosoft.com (`dd657127-91f5-4568-a3a3-c024bc03fb0f`) | OAuth2 | Get Email List | List Emails |

#### HTTP Webhook

**Operations:**

| Operation | Activity Type ID | Method | Input Fields | Output Fields |
|-----------|------------------|--------|-------------|---------------|
| Event (GENERIC) | `773cab30-51dc-3eb4-b19d-720dfa151cc9` | EVENT | body: json | response (request_body: string, request_headers: string) |

#### Microsoft Outlook 365

**Operations:**

| Operation | Activity Type ID | Method | Input Fields | Output Fields |
|-----------|------------------|--------|-------------|---------------|
| Get Email List | `5b154ea8-15bb-30a6-b07d-74a8cd1c1688` | GET | parentFolderId (required), limit, filter, unReadOnly, importance, withAttachmentsOnly, includeSubfolders, markAsRead, conversationId | email list: subject, from, receivedDateTime, isRead, … |

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| API Workflow | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 | `b9e4f81a-a2c5-4e6d-ab72-a819649c7666` (v1.0.6) | APIInput1 → APIOutput1 | Call Expense API |

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|--------------------|---------------|
| Agent | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 | `ccf5793f-54ab-4262-bf44-fcd09a52ed4e` (v1.0.6) | expenseRequest → AgentExpenseRequest | Analyze Expense Request |

### Processes & RPA

| Resource | Type | Folder | Resource ID (+version) | Used By Tasks |
|----------|------|--------|------------------------|---------------|
| Agentic Process | process (ProcessOrchestration) | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 | `7d01a11a-c8a3-41b0-b30f-f65c4d7ddbb9` (v1.0.6) | Process Expense Request |
| RPA Workflow | rpa | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 | `0bc08e50-b45a-401c-aec8-a720e1d190e3` (v1.0.6) | Record Expense via RPA |

### Child Cases

| Child Case | Identifier Prefix | Wait for Completion | Used By Tasks |
|------------|-------------------|---------------------|---------------|
| Task agentic case | CASE | — | Start Child Case |
