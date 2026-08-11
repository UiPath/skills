# SDD — CreateMissingAgentCase

**Case Definition Blueprint** · Build one missing agent inline and wire a minimal string contract through the case.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | CreateMissingAgentCase |
| Case Description | Sends a customer name to a tiny inline greeting agent and stores its greeting. |
| Case Identifier | Type: constant. Prefix: CMA |
| Priority | Choiceset: Low, Medium, High — Default: Medium |
| Case-Level SLA | — |
| SLA Type | — |
| Case App | Disabled |
| Task-output passing | Direct |

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
| customerName | Variable | string | | | "Ada" | Name sent from the case to the agent. |
| greeting | Variable | string | | | | Greeting returned by the agent. |

---

## Section 2: Stages & Tasks

### Stage 1: Greet Customer

**Type:** Stage
**Description:** Invoke the inline greeting agent.
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
| 1 | Generate Greeting | agent | Yes | Yes | system | — |

##### Task 1.1: Generate Greeting

**Type:** agent
**Description:** Return a short greeting that includes the supplied customer name. No tools, connectors, or external data are needed.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** InlineGreetingAgentQ74
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Binding Sub-Type:** Agent
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| customerName | string | =vars.customerName |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| greeting | -> greeting |

---

## Section 3: Personas & App Views

### Personas

> None. The task is automated.

### App Views

> None. Case App is disabled.

---

## Section 4: Integrations

### Agents

| Agent | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|-------|--------|------------------------|------------------|---------------|
| InlineGreetingAgentQ74 | <UNRESOLVED> | <UNRESOLVED> | customerName → greeting | Generate Greeting |
