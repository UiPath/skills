# Process Design Document
## Aged Invoice Payment Case Management Proof of Value

**Client/demo context:** Large Australian retail enterprise similar to Woolworths Group  
**Process:** Aged Invoice Payment Resolution  
**Source BRD:** `aged_invoice_payment_brd.md`  
**Document type:** Process Design Document (PDD)  
**Version:** 1.0 - PoV process design  
**Date:** 2026-06-04  
**Prepared for:** UiPath-led proof of value demonstration  

---

## 1. Document Control

| Field | Value |
|---|---|
| Document owner | UiPath account / solution team |
| Business process owner | Accounts Payable / Finance Operations, assumed for PoV |
| Technical owner | UiPath automation / platform team |
| Status | Process design baseline for SDD handoff |
| Related documents | `aged_invoice_payment_brd.md`; future SDD; future implementation plan; future deployment package |
| Primary audience | Finance, AP, Procurement, Treasury, IT, Automation CoE, Risk, Demo stakeholders |

### 1.1 Version history

| Version | Date | Author | Summary of change |
|---|---:|---|---|
| 0.1 | 2026-06-03 | UiPath / ChatGPT draft | Initial PDD for mock-data case management proof of value |
| 1.0 | 2026-06-04 | UiPath / Codex | Reworked as structured process design baseline aligned to the BRD and SDD handoff needs |

### 1.2 Terminology note

This document uses the phrase **Data Fabric** because that is the terminology requested for the PoV. UiPath documentation also uses **Data Service** in some areas and notes that Data Service is transitioning to Data Fabric in some delivery options. This PDD treats Data Fabric/Data Service as the persistent data model and mock operational store for the PoV.

This document uses the phrase **Coded Action App** to mean a human-task experience built with an action-app pattern and, where supported by the target tenant, delivered using coded app development patterns. The SDD must validate the exact implementation approach against the available tenant version and licensing.

---

## 2. Purpose and Objectives

### 2.1 Purpose

The purpose of this PDD is to define the **business process design** for a proof of value that demonstrates how the UiPath Platform can manage aged invoice exceptions through an end-to-end case management experience. The PoV will use mocked data instead of live customer systems, but it should feel realistic enough for a Woolworths-style retail finance audience.

The PoV will show how aged invoices can be identified, classified, converted into resolution cases, routed to the right owner, handled by humans and agents, updated through API/RPA automations, monitored by SLA, and closed with a complete audit trail.

### 2.2 PoV objectives

| Objective | Description | Demo evidence |
|---|---|---|
| Demonstrate case management | Show aged invoice cases with priority, status, owner, SLA, root cause, activity history, and next best action. | AP Control Tower and Case Workspace. |
| Demonstrate mocked enterprise data | Use realistic mock invoices, suppliers, purchase orders, goods receipts, payments, users, and exception history. | Data Fabric entities and seeded demo dataset. |
| Demonstrate orchestration | Use Maestro to coordinate APIs, RPA workflows, agents, rules, actions, and case state transitions. | Maestro process instance timeline. |
| Demonstrate human-in-the-loop work | Use action apps for AP review, GRN confirmation, procurement approval, payment hold release, and urgent payment review. | Action Center / coded action app screens. |
| Demonstrate agents | Use agents for exception triage, supplier query interpretation, dispute summarization, payment risk assessment, and resolution recommendation. | Agent output panels with confidence and evidence. |
| Demonstrate API and RPA patterns | Use APIs for mock ERP/procurement/payment systems and RPA workflows for legacy-style screen or mailbox automation. | Mock API logs and bot execution results. |
| Demonstrate business value | Show reduction in manual triage effort, faster prioritization, stronger controls, and better visibility. | KPIs and before/after demo narrative. |

### 2.3 Desired customer reaction

The PoV should help Woolworths stakeholders see that UiPath can support a realistic finance operations transformation pattern, not just task automation. The target reaction is:

> "This gives us a practical blueprint for an AP exception control tower: case management, SLA governance, human actions, agents, API/RPA automation, and auditability in one operating model."

---

## 3. Process Overview

### 3.1 Process purpose

The aged invoice payment process identifies supplier invoices that are unpaid, blocked, disputed, awaiting approval, or at risk of breaching payment terms. In the PoV, every material exception is managed as a case with an owner, SLA, priority, evidence pack, next action, and audit trail.

The process is deliberately designed as a **case-centric control tower** rather than a single bot or linear workflow. Aged invoice resolution requires AP, procurement, finance, treasury, store/DC operations, suppliers, agents, APIs, and robots to coordinate around the same operational record.

### 3.2 Business baseline from the BRD

| BRD driver | PDD design response |
|---|---|
| Fragmented aged invoice visibility | AP Control Tower and persistent case data provide one view of invoice, supplier, payment, hold, dispute, and SLA status. |
| Manual root-cause analysis | Triage rules and agents classify exceptions using invoice, PO, GRN, payment, supplier, and communication context. |
| Email-driven chasing | Maestro routes work through structured human actions, supplier communication events, reminders, and escalations. |
| Payment governance risk | Payment Risk Agent and approval actions prevent release where duplicate, hold, tax, bank, approval, or dispute risks remain. |
| Supplier query volume | Supplier Query Agent and controlled supplier notifications provide consistent status responses and evidence requests. |
| Weak audit evidence | CaseActivity, AuditEvent, evidence records, human decisions, agent recommendations, and automation logs form a case timeline. |

### 3.3 End-to-end PoV narrative

1. Aged and at-risk invoices are loaded from mocked ERP/AP data.
2. Mock API workflows enrich each invoice with supplier, PO, GRN, payment, hold, approval, and statement context.
3. Rules and agents classify root cause, assign priority, calculate SLA, and recommend next action.
4. UiPath Case Management creates or updates a case record.
5. Maestro orchestrates human actions, agent calls, API workflows, RPA workflows, reminders, escalations, and incidents.
6. Coded Apps give AP users a control tower and case workspace.
7. Action Apps or Coded Action Apps capture approvals and exception decisions from AP, procurement, stores/DCs, finance, and treasury.
8. RPA workflows simulate legacy mailbox, mock ERP UI, and supplier statement reconciliation patterns.
9. Mock payment and supplier updates are recorded.
10. The case closes with evidence, audit trail, reporting updates, and a clear final outcome.

---

## 4. Background and Business Context

The BRD defines an aged invoice process where supplier invoices remain unpaid, unresolved, disputed, blocked, or overdue because of issues such as missing purchase orders, missing goods receipts, pricing mismatches, quantity mismatches, duplicate invoice risk, supplier master data issues, tax problems, approval delays, and payment holds.

For the PoV, the process will be simplified into a set of high-impact demo scenarios that are believable for a national-scale retailer:

1. **Missing goods receipt** for a distribution-centre delivery.
2. **Price mismatch** against purchase order or contract price.
3. **Duplicate invoice risk** caused by the same supplier submitting through two channels.
4. **Approval delay** for a non-PO services invoice.
5. **Payment hold review** for a critical supplier.
6. **Supplier statement mismatch** where supplier claims an invoice is unpaid.
7. **Urgent supplier payment request** requiring risk review and controlled approval.

The PoV should not attempt to reproduce every AP process variation. It should focus on the control tower, case lifecycle, orchestration, and decision support patterns that can be reused across multiple exception types.

---

## 5. Platform Context

The PoV will position UiPath as the orchestration and execution platform across people, systems, robots, APIs, and AI agents.

| UiPath capability | Role in the PoV |
|---|---|
| Maestro | End-to-end orchestration of the aged invoice resolution process, including process instances, tasks, agent calls, API workflows, robot work, routing, incidents, and SLA-driven monitoring. |
| Case Management | Business-facing case layer for aged invoice exceptions, case status, owner, priority, SLA, activity history, evidence, and closure. |
| Data Fabric / Data Service | Persistent mock operational data store for invoices, suppliers, POs, GRNs, cases, actions, rules, audit events, and demo metrics. |
| Agents | Assist with triage, root-cause classification, dispute summarization, payment risk assessment, supplier query interpretation, and next-best-action recommendations. |
| Coded Apps | Build the AP Control Tower, Case Workspace, Supplier 360, and Manager Dashboard demo screens. |
| Action Center / Action Apps | Provide human-in-the-loop tasks for AP review, GRN confirmation, procurement approval, payment hold release, and urgent payment approval. |
| Coded Action Apps | Provide richer action task UIs where the business reviewer needs invoice context, evidence, recommendations, and structured decision outputs. |
| API workflows | Simulate enterprise integrations with mock ERP, procurement, supplier portal, payment platform, and reporting endpoints. |
| RPA workflows | Simulate legacy and UI-based work such as AP mailbox triage, mock ERP update, supplier statement extraction, and payment screen update. |
| Orchestrator queues/assets | Manage background work items, credentials/configuration, job execution, and operational logs for the PoV. |
| Process Apps / dashboards | Provide visibility into process instances, cases, SLA performance, queue status, and exception volumes. |

### 5.1 Reference notes

This design is aligned with current UiPath platform concepts in public documentation:

- UiPath Maestro is described as a cloud-native orchestration platform that unifies automation, AI agents, and human interactions into end-to-end business processes.
- Maestro tasks can orchestrate robots, agents, API workflows, queues, and business rules.
- Data Fabric / Data Service provides persistent data storage and no-code data modeling capabilities for RPA projects.
- UiPath Apps supports enterprise custom applications connected to underlying systems through automation.
- UiPath Coded Apps allow browser-based web applications to be built through direct code development.
- Action Center supports human intervention in long-running workflows, and Action Apps support forms or UI interactions for tasks requiring human input.

Reference URLs are included in Appendix C.

---

## 6. Scope

### 6.1 In scope

| Area | In scope for PoV |
|---|---|
| Mock data | Mock invoices, suppliers, POs, GRNs, payments, users, cases, activities, rules, audit events, and supplier statements. |
| Case creation | Automatic conversion of aged/at-risk invoice exceptions into cases. |
| Case lifecycle | New, triaged, assigned, awaiting internal action, awaiting supplier, on hold, recommended for payment, approved, closed, reopened. |
| Triage | Rule-based and agent-assisted root-cause classification and priority scoring. |
| Workflow routing | Routing to AP, procurement, receiver/store/DC, finance, treasury, supplier contact, and AP lead. |
| Human actions | Approval and exception actions through Action Center/action apps. |
| Agents | Triage, summary, supplier query, payment risk, next-best-action recommendations. |
| API workflows | Mock APIs for ERP invoice status, procurement PO lookup, GRN lookup, payment status, and supplier portal updates. |
| RPA workflows | Mock ERP UI update, mailbox processing, statement reconciliation, and supplier notification. |
| Dashboard | AP control tower, case workspace, manager SLA dashboard, supplier 360. |
| Controls | Audit trail, reason codes, approval thresholds, duplicate checks, hold release controls, role-based actions. |
| Demo scripts | Personas and end-to-end demo scenarios for customer-facing walkthrough. |

### 6.2 Out of scope for PoV

