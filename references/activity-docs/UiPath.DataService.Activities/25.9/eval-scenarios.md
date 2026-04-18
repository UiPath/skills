# UiPath.DataService.Activities — Eval Scenarios

**Package**: `UiPath.DataService.Activities` 25.9  
**Org**: datafabric | **Tenant**: CodingAgentsEvals

## Activities in Scope

| # | Activity | Category |
|---|----------|----------|
| 1 | `CreateEntityRecord` | Entity Record |
| 2 | `GetEntityRecordById` | Entity Record |
| 3 | `UpdateEntityRecord` | Entity Record |
| 4 | `DeleteEntityRecord` | Entity Record |
| 5 | `QueryEntityRecords` | Entity Record |
| 6 | `CreateMultipleEntityRecords` | Batch |
| 7 | `UpdateMultipleEntityRecords` | Batch |
| 8 | `DeleteMultipleEntityRecords` | Batch |
| 9 | `UploadFileToRecordField` | File |
| 10 | `DownloadFileFromRecordField` | File |
| 11 | `DeleteFileFromRecordField` | File |

---

## Validation Model (Current Scope)

Each scenario evaluates two conditions after the agent generates a workflow:

| Condition | What it checks | How |
|-----------|---------------|-----|
| **Build-time** | XAML compiles without errors — namespaces, type arguments, required arguments, RecordState structure | `uip rpa get-errors --file-path <xaml> --project-dir <dir> --output json` returns no errors |
| **Output semantics** | Generated XAML matches the expected structural patterns for the given prompt — correct activity, EntityId, field bindings, namespace declarations, output wiring | Parse XAML and assert specific attributes and element structure |

Each task prompt passes entity and field names as context to the agent. Entities and fields are fixed, pre-existing resources in CodingAgentsEvals — no dynamic entity creation or record writes occur as part of the eval. The agent resolves GUIDs from `EntitiesStore.json`.

Two entities are used across all scenarios:

| Entity | Fields | Used In |
|--------|--------|---------|
| `CodingAgentsBuildTimeEntity` | `Title` (NVARCHAR, required), `Notes` (NVARCHAR), `Status` (NVARCHAR), `Score` (INT), `Price` (DECIMAL), `IsActive` (BIT), `EventDate` (DATE), `ScheduledAt` (DATETIMEOFFSET) | All CRUD, batch, filter, and sort scenarios |
| `CodingAgentsBuildTimeFileEntity` | `Title` (NVARCHAR, required), `Attachment` (File), `Report` (File), `Contract` (File), `attachmentFile` (File) | All file activity scenarios (Upload, Download, DeleteFile) |

---

## Scenario Summary

| Category | Count | Cadence |
|----------|-------|---------|
| Negative Skill Activation | 5 | Every PR (CI) |
| Positive Skill Activation | 5 | Every PR (CI) |
| Smoke | 6 | Every PR (CI) |
| Integration | 43 (I1–I43) | Daily / on request |
| Quality | 10 | Daily / weekly |
| **Total** | **69** | |

---

## 1. Negative Skill Activation

**Purpose**: Verify the agent does NOT activate the `UiPath.DataService.Activities` skill for tasks that belong elsewhere. The SKILL.md description must be precise enough that superficially similar prompts — queuing, file I/O, in-memory data, REST calls, storage — do not cause the agent to generate DataService XAML.

**Evaluation**: The generated workflow must contain zero DataService activities, no `xmlns:uda` namespace, and no `entitiesStores` dependency.

| ID | Scenario | Agent Prompt | Eval Summary | Must NOT appear in output |
|----|----------|-------------|--------------|--------------------------|
| N1 | **Task queue — not entity storage** | "After processing each invoice, add it as a queue item to the Orchestrator queue named `InvoiceQueue` with the reference `INV-001` and a JSON transaction payload." | The agent must not conflate "persistent data store" with entity storage; the workflow must use queue activities with no DataService package or namespace present. | `uda:CreateEntityRecord` or any `xmlns:uda`; `UiPath.DataService.Activities` in `project.json` dependencies; `entitiesStores` block |
| N2 | **CSV file — not entity query** | "Read the file `'C:\data\employees.csv'` and load its rows into a DataTable variable named `employeeTable`." | A file-read task must stay within file and DataTable activities; no DataService dependency or namespace must appear. | Any `uda:` activity; `entitiesStores` in `project.json`; DataService namespace declarations |
| N3 | **External REST API — not Data Fabric** | "Call the external HR system REST API at the provided base URL with a GET request to `/api/v1/users/{userId}` and deserialise the JSON response into a `JObject` variable." | An external HTTP call must remain in the web/REST activity domain and must not introduce any DataService dependency. | `uda:GetEntityRecordById` or any DataService activity; `UiPath.DataService.Activities` dependency; `entitiesStores` block |
| N4 | **Orchestrator Storage Bucket — not file field** | "Upload the report file at `'C:\reports\monthly.pdf'` to the Orchestrator Storage Bucket named `ReportsBucket` under the path `2026/april/monthly.pdf`." | File upload to an Orchestrator Storage Bucket is distinct from DataService file fields; no DataService activity or namespace must appear. | `uda:UploadFileToRecordField`; any `xmlns:uda`; `UiPath.DataService.Activities` in dependencies |
| N5 | **In-memory DataTable — not entity records** | "Build an in-memory lookup table with two columns — `ProductCode` (String) and `UnitPrice` (Double) — and populate it with 3 rows of test data." | In-memory data structures must use native .NET collections; the agent must not activate the DataService skill for a task with no entity or tenant context. | Any `uda:` activity; `entitiesStores` in `project.json`; DataService namespace or assembly references |

---

## 2. Positive Skill Activation

**Purpose**: Verify the agent correctly activates the DataService activity references across different phrasings of Data Service tasks — explicit package mentions, Data Fabric terminology, and implicit entity operations.

