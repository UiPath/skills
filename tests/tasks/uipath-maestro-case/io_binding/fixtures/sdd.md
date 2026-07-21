# SDD — IoBindingCase

Single-stage case that exercises common task-level input and output binding
forms against existing deterministic tenant resources.

## Section 1: Case Definition

### 1.1 Case Metadata
| Property | Value |
|---|---|
| Case Name | IoBindingCase |
| Case Description | Sequential task I/O binding matrix using existing tenant resources. |
| Case Identifier | Prefix: IOB, Type: constant |
| Priority | Choiceset: Low, Medium, High - Default: Medium |
| Case-Level SLA | 1 d |
| SLA Type | Static |

### 1.3 Triggers
| Trigger Type | Source | Configuration | Initial Variable Mapping |
|---|---|---|---|
| manual | User-initiated start of the case | - | - |

### 1.4 Case Completion Conditions
| WHEN | IF | THEN | Marks Case Complete |
|---|---|---|---|
| required-stages-completed | - | Case marked complete | Yes |

### 1.5 Case Variables
| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|---|---|---|---|---|---|---|
| caseInput | In | string | | | case-seed | Stable input supplied to variable and expression bindings. |
| renamedResult | Variable | string | | | | Golden API output captured under a different case-variable name. |
| errorMessage | Variable | string | | | | Nested Golden API error message, empty on the successful path. |
| literalResult | Out | string | | | | Literal assigned when Echo prior output completes. |
| copiedResult | Out | string | | | | Copy of renamedResult assigned when Echo prior output completes. |
| computedResult | Out | string | | | | Computed value based directly on Echo literal's task output. |
| metadataResult | Out | string | | | | Case ExternalId copied from metadata when Echo expression completes. |
| estimatedAge | Variable | number | | | | Predicted age written by an explicit same-name output extraction. |
| collisionCopy | Out | number | | | | Copy of the colliding same-name task output resolved through its source output ID. |
| customReferenceCopy | Out | number | | | | Copy of a custom output resolved through its root Case-variable companion. |

## Section 2: Stages & Tasks

### Stage 1: Binding Matrix (`bindingMatrix`)
**Type:** Stage
**Description:** Run eight existing API workflows sequentially to exercise the binding matrix.
**Required for Case Completion:** Yes

#### Stage Entry Conditions
| WHEN | IF | Interrupting |
|---|---|---|
| case-entered | - | No |

#### Stage Completion Conditions
| WHEN | IF | Exit Type | Marks Stage Complete |
|---|---|---|---|
| required-tasks-completed | - | exit-only | Yes |

#### Tasks
| # | Task ID | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|---------|-----------|------|----------|---------------|---------|-----|
| 1 | `bindingMatrix.echoLiteral` | Echo literal | api-workflow | Yes | Yes | system | — |
| 2 | `bindingMatrix.echoCaseVariable` | Echo case variable | api-workflow | Yes | Yes | system | — |
| 3 | `bindingMatrix.echoPriorOutput` | Echo prior output | api-workflow | Yes | Yes | system | — |
| 4 | `bindingMatrix.echoExpression` | Echo expression | api-workflow | Yes | Yes | system | — |
| 5 | `bindingMatrix.lookupExactSameName` | Lookup exact same name | api-workflow | Yes | Yes | system | — |
| 6 | `bindingMatrix.lookupCollidingSameName` | Lookup colliding same name | api-workflow | Yes | Yes | system | — |
| 7 | `bindingMatrix.consumeCollidingOutput` | Consume colliding output | api-workflow | Yes | Yes | system | — |
| 8 | `bindingMatrix.consumeCustomOutput` | Consume custom output | api-workflow | Yes | Yes | system | — |

##### Task 1.1: Echo literal (`bindingMatrix.echoLiteral`)

**Type:** api-workflow
**Description:** The Golden Expense API is a deterministic echo: APIInput1 is returned as APIOutput1. This call uses a literal input and leaves Outputs undeclared so schema discovery must auto-mint APIOutput1 internally.

**Entry Condition**

| WHEN | IF |
|---|---|
| current-stage-entered | - |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | "literal-seed" |

