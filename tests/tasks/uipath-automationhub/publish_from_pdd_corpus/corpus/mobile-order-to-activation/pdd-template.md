<!-- pdd:doc header="Order to Activation - Mobile eCommerce {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | Kestrel Mobile" client="Kestrel Mobile" author="Local Developer" date="29 September 2026" version="1.0" process="Order to Activation - Mobile eCommerce {{RUN_TOKEN}}" -->

# Order to Activation - Mobile eCommerce {{RUN_TOKEN}}

<!-- pdd:section id=business-context sources=as-is/overview.md,as-is/pain-points.md,to-be/overview.md,to-be/benefits.md reproj=g0 -->
## 1. Business Context

### 1.1 Problem Statement
The current mobile eCommerce order-to-activation process spans **Big Commerce**, **Siebel**, **ClearFlow**, **NPX/INPX**, fulfilment partners, and customer communications. It contains manual fraud and credit handling, allocation rework, porting fallout, and delivery exceptions that can delay activation inside the stated **24–48 hour** end-to-end KPI. The resulting system pivots and exception handoffs reduce visibility and make consistent audit evidence harder to maintain.

### 1.2 Objectives
- Enable straight-through processing for orders with clear fraud and credit outcomes, valid subscriber allocation, successful porting where applicable, and confirmed delivery.
- Preserve human judgement for fraud flags, referred credit outcomes, porting/delivery fallout, and every order with earlier manual intervention.
- Correlate order, subscriber, porting, fulfilment, review, activation, and notification status across systems.
- Prevent activation unless all prerequisite controls have passed or a reviewer explicitly approves the exception order.

### 1.3 Expected Value
The target design reduces avoidable re-keying and allocation errors, makes stalled and exception orders visible earlier, and improves traceability across the lifecycle. It retains people where judgement is required while accelerating the predictable path. See Section 10 for KPI and acceptance criteria.