| Area | Out of scope | Reason |
|---|---|---|
| Live Woolworths integrations | No connection to actual ERP, procurement, supplier, payment, banking, or email systems. | No source-system access for PoV. |
| Real supplier data | No real supplier invoices, statements, bank details, or contracts. | Privacy, security, and access constraints. |
| Actual payment execution | No real payment file generation or bank integration. | Risk and demo-only purpose. |
| Production tax validation | GST/tax checks are simulated. | Requires legal/tax validation and real master data. |
| Production security model | Basic role simulation only. | Full IAM design belongs in SDD. |
| Full exception universe | Focus on selected high-value exception scenarios. | Keep PoV build achievable and demo-friendly. |
| Full analytics platform | Demo dashboards only. | Enterprise BI design belongs in SDD/implementation. |
| Full process mining implementation | Simulated event log and dashboard patterns only. | Process mining requires real event logs for production value. |

---

## 7. Assumptions

| ID | Assumption |
|---|---|
| A-001 | The PoV is a demonstration, not a production deployment. |
| A-002 | All source-system data will be mocked and seeded into Data Fabric/Data Service or mock API services. |
| A-003 | No live customer credentials, supplier records, payment details, or invoice images will be used. |
| A-004 | The demo will represent a Woolworths-like retail AP process, not claim to replicate Woolworths' internal design. |
| A-005 | The case management process will use UiPath platform components available in the selected demo tenant. |
| A-006 | Maestro will act as the primary orchestration layer for the end-to-end process. |
| A-007 | Data Fabric/Data Service will hold mock operational entities and case state for the PoV. |
| A-008 | APIs will be mocked using lightweight services, local JSON endpoints, Data Fabric wrappers, or UiPath API workflows. |
| A-009 | RPA workflows will simulate interactions with legacy systems through mock web pages, desktop screens, spreadsheets, email inboxes, or generated PDFs. |
| A-010 | Agents will provide recommendations and summaries, but final payment-impacting decisions will require human approval in the demo. |
| A-011 | Coded Apps and action apps will be built for demo usability, not full production UX completeness. |
| A-012 | The PoV will prioritize storytelling, traceability, and process value over exhaustive ERP integration detail. |
| A-013 | The SDD will define implementation architecture, packages, repository structure, environment setup, authentication, CI/CD, deployment, and technical build details. |

---

## 8. Personas and Roles

| Persona | Demo role | Key activities in PoV | Primary screens/actions |
|---|---|---|---|
| AP Clerk | First-line case worker | Reviews aged invoices, validates triage, contacts supplier, resolves simple cases. | AP Control Tower, Case Workspace, AP Review Action. |
| AP Team Lead | Operations manager | Monitors backlog, reassigns cases, reviews SLA breaches, approves overrides. | Manager Dashboard, Case Reassignment, SLA Escalation View. |
| Procurement Officer | PO/price owner | Reviews price mismatches, validates PO terms, approves or disputes variance. | Price Mismatch Action App, Supplier 360. |
| Store/DC Receiver | Receipt owner | Confirms missing GRN or delivery discrepancy. | GRN Confirmation Action App. |
| Finance Manager | Governance reviewer | Reviews high-value cases, payment holds, and urgent payment recommendations. | Payment Hold Release Action, Urgent Payment Action. |
| Treasury User | Payment run owner | Reviews payment release recommendations and simulated payment status. | Payment Review Workspace. |
| Supplier Contact | External stakeholder | Receives mock status updates and provides missing evidence. | Simulated supplier portal / email response. |
| Internal Auditor | Control reviewer | Reviews audit trail, approvals, and case evidence. | Audit Timeline View. |
| Automation Support | Bot/process support | Reviews robot/API/agent execution logs and failed tasks. | Technical Monitoring View. |
| Demo Presenter | Story owner | Drives the narrative and switches personas during the customer demo. | All demo screens. |

---

## 9. Current-State Simulation

Because the PoV has no source-system access, the current state will be simulated using mock data and staged process artefacts. The simulated current state should make the pain visible before showing the UiPath target state.

### 9.1 Simulated current-state characteristics

| Current-state issue | How it will be simulated |
|---|---|
| Fragmented visibility | Mock invoice records have statuses scattered across `ERPStatus`, `ProcurementStatus`, `GRNStatus`, `PaymentStatus`, and `EmailStatus`. |
| Manual triage | Several invoices have ambiguous reason text such as `Blocked`, `Mismatch`, or `Needs review`. |
| Email chasing | Mock email records show AP follow-ups and supplier queries without structured case ownership. |
| Spreadsheet reporting | A static CSV file contains aged invoice rows with inconsistent reason codes. |
| Approval delay | Mock action records show overdue approver tasks. |
| Missing audit evidence | Some cases have unstructured notes rather than structured decisions. |
| Supplier frustration | Mock supplier portal/email query asks why invoices remain unpaid. |

### 9.2 Current-state demo setup

The demo can begin by showing a spreadsheet or simple mock report with aged invoices, for example:

| Invoice | Supplier | Amount | Days overdue | Status | Problem |
|---|---|---:|---:|---|---|
| INV-100472 | FreshHarvest Produce | 188,420 | 34 | Blocked | Missing GRN |
| INV-100511 | Metro Packaging Co | 92,800 | 48 | Mismatch | Price variance |
| INV-100533 | Southern Logistics | 241,300 | 12 | Hold | Payment hold |
| INV-100601 | Pacific Cleaning Services | 61,500 | 71 | Pending approval | Non-PO approval overdue |
| INV-100633 | Bright Dairy Supplies | 133,900 | 4 | Duplicate risk | Submitted by EDI and PDF |

The presenter then moves into the target process where these invoices are ingested, triaged, converted to cases, routed, worked, and closed.

---

## 10. Target Future-State PoV Process

### 10.1 Level 0 process

**Aged Invoice Case Management**

1. Ingest aged invoice candidates.
2. Enrich with mock ERP/procurement/GRN/payment data.
3. Classify exception and score priority.
4. Create or update case.
5. Route case to owner or action task.
6. Execute human, API, RPA, and agent steps.
7. Recommend resolution.
8. Approve payment/hold/rejection/partial payment.
9. Update mock systems and notify supplier.
10. Close case and update dashboards.

### 10.2 Level 1 process stages

| Stage | Name | Objective | Primary actor/component |
|---:|---|---|---|
| 1 | Aged invoice intake | Identify invoices that are aged, at risk, blocked, or disputed. | Maestro scheduled trigger, API workflow, RPA import. |
| 2 | Data enrichment | Gather supplier, PO, GRN, payment, hold, and statement context. | API workflows, Data Fabric. |
| 3 | Triage and prioritization | Classify root cause and calculate priority/SLA. | Triage Agent, business rules. |
| 4 | Case creation/update | Create case or update existing case. | Case Management, Data Fabric. |
| 5 | Routing | Assign owner, queue, action app, and escalation path. | Maestro, business rules. |
| 6 | Human resolution | Capture decisions from AP, procurement, receiver, finance, treasury. | Action Center / Coded Action Apps. |
| 7 | Automation execution | Update mock ERP, send supplier notification, reconcile statement, update payment status. | RPA/API workflows. |
| 8 | Risk and recommendation | Assess duplicate, tax, payment hold, bank change, and approval risks. | Payment Risk Agent, rules. |
| 9 | Closure | Close case with outcome, evidence, audit trail, and KPI update. | AP Clerk / AP Lead / Maestro. |
| 10 | Monitoring | Track SLA, bottlenecks, ageing trends, and demo value. | Process Apps, dashboards, event log. |

---

## 11. Detailed Process Design

### 11.1 Stage 1 - Aged invoice intake

**Trigger options for PoV:**

| Trigger | Description | Demo use |
|---|---|---|
| Scheduled daily run | Maestro starts a daily aged invoice review process. | Primary demo trigger. |
| Manual demo button | Presenter clicks `Run Daily Aged Invoice Review`. | Useful for live demo control. |
| Supplier query received | Mock supplier email/portal query triggers lookup and case creation. | Supplier query scenario. |
| SLA breach event | Existing case approaches or breaches SLA. | Escalation scenario. |
| Payment run pre-check | Payment candidate is checked for risk before release. | Payment control scenario. |

**Process steps:**

1. Retrieve unpaid invoices from mock ERP dataset.
2. Retrieve unresolved exceptions from mock AP exception dataset.
3. Retrieve supplier statement mismatches from uploaded mock statements.
4. Calculate days past due and ageing bucket.
5. Identify invoices that meet case criteria:
   - overdue by at least 1 day,
   - due within 7 days and blocked,
   - payment hold active,
   - duplicate risk score above threshold,
   - supplier dispute exists,
   - approval overdue,
   - high-value invoice with incomplete evidence.
6. Publish candidates to orchestration queue or directly to Maestro process instances.

**Business rules:**

| Rule ID | Rule |
|---|---|
| BR-IN-001 | Create a case if invoice is past due and not paid. |
| BR-IN-002 | Create a case if invoice is not yet due but has a blocking exception likely to breach SLA. |
| BR-IN-003 | Do not create duplicate case if an open case already exists for the invoice and supplier. |
| BR-IN-004 | Reopen case if supplier disputes a closed invoice and payment evidence is incomplete. |
| BR-IN-005 | Group invoices into one supplier statement case only when all invoices belong to the same supplier and same dispute type. |

### 11.2 Stage 2 - Data enrichment

**Objective:** Build a complete invoice context packet before triage.

| Data source | Mock method | Data retrieved |
|---|---|---|
| Mock ERP | API workflow or Data Fabric entity | Invoice header, line amount, posting status, payment status, holds. |
| Mock procurement | API workflow | PO header, PO lines, buyer, contract, price, tolerance. |
| Mock receiving / GRN | API workflow | Goods receipt number, received quantity, receiver, site, timestamp. |
| Mock supplier master | Data Fabric | Supplier name, type, payment terms, criticality, ABN, bank status. |
| Mock payment platform | API workflow | Payment run date, payment reference, failed payment reason. |
| Mock email/supplier portal | RPA/API workflow | Supplier query, attachments, dispute reason. |
| Mock document store | Data Fabric attachment metadata or generated files | Invoice PDF, delivery docket, supplier statement, remittance. |

**Output:** `InvoiceContext` object with normalized data for rules, agents, and case creation.

### 11.3 Stage 3 - Triage and prioritization

**Objective:** Determine root cause, priority, owner, SLA, and recommended next action.

**Triage inputs:**

- Days overdue.
- Invoice amount.
- Supplier criticality.
- Supplier type.
- PO status.
- GRN status.
- Price/quantity/tax variance.
- Duplicate score.
- Payment hold reason.
- Approval status.
- Supplier query status.
- Historical case pattern.

**Root cause hierarchy:**

1. Duplicate risk.
2. Payment hold / fraud / bank validation risk.
3. Missing or invalid supplier master data.
4. Missing PO or invalid PO.
5. Missing GRN or quantity mismatch.
6. Price mismatch.
7. Tax issue.
8. Approval delay.
9. Payment execution failure.
10. Supplier statement mismatch.
11. Other / manual review required.

**Priority scoring:**

| Factor | Example score contribution |
|---|---:|
| 90+ days overdue | +40 |
| 61-90 days overdue | +30 |
| 31-60 days overdue | +20 |
| 1-30 days overdue | +10 |
| Amount greater than AUD 250k | +25 |
| Critical supplier | +25 |
| Supplier dispute open | +15 |
| Payment hold risk | +20 |
| Duplicate risk high | +20 |
| Approval overdue | +10 |
| Due within 7 days and blocked | +10 |

