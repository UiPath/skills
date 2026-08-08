# SDD — GrantReview

A Case Definition Blueprint for reviewing a community grant application at Rivermark Foundation: check eligibility, then either award the grant or close the application as rejected.

---

## Requirements (authoritative — settled with the business owner)

- Eligibility Review runs first. The Grant Officer ends it with a single decision: **Approve** or **Reject**.
- **Rejection is automatic from that decision.** Choosing Reject sends the application straight into the Application Rejected lane — the decision itself does the routing. Nobody picks that lane by hand, no reviewer browses a stage list, and there is no connector event or SLA involved.
- Choosing Approve sends the application to Award instead. The two outcomes are mutually exclusive: an application never lands in both Award and Application Rejected.
- Application Rejected is terminal: the case exits there without being marked complete.

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | GrantReview |
| Case Description | Reviews a community grant application at Rivermark Foundation from eligibility review through award or rejection. |
| Case Identifier | Type: constant. Prefix: GR |
| Case-Level SLA | — |
| SLA Type | — |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T01 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| `required-stages-completed` | — | Grant awarded | Yes |
| `selected-stage-completed("Application Rejected")` | — | Application closed as rejected | No |

### Case Variables

| Variable | Type | Default | Producer | Consumed By |
|----------|------|---------|----------|-------------|
| applicantName | String | — | Case trigger input | Reviewer Decision, Issue Award Letter |
| reviewDecision | String | — | Reviewer Decision | Award entry gate, Application Rejected entry gate |
| rejectionReason | String | — | Reviewer Decision | Record Rejection |

---

## Section 2: Stages & Tasks

### Stage 1: Eligibility Review (`stage-eligibility-review`)

**Type:** Stage
**Description:** The Grant Officer checks the application against the eligibility criteria and decides whether to approve or reject it.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `case-entered` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Reviewer Decision | action | Yes | No | Grant Officer | — |

---

##### Task 1.1: Reviewer Decision (`t01`)

**Type:** action
**Description:** The Grant Officer reviews the application against the eligibility criteria and approves or rejects it, capturing a reason on rejection.
**Design Rationale:** A human judgment call that decides the case route, so an action task carrying the decision.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| applicantName | String | =vars.applicantName | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| reason | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | reviewDecision = "Approve" | Send the application to Award |
| Reject | reviewDecision = "Reject" | Send the application to the Application Rejected lane |

---

### Stage 2: Award (`stage-award`)

**Type:** Stage
**Description:** Issues the award letter to the approved applicant.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Eligibility Review")` | `=js:(vars.reviewDecision === "Approve")` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Issue Award Letter | api-workflow | Yes | No | system | — |

---

##### Task 2.1: Issue Award Letter (`t02`)

**Type:** api-workflow
**Description:** Generates and sends the grant award letter to the applicant.
**Design Rationale:** A system integration with no human judgment, so an api-workflow.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Resource Identity:** `<UNRESOLVED: api-workflow "Issue Award Letter">`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Binding / Value |
|-------|-----------------|
| applicantName | =vars.applicantName |

---

### Secondary Stage: Application Rejected (`stage-application-rejected`)

**Type:** Secondary Stage
**Interrupting:** Yes
**Description:** Closes the application as rejected and records the reason on the applicant record.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `user-selected-stage` | — | Yes |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Record Rejection | api-workflow | Yes | No | system | — |

---

##### Task 3.1: Record Rejection (`t03`)

**Type:** api-workflow
**Description:** Writes the rejection and its reason to the applicant record.
**Design Rationale:** A system write with no human judgment, so an api-workflow.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Resource Identity:** `<UNRESOLVED: api-workflow "Record Rejection">`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Binding / Value |
|-------|-----------------|
| applicantName | =vars.applicantName |
| rejectionReason | =vars.rejectionReason |

---

## Section 3: Personas & App Views

| Persona | Description |
|---------|-------------|
| Grant Officer | Reviews the application and makes the approve/reject decision. |

---

## Section 4: Integrations

| Integration | Connector | Usage |
|-------------|-----------|-------|
| Applicant record system | — | Award letter and rejection write-back via api-workflows. |
