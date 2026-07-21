# Loan Origination — BPMN Solution Design Document

## 1. Process identity

| Field | Value |
| --- | --- |
| Process name | Loan Origination |
| Logical process ID | `loan-origination` |
| Business objective | Validate a loan application, route eligible applications to an underwriter, and record an approved or rejected outcome. |
| Scope | Manual applications only; no document extraction, funding, or post-approval servicing. |
| Implementation readiness | `Executable` |

## 2. Participants and triggers

| Logical ID | Participant or trigger | Role in the process | Input or event |
| --- | --- | --- | --- |
| `loan-applicant` | Loan applicant | Starts a manual application | application ID and requested amount |
| `underwriter` | Underwriter | Reviews eligible applications | application details and validation result |

The process starts manually with an application ID and requested amount.

## 3. Process graph

### Nodes

| Logical ID | BPMN kind | Name | Inputs | Outputs | Resource intent |
| --- | --- | --- | --- | --- | --- |
| `start-application` | start event | Start Application | application ID, requested amount | application ID, requested amount | none |
| `validate-application` | script task | Validate Application | application ID, requested amount | application valid | none |
| `assess-eligibility` | exclusive gateway | Assess Eligibility | application valid | none | none |
| `underwriter-review` | user task | Underwriter Review | application ID, requested amount | review decision | `loan-underwriter-review` |
| `route-review-decision` | exclusive gateway | Route Review Decision | review decision | none | none |
| `application-approved` | end event | Application Approved | review decision | none | none |
| `application-rejected` | end event | Application Rejected | application valid or review decision | none | none |

### Sequence flows

| Logical flow ID | From node | To node | Condition | Default path |
| --- | --- | --- | --- | --- |
| `flow-start-validate` | `start-application` | `validate-application` | Always | No |
| `flow-validate-eligibility` | `validate-application` | `assess-eligibility` | Always | No |
| `flow-eligible-review` | `assess-eligibility` | `underwriter-review` | `=js:vars.applicationValid === true` | No |
| `flow-ineligible-rejected` | `assess-eligibility` | `application-rejected` | Always | Yes |
| `flow-review-decision` | `underwriter-review` | `route-review-decision` | Always | No |
| `flow-approved` | `route-review-decision` | `application-approved` | `=js:vars.reviewDecision === "Approved"` | No |
| `flow-review-rejected` | `route-review-decision` | `application-rejected` | Always | Yes |

## 4. Data and variables

| Variable ID | Type | Source | Consumers | Purpose |
| --- | --- | --- | --- | --- |
| `application-id` | string | `start-application` | `validate-application`, `underwriter-review` | Identifies the application. |
| `requested-amount` | number | `start-application` | `validate-application`, `underwriter-review` | Records the requested loan amount. |
| `application-valid` | boolean | `validate-application` | `assess-eligibility`, `application-rejected` | States whether required application data is valid. |
| `review-decision` | string | `underwriter-review` | `route-review-decision`, `application-approved`, `application-rejected` | States the underwriter's outcome. |

## 5. Events, subprocesses, and loops

None.

## 6. Resource intent

| Resource intent ID | Used by node | Intended capability | Intended resource name | Connection or folder intent | Required | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| `loan-underwriter-review` | `underwriter-review` | human review | Loan Underwriting Review | Shared/Loan Operations; action app `loan-underwriting-review`, version `1`, action `ReviewApplication`, key `loan-operations` | Yes | Resolved |

## 7. Exception and event behavior

An invalid application follows the eligibility gateway's default rejected path.
An underwriter decision other than `Approved` follows the review gateway's
default rejected path.

## 8. Implementation readiness

| Check | Status | Evidence or blocker |
| --- | --- | --- |
| Graph is complete | Ready | One manual start, two explicit outcomes, and all gateway paths are declared. |
| Variable lineage is complete | Ready | Every gateway input has a declared producer. |
| Required resources are resolved | Ready | `loan-underwriter-review` is resolved by the approved mocked registry result. |
| Executable BPMN may be authored | Yes | All required resource intent is resolved. |