[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
## 2. Scope

### 2.1 Process Identity

| Process name | Process group | Process identifier | Industry |
|---|---|---|---|
| Order to Activation - Mobile eCommerce | Customer order fulfilment and activation | O2A-MOB-ECOM-001 | Telecommunications |

### 2.2 Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| Online order intake and confirmation | Product catalogue design |
| Fraud and credit routing | Credit-policy threshold design |
| Customer, billing, asset, SIM, and MSISDN setup | Hardware repair after order closure |
| Conditional number porting and fallout | Jurisdiction-specific porting-policy definition |
| Hardware dispatch, delivery status, activation, notification, and closure | Unrelated retail or assisted-sales journeys |

### 2.3 Systems and Applications

| System | Role in Process | Access Type |
|---|---|---|
| **Big Commerce** | Online order and fraud-list processing | Both |
| **Siebel** | Customer, billing, asset, SIM, MSISDN, proposition, and order records | Both |
| **ClearFlow** | Credit assessment | Both |
| **NPX/INPX** | Number-port submission and status | Both |
| **SMSPulse**, **IVR AWS Connect**, **Microsoft Outlook** | Customer and operational communications | Both |
| **Service Compass** | Procedure and support guidance | Read |

[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/process.bpmn,as-is/metrics.md,as-is/pain-points.md,as-is/exception-handling.md reproj=g0 -->
## 3. Current State

### 3.1 Overview
The current process starts with an eCommerce order in Big Commerce and proceeds through fraud/credit checks, customer and subscriber setup, conditional porting, equipment fulfilment, activation, notification, and closure. Work crosses multiple systems and teams; referred checks and operational fallout require manual intervention.

### 3.2 Current Flow

| # | Current step |
|---|---|
| 1 | Receive online order and send confirmation |
| 2 | Perform fraud checks and route flagged orders for review |
| 3 | Set up customer, proposition, billing, and installed asset |
| 4 | Submit and resolve credit assessment |
| 5 | Allocate SIM and MSISDN |
| 6 | Create, track, and complete a port request when required |
| 7 | Request, dispatch, track, and confirm hardware delivery |
| 8 | Complete connection and activate service |
| 9 | Update status, notify customer, invoice, and close order |

### 3.3 Metrics

| Metric | Current signal | Measurement method |
|---|---|---|
| End-to-end order to activation | 24 to 48 hours | Supplied process overview |
| Volume, backlog, and peak | Not provided | No source report or SME estimate supplied |

### 3.4 Pain Points

| Where | What breaks | Impact |
|---|---|---|
| Credit assessment | Referred credit checks cannot be automated | Manual delay |
| Subscriber setup | SIM conflict or expired MSISDN reservation | Rework and failed allocation |
| Porting | Rejections and NPX/INPX synchronisation issues | Delayed activation |
| Fulfilment | Delivery exception or return | Delayed closure |

The current BPMN model is the approved process-model source of record.

[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)

[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/activities.md,to-be/gateways-and-routes.md,to-be/exception-handling.md,to-be/benefits.md reproj=g0 -->
## 4. Future State

### 4.1 Vision
The future state is a BPMN-orchestrated order lifecycle. Clean orders proceed automatically through validation, checks, subscriber setup, porting when applicable, fulfilment, and activation; **Human Review** remains mandatory before activation whenever fraud, credit, or any earlier manual intervention has occurred. The target model is the process model of record.

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)

### 4.2 Target Flow

| # | BPMN element | Participant / lane | Element type | Input / message | Output / message | Route / exception path |
|---|---|---|---|---|---|---|
| 1 | Order accepted | Order Orchestration | Start event | Accepted eCommerce order | Correlated order | Start lifecycle |
| 2 | Validate and correlate order | Order Orchestration | Service task | Order data | Correlation ID | Invalid data routes to review |
| 3 | Run fraud and credit checks | Automated Provisioning | Service task | Customer and order data | Clear or review outcome | Flagged/referred routes to review |
| 4 | Review flagged order | Human Review | User task | Evidence and reason code | Approve/reject decision | Reject cancels order |
| 5 | Set up customer and subscriber | Automated Provisioning | Service task | Validated order | Billing, asset, SIM, MSISDN | Allocation error routes to review |
| 6 | Submit and monitor port | Automated Provisioning | Service task | Port request | Port status | Failure routes to port exception |
| 7 | Request equipment dispatch / wait for delivery | Fulfilment Partners | Send/receive tasks | Hardware order | Delivery status | Failed delivery routes to review |
| 8 | Activation eligible? | Automated Provisioning | Gateway | Control outcomes and intervention flag | Activation route | Manual touch requires review |
| 9 | Activate service and close order | Order Orchestration | Service task | All controls passed | Service live, notification, closure | Service-activated end event |

### 4.2.1 Future Work Details

#### Orchestrate Order Intake and Controls
**Trigger:** Accepted eCommerce order.  
**Systems:** Big Commerce, orchestration, ClearFlow.  
**Inputs / outputs:** Order, customer, fraud and credit outcomes; correlated lifecycle record.  
**Rule:** A non-clear result creates a Human Review work item.  
**Exception:** System outage pauses the activity and resumes safely from the correlated state.

#### Provision Subscriber and Coordinate Porting
**Trigger:** Clear or human-approved order.  
**Systems:** Siebel and NPX/INPX.  
**Inputs / outputs:** Customer, billing, asset, SIM, MSISDN, port request, and port status.  
**Rule:** Allocation must validate before activation; unresolved port fallout blocks activation.  
**Exception:** Allocation or porting failure routes to Human Review and reason-coded recovery.

#### Fulfil Equipment and Activate
**Trigger:** Subscriber setup complete; port complete when applicable.  
**Systems:** Swiftline Logistics, Courier, Siebel, customer communications.  
**Inputs / outputs:** Hardware order, delivery status, intervention flag, activation status.  
**Rule:** Activation proceeds automatically only for clean orders with all controls passed.  
**Exception:** Any prior manual intervention, delivery exception, fraud flag, or referred credit outcome requires Human Review approval before activation.

### 4.3 What Changes

| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Checks | Manual exception coordination | Automated clear path with review routing | Faster clean orders | Correlated decision gateways |
| Provisioning | Multiple manual system updates | Validated orchestration | Reduce re-keying and allocation errors | Automated activities with safe retry |
| Porting | Manual monitoring | Status-driven monitoring and review | Earlier exception visibility | Correlated port lifecycle and reason codes |
| Activation | Operationally dependent closure | Explicit eligibility gateway | Prevent control bypass | Persistent intervention flag and approval gate |

### 4.4 BPMN Work Summary
The design includes automated validation, checks, setup, porting coordination, fulfilment recording, and activation; Human Review performs exception resolution and approval. No AI-driven decision-making is proposed.

[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/business-rules.md reproj=g0 -->
## 5. Business Rules

| Rule ID | Description |
|---|---|
| BR-001 | Fraud and credit checks must return a clear outcome before straight-through processing continues. |
| BR-002 | Any order flagged by fraud or credit review, or touched manually at an earlier point, requires human approval before activation. |
| BR-003 | SIM and MSISDN allocation must validate before activation. |
| BR-004 | Porting exceptions must be resolved or explicitly cancelled before activation. |
| BR-005 | Cross-system updates must use one correlation identifier and be safe to retry. |

[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md,to-be/data-objects.md reproj=g0 -->
## 6. Data Model

### 6.1 Entities

| Entity | Description |
|---|---|
| Correlated Order Record | Lifecycle anchor for all process status and audit events |
| Customer / Billing Account | Customer and financial profile in Siebel |
| Subscriber Provisioning Record | Installed asset, SIM, MSISDN, and proposition binding |
| Port Request | Conditional number-port request and status |
| Hardware Delivery Record | Dispatch, tracking, delivery, return, and exception status |
| Human Review Decision | Reason, reviewer, outcome, timestamp, and release/block state |

### 6.2 Data Inputs and Outputs

| Artifact | Source / Destination | Format | Consumed / Produced By |
|---|---|---|---|
| eCommerce Order | Big Commerce → orchestration | Application record | Order intake |
| Subscriber Provisioning Record | Siebel ↔ orchestration | Application record | Provisioning |
| Port Request | NPX/INPX ↔ orchestration | Application record | Porting coordination |
| Delivery Status | Fulfilment partners → orchestration | Status event | Fulfilment and activation |

### 6.3 Field-Level Data Dictionary

| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
|---|---|---|---|---|---|
| Correlation ID | String | Immutable unique ID | Unique per order | Yes | Internal |
| SIM / MSISDN | String | System identifier | Allocated/validated | Conditional | Sensitive |
| Fraud / Credit Outcome | Enum | Decision status | Clear, referred, reject | Yes | Sensitive |
| Manual Intervention Flag | Boolean | True/false | True blocks straight-through activation | Yes | Internal |
| Porting Credential / Consent | Token / record | Masked and access controlled | Valid/invalid | Conditional | Sensitive |

### 6.4 Data Flow and Lineage
1. Big Commerce order creates the correlated order record.
2. Checks, setup, porting, and fulfilment add timestamped status events.
3. The intervention flag and review decision gate activation.
4. Activation, notification, and closure complete the audit trail.

### 6.5 Integrations

| Integration | Fields passed | Connector / type | Endpoint + Auth |
|---|---|---|---|
| Big Commerce → orchestration | Order, customer, status | Not confirmed | Not confirmed |
| Orchestration → Siebel | Customer, billing, asset, SIM, MSISDN | Not confirmed | Not confirmed |
| Orchestration → ClearFlow | Credit assessment data and outcome | Not confirmed | Not confirmed |
| Orchestration → NPX/INPX | Port request and status | Not confirmed | Not confirmed |

==TBD: confirm integration endpoints and authentication during solution design==

[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
## 7. People

### 7.1 Roles & Personas

| Stakeholder | Responsibility |
|---|---|
| Customer | Places order, authorises porting, receives equipment and communications |
| Online Shop Agent / Kestrel Mobile Operations | Handles current order operations and future exception/review work |
| Human Reviewer | Approves, corrects, rejects, or releases orders requiring judgement |
| Automated Provisioning | Performs validated rule-based setup and status updates |
| Order Orchestration | Coordinates state, controls, routing, and audit events |
| Clearcred / ClearFlow | Supplies credit assessment outcomes |
| Swiftline Logistics | Dispatches hardware and provides fulfilment status |
| Courier | Collects, delivers, returns, and confirms hardware status |
| Business Partner / Porting Parties | Coordinate applicable number-port activities |

[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=entities/people/ reproj=g0 -->
## 7.2 RACI

| Activity / Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Order intake and orchestration | Order Orchestration | Kestrel Mobile Operations | Online Shop Agent | Customer |
| Fraud / credit exception review | Human Reviewer | Kestrel Mobile Operations | ClearFlow | Customer |
| Subscriber setup | Automated Provisioning | Kestrel Mobile Operations | Online Shop Agent | Customer |
| Porting | Automated Provisioning / Human Reviewer | Kestrel Mobile Operations | Porting parties | Customer |
| Fulfilment | Swiftline Logistics / Courier | Kestrel Mobile Operations | Order Orchestration | Customer |
| Activation and closure | Automated Provisioning / Human Reviewer | Kestrel Mobile Operations | Order Orchestration | Customer |

[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/exception-handling.md reproj=g0 -->
## 8. Exceptions and Error Handling

### 8.1 Known Exceptions

| Exception | Trigger | AS-IS Handling | TO-BE Handling |
|---|---|---|---|
| Fraud / referred credit | Non-clear check outcome | Manual review | Human Review work item, reason code, and explicit approval/reject outcome |
| SIM/MSISDN allocation failure | Conflict or expired reservation | Manual correction | Safe retry, correction, or review routing |
| Porting failure | Reject, timeout, or sync discrepancy | Porting fallout handling | Reason-coded exception, monitored recovery, resubmit/cancel decision |
| Delivery exception | Failed or returned delivery | Delivery escalation | Review work item; resume only after resolution |
| System outage | Dependency unavailable | Manual follow-up | Pause, retry safely, alert support, and resume from correlation state |

### 8.2 Exception Data State Transitions

| Exception | Affected record | State on entry | State on resolution | State on terminal failure |
|---|---|---|---|---|
| Fraud / credit | Correlated order | Manual Review Required | Released for processing | Cancelled |
| Porting | Port request | Port Exception | Resubmitted / complete | Cancelled or held |
| Delivery | Hardware delivery | Delivery Exception | Confirmed delivery | Returned / cancelled / held |
| Dependency outage | Correlated order | External Dependency Unavailable | Resumed | Escalated for manual disposition |

### 8.3 Human Review Task Specification

| Escalation point | Trigger | Fields surfaced | Available actions → resulting state | Task SLA | Assignee role |
|---|---|---|---|---|---|
| Fraud / credit review | Flagged or referred outcome | Order ID, reason, evidence, check outcome | Approve → released; Correct → reprocess; Reject → cancelled | Not confirmed | Human Reviewer |
| Pre-activation approval | Earlier manual intervention | Correlation ID, intervention history, prerequisites, activation eligibility | Approve → activate; Reject → cancelled/held | Not confirmed | Human Reviewer |

<!-- doc:placeholder kind="screenshot" -->
> [!NOTE]
> **Screenshot Placeholder**
> Insert screenshot: Human Review task showing order evidence, reason code, and Approve / Correct / Reject actions.

[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/business-rules.md reproj=g0 -->
## 9. Compliance and Regulatory

> [!WARNING]
> **Needs capture:** Confirm applicable jurisdiction, privacy classification, consent/authorisation policy, retention period, and audit-evidence obligations. This section will auto-fill when the required compliance source is available.

### 9.1 Compliance Traceability Matrix

| Requirement / Rule | Enforced at | Evidence retained |
|---|---|---|
| BR-001 check outcome | Fraud and credit gateway | Outcome and timestamp |
| BR-002 human approval after intervention | Activation-eligibility gateway | Reviewer, reason, decision, and timestamp |
| BR-003 validated allocation | Subscriber setup | SIM/MSISDN validation result |
| BR-004 resolved porting exception | Porting gateway | Port status and resolution history |
| BR-005 correlation and retry safety | Orchestration activities | Correlation ID and processing history |

### 9.2 Audit & Traceability
All future-state status transitions, decisions, exceptions, retries, and customer notifications must be timestamped against the correlated order record. Applicable retention and legal requirements remain open pending Kestrel Mobile policy and jurisdiction confirmation.

[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
## 10. KPIs and Acceptance Criteria

### 10.1 KPIs

| KPI | Target / acceptance signal |
|---|---|
| Order-to-activation cycle time | Retain current 24–48 hour KPI; target improvement not yet confirmed |
| Straight-through processing rate | Measure clean orders completed without Human Review; target not confirmed |
| Human Review aging | Measure review queue age and completion; target not confirmed |
| Activation success rate | Measure activations completed without recovery; target not confirmed |
| Porting / delivery exception recurrence | Measure reason-coded exceptions by type; target not confirmed |

### 10.2 Acceptance Criteria
- Clean orders activate automatically only after all documented prerequisites pass.
- An order with fraud, credit, or any earlier manual intervention cannot bypass Human Review before activation.
- Each lifecycle update is correlated, auditable, and safe to retry.
- Exceptions have a reason-coded owner, recovery route, and terminal outcome.

[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
## 11. Assumptions, Constraints, Dependencies and Risks

### 11.1 Assumptions

| Assumption | Detail |
|---|---|
| Order trigger | An accepted Big Commerce order starts the lifecycle |
| Delivery prerequisite | Delivery confirmation is required on the normal activation path |
| Porting | Porting is conditional and must complete or be explicitly resolved before activation |

### 11.2 Constraints

| Constraint | Detail |
|---|---|
| Source evidence | Volumes, detailed SLAs, privacy class, retention, and compliance policy are not confirmed |
| Scope | The PDD covers the documented mobile eCommerce lifecycle only |

==TBD: confirm compliance, privacy, retention, volumes, and stage-level SLA requirements==

### 11.3 Dependencies

| Dependency | Type | Detail |
|---|---|---|
| Big Commerce, Siebel, ClearFlow, NPX/INPX availability | Hard | Required for relevant automated activities |
| Swiftline Logistics and courier delivery updates | Hard | Required to progress normal fulfilment path |
| Human Review capacity and decision authority | Hard | Required for flagged, referred, and manually touched orders |
| Customer port authorisation | Hard when porting | Required before port request submission |

### 11.4 Risks

| Risk | Mitigation |
|---|---|
| Incorrect integration design | Validate endpoints, authentication, and error behaviour during solution design |
| Control bypass | Enforce persistent manual-intervention flag at activation gateway |
| Outage / duplicate replay | Use correlation ID, idempotent operations, retries, and reconciliation |
| Unconfirmed policy obligations | Keep as open items and obtain Kestrel Mobile policy review before production |

[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
## 12. Glossary

| Term | Definition |
|---|---|
| Big Commerce | eCommerce order management platform for eShop/eChannel |
| Correlation ID | Immutable identifier tying cross-system lifecycle events to one order |
| Fallout | An order or activity leaving the normal automated path for manual handling |
| MSISDN | Mobile Subscriber Integrated Services Digital Network number assigned to a subscriber |
| Port-In | Transfer of an existing mobile number to the gaining carrier |
| SIM | Subscriber identity module allocated to the service |
| NPX/INPX | Mobile number-portability interfaces used for request and status coordination |

[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
## 13. Next Steps

| # | Action item |
|---|---|
| 1 | Confirm applicable privacy, consent, regulatory, audit-evidence, and retention requirements. |
| 2 | Define volumes, peak load, queue SLAs, escalation timers, KPI targets, and reporting ownership. |
| 3 | Confirm integration endpoints, authentication, retry limits, reconciliation, and outage responsibilities. |
| 4 | Validate Human Review task fields, decision authority, assignees, and service levels. |
| 5 | Proceed to solution design to select UiPath products and implementation architecture. |

[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=to-be/process.bpmn reproj=g0 -->
## Appendix A: Process Map and Diagrams

The approved BPMN current and future process models are the process-model records for this PDD. The future model is the primary target-state reference and depicts cross-functional orchestration, exception review, and the pre-activation approval control.

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=appendix-a)

<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert integration sequence diagram showing Big Commerce, orchestration, Siebel, ClearFlow, NPX/INPX, fulfilment partners, Human Review, and customer communications.

[Refine section](delegate:refine-section?section=appendix-a)
