<!-- pdd:doc header="Orvane Sales Command Center {{RUN_TOKEN}} | Process Definition Document" footer="Confidential | Orvane Medical" client="Orvane Medical" author="Local Developer" date="29 September 2026" version="1.0" process="Orvane Sales Command Center {{RUN_TOKEN}}" -->

# Orvane Sales Command Center {{RUN_TOKEN}}

<!-- pdd:section id=business-context sources=to-be/overview.md reproj=g0 -->
# 1. Business Context

## 1.1 Problem Statement
Orvane Sales users currently depend on predefined Power BI reports for sales, inventory, contract, pricing, rebate, and compliance questions. The Orvane Sales Command Center provides a governed conversational path from authorized insight to controlled action without bypassing commercial, security, or regulatory controls.

## 1.2 Objectives
- Return an authorized initial insight in under 45 seconds.
- Enforce role- and record-level access before retrieval.
- Route material actions through approval and MFA where required.
- Retain complete evidence for queries, exports, approvals, and actions.

## 1.3 Expected Value
The capability reduces dependency on newly developed reports, supports faster data-informed decisions, and makes action execution auditable. Measured acceptance targets are in Section 10.

[Refine section](delegate:refine-section?section=business-context)

<!-- pdd:section id=scope sources=as-is/scope.md,entities/applications/ reproj=g0 -->
# 2. Scope

## 2.1 Process Identity
| Process name | Process group | Process identifier | Industry |
| --- | --- | --- | --- |
| Orvane Sales Command Center | Sales Operations | ORV-SCC-001 | Medical devices |

## 2.2 Scope Boundaries
| In scope | Out of scope |
| --- | --- |
| Natural-language sales and operational inquiries | Replacement of CRM, Snowflake, TMS, or CIP data platforms |
| Priority alerts and governed recommendations | Creation of new contractual policy |
| Approval, MFA, execution, confirmation, and evidence capture | Autonomous override of compliance or price controls |

## 2.3 Systems and Applications
| System | Role in Process | Access Type |
| --- | --- | --- |
| **CRM** | Account, contract, price, and action context | Both |
| **Snowflake** | Governed analytics retrieval | Read |
| **TMS** | Transaction/action execution where applicable | Both |
| **CIP data** | Approved internal analytics and context | Read |

[Refine section](delegate:refine-section?section=scope)

<!-- pdd:section id=current-state sources=to-be/overview.md,to-be/bpmn-details.md reproj=g0 -->
# 3. Current State

This is a net-new capability. There is no existing operational process to document; this PDD defines the proposed governed future process.

[Refine section](delegate:refine-section?section=current-state)

<!-- pdd:section id=target-state sources=to-be/overview.md,to-be/process.bpmn,to-be/bpmn-details.md,to-be/participants-and-lanes.md,to-be/activities.md,to-be/gateways-and-routes.md,to-be/exception-handling.md,to-be/benefits.md reproj=g0 -->
# 4. Future State

## 4.1 Vision
The Orvane Sales Command Center orchestrates a fixed, auditable path from a user question or priority alert through authorization, retrieval, risk evaluation, governed recommendation, approval, MFA, execution, confirmation, and closure. Humans remain responsible for policy-sensitive and delegated approvals; the system performs controlled retrieval, evaluation, routing, execution, and evidence capture.

