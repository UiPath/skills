# SDD — AmbiguousRegistryHandoff

**Case Definition Blueprint** · Verify that Phase 1 does not settle a resource name matching several tenant resources by its position in the registry.

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | AmbiguousRegistryHandoff |
| Case Description | Runs one existing API workflow whose name is shared by several resources on the tenant. |
| Case Identifier | Type: constant. Prefix: ARH |
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
| outcomeCode | Variable | string | | | "OK" | Outcome code passed to the API workflow. |

---

## Section 2: Stages & Tasks

### Stage 1: Resolve Resources

**Type:** Stage
**Description:** Invokes one API workflow after Phase 1 resolves it by the name preserved in this SDD.
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
| 1 | Record Outcome | api-workflow | Yes | No | system | — |

##### Task 1.1: Record Outcome

**Type:** api-workflow
**Description:** Calls the existing outcome-recording workflow with an outcome code.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** API Workflow
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Binding Sub-Type:** Api
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| outcomeCode | string | =vars.outcomeCode |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|

---

## Section 3: Personas & App Views

### Personas

> None. The task is automated.

### App Views

> None. Case App is disabled.

---

## Section 4: Integrations

### API Workflows

| Workflow | Folder | Resource ID (+version) | Inputs → Outputs | Used By Tasks |
|----------|--------|------------------------|------------------|---------------|
| API Workflow | <UNRESOLVED> | <UNRESOLVED> | outcomeCode → — | Record Outcome |
