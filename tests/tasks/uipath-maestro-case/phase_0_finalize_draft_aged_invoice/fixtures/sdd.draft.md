# SDD — AgedInvoicePayment

> **Case Definition Blueprint** — Aged invoice payment resolution case for a retail AP proof of value.

> **Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: 13 stages (9 primary + 4 secondary exception lanes), 25 tasks, 5 integrations (Mock ERP, Outlook, ServiceNow, Slack, SAP), 7 personas, 1 child case (Payment Tracking).
> Review carefully before approving. This remains one Maestro case by request.

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|---|---|
| Case Name | AgedInvoicePayment |
| Case Description | Coordinates aged invoice intake, context enrichment, root-cause triage, AP review, exception resolution, supplier collaboration, payment-risk review, approval, and closure for a mocked retail AP proof of value. |
| Case Identifier | Type: constant. Prefix: AIP |
| Priority | Choiceset: Low, Medium, High, Critical — Default: High |
| Case-Level SLA | 30 minutes |
| SLA Type | time-based |
| Case App | Enabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|---|---|---|
| At-Risk | 70% of SLA duration | Notify: UserGroup: AP Team Leads |
| Breached | 100% of SLA duration | Notify: UserGroup: Finance Leadership |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|---|---|---|
| T02 | Intsvc.EventTrigger | aged_invoice_cases | Record created |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|---|---|---|---|---|
| `required-stages-completed` | — | Case exited | Yes | Complete Rule 1 |
| `selected-stage-completed("Closure")` | — | Case exited | No | Exit Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|---|---|---|---|---|---|---|
| invoiceId | Variable | string | T02 | response.invoice_id | | Aged invoice identifier from the record-created payload |
| supplierName | Variable | string | T02 | response.supplier_name | | Supplier name from the aged invoice payload |
| supplierEmail | Variable | string | T02 | response.supplier_email | | Supplier contact email |
| invoiceAmount | Variable | float | T02 | response.amount | | Invoice amount |
| currency | Variable | string | T02 | response.currency | "AUD" | Invoice currency |
| dueDate | Variable | datetime | T02 | response.due_date | | Due date for payment terms |
| invoiceAgeDays | Variable | integer | T02 | response.age_days | | Number of days aged |
| caseStatus | Variable | string | | | "Open" | Current case state |
| enrichmentData | Variable | jsonSchema | | | | Mock ERP, PO, GRN, payment, supplier, and hold context |
| rootCause | Variable | string | | | | Triage root-cause classification |
| priorityScore | Variable | integer | | | 0 | Priority/SLA score calculated during triage |
| slaTier | Variable | string | | | "Standard" | SLA tier from triage |
| caseOwner | Variable | string | | | | AP owner assigned during AP review |
| apDecision | Variable | string | | | | AP Review decision: Resolve, SupplierInfo, Escalate, Hold |
| exceptionResolution | Variable | string | | | | Exception Resolution result |
| supplierQuerySummary | Variable | string | | | | Agent-generated supplier communication summary |
| supplierResponse | Variable | jsonSchema | | | | Evidence received from supplier |
| paymentRiskDecision | Variable | string | | | | Payment Risk result: Clear, Hold, Reject |
| approvalDecision | Variable | string | | | | Approval decision from Finance Manager or Treasury |
| paymentTrackingCaseId | Variable | string | | | | Child Payment Tracking case ID |
| closureSummary | Variable | string | | | | Final closure summary |
| automationIncidentId | Variable | string | | | | ServiceNow incident ID for failed automation |
| auditPostResult | Variable | string | | | | SAP/Slack/ServiceNow close-out result |

---

## Section 2: Stages & Tasks

### Stage 1: Intake and Registration

**Type:** Stage
**Description:** Registers a new aged-invoice case from the case-entity record and creates the initial audit trail.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `case-entered` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Register Invoice Case | api-workflow | Yes | Yes | System | — |
| 2 | Create Initial Audit Event | execute-connector-activity | Yes | Yes | System | — |

