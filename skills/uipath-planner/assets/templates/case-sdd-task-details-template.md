# SDD Task Detail Blocks — Case Management

<!-- Companion to case-sdd-template.md (do not render this title or comment). Each `##### Task <N>.<M>:`
block in Section 2 carries, after its Task envelope table, the ONE detail block below that its Type
requires. Cell rules are complete where they stand, as in the main template. -->

###### Action Task Detail (type: `action`)

**HITL Implementation:** Action App: <concrete intended deploymentTitle; never <UNRESOLVED>> <!-- `Action App: <title>` is the ONLY form this cell takes — there is no JSON-schema, schema-only, or form-builder variant to choose between. The task's fields are the Input Schema table below, not a value of this cell. -->
**Action App ID:** <actionAppId or <UNRESOLVED>>
**Deployment Folder:** <folder path or <UNRESOLVED>>
**actionType:** <dispatch code or —>
**Recipient:** <Role:name \| User:uuid \| UserGroup:uuid \| Email:addr \| Expression:=vars.id — typed prefix only; none known → drop the cell + high review item>
**Priority:** <Low \| Medium \| High \| Critical> · **Task Title:** <one-line Action Center prompt> · **Labels:** <csv or —>

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| <field name> | <String \| Number \| Boolean \| Date \| ...> | <=vars.X \| =metadata.X \| =js:(...) \| literal> | <Yes \| No> |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| <schema field name> | -> <case variable> |
| — | <case variable> = <literal, =js:expression, or =js:vars.X.Y> |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| <button label> | <variable = value> | <Complete task \| Complete task and set variables> |

<!-- Buttons only on a decision task — then ≥2 rows; Maps To LHS = a §1.5 Name, taskOutcome, or this
task's own output (read downstream via a direct producer reference) — never an identifier occurring
nowhere else. Input/Output Schema fields MUST be ⊆ the resolved app's schema — a field the app lacks →
Ask (task-specific app / drop / placeholder), never silently author. Field NAMES are carried verbatim
from whatever supplied them, never re-cased or convention-converted, and never read off a
`--output json` envelope's PascalCased keys (case-data-and-time-guide.md § External names); unsourced spelling →
<UNRESOLVED> + review item. Reusing ONE deployed app across
several action tasks is sanctioned only when each task carries a distinct actionType dispatch value AND
its fields ⊆ the app schema (code-switched app); otherwise it is the substitute-app defect. -->

###### Connector Task Detail (type: `wait-for-connector`, `execute-connector-activity`, `external-agent` or `external-workflow`)

**Connector:** <connector name> · **Connector Key:** <connectorKey>
**Connection:** <connection instance name or Tenant default> · **Connection ID:** <connectionId or <UNRESOLVED>>
**Activity Type ID:** <activityTypeId or <UNRESOLVED>>
**Auth Method:** <OAuth2 \| API Key \| Basic \| Service Account \| ...>
**Account / Endpoint:** <explicit endpoint or —>
**Operation:** <display/operation name>
**Trigger / Event:** <trigger display name for wait-for-connector, or —>

<!-- Missing Connection ID / Activity Type ID → high review item. Inputs `Field` verbatim to the IS
activity schema. Operation Configuration carries through as =jsonString: only here. A solution-resource
picker (a Data Fabric entity) is an Inputs row holding the resource name; when that name can exist in
more than one folder, add a `<picker>_folderKey` row with the folder key (and `entityScope` = `folder`).
The task's own outputs are `response` and `Error`; a later task reads a field as
`"<Stage>"."<Task>".response.<field>`. -->

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| <field name> | <type> | <=vars.X \| =metadata.X \| =js:(...) \| literal> |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.<field> | -> <case variable> |
| — | <case variable> = <literal, =js:expression, or =js:vars.X.Y> |

###### Timer Task Detail (type: `wait-for-timer`)

**Timer:** <timeDuration (relative) \| timeDate (absolute) \| timeCycle>
**Value:** <ISO 8601 expression, date expression, or variable expression — NEVER <UNRESOLVED>: a timer cannot fire without it; block approval>
**Business Calendar:** <calendar name or —>

###### HTTP Request Task Detail (type: `http-request`)

**Method:** <GET \| POST \| PUT \| PATCH \| DELETE>
**URL:** <absolute URL; a path relative to the connector's base URL when Connector Key and Connection ID are set (convert stores it as the request path)>
**Headers:** <JSON object in backticks, e.g. `{"Accept": "application/json"}`, or —; never a credential — authenticate with Connector Key + Connection ID>
**Query:** <JSON object in backticks, or —>
**Body:** <JSON literal in backticks, an `=` expression, or —>
**Connector Key:** <connector whose connection authenticates the call, or — for a direct request>
**Connection ID:** <tenant connection id, or <UNRESOLVED>; only with Connector Key>