**Evaluation**: Pass condition — `uipath-rpa` skill is loaded in the agent session AND the agent reads from the `references/UiPath.DataService.Activities` reference files within that skill. No inspection of the generated workflow or project files.

| ID | Scenario | Agent Prompt | Eval Summary | Expected Activation Signal |
|----|----------|-------------|--------------|---------------------------|
| P1 | **"Data Service" terminology** | "Create an RPA automation that creates a record in the Data Service entity `CodingAgentsBuildTimeEntity` with field `Title` set to `'Hello'`." | Explicit "Data Service" phrasing must route the agent to the RPA skill and load the DataService activity reference files — not resolve to a generic or integration skill. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P2 | **"Data Fabric" terminology** | "Create an RPA automation that stores a new order in the Data Fabric entity `CodingAgentsBuildTimeEntity` with field `Title` set to `'ORD-001'`." | "Data Fabric" phrasing — without naming the package — must still resolve to the RPA skill and load the DataService reference files. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P3 | **Retrieve by name** | "Create an RPA automation that fetches a record from the Data Service entity `CodingAgentsBuildTimeEntity` and stores it in a variable." | A record-retrieval prompt on a named entity must activate the RPA skill with DataService references — not a REST or generic HTTP skill. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P4 | **Search/filter phrasing** | "Create an RPA automation that finds all records in the Data Fabric entity `CodingAgentsBuildTimeEntity` where `Status` equals `'Active'`." | Filter/search phrasing on a Data Fabric entity must activate the RPA skill with DataService references — not a LINQ, DataTable, or external API skill. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P5 | **File attachment phrasing** | "Create an RPA automation that attaches the file `'C:\docs\contract.pdf'` to the `Contract` field of a record in Data Service entity `CodingAgentsBuildTimeFileEntity`." | File-attach phrasing on a named entity field must activate the RPA skill with DataService references — not a Storage Bucket or file system skill. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |

---

## 3. Smoke

**Purpose**: Verify basic plumbing is correct across all 11 activities — namespaces, EntityId, TypeArguments, RecordState, output wiring. Activities are grouped by natural pairing so each scenario exercises the minimal set of plumbing needed to confirm the structural baseline is correct.

Entity context passed in every prompt: entity name and field names only. Scope is always Tenant for smoke. The agent resolves GUIDs from `EntitiesStore.json`.

---

### S1 — Create + Read *(CreateEntityRecord, GetEntityRecordById)*

**Prompt**:
> Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with field `Title` set to `"Smoke Test Record"`, then read the record back and return it as a workflow output.

**Eval summary**: Verifies complete project boilerplate — all four namespaces, `entitiesStores`, assembly references — and that `CreateEntityRecord` correctly sets `IsInRecordView`, `InputEntityInFieldView`, and `RecordState`, while `GetEntityRecordById` chains off the created record's ID with no write-mode properties.

| Check | Condition |
|-------|-----------|
| `project.json` dependencies | `UiPath.DataService.Activities` present |
| `project.json` entitiesStores | Entry with `serviceDocument: ".entities/EntitiesStore.json"`, `namespace: "<ProjectName>"` |
| XAML namespaces | All four present: `xmlns:uda`, `xmlns:udam`, `xmlns:udd`, `xmlns:local="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"` |
| TextExpression namespaces | `UiPath.DataService.Activities`, `UiPath.DataService.Activities.Models`, `UiPath.DataService.Definition`, `<ProjectName>` |
| TextExpression references | `UiPath.DataService.Activities.Core`, `UiPath.DataService.Definition`, `DataService.<ProjectName>` |
| CreateEntityRecord — type | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` (not `udd:IEntity`) |
| CreateEntityRecord — EntityId | `"<EntityGuid>"` |
| CreateEntityRecord — scope | `ScopeValue="Tenant"`, `SolutionEntityKey="{x:Null}"`, `SolutionEntityName="{x:Null}"` |
| CreateEntityRecord — record view | `IsInRecordView="[False]"` |
| CreateEntityRecord — field view | `InputEntityInFieldView` constructs entity with `Title = "Smoke Test Record"` |
| CreateEntityRecord — RecordState | One `DynamicEntityField`: `FieldId="<TitleFieldGuid>"`, `IsRequired="True"`, `ArgumentValue` set |
| CreateEntityRecord — output | `OutputEntity` bound to `createdRecord`; `VisibleDynamicPropertiesInfo="{x:Null}"` |
| GetEntityRecordById — type | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` |
| GetEntityRecordById — RecordId | Bound to `createdRecord.Id` |
| GetEntityRecordById — output | `OutputEntity` bound to out-argument `RetrievedRecord` |
| GetEntityRecordById — absent | No `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView` |
| Build | `uip rpa get-errors` returns no errors |

---

### S2 — Create + Update *(CreateEntityRecord, UpdateEntityRecord)*

**Prompt**:
> Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` `"Original"` and `Score` `10`, then update the same record setting `Title` to `"Updated"` and `Score` to `99`.

**Eval summary**: Verifies that both `CreateEntityRecord` and `UpdateEntityRecord` correctly populate `InputEntityInFieldView` and `RecordState.SelectedFields` for a multi-field entity, and that the update chains off the created record's ID.

| Check | Condition |
|-------|-----------|
| CreateEntityRecord — field view | `InputEntityInFieldView` sets `Title = "Original"`, `Score = 10` |
| CreateEntityRecord — RecordState | Two `DynamicEntityField` entries: `<TitleFieldGuid>` (required) and `<ScoreFieldGuid>` (not required), both with `ArgumentValue` set |
| UpdateEntityRecord — type | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` |
| UpdateEntityRecord — RecordId | Bound to `createdRecord.Id` |
| UpdateEntityRecord — record view | `IsInRecordView="[False]"` |
| UpdateEntityRecord — field view | `InputEntityInFieldView` sets `Title = "Updated"`, `Score = 99` |
| UpdateEntityRecord — RecordState | Two `DynamicEntityField` entries with updated `ArgumentValue` values |
| UpdateEntityRecord — output | `OutputEntity` wired; `VisibleDynamicPropertiesInfo="{x:Null}"` |
| Build | `uip rpa get-errors` returns no errors |

