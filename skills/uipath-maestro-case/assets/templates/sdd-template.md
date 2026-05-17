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
- CLI registry cache at `~/.uip/case-resources/` (deployed processes, connectors, action apps from the user's tenant — flat `<type>-index.json` files per resource type, populated by `uip maestro case registry pull`)
- IS connector cache at `~/.uipath/cache/integrationservice/<connectorKey>/` (`connections.json`, `activities.json`) for connection + operation metadata

**Output:** `sdd.md`

### Key Rules

1. **SLA placement:** SLA is supported on the **case**, on **stages**, and on **`action` tasks only**. Do NOT put SLA on `process`, `agent`, `rpa`, `api-workflow`, `wait-for-timer`, `wait-for-connector`, `execute-connector-activity`, or `case-management` tasks.

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

7. **Task types — closed enum of 9 values. Choose based on WHAT THE TASK DOES, not its surface label.** Any other value (e.g., `external-agent`, `connector-activity`, `wait-for-event`) is invalid and breaks downstream JSON generation. Consider all 9 for every task:
   - `action` — a human must review, approve, or make a judgment call. The task PAUSES for a person.
   - `agent` — AI reasoning: classification, criteria application, document analysis, risk assessment, triage. Use for any semi-structured reasoning.
   - `process` — deterministic multi-step BPMN: routing, orchestration, batch processing, report generation. No judgment (human or AI).
   - `rpa` — UI automation for legacy systems without APIs. An attended or unattended robot drives a desktop/web app.
   - `api-workflow` — structured API call with defined I/O. System-to-system.
   - `wait-for-timer` — waits for a duration, date, or schedule.
   - `wait-for-connector` — waits for an Integration Service event from an external system (in-stage trigger).
   - `execute-connector-activity` — executes a pre-built IS connector operation. Prefer over `api-workflow` when a connector exists.
   - `case-management` — starts a child case with its own lifecycle.

   **A well-designed SDD uses a MIX of types.** If all tasks are `action`, the SDD is wrong — most processes have automated steps. If no tasks are `agent`, consider whether any task involves classification, criteria application, or document analysis.

   **Externally-hosted AI agents** (CrewAI, Salesforce Einstein, Databricks, LangChain, etc.) have no first-class type in this skill. Model them as `api-workflow` (system-to-system invocation) or `execute-connector-activity` if a connector exists. Do not invent `external-agent`.

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
- **Express author intent, not skill implementation.** The SDD describes the business case; the skill is responsible for translating that into the plan and the JSON. The author should not need to know how the skill internally builds anything. Prose in Descriptions, subtitles, and any narrative cells MUST follow these rules:
  - **No explanatory Notes about column semantics or skill internals.** Forbidden: `> **Note:**` blocks (or any prose) that justify why a row is shaped a certain way using skill vocabulary — e.g., "this Variable has no `sourceTriggers` because its producer is a task," or "the `<-` notation captures the response field into the companion." The columns and `<-` notation are the agreed authoring shapes; the skill's validator enforces correctness. Authors do not document their own conformance.
  - **No raw structured formats inline.** Forbidden: `FilterTree` JSON, payload schema JSON, expression-language ASTs, `=jsonString:` blobs, or other plugin-internal data shapes embedded in the SDD body. Filters, payloads, and expressions belong as plain English. The skill builds the structured form. Canonical filter expression:
    ```
    **Filter:** Subject contains "urgent" AND From is "alice@example.com".
    ```
    The wait-for-connector / connector-activity plugin builds the FilterTree from this prose, validates the field/operator pair against the trigger spec, and AskUserQuestion's if a clause is unsupported.
  - **No skill-internal vocabulary in prose.** Forbidden in any narrative cell: `Pattern C`, `bridge`, `companion`, `inputOutputs[]`, `=jsonString:`, `groupOperator`, `essentialConfiguration`, `savedFilterTrees`, `dispatcher`, `Phase 2 validator`, `Phase 3 dispatcher`, `Q10 II`, `Finding #N`, `io-binding`, `aliased into`, `aliased from`, `aliased back into`, `via the <- notation`. These are internal terms used inside the skill's references — not the author's vocabulary. Describe outcomes in business terms instead. Examples:
    - **Bad:** `Slack message timestamp aliased into the messageTs Variable.`
    - **Good:** `Slack message timestamp.` (the Binding column already declares the aliasing visually)
    - **Bad:** `INVALID (Finding #6): In-argument with event-trigger source — Dispatcher must reject.`
    - **Good:** `Subject sourced from the trigger. (Misclassified: trigger-sourced rows are Variables, not In-arguments.)`
  - **What stays:** column headers (`sourceTriggers`, `sourceFields`, `Category`, etc.), the `<-` notation in Outputs Binding cells, `=vars.X` / `=js:(...)` expressions in Input Binding cells and IF columns. These are the *agreed authoring shapes*, not skill internals.

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

> Variable mapping (which trigger payload field populates which case variable) is declared in the **Case Variables** table below via `sourceTriggers` / `sourceFields` columns — NOT here. This table just identifies and configures each trigger.

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | {None \| Intsvc.EventTrigger \| Intsvc.TimerTrigger \| Manual} | {source system, connector, or "Manual"} | {see Configuration rules below} |

> Number triggers sequentially starting at T02 (T01 is reserved for the case file). The T-number is referenced by Case Variables rows whose value comes from this trigger's payload.

**Configuration column — write user-specified intent only:**

| Trigger type | What to write |
|---|---|
| Event trigger | The operation in business terms (e.g., `Calendar created`, `Email received`). Append a filter expression if the user wants filtering (e.g., `Email received in Inbox; filter: subject contains "URGENT"`). Append a required event-param value only when the user supplies it explicitly (e.g., `Email received in folder "<folder name>"`). |
| Timer trigger | Cycle or duration (e.g., `every 24 hours`, `daily at 09:00 UTC`). |
| Manual | `N/A` or omit. |

DO NOT include in Configuration:
- CLI enum values like `CALENDAR_CREATED` or `createdRecord` (the skill resolves these from the IS connector cache at planning time).
- Default modes like `polling` vs `webhook` (the skill defaults; the user only overrides when they care).
- Meta notes like `No required event parameters` or `No user filter` (absence is the default; the skill discovers required params at `case spec` time).
- Connector activity slug, HTTP method, or any spec-discovered detail.

### Case Exit Conditions

> **WHEN ↔ Marks Case Complete pairing is a schema constraint (see Key Rule 4):** `Yes` row MUST use `required-stages-completed` (preferred) or `wait-for-connector`; `No` row MAY use `selected-stage-completed(...)` / `selected-stage-exited(...)` / `wait-for-connector`. Mixing `Yes` with a `selected-*` rule is invalid.

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| {`required-stages-completed` for Yes; `selected-stage-completed("StageName")` or other rule for No} | {conditionExpression, or "—" if none} | Case exited | {Yes \| No} |

### Case Variables

> Complete inventory of all case-level variables and arguments. Every row's `Category` column is REQUIRED — drives classification at build time. Inference from other columns is no longer supported.

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| {camelCase name} | {In \| Out \| Variable} | {string \| number \| boolean \| date \| object \| array \| jsonSchema} | {T-number(s), CSV — required when value comes from trigger payload; empty for pure state / Out-args} | {keyed `T<N>: <path>; T<M>: <path>` format when sourceTriggers has multiple entries; single `<path>` when one trigger; empty when no trigger source} | {default value or empty} | {what this variable represents} |

**Category semantics:**

- **`In`** — formal case argument supplied by an external caller (manual trigger / API). For manual/timer triggers only. **NOT valid for event-trigger-sourced rows** — those are case-internal state populated by the trigger, not formal arguments. Use `Variable` instead.
- **`Out`** — formal case argument returned to the caller at case end. Value comes from a task output (via task plugin's `<-` aliasing — see per-task `Outputs` tables below) OR from a `Default` value if no task fires. `sourceTriggers` MUST be empty (direction mismatch — values flow case→caller, not trigger→case).
- **`Variable`** — case-internal state. May be populated by trigger payload (use `sourceTriggers` + `sourceFields`), by a task output (use `<-` notation in that task's Outputs table — same Name on both sides drives the wiring), or initialized via `Default` only.

**`sourceFields` notation (when sourceTriggers has multiple T-numbers):**

```
T02: response.subject; T03: response.title
```

Strict per-trigger — each T-number in `sourceTriggers` must have a corresponding entry in `sourceFields`. Same field name across triggers must be spelled out per trigger (no shorthand). Paths support dot-path nesting (e.g., `response.user.name`); array indexing (`items[0]`) not supported in v1.

**Out-arg producer rule (validated at end of Phase 3):**

Every `Out` row must have at least one of:
1. A `Default` value (the fallback returned when no task fires)
2. A task whose `Outputs` table includes a row with the same Name as the Out-arg (the producer — runtime writes its value into the Out-arg slot)

If neither holds, the io-binding validator surfaces the misalignment.

**Examples:**

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| caseStatus | Variable | string | | | "Open" | Pure case state |
| subject | Variable | string | T02 | response.subject | | Populated by event trigger payload |
| caseStarter | Variable | string | T02, T03 | T02: response.user; T03: response.initiator | | Multi-trigger, different fields per trigger |
| applicantName | In | string | | | | Formal In-arg for manual trigger (no source) |
| finalDecision | Out | string | | | | Out-arg; producer is "Approve Decision" task |

---

## Section 2: Stages & Tasks

**Purpose:** The case plan — every stage as a self-contained subsection with its own entry/exit conditions, SLA, and task definitions with inline I/O bindings. Stages use correct node types from the schema (`case-management:Stage` or `case-management:ExceptionStage`).

**I/O bindings — how the Inputs / Outputs tables drive task wiring:**

- **Inputs `Binding` column** = the case variable expression (`=vars.X`), metadata (`=metadata.X`), or literal that feeds this task input at runtime. Written into `task.data.inputs[].value`.
- **Outputs `Field` column** = the connector / process response field name. Supports dot-path nesting for nested responses (e.g., `result.score`, `data.user.id`). Top-level field name when the response is flat.
- **Outputs `Binding` column** = the case-scope variable name (camelCase) that stores the extracted value. Drives `var` / `id` on `task.data.outputs[]`. When Field and Binding camelCase to the same string, no aliasing is needed; when they differ, the aliasing is automatic — the Binding column is the authoritative storage slot name. The runtime engine writes the extracted `Field` value into `vars.<Binding>`.

The wiring on disk:
```jsonc
// task.data.outputs[] entry (written by task plugin)
{ "name": "<schema-display-name>",
  "source": "=<Field>",        // ← extracts from response
  "var":    "<Binding>",       // ← storage slot name (resolver key)
  "id":     "<Binding>",       // ← mirrors var
  ...
}
```

If a task output's Binding matches a Case Variables row's Name (e.g., `Out` arg), the runtime engine writes the value into that slot — natural alignment via shared name.

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
| 1 | {task name} | {action \| process \| agent \| rpa \| api-workflow \| wait-for-timer \| wait-for-connector \| execute-connector-activity \| case-management} | {Yes \| No} | {Yes \| No} | {persona name or "—"} | {count unit or "—" (only for action tasks)} |

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
> - **Operation** ← `~/.uipath/cache/integrationservice/{connectorKey}/activities.json` for the display/operation name; `~/.uip/case-resources/typecache-activities-index.json` (or `typecache-triggers-index.json` for events) for I/O schemas — each is a flat JSON array of activities, filter by connector + operation name.
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

###### Process / Agent / RPA / API Workflow Task Detail

> Use this block for `process`, `agent`, `rpa`, and `api-workflow` tasks. These tasks do NOT support SLA — SLA column in the task summary should be "—".

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
