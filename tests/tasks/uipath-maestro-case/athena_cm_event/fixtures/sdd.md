# SDD — AthenaCMEventCase

**Case Definition Blueprint** · Athena event-directed case

> A compact three-stage case plan that receives an external case identity and
> event payload. This fixture specifies the supported caseplan topology only:
> its trigger, stages, tasks, and completion rules.

## Table of Contents

1. [Case Definition](#section-1-case-definition) — metadata, trigger, exit conditions, and variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: StageA](#stage-1-stagea) — 2 tasks
   - [Stage 2: StageB](#stage-2-stageb) — 2 tasks
   - [Stage 3: StageC](#stage-3-stagec) — 3 tasks

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | AthenaCMEventCase |
| Case Description | Coordinates three operational stages for an event-directed case. |
| Case Identifier | Type: external. Source: `=vars.InstanceExternalId` |
| Priority | Choiceset: Normal — Default: Normal |
| Case-Level SLA | 10 d |
| SLA Type | time-based |
| Case App | Enabled |
| Task-output passing | Direct |
| Case Identifier source | custom |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|--------------|--------|---------------|
| T02 | Intsvc.EventTrigger | athena_cm_events | External event payload starts or updates the case. |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| InstanceExternalId | In | string | T02 | | | External identifier supplied by the caller. |
| eventPayload | In | jsonSchema | T02 | | | External event content supplied to the case. |

## Section 2: Stages & Tasks

### Stage 1: StageA

**Type:** Stage
**Description:** Provides the initial work items for the event-directed case.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|--------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| selected-tasks-completed("StageATask2") | — | exit-only | No | Exit Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | StageATask1 | process | Yes | No | system | — |
| 2 | StageATask2 | process | Yes | Yes | system | — |

##### Task 1.1: StageATask1

**Type:** process
**Description:** Performs the first deterministic Stage A operation.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageATask1
**Folder Path:** Shared

##### Task 1.2: StageATask2

**Type:** process
**Description:** Performs the follow-up deterministic Stage A operation.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| selected-tasks-completed("StageATask1") | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageATask2
**Folder Path:** Shared

### Stage 2: StageB

**Type:** Stage
**Description:** Hosts the Stage B work.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|--------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | StageBTask1 | process | No | No | system | — |
| 2 | StageBTask2 | process | Yes | No | system | — |

##### Task 2.1: StageBTask1

**Type:** process
**Description:** Performs a Stage B operation.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageBTask1
**Folder Path:** Shared

##### Task 2.2: StageBTask2

**Type:** process
**Description:** Performs the required Stage B operation.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | No | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageBTask2
**Folder Path:** Shared

### Stage 3: StageC

**Type:** Stage
**Description:** Completes the event-directed processing after Stage B finishes.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|--------------|--------------|
| selected-stage-completed("StageB") | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | StageCTask1 | process | No | Yes | system | — |
| 2 | StageCTask2 | process | No | Yes | system | — |
| 3 | StageCTask3 | process | Yes | Yes | system | — |

##### Task 3.1: StageCTask1

**Type:** process
**Description:** Performs the initial Stage C operation when the stage begins.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageCTask1
**Folder Path:** Shared

##### Task 3.2: StageCTask2

**Type:** process
**Description:** Performs the second Stage C operation selected by an event.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| current-stage-entered | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| No | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageCTask2
**Folder Path:** Shared

##### Task 3.3: StageCTask3

**Type:** process
**Description:** Performs the final required Stage C operation.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| selected-tasks-completed("StageCTask2") | — | Entry Rule 1 |

| Required | Run Only Once | Skip Condition |
|----------|---------------|----------------|
| Yes | Yes | — |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** StageCTask3
**Folder Path:** Shared
