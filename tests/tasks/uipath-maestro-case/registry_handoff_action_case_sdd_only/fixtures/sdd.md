# SDD — Portable Action and Child-Case Handoff

**Case Definition Blueprint** · Verifies type-specific resource names survive a cross-machine Phase 0 to Phase 1 handoff.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | PortableActionCaseHandoff |
| Case Description | Plans resolved and unresolved Action App tasks plus a child-case task while treating this SDD as authoritative over any stale registry cache. |
| Case Identifier | Type: constant. Prefix: PAC |
| Priority | Choiceset: Low, Medium, High — Default: Medium |
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
| requestId | Variable | string | | | "REQ-001" | Request identifier passed to both referenced resources. |

---

## Section 2: Stages & Tasks

### Stage 1: Review and Follow-up

**Type:** Stage
**Description:** Requests a human review and starts a follow-up child case.
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
| 1 | Resolved App Review | action | Yes | No | Reviewer | — |
| 2 | Review Request | action | Yes | No | Reviewer | — |
| 3 | Launch Follow-up | case-management | Yes | Yes | system | — |

##### Task 1.1: Resolved App Review

**Type:** action
**Description:** Uses an existing deployed Action App so Phase 1 must emit its runtime name and folder bindings.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: purchaseorderapp-1782974854
**Action App ID:** b20c471c-adef-4b37-a884-897f56ca53bc
**Deployment Folder:** Shared
**actionType:** —
**Recipient:** Role:Reviewer
**Priority:** Medium · **Task Title:** Review existing app request · **Labels:** —

**Input Schema:** —

**Output Schema:** —

##### Task 1.2: Review Request

**Type:** action
**Description:** Presents the request to a reviewer for acknowledgment.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: PortableReviewActionProbeQ91
**Action App ID:** <UNRESOLVED>
**Deployment Folder:** <UNRESOLVED>
**actionType:** —
**Recipient:** Role:Reviewer
**Priority:** Medium · **Task Title:** Review request · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| requestId | string | =vars.requestId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|

##### Task 1.3: Launch Follow-up

**Type:** case-management
**Description:** Starts the intended child case after the review task finishes.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| selected-tasks-completed("Review Request") | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

###### Child Case Task Detail (type: `case-management`)

**Child Case:** PortableChildCaseProbeQ91
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|-----------------|----------------|
| requestId | requestId |

**Wait for Completion:** No

---

## Section 3: Personas & App Views

### Personas

| Persona | Stages | Permissions | Description |
|---------|--------|-------------|-------------|
| Reviewer | Review and Follow-up | View, Act | Reviews the request. |

### App Views

> None. Case App is disabled.

---

## Section 4: Integrations

### Action Apps

| App | Folder | Action App ID | Used By Tasks |
|-----|--------|---------------|---------------|
| purchaseorderapp-1782974854 | Shared | b20c471c-adef-4b37-a884-897f56ca53bc | Resolved App Review |
| PortableReviewActionProbeQ91 | <UNRESOLVED> | <UNRESOLVED> | Review Request |

### Child Cases

| Child Case | Folder | Resource ID | Identifier Prefix | Wait for Completion | Used By Tasks |
|------------|--------|-------------|-------------------|---------------------|---------------|
| PortableChildCaseProbeQ91 | <UNRESOLVED> | <UNRESOLVED> | PCQ | No | Launch Follow-up |
