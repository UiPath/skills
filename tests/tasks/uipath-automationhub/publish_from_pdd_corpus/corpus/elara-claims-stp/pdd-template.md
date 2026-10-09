<!-- pdd:doc header="Motor Claims STP: Automated Adjudication and SEPA Settlement for Minor Damage Claims {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | Elara Versicherung AG" client="Elara Versicherung AG" author="Business Analysis" date="29 September 2026" version="1.0" process="Motor Claims STP: Automated Adjudication and SEPA Settlement for Minor Damage Claims {{RUN_TOKEN}}" -->

# Motor Claims STP: Automated Adjudication and SEPA Settlement for Minor Damage Claims {{RUN_TOKEN}}
<!-- pdd:section id=business-context sources=as-is/overview.md,as-is/pain-points.md,to-be/overview.md,to-be/benefits.md reproj=g0 -->
# 1. Business Context

## 1.1 Problem Statement
Elara Versicherung AG operates an automated straight-through processing path for qualifying minor motor-damage claims. The process spans the customer portal, **Guidewire ClaimCenter**, fraud scoring, photo-based assessment, rules-based adjudication, and SEPA payment initiation; the supplied operating documentation leaves compliance timers, exception visibility, payment finality, and customer-review handling partly implicit.

## 1.2 Objectives
- Retain automated adjudication for claims meeting the approved eligibility conditions.
- Dispatch and evidence the customer acknowledgment within 30 minutes of portal submission.
- Route fraud, coverage, assessment-confidence, eligibility, and payment exceptions to named teams.
- Confirm payment finality before settlement notification and closure.
- Provide auditable automated-decision transparency and a human-review route.

## 1.3 Expected Value
The target design preserves fast, rules-based settlement for eligible claims while improving operational transparency, regulatory evidence, and ownership of exceptions. Measured targets are defined in Section 10.