```bpmn
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_OrvaneSalesCommandCenter" targetNamespace="https://uipath.com/business-analysis/orvane-sales-command-center">
  <bpmn:collaboration id="Collaboration_OrvaneSalesCommandCenter"><bpmn:participant id="Participant_OrvaneSalesCommandCenter" name="Orvane Sales Command Center" processRef="Process_OrvaneSalesCommandCenter" /></bpmn:collaboration>
  <bpmn:process id="Process_OrvaneSalesCommandCenter" name="Orvane Sales Command Center governed action" isExecutable="false">
    <bpmn:startEvent id="Start_UserQuestion" name="User question" />
    <bpmn:startEvent id="Start_PriorityAlert" name="Priority alert" />
    <bpmn:serviceTask id="Task_CaptureRequest" name="Capture request context" />
    <bpmn:serviceTask id="Task_ValidateAccess" name="Validate role and access" />
    <bpmn:exclusiveGateway id="Gateway_Authorized" name="Access authorized?" />
    <bpmn:serviceTask id="Task_RetrieveData" name="Retrieve authorized data" />
    <bpmn:businessRuleTask id="Task_AssessRisk" name="Assess policy and risk" />
    <bpmn:exclusiveGateway id="Gateway_ActionNeeded" name="Action needed?" />
    <bpmn:serviceTask id="Task_ProposeAction" name="Propose governed action" />
    <bpmn:userTask id="Task_ReviewApproval" name="Review proposed action" />
    <bpmn:serviceTask id="Task_ValidateMfa" name="Validate MFA evidence" />
    <bpmn:serviceTask id="Task_ExecuteAction" name="Execute approved action" />
    <bpmn:serviceTask id="Task_ArchiveEvidence" name="Archive closure evidence" />
    <bpmn:endEvent id="End_Completed" name="Completed and confirmed" />
  </bpmn:process>
</bpmn:definitions>
```

*Figure: BPMN 2.0 process model. The validated process model of record is retained with the process design.*

[Open TO-BE diagram](delegate:open-diagram?which=to-be&anchor=target-state)

## 4.2 Target Flow
| # | BPMN element | Participant / lane | Element type | Input / message | Output / message | Route / exception path |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | User question or priority alert | Requester / alert source | Start event | Query or alert | Correlation context | Starts deterministic flow |
| 2 | Validate role and access | Command Center | Activity | Identity and requested scope | Authorization result | Deny without retrieval if unauthorized |
| 3 | Retrieve authorized data | Command Center | Activity | Authorized context | Source data snapshot | Close as exception when unusable |
| 4 | Assess policy and risk | Command Center | Activity | Data snapshot | Risk and rule result | Hard stop blocks execution |
| 5 | Propose governed action | Command Center | Activity | Eligible recommendation | Proposed action | Continue only where action is needed |
| 6 | Review proposed action | Authorized approver | Activity | Recommendation and rationale | Approval decision | Reject or expire to documented closure |
| 7 | Validate MFA evidence | Identity service | Activity | Step-up authentication | MFA result | Fail to denied closure |
| 8 | Execute and confirm | Command Center / target system | Activity | Approved action | Confirmation | Failure closes as exception |
| 9 | Archive evidence | Command Center | Activity | Lifecycle records | Immutable audit record | Completed, denied, or exception terminal state |

## 4.3 What Changes
| Area | AS-IS | TO-BE | Why | How |
| --- | --- | --- | --- | --- |
| Insight access | Static reports | Natural-language authorized retrieval | Faster decisions | Context-aware data retrieval |
| Follow-up action | Informal or separate | Governed recommendation-to-execution path | Reduce missed actions | Approval, MFA, and controlled execution |
| Evidence | Fragmented | Complete lifecycle audit record | Support audit and compliance | Timestamped query, decision, approval, and execution evidence |

## 4.4 Process Work Summary
The process contains two trigger types, controlled retrieval and rule-evaluation activities, approval and MFA decision gates, execution activities, and three terminal outcome categories: completed, denied/blocked, and exception closed.

[Refine section](delegate:refine-section?section=target-state)

<!-- pdd:section id=business-rules sources=to-be/business-rules.md reproj=g0 -->
# 5. Business Rules

| Rule ID | Description |
| --- | --- |
| BR-001 | Row-level and role-based authorization must be validated before any data retrieval. |
| BR-002 | Contracted prices, discounts, and recommendations must not violate MFN clauses or GPO rates. |
| BR-003 | High-value actions require the applicable delegated approval and MFA. |
| BR-004 | The requester may not self-approve a material exception. |
| BR-005 | Every query, export, approval, action, and terminal outcome must have timestamped audit evidence. |

[Refine section](delegate:refine-section?section=business-rules)

<!-- pdd:section id=data-model sources=entities/artifacts/,as-is/data-inputs-outputs.md reproj=g0 -->
# 6. Data Model

