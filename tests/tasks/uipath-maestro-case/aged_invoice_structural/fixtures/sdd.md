# SDD — AgedInvoiceResolution

**Case Definition Blueprint** · Aged Invoice Payment Resolution — compact connector-free structural variant

> Derived from the Aged Invoice Payment Case Management PoV PDD, reduced to a
> compact three-stage backbone plus the two interrupting exception lanes so it
> builds within the agent turn budget. Every external system is modelled as an
> `api-workflow` / `rpa` task (PDD §12.4), so no Integration Service connection
> is required. Exercises the full connector-free task-type mix (api-workflow,
> agent, action, rpa, wait-for-timer, case-management) and — the point of this
> eval — two interrupting secondary lanes (SLA Escalation, Automation Incident)
> that return to origin. Tasks bind real deployed resources (NameToAgeFixed2,
> CountLetters, ProjectEuler, purchaseorderapp, CaseTest); payloads are generic.

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Trigger, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Intake](#stage-1-intake) — 2 tasks
   - [Stage 2: AP Review](#stage-2-ap-review) — 1 task
   - [Stage 3: Closure](#stage-3-closure) — 3 tasks
   - [Secondary Stage: SLA Escalation](#secondary-stage-sla-escalation) — 1 task
   - [Secondary Stage: Automation Incident](#secondary-stage-automation-incident) — 1 task
3. [Personas & App Views](#section-3-personas--app-views)
4. [Integrations](#section-4-integrations)

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | AgedInvoiceResolution |
| Case Description | Registers an aged invoice case, triages it, captures AP ownership, and closes it, with interrupting SLA-escalation and automation-incident lanes. Compact connector-free proof-of-value variant. |
| Case Identifier | Type: constant. Prefix: AIR |
| Priority | Choiceset: Low, Medium, High, Critical — Default: High |
| Case-Level SLA | 30 m |
| SLA Type | time-based |
| Case App | Disabled |
| Task-output passing | Direct |
| Case Identifier source | `=metadata.ExternalId` |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 70% of SLA duration | Notify: AP Team Leads |
| Breached | 100% of SLA duration | Notify: Finance Leadership |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Intsvc.EventTrigger | aged_invoice_cases | Record created |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |
| selected-stage-completed("Closure") | — | Case exited | No | Exit Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| invoiceId | Variable | string | T02 | response.invoice_id | | Aged invoice identifier from the record-created payload. |
| supplierName | Variable | string | T02 | response.supplier_name | | Supplier name from the payload. |
| invoiceAmount | Variable | float | T02 | response.amount | | Invoice amount. |
| caseStatus | Variable | string | | | "Open" | Current case state; "AutomationFailed" diverts to the incident lane. |
| priorityScore | Variable | integer | | | 50 | Triage priority score; >= 80 diverts to the SLA-escalation lane. |
| apDecision | Variable | string | | | "Accept" | AP ownership decision; produced by AP Ownership Review. |
| finalOutcome | Out | string | | | Pending | Final case disposition returned to the caller. |

---

## Section 2: Stages & Tasks

---

### Stage 1: Intake

**Type:** Stage
**Description:** Registers the aged invoice as a case from the record-created trigger and triages its root cause.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: AP Intake | Notify: AP Intake |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Register case | api-workflow | Yes | No | system | — |
| 2 | Run Invoice Triage Agent | agent | No | No | system | — |

##### Task 1.1: Register case

**Type:** api-workflow
**Description:** Creates the case shell record linking invoice and supplier.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.invoiceId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Registered" |

##### Task 1.2: Run Invoice Triage Agent

**Type:** agent
**Description:** Classifies the exception root cause and proposes a priority.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** CountLetters
**Folder Path:** Shared/uipath-maestro-flow/CountLetters CodedAgent
**Resource Identity:** 19677045-6c7c-406f-be8b-48bd1eb06414
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| inputString | string | =vars.supplierName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | priorityScore = 50 |

---

### Stage 2: AP Review

**Type:** Stage
**Description:** AP accepts ownership of the case and confirms the resolution path.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("Intake") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | =js:(vars.apDecision === "Accept") | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: AP Clerk | Notify: AP Team Lead |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | AP ownership review | action | Yes | No | AP Clerk | 5 m |

##### Task 2.1: AP ownership review

**Type:** action
**Description:** AP clerk accepts ownership of the case or reclassifies it.

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
**Recipient:** Role:Everyone
**Priority:** Medium · **Task Title:** AP ownership review · **Labels:** —

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| poNumber | String | =metadata.ExternalId | Yes |
| vendorName | String | =vars.supplierName | Yes |
| totalAmount | Number | =vars.invoiceAmount | Yes |
| requestingDepartment | String | =vars.caseStatus | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> apDecision |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | apDecision = "Accept" | Complete task and set variables |
| Reject | apDecision = "Reclassify" | Complete task and set variables |

---

### Stage 3: Closure

**Type:** Stage
**Description:** Updates the mock ERP, tracks the reimbursement via a child case, and closes the case.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-completed("AP Review") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: AP Clerk | Notify: AP Team Lead |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Update mock ERP outcome | rpa | Yes | No | system | — |
| 2 | Track Payment Sub-Case | case-management | No | No | system | — |
| 3 | Close case and update KPIs | api-workflow | Yes | No | system | — |

##### Task 3.1: Update mock ERP outcome

**Type:** rpa
**Description:** RPA bot posts the resolution outcome to the mock ERP UI.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** ProjectEuler
**Folder Path:** Shared/uipath-maestro-flow/ProjectEuler RPA
**Resource Identity:** 486edc26-0658-4ac1-92c9-1ef953927151
**Binding Sub-Type:** —
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| problemId | integer | 1 |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 3.2: Track Payment Sub-Case

**Type:** case-management
**Description:** Spawns a payment-tracking child case with its own lifecycle.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Child Case Task Detail (type: `case-management`)

**Child Case:** CaseTest
**Resolved Resource:** Maestro Case
**Folder Path:** Shared/uipath-maestro-case/CaseTest
**Resource Identity:** dc377f10-090c-43a9-9e19-2ab935ba0489
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|----------------|----------------|
| — | — |

**Wait for Completion:** No

**Data Returned (child -> parent):**

| Child Variable | Parent Variable |
|----------------|----------------|
| — | — |

##### Task 3.3: Close case and update KPIs

**Type:** api-workflow
**Description:** Records the closure reason and updates dashboard metrics.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.invoiceId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalOutcome = "Closed" |

---

### Secondary Stage: SLA Escalation

**Type:** Stage
**Stage Kind:** secondary
**Description:** Interrupting lane for at-risk or breached SLA conditions; holds for an escalation timer and returns to the originating stage.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-exited("AP Review") | =js:(vars.priorityScore >= 80) | Yes | Escalate At Risk |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| selected-tasks-completed("SLA warning timer") | — | return-to-origin | No | Return After Escalation |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: AP Team Lead | Notify: Finance Operations |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | SLA warning timer | wait-for-timer | Yes | No | system | — |

##### Task S1.1: SLA warning timer

**Type:** wait-for-timer
**Description:** Short hold representing the SLA escalation reminder window.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Timer Task Detail (type: `wait-for-timer`)

**Timer:** timeDuration
**Value:** PT5S

---

### Secondary Stage: Automation Incident

**Type:** Stage
**Stage Kind:** secondary
**Description:** Interrupting lane for failed API/RPA/agent automation; raises an incident and returns to the originating stage.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| selected-stage-exited("Intake") | =js:(vars.caseStatus === "AutomationFailed") | Yes | Automation Failed |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| selected-tasks-completed("Create incident record") | — | return-to-origin | No | Return After Incident |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | m | 70% | Notify: Automation Support | Notify: Automation CoE |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Create incident record | api-workflow | Yes | Yes | system | — |

##### Task S2.1: Create incident record

**Type:** api-workflow
**Description:** Raises an incident for the failed automation (ServiceNow transport re-typed to an api-workflow).

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** NameToAgeFixed2
**Folder Path:** Shared/uipath-maestro-case/NameToAgeFixed2
**Resource Identity:** b6af8fa1-07cc-4a03-b0a1-f966e3fa23be
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| name | string | =vars.invoiceId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| AP Clerk | AP Review | View, Act | First-line case worker. |
| AP Team Lead | SLA Escalation | View, Act | Handles SLA escalations. |
| Automation Support | Automation Incident | View, Act | Handles automation incidents. |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| AP Control Tower | Case List | AP Team Lead | Track aged invoice cases | Columns: invoiceId, supplierName, priorityScore, caseStatus |
| Case Workspace | Case Detail | AP Clerk | Work a single case | Sections: invoice context, decision, timeline |

---

## Section 4: Integrations

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| NameToAgeFixed2 | Shared/uipath-maestro-case/NameToAgeFixed2 | b6af8fa1-07cc-4a03-b0a1-f966e3fa23be | name → estimatedAge | Register case, Close case and update KPIs, Create incident record |

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|----------------------|---------------|
| CountLetters | Shared/uipath-maestro-flow/CountLetters CodedAgent | 19677045-6c7c-406f-be8b-48bd1eb06414 | inputString → count | Run Invoice Triage Agent |

### Processes & RPA

| Resource | Type | Folder | Resource ID (+version) | Used By Tasks |
|----------|------|--------|------------------------|---------------|
| ProjectEuler | rpa | Shared/uipath-maestro-flow/ProjectEuler RPA | 486edc26-0658-4ac1-92c9-1ef953927151 | Update mock ERP outcome |

### Child Cases

| Child Case | Identifier Prefix | Wait for Completion | Used By Tasks |
|------------|-------------------|---------------------|---------------|
| CaseTest | CT | No | Track Payment Sub-Case |

### Action Apps

| App | Folder | Action App ID | Used By Tasks |
|-----|--------|---------------|---------------|
| purchaseorderapp-1782974854 | Shared | b20c471c-adef-4b37-a884-897f56ca53bc | AP ownership review |
