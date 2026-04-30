# SDD Template — Case Definition Blueprint
# Purpose: Defines the output format for sdd.md — a case definition blueprint
#          that a developer can directly implement in the UiPath Case Designer.

---

## Instructions for SDD Generation

You are generating an **SDD — a case definition blueprint** (NOT a traditional
solution design document). Every section maps directly to what the UiPath Case
Designer actually consumes. A developer reading this document should be able to
build the case in the Case Designer without guessing.

**Inputs:**
- Phase 0 interview answers (free-text + AskUserQuestion picks) — primary source
- This template — defines the output structure
- See [references/case-schema.md](../../references/case-schema.md) for the JSON schema reference (types, rules, SLA model)

**Optional enrichment sources:**
- CLI registry cache at `~/.uipcli/case-resources/` (deployed processes, connectors, action apps from the user's tenant — flat `<type>-index.json` files per resource type, populated by `uip maestro case registry pull`)
- IS connector cache at `~/.uipath/cache/integrationservice/<connectorKey>/` (`connections.json`, `activities.json`) for connection + operation metadata

**Output:** `sdd.md`

### Key Rules

1. **SLA placement:** SLA is supported on the **case**, on **stages**, and on **`action` tasks only**. Do NOT put SLA on `process`, `agent`, `rpa`, `api-workflow`, `external-agent`, `wait-for-timer`, `wait-for-connector`, `execute-connector-activity`, or `case-management` tasks.

2. **No skip conditions:** Stage skip conditions are NOT supported in the schema. Do not generate them. Use task-level `shouldRunOnlyOnce` for re-entry behavior.

3. **Rule types:** Use only actual rule types from the schema:
   - `case-entered` — case has been created/entered
   - `selected-stage-completed` — a specific stage has completed
   - `selected-stage-exited` — a specific stage has exited (not necessarily completed)
   - `selected-tasks-completed` — specific tasks have completed
   - `current-stage-entered` — the current stage has been entered
   - `required-stages-completed` — all required stages completed
   - `required-tasks-completed` — all required tasks in stage completed
   - `wait-for-connector` — an Integration Service event received
   - `adhoc` — ad-hoc / manual trigger

4. **Exit conditions:** Every exit condition MUST specify:
   - **Exit Type:** `exit-only` | `return-to-origin` | `wait-for-user`
   - **Marks Stage Complete:** Yes | No
   These are separate concepts. A stage can exit without completing (exit-only + No).

   **WHEN ↔ Marks Complete pairing (hard constraint — schema-enforced; applies identically to STAGE exit and CASE exit):**

   *Stage exit:*
   - `Marks Stage Complete: Yes` → WHEN MUST be `required-tasks-completed` (typical) or `required-stages-completed`. **NEVER** `selected-tasks-completed(...)`.
   - `Marks Stage Complete: No` (routing / divergent exits) → WHEN may be `selected-tasks-completed("TaskA")`, `selected-stage-completed(...)`, `wait-for-connector`, etc.
   - Same stage may carry one completion exit (`Yes` + `required-tasks-completed`) plus zero or more routing exits (`No` + `selected-tasks-completed`).

   *Case exit (preferred pattern: one row, `Yes` + `required-stages-completed`):*
   - `Marks Case Complete: Yes` → WHEN MUST be `required-stages-completed` or `wait-for-connector`. **NEVER** `selected-stage-completed(...)` / `selected-stage-exited(...)`.
   - `Marks Case Complete: No` (case exits without closing — rare) → WHEN may be `selected-stage-completed(...)`, `selected-stage-exited(...)`, or `wait-for-connector`.

5. **Descriptions are mandatory:** Every case, stage, and task MUST have a prose description. No empty or placeholder descriptions.

6. **Entry/exit conditions use WHEN + IF format:**
   - **WHEN** = the rule type (event that triggers evaluation, e.g., `selected-stage-completed("Intake")`)
   - **IF** = the optional `conditionExpression` (JavaScript expression evaluated against case variables, e.g., `applicationStatus == "Approved"`)

7. **Task types — choose based on WHAT THE TASK DOES, not its surface label.** All 10 types must be considered for every task:
   - `action` — a human must review, approve, or make a judgment call. The task PAUSES for a person.
   - `agent` — AI reasoning: classification, criteria application, document analysis, risk assessment, triage. Use for any semi-structured reasoning.
   - `process` — deterministic multi-step BPMN: routing, orchestration, batch processing, report generation. No judgment (human or AI).
   - `rpa` — UI automation for legacy systems without APIs. An attended or unattended robot drives a desktop/web app.
   - `api-workflow` — structured API call with defined I/O. System-to-system.
   - `external-agent` — AI agent hosted OUTSIDE UiPath (CrewAI, Salesforce Einstein, Databricks, LangChain, etc.)
   - `wait-for-timer` — waits for a duration, date, or schedule.
   - `wait-for-connector` — waits for an Integration Service event from an external system.
   - `execute-connector-activity` — executes a pre-built IS connector operation. Prefer over `api-workflow` when a connector exists.
   - `case-management` — starts a child case with its own lifecycle.
   
   **A well-designed SDD uses a MIX of types.** If all tasks are `action`, the SDD is wrong — most processes have automated steps. If no tasks are `agent`, consider whether any task involves classification, criteria application, or document analysis.

### Naming Conventions

- **Case names:** PascalCase (e.g., `MortgageLoanOrigination`)
- **Case identifier prefix:** UPPER, 2-4 characters (e.g., `MLO`)
- **Variable names:** camelCase (e.g., `applicationStatus`, `loanAmount`)
- **Workflows/Processes:** PascalCase (e.g., `ValidateEligibility`)
- **Entity names:** PascalCase (e.g., `LoanApplication`)
- **Entity fields:** camelCase (e.g., `applicantName`)

### Output Structure

The generated SDD must start with:

1. **Title** — `# SDD — {Case Name}`
2. **Subtitle** — Case Definition Blueprint blurb
3. **Table of Contents** — Numbered list with markdown anchor links. Use plain numbered list items with links, NOT headings (no `###`). Format:
   ```markdown
   ## Table of Contents

   1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
   2. [Stages & Tasks](#section-2-stages--tasks)
      - [Stage 1: {Name}](#stage-1-{slug}) — {N} tasks
      - [Stage 2: {Name}](#stage-2-{slug}) — {N} tasks
      ...
   3. [Personas & App Views](#section-3-personas--app-views) — {N} Personas, Process App Views
   4. [Integrations](#section-4-integrations) — Integration Service Connectors, External Agents
   ```
   Anchor slugs must match the actual heading text: lowercase, spaces→hyphens, strip special chars (e.g., `### Stage 1: Request Intake & Triage` → `#stage-1-request-intake--triage`).

### Output Rules (applies to every section of the rendered SDD)

- The SDD is a standalone developer artifact. It must NOT reference its own generation sources. Forbidden phrases anywhere in the output: `interview answers`, `from cache`, `from the registry`, `from state.*`, `REVIEW:`, `wiki/`, `PDD`, `pdd.md`, or any chain-of-thought explanation of how a value was derived.
- State every fact directly. If mock substitution is permitted, say "Mock Connector substitution is permitted until a live connection is provisioned" — do not attribute the decision to a generation source.
- Unknown values render as `—`, not as REVIEW markers. Review items belong in the Phase 0 round-4 summary or post-build loop, not in the document body.

---

## Section 1: Case Definition

**Purpose:** Top-level case configuration — what appears at the root of the case plan. This section defines the case identity, SLA, triggers, exit conditions, and the complete variable inventory.

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | {PascalCase name} |
| Case Description | {2-3 sentence description of what the case manages} |
| Case Identifier | Prefix: {2-4 char UPPER prefix}, Type: {constant \| external} |
| Priority | Choiceset: {comma-separated values} — Default: {value} |
| Case-Level SLA | {count} {unit: h/d/w/m} |
| SLA Type | {Static \| Variable} |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | {percentage}% of SLA duration | {Notify: recipient or group} |
| Breached | 100% of SLA duration | {Notify: recipient or group} |

### Variable SLA Rules

> Include this table only if SLA Type is Variable. Each row defines an expression-based SLA override.

| Expression | SLA | Unit |
|------------|-----|------|
| {conditionExpression evaluated against case variables} | {count} | {h \| d \| w \| m} |

### Case Triggers

| Trigger Type | Source | Configuration | Initial Variable Mapping |
|-------------|--------|---------------|-------------------------|
| {None \| Intsvc.EventTrigger \| Intsvc.TimerTrigger} | {source system, connector, or "Manual"} | {IS connector event config, timer cycle/duration, or "N/A"} | {source field -> case variable, one per line} |

### Case Exit Conditions

> **WHEN ↔ Marks Case Complete pairing is a schema constraint (see Key Rule 4):** `Yes` row MUST use `required-stages-completed` (preferred) or `wait-for-connector`; `No` row MAY use `selected-stage-completed(...)` / `selected-stage-exited(...)` / `wait-for-connector`. Mixing `Yes` with a `selected-*` rule is invalid.

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| {`required-stages-completed` for Yes; `selected-stage-completed("StageName")` or other rule for No} | {conditionExpression, or "—" if none} | Case exited | {Yes \| No} |

### Case Variables

> Complete inventory of all case-level variables. Every variable must list where it is produced and where it is consumed.

| Variable | Type | Default | Description | Produced By | Consumed By |
|----------|------|---------|-------------|-------------|-------------|
| {camelCase name} | {String \| Number \| Boolean \| Date \| Object \| Array \| ...} | {default value or "—"} | {description of what this variable represents} | {trigger, task name, or "computed"} | {comma-separated list of tasks that read this variable} |

---

## Section 2: Stages & Tasks

**Purpose:** The case plan — every stage as a self-contained subsection with its own entry/exit conditions, SLA, and task definitions with inline I/O bindings. Stages use correct node types from the schema (`case-management:Stage` or `case-management:ExceptionStage`).

> Repeat the following structure for each stage in the case plan. Number stages sequentially.

---

### Stage {N}: {Stage Name}

**Type:** {Stage \| ExceptionStage}
**Description:** {Prose description of what this stage accomplishes in the case lifecycle}
**Required for Case Completion:** {Yes \| No}
**Interrupting:** {Yes \| No} _(ExceptionStage only — omit for regular stages)_

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| {rule type with target, e.g., selected-stage-completed("Previous Stage Name")} | {conditionExpression, or "—" if none} | {Yes \| No} |

#### Stage Exit Conditions

> **WHEN ↔ Marks Stage Complete pairing is a schema constraint (see Key Rule 4):** `Yes` row MUST use `required-tasks-completed` (or `required-stages-completed`); `No` row MAY use `selected-tasks-completed(...)`. Mixing is invalid.

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| {`required-tasks-completed` for Yes; `selected-tasks-completed("TaskName")` or other rule for No} | {conditionExpression, or "—" if none} | {exit-only \| return-to-origin \| wait-for-user} | {Yes \| No} |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| {count} | {h \| d \| w \| m} | {percentage}% | {Notify: recipient or specific action} | {Notify: recipient or specific action} |

#### Tasks

> Tasks are listed in the order provided by the source spec / interview answers. Do not add, split, merge, or rename tasks; do not infer new tasks from context.

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | {task name} | {action \| process \| agent \| rpa \| api-workflow \| external-agent \| wait-for-timer \| wait-for-connector \| execute-connector-activity \| case-management} | {Yes \| No} | {Yes \| No} | {persona name or "—"} | {count unit or "—" (only for action tasks)} |

> After the summary table, provide a detailed subsection for each task.

---

##### Task {N}.{M}: {Task Name}

**Type:** {exact task type from schema}
**Description:** {What this task does and why it exists in the case plan}

**Entry Condition:**

| WHEN | IF |
|------|-----|
| {rule type with target, or "current-stage-entered" for first task} | {conditionExpression, or "—" if none} |

---

###### Action Task Detail (type: `action`)

> Use this block for every task of type `action`. Choose Action App or JSON Schema based on task complexity and registry availability.

**HITL Implementation:** {Action App: {app name} \| JSON Schema}

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| {field name} | {String \| Number \| Boolean \| Date \| ...} | {case variable} | {Yes \| No} |

**Output Schema:**

| Field | Type | Binding |
|-------|------|---------|
| {field name} | {type} | -> {case variable that receives this value} |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| {button label, e.g., "Approve"} | {variable = value, e.g., reviewDecision = "Approved"} | {Complete task \| Complete task and set variables \| ...} |

---

###### Connector Task Detail (type: `wait-for-connector` or `execute-connector-activity`)

> Use this block for connector-based tasks. Connection + Auth are **tenant-authoritative** and come from the Integration Service CLI cache, not from the user spec:
> - **Connection** ← `~/.uipath/cache/integrationservice/{connectorKey}/connections.json` — the `name` (and optional `id`) of the default or first enabled entry.
> - **Auth Method** ← `~/.uipath/cache/integrationservice/connectors.json` — the connector's `defaultAuthenticationType`.
> - **Operation** ← `~/.uipath/cache/integrationservice/{connectorKey}/activities.json` for the display/operation name; `~/.uipcli/case-resources/typecache-activities-index.json` (or `typecache-triggers-index.json` for events) for I/O schemas — each is a flat JSON array of activities, filter by connector + operation name.
> - **Account/Endpoint is not stored** in the compact cache. Render `—` unless the user spec supplies it explicitly.
> If a cache is unavailable or no enabled connection is found, render `—` rather than inventing values.

**Connector:** {connector name from Integration Service, e.g., "Salesforce"}
**Connection:** {connection instance `name` from `connections.json`, e.g., "Salesforce-Prod" — or "Tenant default (connection ID {id})" when `isDefault: true`}
**Auth Method:** {`defaultAuthenticationType` from `connectors.json`, e.g., OAuth2 \| API Key \| Basic \| Service Account}
**Account / Endpoint:** {explicit endpoint if supplied — or "—" (not stored in the CLI cache)}
**Operation:** {`displayName` / `operation` from `activities.json`}
**Trigger / Event:** {trigger display name for `wait-for-connector`, or "—" for `execute-connector-activity`}

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| {field name} | {type} | {case variable providing the value} |

**Outputs:**

| Field | Type | Binding |
|-------|------|---------|
| {field name} | {type} | -> {case variable that receives this value} |

---

###### Timer Task Detail (type: `wait-for-timer`)

> Use this block for timer-based wait tasks.

**Timer:** {timeDuration \| timeDate \| timeCycle}
**Value:** {ISO 8601 expression, e.g., "PT24H" for 24 hours, "P3D" for 3 days, or a variable expression}

---

###### Child Case Task Detail (type: `case-management`)

> Use this block for tasks that spawn a child case.

**Child Case:** {PascalCase case project name}
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|----------------|----------------|
| {parent case variable} | {child case variable} |

**Wait for Completion:** {Yes \| No}

**Data Returned (child -> parent):**

| Child Variable | Parent Variable |
|----------------|----------------|
| {child case variable} | {parent case variable} |

---

###### Process / Agent / RPA / API Workflow / External Agent Task Detail

> Use this block for `process`, `agent`, `rpa`, `api-workflow`, and `external-agent` tasks. These tasks do NOT support SLA — SLA column in the task summary should be "—".

**Inputs:**

| Variable | Type | Binding |
|----------|------|---------|
| {input variable name} | {type} | {case variable providing the value} |

**Outputs:**

| Variable | Type | Binding |
|----------|------|---------|
| {output variable name} | {type} | -> {case variable that receives this value} |

---

## Section 3: Personas & App Views

**Purpose:** Who interacts with the case and through what interfaces. Maps personas to stage scope and permissions, and defines Process App views.

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| {persona name} | {comma-separated stage names, or "All"} | {comma-separated permission list, e.g., "View, Act, Reassign"} | {description of this persona's role in the process} |

### Process App Views

> Define the views available in the Case App / Process App. Include case list and case detail views at minimum.

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| {app name} | {view name, e.g., "Case List", "Case Detail", "Dashboard"} | {persona who uses this view} | {what this view enables} | {key UI components: columns, filters, sections, charts} |

---

## Section 4: Integrations

**Purpose:** External systems and how they connect to the case. Covers Integration Service connectors with their operations and external agent configurations.

### Integration Service Connectors

| Connector | System | Auth Method | Operations Used | Used By Tasks |
|-----------|--------|-------------|-----------------|---------------|
| {connector name} | {target system name} | {OAuth2 \| API Key \| Basic \| Service Account \| ...} | {comma-separated operation names} | {comma-separated task names} |

> For each connector, provide operation detail. If CLI registry data is available, include actual I/O fields from the registry.

#### {Connector Name}

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| {operation name} | {GET \| POST \| PUT \| DELETE \| PATCH \| EVENT} | {field: type, field: type, ...} | {field: type, field: type, ...} |

### External Agents

> Include this table only if the case uses external agent tasks.

| Agent | Service Type | Endpoint | Used By Tasks |
|-------|-------------|----------|---------------|
| {agent name} | {CrewAI \| Salesforce \| ServiceNow \| Custom \| ...} | {endpoint URL or reference} | {comma-separated task names} |
