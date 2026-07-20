# SDD — ExpenseReimbursementRunnable

**Case Definition Blueprint** · Employee Expense Reimbursement — fully-automated runnable e2e variant

> Bug-bash "Employee Expense Reimbursement" scenario, adapted to run end-to-end
> headlessly on the coder-eval tenant with existing generic resources only.
> Adaptations: connector transport steps are re-typed to `api-workflow` /
> `process`; the two human-review steps and the finance stage-selection are
> replaced by automated transitions (decision variables default to `Approve`,
> giving a deterministic linear happy path) so `uip maestro case debug` can run
> the case to completion without human input; escalation timers use seconds; a manual
> trigger starts the case so `uip maestro case debug` can run it headlessly. Task payloads are generic (bound to
> `NameToAgeFixed2`, `CountLetters`, `ProcurementProcess`, `ProjectEuler`,
> `CaseTest`). The 7-stage topology, stage chaining, child case, and the
> Rejected / Withdrawn terminal lanes are preserved; the reject / withdraw lanes
> stay dormant at runtime (gated off by the default-`Approve` decision vars) but
> present for structural coverage.

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Trigger, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Submission](#stage-1-submission) — 2 tasks
   - [Stage 2: Manager Approval](#stage-2-manager-approval) — 2 tasks
   - [Stage 3: Finance Approval](#stage-3-finance-approval) — 3 tasks
   - [Stage 4: Payment](#stage-4-payment) — 3 tasks
   - [Stage 5: Approved](#stage-5-approved) — 2 tasks
   - [Stage 6: Rejected](#stage-6-rejected) — 2 tasks
   - [Stage 7: Withdrawn](#stage-7-withdrawn) — 1 task
3. [Personas & App Views](#section-3-personas--app-views)
4. [Integrations](#section-4-integrations)

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | ExpenseReimbursementRunnable |
| Case Description | Handles an employee-submitted expense from submission through manager and finance approval to payment and close-out, ending in Approved, Rejected, or Withdrawn. Fully-automated runnable variant bound to generic tenant resources. |
| Case Identifier | Type: constant. Prefix: EXP |
| Priority | Choiceset: Low, Medium, High — Default: Medium |
| Case-Level SLA | 15 m |
| SLA Type | time-based |
| Case App | Disabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 70% of SLA duration | Notify: Finance Ops |
| Breached | 100% of SLA duration | Notify: Finance Ops |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | User-initiated | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |
| selected-stage-completed("Rejected") | — | Case exited | No | Exit Rule 1 |
| selected-stage-completed("Withdrawn") | — | Case exited | No | Exit Rule 2 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| caseRef | In | string | | | | External reference supplied by the caller at case start. |
| employeeName | Variable | string | | | "Jane Smith" | Submitting employee's name. |
| employeeEmail | Variable | string | | | "jane.smith@acme.com" | Submitting employee's email. |
| amount | Variable | float | | | 1250.00 | Expense amount. |
| department | Variable | string | | | "Engineering" | Requesting department. |
| expenseType | Variable | string | | | "Travel" | Expense category. |
| managerDecision | Variable | string | | | Approve | Manager's decision; defaults to Approve so the automated happy path advances. |
| financeDecision | Variable | string | | | Approve | Finance decision; defaults to Approve so the automated happy path advances. |
| withdrawSignal | Variable | boolean | | | false | Set when the employee withdraws; false on the automated happy path. |
| finalOutcome | Out | string | | | Pending | Final disposition returned to the caller. |

---

## Section 2: Stages & Tasks

---

### Stage 1: Submission

**Type:** Stage
**Description:** Receives the case after the expense record is created; validates the submission and categorizes the expense before advancing to manager approval.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| case-entered | — | No | Entry Rule 1 |
| selected-stage-exited("Manager Approval") | =js:(vars.managerDecision === "Return") | No | Entry Rule 2 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | =js:(!vars.withdrawSignal) | exit-only | Yes | Complete Rule 1 |
| selected-tasks-completed("Validate Expense Data") | =js:vars.withdrawSignal | exit-only | No | Exit Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 3 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Validate Expense Data | api-workflow | Yes | No | system | — |
| 2 | Auto-Categorize Expense | agent | No | No | system | — |

##### Task 1.1: Validate Expense Data

**Type:** api-workflow
**Description:** Runs an internal policy check on the submitted expense before it advances.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalOutcome = "InReview" |

##### Task 1.2: Auto-Categorize Expense

**Type:** agent
**Description:** AI categorization pass over the expense description.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** CountLetters
**Folder Path:** Shared/uipath-maestro-flow/CountLetters CodedAgent
**Resource Identity:** 19677045-6c7c-406f-be8b-48bd1eb06414
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| inputString | string | =vars.expenseType |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

### Stage 2: Manager Approval

**Type:** Stage
**Description:** The manager-approval stage. In the automated variant a notification api-workflow stands in for the manager review, and the decision variable defaults to Approve so the case advances to Finance Approval.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Submission") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | =js:(vars.managerDecision === "Approve") | exit-only | Yes | Complete Rule 1 |
| selected-tasks-completed("Send Approval Request") | =js:(vars.managerDecision === "Reject") | exit-only | No | Exit Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: Manager | Notify: Manager |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Approval Request | api-workflow | Yes | No | system | — |
| 2 | Approval Escalation | wait-for-timer | No | No | system | — |

##### Task 2.1: Send Approval Request

**Type:** api-workflow
**Description:** Notifies the manager that an expense is awaiting review (email transport re-typed to an api-workflow for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeEmail |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 2.2: Approval Escalation

**Type:** wait-for-timer
**Description:** Short escalation timer; if the manager has not acted it escalates. Seconds-scale for the runnable variant.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Timer Task Detail (type: `wait-for-timer`)

**Timer:** timeDuration
**Value:** PT5S

---

### Stage 3: Finance Approval

**Type:** Stage
**Description:** Finance runs compliance, fraud, and budget checks. In the automated variant the finance decision defaults to Approve and the stage completes normally, chaining to Payment.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Manager Approval") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | =js:(vars.financeDecision === "Approve") | exit-only | Yes | Complete Rule 1 |
| selected-tasks-completed("Policy Compliance Check") | =js:(vars.financeDecision === "Reject") | exit-only | No | Exit Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Policy Compliance Check | api-workflow | Yes | No | system | — |
| 2 | Fraud Anomaly Detection | agent | No | No | system | — |
| 3 | Budget & GL Reconciliation | process | Yes | No | system | — |

##### Task 3.1: Policy Compliance Check

**Type:** api-workflow
**Description:** Checks the expense against policy and budget rules.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 3.2: Fraud Anomaly Detection

**Type:** agent
**Description:** AI pass flagging anomalous expense patterns.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** CountLetters
**Folder Path:** Shared/uipath-maestro-flow/CountLetters CodedAgent
**Resource Identity:** 19677045-6c7c-406f-be8b-48bd1eb06414
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| inputString | string | =vars.employeeEmail |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 3.3: Budget & GL Reconciliation

**Type:** process
**Description:** Deterministic budget verification and approval-tier routing.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** ProcurementProcess
**Folder Path:** Shared/uipath-agents/ProcurementProcess
**Resource Identity:** 4fc450ab-89be-4462-8fc8-21ac4c1d6fb9
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| productId | integer | 1 |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

### Stage 4: Payment

**Type:** Stage
**Description:** Processes the reimbursement, spawns a payment-tracking child case, and confirms settlement.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Finance Approval") | =js:(vars.financeDecision === "Approve") | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 4 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Process Reimbursement | rpa | Yes | No | system | — |
| 2 | Track Reimbursement Sub-Case | case-management | No | No | system | — |
| 3 | Payment Confirmation | api-workflow | Yes | No | system | — |

##### Task 4.1: Process Reimbursement

**Type:** rpa
**Description:** RPA bot posts the reimbursement to the ERP and returns a payment reference.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** ProjectEuler
**Folder Path:** Shared/uipath-maestro-flow/ProjectEuler RPA
**Resource Identity:** 486edc26-0658-4ac1-92c9-1ef953927151
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| problemId | integer | 1 |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 4.2: Track Reimbursement Sub-Case

**Type:** case-management
**Description:** Spawns a Payment Tracking child case with its own lifecycle.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Child Case Task Detail (type: `case-management`)

**Child Case:** CaseTest
**Resolved Resource:** Maestro Case
**Folder Path:** Shared/uipath-maestro-case/CaseTest
**Resource Identity:** dc377f10-090c-43a9-9e19-2ab935ba0489
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|----------------|----------------|
| — | — |

**Wait for Completion:** No

**Data Returned (child -> parent):**

| Child Variable | Parent Variable |
|----------------|----------------|
| — | — |

##### Task 4.3: Payment Confirmation

**Type:** api-workflow
**Description:** Confirms the payment settled (bank confirmation transport re-typed to an api-workflow for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalOutcome = "Approved" |

---

### Stage 5: Approved

**Type:** Stage
**Description:** Terminal success lane: sends confirmation and posts the GL entry, then completes the case.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Payment") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Approval Confirmation | api-workflow | Yes | No | system | — |
| 2 | Update GL Records | process | Yes | No | system | — |

##### Task 5.1: Send Approval Confirmation

**Type:** api-workflow
**Description:** Confirms the reimbursement to the employee (Slack transport re-typed to an api-workflow for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 5.2: Update GL Records

**Type:** process
**Description:** Posts the journal entry to the general ledger (SAP transport re-typed to a process for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** ProcurementProcess
**Folder Path:** Shared/uipath-agents/ProcurementProcess
**Resource Identity:** 4fc450ab-89be-4462-8fc8-21ac4c1d6fb9
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| productId | integer | 1 |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

### Stage 6: Rejected

**Type:** Stage
**Description:** Terminal rejection lane: notifies the employee and logs the rejection for audit. Dormant on the automated happy path (reached only when a decision variable is Reject).
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-exited("Manager Approval") | =js:(vars.managerDecision === "Reject") | No | Entry Rule 1 |
| selected-stage-exited("Finance Approval") | =js:(vars.financeDecision === "Reject") | No | Entry Rule 2 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Rejection Notification | rpa | Yes | No | system | — |
| 2 | Log Rejection for Audit | api-workflow | Yes | No | system | — |

##### Task 6.1: Send Rejection Notification

**Type:** rpa
**Description:** Sends the rejection notice with reason and source.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** ProjectEuler
**Folder Path:** Shared/uipath-maestro-flow/ProjectEuler RPA
**Resource Identity:** 486edc26-0658-4ac1-92c9-1ef953927151
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| problemId | integer | 1 |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalOutcome = "Rejected" |

##### Task 6.2: Log Rejection for Audit

**Type:** api-workflow
**Description:** Logs the rejection as an audit record (ServiceNow transport re-typed to an api-workflow for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeEmail |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

### Stage 7: Withdrawn

**Type:** Stage
**Description:** Terminal withdrawal lane: confirms the employee's withdrawal and closes the case. Dormant on the automated happy path (reached only when withdrawSignal is set).
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-exited("Submission") | =js:vars.withdrawSignal | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | m | 70% | Notify: Finance Ops | Notify: Finance Ops |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Withdrawal Confirmation | api-workflow | Yes | No | system | — |

##### Task 7.1: Send Withdrawal Confirmation

**Type:** api-workflow
**Description:** Confirms to the employee that the expense request was withdrawn (Outlook transport re-typed to an api-workflow for the runnable variant).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.employeeEmail |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalOutcome = "Withdrawn" |

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Manager | Manager Approval | View, Act | Owns the manager-approval stage (automated in this variant). |
| Finance Ops | Finance Approval, Payment | View, Act | Owns finance review and payment (automated in this variant). |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| Expense | Case List | Finance Ops | Track expense cases | Columns: employeeName, amount, stage |
| Expense | Case Detail | Manager | Review a single expense | Sections: expense summary, decision |

---

## Section 4: Integrations

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| NameToAgeFixed2 | Shared/uipath-maestro-case/NameToAgeFixed2 | b6af8fa1-07cc-4a03-b0a1-f966e3fa23be | name → estimatedAge | Validate Expense Data, Send Approval Request, Policy Compliance Check, Payment Confirmation, Send Approval Confirmation, Log Rejection for Audit, Send Withdrawal Confirmation |

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|----------------------|---------------|
| CountLetters | Shared/uipath-maestro-flow/CountLetters CodedAgent | 19677045-6c7c-406f-be8b-48bd1eb06414 | inputString → count | Auto-Categorize Expense, Fraud Anomaly Detection |

### Processes & RPA

| Resource | Type | Folder | Resource ID (+version) | Used By Tasks |
|----------|------|--------|------------------------|---------------|
| ProcurementProcess | process | Shared/uipath-agents/ProcurementProcess | 4fc450ab-89be-4462-8fc8-21ac4c1d6fb9 | Budget & GL Reconciliation, Update GL Records |
| ProjectEuler | rpa | Shared/uipath-maestro-flow/ProjectEuler RPA | 486edc26-0658-4ac1-92c9-1ef953927151 | Process Reimbursement, Send Rejection Notification |

### Child Cases

| Child Case | Identifier Prefix | Wait for Completion | Used By Tasks |
|------------|-------------------|---------------------|---------------|
| CaseTest | CT | No | Track Reimbursement Sub-Case |