## 6.1 Entities
| Entity | Description |
| --- | --- |
| Request or alert | Trigger, requester, purpose, and correlation ID. |
| Authorization context | Role, hierarchy, record scope, and access decision. |
| Evaluation record | Source snapshot, applied rules, risk findings, and recommendation rationale. |
| Approval and MFA evidence | Approver, authority, decision, conditions, authentication evidence, and timestamp. |
| Execution and closure record | Action outcome, confirmation, exception disposition, and retained audit events. |

## 6.2 Data Inputs and Outputs
| Artifact | Source / Destination | Format | Consumed / Produced By |
| --- | --- | --- | --- |
| Sales and account context | CRM / Snowflake / CIP data | Structured records | Command Center |
| Inventory and transaction context | TMS | Structured records | Command Center and execution target |
| Audit event | Command Center to retained audit store | Timestamped event | Command Center |

## 6.3 Field-Level Data Dictionary
| Field | Type | Format / Pattern | Valid values / range | Mandatory | Privacy class |
| --- | --- | --- | --- | --- | --- |
| Correlation ID | String | Unique identifier | Unique per trigger | Yes | Internal |
| Requester identity | String | Enterprise identity | Authorized user | Yes | Confidential |
| Account and product context | Structured | CRM/TMS reference | Authorized scope only | As applicable | Confidential |
| Approval decision | Enum | Approved / Rejected / Conditional | Delegated authority | When required | Confidential |

[Refine section](delegate:refine-section?section=data-model)

<!-- pdd:section id=people sources=entities/people/ reproj=g0 -->
# 7. People

## 7.1 Roles & Personas
| Stakeholder | Responsibility |
| --- | --- |
| Territory Manager | Uses account-level insight and initiates permitted actions. |
| District/Regional Manager | Oversees performance and approves delegated actions. |
| Sales Operations | Reviews commercial and pricing risks. |
| Orvane Leadership Team | Monitors US CVR business health and strategic performance. |
| Orvane Sales Command Center | Executes controlled orchestration and evidence capture. |
| Authorized Approver | Makes delegated approval decisions without self-approval conflict. |

[Refine section](delegate:refine-section?section=people)

<!-- pdd:section id=raci sources=entities/people/ reproj=g0 -->
# 7.2 RACI

> [!WARNING]
> **Needs capture:** The accountable approval matrix and exception-owner assignments must be captured. This section will auto-fill when the wiki source is available.

[Refine section](delegate:refine-section?section=raci)

<!-- pdd:section id=exceptions sources=to-be/exception-handling.md reproj=g0 -->
# 8. Exceptions and Error Handling

| Exception | Trigger | AS-IS Handling | TO-BE Handling |
| --- | --- | --- | --- |
| Unauthorized access | Role or record check fails | Not applicable | Deny retrieval; retain access decision evidence. |
| Unusable source data | Missing, stale, or conflicting data | Not applicable | Do not recommend or execute; close as documented exception. |
| Policy hard stop | Pricing, contract, or compliance rule fails | Not applicable | Block execution; retain rationale and route for authorized disposition. |
| Approval timeout/rejection | Decision absent or negative | Not applicable | Close with decision/expiry evidence; no unattended queue. |
| MFA or execution failure | Authentication or target-system response fails | Not applicable | Do not execute or mark execution failed; close with evidence. |

[Refine section](delegate:refine-section?section=exceptions)

<!-- pdd:section id=compliance sources=to-be/business-rules.md reproj=g0 -->
# 9. Compliance and Regulatory

## 9.1 Compliance Traceability Matrix
| Requirement / Rule | Enforced at | Evidence retained |
| --- | --- | --- |
| RLS/RBAC | Authorization gate | Requester identity, scope, decision, timestamp |
| Encryption in transit and at rest | Data retrieval and retention | Security configuration and system audit records |
| MFA for high-value actions | MFA gate | MFA outcome and timestamp |
| MFN/GPO price protection | Policy and risk evaluation | Ruleset, price/contract finding, disposition |
| Sunshine Act traceability | Evaluation and closure | Account interaction/activity record and audit trail |
| BR-005 audit evidence | All lifecycle transitions | Immutable timestamped query, approval, action, and closure events |

## 9.2 Audit & Traceability
The process records the trigger, authorization, data source and retrieval scope, policy outcome, recommendation rationale, approval decision, MFA evidence, execution response, confirmation, and final disposition. Retention duration and evidence repository ownership remain policy decisions.