**Priority bands:**

| Priority | Score | SLA |
|---|---:|---|
| Critical | 80+ | Same business day review |
| High | 60-79 | 1 business day |
| Medium | 35-59 | 3 business days |
| Low | 0-34 | 5 business days |

### 11.4 Stage 4 - Case creation and update

**Objective:** Create a structured case for every unresolved aged invoice requiring action.

**Case creation requirements:**

| Field | Requirement |
|---|---|
| Case ID | Unique case ID generated by the platform. |
| Case type | One of the standard exception types. |
| Primary invoice | Mandatory. |
| Related invoices | Optional for supplier statement or duplicate cases. |
| Supplier | Mandatory. |
| Owner queue | Derived from root cause. |
| Assigned user | Optional at creation; can be assigned by queue. |
| Priority | Derived from priority score. |
| SLA due date | Derived from priority and exception type. |
| Status | Starts as `New` or `Triaged`. |
| Recommended action | Generated by rules and/or agent. |
| Evidence pack | Invoice, PO, GRN, supplier query, statement, payment evidence. |
| Audit event | Case creation event recorded. |

### 11.5 Stage 5 - Routing

| Exception type | Default owner | Human action | Automation support |
|---|---|---|---|
| Missing GRN | Store/DC receiver | GRN Confirmation Action | API update to mock GRN system. |
| Price mismatch | Procurement officer | Price Variance Review Action | API lookup of PO/contract. |
| Approval delay | Business approver | Approval Action | Reminder/escalation workflow. |
| Duplicate risk | AP clerk | Duplicate Review Action | Duplicate investigation pack. |
| Payment hold | Finance manager / Treasury | Payment Hold Release Action | Payment risk assessment. |
| Supplier statement mismatch | AP reconciliation | Statement Reconciliation Action | RPA extraction and matching. |
| Supplier query | AP clerk | Supplier Response Review Action | Supplier Query Agent draft. |
| Urgent payment | AP lead + Finance + Treasury | Urgent Payment Review Action | Risk and controls pre-check. |

### 11.6 Stage 6 - Human resolution

Human users interact through action apps and case workspaces. Every action must return structured output, not only free-text comments.

| Action | Persona | Required inputs | Required outputs |
|---|---|---|---|
| AP Review Action | AP Clerk | Invoice context, exception reason, agent recommendation. | Confirm reason, assign owner, request info, close as duplicate, escalate. |
| GRN Confirmation Action | Store/DC Receiver | Invoice, PO, delivery details, supplier evidence. | Goods received yes/no, quantity, receipt date, comment, attachment. |
| Price Variance Review Action | Procurement Officer | Invoice line, PO price, contract price, variance. | Approve variance, reject, request credit note, update PO needed. |
| Payment Hold Release Action | Finance Manager | Hold reason, risk checks, invoice amount, supplier criticality. | Release hold, retain hold, escalate, require more evidence. |
| Urgent Payment Review Action | AP Lead / Finance / Treasury | Urgency reason, risk score, supplier status, bank validation status. | Approve urgent payment, reject, defer to next run. |
| Supplier Response Review Action | AP Clerk | Agent-drafted response, evidence, case status. | Send response, edit response, request more info, close. |

### 11.7 Stage 7 - Automation execution

| Workflow | Type | Purpose | Example output |
|---|---|---|---|
| `WF_LoadMockInvoices` | API/Data workflow | Load invoices from CSV or mock API into Data Fabric. | New/updated invoice records. |
| `WF_EnrichInvoiceContext` | API workflow | Query mock ERP, PO, GRN, supplier, payment data. | Normalized `InvoiceContext`. |
| `WF_CreateOrUpdateCase` | API/Data workflow | Create or update case entity and activity history. | Case ID and state. |
| `WF_SendSupplierNotification` | RPA/API workflow | Send mock email or portal update to supplier. | Notification event and email artifact. |
| `WF_UpdateMockERPHoldStatus` | RPA workflow | Simulate updating payment hold/release in a mock ERP UI. | Updated status screenshot/log. |
| `WF_ReconcileSupplierStatement` | RPA/document workflow | Extract statement lines and match to invoices/payments. | Matched/unmatched statement records. |
| `WF_GenerateAuditPack` | API/RPA workflow | Compile case evidence into demo audit pack. | Audit pack record/file. |
| `WF_CloseCase` | API/Data workflow | Update case status, resolution, closure reason, KPIs. | Closed case and audit event. |

### 11.8 Stage 8 - Resolution and payment recommendation

The process must support multiple outcomes:

| Outcome | Description | Required approval/control |
|---|---|---|
| Release for payment | Invoice is valid, matched, approved, and no holds remain. | AP/Treasury approval depending on value. |
| Retain hold | Invoice remains blocked due to unresolved risk. | Hold reason and next review date required. |
| Reject invoice | Supplier must resubmit corrected invoice or credit note. | AP reason code and supplier notification. |
| Partial payment | Undisputed amount can be released while disputed line remains open. | Finance/procurement approval. |
| Request credit note | Supplier must issue credit for price/quantity difference. | Procurement/AP decision. |
| Update PO/GRN | Internal data correction required before payment. | Owner confirmation and audit note. |
| Close as duplicate | Duplicate invoice rejected or merged. | Duplicate evidence required. |
| Escalate | Case cannot be resolved within SLA or requires senior decision. | Escalation reason and owner. |

### 11.9 Stage 9 - Closure

A case can be closed only when all mandatory closure fields are complete.

| Closure field | Requirement |
|---|---|
| Closure reason | Mandatory standard value. |
| Final payment status | Mandatory for paid/released cases. |
| Supplier communication status | Mandatory where supplier was involved. |
| Evidence pack | Mandatory for duplicate, payment hold, urgent payment, and rejection cases. |
| Final owner | Mandatory. |
| Resolution notes | Mandatory but should be concise and structured. |
| Audit event | Automatically recorded. |

---

## 12. Case Lifecycle Design

### 12.1 Case states

| State | Description | Entry condition | Exit condition |
|---|---|---|---|
| New | Candidate invoice identified. | Intake process creates case. | Triage completed. |
| Triaged | Root cause, priority, SLA, and owner proposed. | Triage rules/agent complete. | Owner accepts or routing creates action. |
| Assigned | Case assigned to user or team queue. | Routing complete. | User action started or automation begins. |
| Awaiting internal action | Waiting for AP/procurement/store/finance/treasury. | Action task created. | Action completed or escalated. |
| Awaiting supplier | Supplier information or corrected invoice needed. | Supplier communication sent. | Supplier responds or timeout occurs. |
| Automation in progress | API/RPA/agent workflow running. | Automation step triggered. | Workflow succeeds, fails, or requires human review. |
| On hold | Payment intentionally blocked. | Hold applied or retained. | Hold released or case closed as unresolved. |
| Recommended for payment | Resolution complete and payment release recommended. | Risk checks passed. | Payment approved or rejected. |
| Approved for payment | Human approval captured. | Required approvals complete. | Mock payment update succeeds. |
| Closed | Final outcome recorded. | Closure requirements met. | Reopened only by authorized user/event. |
| Reopened | Closed case reactivated due to supplier dispute or payment issue. | Supplier query or audit issue. | Case re-enters triage. |

### 12.2 Case status transition rules

| From | To | Rule |
|---|---|---|
| New | Triaged | Invoice context enrichment and classification complete. |
| Triaged | Assigned | Routing rule identifies owner queue. |
| Assigned | Awaiting internal action | Human task created. |
| Assigned | Automation in progress | Automation can resolve or enrich case. |
| Awaiting internal action | Recommended for payment | User approves resolution and controls pass. |
| Awaiting internal action | Awaiting supplier | User requests supplier evidence or corrected invoice. |
| Awaiting supplier | Assigned | Supplier response received. |
| Automation in progress | Assigned | Automation completes but human decision needed. |
| Automation in progress | Closed | Automation closes low-risk duplicate/status case where policy allows. |
| On hold | Recommended for payment | Hold released by authorized user. |
| Recommended for payment | Approved for payment | Required approvals complete. |
| Approved for payment | Closed | Mock payment status updated. |
| Closed | Reopened | Supplier dispute or audit exception received. |

### 12.3 Case audit timeline

Each case must show an audit timeline, including:

- Invoice candidate identified.
- Context enriched.
- Triage reason and confidence.
- Case created.
- Owner assigned.
- Human action created and completed.
- Agent recommendation generated.
- Automation workflow started/completed/failed.
- Supplier communication sent/received.
- Payment hold applied/released.
- Approval captured.
- Payment status updated.
- Case closed or reopened.

### 12.4 UiPath case plan outline for SDD handoff

This section defines the **process-level case plan** that should be translated into a UiPath Case Management `caseplan.json` during the SDD and build phases. It deliberately avoids implementation details such as task type IDs, field schemas, registry identifiers, exact bindings, expressions, selectors, and package structure.

The outline uses UiPath Case Management concepts from the case authoring skill:

- **Regular stages** are the main path from case intake to closure.
- **Exception stages** are secondary stages for escalation, automation failure, reopen, or risk handling.
- **Tasks** inside stages are typed at process level as `api-workflow`, `agent`, `action`, `rpa`, `wait-for-timer`, or `case-management` only where a true sub-case is required.
- **Edges and conditions** should be defined in the SDD from the entry/exit criteria below.
- **Exception stages** should be entered through interrupting entry conditions and should return to the originating regular stage after resolution, rather than being wired as normal stage-to-stage edges.
- **SLA rules** should be attached at case, stage, and action level where noted.

### 12.4.1 Human action experience and routing design

The PoV should demonstrate that Action Center tasks are not generic approval forms. Each human task should open a role-specific case workspace aligned to the **stage and task combination**. The business reviewer should see the evidence, recommendation, controls, decision options, and downstream impact relevant to that task.

For maintainability, the process design uses one normalized human decision contract:

| Contract area | Process-level meaning |
|---|---|
| Task identity | Stage ID, task ID, task purpose, persona, owner, and exception type identify which workbench variant is shown. |
| Decision input | Human decision, comments, evidence reference, optional amount/date/quantity/message fields. |
| Downstream signal | Next stage, case route, resolution path, supplier-input flag, escalation flag, payment-risk-hold flag, payment approval flag, and audit note. |
| Case effect | The case plan uses the downstream signal to decide whether to continue to exception work, supplier collaboration, payment risk, compliance hold, approval, closure, or rework. |

