<!-- pdd:doc header="TriStar Standard Prior Authorization {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | TriStar Benefits Group" client="TriStar Benefits Group" author="Business Analysis" date="29 September 2026" version="1.0" process="TriStar Standard Prior Authorization {{RUN_TOKEN}}" -->

# TriStar Standard Prior Authorization {{RUN_TOKEN}}
<!-- pdd:section id=business-context sources=as-is/overview.md,as-is/pain-points.md,to-be/overview.md,to-be/benefits.md reproj=g0 -->
# 1. Business Context
## 1.1 Problem Statement
TriStar Benefits Group processes standard TennCare EDI X12 278 prior authorization requests through **MedVisor**, the EDI gateway, eligibility and benefit records, clinical criteria, and notification channels. Source materials identify risks in scope control, behavioral-health routing, notice compliance, and timing interpretation; operational-volume and handling-time baselines are not available.
## 1.2 Objectives
- Automate deterministic intake, validation, routing, notice assembly, response transmission, evidence capture, and SLA monitoring.
- Retain qualified clinical and physician judgment for decisions requiring clinical authority.
- Enforce behavioral-health segregation and notice-completeness controls.
## 1.3 Expected Value
Expected value is consistent, traceable standard-request handling, reduced routing and notice-content errors, and improved visibility of aging work. See Section 10 for acceptance signals.
[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope
## 2.1 Process Identity
| Item | Value |
|---|---|
| Process name | TriStar Standard Prior Authorization Request Processing |
| Process group | Utilization Management Operations |
| Process identifier | TennCare standard EDI 278 PA |
| Industry | Medicaid managed care |

## 2.2 Scope Boundaries
| In Scope | Out of Scope |
|---|---|
| Standard EDI 278 intake and validation | Expedited request processing |
| Eligibility, benefit, and provider checks | Member appeals and grievances |
| Clinical criteria routing and determination support | Claims adjudication |
| Determination notices and EDI 278 responses | Inpatient concurrent review |
| Provider reconsideration boundary | |

## 2.3 Systems and Applications
| System | Role in Process | Access Type |
|---|---|---|
| **TriStar EDI gateway** | Receives and parses inbound EDI 278 transactions | both |
| **MedVisor** | PA request record, workflow, rationale, and notices | both |
| **InterQual / MCG** | Clinical criteria capability | read |
| Enrollment/member records | Eligibility and benefit validation | read |
| Provider portal / response channel | Provider communication | both |
[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/process.bpmn,as-is/steps/,as-is/metrics.md,as-is/pain-points.md reproj=g0 -->
# 3. Current State
## 3.1 Overview
The current standard process starts with EDI 278 receipt and ends with transmission of the determination notice and response. It contains automated system checks and manual clinical/physician review, with timing and exception evidence maintained across the named systems.
## 3.2 Current Flow
| # | Current step |
|---|---|
| 1 | Receive, parse, and classify the EDI 278 request |
| 2 | Validate member eligibility, benefit coverage, and provider status |
| 3 | Pend and request missing information when required |
| 4 | Apply InterQual or MCG clinical criteria |
| 5 | Route for auto-approval, clinical review, or physician review |
| 6 | Generate compliant determination notice and EDI 278 response |
| 7 | Close the request or hand off the later member appeal |
## 3.3 Metrics
| Metric | Current signal | Measurement method |
|---|---|---|
| Standard determination deadline | 72 hours after receipt of a complete PA request | TennCare contract |
| Validation-RFI response window | 5 business days | Draft workflow |
| Additional-clinical-information window | 14 calendar days | Draft workflow |
| Volume, backlog, staffing, handling time | Not provided | Open operational data need |
## 3.4 Pain Points
| Where | What breaks | Impact |
|---|---|---|
| Scope | Appeals wording could be incorrectly restored | Incorrect workflow boundary |
| BH routing | Capacity pressure could drive improper reassignment | Regulatory and clinical risk |
| Notices | Commercial template is insufficient as-is | Audit and contract-penalty risk |
| Timing | Incomplete-request and receipt-time calculation is unresolved | SLA-control risk |
```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_TriStar_Current_PA" targetNamespace="https://uipath.com/business-analysis/tristar-current-pa"><bpmn:process id="Process_TriStar_Current_PA" name="Current Standard Prior Authorization Request Processing" isExecutable="false"/></bpmn:definitions>
```
*Figure: Current BPMN process model rendered from the approved current process model.*
[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)
[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/bpmn-details.md,to-be/transformation-decisions.md,to-be/participants-and-lanes.md,to-be/events-and-triggers.md,to-be/activities.md,to-be/gateways-and-routes.md,to-be/message-and-timer-flows.md,to-be/data-objects.md,to-be/exception-handling.md,to-be/benefits.md reproj=g0 -->
# 4. Future State
## 4.1 Vision
The future standard-request process uses automation to ingest and validate EDI 278 transactions, apply configured routing rules, create pending work, assemble notices, transmit responses, and monitor SLA risk. Qualified clinicians and physician reviewers retain all high-judgment and adverse-decision work.
```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_TriStar_Future_PA" targetNamespace="https://uipath.com/business-analysis/tristar-future-pa"><bpmn:collaboration id="Collaboration_Future"><bpmn:participant id="Participant_PA" name="TriStar Automated Standard Prior Authorization" processRef="Process_Future_PA" /></bpmn:collaboration><bpmn:process id="Process_Future_PA" name="Automated Standard Prior Authorization" isExecutable="false"><bpmn:startEvent id="Start_278" name="278 request received"/><bpmn:serviceTask id="Task_Ingest" name="Ingest and normalize request"/><bpmn:endEvent id="End_Complete" name="Determination communicated"/><bpmn:sequenceFlow id="F1" sourceRef="Start_278" targetRef="Task_Ingest"/></bpmn:process></bpmn:definitions>
```
*Figure: Future BPMN process model rendered from the proposed automated process model.*
[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)
## 4.2 Target Flow
| # | BPMN element | Participant / lane | Element type | Input / message | Output / message | Route / exception path |
|---|---|---|---|---|---|---|
| 1 | Ingest and normalize request | Automation | activity | EDI 278 | MedVisor work record | Technical exception to PA operations |
| 2 | Classify urgency and request | Automation | activity | 278 urgency data | Standard or expedited route | Expedited route terminates this process |
| 3 | Validate eligibility, benefit, provider | Automation | activity | Member, benefit, provider data | Validated request or RFI | Incomplete item becomes pending |
| 4 | Apply criteria and routing rules | Automation | activity | Request and criteria data | Straight-through or human-review route | BH routed only to qualified BH review |
| 5 | Clinical or physician review | Clinical / physician | activity | Review task and evidence | Decision or information request | Adverse proposal triggers P2P control |
| 6 | Assemble and validate notice | Automation | activity | Decision and rationale | Compliant notice package | Missing content is blocked for correction |
| 7 | Transmit response and notices | Automation | activity | Approved notice package | EDI 278 response and notifications | Delivery failure escalates |
## 4.3 What Changes
| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Intake | Parse/load work may require operations attention | Automated ingestion and evidence capture | Reduce manual handling | Configured EDI-to-MedVisor integration |
| Validation | Rules and pends are handled across systems | Automated validation and pending-item creation | Improve consistency | Configured eligibility, benefit, and provider checks |
| Routing | Manual queue control risk | Rules-based routing with BH segregation | Protect qualified-reviewer rule | Dedicated routing constraints and supervisor alert |
| Notices | Compliance review can be late | Notice-content validation before release | Prevent non-compliant communication | Required-field and citation controls |
| SLA control | Timing interpretation is not operationalized | Visible aging and escalation controls | Improve oversight | Configurable decision-clock monitoring |
## 4.4 Work Summary
Automation handles deterministic data and communications work; humans retain clinical review, physician determination, peer-to-peer activity, and ambiguous exception handling.
[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/business-rules.md reproj=g0 -->
# 5. Business Rules
| Rule ID | Description |
|---|---|
| BR-001 | Issue a standard written determination within 72 hours of receipt of a complete PA request. |
| BR-002 | Identify and route expedited requests before standard clinical evaluation. |
| BR-003 | Validate enrollment, benefit coverage, and provider status. |
| BR-004 | Route behavioral-health requests only to qualified BH clinicians. |
| BR-005 | Use the applicable InterQual or MCG criteria. |
| BR-006 | Retain physician authority for adverse or judgment-dependent determinations. |
| BR-007 | Block notice release until 42 CFR 438.210 content is complete. |
| BR-008 | Route member appeals to Appeals & Grievances; retain timely provider reconsideration in PA operations. |
[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md reproj=g0 -->
# 6. Data Model
## 6.1 Entities
| Entity | Description |
|---|---|
| Prior authorization request | Primary EDI 278-driven work record |
| Member eligibility record | Enrollment and benefit validation input |
| Provider record | Credentialing and contract-status input |
| Clinical criteria result | InterQual/MCG evaluation evidence |
| Determination record | Decision, rationale, reviewer, and notice evidence |
## 6.2 Data Inputs and Outputs
| Artifact | Source / Destination | Format | Consumed / Produced By |
|---|---|---|---|
| EDI 278 request | Provider to EDI gateway / MedVisor | X12 EDI | Intake automation |
| Eligibility and provider data | Enterprise records to MedVisor | System record | Validation automation |
| Determination notice | MedVisor to provider/member | Written notice | Notification automation |
| EDI 278 response | MedVisor to provider | X12 EDI | Notification automation |
## 6.3 Field-Level Data Dictionary
| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
|---|---|---|---|---|---|
| Member identifier | Identifier | Not confirmed | Active enrollee | Yes | PII |
| Service code | Code | CPT/HCPCS/revenue code | Covered-benefit rules | Yes | Sensitive business data |
| Urgency indicator | Code | EDI 278 element | Standard / expedited | Yes | Sensitive business data |
| Determination | Code | System value | Approval / adverse / closure | Yes | Sensitive business data |
## 6.4 Data Flow & Lineage
| # | Data movement |
|---|---|
| 1 | Provider sends EDI 278 to the EDI gateway. |
| 2 | Automation creates or updates the MedVisor work record. |
| 3 | Validation and criteria evidence is linked to the request. |
| 4 | Determination evidence produces the notice and EDI response. |
## 6.5 Integrations
| Integration (System → System) | Fields passed | Connector / type | Endpoint + Auth |
|---|---|---|---|
| EDI gateway → MedVisor | 278 request and receipt evidence | Not confirmed | Not confirmed |
| MedVisor → eligibility/provider data | Member, benefit, provider checks | Not confirmed | Not confirmed |
| MedVisor → provider/member channels | Decision, notice, response | Not confirmed | Not confirmed |

==TBD: confirm integration endpoints and authentication during solution design==
[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
# 7. People
## 7.1 Roles & Personas
| Stakeholder | Responsibility |
|---|---|
| Requesting provider / authorized billing agent | Submits request and supporting information |
| PA operations | Resolves operational exceptions and pending work |
| Qualified BH clinician | Reviews behavioral-health requests only |
| Clinical reviewer | Reviews non-straight-through requests within authority |
| Physician reviewer | Makes adverse, complex, and judgment-dependent determinations |
| BH supervisor | Addresses BH capacity without prohibited reassignment |
| Appeals & Grievances | Receives and processes member appeals outside this workflow |
| Automation service | Performs deterministic transaction, routing, notice, and monitoring work |
[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=entities/people/ reproj=g0 -->
# 7.2 RACI
> [!WARNING]
> **Needs capture:** accountable operational owners and consultation responsibilities must be confirmed. This section will auto-fill when the wiki source is available.
[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/exception-handling.md reproj=g0 -->
# 8. Exceptions and Error Handling
## 8.1 Known Exceptions
| Exception | Trigger | AS-IS Handling | TO-BE Handling |
|---|---|---|---|
| Expedited indicator | Urgency at intake | Separate from standard queue | Automated route-out before standard work |
| Incomplete request | Missing data or documentation | Pend and RFI | Pending item, RFI, and controlled return to validation |
| BH capacity issue | No qualified reviewer available | Hold and notify supervisor | Enforce queue restriction and alert supervisor |
| Notice-content defect | Missing required content | Correct before release | Automated release block and human correction task |
| Member appeal | Appeal after determination | Handoff to A&G | Automated handoff; no PA re-entry |
## 8.2 Exception Data State Transitions
| Exception | Affected record | State on entry | State on resolution | State on terminal failure |
|---|---|---|---|---|
| Incomplete request | PA request | Pending information | Validated | Administrative closure |
| BH capacity | PA request | Held in BH queue | Assigned to qualified reviewer | Escalated operationally |
| Notice defect | Determination | Blocked | Released after correction | Compliance escalation |
## 8.3 Human-in-the-Loop Specifications
| Escalation point | Trigger | Fields surfaced | Available actions → resulting state | Task SLA | Assignee role |
|---|---|---|---|---|---|
| Clinical review | Not straight-through | Request, criteria, evidence | Approve / refer physician / request information | Contractual clock applies | Clinical reviewer |
| Physician review | Judgment or adverse route | Clinical evidence and criteria | Approve / adverse / request information | Contractual clock applies | Physician reviewer |
| BH capacity | No qualified reviewer available | Request and queue status | Assign / hold / escalate | Contractual clock applies | BH supervisor |
[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/business-rules.md reproj=g0 -->
# 9. Compliance and Regulatory
## 9.1 Compliance Traceability Matrix
| Requirement / Rule | Enforced at | Evidence retained |
|---|---|---|
| 72-hour complete-request decision rule | SLA monitor and escalation | Receipt, completeness, decision, and notice timestamps |
| BH segregation | Routing decision and BH queue | Assignment and reviewer credential evidence |
| 42 CFR 438.210 notice content | Notice validation | Notice version, criteria citation, rationale, reviewer credential |
| Appeal boundary | Final communication and handoff | Notice and A&G handoff evidence |
## 9.2 Audit & Traceability
Automation must retain transaction receipt, validation results, criteria and version, routing outcome, human decisions, notice content, transmission status, and SLA-risk events. Retention duration is not confirmed in the supplied materials.
[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria
## 10.1 KPIs
| KPI | Target / acceptance signal |
|---|---|
| Standard decision timeliness | No decision issued after the applicable 72-hour complete-request requirement without documented escalation |
| BH routing compliance | Zero general-medical assignments for BH requests |
| Notice control | Zero released adverse notices missing required content |
| Audit traceability | Every processed request retains receipt, routing, decision, and communication evidence |
## 10.2 Acceptance Criteria
- The process routes expedited requests out of the standard path before clinical evaluation.
- A BH request cannot be assigned to an unqualified general medical reviewer.
- An adverse notice cannot be released without required rationale, criteria, rights, and reviewer data.
- Human review tasks expose the decision-driving request and clinical evidence.
[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks
## 11.1 Assumptions
| Assumption | Detail |
|---|---|
| Interfaces can be configured | Exact technical methods require confirmation. |
| Provider reconsideration stays in PA operations | The source establishes boundary and 60-day submission period but not detailed workflow. |
## 11.2 Constraints
| Constraint | Detail |
|---|---|
| Regulatory timing | 72-hour standard complete-request decision rule |
| BH review | No general-medical assignment permitted |
| Scope | Standard requests only; appeals and expedited processing excluded |

==TBD: confirm incomplete-request clock and receipt-time interpretation==
## 11.3 Dependencies
| Dependency | Type | Detail |
|---|---|---|
| EDI gateway and MedVisor interface | hard | Required for automated intake and request creation |
| Eligibility, benefit, and provider data access | hard | Required for validation |
| Criteria capability | hard | Required for routing and evidence |
| Notice-delivery channels | hard | Required for compliant communication |
| Operational baseline data | soft | Required to quantify automation benefit |
## 11.4 Risks
| Risk | Mitigation |
|---|---|
| Incorrect clock configuration | Make the rule configurable and obtain contract-team confirmation |
| Improper BH routing | Enforce queue constraint and supervisor escalation |
| Non-compliant notices | Validate required content before release |
| Undefined reconsideration process | Keep outside initial automation scope until documented |
[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
# 12. Glossary
| Term | Definition |
|---|---|
| BH | Behavioral health |
| EDI 278 | X12 Health Care Services Review transaction |
| InterQual / MCG | Clinical criteria sets used for authorization decisions |
| PA | Prior authorization |
| P2P | Peer-to-peer discussion |
| RFI | Request for Information |
| SLA | Service-level commitment |
[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps
| # | Action item |
|---|---|
| 1 | Obtain contract-team interpretation for incomplete-request and receipt-time clock calculation. |
| 2 | Define provider-reconsideration roles, sequence, notifications, and timing. |
| 3 | Confirm interface endpoints, authentication, source-of-truth ownership, and downtime procedures. |
| 4 | Capture volume, backlog, staffing, touch-time, and peak-period baseline. |
| 5 | Confirm RACI and evidence-retention requirements. |
[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=to-be/process.bpmn reproj=g0 -->
# Appendix A: Process Map and Diagrams
The BPMN diagram embedded in Section 4.1 is the future-state process model of record for the proposed automated standard-request flow. An integration-sequence diagram remains to be designed after technical interfaces are confirmed.
<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert an integration sequence showing the EDI gateway, automation service, MedVisor, eligibility/provider data, criteria capability, notification channels, and exception/retry routes.
[Refine section](delegate:refine-section?section=appendix-a)
