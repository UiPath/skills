# SDD — BusinessRuleSingleCase

Single-stage, single-task case exercising the business-rule task plugin end-to-end.

## Section 1: Case Definition

### Case Metadata
| Property | Value |
|---|---|
| Case Name | BusinessRuleSingleCase |
| Case Description | Single-node case that scores a credit application with the CreditRisk business rule. |
| Case Identifier | Prefix: BRC, Type: constant |
| Case-Level SLA | 1 d |
| SLA Type | Static |

### Case Triggers
| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | User-initiated | N/A |

### Case Exit Conditions
| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| required-stages-completed | — | Case exited | Yes | Complete Rule 1 |

### Case Variables
| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| creditScore | In | number | | | 742 | Applicant credit score passed to the rule. |
| riskBand | Variable | string | | | | Risk band the CreditRisk rule returns; populated by Score Credit Risk. |

## Section 2: Stages & Tasks

### Stage 1: Score (`score`)

**Type:** Stage
**Description:** Score the application with the CreditRisk business rule.
**Required for Case Completion:** Yes

#### Stage Entry Conditions
| WHEN | IF | Interrupting | Display Name |
|------|-----|--------------|--------------|
| case-entered | — | No | Entry Rule 1 |

#### Stage Exit Conditions
| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|----------------------|--------------|
| required-tasks-completed | — | exit-only | Yes | Exit Rule 1 |

#### Tasks
| # | Task Name | Type | Activation Mode | Starts When | Required | Run Only Once | Persona | SLA |
|---|-----------|------|-----------------|-------------|----------|---------------|---------|-----|
| 1 | Score Credit Risk | business-rule | sequential | stage enters | Yes | No | system | — |

##### Task 1.1: Score Credit Risk

**Type:** business-rule
**Description:** Evaluate the CreditRisk rule on the applicant's credit score.

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `current-stage-entered` | — | Entry rule 1 |

**Resolved Resource:** CreditRisk
**Folder Path:** <UNRESOLVED>
**Resource Identity:** <UNRESOLVED>
**Dispatch / Operation:** —

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| creditScore | number | =vars.creditScore |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| RiskDecision.riskBand | -> riskBand |