Outputs are the response's `code`, `headers` and `body`, plus `Error`.

###### Script Task Detail (type: `script`)

<!-- One ```js fenced FUNCTION BODY (```javascript also reads): read case state through `vars.<name>`
(and `metadata`), end in `return { … }`; a top-level `return` is legal. Only the first js fence in the
block is read. No Inputs table: the task receives `vars`, the whole case state. Outputs are fixed:
`scriptResponse` (what the body returns) and `Error`; bind the result with an arrow row,
`| scriptResponse | object | -> <variable> |`. Never a credential or secret in the body: it ships in
caseplan.case. -->

```js
<function body: reads vars.<name>, ends in return { … }>
```

###### Document Extraction Task Detail (type: `document-extraction`)

<!-- Runs a deployed IXP model on one file. All five lines come from read-only tenant lookups:
`uip solution resources list --kind IxpDeployment --source remote --output json` gives the
deployment's Name (IXP Deployment), Key (Deployment Key), Folder (Folder Path) and FolderKey
(Folder Key); `uip ixp deployments list <ixp-project-name> --output json` gives its DeploymentName
(Model Name) on the row whose DeploymentTitle is that Name. Model Name is the deployment's name,
never the IXP project's. A deployment not found yet → `<UNRESOLVED>` on Deployment Key and Folder Key
+ high review item. Inputs take only `fileRef` (the file, e.g. `=vars.invoiceFile`, required) and
`pageRange` (optional). The outputs are fixed: `output` (the IXP result, `ExtractionResult` and
`Taxonomy`) and `error`. Read the result downstream as `"<Stage>"."<Task>".output` and omit the
Outputs table; an arrow row (`| output | -> extraction |`) needs a `jsonSchema` case variable with a
body schema. No document-extraction deployment for the documents →
the model build routes to `uipath-ixp` (Section 4 § IXP / Document Understanding Models). -->

**IXP Deployment:** <deployment name as the solution lists it (DeploymentTitle)>
**Model Name:** <the deployment's DeploymentName, e.g. `<name>-<hash>-ixp`>
**Folder Path:** <folder the deployment is deployed to>
**Deployment Key:** <solution resource Key, or <UNRESOLVED>>
**Folder Key:** <deployment FolderKey, or <UNRESOLVED>>

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| fileRef | file | <=vars.X holding the document> |
| pageRange | string | <page range, or omit the row> |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| output | -> <jsonSchema case variable, or omit this table> |

###### Child Case Task Detail (type: `case-management`)

**Child Case:** <concrete intended child-case resource name; never <UNRESOLVED>, never the parent task's display name>
**Child Case Identifier Prefix:** <2-4 char UPPER prefix>
**Folder Path:** <folder path or <UNRESOLVED>>
**Resource Identity:** <entityKey or <UNRESOLVED>>
**Data Passed (parent -> child):**

| Parent Variable | Child Variable |
|----------------|----------------|
| <parent case variable> | <child case variable> |

**Wait for Completion:** <Yes \| No>

**Data Returned (child -> parent):** <!-- only when Wait for Completion: Yes -->

| Child Variable | Parent Variable |
|----------------|----------------|
| <child case variable> | <parent case variable> |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** <concrete intended resource name; never <UNRESOLVED>>
**Folder Path:** <resolved exact folder path or <UNRESOLVED>>
**Resource Identity:** <apiWorkflowId / agentId / processOrchestrationId (+version) or <UNRESOLVED>>
**Dispatch / Operation:** <selector and value for shared facades (`requestSource = "RegisterCaseShell"`) — also an Inputs row; — for single-purpose resources>

<!-- Folder Path = the exact resource folder (never a parent), or <UNRESOLVED> when identity is
unresolved. When a task resolves to a live resource: every REQUIRED declared input has a non-empty
Binding (any form incl. a direct upstream-output reference — needs no §1.5 row) or <UNRESOLVED> + high
review item; every Outputs -> Field exists verbatim in the resolved output contract (phantom field → high
review item). Unresolved-identity tasks have no contract — skipped; portable names stay concrete. Bare
field-name input lists are forbidden — table form only. No task-level SLA on any non-action type. Deep
runtime metadata (agent prompts, package versions, endpoints) stays out of the SDD. -->

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| <input argument name> | <type> | <=vars.X \| =metadata.X \| =js:(...) \| literal \| <- "Stage"."Task".out> |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| <output argument name> | -> <case variable> |
| — | <case variable> = <literal, =js:expression, or =js:vars.X.Y> |