##### Task 1.1: Register Invoice Case

**Type:** api-workflow
**Description:** Calls the mock ERP API workflow to register the invoice case and normalize basic invoice metadata.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: AgedInvoiceMockIntegrationApi api-workflow>`
**Folder Path:** `<UNRESOLVED>`
**Binding Sub-Type:** Api

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| supplierName | string | `=vars.supplierName` |
| amount | float | `=vars.invoiceAmount` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| normalizedStatus | caseStatus = "Registered" |

##### Task 1.2: Create Initial Audit Event

**Type:** execute-connector-activity
**Description:** Posts an initial ServiceNow audit event for the new aged invoice case.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Register Invoice Case")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: ServiceNow Create Audit Event connector activity>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| eventType | string | "case_registered" |

**Outputs:**

| Field | Binding / Value |
|---|---|
| result | -> auditPostResult |

### Stage 2: Context Enrichment

**Type:** Stage
**Description:** Pulls invoice, supplier, PO, GRN, payment, hold, and supplier statement context from mocked enterprise systems.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Intake and Registration")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Enrich Invoice Context | api-workflow | Yes | Yes | System | — |
| 2 | Reconcile Supplier Statement | rpa | No | Yes | System | — |

##### Task 2.1: Enrich Invoice Context

**Type:** api-workflow
**Description:** Calls the Mock ERP and procurement API workflow to fetch invoice, PO, GRN, payment, hold, and supplier history.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: AgedInvoiceContextEnrichment api-workflow>`
**Folder Path:** `<UNRESOLVED>`
**Binding Sub-Type:** Api

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| context | -> enrichmentData |
| — | caseStatus = "Enriched" |

##### Task 2.2: Reconcile Supplier Statement

**Type:** rpa
**Description:** Runs an RPA workflow to simulate supplier statement extraction and match the invoice against mocked records.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Enrich Invoice Context")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: AgedInvoice_StatementReconciliation rpa>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| supplierName | string | `=vars.supplierName` |
| invoiceId | string | `=vars.invoiceId` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| reconciliationStatus | -> exceptionResolution |

### Stage 3: Triage

**Type:** Stage
**Description:** Classifies root cause, scores priority/SLA, and recommends the next action.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Context Enrichment")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Classify Root Cause and Priority | agent | Yes | Yes | System | — |
| 2 | Assign AP Owner | process | Yes | Yes | AP Team Lead | — |

##### Task 3.1: Classify Root Cause and Priority

**Type:** agent
**Description:** Invoice Triage Agent classifies rootCause and calculates priorityScore and slaTier from invoice, supplier, GRN, PO, and payment evidence.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: InvoiceTriageAgent agent>`
**Folder Path:** `<UNRESOLVED>`
**Binding Sub-Type:** Agent

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| enrichmentData | jsonSchema | `=vars.enrichmentData` |
| invoiceAgeDays | integer | `=vars.invoiceAgeDays` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| rootCause | -> rootCause |
| priorityScore | -> priorityScore |
| slaTier | -> slaTier |

##### Task 3.2: Assign AP Owner

**Type:** process
**Description:** Assigns the case to an AP Clerk or AP Team Lead based on priorityScore and rootCause.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Classify Root Cause and Priority")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: AssignAgedInvoiceOwner process>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| rootCause | string | `=vars.rootCause` |
| priorityScore | integer | `=vars.priorityScore` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| owner | -> caseOwner |

### Stage 4: AP Review

**Type:** Stage
**Description:** AP reviews the triage recommendation and chooses the resolution route.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Triage")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | AP Ownership Review | action | Yes | Yes | AP Clerk | 5 min |
| 2 | Start SLA Reminder Timer | wait-for-timer | No | Yes | System | — |

##### Task 4.1: AP Ownership Review

**Type:** action
**Description:** Human action for the AP Clerk to confirm owner, root cause, next action, and whether supplier evidence is needed.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**HITL Implementation:** Action App: `<UNRESOLVED: Aged Invoice AP Review>`
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| rootCause | string | `=vars.rootCause` |
| priorityScore | integer | `=vars.priorityScore` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| decision | -> apDecision |

##### Task 4.2: Start SLA Reminder Timer

**Type:** wait-for-timer
**Description:** Waits five minutes before SLA escalation checks.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 2 |

**Timer:** Duration `PT5M`

**Outputs:**

| Field | Binding / Value |
|---|---|
| — | caseStatus = "AP Review In Progress" |

### Stage 5: Exception Resolution

**Type:** Stage
**Description:** Resolves internal exceptions such as missing GRN, price mismatch, duplicate invoice, approval delay, or payment hold.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("AP Review")` | `=vars.apDecision != "SupplierInfo"` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | GRN Confirmation | action | No | Yes | Store/DC Receiver | 5 min |
| 2 | Update Mock ERP Exception | rpa | Yes | Yes | System | — |

