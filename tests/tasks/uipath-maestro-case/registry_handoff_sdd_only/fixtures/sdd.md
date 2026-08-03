# SDD — CrossMachineRegistryHandoff

**Case Definition Blueprint** · Verify that Phase 1 can resolve runnable resources from an SDD copied from another machine.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | CrossMachineRegistryHandoff |
| Case Description | Runs two existing tenant resources from an approved SDD whose Phase 0 registry cache was not transferred. |
| Case Identifier | Type: constant. Prefix: XMH |
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
| invoiceNumber | Variable | string | | | "INV-1042" | Invoice number passed to the API workflow. |
| emailSubject | Variable | string | | | "Portable handoff" | Subject passed to the agent. |

---

## Section 2: Stages & Tasks

### Stage 1: Resolve Resources

**Type:** Stage
**Description:** Invokes two resources after Phase 1 resolves them by the names preserved in this SDD.
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
| 1 | Post Invoice | api-workflow | Yes | No | system | — |
| 2 | Draft Notification | agent | Yes | No | system | — |

##### Task 1.1: Post Invoice

**Type:** api-workflow
**Description:** Calls the existing financial-posting workflow with an invoice number.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** FinancialPostingFunction
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| invoiceNumber | string | =vars.invoiceNumber |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

##### Task 1.2: Draft Notification

**Type:** agent
**Description:** Calls the existing email-drafting agent with a subject.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** EmailDrafter
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| subject | string | =vars.emailSubject |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

## Section 3: Personas & App Views

### Personas

> None. Both tasks are automated.

### App Views

> None. Case App is disabled.

---

## Section 4: Integrations

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| FinancialPostingFunction | <UNRESOLVED> | <UNRESOLVED> | invoiceNumber → — | Post Invoice |

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|------------------|---------------|
| EmailDrafter | <UNRESOLVED> | <UNRESOLVED> | subject → content | Draft Notification |