[Refine section](delegate:refine-section?section=compliance)

<!-- pdd:section id=kpis sources=to-be/benefits.md reproj=g0 -->
# 10. KPIs and Acceptance Criteria

## 10.1 KPIs
| KPI | Target / acceptance signal |
| --- | --- |
| Initial insight response | Under 45 seconds |
| Access-control compliance | No unauthorized retrievals |
| Audit completeness | Every query, export, approval, and action has a timestamped record |
| Policy-gate integrity | No execution after a hard-stop result |

## 10.2 Acceptance Criteria
- A Territory Manager can retrieve only assigned-account records.
- A high-value action cannot execute without required delegated approval and successful MFA.
- A contract price recommendation that conflicts with an MFN or GPO rule is blocked and documented.
- A completed or failed action has a retrievable evidence record.

[Refine section](delegate:refine-section?section=kpis)

<!-- pdd:section id=assumptions-risks sources=queries/,as-is/scope.md reproj=g0 -->
# 11. Assumptions, Constraints, Dependencies and Risks

## 11.1 Assumptions
| Assumption | Detail |
| --- | --- |
| Approval timeout | 24 hours is a proposed design value pending policy owner confirmation. |
| System interfaces | CRM, Snowflake, TMS, and CIP data can provide governed integration points. |

## 11.2 Constraints
| Constraint | Detail |
| --- | --- |
| Security | RLS/RBAC, encryption, and MFA are mandatory. |
| Compliance | MFN/GPO protection, Sunshine Act traceability, and audit logging are mandatory. |

## 11.3 Dependencies
| Dependency | Type (hard/soft) | Detail |
| --- | --- | --- |
| Approval matrix | Hard | Policy owners must define thresholds, approvers, substitutes, and escalation. |
| Integration contracts | Hard | System owners must confirm write-back actions, endpoints, and authentication. |
| Retention policy | Hard | Compliance owner must define evidence repository and retention period. |

## 11.4 Risks
| Risk | Mitigation |
| --- | --- |
| Incorrect policy configuration | Version rules, test controls, and require policy-owner approval. |
| Unauthorized action | Enforce least privilege, delegated approval, MFA, and immutable evidence. |
| Source-data conflict | Prevent action and close with exception evidence until disposition. |

[Refine section](delegate:refine-section?section=assumptions-risks)

<!-- pdd:section id=glossary sources=entities/ reproj=g0 -->
# 12. Glossary

| Term | Definition |
| --- | --- |
| GPO | Group Purchasing Organization. |
| MFA | Multi-factor authentication. |
| MFN | Most Favored Nation contractual price protection clause. |
| RLS | Row-level security. |
| RBAC | Role-based access control. |
| TMS | Transaction management system. |

[Refine section](delegate:refine-section?section=glossary)

<!-- pdd:section id=next-steps sources=queries/open-questions.md reproj=g0 -->
# 13. Next Steps

| # | Action item |
| --- | --- |
| 1 | Assign policy owners for the approval matrix, hard-stop conditions, and escalation paths. |
| 2 | Confirm CRM, Snowflake, TMS, and CIP integration ownership, endpoints, and authentication. |
| 3 | Define SLA targets beyond the under-45-second initial response requirement. |
| 4 | Confirm audit retention, evidence repository, and Sunshine Act operating procedure. |
| 5 | Validate the final process with Security, Compliance, Sales Operations, and business approvers. |

[Refine section](delegate:refine-section?section=next-steps)

<!-- pdd:section id=appendix-a sources=to-be/process.bpmn reproj=g0 -->
# Appendix A: Process Map and Diagrams

The BPMN 2.0 TO-BE model in Section 4.1 is the process model of record. An integration sequence diagram should be created during solution design after endpoint and authentication decisions are confirmed.

<!-- doc:placeholder kind="integration-diagram" -->
> [!NOTE]
> **Integration Diagram Placeholder**
> Insert diagram: Command Center interaction with CRM, Snowflake, TMS, CIP data, approval participants, identity service, and audit repository.

[Refine section](delegate:refine-section?section=appendix-a)