##### Task 5.1: GRN Confirmation

**Type:** action
**Description:** Human action to confirm missing goods receipt or delivery discrepancy.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | `=vars.rootCause == "Missing GRN"` | Entry Rule 1 |

**HITL Implementation:** Action App: `<UNRESOLVED: GRN Confirmation>`
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| supplierName | string | `=vars.supplierName` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| resolution | -> exceptionResolution |

##### Task 5.2: Update Mock ERP Exception

**Type:** rpa
**Description:** Updates the Mock ERP exception status after AP or GRN resolution.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("GRN Confirmation")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: MockERPExceptionUpdate rpa>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| exceptionResolution | string | `=vars.exceptionResolution` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| updateStatus | caseStatus = "Exception Resolved" |

### Stage 6: Supplier Collaboration

**Type:** Stage
**Description:** Contacts the supplier, interprets the response, and waits for missing evidence when supplier input is required.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Exception Resolution")` | — | No | Entry Rule 1 |
| `selected-stage-completed("AP Review")` | `=vars.apDecision == "SupplierInfo"` | No | Entry Rule 2 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Notify Supplier via Outlook | execute-connector-activity | Yes | Yes | System | — |
| 2 | Wait for Supplier Evidence | wait-for-connector | No | No | Supplier Contact | — |
| 3 | Interpret Supplier Query | agent | No | Yes | System | — |

##### Task 6.1: Notify Supplier via Outlook

**Type:** execute-connector-activity
**Description:** Sends an Outlook request for evidence or status clarification to the supplier contact.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: Outlook Send Supplier Request connector activity>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| to | string | `=vars.supplierEmail` |
| invoiceId | string | `=vars.invoiceId` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| sentStatus | caseStatus = "Awaiting Supplier" |

##### Task 6.2: Wait for Supplier Evidence

**Type:** wait-for-connector
**Description:** Waits for supplier portal or Outlook evidence for the invoice.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Notify Supplier via Outlook")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: SupplierEvidenceReceived connector trigger>`
**Folder Path:** `<UNRESOLVED>`

**Outputs:**

| Field | Binding / Value |
|---|---|
| evidence | -> supplierResponse |

##### Task 6.3: Interpret Supplier Query

**Type:** agent
**Description:** Supplier Query Agent summarizes supplier response, dispute reason, and recommended next action.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Wait for Supplier Evidence")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: SupplierQueryAgent agent>`
**Folder Path:** `<UNRESOLVED>`
**Binding Sub-Type:** Agent

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| supplierResponse | jsonSchema | `=vars.supplierResponse` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| summary | -> supplierQuerySummary |

### Stage 7: Payment Risk Review

**Type:** Stage
**Description:** Assesses duplicate, tax, bank, hold, approval, and dispute risk before payment approval.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Supplier Collaboration")` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Assess Payment Risk | agent | Yes | Yes | System | — |
| 2 | Start Payment Tracking Case | case-management | No | Yes | System | — |

##### Task 7.1: Assess Payment Risk