| Stage/task | Required UI character | Decision examples | Expected downstream effect |
|---|---|---|---|
| STG-03 Low-confidence triage review | Triage cockpit with agent confidence, root-cause candidates, evidence gaps, and owner recommendation. | Accept triage, reclassify, route to buyer/receiver, escalate. | Continue to AP ownership, return to enrichment, or create escalation. |
| STG-04 AP ownership review | AP ownership desk with queue, SLA, workload, and route choices. | Accept ownership, reassign owner queue, request context, escalate. | Open exception-resolution work, return to enrichment, or escalate. |
| STG-05 GRN confirmation | Store/DC receiver workspace with PO quantity, invoice quantity, received quantity, GRN/evidence checklist. | Goods received, partial receipt, not received, dispute supplier evidence. | Proceed to payment risk, request supplier evidence, or require approval. |
| STG-05 Price variance review | Commercial review workspace with PO price, invoice price, tolerance, category/buyer context. | Approve variance, reject, request credit note, update PO. | Proceed to payment risk, supplier collaboration, or approval. |
| STG-05 Payment hold review | Finance hold workspace with hold reason, risk flags, supplier criticality, payment calendar. | Release hold, retain hold, escalate to risk, schedule review. | Proceed to risk assessment or compliance hold. |
| STG-06 Supplier message review | Supplier communication workspace with agent-drafted message, editable text, requested evidence, and internal/supplier separation. | Send, request more information, do not send, escalate. | Send mock notification, wait for response, then return to exception work. |
| STG-07 High-risk payment review | Payment risk router with control result, risk score, recommendation, and unresolved payment controls. | Approve risk, retain hold, route to compliance. | Continue to approval or enter compliance risk hold. |
| STG-08 Approval tasks | Approval matrix with policy threshold, SoD/control flags, amount, urgent payment context, and closure impact. | Approve, reject, defer, approve urgent, reject urgent. | Close through mock update, request supplier/rework, or retain risk hold. |
| EXC stages | Exception-specific support workspaces for SLA, incident, reopen, and compliance review. | Reassign, retry, bypass, reopen, release/retain hold. | Return to originating stage or continue exception handling. |

### 12.5 Case plan stages

| Stage ID | Stage name | Stage type | Objective | Entry criteria | Exit criteria |
|---|---|---|---|---|---|
| STG-01 | Intake and Case Registration | Regular | Create or update the aged invoice case from a mocked invoice, supplier query, statement item, or payment-risk trigger. | Invoice candidate, supplier query, statement mismatch, or manual demo trigger received. | Case record exists with initial invoice, supplier, source, status, and audit event. |
| STG-02 | Context Enrichment and Evidence Assembly | Regular | Collect the mocked ERP, procurement, GRN, payment, hold, supplier, document, and communication context required for triage. | Case is registered and invoice reference is valid. | Invoice context packet and evidence pack are available or an integration incident is raised. |
| STG-03 | Triage, Classification, and Prioritisation | Regular | Classify root cause, score risk/priority, assign SLA, and propose next best action. | Enrichment complete. | Reason code, confidence, priority, SLA, owner queue, and recommended action are recorded. |
| STG-04 | AP Review and Ownership Acceptance | Regular | Let AP validate classification, accept ownership, reclassify, or route to the correct resolution path. | Triage complete or low-confidence triage requires review. | AP accepts or adjusts the case and routing decision is confirmed. |
| STG-05 | Exception Resolution Work | Regular | Execute the business-resolution task for the selected exception type, such as GRN, price, duplicate, approval, hold, statement, supplier information, tax, or master-data issue. | AP review confirms exception type and owner queue. | Required business decision or evidence is captured, or case moves to supplier wait/escalation. |
| STG-06 | Supplier Collaboration and Evidence Request | Regular | Handle supplier-facing messages, evidence requests, corrected invoice requests, credit-note requests, and supplier responses. | Resolution task requires supplier input or supplier query is active. | Supplier response is received, timed out, or no supplier action remains. |
| STG-07 | Payment Risk and Resolution Recommendation | Regular | Assess duplicate, hold, tax, bank-change, approval, dispute, and urgent-payment risk before payment recommendation. | Resolution evidence is available and invoice is a payment candidate. | Release, retain hold, reject, partial pay, request credit note, or escalate recommendation is recorded. |
| STG-08 | Approval and Payment Decision | Regular | Capture required AP, finance, procurement, and treasury decisions for payment-impacting outcomes. | Recommendation requires approval or payment-impacting decision. | Required approvals are complete, rejected, or escalated. |
| STG-09 | Mock System Update and Case Closure | Regular | Update mocked ERP/payment/supplier systems, generate audit evidence, close the case, and update KPIs. | Final decision is approved or non-payment closure is confirmed. | Case is closed with closure reason, final status, evidence, and audit trail. |
| EXC-01 | SLA Escalation and Reassignment | Exception | Handle overdue owner actions, breached stages, and manager escalation. | Stage or action SLA warning/breach condition occurs. | Case is reassigned, escalated, or returned to origin stage with updated due date and escalation history. |
| EXC-02 | Automation Incident Handling | Exception | Handle failed API, RPA, agent, or mock integration steps. | Automation retry is exhausted or critical integration failure occurs. | Support action completes, failed task is retried, skipped by approval, or returned to origin stage. |
| EXC-03 | Reopen and Supplier Dispute | Exception | Reopen a closed case when a supplier disputes closure, payment status, or remittance evidence. | Supplier dispute, statement mismatch, or audit issue references a closed case. | Case is reopened and returned to triage or closed again with new evidence. |
| EXC-04 | Compliance and Payment Risk Hold | Exception | Pause payment release for duplicate, tax, supplier bank, fraud, or policy-control risk. | Payment Risk Agent or rules identify unresolved high-risk flag. | Hold is retained with review date or released by authorized user and returned to origin stage. |

### 12.6 Tasks by stage

The following table is the case-plan task outline for the PoV. The SDD should convert each row into the concrete case task, resource reference, input/output mapping, and conditions.

| Stage | Task ID | Task name | UiPath task type | Primary owner/component | Trigger condition | Business output |
|---|---|---|---|---|---|---|
| STG-01 | T-01-01 | Start aged invoice case | `api-workflow` | Mock ERP / Data Fabric | Daily review, manual demo start, supplier query, statement mismatch, or payment pre-check. | Invoice candidate loaded and case start event captured. |
| STG-01 | T-01-02 | Check existing open case | `api-workflow` | Data Fabric | Invoice candidate received. | Existing case updated or new case allowed. |
| STG-01 | T-01-03 | Register case shell | `api-workflow` | Case Management / Data Fabric | No open case exists, or existing case is eligible for update. | Case ID, source type, initial status, invoice link, supplier link, and audit event. |
| STG-01 | T-01-04 | Set initial owner queue | `api-workflow` | Maestro / rules | Case shell exists. | Initial owner queue such as AP Intake, AP Reconciliation, or Payment Risk Review. |
| STG-02 | T-02-01 | Retrieve mock ERP invoice status | `api-workflow` | Mock ERP Finance | Registered invoice has ERP reference. | Posting status, payment status, hold status, due date, amount, and ledger status. |
| STG-02 | T-02-02 | Retrieve mock PO and contract context | `api-workflow` | Mock Procurement | Invoice has PO or category requiring PO lookup. | PO status, buyer, line price, tolerance, contract, category, business unit. |
| STG-02 | T-02-03 | Retrieve mock GRN or service entry context | `api-workflow` | Mock Receiving / GRN | Invoice is PO-backed or service-entry-backed. | Receipt status, quantity, site, receiver, receipt timestamp. |
| STG-02 | T-02-04 | Retrieve supplier and payment risk context | `api-workflow` | Supplier master / payment mock | Supplier ID exists. | Supplier criticality, terms, ABN, bank validation, small-supplier flag, active/block status. |
| STG-02 | T-02-05 | Assemble evidence pack | `api-workflow` | Data Fabric / document mock | Core lookups complete. | Invoice image reference, PO, GRN, payment, statement, email, and prior-case evidence list. |
| STG-02 | T-02-06 | Raise enrichment incident | `action` | Automation Support | Required mocked data lookup fails after retry. | Support decision to retry, bypass for demo, or mark data unavailable. |
| STG-03 | T-03-01 | Run Invoice Triage Agent | `agent` | Triage Agent | Evidence pack is available. | Proposed reason code, confidence, priority rationale, and next best action. |
| STG-03 | T-03-02 | Apply deterministic exception rules | `api-workflow` | Business rules | Triage agent output exists. | Rule-confirmed duplicate, hold, PO, GRN, price, approval, tax, or payment flags. |
| STG-03 | T-03-03 | Calculate priority and SLA | `api-workflow` | Maestro / rules | Reason code and risk factors available. | Priority band, SLA due date, escalation profile, at-risk flag. |
| STG-03 | T-03-04 | Low-confidence triage review | `action` | AP Clerk | Agent confidence is below threshold or rule conflict exists. | Confirmed/reclassified reason code and owner queue. |
| STG-04 | T-04-01 | AP ownership review | `action` | AP Clerk | Case is triaged. | AP accepts classification, assigns owner, requests more information, or escalates. |
| STG-04 | T-04-02 | Update case route | `api-workflow` | Case Management / Data Fabric | AP review complete or auto-route allowed. | Case status, owner queue, assigned user/team, next action. |
| STG-04 | T-04-03 | Generate case summary for workspace | `agent` | Dispute Summarization Agent | Case routed to human owner. | Human-readable summary, unresolved issues, evidence highlights. |
| STG-05 | T-05-01 | GRN confirmation | `action` | Store/DC Receiver | Reason is missing GRN or quantity mismatch. | Receipt confirmed, rejected, partially confirmed, or more evidence requested. |
| STG-05 | T-05-02 | Price variance review | `action` | Procurement Officer | Reason is price mismatch outside tolerance. | Approve variance, request credit note, update PO, or reject invoice. |
| STG-05 | T-05-03 | Non-PO approval review | `action` | Business Approver | Reason is approval overdue or non-PO approval required. | Approve, reject, delegate, or request more information. |
| STG-05 | T-05-04 | Duplicate investigation | `action` | AP Clerk | Exact or probable duplicate flag exists. | Close duplicate, merge, false-positive release, or escalate. |
| STG-05 | T-05-05 | Payment hold review | `action` | Finance Manager / Treasury | Payment hold is active or due for review. | Release hold, retain hold, escalate, or request risk review. |
| STG-05 | T-05-06 | Supplier statement reconciliation | `rpa` | AP Reconciliation Bot | Case originates from statement mismatch or uploaded statement. | Matched, unmatched, already paid, missing invoice, or disputed statement line. |
| STG-05 | T-05-07 | Tax or supplier master review | `action` | AP Specialist / Master Data | Tax issue, inactive supplier, blocked vendor, or bank validation issue. | Corrected data requested, exception approved, or payment blocked. |
| STG-05 | T-05-08 | Update mock ERP/GRN outcome | `rpa` | Mock ERP Bot | Human decision requires legacy-style update. | Mock ERP/GRN hold, receipt, match, or status update logged. |
| STG-06 | T-06-01 | Draft supplier message | `agent` | Supplier Query Agent | Supplier input or communication required. | Draft status update, evidence request, rejection note, or credit-note request. |
| STG-06 | T-06-02 | Review supplier message | `action` | AP Clerk | Draft message is supplier-facing. | Approved/edited message, send decision, communication reason. |
| STG-06 | T-06-03 | Send mock supplier notification | `api-workflow` or `rpa` | Mock supplier portal / mailbox | Message approved or template auto-send allowed. | Supplier communication event and outbound artifact. |
| STG-06 | T-06-04 | Wait for supplier response | `wait-for-timer` | Maestro | Supplier evidence is requested. | Response due date reached or demo-simulated supplier reply available. |
| STG-06 | T-06-05 | Process supplier response | `rpa` or `api-workflow` | Mock AP Mailbox / Supplier Portal | Supplier response is received. | Evidence attached, invoice corrected, dispute updated, or timeout escalated. |
| STG-07 | T-07-01 | Run Payment Risk Agent | `agent` | Payment Risk Agent | Resolution evidence suggests payment, partial payment, hold release, or urgent payment. | Release/hold/reject/partial-pay recommendation with risk flags. |
| STG-07 | T-07-02 | Run payment control pre-check | `api-workflow` | Rules / payment mock | Payment recommendation exists. | Duplicate, tax, bank, hold, approval, supplier, and SoD control result. |
| STG-07 | T-07-03 | Generate resolution recommendation | `agent` | Resolution Recommendation Agent | Risk pre-check complete. | Recommended final outcome and checklist. |
| STG-07 | T-07-04 | Route high-risk hold | `action` | Finance Manager / Risk | Any high-risk payment flag remains unresolved. | Hold retained, hold released, or escalated to treasury/risk. |
| STG-08 | T-08-01 | AP lead approval | `action` | AP Team Lead | Amount, age, or policy threshold requires AP lead approval. | Approve, reject, defer, request more evidence. |
| STG-08 | T-08-02 | Procurement or finance approval | `action` | Procurement / Finance | Price variance, partial pay, credit note, tax, or high-value threshold applies. | Approved business decision or rejection. |
| STG-08 | T-08-03 | Treasury urgent payment decision | `action` | Treasury User | Urgent or out-of-cycle payment requested. | Approve urgent payment, defer to next run, or reject. |
| STG-08 | T-08-04 | Final decision consolidation | `api-workflow` | Case Management / rules | Required approvals complete. | Final case outcome selected and required closure controls checked. |
| STG-09 | T-09-01 | Update mock payment or invoice status | `api-workflow` or `rpa` | Mock ERP / payment platform | Final decision requires mocked system update. | Scheduled, paid, rejected, hold retained, credit note requested, or partial-pay status. |
| STG-09 | T-09-02 | Generate audit pack | `api-workflow` | Data Fabric / document mock | Case outcome is ready for closure. | Audit evidence summary, activity list, approval list, agent outputs, automation log. |
| STG-09 | T-09-03 | Send closure notification | `api-workflow` or `rpa` | Supplier portal / AP mailbox | Supplier communication required at closure. | Closure, rejection, payment, hold, or evidence-request notification event. |
| STG-09 | T-09-04 | Close case and update KPIs | `api-workflow` | Case Management / Data Fabric | Closure checklist complete. | Case closed, closure reason recorded, dashboard metrics updated. |
| EXC-01 | T-E01-01 | SLA warning timer | `wait-for-timer` | Maestro | Stage/action approaches SLA breach. | Warning event and reminder activity. |
| EXC-01 | T-E01-02 | Escalation review | `action` | AP Team Lead / Manager | SLA breached or repeated reminders ignored. | Reassign, extend SLA, escalate, or return to origin. |
| EXC-02 | T-E02-01 | Automation support review | `action` | Automation Support | API/RPA/agent task fails after retry. | Retry, skip for demo, manual update, or incident closure. |
| EXC-02 | T-E02-02 | Retry failed automation | `api-workflow` or `rpa` | Failed automation owner | Support approves retry. | Successful retry or confirmed unresolved incident. |
| EXC-03 | T-E03-01 | Reopen case review | `action` | AP Lead | Supplier disputes closure or payment evidence after closure. | Reopen and return to triage, reject reopen, or add evidence and re-close. |
| EXC-04 | T-E04-01 | Compliance risk review | `action` | Finance / Risk / Treasury | High-risk flag blocks payment recommendation. | Release with approval, retain hold, request more evidence, or escalate. |

