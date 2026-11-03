<!-- pdd:doc header="Connectivity Service Termination due to Customer Request {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | Sundara Telekom" client="Sundara Telekom" author="Local Developer" date="29 September 2026" version="1.0" process="Connectivity Service Termination due to Customer Request {{RUN_TOKEN}}" -->

# Connectivity Service Termination due to Customer Request {{RUN_TOKEN}}

<!-- pdd:section id=business-context sources=as-is/overview.md,to-be/overview.md,to-be/benefits.md reproj=g0 -->
# 1. Business Context
## 1.1 Problem Statement
Sundara Telekom manages customer-requested connectivity-service termination across multiple channels, approvals, commercial activities, and technical work. The documented process relies on **Smartsheet** coordination and manual follow-up, while the request cannot close until both administrative and dismantle work complete.
## 1.2 Objectives
- Establish one end-to-end tracked termination record.
- System-manage completeness checks, reminders, SLA timers, and escalation.
- Preserve human judgement for approvals, retention, waiver decisions, and technical execution.
## 1.3 Expected Value
The future process improves traceability, coordination, and control; acceptance signals are in Section 10.
[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope
## 2.1 Process Identity
| Process name | Process group | Industry |
|---|---|---|
| Connectivity Service Termination due to Customer Request | Customer Operations | Telecommunications |

## 2.2 Scope Boundaries
| In Scope | Out of Scope |
|---|---|
| Customer-requested connectivity termination | Broader customer lifecycle |
| Intake through closure | Unspecified termination types |
| Approval, administration, dismantle coordination | Undocumented downstream policy redesign |
[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/diagram.md,as-is/stages.md,as-is/metrics.md,as-is/exception-handling.md reproj=g0 -->
# 3. Current State
## 3.1 Overview
The current process receives requests through Helpdesk, Sales, AM/CSM, and email, records them in **Smartsheet**, validates customer/PIC information, obtains approvals, and then runs administrative and dismantle work in parallel.
## 3.2 Current Flow
1. Request intake and documentation.
2. Customer/PIC validation and completeness check.
3. Retention discussion and Sales/AVP approval.
4. Parallel administrative closure and service dismantle.
5. Completion after both workstreams converge.
## 3.3 Metrics
| Metric | Current signal |
|---|---|
| Reminder handling | 3 working days noted |
| Regular termination | 15 working days noted |
| Priority termination | 3–5 working days noted |
| Penalty response escalation | 20 days noted |
## 3.4 Pain Points
Manual consolidation, reminders, status coordination, and parallel-work reconciliation are implied by the documented flow; volumes and measured impacts are not documented.
[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)
[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/benefits.md reproj=g0 -->
# 4. Future State
## 4.1 Vision
A BPMN-orchestrated future process creates one tracked request, automates intake, document checks, notifications, timers, parallel coordination, and evidence capture. Human owners retain exceptions, retention, approvals, waiver decisions, and technical execution.
[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)
## 4.2 Target Flow
| # | BPMN element | Owner | Outcome |
|---|---|---|---|
| 1 | Request receipt and validation | Automation / CXOH-SVQA | Complete record or information request |
| 2 | Retention and approvals | Sales / AVP Sales | Approved, cancelled, or escalated |
| 3 | Parallel administration | BAO | Commercial closure evidence |
| 4 | Parallel dismantle | NDFT | Technical completion evidence |
| 5 | Completion gateway | Orchestration | Closure only when both streams complete |
## 4.3 What Changes
| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Intake | Manual consolidation | Unified tracked request | Improve traceability | Channel capture and structured record |
| Follow-up | Individual chasing | Timer-driven reminders | Protect SLA | Automated alerts and escalation |
| Closure | Parallel work manually reconciled | Completion gateway | Prevent premature close | BPMN parallel join |
## 4.4 Automation Summary
Automation manages orchestration, reminders, evidence tracking, and coordination; humans retain high-judgement and technical work.
[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/business-rules.md reproj=g0 -->
# 5. Business Rules
| Rule ID | Description |
|---|---|
| BR-001 | Requests may arrive through documented customer-contact channels. |
| BR-002 | Required documentation and customer/PIC details must be complete before progression. |
| BR-003 | Customer/PIC approval is required. |
| BR-004 | Incomplete or unapproved requests receive reminders and may close under the documented 3-working-day SLA. |
| BR-005 | Penalties and waiver requests follow the documented approval path. |
| BR-006 | Sales and AVP approval precede closure work. |
| BR-007 | Administrative and dismantle work must both complete before final closure. |
[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=as-is/data-inputs-outputs.md,entities/artifacts/ reproj=g0 -->
# 6. Data Model
| Entity / Artifact | Description |
|---|---|
| Termination request | Primary tracked business record. |
| Termination form and documents | Customer/PIC evidence and request details. |
| Service Order | Technical dismantle instruction. |
| Penalty, waiver, invoice, and adjustment records | Commercial closure evidence. |

==TBD: confirm decision-driving fields, privacy classification, integration endpoints, and authentication during solution design==
[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=as-is/overview.md reproj=g0 -->
# 7. People
## 7.1 Roles and Personas
| Stakeholder | Responsibility |
|---|---|
| Customer / authorized PIC | Provides information, approval, and responses. |
| CXOH/SVQA | Validates requests, documentation, reminders, and waiver coordination. |
| Sales / AM / CSM | Retention and commercial approval. |
| AVP Sales | Final approval. |
| BAO / Administration | Dunning, penalty, quote, invoice, and adjustment work. |
| NDFT | Technical validation and dismantle. |
| Product team | Waiver evaluation. |
| Orchestration service | Timers, routing, evidence, and completion gating. |
[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=as-is/stages.md reproj=g0 -->
# 7.2 RACI
| Activity / Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Intake and validation | CXOH/SVQA | Sales Operations | Customer/PIC | Sales |
| Commercial approval | Sales / AVP Sales | AVP Sales | Customer | CXOH/SVQA |
| Administrative closure | BAO | Sales Operations | Product team | Customer |
| Dismantle | NDFT | NDFT | BAO | Customer |
[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/overview.md reproj=g0 -->
# 8. Exceptions and Error Handling
| Exception | AS-IS Handling | TO-BE Handling |
|---|---|---|
| Missing documents | Customer follow-up and recheck | Structured request, timer, escalation, resubmission loop |
| Missing PIC approval | Reminder and possible closure | Monitored approval task and policy-controlled closure |
| Retention outcome | Cancel/drop request | Recorded terminal outcome |
| Penalty dispute | Waiver escalation | Tracked exception task with Product-team decision |
| Failed dismantle | Not documented | Escalated active exception; recovery path to be confirmed |
[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/business-rules.md reproj=g0 -->
# 9. Compliance and Regulatory
Documented controls cover customer/PIC evidence, approval, penalty communication, waiver escalation, and dual-workstream closure evidence.

==TBD: confirm privacy, regulatory retention, authentication, fraud prevention, and audit requirements before implementation==
[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria
| KPI | Target / acceptance signal |
|---|---|
| Completion control | No request closes before both workstreams complete. |
| Traceability | Every approval, reminder, and exception has a timestamped owner and outcome. |
| SLA controls | Timer values are policy-confirmed before production use. |
[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/open-questions.md,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks
## 11.1 Assumptions
| Assumption | Detail |
|---|---|
| Orchestration | Can exchange work/status with Smartsheet, Service Order, and billing environments. |
| Automation opportunities | Email extraction and penalty assistance require validation before production. |
## 11.2 Constraints
| Constraint | Detail |
|---|---|
| Scope | Limited to customer-requested connectivity termination. |
| Policy data | Privacy, fraud, and retention requirements are not confirmed. |
## 11.3 Dependencies
| Dependency | Type | Detail |
|---|---|---|
| Smartsheet and source systems | Hard | Access and integration design required. |
| Policy owners | Hard | Confirm SLAs, controls, and closure obligations. |
| NDFT and billing stakeholders | Hard | Define operational exception and recovery paths. |
## 11.4 Risks
| Risk | Mitigation |
|---|---|
| Unconfirmed controls | Validate before production and route exceptions to humans. |
| Integration limitations | Assess interfaces during solution design. |
[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=as-is/overview.md reproj=g0 -->
# 12. Glossary
| Term | Definition |
|---|---|
| AM | Account Manager. |
| AVP | Assistant Vice President. |
| BAO | Administrative function handling commercial closure work. |
| CPE | Customer Premises Equipment. |
| CXOH/SVQA | Documented validation and coordination function. |
| PIC | Person in Charge. |
| NDFT | Team responsible for technical service dismantling. |
[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps
| # | Action item |
|---|---|
| 1 | Confirm integration methods and source-of-truth ownership. |
| 2 | Confirm SLA applicability, volume, backlog, and acceptance thresholds. |
| 3 | Confirm privacy, audit, fraud, final-billing, and charge-cessation controls. |
| 4 | Define failed-dismantle and downstream-system recovery paths. |
[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=to-be/process.bpmn,as-is/diagram.md reproj=g0 -->
# Appendix A: Process Map and Diagrams
The current case map and future BPMN process model are the process-design references. The future BPMN model in `to-be/process.bpmn` is the target process model of record.
[Refine section](delegate:refine-section?section=appendix-a)