**Type:** agent
**Description:** Payment Risk Agent evaluates paymentRiskDecision from enrichmentData, supplierResponse, exceptionResolution, duplicate risk, and approval thresholds.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: PaymentRiskAgent agent>`
**Folder Path:** `<UNRESOLVED>`
**Binding Sub-Type:** Agent

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| enrichmentData | jsonSchema | `=vars.enrichmentData` |
| supplierResponse | jsonSchema | `=vars.supplierResponse` |
| exceptionResolution | string | `=vars.exceptionResolution` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| decision | -> paymentRiskDecision |

##### Task 7.2: Start Payment Tracking Case

**Type:** case-management
**Description:** Starts the Payment Tracking child case when payment follow-up needs separate tracking.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Assess Payment Risk")` | `=vars.paymentRiskDecision == "Clear"` | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: Payment Tracking case-management>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| caseId | -> paymentTrackingCaseId |

### Stage 8: Approval

**Type:** Stage
**Description:** Finance Manager or Treasury approves or rejects payment release after Payment Risk clears.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Payment Risk Review")` | `=vars.paymentRiskDecision == "Clear"` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Payment Approval | action | Yes | Yes | Finance Manager | 5 min |
| 2 | Post Approval Slack Update | execute-connector-activity | No | Yes | System | — |

##### Task 8.1: Payment Approval

**Type:** action
**Description:** Finance Manager reviews paymentRiskDecision, priorityScore, supplier evidence, and approves payment release or hold.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**HITL Implementation:** Action App: `<UNRESOLVED: Aged Invoice Payment Approval>`
**Action App ID:** `<UNRESOLVED>`
**Deployment Folder:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| paymentRiskDecision | string | `=vars.paymentRiskDecision` |
| priorityScore | integer | `=vars.priorityScore` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| decision | -> approvalDecision |

##### Task 8.2: Post Approval Slack Update

**Type:** execute-connector-activity
**Description:** Posts approval status to a Slack AP operations channel.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Payment Approval")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: Slack Post Message connector activity>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| approvalDecision | string | `=vars.approvalDecision` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| result | -> auditPostResult |

### Stage 9: Closure

**Type:** Stage
**Description:** Updates SAP/Mock ERP, records final audit evidence, and closes the aged invoice case.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-completed("Approval")` | `=vars.approvalDecision == "Approved"` | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Post SAP Closure Record | execute-connector-activity | Yes | Yes | System | — |
| 2 | Close Mock ERP Invoice | rpa | Yes | Yes | System | — |

##### Task 9.1: Post SAP Closure Record

**Type:** execute-connector-activity
**Description:** Posts the final SAP closure record and payment status for audit.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: SAP Post Closure connector activity>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |
| approvalDecision | string | `=vars.approvalDecision` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| result | -> auditPostResult |

##### Task 9.2: Close Mock ERP Invoice

**Type:** rpa
**Description:** Updates the Mock ERP invoice screen to closed for the demo.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `selected-tasks-completed("Post SAP Closure Record")` | — | Entry Rule 1 |

**Resolved Resource:** `<UNRESOLVED: MockERPCloseInvoice rpa>`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Type | Binding |
|---|---|---|
| invoiceId | string | `=vars.invoiceId` |

**Outputs:**

| Field | Binding / Value |
|---|---|
| summary | -> closureSummary |
| — | caseStatus = "Closed" |

### Secondary Stage: SLA Escalation

**Type:** Stage
**Stage Kind:** secondary
**Interrupting:** Yes
**Description:** Interrupting lane for at-risk or breached SLA conditions.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-exited("AP Review")` | `=vars.priorityScore >= 80` | Yes | Escalate At Risk |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `selected-tasks-completed("Notify AP Lead")` | — | return-to-origin | No | Return After Escalation |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Notify AP Lead | execute-connector-activity | Yes | No | System | — |

##### Task S1.1: Notify AP Lead

**Type:** execute-connector-activity
**Description:** Sends Slack and Outlook escalation notifications to AP Team Leads.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Outputs:**

| Field | Binding / Value |
|---|---|
| result | -> auditPostResult |