### 12.7 Main stage flow and branching logic

| Flow segment | Routing pattern | Condition |
|---|---|---|
| Intake to enrichment | STG-01 -> STG-02 | Case shell created or existing case updated. |
| Enrichment to triage | STG-02 -> STG-03 | Required context available. |
| Enrichment to incident handling | Interrupting entry into EXC-02, then return to origin | Required mock integration or evidence retrieval fails after retry. |
| Triage to AP review | STG-03 -> STG-04 | Classification completed, or low confidence requires review. |
| AP review to exception resolution | STG-04 -> STG-05 | AP confirms owner and exception path. |
| Exception resolution to supplier collaboration | STG-05 -> STG-06 | Supplier evidence, corrected invoice, credit note, or status response required. |
| Exception resolution to payment risk | STG-05 -> STG-07 | Internal resolution complete and payment/closure recommendation can be assessed. |
| Supplier collaboration to exception resolution | STG-06 -> STG-05 | Supplier response changes the resolution work required. |
| Supplier collaboration to payment risk | STG-06 -> STG-07 | Supplier response resolves required evidence. |
| Payment risk to approval | STG-07 -> STG-08 | Recommendation requires approval, urgent payment decision, partial payment, hold release, or rejection approval. |
| Payment risk to compliance hold | Interrupting entry into EXC-04, then return to origin | Unresolved duplicate, tax, bank, fraud, SoD, or payment-hold risk remains. |
| Approval to closure | STG-08 -> STG-09 | Final decision captured and controls pass. |
| Any active stage to SLA escalation | Interrupting entry into EXC-01, then return to origin | Stage/action SLA warning or breach fires. |
| Closed to reopen | Interrupting entry into EXC-03, then return to triage if reopened | Supplier dispute, statement mismatch, payment failure, or audit issue references closed case. |

At process level, all human decisions should emit normalized downstream signals. The SDD and build should map those signals into concrete Case Management variables and entry/exit conditions without hard-coding business logic into UI text.

### 12.8 Stage-level SLA and ownership outline

| Stage | Default owner | Stage SLA | Escalation path |
|---|---|---:|---|
| STG-01 Intake and Case Registration | AP Intake / Automation | Same business day | Automation Support if registration fails. |
| STG-02 Context Enrichment and Evidence Assembly | Automation / AP | Same business day | Automation Support, then AP Lead. |
| STG-03 Triage, Classification, and Prioritisation | AP Operations | Same business day | AP Lead if low-confidence cases queue for more than 4 business hours. |
| STG-04 AP Review and Ownership Acceptance | AP Clerk | 1 business day | AP Team Lead. |
| STG-05 Exception Resolution Work | Exception owner queue | 1-5 business days by reason code | Store/DC manager, procurement manager, finance manager, or AP Lead. |
| STG-06 Supplier Collaboration and Evidence Request | AP Clerk / Supplier | 5 business days | AP Lead and supplier relationship owner. |
| STG-07 Payment Risk and Resolution Recommendation | Finance / Treasury / AP | Same business day for urgent, 1 business day otherwise | Finance Manager and Treasury Lead. |
| STG-08 Approval and Payment Decision | AP Lead / Finance / Treasury | Same business day for urgent, 2 business days otherwise | Finance leadership for high-value or overdue approval. |
| STG-09 Mock System Update and Case Closure | AP Clerk / Automation | Same business day | AP Lead and Automation Support. |
| EXC-01 SLA Escalation and Reassignment | AP Lead | Same business day | Finance Operations Manager. |
| EXC-02 Automation Incident Handling | Automation Support | Same business day | Automation CoE Lead. |
| EXC-03 Reopen and Supplier Dispute | AP Lead | 1 business day | Finance Manager. |
| EXC-04 Compliance and Payment Risk Hold | Finance / Risk / Treasury | Same business day for urgent, 2 business days otherwise | Finance Manager / Risk Lead. |

### 12.9 Minimum viable case plan for the first demo

For the first demonstrable PoV, the case plan can be reduced to the following minimum without losing the core story:

| Minimum stage | Required tasks |
|---|---|
| STG-01 Intake and Case Registration | Start aged invoice case, check existing open case, register case shell. |
| STG-02 Context Enrichment | Retrieve ERP status, retrieve PO/GRN context, assemble evidence pack. |
| STG-03 Triage | Run Invoice Triage Agent, calculate priority and SLA. |
| STG-04 AP Review | AP ownership review, update case route. |
| STG-05 Exception Resolution | GRN confirmation and price variance review as the first two action apps. |
| STG-07 Payment Risk | Run Payment Risk Agent, run payment control pre-check. |
| STG-08 Approval | AP lead approval and treasury urgent payment decision. |
| STG-09 Closure | Update mock payment status, generate audit pack, close case and update KPIs. |
| EXC-01 SLA Escalation | SLA warning timer and escalation review. |
| EXC-02 Automation Incident Handling | Automation support review. |

This MVP gives the demo a complete case backbone while leaving supplier statement reconciliation, tax/master-data review, reopen handling, and advanced compliance hold handling as second-wave additions.

---

## 13. Data Design for PoV

### 13.1 Data Fabric / Data Service entities

The following entities are required for the PoV. Final field names and data types belong in the SDD, but the PDD defines the business data model.

| Entity | Purpose | Key fields |
|---|---|---|
| `Invoice` | Core invoice record. | InvoiceId, InvoiceNumber, SupplierId, InvoiceDate, DueDate, Amount, Currency, AgeingBucket, DaysOverdue, Status, PaymentStatus, ExceptionReasonCode. |
| `Supplier` | Supplier master simulation. | SupplierId, SupplierName, ABN, SupplierType, Criticality, PaymentTerms, BankValidationStatus, ContactEmail. |
| `PurchaseOrder` | PO header simulation. | POId, PONumber, SupplierId, BuyerId, Status, BusinessUnit, ContractId, TotalAmount. |
| `PurchaseOrderLine` | PO line details. | POLineId, POId, ItemCode, Description, QuantityOrdered, UnitPrice, TaxCode. |
| `GoodsReceipt` | Goods receipt/service entry simulation. | GRNId, PONumber, SiteId, ReceivedQuantity, ReceiptDate, ReceiverId, Status. |
| `Payment` | Payment status simulation. | PaymentId, InvoiceId, PaymentRunDate, PaymentReference, PaymentStatus, FailureReason. |
| `PaymentHold` | Payment hold records. | HoldId, InvoiceId, HoldReason, HoldOwner, HoldStatus, ReviewDate, ReleasedBy. |
| `AgedInvoiceCase` | Main case record. | CaseId, InvoiceId, SupplierId, CaseType, Priority, Score, Status, OwnerQueue, AssignedUser, SLADueDate, ClosureReason. |
| `CaseActivity` | Case timeline and notes. | ActivityId, CaseId, ActivityType, Actor, Timestamp, Summary, Details, Source. |
| `CaseEvidence` | Evidence and attachments. | EvidenceId, CaseId, EvidenceType, FileName, Source, Link, UploadedBy. |
| `ActionTask` | Human-in-the-loop task tracking. | ActionId, CaseId, ActionType, AssignedTo, Priority, DueDate, Status, Decision, CompletedAt. |
| `SupplierStatement` | Supplier statement header. | StatementId, SupplierId, StatementDate, UploadedBy, Status. |
| `SupplierStatementLine` | Statement line matching. | StatementLineId, StatementId, InvoiceNumber, Amount, SupplierStatus, MatchStatus, MatchedInvoiceId. |
| `ExceptionReason` | Standard exception taxonomy. | ReasonCode, ReasonName, DefaultOwnerQueue, DefaultSLA, RiskCategory. |
| `ApprovalMatrix` | Demo approval rules. | RuleId, BusinessUnit, AmountFrom, AmountTo, RequiredRole, RequiredApprover. |
| `UserProfile` | Demo personas and routing. | UserId, Name, Role, Team, BusinessUnit, DelegationUserId, ActiveFlag. |
| `AuditEvent` | Control and audit event log. | AuditId, EntityType, EntityId, EventType, Actor, Timestamp, BeforeValue, AfterValue, ReasonCode. |
| `MockIntegrationLog` | API/RPA/agent execution visibility. | LogId, WorkflowName, CaseId, Status, StartTime, EndTime, ErrorMessage. |