[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope

## 2.1 Process Identity
| Process attribute | Value |
|---|---|
| Process name | Motor Claims STP: Automated Adjudication and SEPA Settlement for Minor Damage Claims |
| Process group | Motor Claims Operations |
| Process identifier | ELARA-IT-FS-2024-0147 |
| Industry | German insurance |

## 2.2 Scope Boundaries
| In Scope | Out of Scope |
|---|---|
| Portal-submitted qualifying minor motor-damage claims | Manual claims adjudication workflow |
| Coverage, fraud, image-assessment, and eligibility routing | SIU investigation case management |
| Automated approval and SEPA SCT settlement lifecycle | Third-party liability claims |
| Customer notices, payment exceptions, and review-request handoff | Glass, theft, and partial-theft claims |

## 2.3 Systems and Applications
| System | Role in Process | Access Type |
|---|---|---|
| **Elara self-service portal** | Claim capture, evidence upload, CRN creation, event publication | both |
| **Guidewire ClaimCenter v10.1.2** | Policy/claim system of record, queues, approvals, deductions | both |
| **Fraud ML Model API** | Fraud probability score | read |
| **Solera CV API** | Damage estimate, category, and confidence | read |
| **Deutsche Bank PaymentConnect** | SEPA Credit Transfer submission and payment status | both |
| **Notification Service** | Acknowledgment and settlement notices | both |
| **Splunk SIEM** | Immutable audit events | write |

[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/process.bpmn,as-is/metrics.md,as-is/pain-points.md reproj=g0 -->
# 3. Current State

## 3.1 Overview
The current process is an event-driven STP pipeline. It validates coverage, scores fraud, assesses damage, evaluates eligibility, auto-approves qualifying claims, initiates SEPA payment, and notifies the customer; manual, SIU, and Payments Operations off-ramps exist but are incompletely represented in the source flow.

## 3.2 Current Flow
| # | Current step |
|---|---|
| 1 | Customer submits structured claim data and photo evidence through the portal; a CRN and Kafka event are created. |
| 2 | Pipeline validates completeness and active Vollkasko cover in ClaimCenter. |
| 3 | Fraud ML API returns a score; score >0.7 routes to SIU. |
| 4 | Solera CV assesses damage and returns estimate, category, and confidence. |
| 5 | Rules engine checks value, prior claims, coverage, and damage eligibility. |
| 6 | Qualifying claim is auto-approved and recorded in ClaimCenter. |
| 7 | SEPA payment is initiated through PaymentConnect. |
| 8 | Customer is notified after payment initiation. |

## 3.3 Metrics
| Metric | Current signal | Measurement method |
|---|---|---|
| End-to-end STP cycle | ≤24 hours to SEPA instruction | Functional specification target |
| Acknowledgment | ≤30 minutes | Portal and notification audit events |
| Fraud API | p95 ≤8 seconds; timeout 15 seconds | API telemetry |
| Solera CV | p95 ≤45 seconds | API telemetry |
| Availability | 99.5% monthly | Platform monitoring |
| Volume/backlog | Not recorded | Open item for Claims Analytics |

## 3.4 Pain Points
| Where | What breaks | Impact |
|---|---|---|
| Acknowledgment | Timer is not a visible process step | Compliance-breach risk |
| Exceptions | Fraud outage and low-confidence routes are absent from supplied flow | Handoff ambiguity |
| Payment | Initiation is treated as settlement | No confirmed payment-finality control |
| Human review | Required right lacks a documented work path | Customer-protection risk |

```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_Current" targetNamespace="https://elara.de/claims/current"><bpmn:process id="Process_Current" isExecutable="false"><bpmn:startEvent id="Start_Submission" name="Claim submitted"/><bpmn:serviceTask id="Task_Validate" name="Validate completeness and coverage"/><bpmn:serviceTask id="Task_Fraud" name="Score fraud"/><bpmn:serviceTask id="Task_Assess" name="Assess damage"/><bpmn:businessRuleTask id="Task_Eligibility" name="Evaluate STP eligibility"/><bpmn:serviceTask id="Task_Approve" name="Auto-approve claim"/><bpmn:serviceTask id="Task_Payment" name="Initiate SEPA payment"/><bpmn:endEvent id="End_Settled" name="Settlement initiated"/></bpmn:process></bpmn:definitions>
```

*Figure: Current BPMN process model rendered from the approved current process artifact.*

[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)
[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/activities.md,to-be/exception-handling.md,to-be/benefits.md reproj=g0 -->
# 4. Future State

## 4.1 Vision
The future state is a BPMN-orchestrated, event-driven process that retains the approved STP rules while making timers, message callbacks, exception routes, payment finality, and customer-review obligations explicit. It uses ClaimCenter as the system of record; the documented model is a business process design, not an executable implementation specification.

```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_Target" targetNamespace="https://elara.de/claims/target"><bpmn:process id="Process_Target" isExecutable="false"><bpmn:startEvent id="Start_Submission" name="Claim submitted"/><bpmn:sendTask id="Task_Acknowledge" name="Send acknowledgment"/><bpmn:boundaryEvent id="Boundary_AckTimer" attachedToRef="Task_Acknowledge" name="30-minute SLA"><bpmn:timerEventDefinition><bpmn:timeDuration>PT30M</bpmn:timeDuration></bpmn:timerEventDefinition></bpmn:boundaryEvent><bpmn:serviceTask id="Task_Validate" name="Validate claim and coverage"/><bpmn:serviceTask id="Task_Fraud" name="Score fraud"/><bpmn:serviceTask id="Task_Assess" name="Assess damage"/><bpmn:businessRuleTask id="Task_Eligibility" name="Evaluate STP eligibility"/><bpmn:serviceTask id="Task_Approve" name="Auto-approve claim"/><bpmn:serviceTask id="Task_SubmitPayment" name="Submit SEPA payment"/><bpmn:intermediateCatchEvent id="Event_PaymentStatus" name="Payment status callback"><bpmn:messageEventDefinition/></bpmn:intermediateCatchEvent><bpmn:sendTask id="Task_SettlementNotice" name="Send settlement notice"/><bpmn:endEvent id="End_Settled" name="Claim settled"/></bpmn:process></bpmn:definitions>
```

*Figure: Future BPMN process model rendered from the process model of record.*

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)

## 4.2 Target Flow
| # | BPMN element | Participant / lane | Element type | Input / message | Output / message | Route / exception path |
|---|---|---|---|---|---|---|
| 1 | Claim submitted | Customer / Portal | Start event | Claim and photos | CRN, claim event | Starts timer and validation |
| 2 | Send acknowledgment | STP Engine | Send task | CRN, contact data | Delivery record | 30-minute breach escalates |
| 3 | Validate claim and coverage | STP Engine | Activity | Claim/policy data | Validation result | Manual route if incomplete/not covered |
| 4 | Score fraud | STP Engine | Activity | Claim feature set | Fraud score | SIU if >0.7; manual if unavailable |
| 5 | Assess damage | STP Engine | Activity | Photo references | Estimate/category/confidence | Manual route if confidence <0.85 |
| 6 | Evaluate STP eligibility | STP Engine | Gateway/rule task | Assessment and history | Eligibility result | Manual route if any criterion fails |
| 7 | Auto-approve claim | STP Engine | Activity | Eligible result | Approval audit record | Continues to payment |
| 8 | Submit SEPA payment | STP Engine | Activity | Net amount and IBAN | Payment ID | Await final status |
| 9 | Payment status callback | PaymentConnect | Message event | Bank status | Confirmed/failed/returned state | Payments Operations on exception |
| 10 | Send settlement notice | Notification Service | Send task | Confirmed payment and review rights | Customer notice | Ends settled path |

## 4.2.1 Future Work Details
> **Intake and validation:** Capture the claim, deliver the statutory acknowledgment, and determine whether the claim can continue through STP.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| Portal claim event | Acknowledge; validate coverage | Complete and covered? | STP Engine | Portal | Fraud scoring or manual queue | Claim payload, CRN, policy data | Acknowledgment, validation result |

> **Automated adjudication:** Apply fraud, damage, and eligibility controls without relaxing any approved threshold.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| Validated claim | Fraud scoring; CV assessment; rule evaluation; approval | Fraud outcome; confidence; eligible for STP | STP Engine | Validation | Payment, SIU, or manual queue | Features, photos, policy history | Decisions, assessments, audit record |

> **Settlement and closure:** Submit only SEPA SCT payment, wait for final bank state, notify the claimant, and preserve a review path.

| Trigger/event | Activities | Key gateway | Owner/participant | Flows From | Flows To | Inputs/messages | Outputs/messages |
|---|---|---|---|---|---|---|---|
| Approved claim | Submit payment; wait for status; notify | Payment confirmed? | STP Engine / PaymentConnect | Approval | Settlement or Payments Operations | Net payment, bank callback | Payment state, settlement notice |

## 4.3 What Changes
| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Acknowledgment | Annotated compliance requirement | Explicit activity, timer, and escalation | Demonstrate SLA control | Boundary timer and compliance event |
| Exceptions | Some routes exist only in technical prose | Named BPMN routes and owners | Remove handoff ambiguity | Gateways for fraud outage and confidence failure |
| Payment | Initiation treated as settlement | Callback before notification/closure | Ensure finality | Payment status event and gateway |
| Human review | Notice requirement only | Managed escalation route | Meet customer safeguards | Preserve evidence and assign senior adjuster |

## 4.4 BPMN Work Summary
The future model contains automated portal, validation, scoring, assessment, rules, payment, and notification activities; human-owned exception endpoints remain for Motor Claims Operations, SIU, Payments Operations, and senior claims adjusters.

[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/business-rules.md reproj=g0 -->
# 5. Business Rules

| Rule ID | Description |
|---|---|
| BR-001 | Acknowledgment is dispatched within 30 minutes of portal submission; a missed window creates a compliance escalation. |
| BR-002 | Fraud score greater than 0.7 unconditionally routes to SIU. |
| BR-003 | Fraud API error or timeout after 15 seconds routes to manual adjustment with `FRAUD_API_UNAVAILABLE`. |
| BR-004 | Solera confidence below 0.85 routes to manual adjustment. |
| BR-005 | STP requires damage estimate ≤€5,000, fraud score ≤0.7, zero prior claims in 12 months, active Vollkasko, and eligible MINOR damage. |
| BR-006 | Glass, theft/partial theft, Haftpflicht, and Teilkasko claims are excluded from STP. |
| BR-007 | Net payout equals assessed damage less ClaimCenter deductible. |
| BR-008 | German domestic settlements use SEPA Credit Transfer only. |
| BR-009 | Payment errors retry after 2s, 8s, and 32s; persistent failure routes to Payments Operations. |

[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md reproj=g0 -->
# 6. Data Model

## 6.1 Entities
| Entity | Description |
|---|---|
| Motor STP Claim | CRN, policy, loss, photos, assessment, fraud, eligibility, approval, and payment state. |
| PolicyDetails | ClaimCenter policy snapshot, cover, deductible, and claimant IBAN. |
| Assessment | Solera estimate, category, confidence, and assessment ID. |
| Payment instruction | ISO 20022 SCT instruction, payment ID, and lifecycle status. |
| Audit event | Immutable claim event with UTC time, outcome, `STP-ENGINE-v2`, and input-payload hash. |

## 6.2 Data Inputs and Outputs
| Artifact | Source / Destination | Format | Consumed / Produced By |
|---|---|---|---|
| Claim submission | Portal → STP Engine | JSON/photo blob references | Intake |
| Policy snapshot | ClaimCenter → STP Engine | REST JSON | Validation and calculation |
| Fraud score | Fraud ML → STP Engine | REST JSON | Fraud gateway |
| Damage assessment | Solera → STP Engine | REST JSON | Eligibility and payment |
| SEPA instruction | STP Engine → PaymentConnect | ISO 20022 pain.001.003.03 | Settlement |
| Audit event | STP Engine → Splunk | Structured event | All processing steps |

## 6.3 Field-Level Data Dictionary
| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
|---|---|---|---|---|---|
| crn | string | ELR-YYYY-XXXXXXXX | Unique claim reference | Yes | PII-linked |
| policy_number | string | ClaimCenter identifier | Active policy | Yes | PII-linked |
| claimant_iban | string | IBAN | Valid bank account | Yes for settlement | PII |
| estimated_damage_eur | float | EUR | ≤€5,000 for STP | Yes | Financial |
| fraud_score | float | 0.0-1.0 | >0.7 → SIU | Yes | Restricted |
| confidence_score | float | 0.0-1.0 | <0.85 → manual | Yes | Restricted |
| payment_status | enum | PaymentConnect value | INITIATED/CONFIRMED/FAILED | Yes after payment | Financial |

## 6.4 Data Flow and Lineage
| # | Data movement |
|---|---|
| 1 | Portal creates CRN and submits claim/pictures to pipeline. |
| 2 | Pipeline retrieves PolicyDetails from ClaimCenter. |
| 3 | Pipeline submits features to Fraud ML and photos to Solera. |
| 4 | Pipeline stores assessments and decision evidence in ClaimCenter/Splunk. |
| 5 | Pipeline submits net SCT instruction to PaymentConnect. |
| 6 | Payment status updates ClaimCenter before settlement notice. |

## 6.5 Integrations
| Integration (System → System) | Fields passed | Connector / type | Endpoint + Auth |
|---|---|---|---|
| Portal → Kafka | CRN and claim event | Internal event | Not confirmed |
| STP → ClaimCenter | Policy/claim/approval/payment record | REST JSON | ClaimCenter REST API v2 |
| STP → Fraud ML | Claim features | REST JSON, mTLS | Internal fraud score endpoint |
| STP → Solera | Photo references | REST JSON, API key | Solera CV v3 endpoint |
| STP → PaymentConnect | SCT instruction | REST JSON | PaymentConnect API; auth not confirmed |

==TBD: confirm the PaymentConnect callback endpoint, authentication, and final-status contract at solution design.==

[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
# 7. People

## 7.1 Roles and Personas
| Stakeholder | Responsibility |
|---|---|
| Policyholder | Submits claim, receives notices, may request human review. |
| STP Engine | Automated system persona executing validation, decisioning, approval, payment, and audit events. |
| Motor Claims Operations | Handles manual-adjuster queue, incomplete claims, low confidence, and ineligible claims. |
| Special Investigations Unit | Owns high-fraud-score referrals. |
| Payments Operations | Resolves persistent payment failures and returns. |
| Claims Operations duty manager | Receives acknowledgment-SLA escalations. |
| Chief Compliance Office | Receives reportable compliance events. |
| Senior claims adjuster | Reviews customer contests of automated decisions within two business days. |
| Claims Analytics | Produces quarterly BaFin aggregate reporting. |

[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=entities/people/ reproj=g0 -->
## 7.2 RACI
| Activity/Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Automated STP execution | STP Engine | Claims Platform | Claims Operations | Policyholder |
| Manual adjustment | Motor Claims Operations | Head of Claims Operations | STP Engine | Policyholder |
| SIU referral | SIU | Head of Claims Operations | Compliance | Policyholder where appropriate |
| Payment exception | Payments Operations | Treasury Operations | Claims Platform | Policyholder |
| Automated-decision review | Senior claims adjuster | Head of Claims Operations | Compliance | Policyholder |
| Regulatory reporting | Claims Analytics | CCO | Data Science | BaFin |

[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/exception-handling.md reproj=g0 -->
# 8. Exceptions and Error Handling

## 8.1 Known Exceptions
| Exception | Trigger | AS-IS Handling | TO-BE Handling |
|---|---|---|---|
| Invalid/incomplete coverage | Validation failure | Manual queue | Manual route with reason code |
| High fraud | Score >0.7 | SIU referral | Unconditional SIU terminal path with model evidence |
| Fraud outage | API error/timeout | Technical requirement only | Explicit manual route `FRAUD_API_UNAVAILABLE` |
| Low CV confidence | <0.85 | ClaimCenter configuration | Explicit manual route |
| Payment failure | Persistent API error | Payments Operations | Callback/return state, payment investigation, terminal exception |
| Customer review request | Portal or helpline | Requirement only | Senior-adjuster work path within two business days |

## 8.2 Exception Data State Transitions
| Exception | Affected record | State on entry | State on resolution | State on terminal failure |
|---|---|---|---|---|
| Fraud/SIU | Claim | SIU | SIU disposition | SIU referral retained |
| Manual route | Claim | MANUAL | Adjusted/settled | Manual queue retained |
| Payment failure | Payment/claim | PAYMENT_FAILED | CONFIRMED after re-submit | Payment exception |
| Review request | Claim | REVIEW_REQUESTED | REVIEW_COMPLETED | Escalated review |

## 8.3 HITL and Action Center Task Form Specifications
| Escalation point | Trigger | Fields surfaced | Available actions → resulting state | Task SLA | Assignee role |
|---|---|---|---|---|---|
| Customer review request | Customer contests automated decision | CRN, policy, decision evidence, assessment, fraud outcome, customer statement | Uphold / amend / request information → reviewed state | Two business days to assignment | Senior claims adjuster |

<!-- doc:placeholder kind="screenshot" -->
> [!NOTE]
> **Screenshot Placeholder**
> Insert screenshot: customer-review task showing automated decision evidence and review actions.

[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/business-rules.md reproj=g0 -->
# 9. Compliance and Regulatory

## 9.1 Compliance Traceability Matrix
| Requirement / Rule | Enforced at | Evidence retained |
|---|---|---|
| VVG §13 / BR-001 | Acknowledgment activity and 30-minute timer | Submission/delivery timestamps and escalation event |
| GDPR Article 22 | Settlement notice and review-request route | Decision record, notice, review task |
| BaFin MaACH | Fraud/CV decision routes and model governance | Feature-level logs and validation report |
| BR-002 to BR-006 | Fraud, confidence, and eligibility gateways | Inputs, scores, assessment, rule result, reason code |
| SEPA Regulation / BR-008 | Payment submission | SCT instruction and payment ID |
| BR-009 | Payment callback exception route | Retry evidence and Operations handoff |

## 9.2 Audit and Traceability
Every STP step emits a structured Splunk audit event containing CRN, ISO 8601 UTC timestamp, step, outcome, `STP-ENGINE-v2`, and SHA-256 input-payload hash. Claim records and audit evidence are retained for ten years; fraud feature logs are restricted and retained for five years.

[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria

## 10.1 KPIs
| KPI | Target / acceptance signal |
|---|---|
| STP cycle time | ≤24 hours from submission to SEPA instruction submitted |
| Acknowledgment | Within 30 minutes; zero un-escalated breaches |
| Fraud API | p95 ≤8 seconds; safe manual route at 15-second timeout |
| Solera CV | p95 ≤45 seconds; confidence <0.85 routes manual |
| Pipeline availability | 99.5% monthly |
| Payment finality | Settlement notice only after confirmed payment-state event |
| Customer transparency | Every settlement notice includes automated-decision and human-review information |

## 10.2 Acceptance Criteria
- A claim with fraud score >0.7 never reaches automated approval or payment.
- A claim above €5,000 never reaches automated approval.
- A domestic payment instruction is SCT only.
- A payment failure after the defined retries is handed to Payments Operations.
- Customer review requests are assigned to a senior claims adjuster within two business days.

[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks

## 11.1 Assumptions
| Assumption | Detail |
|---|---|
| Existing source scope | PDD covers qualifying minor motor-damage STP, not end-to-end motor claims. |
| Payment notification | Future settlement notification follows payment confirmation, subject to callback-contract confirmation. |

## 11.2 Constraints
| Constraint | Detail |
|---|---|
| Eligibility ceiling | €5,000 absolute limit |
| Fraud threshold | >0.7 unconditional SIU route |
| Payment rail | SEPA SCT only for domestic German claims |
| Data residency | EU Frankfurt region |
| Retention | 10 years claim/audit; five years fraud feature log |

## 11.3 Dependencies
| Dependency | Type (hard/soft) | Detail |
|---|---|---|
| ClaimCenter policy/history data | hard | Must provide active cover, deductible, IBAN, and prior-claim history. |
| Fraud ML API | hard | Must be available or safely route to manual review. |
| Solera CV API | hard | Must return assessment/confidence or route to manual review. |
| PaymentConnect callback/status service | hard | Contract must define final, failed, and returned states. |
| Notification Service | hard | Must produce delivery evidence for acknowledgement and settlement notices. |

## 11.4 Risks
| Risk | Mitigation |
|---|---|
| Payment initiation mistaken for settlement | Await confirmed payment status before settlement notice. |
| Missing prior-claim data source | Resolve design dependency before build. |
| SLA breach not surfaced | Timer-based compliance escalation and reporting. |
| Human-review process not implemented | Define queue, fields, states, and owner before go-live. |

[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
# 12. Glossary

| Term | Definition |
|---|---|
| BaFin | German Federal Financial Supervisory Authority. |
| ClaimCenter | Guidewire claims-management system of record. |
| CRN | Elara Claim Reference Number. |
| GDPR | General Data Protection Regulation. |
| MaACH | BaFin minimum requirements for automated claims handling. |
| SCT | SEPA Credit Transfer. |
| SIU | Special Investigations Unit. |
| STP | Straight-through processing. |
| VVG | German Insurance Contract Act. |
| Vollkasko | Comprehensive motor insurance coverage. |

[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps

| # | Action item |
|---|---|
| 1 | Confirm prior-claim-history source, interface, and audit evidence. |
| 2 | Confirm PaymentConnect callback/polling contract, returns, and reconciliation ownership. |
| 3 | Define after-cutoff TARGET2 treatment and notification wording. |
| 4 | Define customer-review queue, fields, state transitions, and closure communication. |
| 5 | Obtain Claims Analytics volume, peak, backlog, and aging baselines. |
| 6 | Validate the process design with Claims Operations, Payments Operations, Compliance, and Treasury before solution design. |

[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=derived reproj=g0 -->
# Appendix A: Process Map and Diagrams

The future BPMN diagram embedded in Section 4.1 is the process model of record for the target state. It represents the process from claim submission through acknowledgment, validation, fraud and damage decisioning, payment-status finality, customer notification, and the principal manual, SIU, and payment-exception terminal outcomes.

<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert integration sequence diagram showing Portal, Kafka, ClaimCenter, Fraud ML, Solera, PaymentConnect, Notification Service, Splunk, and payment-status callbacks.

[Refine section](delegate:refine-section?section=appendix-a)