### Secondary Stage: Automation Incident

**Type:** Stage
**Stage Kind:** secondary
**Interrupting:** Yes
**Description:** Interrupting lane for failed API, RPA, connector, or agent automation.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-exited("Context Enrichment")` | `=vars.caseStatus == "AutomationFailed"` | Yes | Automation Failed |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `selected-tasks-completed("Create ServiceNow Incident")` | — | return-to-origin | No | Return After Incident |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Create ServiceNow Incident | execute-connector-activity | Yes | Yes | Automation Support | — |

##### Task S2.1: Create ServiceNow Incident

**Type:** execute-connector-activity
**Description:** Creates a ServiceNow incident for failed automation and stores automationIncidentId.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Outputs:**

| Field | Binding / Value |
|---|---|
| incidentId | -> automationIncidentId |

### Secondary Stage: Reopen and Supplier Dispute

**Type:** Stage
**Stage Kind:** secondary
**Interrupting:** Yes
**Description:** Interrupting lane for supplier disputes or reopened invoices after closure.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-exited("Closure")` | `=vars.supplierQuerySummary == "Dispute"` | Yes | Reopen Dispute |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `selected-tasks-completed("Summarize Supplier Dispute")` | — | return-to-origin | No | Return After Reopen |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Summarize Supplier Dispute | agent | Yes | Yes | System | — |

##### Task S3.1: Summarize Supplier Dispute

**Type:** agent
**Description:** Summarizes reopened supplier dispute and recommends next best action.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Outputs:**

| Field | Binding / Value |
|---|---|
| summary | -> supplierQuerySummary |

### Secondary Stage: Compliance and Payment Risk Hold

**Type:** Stage
**Stage Kind:** secondary
**Interrupting:** Yes
**Description:** Interrupting lane for compliance holds, duplicate risk, tax risk, bank-data issues, and payment-risk holds.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| `selected-stage-exited("Payment Risk Review")` | `=vars.paymentRiskDecision == "Hold"` | Yes | Compliance Hold |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|---|---|---|---|---|
| `selected-tasks-completed("Compliance Hold Review")` | — | return-to-origin | No | Return After Hold |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|
| 1 | Compliance Hold Review | action | Yes | Yes | Finance Manager | 5 min |

##### Task S4.1: Compliance Hold Review

**Type:** action
**Description:** Human action to release or keep a compliance and payment risk hold.

**Entry Condition:**

| WHEN | IF | Display Name |
|---|---|---|
| `current-stage-entered` | — | Entry Rule 1 |

**Outputs:**

| Field | Binding / Value |
|---|---|
| decision | -> paymentRiskDecision |

---

## Section 3: Personas & App Views

| Persona | View / Responsibility |
|---|---|
| AP Clerk | AP Control Tower and AP Ownership Review |
| AP Team Lead | SLA escalation and reassignment |
| Procurement Officer | Price mismatch and PO exception decisions |
| Store/DC Receiver | GRN Confirmation |
| Finance Manager | Payment Approval and Compliance Hold Review |
| Treasury User | Payment release oversight |
| Automation Support | Automation Incident review |

## Section 4: Integrations

| Family | Resource | Purpose |
|---|---|---|
| API Workflow | AgedInvoiceMockIntegrationApi | Mock ERP registration and enrichment |
| Agent | InvoiceTriageAgent | rootCause classification and priorityScore calculation |
| Agent | PaymentRiskAgent | Payment Risk decision gate |
| Action App | Aged Invoice AP Review | AP human decision |
| Action App | Aged Invoice Payment Approval | Finance approval |
| RPA | AgedInvoice_StatementReconciliation | Supplier statement reconciliation |
| RPA | MockERPCloseInvoice | Mock ERP close-out |
| Connector | Outlook | Supplier notification and evidence request |
| Connector | ServiceNow | Automation incident and audit event |
| Connector | Slack | AP escalation and approval updates |
| Connector | SAP | Closure posting |
| Case Management | Payment Tracking | Child case for payment follow-up |