### 13.2 Mock dataset requirements

| Data area | Minimum PoV dataset | Recommended richer dataset |
|---|---:|---:|
| Suppliers | 25 | 75-100 |
| Invoices | 150 | 750-1,500 |
| Aged invoices | 40 | 200-300 |
| Purchase orders | 80 | 500 |
| Goods receipts | 60 | 400 |
| Payment records | 100 | 1,000 |
| Open cases | 20 | 80-120 |
| Closed historical cases | 30 | 300 |
| Supplier statement lines | 50 | 500 |
| Demo users | 10 | 25 |

### 13.3 Mock data segmentation

| Segment | Target distribution for realistic demo |
|---|---:|
| 0-30 days overdue | 45% of aged invoices |
| 31-60 days overdue | 25% |
| 61-90 days overdue | 15% |
| 90+ days overdue | 15% |
| Missing GRN | 25% of exceptions |
| Price mismatch | 20% |
| Approval delay | 15% |
| Payment hold | 10% |
| Duplicate risk | 10% |
| Supplier statement mismatch | 10% |
| Other/tax/master data | 10% |

### 13.4 Sample mock suppliers

Use fictional supplier names that feel retail-relevant but do not represent actual supplier relationships.

| Supplier | Type | Criticality | Typical issue |
|---|---|---|---|
| FreshHarvest Produce Pty Ltd | Fresh produce | Critical | Missing GRN / quantity mismatch. |
| Bright Dairy Supplies Pty Ltd | Trade goods | High | Duplicate invoice risk. |
| Metro Packaging Co | Packaging | Medium | Price mismatch. |
| Southern Logistics Services | Logistics | Critical | Payment hold / urgent payment. |
| Pacific Cleaning Services | Store services | Medium | Non-PO approval delay. |
| CoreTech POS Support | Technology services | High | Approval and contract validation. |
| GreenShelf Merchandising | Merchandising services | Medium | Supplier statement mismatch. |

---

## 14. Mock Source Systems and Interfaces

### 14.1 Mock systems

| Mock system | Purpose | Implementation option |
|---|---|---|
| Mock ERP Finance | Invoice posting, payment status, holds, GL status. | Data Fabric entity plus API workflow; optional mock web UI for RPA. |
| Mock Procurement | PO, contract, buyer, pricing, tolerance data. | Mock REST endpoint/API workflow. |
| Mock Receiving / GRN | Goods receipt and service entry status. | Data Fabric entity and API workflow. |
| Mock Supplier Portal | Supplier query and evidence submission. | Coded App screen or simple mock endpoint. |
| Mock Payment Platform | Payment run, payment reference, failed payment reason. | API workflow and mock payment table. |
| Mock AP Mailbox | Supplier emails and invoice attachments. | Outlook test mailbox, local `.eml` files, or generated mock messages. |
| Mock Document Store | Invoice PDFs, delivery dockets, statements. | Folder storage, storage bucket, or Data Fabric attachment metadata. |
| Mock BI/Event Log | KPI and process event view. | Process App/dashboard backed by case and event data. |

### 14.2 Interface pattern by process step

| Step | Preferred pattern for PoV | Why |
|---|---|---|
| Load aged invoices | API workflow or Data Fabric import | Fast, deterministic, demo-friendly. |
| Query PO details | API workflow | Demonstrates API automation and system integration. |
| Query GRN | API workflow | Shows structured integration. |
| Update payment hold | RPA workflow against mock ERP UI | Demonstrates UI automation for legacy systems. |
| Send supplier update | API or RPA email workflow | Demonstrates controlled supplier communication. |
| Read supplier statement | RPA/document workflow | Demonstrates document and reconciliation automation. |
| Create human task | Action Center/action app | Demonstrates human-in-the-loop. |
| Orchestrate lifecycle | Maestro | Demonstrates end-to-end control. |

---

## 15. Agent Design at Process Level

### 15.1 Agent roles

| Agent | Purpose | Inputs | Outputs | Human guardrail |
|---|---|---|---|---|
| Invoice Triage Agent | Classify root cause and suggest priority. | Invoice context, PO/GRN/payment data, notes, exception history. | Reason code, confidence, priority rationale, next action. | Low-confidence or high-risk results require AP review. |
| Supplier Query Agent | Interpret supplier email/portal query and identify relevant invoice/case. | Supplier message, invoice numbers, statement lines, case history. | Matched invoice/case, response draft, evidence request. | Human approves supplier-facing response. |
| Dispute Summarization Agent | Summarize case history and dispute evidence. | Activities, supplier messages, PO/GRN/payment data, attachments metadata. | Concise summary, timeline, unresolved issues. | Human validates summary before decision. |
| Payment Risk Agent | Assess whether invoice can be released for payment. | Duplicate score, hold status, bank validation, tax flag, approvals, amount. | Release/hold/reject recommendation, risk flags. | Payment-impacting decisions require approval. |
| Resolution Recommendation Agent | Recommend closure path. | Full case context and business rules. | Recommended outcome and checklist. | User must select final outcome. |

### 15.2 Agent output structure

All agent outputs should be structured, not free-form only.

| Field | Description |
|---|---|
| `recommendation` | Recommended next action. |
| `reasonCode` | Standard reason code. |
| `confidence` | 0-100 confidence score. |
| `riskFlags` | List of risks such as duplicate, payment hold, tax issue, bank validation. |
| `evidenceReferences` | Invoice/PO/GRN/case records used. |
| `humanReviewRequired` | Boolean. |
| `summaryForUser` | Short explanation for business user. |
| `draftSupplierMessage` | Optional supplier-facing draft. |

### 15.3 Agent guardrails

| Guardrail | Requirement |
|---|---|
| No autonomous payment release | Agents can recommend but not independently approve payment release. |
| Evidence required | Recommendations must reference data used to reach the recommendation. |
| Confidence threshold | Below threshold, route to AP review. |
| Supplier communication review | Supplier-facing messages must be approved or use approved templates. |
| Audit logging | Agent input/output, user edits, and final action must be logged. |
| Data minimization | Agents should only receive the case data needed for their task. |

---

## 16. Human Action and UX Design

### 16.1 Coded Apps / app screens

| Screen | Users | Purpose | Key elements |
|---|---|---|---|
| AP Control Tower | AP Clerk, AP Lead, Finance | Operational landing page for aged invoice cases. | KPI tiles, ageing buckets, priority queue, filters, case list, SLA alerts. |
| Case Workspace | AP Clerk, AP Lead, Audit | Work a single invoice case. | Case header, invoice context, agent recommendation, evidence, actions, timeline, decision panel. |
| Supplier 360 | AP, Procurement, Finance | Supplier-level view of aged exposure and disputes. | Supplier summary, outstanding invoices, open cases, payment terms, risk flags, statement mismatches. |
| Manager Dashboard | AP Lead, Finance Manager | Manage backlog, SLAs, workload, escalations. | SLA breaches, owner queues, root causes, trend charts, reassignment panel. |
| Demo Admin Console | Demo Presenter | Reset data, seed scenarios, start process, toggle mock outcomes. | Scenario selector, reset button, process trigger, mock API failure toggles. |

### 16.2 Action apps

| Action app | Trigger | Main decision buttons |
|---|---|---|
| AP Review Action | New case needs AP validation. | Confirm reason, reclassify, request supplier info, assign, close duplicate. |
| GRN Confirmation Action | Missing GRN or quantity mismatch. | Confirm receipt, reject receipt, partial receipt, request more evidence. |
| Price Variance Review Action | Price mismatch outside tolerance. | Approve variance, reject invoice, request credit note, update PO. |
| Approval Delay Action | Non-PO invoice awaiting approval. | Approve, reject, delegate, request more information. |
| Payment Hold Release Action | Hold due for review or release requested. | Release hold, retain hold, escalate, request risk review. |
| Urgent Payment Action | Critical supplier requests urgent payment. | Approve urgent payment, defer, reject, escalate. |
| Supplier Response Review Action | Supplier response drafted by agent. | Send, edit, request more info, close case. |

### 16.3 UX principles

1. Users should not need to know which mock system holds the data.
2. Every case should present a clear `next best action`.
3. Agent recommendations should be visible but not hidden behind automation.
4. High-risk decisions should show the reason human review is required.
5. The case timeline should make the audit story obvious.
6. Demo screens should emphasize process value, not only technology features.

---

## 17. Business Rules and SLA Design

### 17.1 Ageing rules

| Rule ID | Rule |
|---|---|
| AGE-001 | Days overdue = current business date minus invoice due date. |
| AGE-002 | Ageing bucket values: Not due, Due in 7 days, 0-30, 31-60, 61-90, 90+. |
| AGE-003 | Invoices due within 7 days with blocking exception are marked `At Risk`. |
| AGE-004 | Paid invoices are excluded from aged backlog unless supplier dispute remains open. |

### 17.2 SLA rules

| Case type | Default SLA | Escalation |
|---|---:|---|
| Missing GRN | 2 business days | Store/DC manager after SLA breach. |
| Price mismatch | 3 business days | Procurement manager after SLA breach. |
| Duplicate risk | 1 business day | AP lead after 1 day. |
| Approval delay | 2 business days | Approver manager after 2 reminders. |
| Payment hold | Review every 7 calendar days | Finance manager if review missed. |
| Supplier statement mismatch | 5 business days | AP reconciliation lead. |
| Urgent payment request | Same business day | AP lead + Finance + Treasury. |

### 17.3 Approval rules

| Rule ID | Rule |
|---|---|
| APR-001 | Payment-impacting decisions above AUD 100,000 require AP lead or finance manager approval in the PoV. |
| APR-002 | Urgent payment requests require AP lead, finance, and treasury approval in the PoV. |
| APR-003 | Duplicate-risk invoices cannot be released until duplicate review is completed. |
| APR-004 | Payment holds cannot be released without hold owner approval. |
| APR-005 | Price variances outside tolerance require procurement approval. |
| APR-006 | Manual override requires reason code and comment. |

### 17.4 Tolerance rules

| Rule ID | Rule |
|---|---|
| TOL-001 | Price variance <= 2% or AUD 500 can be auto-marked as within tolerance for demo. |
| TOL-002 | Price variance above tolerance routes to procurement. |
| TOL-003 | Quantity variance above 0 requires receiver confirmation. |
| TOL-004 | Tax mismatch is routed to AP specialist in the PoV but not fully implemented for production tax logic. |

---

## 18. Exception Taxonomy for PoV

