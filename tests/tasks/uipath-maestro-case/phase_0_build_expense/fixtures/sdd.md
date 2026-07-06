# SDD — ExpenseReimbursement

> **Case Definition Blueprint** — Employee Expense Reimbursement end-to-end case, from submission through payment to terminal disposition.

> **⚠️ Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: 8 stages (5 primary + 3 terminal secondary), 22 tasks, 5 integrations (Workday API, Outlook, ERP RPA, Slack, ServiceNow), 4 personas, 1 child case (Payment Tracking).
> Review carefully before approving. Consider splitting into smaller cases or trimming scope.

---

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Submission](#stage-1-submission) — 3 tasks
   - [Stage 2: Manager Approval](#stage-2-manager-approval) — 5 tasks
   - [Stage 3: Finance Approval](#stage-3-finance-approval) — 4 tasks
   - [Stage 4: Payment](#stage-4-payment) — 4 tasks
   - [Stage 5: Approved](#stage-5-approved) — 2 tasks
   - [Secondary Stage: Rejected](#secondary-stage-rejected) — 2 tasks
   - [Secondary Stage: Withdrawn](#secondary-stage-withdrawn) — 2 tasks
3. [Personas & App Views](#section-3-personas--app-views) — 4 Personas, Process App Views
4. [Integrations](#section-4-integrations) — API Workflows, Agents, Processes & RPA, IS Connectors, Child Cases

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | ExpenseReimbursement |
| Case Description | Manages the end-to-end lifecycle of an employee expense reimbursement request, from initial submission through manager and finance approval, payment execution, and final disposition. Supports automatic escalation, fraud detection, ad-hoc information requests, and withdrawal. |
| Case Identifier | Type: constant. Prefix: ER |
| Priority | Choiceset: Low, Medium, High, Critical — Default: Medium |
| Case-Level SLA | 15 minutes |
| SLA Type | time-based |
| Case App | Enabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 70% of SLA duration (≈ 10.5 min) | Notify: UserGroup: Finance Operations |
| Breached | 100% of SLA duration (15 min) | Notify: UserGroup: Finance Leadership |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Intsvc.EventTrigger | expense_requests | Record created |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| `required-stages-completed` | — | Case exited | Yes | Complete Rule 1 |
| `selected-stage-completed("Rejected")` | — | Case exited | No | Exit Rule 1 |
| `selected-stage-completed("Withdrawn")` | — | Case exited | No | Exit Rule 2 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| employeeName | Variable | string | T02 | response.employee_name | | Employee's full name from the expense_requests record-created payload |
| employeeEmail | Variable | string | T02 | response.employee_email | | Employee's email address from the expense_requests record-created payload |
| department | Variable | string | T02 | response.department | | Employee's department from the expense_requests record-created payload |
| expenseType | Variable | string | T02 | response.expense_type | | Category of expense from the expense_requests record-created payload |
| amount | Variable | float | T02 | response.amount | | Expense amount from the expense_requests record-created payload |
| currency | Variable | string | T02 | response.currency | "USD" | Currency code from the expense_requests record-created payload |
| description | Variable | string | T02 | response.description | | Expense description from the expense_requests record-created payload |
| receiptUrl | Variable | string | T02 | response.receipt_url | | URL to uploaded receipt from the expense_requests record-created payload |
| submittedDate | Variable | datetime | T02 | response.submitted_date | | Date the expense was submitted from the expense_requests record-created payload |
| expenseDocuments | Variable | jsonSchema | | | | Companion case entity expense_documents for receipts and supporting files |
| expenseComments | Variable | jsonSchema | | | | Companion case entity expense_comments for participant notes |
| caseStatus | Variable | string | | | "Open" | Current case lifecycle status |
| validationResult | Variable | string | | | | Result of expense validation API workflow |
| enrichedEmployeeData | Variable | jsonSchema | | | | Employee details enriched from Workday |
| expenseCategory | Variable | string | | | | AI-determined expense category |
| managerEmail | Variable | string | | | | Manager's email address (from Workday enrichment) |
| managerDecision | Variable | string | | | | Manager's approval decision: Approved or Rejected or RequestInfo |
| managerComments | Variable | string | | | | Manager's comments from review action |
| escalationFired | Variable | boolean | | | false | Whether manager escalation timer fired |
| policyCheckResult | Variable | string | | | | Result of finance policy API workflow check |
| fraudCheckResult | Variable | string | | | | Result of fraud/anomaly agent analysis |
| budgetGlResult | Variable | jsonSchema | | | | Result of Budget and GL reconciliation process |
| financeDecision | Variable | string | | | | Finance team's review decision: Approved or Rejected |
| financeComments | Variable | string | | | | Finance team's comments from review action |
| selectedPaymentMethod | Variable | string | | | | Payment method selected by the finance reviewer |
| paymentTrackingCaseId | Variable | string | | | | Child case ID for optional Payment Tracking sub-case |
| paymentConfirmationData | Variable | jsonSchema | | | | Payload received from payment-confirmation webhook |
| erpReimbursementResult | Variable | string | | | | Result of ERP RPA reimbursement process |
| slackConfirmationResult | Variable | string | | | | Result of Slack confirmation connector activity |
| sapGlResult | Variable | string | | | | Result of SAP GL record posting process |
| rejectionNotificationResult | Variable | string | | | | Result of rejection notification connector activity |
| serviceNowAuditResult | Variable | string | | | | Result of ServiceNow audit log process |
| withdrawalConfirmationResult | Variable | string | | | | Result of withdrawal Outlook confirmation connector activity |
| rpaCleanupResult | Variable | string | | | | Result of RPA cleanup process |
| infoRequestResult | Variable | string | | | | Result of ad-hoc information request connector activity |

---

## Section 2: Stages & Tasks

---

### Stage 1: Submission

**Type:** Stage
**Description:** Validates the submitted expense via API, enriches employee details from Workday, and uses an AI agent to categorize the expense before routing to manager approval.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `case-entered` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 3 | min | 75% | Notify: UserGroup: Expense Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Validate Expense | api-workflow | Yes | Yes | — | — |
| 2 | Enrich Employee Details | api-workflow | Yes | Yes | — | — |
| 3 | Categorize Expense | agent | Yes | Yes | — | — |

---

##### Task 1.1: Validate Expense

**Type:** api-workflow
**Description:** Calls the expense validation API workflow to check the expense against business rules (amount limits, required fields, policy compliance). Stores the validation result for downstream routing.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: ExpenseValidation api-workflow>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeName | string | `=vars.employeeName` |
| employeeEmail | string | `=vars.employeeEmail` |
| department | string | `=vars.department` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| description | string | `=vars.description` |
| receiptUrl | string | `=vars.receiptUrl` |
| submittedDate | datetime | `=vars.submittedDate` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| validationStatus | -> validationResult |
| — | caseStatus = "Validating" |

---

##### Task 1.2: Enrich Employee Details

**Type:** api-workflow
**Description:** Calls the Workday enrichment API workflow to retrieve additional employee information including manager email, cost center, and employment status needed for approval routing.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Validate Expense")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: WorkdayEmployeeEnrichment api-workflow>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeEmail | string | `=vars.employeeEmail` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| employeeData | -> enrichedEmployeeData |
| managerEmail | -> managerEmail |

---

##### Task 1.3: Categorize Expense

**Type:** agent
**Description:** Uses an AI agent to analyze the expense description, receipt, and type to produce a normalized expense category for routing and reporting.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Enrich Employee Details")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: ExpenseCategorizationAgent agent>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| expenseType | string | `=vars.expenseType` |
| description | string | `=vars.description` |
| amount | float | `=vars.amount` |
| receiptUrl | string | `=vars.receiptUrl` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| category | -> expenseCategory |

---

### Stage 2: Manager Approval

**Type:** Stage
**Description:** Sends an Outlook email notification to the manager, waits for their review via an action task, with a 3-minute escalation timer and ad-hoc paths for requesting more information or withdrawal.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Submission")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.managerDecision === "Approved")` | exit-only | Yes | Complete Rule 1 |
| `selected-tasks-completed("Manager Review")` | `=js:(vars.managerDecision === "Rejected")` | exit-only | No | Exit Rule 1 |
| `selected-tasks-completed("Manager Review")` | `=js:(vars.managerDecision === "Withdrawn")` | exit-only | No | Exit Rule 2 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | min | 70% | Notify: UserGroup: Expense Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Manager Notification | execute-connector-activity | No | Yes | — | — |
| 2 | Escalation Timer | wait-for-timer | No | Yes | — | — |
| 3 | Manager Review | action | Yes | No | Manager | Medium |
| 4 | Request Additional Info | execute-connector-activity | No | No | — | — |
| 5 | Process Withdrawal | execute-connector-activity | No | No | — | — |

---

##### Task 2.1: Send Manager Notification

**Type:** execute-connector-activity
**Description:** Sends an Outlook email to the manager notifying them that an expense report is pending their review, including a link to the case and key expense details.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `microsoftOutlook365`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| to | string | `=vars.managerEmail` |
| subject | string | `=js:("Expense Approval Required: " + vars.employeeName + " - " + vars.expenseType)` |
| body | string | `=js:("Please review expense request for " + vars.employeeName + ". Amount: " + vars.amount + " " + vars.currency + ". Description: " + vars.description)` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Pending Manager Approval" |

---

##### Task 2.2: Escalation Timer

**Type:** wait-for-timer
**Description:** Waits 3 minutes. If the manager has not completed their review, the timer fires and sets the escalation flag, allowing downstream conditions to route appropriately.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Timer:** timeDuration
**Value:** PT3M

---

##### Task 2.3: Manager Review

**Type:** action
**Description:** Presents the expense details to the manager for review and decision. The manager can approve, reject, request more information, or mark the expense as withdrawn.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: `<UNRESOLVED: ManagerReview action app>`
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`
**actionType:** ManagerExpenseReview
**Recipient:** `Expression: =vars.managerEmail`
**Priority:** Medium · **Task Title:** Review Expense Report — `=js:(vars.employeeName + ": " + vars.expenseType + " " + vars.amount + " " + vars.currency)` · **Labels:** expense-approval

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| employeeName | String | `=vars.employeeName` | Yes |
| department | String | `=vars.department` | Yes |
| expenseType | String | `=vars.expenseType` | Yes |
| amount | Float | `=vars.amount` | Yes |
| currency | String | `=vars.currency` | Yes |
| description | String | `=vars.description` | Yes |
| receiptUrl | String | `=vars.receiptUrl` | No |
| expenseCategory | String | `=vars.expenseCategory` | No |
| submittedDate | DateTime | `=vars.submittedDate` | No |
| validationResult | String | `=vars.validationResult` | No |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> managerDecision |
| Comments | -> managerComments |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | managerDecision = "Approved" | Complete task and advance to Finance Approval |
| Reject | managerDecision = "Rejected" | Complete task and route to Rejected terminal stage |
| Request Info | managerDecision = "RequestInfo" | Complete task and trigger ad-hoc info request |
| Withdraw | managerDecision = "Withdrawn" | Complete task and route to Withdrawn terminal stage |

---

##### Task 2.4: Request Additional Info

**Type:** execute-connector-activity
**Description:** Ad-hoc task that sends an Outlook email to the employee requesting additional information or documentation. Can be triggered multiple times.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Manager Review")` | `=js:(vars.managerDecision === "RequestInfo")` | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `microsoftOutlook365`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| to | string | `=vars.employeeEmail` |
| subject | string | `=js:("Additional Information Required for Expense: " + vars.expenseType)` |
| body | string | `=js:("Your manager has requested additional information. Comments: " + vars.managerComments)` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | infoRequestResult = "Sent" |

---

##### Task 2.5: Process Withdrawal

**Type:** execute-connector-activity
**Description:** Ad-hoc task that sends an Outlook email to the employee confirming the withdrawal request has been received. Routes the case to the Withdrawn terminal stage.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Manager Review")` | `=js:(vars.managerDecision === "Withdrawn")` | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `microsoftOutlook365`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| to | string | `=vars.employeeEmail` |
| subject | string | `=js:("Expense Withdrawal Confirmed: " + vars.expenseType)` |
| body | string | `=js:("Your expense withdrawal request has been received. Case: " + metadata.ExternalId)` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | withdrawalConfirmationResult = "Sent" |

---

### Stage 3: Finance Approval

**Type:** Stage
**Description:** Runs a policy compliance API workflow, fraud and anomaly agent analysis, Budget and GL reconciliation process, and presents the Finance Team Review action for final finance decision.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Manager Approval")` | `=js:(vars.managerDecision === "Approved")` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | `=js:(vars.financeDecision === "Approved")` | exit-only | Yes | Complete Rule 1 |
| `selected-tasks-completed("Finance Team Review")` | `=js:(vars.financeDecision === "Rejected")` | exit-only | No | Exit Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | min | 70% | Notify: UserGroup: Finance Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Policy Compliance Check | api-workflow | No | Yes | — | — |
| 2 | Fraud and Anomaly Detection | agent | No | Yes | — | — |
| 3 | Budget and GL Reconciliation | process | No | Yes | — | — |
| 4 | Finance Team Review | action | Yes | No | Finance Reviewer | High |

---

##### Task 3.1: Policy Compliance Check

**Type:** api-workflow
**Description:** Calls the finance policy API workflow to validate the expense against corporate travel and expense policies, spending limits, and approval authority thresholds.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Resolved Resource:** `<UNRESOLVED: FinancePolicyCheck api-workflow>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| department | string | `=vars.department` |
| expenseCategory | string | `=vars.expenseCategory` |
| enrichedEmployeeData | jsonSchema | `=vars.enrichedEmployeeData` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| policyResult | -> policyCheckResult |

---

##### Task 3.2: Fraud and Anomaly Detection

**Type:** agent
**Description:** Uses an AI agent to analyze the expense for fraud signals and anomalies, comparing against historical patterns, receipt data, and known fraud indicators.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Resolved Resource:** `<UNRESOLVED: FraudAnomalyAgent agent>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeEmail | string | `=vars.employeeEmail` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| receiptUrl | string | `=vars.receiptUrl` |
| submittedDate | datetime | `=vars.submittedDate` |
| expenseCategory | string | `=vars.expenseCategory` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| fraudResult | -> fraudCheckResult |

---

##### Task 3.3: Budget and GL Reconciliation

**Type:** process
**Description:** Invokes the Budget and GL Reconciliation orchestration process to verify available budget and check general ledger codes for the expense before finance review.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Policy Compliance Check", "Fraud and Anomaly Detection")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Resolved Resource:** `<UNRESOLVED: BudgetGLReconciliation process>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| department | string | `=vars.department` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| expenseCategory | string | `=vars.expenseCategory` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| reconciliationResult | -> budgetGlResult |

---

##### Task 3.4: Finance Team Review

**Type:** action
**Description:** Presents a comprehensive finance review dashboard to the Finance Reviewer, including policy check, fraud score, and GL reconciliation results. Reviewer selects the payment method on approval.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Budget and GL Reconciliation")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

**HITL Implementation:** Action App: `<UNRESOLVED: FinanceReview action app>`
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`
**actionType:** FinanceExpenseReview
**Recipient:** `Role: Finance Reviewer`
**Priority:** High · **Task Title:** Finance Review: `=js:(vars.employeeName + " - " + vars.expenseType + " " + vars.amount + " " + vars.currency)` · **Labels:** finance-approval, expense

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| employeeName | String | `=vars.employeeName` | Yes |
| department | String | `=vars.department` | Yes |
| expenseType | String | `=vars.expenseType` | Yes |
| amount | Float | `=vars.amount` | Yes |
| currency | String | `=vars.currency` | Yes |
| description | String | `=vars.description` | Yes |
| receiptUrl | String | `=vars.receiptUrl` | No |
| expenseCategory | String | `=vars.expenseCategory` | Yes |
| policyCheckResult | String | `=vars.policyCheckResult` | Yes |
| fraudCheckResult | String | `=vars.fraudCheckResult` | Yes |
| budgetGlResult | jsonSchema | `=vars.budgetGlResult` | Yes |
| managerComments | String | `=vars.managerComments` | No |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> financeDecision |
| Comments | -> financeComments |
| PaymentMethod | -> selectedPaymentMethod |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | financeDecision = "Approved" | Complete task and advance to Payment stage. Reviewer must select payment method. |
| Reject | financeDecision = "Rejected" | Complete task and route to Rejected terminal stage |

---

### Stage 4: Payment

**Type:** Stage
**Description:** Executes ERP RPA reimbursement using the method selected by the finance reviewer, optionally launches a Payment Tracking sub-case, and waits for a payment-confirmation webhook.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Finance Approval")` | `=js:(vars.financeDecision === "Approved")` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `wait-for-connector` | — | exit-only | Yes | Complete Rule 1 |

**Connector Rule Detail:**
- Connector: `<UNRESOLVED: Payment Confirmation webhook connector>`
- Connection: `<UNRESOLVED>`
- Event: Payment Confirmed
- Filter: —
- Event Parameters: —

**Connector Rule Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response | -> paymentConfirmationData |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 4 | min | 75% | Notify: UserGroup: Finance Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | ERP Reimbursement | rpa | Yes | Yes | — | — |
| 2 | Launch Payment Tracking | case-management | No | Yes | — | — |
| 3 | Await Payment Confirmation | wait-for-connector | No | Yes | — | — |

---

##### Task 4.1: ERP Reimbursement

**Type:** rpa
**Description:** Runs the ERP RPA reimbursement robot to enter and process the payment in the ERP system using the payment method selected by the Finance Reviewer.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: ERPReimbursement rpa process>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeName | string | `=vars.employeeName` |
| employeeEmail | string | `=vars.employeeEmail` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| expenseType | string | `=vars.expenseType` |
| selectedPaymentMethod | string | `=vars.selectedPaymentMethod` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| result | -> erpReimbursementResult |

---

##### Task 4.2: Launch Payment Tracking

**Type:** case-management
**Description:** Optionally launches a Payment Tracking sub-case to monitor the payment through to settlement. Triggered after ERP reimbursement initiates.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("ERP Reimbursement")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Child Case:** PaymentTracking
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|----------------|----------------|
| employeeName | employeeName |
| employeeEmail | employeeEmail |
| amount | amount |
| currency | currency |
| selectedPaymentMethod | paymentMethod |
| erpReimbursementResult | erpTransactionId |

**Wait for Completion:** No

**Data Returned (child -> parent):**

> Not applicable — Wait for Completion is No.

---

##### Task 4.3: Await Payment Confirmation

**Type:** wait-for-connector
**Description:** Waits for a payment-confirmation webhook callback from the payment processor confirming that the reimbursement has been processed.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("ERP Reimbursement")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

**Connector:** `<UNRESOLVED: Payment Confirmation webhook connector>` · **Connector Key:** `<UNRESOLVED>`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.WaitForEvent`
**Auth Method:** `<UNRESOLVED>`
**Account / Endpoint:** —
**Operation:** —
**Trigger / Event:** Payment Confirmed

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response | -> paymentConfirmationData |

---

### Stage 5: Approved

**Type:** Stage
**Description:** Terminal happy-path stage. Sends a Slack confirmation message to the employee and posts the SAP GL records for accounting.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-completed("Payment")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | min | 75% | Notify: UserGroup: Finance Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Slack Confirmation | execute-connector-activity | Yes | Yes | — | — |
| 2 | Post SAP GL Records | process | Yes | Yes | — | — |

---

##### Task 5.1: Send Slack Confirmation

**Type:** execute-connector-activity
**Description:** Sends a Slack message to the employee confirming that their expense reimbursement has been approved and payment is being processed.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Connector:** Slack · **Connector Key:** `slack`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Message

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| channel | string | `=vars.employeeEmail` |
| text | string | `=js:("Your expense request has been approved and payment of " + vars.amount + " " + vars.currency + " is being processed. Reference: " + metadata.ExternalId)` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | slackConfirmationResult = "Sent" |
| — | caseStatus = "Approved" |

---

##### Task 5.2: Post SAP GL Records

**Type:** process
**Description:** Invokes the SAP GL posting orchestration process to record the approved reimbursement in the general ledger with appropriate cost center and account codes.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Send Slack Confirmation")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: SAPGLPosting process>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeName | string | `=vars.employeeName` |
| department | string | `=vars.department` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| expenseCategory | string | `=vars.expenseCategory` |
| paymentConfirmationData | jsonSchema | `=vars.paymentConfirmationData` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| glPostResult | -> sapGlResult |

---

### Secondary Stage: Rejected

**Type:** Stage
**Stage Kind:** secondary
**Description:** Terminal rejection stage. Sends a rejection notification to the employee and logs an audit record in ServiceNow.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Manager Approval")` | `=js:(vars.managerDecision === "Rejected")` | No | Entry Rule 1 |
| `selected-stage-exited("Finance Approval")` | `=js:(vars.financeDecision === "Rejected")` | No | Entry Rule 2 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | min | 75% | Notify: UserGroup: Finance Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Rejection Notification | execute-connector-activity | Yes | Yes | — | — |
| 2 | Log ServiceNow Audit | process | Yes | Yes | — | — |

---

##### Task R.1: Send Rejection Notification

**Type:** execute-connector-activity
**Description:** Sends an Outlook email to the employee notifying them that their expense request has been rejected, including the reviewer's comments and next steps.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `microsoftOutlook365`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| to | string | `=vars.employeeEmail` |
| subject | string | `=js:("Expense Request Rejected: " + vars.expenseType)` |
| body | string | `=js:("Your expense request has been rejected. Comments: " + (vars.financeComments || vars.managerComments))` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | rejectionNotificationResult = "Sent" |
| — | caseStatus = "Rejected" |

---

##### Task R.2: Log ServiceNow Audit

**Type:** process
**Description:** Invokes the ServiceNow audit logging orchestration process to create an audit record of the rejection, capturing decision maker, timestamp, and rejection reason for compliance tracking.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Send Rejection Notification")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: ServiceNowAuditLog process>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** ProcessOrchestration
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeName | string | `=vars.employeeName` |
| employeeEmail | string | `=vars.employeeEmail` |
| expenseType | string | `=vars.expenseType` |
| amount | float | `=vars.amount` |
| currency | string | `=vars.currency` |
| rejectionReason | string | `=js:(vars.financeComments || vars.managerComments)` |
| managerDecision | string | `=vars.managerDecision` |
| financeDecision | string | `=vars.financeDecision` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| auditResult | -> serviceNowAuditResult |

---

### Secondary Stage: Withdrawn

**Type:** Stage
**Stage Kind:** secondary
**Description:** Terminal withdrawal stage. Sends an Outlook confirmation to the employee and runs an RPA cleanup process to reverse any partial entries in downstream systems.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `selected-stage-exited("Manager Approval")` | `=js:(vars.managerDecision === "Withdrawn")` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | min | 75% | Notify: UserGroup: Finance Operations | Notify: UserGroup: Finance Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Withdrawal Confirmation | execute-connector-activity | Yes | Yes | — | — |
| 2 | RPA Cleanup | rpa | Yes | Yes | — | — |

---

##### Task W.1: Send Withdrawal Confirmation

**Type:** execute-connector-activity
**Description:** Sends an Outlook email to the employee confirming that their expense request withdrawal has been processed.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Connector:** Microsoft Outlook 365 · **Connector Key:** `microsoftOutlook365`
**Connection:** `<UNRESOLVED>` · **Connection ID:** `<UNRESOLVED>`
**Activity Type ID:** `<UNRESOLVED>` · **Service Type:** `Intsvc.ConnectorActivity`
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| to | string | `=vars.employeeEmail` |
| subject | string | `=js:("Expense Withdrawal Confirmed: " + vars.expenseType)` |
| body | string | `=js:("Your expense request has been successfully withdrawn. Reference: " + metadata.ExternalId)` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | withdrawalConfirmationResult = "Sent" |
| — | caseStatus = "Withdrawn" |

---

##### Task W.2: RPA Cleanup

**Type:** rpa
**Description:** Runs an RPA cleanup process to reverse any partial entries created during expense submission and validation in downstream systems.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `selected-tasks-completed("Send Withdrawal Confirmation")` | — | Entry Rule 1 |

**Task envelope:**

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

**Resolved Resource:** `<UNRESOLVED: ExpenseCleanupRPA rpa process>`
**Folder Path:** `<UNRESOLVED>`
**Resource Identity:** `<UNRESOLVED>`
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| caseId | string | `=metadata.ExternalId` |
| employeeEmail | string | `=vars.employeeEmail` |
| expenseType | string | `=vars.expenseType` |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| cleanupResult | -> rpaCleanupResult |

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Employee | Submission, Manager Approval (read), Withdrawn | View, Comment | The employee who submits the expense request and receives status communications |
| Manager | Manager Approval | View, Act, Reassign | The employee's direct manager who performs the initial approval review |
| Finance Reviewer | Finance Approval, Payment | View, Act, Reassign | Finance team member who performs the policy-based finance review and selects the payment method |
| Finance Operations | All | View, Manage, Escalate | Finance operations team with oversight across all stages for escalation and exception handling |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| Expense Reimbursement App | Case List | Finance Operations | Overview of all active expense cases by status and stage | Stage filter, amount range filter, employee search, SLA indicator column |
| Expense Reimbursement App | Case Detail | All Personas | Full case details including expense data, decision history, and current status | Expense summary header, stage timeline, document viewer, comments feed, action history |
| Expense Reimbursement App | Manager Review View | Manager | Focused review interface for manager approval actions | Expense summary, receipt preview, employee enrichment data, approve/reject/request-info/withdraw buttons |
| Expense Reimbursement App | Finance Review Dashboard | Finance Reviewer | Comprehensive finance review with policy, fraud, and GL data | Policy check panel, fraud score indicator, GL reconciliation results, payment method selector |

---

## Section 4: Integrations

### Integration Service Connectors

| Connector | Connector Key | System | Connection (ID) | Auth Method | Operations Used | Used By Tasks |
|-----------|---------------|--------|-----------------|-------------|-----------------|---------------|
| Microsoft Outlook 365 | `microsoftOutlook365` | Microsoft 365 | `<UNRESOLVED>` | OAuth2 | Send Email | Send Manager Notification, Request Additional Info, Process Withdrawal, Send Rejection Notification, Send Withdrawal Confirmation |
| Slack | `slack` | Slack | `<UNRESOLVED>` | OAuth2 | Send Message | Send Slack Confirmation |
| Payment Confirmation Webhook | `<UNRESOLVED>` | Payment Processor | `<UNRESOLVED>` | `<UNRESOLVED>` | Payment Confirmed (event) | Await Payment Confirmation (stage exit + task) |

#### Microsoft Outlook 365

**Operations:**

| Operation | Activity Type ID | Method | Input Fields | Output Fields |
|-----------|------------------|--------|-------------|---------------|
| Send Email | `<UNRESOLVED>` | POST | to: string, subject: string, body: string | messageId: string |

#### Slack

**Operations:**

| Operation | Activity Type ID | Method | Input Fields | Output Fields |
|-----------|------------------|--------|-------------|---------------|
| Send Message | `<UNRESOLVED>` | POST | channel: string, text: string | ts: string |

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| ExpenseValidation | `<UNRESOLVED>` | `<UNRESOLVED>` | expenseType, amount, currency, description, receiptUrl → validationStatus | Validate Expense |
| WorkdayEmployeeEnrichment | `<UNRESOLVED>` | `<UNRESOLVED>` | employeeEmail → employeeData, managerEmail | Enrich Employee Details |
| FinancePolicyCheck | `<UNRESOLVED>` | `<UNRESOLVED>` | expenseType, amount, department, expenseCategory → policyResult | Policy Compliance Check |

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|----------------------------------------|---------------|
| ExpenseCategorizationAgent | `<UNRESOLVED>` | `<UNRESOLVED>` | expenseType, description, amount, receiptUrl → category | Categorize Expense |
| FraudAnomalyAgent | `<UNRESOLVED>` | `<UNRESOLVED>` | employeeEmail, expenseType, amount, receiptUrl, submittedDate → fraudResult | Fraud and Anomaly Detection |

### Processes & RPA

| Resource | Type | Folder | Resource ID (+version) | Used By Tasks |
|----------|------|--------|------------------------|---------------|
| BudgetGLReconciliation | process | `<UNRESOLVED>` | `<UNRESOLVED>` | Budget and GL Reconciliation |
| SAPGLPosting | process | `<UNRESOLVED>` | `<UNRESOLVED>` | Post SAP GL Records |
| ServiceNowAuditLog | process | `<UNRESOLVED>` | `<UNRESOLVED>` | Log ServiceNow Audit |
| ERPReimbursement | rpa | `<UNRESOLVED>` | `<UNRESOLVED>` | ERP Reimbursement |
| ExpenseCleanupRPA | rpa | `<UNRESOLVED>` | `<UNRESOLVED>` | RPA Cleanup |

### Child Cases

| Child Case | Identifier Prefix | Wait for Completion | Used By Tasks |
|------------|-------------------|---------------------|---------------|
| PaymentTracking | PT | No | Launch Payment Tracking |

### External Agents

> None. All AI agents are modeled as first-class UiPath `agent` tasks.
