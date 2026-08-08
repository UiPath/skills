# SDD — OutcomeExpenseApproval

Approved design for the expense-approval case. Two stages, both of which must
produce a REAL effect in a third-party system: the approver is notified by email
(Microsoft Outlook 365) and an audit record is filed as a Jira issue.

`{{RUN_TOKEN}}` is this request's reference. It MUST appear verbatim in the
approval email's subject and in the Jira issue's summary — downstream auditing
correlates the notification and the audit record by that reference.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | OutcomeExpenseApproval |
| Case Description | Notifies the approver of an expense request and files the audit record. |
| Case Identifier | Type: constant. Prefix: OEA |
| Case-Level SLA | — |
| SLA Type | — |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T01 | Manual | User-initiated start of the case | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|

---

## Section 2: Stages & Tasks

### Stage 1: Approval Request

**Type:** Stage
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Notify Approver | execute-connector-activity | Yes | No | system | — |

---

##### Task 1.1: Notify Approver

**Type:** execute-connector-activity
**Description:** Emails the approver that an expense request awaits their decision.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

###### Connector Task Detail (type: `execute-connector-activity`)

**Connector:** Microsoft Outlook 365
**Connector Key:** uipath-microsoft-outlook365
**Connection Name:** is-sandboxes-test@uipathsandboxes.onmicrosoft.com
**Connection ID:** dd657127-91f5-4568-a3a3-c024bc03fb0f
**Activity:** Send Email

> **The email MUST actually be delivered to the approver's mailbox — a saved
> draft does NOT notify anyone and does NOT satisfy this requirement.** The
> connector documents `saveAsDraft` as defaulting to `true` ("By default, the
> email will be saved as draft"), so bind it explicitly to `false` rather than
> relying on the default.

**Inputs (body):**

| Field | Value |
|-------|-------|
| message.toRecipients | is-sandboxes-test@uipathsandboxes.onmicrosoft.com |
| message.subject | Expense approval required — {{RUN_TOKEN}} |
| message.body.contentType | Text |
| message.body.content | An expense request is awaiting approval. Reference: {{RUN_TOKEN}} |
| saveToSentItems | true |

**Inputs (query parameters):**

| Field | Value |
|-------|-------|
| saveAsDraft | false |

> `saveAsDraft` is a QUERY parameter on this operation, not a body field. Binding
> it in the body leaves the query default (`true`) in force and the message is
> drafted rather than sent.

---

### Stage 2: Audit

**Type:** Stage
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Approval Request") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | File Audit Record | execute-connector-activity | Yes | No | system | — |

---

##### Task 2.1: File Audit Record

**Type:** execute-connector-activity
**Description:** Files the audit record for the approved expense request.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

###### Connector Task Detail (type: `execute-connector-activity`)

**Connector:** Jira
**Connector Key:** uipath-atlassian-jira
**Connection Name:** is-sandboxes-test@uipath.com-uipath-sandbox-380
**Connection ID:** f5273a4d-d492-4bcd-a106-5a20bf89a3ef
**Activity:** Create Issue

> `fields.summary` and `fields.description` are absent from this connector's
> published input metadata (Jira's create schema is per-project and resolved at
> runtime) but the endpoint DOES accept them. Send them anyway — an audit record
> with no summary carries no reference and is useless.

**Inputs (body):**

| Field | Value |
|-------|-------|
| fields.project.key | SJP |
| fields.issuetype.id | 10506 |
| fields.summary | Expense audit — {{RUN_TOKEN}} |
| fields.description | Audit record for approved expense request. Reference: {{RUN_TOKEN}} |

---

## Section 3: Personas & App Views

None — fully automated, no human-in-the-loop tasks.

## Section 4: Integrations

| Resolved Resource | Kind | Connection ID | Used by |
|---|---|---|---|
| Microsoft Outlook 365 | connector activity | dd657127-91f5-4568-a3a3-c024bc03fb0f | Notify Approver |
| Jira | connector activity | f5273a4d-d492-4bcd-a106-5a20bf89a3ef | File Audit Record |

> Both connection IDs are pinned because the tenant hosts several connections per
> connector — including personally-owned ones whose names collide with the shared
> sandbox connections. Resolve the activity type IDs from the registry, but use
> these connection IDs verbatim.