##### Task 1.2: Echo case variable (`bindingMatrix.echoCaseVariable`)

**Type:** api-workflow
**Description:** Echo a case variable, rename the business output, and extract a nested error field.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Echo literal") | selected-tasks: Echo literal |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | =vars.caseInput |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| APIOutput1 | string | -> renamedResult |
| Error.Message | string | -> errorMessage |

##### Task 1.3: Echo prior output (`bindingMatrix.echoPriorOutput`)

**Type:** api-workflow
**Description:** Consume Echo literal's entire output directly, then exercise literal, variable-copy, and computed output assignments.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Echo case variable") | selected-tasks: Echo case variable |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | `<- "Binding Matrix"."Echo literal".APIOutput1` |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| — | string | literalResult = "literal-assigned" |
| — | string | copiedResult = =vars.renamedResult |
| — | string | computedResult = =js:vars.$xref('Binding Matrix','Echo literal','APIOutput1') + '-computed' |

##### Task 1.4: Echo expression (`bindingMatrix.echoExpression`)

**Type:** api-workflow
**Description:** Echo a JavaScript input expression and copy case metadata through a custom output assignment.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Echo prior output") | selected-tasks: Echo prior output |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | =js:vars.renamedResult + '-input-expression' |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| — | string | metadataResult = =metadata.ExternalId |

##### Task 1.5: Lookup exact same name (`bindingMatrix.lookupExactSameName`)

**Type:** api-workflow
**Description:** Preserve the exact estimatedAge -> estimatedAge extraction regression using the NameToAge resource whose field follows valid camelCase variable naming.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Echo expression") | selected-tasks: Echo expression |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/NameToAgeFixed2 |
| Resource Identity | b6af8fa1-07cc-4a03-b0a1-f966e3fa23be |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| name | string | =vars.caseInput |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| estimatedAge | number | -> estimatedAge |

##### Task 1.6: Lookup colliding same name (`bindingMatrix.lookupCollidingSameName`)

**Type:** api-workflow
**Description:** Repeat estimatedAge -> estimatedAge after another task already owns the unsuffixed task-output ID, requiring collision-safe source-side allocation while preserving the case-variable target.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Lookup exact same name") | selected-tasks: Lookup exact same name |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/NameToAgeFixed2 |
| Resource Identity | b6af8fa1-07cc-4a03-b0a1-f966e3fa23be |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| name | string | =vars.caseInput |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| estimatedAge | number | -> estimatedAge |

##### Task 1.7: Consume colliding output (`bindingMatrix.consumeCollidingOutput`)

**Type:** api-workflow
**Description:** Consume the colliding same-name output by task reference and copy the same output through an in-expression reference, proving both resolvers use the source output ID rather than its case-variable pointer.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Lookup colliding same name") | selected-tasks: Lookup colliding same name |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | `<- "Binding Matrix"."Lookup colliding same name".estimatedAge` |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| — | number | collisionCopy = =js:vars.$xref('Binding Matrix','Lookup colliding same name','estimatedAge') + 0 |

##### Task 1.8: Consume custom output (`bindingMatrix.consumeCustomOutput`)

**Type:** api-workflow
**Description:** Consume a custom `=` output, which has no task-output ID, through both whole-value and in-expression references so both resolvers must use its root Case-variable companion ID.

**Entry Condition**

| WHEN | IF |
|---|---|
| selected-tasks-completed ("After Consume colliding output") | selected-tasks: Consume colliding output |

| Field | Value |
|---|---|
| Resolved Resource | API Workflow |
| Folder Path | Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106 |
| Resource Identity | b9e4f81a-a2c5-4e6d-ab72-a819649c7666 |
| Binding Sub-Type | Api |
| Component Type | API_WORKFLOW |

**Inputs**
| Field | Type | Binding |
|---|---|---|
| APIInput1 | string | `<- "Binding Matrix"."Consume colliding output".collisionCopy` |

**Outputs**
| Field | Type | Binding / Value |
|---|---|---|
| — | number | customReferenceCopy = =js:vars.$xref('Binding Matrix','Consume colliding output','collisionCopy') + 0 |