---

### S3 — Create + Delete *(CreateEntityRecord, DeleteEntityRecord)*

**Prompt**:
> Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` `"To Be Deleted"`, then delete it.

**Eval summary**: Verifies that `DeleteEntityRecord` carries no write-mode properties (`RecordState`, `IsInRecordView`, `OutputEntity`) and correctly receives the record ID from the preceding create.

| Check | Condition |
|-------|-----------|
| DeleteEntityRecord — type | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` |
| DeleteEntityRecord — EntityId | `"<EntityGuid>"` |
| DeleteEntityRecord — RecordId | Bound to `createdRecord.Id` |
| DeleteEntityRecord — absent | No `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`, no `OutputEntity` |
| DeleteEntityRecord — scope | `ScopeValue="Tenant"`, Solution properties nulled |
| Build | `uip rpa get-errors` returns no errors |

---

### S4 — Create + Query *(CreateEntityRecord, QueryEntityRecords)*

**Prompt**:
> Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` `"Query Target"`, then query all records in the entity (no filter, top 100) and return the list and total count as workflow outputs.

**Eval summary**: Verifies that `QueryEntityRecords` uses the correct output arguments (`OutputRecords`, `TotalRecords`) and produces no filter or write-mode properties for an unfiltered query.

| Check | Condition |
|-------|-----------|
| QueryEntityRecords — type | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` |
| QueryEntityRecords — EntityId | `"<EntityGuid>"` |
| QueryEntityRecords — Top | `Top="[100]"` |
| QueryEntityRecords — output | `OutputRecords` bound to `Records`; `TotalRecords` bound to `Total` |
| QueryEntityRecords — filter | `FilterArguments="{x:Null}"` or absent |
| QueryEntityRecords — absent | No `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView` |
| Build | `uip rpa get-errors` returns no errors |

---

### S5 — Batch Create + Batch Delete *(CreateMultipleEntityRecords, DeleteMultipleEntityRecords)*

**Prompt**:
> Create 3 records in Data Service entity `CodingAgentsBuildTimeEntity` with Titles `"Batch1"`, `"Batch2"`, `"Batch3"`, then delete all 3.

**Eval summary**: Verifies that batch create uses `ICollection<CodingAgentsBuildTimeEntity>` and batch delete correctly switches to `ICollection<Guid>` — the most common type-confusion error — and that `FailedRecords` outputs are wired on both activities.

| Check | Condition |
|-------|-----------|
| CreateMultiple — InputRecords type | `ICollection<CodingAgentsBuildTimeEntity>` — list of 3 constructed entity objects |
| CreateMultiple — OutputRecords | Bound to `createdRecords` (`IList<CodingAgentsBuildTimeEntity>`) |
| CreateMultiple — FailedRecords | Bound to `failedCreate` (`IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))`) |
| CreateMultiple — absent | No `RecordState`, no `IsInRecordView` |
| DeleteMultiple — InputRecords type | `ICollection<Guid>` — **not** entity objects; extracted from `createdRecords` |
| DeleteMultiple — FailedRecords | Bound to `failedDelete` (`IList(Of Guid)`) |
| Build | `uip rpa get-errors` returns no errors |

---

### S6 — File Lifecycle *(CreateEntityRecord, UploadFileToRecordField, DownloadFileFromRecordField, DeleteFileFromRecordField)*

**Prompt**:
> Create a record in Data Service entity `CodingAgentsBuildTimeFileEntity` with `Title` `"File Test"`, upload `"C:\temp\test.txt"` to the `Attachment` field, download it to `"C:\temp\downloaded.txt"`, then delete the file from the field.

**Eval summary**: Verifies that all three file activities set `Field` by name (not by ID), that the file field is excluded from `RecordState`, and that `DownloadedFileResource` is correctly wired as an output.

| Check | Condition |
|-------|-----------|
| All activities — type | `x:TypeArguments="local:CodingAgentsBuildTimeFileEntity"` on all four activities |
| All activities — EntityId | `"<FileEntityGuid>"` on all four activities |
| CreateEntityRecord — RecordState | `Attachment` field excluded from `RecordState` and `InputEntityInFieldView` (file fields not set via field view) |
| Upload — Field | `Field="Attachment"` |
| Upload — RecordId | Bound to `createdRecord.Id` |
| Upload — FilePath | `"C:\temp\test.txt"` |
| Upload — OutputEntity | Bound to `recordAfterUpload` |
| Upload — absent | No `RecordState`, no `IsInRecordView` |
| Download — Field | `Field="Attachment"` |
| Download — FilePath | `"C:\temp\downloaded.txt"` |
| Download — DownloadedFileResource | Bound to `downloadedFile` |
| Delete file — Field | `Field="Attachment"` |
| Delete file — RecordId | Bound to `createdRecord.Id` |
| Delete file — OutputEntity | Bound to `recordAfterDelete` |
| Build | `uip rpa get-errors` returns no errors |

---

## 4. Integration

**Purpose**: Validate correct output across diverse scenarios, error paths, optional parameters, and anti-patterns.

**Baseline inheritance**: Every integration scenario inherits the full check set of its referenced smoke scenario — project structure, all four XAML namespaces, TextExpression declarations, EntityId, TypeArguments, scope properties, RecordState shape, output wiring, and `uip rpa get-errors` returning no errors. The **Key Semantic Checks** column captures only the assertions that go beyond that baseline.

Integration prompts pass entity and field names only — no GUIDs. Scenarios that reference pre-existing records use permanently resident records in CodingAgentsEvals — no dynamic data writes occur.

---

### 4.1 Entity Record Activities

#### CreateEntityRecord