| Code | Exception reason | Default owner | Demo scenario |
|---|---|---|---|
| EX-GRN-001 | Missing goods receipt | Store/DC receiver | DC delivery not receipted. |
| EX-GRN-002 | Quantity mismatch | Store/DC receiver | Partial receipt. |
| EX-PRICE-001 | Price mismatch | Procurement officer | Invoice price exceeds PO price. |
| EX-APP-001 | Approval overdue | Business approver | Non-PO services invoice pending. |
| EX-DUP-001 | Exact duplicate risk | AP clerk | Same invoice via EDI and PDF. |
| EX-DUP-002 | Probable duplicate risk | AP clerk | Similar invoice number/amount/date. |
| EX-HOLD-001 | Payment hold active | Finance/Treasury | Hold due for review. |
| EX-SUP-001 | Supplier information required | Supplier/AP | Missing delivery evidence. |
| EX-STAT-001 | Supplier statement mismatch | AP reconciliation | Statement says unpaid but ERP says paid. |
| EX-PAY-001 | Payment execution failure | Treasury | Mock payment run failed. |
| EX-TAX-001 | Tax validation issue | AP/Tax specialist | GST/tax data missing in mock invoice. |
| EX-MD-001 | Supplier master issue | Master data/AP | Supplier blocked or bank validation pending. |

---

## 19. Reporting and KPI Requirements for PoV

### 19.1 Dashboard KPIs

| KPI | Definition | Demo target |
|---|---|---|
| Total aged invoice value | Sum of unpaid overdue invoices. | Show before/after reduction after cases close. |
| Aged invoice count | Count of unpaid overdue invoices. | Filter by bucket, supplier, owner. |
| Cases by status | Count by New, Triaged, Assigned, Awaiting, On Hold, Closed. | Demonstrate case lifecycle. |
| SLA breach count | Cases past SLA due date. | Trigger escalation scenario. |
| Average case age | Average days since case creation. | Show operational visibility. |
| Root cause breakdown | Cases by exception reason. | Highlight process insights. |
| Priority distribution | Critical, High, Medium, Low. | Show risk-based work management. |
| Agent assist rate | Percent of cases with agent recommendation. | Demonstrate agentic value. |
| Automation completion rate | Percent of cases with API/RPA completion. | Demonstrate automation value. |
| Manual review required | Cases requiring human approval. | Show controlled automation. |
| Supplier dispute volume | Open supplier-related cases. | Supplier experience story. |
| Payment release recommended | Value of cases ready for payment. | Payment control story. |

### 19.2 Report views

| View | Audience | Filters |
|---|---|---|
| Aged Invoice Overview | Finance/AP | Ageing bucket, supplier, BU, exception, value. |
| Case Operations | AP Lead | Owner, SLA, priority, status, action type. |
| Supplier Exposure | Procurement/AP | Supplier, criticality, statement mismatch, dispute status. |
| Control Exceptions | Risk/Audit | Payment holds, duplicate risk, urgent payments, overrides. |
| Automation Monitor | Automation Support | Workflow, run status, errors, retry count. |

---

## 20. Controls and Compliance Design for PoV

The PoV will simulate controls that matter in production without connecting to real payment systems.

| Control | PoV implementation |
|---|---|
| Segregation of duties | Demo roles restrict who can approve, release hold, and close cases. |
| Approval thresholds | Rules require finance/AP lead approval for high-value or urgent cases. |
| Duplicate prevention | Duplicate score and evidence pack block payment recommendation. |
| Payment hold governance | Holds require owner, reason, review date, and release approval. |
| Audit trail | Every case state change and decision creates `AuditEvent` and `CaseActivity`. |
| Supplier communication control | Agent-generated messages require human review before sending. |
| Manual override | Reason code, comment, and evidence required. |
| Mock bank/payment safety | No real bank details or real payment file generation. |
| Data privacy | Fictional supplier and invoice data only. |
| AI governance | Agent outputs are recommendations, not autonomous final decisions. |

---

## 21. Demo Scenarios

### 21.1 Scenario 1 - Missing GRN for critical fresh supplier

| Step | Demo action | Capability shown |
|---:|---|---|
| 1 | Daily aged invoice review identifies invoice 34 days overdue. | Maestro trigger, Data Fabric query. |
| 2 | API workflow finds PO exists but no GRN. | API workflow. |
| 3 | Triage Agent classifies `Missing GRN`, priority High due to critical supplier and amount. | Agent. |
| 4 | Case created and routed to DC receiver. | Case Management, Maestro routing. |
| 5 | GRN Confirmation Action created. | Action Center/action app. |
| 6 | Receiver confirms goods received and attaches mock delivery evidence. | Human-in-the-loop. |
| 7 | RPA/API updates mock GRN and ERP match status. | RPA/API workflow. |
| 8 | Payment Risk Agent confirms no remaining hold/duplicate risk. | Agent + controls. |
| 9 | AP approves release and case closes. | Case workflow, audit trail. |

**Value message:** UiPath turns an unowned AP exception into a routed, trackable, SLA-managed case with evidence and automated update.

### 21.2 Scenario 2 - Price mismatch outside tolerance

| Step | Demo action | Capability shown |
|---:|---|---|
| 1 | Invoice has price 6% above PO. | Mock procurement data. |
| 2 | Triage Agent classifies price mismatch and routes to procurement. | Agent and routing. |
| 3 | Procurement reviews price variance action app. | Coded action app. |
| 4 | Procurement requests supplier credit note or approves variance. | Human decision. |
| 5 | Supplier communication draft generated. | Supplier Query/Response Agent. |
| 6 | Case updated to awaiting supplier or recommended for payment. | Case lifecycle. |

**Value message:** Finance, AP, and procurement collaborate in one controlled case rather than email chains.

### 21.3 Scenario 3 - Duplicate invoice risk

| Step | Demo action | Capability shown |
|---:|---|---|
| 1 | Same supplier invoice appears through EDI and PDF. | Mock multi-channel ingestion. |
| 2 | Duplicate engine flags high risk. | Rules/API workflow. |
| 3 | Agent creates duplicate investigation summary. | Agent summarization. |
| 4 | AP reviews evidence and closes duplicate. | Action app and case closure. |
| 5 | Supplier receives controlled notification. | RPA/API supplier communication. |

**Value message:** Duplicate risk is prevented before payment while keeping the supplier informed.

### 21.4 Scenario 4 - Urgent supplier payment request

| Step | Demo action | Capability shown |
|---:|---|---|
| 1 | Supplier query received requesting urgent payment. | RPA mailbox/API portal trigger. |
| 2 | Supplier Query Agent identifies invoice and open payment hold. | Agent. |
| 3 | Payment Risk Agent checks hold, duplicate score, bank validation, approvals. | Agent + rules. |
| 4 | Urgent Payment Action routes to AP lead, Finance, Treasury. | Maestro + Action Center. |
| 5 | Decision captured and mock payment status updated. | Human approval + API/RPA. |
| 6 | Case closes with full audit trail. | Case Management. |

**Value message:** UiPath can manage urgent payment exceptions with speed and governance.

### 21.5 Scenario 5 - Supplier statement mismatch

| Step | Demo action | Capability shown |
|---:|---|---|
| 1 | Supplier statement uploaded with unmatched invoice lines. | RPA/document workflow. |
| 2 | Statement reconciliation matches paid, open, and missing invoices. | Automation workflow. |
| 3 | Case is created for true mismatch. | Case Management. |
| 4 | Agent summarizes statement discrepancy. | Agent. |
| 5 | AP sends response or opens payment investigation. | Action app + supplier communication. |

**Value message:** Supplier statement reconciliation becomes a structured case process rather than spreadsheet work.

---

## 22. End-to-End Happy Path

This is the preferred demo path for a polished customer walkthrough.

1. Presenter opens AP Control Tower and shows aged backlog.
2. Presenter starts `Daily Aged Invoice Review` from Demo Admin Console.
3. Maestro creates process instances for selected aged invoices.
4. API workflow enriches invoice context from mock ERP, procurement, GRN, and payment data.
5. Triage Agent classifies exceptions and assigns priority.
6. Cases appear in AP Control Tower.
7. Presenter opens a high-priority case.
8. Case Workspace shows invoice, supplier, PO/GRN/payment status, agent recommendation, evidence, and audit timeline.
9. Maestro routes a GRN action to the receiver persona.
10. Presenter switches persona and completes GRN Confirmation Action.
11. API/RPA updates mock GRN and ERP invoice status.
12. Payment Risk Agent recommends release.
13. AP Lead approves release.
14. Mock payment platform marks invoice as scheduled/paid.
15. Supplier notification is generated.
16. Case closes with audit trail.
17. Dashboard updates aged value, SLA, and closure metrics.

---

## 23. Error and Exception Handling

| Error scenario | Expected process behavior |
|---|---|
| Mock API unavailable | Maestro logs incident, retries, and routes to Automation Support if retry fails. |
| Agent confidence low | Case routes to AP Review Action. |
| No owner found | Case routes to AP Lead queue with routing exception reason. |
| Human action overdue | Reminder sent, then escalated to manager. |
| Supplier does not respond | Case escalates after supplier response SLA and may remain on hold. |
| Duplicate case detected | Existing case updated instead of creating duplicate. |
| RPA mock ERP update fails | Case remains open with automation failure activity and support task. |
| Payment risk found | Release recommendation blocked and case routes to finance/treasury. |
| User rejects recommendation | User decision captured with reason and audit event. |
| Demo reset required | Demo Admin Console resets data to baseline scenario state. |

---

## 24. Acceptance Criteria

| ID | Acceptance criteria |
|---|---|
| AC-001 | Given mock invoice data exists, when daily aged invoice review runs, then aged/at-risk invoices are identified using due date, ageing bucket, and blocking status. |
| AC-002 | Given an invoice lacks GRN, when triage completes, then a case is created with reason `Missing GRN`, owner queue `Store/DC Receiver`, priority, SLA, and next action. |
| AC-003 | Given a price mismatch exceeds tolerance, when triage completes, then the case is routed to procurement with a price variance action. |
| AC-004 | Given a duplicate-risk invoice is detected, when payment release is evaluated, then release is blocked until duplicate review is completed. |
| AC-005 | Given an urgent payment request is received, when risk assessment completes, then the case requires human approval before mock payment release. |
| AC-006 | Given an agent creates a recommendation, when the case workspace is opened, then the recommendation, confidence score, and evidence references are visible. |
| AC-007 | Given a human completes a stage/task-specific action app, when submitted, then the case captures the decision output, updates the audit/activity trail, and routes to the correct downstream stage such as supplier collaboration, payment risk, compliance hold, approval, closure, or rework. |
| AC-008 | Given an SLA breach occurs, when escalation rules run, then the case is escalated and visible in the manager dashboard. |
| AC-009 | Given a supplier response is generated by an agent, when the response is supplier-facing, then human approval is required before sending. |
| AC-010 | Given a case is closed, when audit view is opened, then the full timeline of data enrichment, triage, human actions, automation, approvals, and closure is visible. |
| AC-011 | Given the dashboard is refreshed after case closure, when viewed by AP Lead, then aged invoice count/value and case status metrics reflect the update. |
| AC-012 | Given no source systems are connected, when the demo runs, then all process steps still execute using mocked APIs, Data Fabric entities, and simulated RPA workflows. |

---

## 25. Success Criteria for the PoV

