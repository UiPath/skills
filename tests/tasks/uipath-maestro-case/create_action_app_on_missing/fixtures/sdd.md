# SDD — Action App Create During Build

**Case Definition Blueprint** · Verifies a missing Action App is built inline as an in-solution Coded Action App and bound.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | ActionAppCreateProbe |
| Case Description | Two human review tasks whose Action Apps do not exist in the tenant. Each must be built during the build, not left as a placeholder. |
| Case Identifier | Type: constant. Prefix: AAC |
| Case-Level SLA | — |
| SLA Type | — |
| Case App | Disabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

> None.

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|--------------|--------|---------------|
| T02 | Manual | User-initiated | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| requestId | Variable | string | | | "REQ-001" | Request identifier shown to both reviewers. |
| decision | Variable | string | | | "" | Approval decision recorded by the approver. |
| reviewNotes | Variable | string | | | "" | Free-text notes recorded by the reviewer. |

---

## Section 2: Stages & Tasks

### Stage 1: Human Review

**Type:** Stage
**Description:** An approver decides on the request, then a reviewer records notes.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|----------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

> None.

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Approve Request | action | Yes | No | Approver | — |
| 2 | Record Review Notes | action | Yes | No | Reviewer | — |

##### Task 1.1: Approve Request

**Type:** action
**Description:** The approver reads the request and approves or rejects it.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: create-probe-approval-app-q93
**Action App ID:** <UNRESOLVED>
**Deployment Folder:** <UNRESOLVED>
**actionType:** —
**Recipient:** Email:approver@example.com
**Priority:** Medium · **Task Title:** Approve or reject the request · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| requestId | String | =vars.requestId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| decision | -> decision |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | decision = "approved" | Complete task |
| Reject | decision = "rejected" | Complete task |

##### Task 1.2: Record Review Notes

**Type:** action
**Description:** The reviewer writes notes about the request.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| selected-tasks-completed("Approve Request") | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: create-probe-review-app-q93
**Action App ID:** <UNRESOLVED>
**Deployment Folder:** <UNRESOLVED>
**actionType:** —
**Recipient:** Email:reviewer@example.com
**Priority:** Low · **Task Title:** Record your review notes · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| requestId | String | =vars.requestId | Yes |
| decision | String | =vars.decision | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| reviewNotes | -> reviewNotes |

---

## Section 3: Personas & App Views

### Personas

| Persona | Stages | Permissions | Description |
|---------|--------|-------------|-------------|
| Approver | Human Review | View | Decides on the request. |
| Reviewer | Human Review | View | Records review notes. |

### App Views

> None. Case App is disabled.

---

## Section 4: Integrations

### Action Apps

| App | Folder | Action App ID | Used By Tasks |
|-----|--------|---------------|---------------|
| create-probe-approval-app-q93 | <UNRESOLVED> | <UNRESOLVED> | Approve Request |
| create-probe-review-app-q93 | <UNRESOLVED> | <UNRESOLVED> | Record Review Notes |