> **Baseline**: [S1 — Create + Read](#s1--create--read) — complete project boilerplate, all four namespaces, `IsInRecordView="[False]"`, `InputEntityInFieldView`, `RecordState.SelectedFields`, `OutputEntity`, `VisibleDynamicPropertiesInfo="{x:Null}"`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I1 | **Multi-type scalar fields** | "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` `'TypeTest'`, `Score` `42`, `Price` `9.99`, and `IsActive` `true`." | Verifies the agent maps each field to its correct XAML type in `InputEntityInFieldView` and `RecordState` — INT → `x:Int32`, DECIMAL → `x:Decimal`, BIT → `x:Boolean`. | `InputEntityInFieldView` constructs entity with correct typed literals; `RecordState` has four `DynamicEntityField` entries with matching types |
| I2 | **Date and datetime fields** | "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `EventDate` set to `'2026-04-18'` and `ScheduledAt` set to `'2026-04-18T09:00:00+05:30'`." | Verifies that DATE and DATETIMEOFFSET fields are passed as ISO 8601 strings (x:String), not as .NET DateTime objects. | Both fields use `x:String` in RecordState ArgumentValue; values match the ISO 8601 strings in the prompt |
| I3 | **Required vs optional — omit optional** | "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with only the required field `Title` set to `'RequiredOnly'`. The entity also has an optional field `Notes`." | Verifies the agent includes only required fields in `RecordState` when optional fields are not specified, avoiding unnecessary null entries. | `RecordState` contains exactly one `DynamicEntityField` for `Title` with `IsRequired="True"`; `Notes` field absent from `RecordState` and `InputEntityInFieldView` |
| I4 | **ContinueOnError=True** | "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` `'ErrorTest'`. The workflow should continue even if the activity fails." | Verifies `ContinueOnError` is set to True — a common requirement for resilient production workflows. | `ContinueOnError="[True]"` on the activity |

#### GetEntityRecordById

> **Baseline**: [S1 — Create + Read](#s1--create--read) — `x:TypeArguments`, `EntityId`, `RecordId` binding, `OutputEntity` wiring, no `RecordState` or `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I5 | **ExpansionDepth override** | "Fetch a record from Data Service entity `CodingAgentsBuildTimeEntity` and expand related entities to depth 1 only." | Verifies the agent correctly sets `ExpansionDepth` to a non-default value when the prompt specifies shallow expansion. | `ExpansionDepth="[1]"` on the activity (default is 2) |
| I6 | **OutputEntity used downstream** | "Fetch a record from Data Service entity `CodingAgentsBuildTimeEntity` and log its `Title` field value to the output." | Verifies that `OutputEntity` is bound to a typed variable whose fields are accessed in a subsequent activity — confirming the agent correctly models the entity type as accessible after retrieval. | `OutputEntity` bound to a typed variable (e.g. `retrievedRecord`); subsequent activity references `retrievedRecord.Title` |
| I7 | **Anti-pattern: IEntity type argument** | "Fetch a record from Data Service entity `CodingAgentsBuildTimeEntity` using the generic entity interface type." | Verifies the agent does not use `udd:IEntity` as the type argument even when prompted with "generic" or "interface" language — a runtime-fatal mistake. | `x:TypeArguments="local:CodingAgentsBuildTimeEntity"` — NOT `x:TypeArguments="udd:IEntity"`; `uip rpa get-errors` returns no errors |

#### UpdateEntityRecord

> **Baseline**: [S2 — Create + Update](#s2--create--update) — `IsInRecordView="[False]"`, `InputEntityInFieldView`, `RecordState.SelectedFields` with `DynamicEntityField` entries, `RecordId` binding, `OutputEntity`, `VisibleDynamicPropertiesInfo="{x:Null}"`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I8 | **Partial field update** | "Update only the `Title` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeEntity`, setting it to `'Revised'`. The entity also has a `Score` field — leave it unchanged." | Verifies the agent includes only the fields being updated in `RecordState.SelectedFields` — not all entity fields. | `RecordState` contains exactly one `DynamicEntityField` for `Title`; `Score` field absent from `RecordState` and `InputEntityInFieldView` |
| I9 | **Update to empty string** | "Update the `Title` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeEntity` to an empty string." | Verifies the agent correctly represents an intentional empty-string update in `InputEntityInFieldView` and `RecordState`, rather than omitting the field. | `InputEntityInFieldView` sets `Title = ""`; `DynamicEntityField` for Title has `ArgumentValue` set to empty string (not null or absent) |
| I10 | **Anti-pattern: InputEntity property** | "Update the `Score` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeEntity` to `100`." | Verifies the agent uses `InputEntityInFieldView` and `RecordState`, not the `InputEntity` property — which causes Studio desync bugs. | `InputEntityInFieldView` present and set; `InputEntity` property absent from the activity |
| I11 | **ContinueOnError=True** | "Update the `Title` of a pre-existing record in Data Service entity `CodingAgentsBuildTimeEntity` to `'SafeUpdate'`. The workflow should continue even if the update fails." | Verifies `ContinueOnError` is correctly applied to an update activity. | `ContinueOnError="[True]"` on `UpdateEntityRecord` |

#### DeleteEntityRecord

> **Baseline**: [S3 — Create + Delete](#s3--create--delete) — `x:TypeArguments`, `EntityId`, `RecordId` binding, no `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`, no `OutputEntity`, Solution properties nulled.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I12 | **ContinueOnError=True** | "Delete a pre-existing record from Data Service entity `CodingAgentsBuildTimeEntity`. The workflow should not abort if the deletion fails." | Verifies `ContinueOnError` is set without introducing any write-mode properties that delete does not support. | `ContinueOnError="[True]"`; still no `RecordState`, `IsInRecordView`, or `OutputEntity` |
| I13 | **Sequential delete of two records** | "Delete two pre-existing records from Data Service entity `CodingAgentsBuildTimeEntity` one after the other." | Verifies the agent generates two independent `DeleteEntityRecord` activities rather than attempting a batch approach. | Two separate `uda:DeleteEntityRecord` activities in sequence; each with its own `RecordId` binding |

#### QueryEntityRecords

> **Baseline**: [S4 — Create + Query](#s4--create--query) — `x:TypeArguments`, `EntityId`, `OutputRecords` and `TotalRecords` wired, no `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I14 | **Equality filter** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `Status` equals `'Active'`." | Verifies the agent generates a correct `FilterArguments` equality expression, not a post-fetch LINQ filter. | `FilterArguments` set with `Equals` operator on `Status` field; `FilterValues` contains `'Active'`; `OutputRecords` wired |
| I15 | **Contains filter** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `Title` contains `'Invoice'`." | Verifies the `Contains` filter operator is used (not `StartsWith` or `Equals`). | `FilterArguments` set with `Contains` operator on `Title`; `FilterValues` contains `'Invoice'` |
| I16 | **GreaterThan filter** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `Score` is greater than `50`." | Verifies the `MoreThan` operator is correctly applied to a numeric field. | `FilterArguments` uses `MoreThan` operator on `Score`; `FilterValues` contains `50` |
| I17 | **Compound AND filter** | "Query records in Data Service entity `CodingAgentsBuildTimeEntity` where `Status` equals `'Active'` and `Score` is greater than `10`." | Verifies the agent generates a filter group combining two conditions rather than two separate queries. | `FilterArguments` contains two filter conditions in a single group; both `Status` (Equals) and `Score` (MoreThan) present |
| I18 | **Sort descending** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity`, sorted by `Score` from highest to lowest." | Verifies `SortByField` and `SortAscending=False` are set — the agent must not default to ascending or omit the sort. | `SortByField="Score"` (or equivalent); `SortAscending="[False]"` |
| I19 | **Pagination — Top + Skip** | "Query records in Data Service entity `CodingAgentsBuildTimeEntity`, returning the second page of 10 records." | Verifies the agent correctly sets both `Top` and `Skip` for offset-based pagination rather than using cursor or fetching all records. | `Top="[10]"`; `Skip="[10]"` |
| I20 | **TotalRecords output** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` and return both the list and the total count of matching records as workflow outputs." | Verifies `TotalRecords` is wired as a workflow output, not just `OutputRecords` — required for pagination UI patterns. | `TotalRecords` bound to a workflow out-argument; `OutputRecords` also wired |
| I21 | **Date equality filter** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `EventDate` equals `'2026-04-18'`." | Verifies the agent treats a DATE field filter value as an ISO 8601 string, not a .NET DateTime — the field type does not change the operator, only the value representation. | `FilterArguments` uses `Equals` on `EventDate`; `FilterValues` contains the string `'2026-04-18'` (not a DateTime literal) |
| I22 | **DateTime range — after a timestamp** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `ScheduledAt` is after `'2026-04-01T00:00:00Z'`." | Verifies `MoreThan` is applied to a DATETIMEOFFSET field with an ISO 8601 timestamp string — the agent must not convert it to a DateTime object or use a numeric comparison. | `FilterArguments` uses `MoreThan` on `ScheduledAt`; `FilterValues` contains the ISO 8601 string `'2026-04-01T00:00:00Z'` |
| I23 | **Date range — between two dates** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `EventDate` falls between `'2026-01-01'` and `'2026-12-31'` inclusive." | Verifies the agent generates a compound filter using `NoLessThan` and `NoMoreThan` on a DATE field — not a single-operator approximation or LINQ post-filter. | `FilterArguments` contains two conditions on `EventDate`: `NoLessThan '2026-01-01'` and `NoMoreThan '2026-12-31'`; both values as ISO 8601 date strings |
| I24 | **Boolean IsTrue filter** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where `IsActive` is true." | Verifies the agent uses the `IsTrue` operator for a BIT field rather than `Equals` with a boolean literal — `IsTrue` requires no `FilterValues` entry. | `FilterArguments` uses `IsTrue` operator on `IsActive`; no corresponding `FilterValues` entry for this condition |
| I25 | **IsNull filter on optional field** | "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where the optional field `Notes` has no value set." | Verifies the agent uses the `IsNull` operator rather than an equality check against empty string or null literal. | `FilterArguments` uses `IsNull` operator on `Notes`; no `FilterValues` entry for this condition |

---

### 4.2 Batch Activities

#### CreateMultipleEntityRecords

> **Baseline**: [S5 — Batch Create + Batch Delete](#s5--batch-create--batch-delete) — `InputRecords` as `ICollection<CodingAgentsBuildTimeEntity>`, `OutputRecords` wired, `FailedRecords` wired, no `RecordState`, no `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I26 | **Large batch** | "Create 10 records in Data Service entity `CodingAgentsBuildTimeEntity` with Titles `'R01'` through `'R10'`." | Verifies the agent constructs a `List(Of CodingAgentsBuildTimeEntity)` with 10 items rather than falling back to 10 individual `CreateEntityRecord` calls. | Single `uda:CreateMultipleEntityRecords` activity; `InputRecords` expression constructs a list of 10 entity objects |
| I27 | **ContinueBatchOnFailure=False** | "Create 3 records in Data Service entity `CodingAgentsBuildTimeEntity`. Stop the entire batch immediately if any record fails." | Verifies `ContinueBatchOnFailure` is set to False — the agent must not leave it at the default True. | `ContinueBatchOnFailure="[False]"` on the activity |
| I28 | **FailedRecords type correctness** | "Create 3 records in Data Service entity `CodingAgentsBuildTimeEntity` and capture any failed records with their error messages." | Verifies `FailedRecords` is typed as `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))` — a common type-confusion point. | `FailedRecords` bound to a variable typed `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))`; `Item1` is the error string, `Item2` is the failed entity |

#### UpdateMultipleEntityRecords

> **Baseline**: [S5 — Batch Create + Batch Delete](#s5--batch-create--batch-delete) (closest batch smoke scenario). Additional fixed checks: `InputRecords` as `ICollection<CodingAgentsBuildTimeEntity>` (entity objects, each with `Id` set), `OutputRecords` wired, `FailedRecords` typed as `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I29 | **Id required on each entity** | "Update the `Title` field of 3 pre-existing records in Data Service entity `CodingAgentsBuildTimeEntity` to `'Updated1'`, `'Updated2'`, `'Updated3'` respectively." | Verifies each entity object in `InputRecords` carries its `Id` property — missing `Id` causes the batch to fail, as the activity cannot determine which record to update. | `InputRecords` expression constructs entities with both `.Id` and `.Title` set on each object |
| I30 | **ContinueBatchOnFailure=False** | "Update 3 records in Data Service entity `CodingAgentsBuildTimeEntity`. Abort the batch if any update fails." | Verifies `ContinueBatchOnFailure` is set to False. | `ContinueBatchOnFailure="[False]"` |
| I31 | **FailedRecords type correctness** | "Update 3 records in Data Service entity `CodingAgentsBuildTimeEntity` and capture failed updates with their error messages." | Verifies `FailedRecords` for update is correctly typed as `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))` — same type as batch create. | `FailedRecords` variable typed `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))` |

#### DeleteMultipleEntityRecords

> **Baseline**: [S5 — Batch Create + Batch Delete](#s5--batch-create--batch-delete) — `InputRecords` as `ICollection<Guid>`, `FailedRecords` typed as `IList(Of Guid)`, no `RecordState`, no `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I32 | **Input must be Guid collection** | "Delete 3 pre-existing records from Data Service entity `CodingAgentsBuildTimeEntity` in a single batch operation." | Verifies `InputRecords` is `ICollection<Guid>` — not entity objects — the most common type error in batch delete. | `InputRecords` expression produces `ICollection(Of Guid)` or `List(Of Guid)`; entity objects not used |
| I33 | **ContinueBatchOnFailure=False** | "Delete 3 records from Data Service entity `CodingAgentsBuildTimeEntity`. Stop immediately if any deletion fails." | Verifies `ContinueBatchOnFailure` is set to False. | `ContinueBatchOnFailure="[False]"` |
| I34 | **FailedRecords type correctness** | "Delete 3 records from Data Service entity `CodingAgentsBuildTimeEntity` and capture the IDs of any that could not be deleted." | Verifies `FailedRecords` for batch delete is typed as `IList(Of Guid)` — not a Tuple type as in create/update. | `FailedRecords` variable typed `IList(Of Guid)` |

---

### 4.3 File Activities

#### UploadFileToRecordField

> **Baseline**: [S6 — File Lifecycle](#s6--file-lifecycle) — `Field` set by name, `RecordId` binding, `OutputEntity` wired, no `RecordState`, no `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I35 | **Upload via FileResource** | "Upload a file resource to the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity`. The file is available as a resource object in variable `fileRes`." | Verifies the agent uses `FileResource` (`InArgument<IResource>`) instead of `FilePath` when the input is a resource object. | `FileResource` property bound to `fileRes`; `FilePath` absent or null |
| I36 | **OutputEntity after upload** | "Upload `'C:\docs\report.pdf'` to the `Report` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity` and return the updated entity as a workflow output." | Verifies `OutputEntity` is wired to capture the entity state post-upload, not discarded. | `OutputEntity` bound to a workflow out-argument or variable; `Field="Report"` |
| I37 | **Field name case sensitivity** | "Upload `'C:\temp\file.txt'` to the field named `attachmentFile` (camelCase) on a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity`." | Verifies the agent sets `Field` to the exact name as given — field names are case-sensitive at runtime. | `Field="attachmentFile"` exactly (not `AttachmentFile` or `attachment_file`) |

#### DownloadFileFromRecordField

> **Baseline**: [S6 — File Lifecycle](#s6--file-lifecycle) — `Field` set by name, `RecordId` binding, `DownloadedFileResource` wired, no `RecordState`, no `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I38 | **Download without specifying destination** | "Download the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity` and make it available for further processing." | Verifies the agent wires `DownloadedFileResource` as the output when no explicit file path is specified — not omitting the output entirely. | `DownloadedFileResource` bound to a variable; `FilePath` absent or null |
| I39 | **DownloadedFileResource used downstream** | "Download the file from the `Report` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity` and log its local path." | Verifies `DownloadedFileResource.LocalPath` is correctly referenced in a downstream activity — confirming the agent models the `ILocalResource` type. | `DownloadedFileResource` bound to a typed variable; downstream activity references `.LocalPath` on that variable |
| I40 | **No ExpansionDepth property** | "Download the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity`." | Verifies the agent does not set `ExpansionDepth` on a download activity — it is not a supported property for file operations. | `ExpansionDepth` absent from `DownloadFileFromRecordField` activity |

#### DeleteFileFromRecordField

> **Baseline**: [S6 — File Lifecycle](#s6--file-lifecycle) — `Field` set by name, `RecordId` binding, `OutputEntity` wired, no `RecordState`, no `IsInRecordView`.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I41 | **OutputEntity after file delete** | "Delete the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity` and return the updated entity state." | Verifies `OutputEntity` is wired on `DeleteFileFromRecordField` — confirming the agent knows this activity returns the entity post-deletion, unlike `DeleteEntityRecord`. | `OutputEntity` bound to a variable or out-argument |
| I42 | **ContinueOnError=True** | "Delete the file from the `Report` field of a pre-existing record in Data Service entity `CodingAgentsBuildTimeFileEntity`. The workflow should proceed even if no file is attached." | Verifies `ContinueOnError` is applied, appropriate for the case where a file may or may not exist. | `ContinueOnError="[True]"` on the activity |
| I43 | **Field name matches upload** | "Upload `'C:\temp\doc.pdf'` to the `Contract` field of a record in Data Service entity `CodingAgentsBuildTimeFileEntity`, then delete the file from the same field." | Verifies the agent uses identical `Field` values on both upload and delete — a round-trip field-name consistency check. | `Field="Contract"` on both `UploadFileToRecordField` and `DeleteFileFromRecordField` |

---

## 5. Quality (~10 scenarios)

**Quality gate concept**: Smoke and integration tests evaluate depth — they verify that each individual activity is configured correctly in isolation. Quality tests evaluate breadth — they verify that the agent can compose multiple activities into a coherent workflow without losing correctness at the seams. The question being answered here is not "did the agent set the right property on this activity?" but "did the agent build a workflow that hangs together end-to-end?". Assertions focus on data flow between steps (output variables correctly chained as inputs to the next activity), type consistency across all activities in the workflow, and structural decisions that span activity boundaries (e.g. file fields excluded from RecordState in both create and update steps). Per-activity configuration details are intentionally left to smoke and integration coverage.

---

### E1 — Basic CRUD Lifecycle

> "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` with a `Title` field set to `"CRUD Test"`. Read the record back by its ID. Update the record, changing `Title` to `"Updated"`. Then delete the record."

**Eval summary:** Verifies the full single-record lifecycle — that the agent chains `OutputEntity.Id` correctly across all four activities and applies the correct structural pattern (IsInRecordView, RecordState, TypeArguments) per activity type.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `InputEntityInFieldView` sets Title; `OutputEntity` → `createdRecord` |
| 2 | `GetEntityRecordById` | `RecordId` bound to `createdRecord.Id`; `OutputEntity` → `fetchedRecord` |
| 3 | `UpdateEntityRecord` | `RecordId` bound to `createdRecord.Id`; `InputEntityInFieldView` sets Title to `"Updated"`; `RecordState` updated; `OutputEntity` wired |
| 4 | `DeleteEntityRecord` | `RecordId` bound to `createdRecord.Id`; no `RecordState`, no `OutputEntity` |

**Build condition:** `uip rpa get-errors` exits 0, no type errors, four-namespace block present.

---

### E2 — Batch Create + Query + Batch Delete

> "Create 5 records in Data Service entity `CodingAgentsBuildTimeEntity`, each with a `Title` field set to `"Batch Item 1"` through `"Batch Item 5"`. Query all records in the entity. Then delete all 5 created records."

**Eval summary:** Verifies that `CreateMultipleEntityRecords` outputs are correctly piped into a LINQ ID-extraction expression for `DeleteMultipleEntityRecords`, and that `QueryEntityRecords` uses the same typed `x:TypeArguments`.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `InputRecords` is `ICollection<CodingAgentsBuildTimeEntity>` (5 items); `OutputRecords` → `createdRecords` |
| 2 | `QueryEntityRecords` | `Top="[100]"`; `OutputRecords` → `queryResult`; `FilterArguments` absent or null |
| 3 | `DeleteMultipleEntityRecords` | `InputRecords` is `ICollection<Guid>` — expression extracts IDs from `createdRecords`; `FailedRecords` wired |

**Build condition:** `uip rpa get-errors` exits 0; all three activities share the same `local:CodingAgentsBuildTimeEntity` type argument.

---

### E3 — Batch Create + Batch Update + Filter Query

> "Create 3 records in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` values `"Alpha"`, `"Beta"`, `"Gamma"` and a numeric `Score` field set to `1`, `2`, `3` respectively. Update all 3 records to set `Score` to `10`. Then query records where `Score` equals `10` and capture the results."

**Eval summary:** Verifies batch update correctly uses entity-typed `InputRecords` (not Guids), and that the filter query correctly encodes an equality predicate on a numeric field.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `InputRecords` constructs 3 `CodingAgentsBuildTimeEntity` objects with `Title` and `Score`; `OutputRecords` → `createdRecords` |
| 2 | `UpdateMultipleEntityRecords` | `InputRecords` is `ICollection<CodingAgentsBuildTimeEntity>` with `.Id` wired from `createdRecords` and `Score = 10`; `FailedRecords` wired |
| 3 | `QueryEntityRecords` | `FilterArguments` encodes `Score Equals 10`; `OutputRecords` → `filtered` |

**Build condition:** `uip rpa get-errors` exits 0; `UpdateMultipleEntityRecords` uses entity objects (not Guids) in `InputRecords`.

---

### E4 — Full File Lifecycle

> "Create a record in Data Service entity `CodingAgentsBuildTimeFileEntity` with a `Title` field set to `"File Test"`. Attach the file at `'C:\temp\source.txt'` to the `Attachment` field. Download the file to `'C:\temp\copy.txt'`. Then remove the attachment from the record."

**Eval summary:** Verifies the complete file attach/detach cycle — correct field-name binding across all three file activities, no RecordState on file activities, and proper output wiring for `DownloadedFileResource` and `OutputEntity`.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `Title` in `InputEntityInFieldView`; `Attachment` field **not** in `RecordState`; `OutputEntity` → `createdRecord` |
| 2 | `UploadFileToRecordField` | `RecordId` = `createdRecord.Id`; `Field="Attachment"`; `FilePath="C:\temp\source.txt"`; `OutputEntity` → `recordAfterUpload` |
| 3 | `DownloadFileFromRecordField` | `RecordId` = `createdRecord.Id`; `Field="Attachment"`; `FilePath="C:\temp\copy.txt"`; `DownloadedFileResource` wired |
| 4 | `DeleteFileFromRecordField` | `RecordId` = `createdRecord.Id`; `Field="Attachment"`; `OutputEntity` wired |

**Build condition:** `uip rpa get-errors` exits 0; no `RecordState` on file activities; `Field` value identical across steps 2, 3, 4.

---

### E5 — Paginated Query Across Two Pages

> "Create 15 records in Data Service entity `CodingAgentsBuildTimeEntity`, each with a `Title` field. Query the first 10 records. Then query the next 5 using the appropriate skip offset. Capture both result sets and the total record count."

**Eval summary:** Verifies that `Top` and `Skip` are correctly encoded as integer expressions on two separate `QueryEntityRecords` activities, and that `TotalRecords` is wired on at least one call.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | 15 entity objects in `InputRecords`; `OutputRecords` wired |
| 2 | `QueryEntityRecords` (page 1) | `Top="[10]"`; `Skip="[0]"` or absent; `OutputRecords` → `page1`; `TotalRecords` → `total` |
| 3 | `QueryEntityRecords` (page 2) | `Top="[10]"` or `"[5]"`; `Skip="[10]"`; `OutputRecords` → `page2` |

**Build condition:** `uip rpa get-errors` exits 0; `Skip` uses an integer expression, not a string literal.

---

### E6 — All Scalar Field Types

> "Create a record in Data Service entity `CodingAgentsBuildTimeEntity` that has fields of each scalar type: a text field `Title`, an integer field `Score`, a decimal field `Price`, a boolean field `IsActive`, a date field `EventDate`, and a datetime field `ScheduledAt`. Then read the record back by its ID."

**Eval summary:** Verifies the agent produces correct VB.NET literal syntax for every scalar SqlType — string, integer, decimal, Boolean, Date, and DateTimeOffset — all encoded in `InputEntityInFieldView` with matching `RecordState` entries.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `InputEntityInFieldView` includes all 6 fields with correct VB literals (e.g. `New Date(...)`, `True`/`False`, `Decimal` literal, integer literal); `RecordState` has one `DynamicEntityField` per field |
| 2 | `GetEntityRecordById` | `RecordId` = `createdRecord.Id`; `OutputEntity` → out-argument; no `RecordState` |

**Build condition:** `uip rpa get-errors` exits 0; no type argument errors; all 6 field types compile cleanly.

---

### E7 — ContinueOnError Recovery

> "Attempt to create a record in Data Service entity `CodingAgentsBuildTimeEntity` with `Title` set to `"Primary"`. If the step fails, the workflow should continue and create a fallback record with `Title` set to `"Fallback"`."

**Eval summary:** Verifies `ContinueOnError="[True]"` is set on the first `CreateEntityRecord` and a second create activity follows it unconditionally — demonstrating the agent correctly models the ContinueOnError recovery pattern.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `ContinueOnError="[True]"`; `InputEntityInFieldView` sets Title to `"Primary"` |
| 2 | `CreateEntityRecord` | `ContinueOnError` absent or `"[False]"`; `InputEntityInFieldView` sets Title to `"Fallback"` |

**Build condition:** `uip rpa get-errors` exits 0; `ContinueOnError` is a bracketed Boolean expression `[True]`, not a string literal.

---

### E8 — Partial Batch Failure Handling

> "Create 3 records in Data Service entity `CodingAgentsBuildTimeEntity` — two with valid `Title` values and one intentionally missing a required field. Wire both the successfully created records and the failed ones to separate workflow outputs."

**Eval summary:** Verifies `OutputRecords` and `FailedRecords` are both wired on `CreateMultipleEntityRecords`, and that the agent correctly types `FailedRecords` as `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))`.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `InputRecords` has 3 objects (2 with Title, 1 without required field); `OutputRecords` → out-argument `SucceededRecords`; `FailedRecords` → out-argument `FailedItems` |

**Build condition:** `uip rpa get-errors` exits 0; `FailedRecords` typed as `IList(Of Tuple(Of String, CodingAgentsBuildTimeEntity))`; `OutputRecords` typed as `IList<CodingAgentsBuildTimeEntity>`.

---

### E9 — Filter with Sort

> "Query all records in Data Service entity `CodingAgentsBuildTimeEntity` where the `Score` field is greater than `5`. Sort the results by `Score` descending. Capture the first result's ID and delete that record."

**Eval summary:** Verifies that `FilterArguments` encodes a `MoreThan` predicate, an `OrderBy` or sort expression is present, and the ID extracted from `OutputRecords` is correctly fed into `DeleteEntityRecord`.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `QueryEntityRecords` | `FilterArguments` encodes `Score MoreThan 5`; sort property set descending; `OutputRecords` → `results` |
| 2 | `DeleteEntityRecord` | `RecordId` bound to `results(0).Id` or equivalent first-item expression |

**Build condition:** `uip rpa get-errors` exits 0; no `RecordState` on `QueryEntityRecords`; `DeleteEntityRecord` has no `RecordState` or `InputEntityInFieldView`.

---

### E10 — File + CRUD Combined

> "Create a record in Data Service entity `CodingAgentsBuildTimeFileEntity` with `Title` set to `"Doc Record"`. Attach the file `'C:\docs\contract.pdf'` to the `Contract` field. Update the record's `Title` to `"Signed Doc"`. Then read the record back."

**Eval summary:** Verifies the agent correctly interleaves a file activity between record mutation steps — particularly that `UpdateEntityRecord` does not include the `Contract` file field in its `RecordState`, and that all activities share the same typed `x:TypeArguments`.

| Step | Activity | Key XAML Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | Title in `RecordState`; `Contract` file field absent from `RecordState`; `OutputEntity` → `createdRecord` |
| 2 | `UploadFileToRecordField` | `RecordId` = `createdRecord.Id`; `Field="Contract"`; `OutputEntity` → `recordAfterUpload` |
| 3 | `UpdateEntityRecord` | `RecordId` = `createdRecord.Id`; `RecordState` includes only `Title`; `Contract` absent from `RecordState` |
| 4 | `GetEntityRecordById` | `RecordId` = `createdRecord.Id`; `OutputEntity` → out-argument |

**Build condition:** `uip rpa get-errors` exits 0; `Contract` field absent from `RecordState` on all non-file activities.
