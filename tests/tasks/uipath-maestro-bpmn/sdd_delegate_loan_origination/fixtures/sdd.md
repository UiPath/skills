# Loan Origination Solution Design Document

## 1. Process Overview

| Field | Value |
|---|---|
| Process name | Loan origination |
| Process ID | loan-origination |
| Scope | Validate a submitted loan application, determine eligibility, and route eligible applications for underwriter review. |
| Intended outcome | Record an approved or rejected loan outcome. |
| In scope | Manual application start, validation, eligibility, underwriter review, and final outcome. |
| Out of scope | Loan funding, payment servicing, and customer notification delivery. |

## 2. Participants and Triggers

| Participant ID | Name | Responsibility | Lane or pool intent |
|---|---|---|---|
| P_APPLICANT | Applicant | Starts the application. | Applicant |
| P_UNDERWRITER | Underwriter | Reviews eligible applications. | Underwriting |

| Trigger ID | Trigger type | Description | Initial data or event | Source intent |
|---|---|---|---|---|
| T_MANUAL_APPLICATION | Manual start | An applicant submits a loan application. | applicationId, applicantName, requestedAmount | Loan application intake |

## 3. Process Graph

### Nodes

| Node ID | Node type | Name | Purpose | Participant | Resource intent |
|---|---|---|---|---|---|
| N_START | Start event | Manual loan application start | Begin the process when an applicant submits an application. | P_APPLICANT | Manual start form or intake trigger. |
| N_VALIDATE_APPLICATION | Script task | Validate application | Validate required application data and calculate eligibility inputs. | System | Scripted validation using application data. |
| N_VALIDATION_RESULT | Exclusive gateway | Application valid? | Route valid applications to eligibility and invalid applications to rejection. | System | Gateway evaluates validationStatus. |
| N_ELIGIBILITY | Exclusive gateway | Eligible? | Route valid applications by the eligibility decision. | System | Gateway evaluates eligibilityDecision. |
| N_HUMAN_REVIEW | User task | Underwriter review | Let an underwriter approve or reject an eligible application. | P_UNDERWRITER | UiPath human review task with application data. |
| N_REVIEW_DECISION | Exclusive gateway | Review approved? | Route the recorded underwriter outcome. | System | Gateway evaluates reviewOutcome. |
| N_APPROVED | End event | Loan approved | End the process with an approved outcome. | System | Outcome recording. |
| N_REJECTED | End event | Loan rejected | End the process with a rejected outcome. | System | Outcome recording. |

### Sequence flows

| Flow ID | Source Node ID | Target Node ID | Condition | Default |
|---|---|---|---|---|
| F_START_VALIDATE | N_START | N_VALIDATE_APPLICATION | Always | No |
| F_VALIDATE_RESULT | N_VALIDATE_APPLICATION | N_VALIDATION_RESULT | Always | No |
| F_VALID_APPLICATION | N_VALIDATION_RESULT | N_ELIGIBILITY | validationStatus == "valid" | No |
| F_INVALID_APPLICATION | N_VALIDATION_RESULT | N_REJECTED | Always | Yes |
| F_ELIGIBLE | N_ELIGIBILITY | N_HUMAN_REVIEW | eligibilityDecision == "eligible" | No |
| F_INELIGIBLE | N_ELIGIBILITY | N_REJECTED | Always | Yes |
| F_REVIEW_DECISION | N_HUMAN_REVIEW | N_REVIEW_DECISION | Always | No |
| F_REVIEW_APPROVED | N_REVIEW_DECISION | N_APPROVED | reviewOutcome == "approved" | No |
| F_REVIEW_REJECTED | N_REVIEW_DECISION | N_REJECTED | Always | Yes |

### Subprocesses and loops

No subprocesses or loops are declared for this process.

## 4. Data and Variables

| Variable | Type | Scope | Producer | Consumers | Source or default |
|---|---|---|---|---|---|
| applicationId | String | Process | T_MANUAL_APPLICATION | N_VALIDATE_APPLICATION, N_HUMAN_REVIEW | Submitted application identifier. |
| applicantName | String | Process | T_MANUAL_APPLICATION | N_HUMAN_REVIEW | Submitted applicant name. |
| requestedAmount | Number | Process | T_MANUAL_APPLICATION | N_VALIDATE_APPLICATION, N_HUMAN_REVIEW | Submitted requested amount. |
| validationStatus | String | Process | N_VALIDATE_APPLICATION | F_VALID_APPLICATION, F_INVALID_APPLICATION | `valid` or `invalid`. |
| eligibilityDecision | String | Process | N_VALIDATE_APPLICATION | F_ELIGIBLE, F_INELIGIBLE | `eligible` or `ineligible`. |
| reviewOutcome | String | Process | N_HUMAN_REVIEW | F_REVIEW_APPROVED, F_REVIEW_REJECTED | `approved` or `rejected`. |

## 5. UiPath Resource Intent

This UiPath resource intent records the required behavior without fabricating a
tenant-specific identity.

| Node ID | UiPath activity or resource intent | Required | Required inputs | Expected outputs | Resolved identity | Status |
|---|---|---|---|---|---|---|
| N_VALIDATE_APPLICATION | Script task for application validation and eligibility calculation. | Yes | applicationId, requestedAmount | validationStatus, eligibilityDecision | `BPMN.ScriptTask` extension type, resolved from the active registry. | Resolved; revalidate the registry template downstream. |
| N_HUMAN_REVIEW | Human review task assigned to an underwriter. | Yes | applicationId, applicantName, requestedAmount | reviewOutcome | `<UNRESOLVED: active-tenant human task must be selected downstream>` | Blocked for executable implementation. |

## 6. Exception and Event Behavior

| Event or exception ID | Triggering node or flow | Behavior | Recovery or outcome | Affected data |
|---|---|---|---|---|
| E_INVALID_APPLICATION | N_VALIDATE_APPLICATION | Set validationStatus to `invalid` and end with a rejected outcome. | Loan rejected. | validationStatus |
| E_REVIEW_REJECTED | F_REVIEW_REJECTED | Record the underwriter rejection. | Loan rejected. | reviewOutcome |

## 7. Implementation Readiness

| Blocker ID | Readiness item | Status | Owner or decision needed | Resolution path |
|---|---|---|---|---|
| R_UNDERWRITER_ASSIGNMENT | Confirm the tenant-specific assignment mechanism for the human review task. | Open | Implementation owner | Revalidate against the active tenant before executable BPMN generation. |
