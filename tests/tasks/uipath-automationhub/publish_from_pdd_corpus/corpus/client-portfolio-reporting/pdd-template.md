<!-- pdd:doc header="Client Portfolio Reporting {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | Wealth Management Operations" client="Wealth Management Operations" author="Business Analysis Team" date="29 September 2026" version="1.0" process="Client Portfolio Reporting {{RUN_TOKEN}}" -->

# Client Portfolio Reporting {{RUN_TOKEN}}
<!-- pdd:section id=business-context sources=as-is/overview.md,as-is/pain-points.md,to-be/seeds.md,to-be/kpis.md reproj=g0 -->
# 1. Business Context

## 1.1 Problem Statement
Wealth Management Operations produces approximately 2,500 regulated client portfolio reports per cycle for full-service advisory relationships, including UHNW private bank and trust households. The current process averages four days and achieves approximately 85% on-time delivery, leaving roughly 375 reports late per cycle. Advisors manually copy positions and prices across systems, personalization is inconsistent, and late compliance rework compresses the available correction window.

## 1.2 Objectives
- Reduce end-to-end cycle time from 4 days to 2 days through automated data preparation and AI-assisted drafting.
- Raise on-time delivery from 85% to 98% through earlier controls, routing, and delivery monitoring.
- Reduce compliance rework from 12% to under 3% through first-pass automated checks and human compliance disposition.
- Raise personalization coverage from 60% to 95% through advisor-reviewed AI insight drafts.
- Raise client acknowledgment within seven days from 45% to 80% through portal/email engagement monitoring and follow-up.

## 1.3 Expected Value
The future process preserves advisor, compliance, and supervisory judgment while removing mechanical preparation work. It improves consistency, makes delivery and engagement observable, and produces stronger evidence of regulatory control. Measured targets are defined in Section 10.