| Success criterion | Measurement approach |
|---|---|
| Clear business story | Stakeholders can explain the before/after process after demo. |
| End-to-end orchestration visible | Maestro process instances show humans, agents, API, and RPA steps. |
| Case management value visible | Cases have owner, SLA, status, priority, evidence, timeline, and closure. |
| Mock data feels realistic | Dataset includes varied suppliers, ageing buckets, exception reasons, and statuses. |
| Agents add value | Agent recommendations reduce triage ambiguity and summarize cases effectively. |
| Human control preserved | Payment-impacting decisions require approvals. |
| API and RPA both demonstrated | At least one API workflow and one RPA workflow execute during demo. |
| Dashboards update | Case actions change operational KPIs. |
| Audit story credible | Case timeline can support an auditor-style walkthrough. |
| Path to production clear | SDD follow-up list identifies what changes for real systems. |

---

## 26. Risks, Constraints, and Mitigations

| Risk / constraint | Impact | Mitigation |
|---|---|---|
| No real source-system access | Demo may feel disconnected from customer reality. | Use realistic mock data, realistic exception patterns, and clear integration placeholders. |
| Product feature availability varies by tenant | Some desired capabilities may not be enabled. | Validate tenant features before SDD; keep alternate implementation patterns. |
| Case Management terminology/product maturity | Ambiguity in exact implementation path. | Model case lifecycle in Data Fabric + Maestro + Apps; validate native case capability in SDD. |
| Overly complex demo | Hard to build and present. | Limit demo to 3-5 scenarios with reusable components. |
| Agents hallucinate or overreach | Poor trust in recommendations. | Use structured inputs, constrained outputs, confidence thresholds, and human review. |
| Too much technical detail in PDD | Confuses business audience. | Keep PDD process-level; move architecture/code details to SDD. |
| Mock payment release could imply real payment capability | Risk/compliance concern. | Clearly label as simulated and never generate real payment files. |
| UI build effort too high | PoV schedule risk. | Start with minimal screens: Control Tower, Case Workspace, two action apps, Admin Console. |
| Data setup takes too long | Demo instability. | Build deterministic seed/reset scripts and small baseline dataset first. |

---

## 27. Open Questions

### 27.1 PoV positioning

1. Is the PoV intended for a Woolworths executive audience, finance operations audience, IT/architecture audience, or all three?
2. Should the demo use Woolworths-style branding, or remain customer-neutral with fictional branding?
3. What is the preferred demo length: 15, 30, 45, or 60 minutes?
4. Which scenario should be the hero story: missing GRN, price mismatch, duplicate risk, urgent payment, or supplier statement reconciliation?

### 27.2 UiPath tenant and product availability

5. Which UiPath tenant will host the PoV?
6. Are Maestro, Case Management, Data Fabric/Data Service, Agents, Coded Apps, Action Center, and required connectors enabled?
7. Are there licensing or preview-feature constraints?
8. Can the demo use external mock APIs, or must all mock integrations be hosted inside UiPath workflows/Data Fabric?

### 27.3 Build approach

9. Should the codebase be optimized for a polished demo or for a reusable accelerator?
10. Should mock APIs be built as UiPath API workflows, lightweight local services, or static Data Fabric wrappers?
11. Should RPA workflows interact with a mock web ERP, a spreadsheet, or a generated desktop app?
12. Should supplier emails be generated and processed from a test mailbox, or simulated inside Data Fabric?
13. Should dashboarding be done through Coded Apps, Process Apps, Insights, or a combination?

### 27.4 Data and process

14. How many mock invoices should be seeded for the demo?
15. Should the dataset include GST/tax validation scenarios?
16. Should small supplier payment terms be represented?
17. Should cases be grouped by supplier statement or treated one invoice at a time?
18. What approval thresholds should be shown in the demo?
19. Should urgent payment require one, two, or three approvals?
20. What audit evidence should be generated as a downloadable artifact?

---

## 28. SDD Handoff Items

The future Solution Design Document should define the following in detail:

| Area | SDD detail required |
|---|---|
| Architecture | Component architecture, environment topology, deployment model, folders, packages, queues, assets. |
| Data model | Exact entity schemas, field types, relationships, indexes, validation rules, seed data scripts. |
| Maestro model | BPMN process design, process variables, task configuration, incidents, SLAs, routing, versioning. |
| Case management | Exact native feature usage or custom case model, status transitions, permissions, data persistence. |
| Apps | Coded App structure, pages, components, API bindings, authentication, state management. |
| Action apps | Input/output schemas, action catalogs, assignment rules, completion behavior. |
| Agents | Agent definitions, prompts, tools, guardrails, structured outputs, test cases. |
| API workflows | Endpoint definitions, request/response schemas, mock data services, error handling. |
| RPA workflows | Studio project structure, activities, selectors for mock UI, retry and logging patterns. |
| Orchestrator | Processes, queues, triggers, assets, folders, credentials, robot accounts. |
| Security | Roles, access model, service accounts, data masking, audit permissions. |
| Testing | Unit, integration, scenario, demo reset, negative-path, and acceptance test cases. |
| Deployment | CI/CD, package promotion, configuration, runbook, rollback, support model. |
| Codebase | Repository layout, naming conventions, configuration files, documentation, deployment scripts. |

---

## 29. Recommended MVP Build Sequence

Although implementation planning is a later deliverable, the following sequence keeps the PDD aligned to a practical build.

| Sequence | Build item | Why first/next |
|---:|---|---|
| 1 | Mock data model and seed data | Everything depends on credible data. |
| 2 | AP Control Tower and Case Workspace wireframes | Defines demo story and required data. |
| 3 | Case lifecycle and status transitions | Core of the PoV. |
| 4 | Maestro orchestration skeleton | Connects process stages. |
| 5 | API workflows for enrichment | Demonstrates integration pattern. |
| 6 | Triage Agent with structured output | Demonstrates agentic value early. |
| 7 | Two action apps: GRN Confirmation and Price Variance | Demonstrates human-in-the-loop. |
| 8 | RPA mock ERP update | Demonstrates RPA relevance for legacy systems. |
| 9 | Payment Risk Agent and urgent payment action | Demonstrates governance. |
| 10 | Dashboards and audit timeline | Completes executive story. |
| 11 | Supplier statement scenario | Optional richer scenario if time allows. |
| 12 | Demo reset/admin console | Required for reliable repeatable demos. |

---

## 30. Appendix A - Mapping BRD Requirements to PoV Features

| BRD theme | PoV feature |
|---|---|
| Single aged invoice control tower | AP Control Tower Coded App. |
| Case ownership | AgedInvoiceCase entity, owner queue, assigned user, SLA. |
| Root-cause taxonomy | ExceptionReason entity and triage rules. |
| Automated escalation | Maestro SLA and escalation flow. |
| Supplier communication | Supplier Query Agent and supplier notification workflow. |
| Duplicate detection | Duplicate scoring rule and AP duplicate review action. |
| Payment hold governance | Payment Hold Release Action and Payment Risk Agent. |
| Audit trail | CaseActivity and AuditEvent entities. |
| Workflow automation | Maestro process and API/RPA workflows. |
| Human-in-the-loop approvals | Action Center/action apps. |
| AI-assisted dispute summarization | Dispute Summarization Agent. |
| Reporting and dashboards | Manager Dashboard and process/case KPIs. |
| Process mining/event logs | CaseActivity/AuditEvent stream as event log foundation. |

---

## 31. Appendix B - Sample Case Records

| Case ID | Invoice | Supplier | Reason | Priority | Owner | Status | Recommended action |
|---|---|---|---|---|---|---|---|
| CASE-0001 | INV-100472 | FreshHarvest Produce | Missing GRN | High | DC Receiver | Awaiting internal action | Confirm receipt and update GRN. |
| CASE-0002 | INV-100511 | Metro Packaging Co | Price mismatch | Medium | Procurement | Assigned | Review 6% variance and request credit note or approve. |
| CASE-0003 | INV-100533 | Southern Logistics | Payment hold | Critical | Finance Manager | On hold | Review hold and urgent payment request. |
| CASE-0004 | INV-100601 | Pacific Cleaning Services | Approval overdue | High | Business Approver | Awaiting internal action | Approve or reject non-PO invoice. |
| CASE-0005 | INV-100633 | Bright Dairy Supplies | Duplicate risk | Medium | AP Clerk | Assigned | Review EDI/PDF duplicate evidence. |
| CASE-0006 | INV-100710 | GreenShelf Merchandising | Statement mismatch | Medium | AP Reconciliation | Assigned | Reconcile statement line and draft supplier response. |

---

## 32. Appendix C - Public UiPath Reference URLs

These references should be rechecked during the SDD phase because product capabilities and names can change.

| Topic | Reference |
|---|---|
| Maestro overview | https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/introduction-to-maestro |
| Maestro tasks | https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/tasks |
| Maestro using agents | https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/using-agents-in-maestro |
| Maestro ecosystem fit | https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/maestro-integration-with-the-uipath-ecosystem |
| Data Fabric / Data Service overview | https://docs.uipath.com/data-service/automation-cloud/latest/user-guide/overview |
| UiPath Apps overview | https://docs.uipath.com/apps/automation-cloud/latest/user-guide/introduction |
| Coded Apps overview | https://docs.uipath.com/apps/automation-cloud/latest/user-guide-ca/introduction |
| Action Center overview | https://docs.uipath.com/action-center/automation-cloud/latest/user-guide/introduction |
| Action Apps | https://docs.uipath.com/action-center/automation-cloud/latest/user-guide/action-definitions |
| Agents overview | https://docs.uipath.com/agents/automation-cloud/latest/user-guide/about-agents |
| Coded agents | https://docs.uipath.com/agents/automation-cloud/latest/user-guide/about-coded-agents |
| UiPath Solutions Management | https://docs.uipath.com/solutions-management/automation-cloud/latest/user-guide/solutions-management-overview |

---

## 33. Immediate Next Iteration Recommendations

Before moving to the SDD, agree on the following decisions:

1. **Hero demo scenario:** Use Missing GRN as the main path because it clearly shows AP, receiving, automation, agent support, and payment release.
2. **Secondary scenario:** Use Urgent Payment Request because it demonstrates controls, risk, approvals, and governance.
3. **Optional advanced scenario:** Use Supplier Statement Mismatch if time allows, because it shows reconciliation and supplier experience.
4. **Minimum screens:** AP Control Tower, Case Workspace, GRN Confirmation Action, Payment Hold/Urgent Payment Action, Demo Admin Console.
5. **Minimum agents:** Triage Agent and Payment Risk Agent first; add Supplier Query Agent and Dispute Summary Agent next.
6. **Minimum automations:** Invoice intake/enrichment API workflow, create/update case workflow, mock ERP update RPA, supplier notification workflow.
7. **Mock data size:** Start with 150 invoices and 25 suppliers, then scale to 750 invoices for dashboard impact.

---

## 34. Completion Statement

This PDD defines the process design for an Aged Invoice Payment Case Management proof of value using mocked data and UiPath platform capabilities. It is ready for stakeholder review and iteration. The next deliverable should be the Solution Design Document, which will translate this process design into architecture, component specifications, schemas, UiPath packages, workflows, agent definitions, app designs, deployment steps, and codebase structure.