[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope

## 2.1 Process Identity

| Process name | Process group | Process identifier | Industry |
|---|---|---|---|
| Client Portfolio Reporting | Wealth Management Operations | WM-CPR-001 | Wealth management / investment advisory |

## 2.2 Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| Monthly, quarterly, and ad-hoc client portfolio reports | Prospect marketing materials |
| Data preparation, personalization, research, compliance, approval, delivery, retention | Trade execution reports |
| Full-service advisory, UHNW private bank, and trust households | GIPS composites |
| Portal/email delivery and acknowledgment follow-up | Form ADV, Form CRS, and other regulatory filings |

## 2.3 Systems and Applications

| System | Role in Process | Access Type |
|---|---|---|
| Portfolio accounting system | Supplies portfolio positions and supports issue investigation | Read / write by source owners |
| Market-data source | Supplies current prices and benchmarks | Read |
| Reporting Engine | Holds the report shell and workflow content | Both |
| Client portal | Delivers reports and supports engagement visibility | Both |
| Email | Delivers reports and alternate-channel retry | Both |
| CRM | Records delivery and acknowledgment events | Both |
| Compliance WORM archive | Retains reporting packages and evidence | Write / read |

[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=as-is/overview.md,as-is/process.bpmn,as-is/steps/,as-is/metrics.md,as-is/pain-points.md reproj=g0 -->
# 3. Current State

## 3.1 Overview
The current workflow is a five-team, cross-functional process spanning portfolio accounting, market data, the Reporting Engine, compliance review, and dual-channel delivery. Manual data movement, late compliance rework, inconsistent personalization, and limited engagement visibility create delivery and control risk.

## 3.2 Current Flow

| # | Current step |
|---:|---|
| 1 | Investment Operations Analyst aggregates positions, market data, time-weighted returns, benchmark variance, and attribution. |
| 2 | Financial Advisor adds personalized insights, recommendations, and notes. |
| 3 | Research Desk Strategist adds relevant macro commentary. |
| 4 | Compliance Analyst reviews disclosures; issues return to Advisor and, when applicable, Research. |
| 5 | Supervisory Principal provides final approval under FINRA Rule 2210. |
| 6 | Client Service delivers through portal and email, logs evidence, and archives the package. |

## 3.3 Metrics

| Metric | Current signal | Measurement method |
|---|---:|---|
| Reports per cycle | Approximately 2,500 | Process-owner estimate |
| End-to-end cycle time | 4 days | Process-owner estimate |
| On-time delivery | 85% | Process-owner estimate |
| Compliance rework | 12% / approximately 300 reports | Process-owner estimate |
| Personalization coverage | 60% | Process-owner estimate |
| Client acknowledgment within 7 days | 45% | Process-owner estimate |

## 3.4 Pain Points

| Where | What breaks | Impact |
|---|---|---|
| Data preparation | Advisors manually copy positions and prices across systems | Handling time and data-quality risk |
| Personalization | Coverage and quality are inconsistent | Only 60% of reports include advisor-curated insights |
| Compliance | Review occurs late and creates rework loops | 12% rework rate; delivery window compression |
| Delivery | Limited systematic read-confirmation and follow-up | 45% acknowledgment within seven days |

The approved AS-IS BPMN process model is the model of record and is available in the process documentation.

[Open AS-IS diagram](delegate:open-diagram?which=as-is&anchor=current-state)
[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/seeds.md,to-be/process.bpmn,to-be/kpis.md,to-be/acceptance-criteria.md reproj=g0 -->
# 4. Future State

## 4.1 Vision
The redesigned process orchestrates automated data preparation, AI-assisted insight drafting, research curation, and first-pass compliance checks while retaining human review for advisor judgment, research validation, compliance disposition, and supervisory approval. The approved BPMN model introduces controlled exception loops, dual-channel delivery recovery, seven-day acknowledgment follow-up, and retained audit evidence.

The approved TO-BE BPMN process model is the model of record and is available in the process documentation.

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)

## 4.2 Target Flow

| # | BPMN element | Participant / lane | Element type | Input / message | Output / message | Route / exception path |
|---:|---|---|---|---|---|---|
| 1 | Start reporting work | Investment Operations | Start event | Schedule or ad-hoc request | Reporting work item | Starts process |
| 2 | Prepare and validate data | Investment Operations | Activity | Positions and market data | Validated reporting data | Portfolio-data issue loops to resolution |
| 3 | Draft personalized insights | Financial Advisor | Activity | Validated report data | AI draft | Advisor review required |
| 4 | Review and edit insights | Financial Advisor | Activity | AI draft | Approved advisor content | Edit audit is recorded |
| 5 | Curate and validate research | Research Desk | Activities | Holdings and macro package | Validated commentary | Proceeds to compliance |
| 6 | Initial compliance check and review | Compliance | Activities / gateway | Report draft | Clear or correction request | Corrections repeat compliance review |
| 7 | Final approval | Supervisory Principal | User task | Cleared report | Approved report | Required before delivery |
| 8 | Deliver and retain | Client Service | Activities / gateway | Approved PDF | Delivery and archive evidence | Retry alternate channel, then follow-up |
| 9 | Wait for acknowledgment | Client Service | Timer / gateway | Retained delivery | Acknowledgment status | Follow-up after seven days if absent |

## 4.2.1 Future Work Details

### Investment Operations
> Automated preparation validates portfolio and market data before client-facing content is drafted.

| Trigger/event | Activities | Key gateway | Owner | Flows From | Flows To | Inputs | Outputs |
|---|---|---|---|---|---|---|---|
| Schedule or request | Prepare data; resolve exceptions; cached-data disclosure | Portfolio data complete; market data current | Investment Operations | Start | Advisor | Positions, market data | Validated data or disclosure |

### Advisor and Research
> AI drafts and curates content; accountable humans review and improve it.

| Trigger/event | Activities | Key gateway | Owner | Flows From | Flows To | Inputs | Outputs |
|---|---|---|---|---|---|---|---|
| Validated data | Draft insights; review/edit; record audit; curate/validate research | Human review completion | Advisor and Research | Operations | Compliance | Data and commentary | Reviewed report content |

### Compliance and Supervision
> Automated checks assist but never replace regulatory judgment or approval.

| Trigger/event | Activities | Key gateway | Owner | Flows From | Flows To | Inputs | Outputs |
|---|---|---|---|---|---|---|---|
| Reviewed report | Initial check; analyst review; correction loop; final approval | Compliance clear | Compliance and Supervision | Advisor/Research | Client Service | Report draft | Approved report or correction request |

### Client Service
> Delivery is observable, recoverable, retained, and followed by acknowledgment monitoring.

| Trigger/event | Activities | Key gateway | Owner | Flows From | Flows To | Inputs | Outputs |
|---|---|---|---|---|---|---|---|
| Approved report | Portal/email delivery; retry; follow-up; archive; acknowledgment follow-up | Delivery successful; acknowledgment received | Client Service | Supervision | End | Approved PDF | Delivery, retention, and engagement evidence |

## 4.3 What Changes

| Area | AS-IS | TO-BE | Why | How |
|---|---|---|---|---|
| Data preparation | Manual cross-system work | Automated validation and preparation | Reduce handling effort and data risk | Workflow and integrations |
| Personalization | 60% coverage; manual drafting | AI draft with advisor review | Improve quality and coverage | AI assistance plus human approval |
| Compliance | Late manual review | First-pass check plus analyst review | Reduce rework and identify issues earlier | Policy-checking assistance and review gate |
| Audit evidence | Advisor edits not systematically evidenced | User ID, timestamp, and prior text retained | Demonstrate human judgment | Immutable edit-audit record |
| Delivery | Limited engagement visibility | Delivery monitoring and seven-day follow-up | Improve acknowledgment | Portal/email events and Client Service task |

## 4.4 BPMN Work Summary
The model contains automated service activities for data preparation, AI drafting/curation, edit-audit recording, delivery, retry, and retention; human user activities for review, correction, approval, and follow-up; and gateways for data, compliance, delivery, and acknowledgment decisions.

[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=as-is/business-rules.md,to-be/seeds.md reproj=g0 -->
# 5. Business Rules

| Rule ID | Description |
|---|---|
| BR-001 | Calculate time-weighted returns, benchmark variance, and attribution before advisor review. |
| BR-002 | Advisors add client-specific insights and recommendations; future AI drafts require advisor review. |
| BR-003 | Research commentary must be relevant to the client holdings and be validated by Research. |
| BR-004 | Compliance findings require correction and repeat review before final approval. |
| BR-005 | Supervisory Principal approval is required before delivery. |
| BR-006 | Delivered reporting packages must be logged and retained in the compliance WORM archive. |
| BR-007 | Client PII must be encrypted in transit and at rest under Regulation S-P. |
| BR-008 | Books and records are retained for five years, with the first two years easily accessible, under SEC Rule 204-2. |
| BR-009 | Cached end-of-day market data requires a delayed-data disclosure. |
| BR-010 | Delivery failures use alternate-channel retry before direct Client Service follow-up. |
| BR-011 | Advisor edits to AI-drafted insights retain advisor user ID, timestamp, and prior text changed. |

[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md,to-be/acceptance-criteria.md reproj=g0 -->
# 6. Data Model

## 6.1 Entities

| Entity | Description |
|---|---|
| Client portfolio report | Client-facing report finalized as PDF |
| Portfolio positions | Holdings sourced from the portfolio accounting system |
| Market and benchmark data | Inputs to performance calculations |
| Macro commentary package | Research content selected for holdings |
| Advisor insight draft | AI-drafted, advisor-reviewed personalized content |
| Insight edit audit record | User ID, timestamp, and prior text changed |

## 6.2 Data Inputs and Outputs

| Artifact | Source / Destination | Format | Consumed / Produced By |
|---|---|---|---|
| Portfolio positions | Portfolio accounting system to Reporting Engine | Not confirmed | Investment Operations |
| Market and benchmark data | Market-data source to Reporting Engine | Not confirmed | Investment Operations |
| Client portfolio report | Reporting Engine to portal/email/CRM/WORM archive | PDF final package | All process participants |
| Macro commentary package | Research Desk to Reporting Engine | Not confirmed | Research Desk Strategist |

## 6.3 Field-Level Data Dictionary

| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
|---|---|---|---|---|---|
| Client identifier | String | Firm-defined | Valid client record | Yes | PII |
| Portfolio positions | Structured data | System-defined | Reconciled holdings | Yes | Confidential |
| Performance metrics | Decimal | Percent / currency | Calculated values | Yes | Confidential |
| Advisor edit user ID | String | Identity ID | Authorized advisor | Conditional | Audit evidence |
| Advisor edit timestamp | Datetime | ISO timestamp | Valid event time | Conditional | Audit evidence |
| Prior text changed | Text | Versioned content | Original AI draft text | Conditional | Confidential |

## 6.4 Data Flow and Lineage

| # | Data movement |
|---:|---|
| 1 | Positions and market data enter the Reporting Engine for validation and calculation. |
| 2 | Validated performance data feeds the report shell and AI insight draft. |
| 3 | Advisor and research-reviewed content feeds compliance review. |
| 4 | Approved PDF is delivered, logged in CRM, and retained in the WORM archive. |
| 5 | Delivery and acknowledgment events produce operational and audit evidence. |

## 6.5 Integrations

| Integration | Fields passed | Connector / type | Endpoint + Auth |
|---|---|---|---|
| Portfolio accounting → Reporting Engine | Positions, balances, holdings | API or managed integration | Not confirmed |
| Market data → Reporting Engine | Prices, benchmarks | API or managed integration | Not confirmed |
| Reporting Engine → Portal/Email/CRM/WORM | PDF, delivery status, acknowledgment, archive reference | API or managed integration | Not confirmed |

==TBD: confirm the integration endpoints and authentication at SDD==

[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
# 7. People

## 7.1 Roles and Personas

| Stakeholder | Responsibility |
|---|---|
| Investment Operations Analyst | Owns data preparation and portfolio-data issue investigation. |
| Financial Advisor | Applies human judgment to insights, recommendations, and AI drafts. |
| Research Desk Strategist | Validates macro commentary relevance. |
| Compliance Analyst | Reviews compliance findings and controls the correction loop. |
| Supervisory Principal | Provides final approval before delivery. |
| Client Service Associate | Manages delivery exceptions and acknowledgment follow-up. |
| AI Insight Assistant | Drafts insights for advisor review; no final authority. |
| AI Research Assistant | Curates candidate commentary for strategist validation. |
| AI Compliance Assistant | Performs first-pass checks for analyst review. |

[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=entities/people/,to-be/seeds.md reproj=g0 -->
# 7.2 RACI

| Activity / Stage | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Data preparation | Investment Operations Analyst | Investment Operations | Data-source owners | Financial Advisor |
| Insight review | Financial Advisor | Financial Advisor | Compliance as needed | Client Service |
| Research validation | Research Desk Strategist | Research Desk | Financial Advisor | Compliance |
| Compliance review | Compliance Analyst | Compliance | Advisor, Research | Supervisory Principal |
| Final approval | Supervisory Principal | Supervisory Principal | Compliance Analyst | Client Service |
| Delivery and acknowledgment follow-up | Client Service Associate | Client Service | Financial Advisor | Compliance |

[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=as-is/exception-handling.md,to-be/seeds.md reproj=g0 -->
# 8. Exceptions and Error Handling

## 8.1 Known Exceptions

| Exception | Trigger | AS-IS Handling | TO-BE Handling |
|---|---|---|---|
| Market-data outage | Current data unavailable | Cached end-of-day data and delayed-data disclosure | Automated fallback and mandatory disclosure task |
| Portfolio-data issue | Missing or inconsistent positions | Investigation by Investment Operations; formal rules open | Held resolution loop with documented escalation criteria to be confirmed |
| Compliance finding | Disclosure or regulatory issue | Advisor/Research correction and repeat review | First-pass check, analyst disposition, correction loop, repeat review |
| Delivery failure | Portal or email failure | Alternate-channel retry then Client Service follow-up | Automated retry, tracked task, and follow-up evidence |
| Missing acknowledgment | No acknowledgment in seven days | No systematic follow-up | Client Service follow-up task after seven-day timer |

## 8.2 Exception Data State Transitions

| Exception | Affected record | State on entry | State on resolution | State on terminal failure |
|---|---|---|---|---|
| Portfolio-data issue | Reporting work item | Held for investigation | Released to validation | Escalated / open |
| Compliance finding | Report draft | Flagged | Cleared for approval | Returned for correction |
| Delivery failure | Approved report | Delivery failed | Delivered / retained | Client Service follow-up |
| Missing acknowledgment | Delivery record | Awaiting acknowledgment | Acknowledged | Follow-up open |

## 8.3 HITL and Action Center Task Form Specifications

| Escalation point | Trigger | Fields surfaced | Available actions → resulting state | Task SLA | Assignee role |
|---|---|---|---|---|---|
| Advisor insight review | AI draft available | Draft, portfolio context, prior text | Approve/edit → reviewed; return → redraft | Within Advisor stage SLA | Financial Advisor |
| Compliance review | Initial check complete | Findings, draft, disclosures | Clear → approval; return → correction | 1 day | Compliance Analyst |
| Acknowledgment follow-up | No acknowledgment after 7 days | Client, delivery evidence, contact history | Follow up → tracked outcome | Not confirmed | Client Service Associate |

[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=as-is/compliance.md,to-be/acceptance-criteria.md reproj=g0 -->
# 9. Compliance and Regulatory

## 9.1 Compliance Traceability Matrix

| Requirement / Rule | Enforced at | Evidence retained |
|---|---|---|
| SEC Marketing Rule | Compliance Analyst review and correction loop | Findings, disposition, corrected report |
| FINRA Rule 2210 | Supervisory Principal approval | Approval event and timestamp |
| Regulation S-P | Data transfer and storage controls | Encryption-control evidence ==TBD: confirm system-level encryption evidence== |
| SEC Rule 204-2 | WORM archive and accessible retention | Archive reference and retention evidence |
| BR-011 AI edit audit | Advisor review/edit stage | User ID, timestamp, and prior text changed |

## 9.2 Audit and Traceability
The future process timestamps data preparation, advisor edits, research validation, compliance findings, approvals, delivery events, acknowledgment activity, and archive references. The five-year retention requirement and first-two-years accessibility obligation are retained as controls. The advisor edit audit record is required evidence of meaningful human judgment.

[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/kpis.md,to-be/acceptance-criteria.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria

## 10.1 KPIs

| KPI | Target / acceptance signal |
|---|---|
| End-to-end cycle time | 2 days |
| On-time delivery | 98% |
| Compliance rework rate | Under 3% |
| Personalization coverage | 95% of reports with advisor-curated insights |
| Client acknowledgment within 7 days | 80% |

## 10.2 Acceptance Criteria
- Advisor edits to AI-drafted insights retain the advisor user ID, edit timestamp, and prior text changed.
- No report is delivered without Compliance Analyst clearance and Supervisory Principal approval.
- AI assistants provide drafts/checks only; final advisor, compliance, and supervisory judgment remains human.
- Delivery failures retry the alternate channel and create follow-up evidence.
- Reports lacking acknowledgment after seven days create a Client Service follow-up task.

[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks

## 11.1 Assumptions

| Assumption | Detail |
|---|---|
| Ad-hoc flow | Uses the same approved process baseline unless an approved exception applies. |
| Human oversight | Advisor, Compliance, and Supervision retain final authority. |

## 11.2 Constraints

| Constraint | Detail |
|---|---|
| Regulatory controls | SEC Marketing Rule, FINRA Rule 2210, Regulation S-P, and SEC Rule 204-2 apply. |
| Scope | Prospect materials, trade reports, GIPS composites, Form ADV, and Form CRS are excluded. |
| Technical control detail | Not confirmed. |

==TBD: confirm system-level encryption evidence, technical access controls, and retention accessibility implementation==

## 11.3 Dependencies

| Dependency | Type | Detail |
|---|---|---|
| Portfolio accounting integration | Hard | Required for validated positions and exception investigation. |
| Market-data integration | Hard | Required for current pricing; cached-data fallback required. |
| Portal, email, CRM, and WORM integration | Hard | Required for delivery, engagement, and retention evidence. |
| AI assistant governance | Hard | Required to enforce review, audit, and non-autonomous approval boundaries. |

## 11.4 Risks

| Risk | Mitigation |
|---|---|
| Portfolio-data exception rule remains incomplete | Confirm pause, escalation, approval, and proceed criteria with team lead. |
| AI output could be rubber-stamped | Require advisor review and immutable edit audit evidence. |
| Compliance rework may still delay delivery | Use first-pass checks and monitor rework rate. |
| Engagement remains unobservable | Implement portal/email tracking and seven-day follow-up. |

[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
# 12. Glossary

| Term | Definition |
|---|---|
| AI | Artificial intelligence used for draft generation, curation, or first-pass checks. |
| FINRA | Financial Industry Regulatory Authority. |
| GIPS | Global Investment Performance Standards. |
| PII | Personally identifiable information. |
| SEC | U.S. Securities and Exchange Commission. |
| WORM | Write once, read many retention storage. |
| UHNW | Ultra-high-net-worth. |

[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps

| # | Action item |
|---:|---|
| 1 | Confirm formal pause, escalation, approval, and proceed criteria for portfolio-accounting data issues. |
| 2 | Confirm named systems, endpoints, authentication, and source-of-truth ownership. |
| 3 | Confirm encryption-control and accessible-retention evidence. |
| 4 | Define delivery-dispute handling and acknowledgment follow-up escalation thresholds. |
| 5 | Validate the process design with technical and compliance stakeholders before solution design. |

[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=as-is/process.bpmn,to-be/process.bpmn reproj=g0 -->
# Appendix A: Process Map and Diagrams

The approved AS-IS and TO-BE BPMN process models are the process models of record. The TO-BE model captures the automated and human-controlled process, including data validation, edit audit evidence, compliance loops, delivery recovery, and acknowledgment monitoring.

<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert integration sequence diagram showing portfolio accounting, market data, Reporting Engine, AI assistance, portal, email, CRM, and WORM archive.

[Refine section](delegate:refine-section?section=appendix-a)
