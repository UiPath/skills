# Testing Guide

Reference for XAML test automation features in UiPath RPA projects — XAML test case structure, data-driven testing, XAML test activities, execution templates, and mock testing.

> For coded test case creation (Given-When-Then, assertions, Before/After hooks), see [coded/operations-guide.md § Add a Test Case File](coded/operations-guide.md).

## Table of Contents

- [Test Manager Setup (CLI)](#test-manager-setup-cli)
- [XAML Test Case Structure (Given-When-Then)](#xaml-test-case-structure-given-when-then)
- [Data-Driven Testing](#data-driven-testing)
- [XAML Test Activities](#xaml-test-activities)
- [Execution Templates](#execution-templates)
- [Mock Testing (XAML Only) — WIP](#mock-testing-xaml-only--wip)

---

## Test Manager Setup (CLI)

Linking a project to Test Manager (server connection + default project) can be done headlessly with `uip rpa tm`, without opening Studio — useful before authoring test cases that reference Test Manager test cases. Commands, ordering constraints (`connect` before `set-default-project`, server switches clearing the default project), and `reloadHint` handling: [cli-reference.md § Test Manager](cli-reference.md#test-manager). The CLI does **not** validate the project id against the server; obtain a real id from Test Manager (the runtime `uip tm project list` tool can list them).

---

## XAML Test Case Structure (Given-When-Then)

XAML test cases use a **Given-When-Then** structure — three nested `<Sequence>` elements inside a parent Sequence. The agent generates these directly as XAML.

### XAML Structure — Test Case Invoking a Workflow

The core pattern: a parent Sequence with three child Sequences named `"... Given"`, `"... When"`, `"... Then"`. The **When** section invokes the workflow under test. Verification activities go in **Then**, except a check of a state that later steps change (a confirmation after a save in an end-to-end flow): it sits right after the step that produces that state, in When or in a workflow When invokes. A verification records its assertion in the test result from any depth.

```xml
<!-- Body inside <Activity> (after namespaces/references) -->
<Sequence DisplayName="TestMyWorkflow">
  <!-- GIVEN — set up preconditions -->
  <Sequence DisplayName="... Given">
    <!-- Assign variables, open apps, prepare test data -->
  </Sequence>

  <!-- WHEN — execute the workflow under test -->
  <Sequence DisplayName="... When">
    <ui:InvokeWorkflowFile
      DisplayName="MyWorkflow - Invoke Workflow File (MyWorkflow.xaml)"
      WorkflowFileName="MyWorkflow.xaml"
      UnSafe="False">
      <ui:InvokeWorkflowFile.Arguments>
        <scg:Dictionary x:TypeArguments="x:String, Argument" />
      </ui:InvokeWorkflowFile.Arguments>
    </ui:InvokeWorkflowFile>
  </Sequence>

  <!-- THEN — verify results -->
  <Sequence DisplayName="... Then">
    <!-- VerifyExpression, VerifyExpressionWithOperator, etc. -->
  </Sequence>
</Sequence>
```

Required xmlns for `InvokeWorkflowFile`:
```
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

### Default Values for Test-Case Arguments

A test case authored with an `<x:Property Name="in_X" Type="InArgument(x:String)" />` argument should generally bake in a default so `uip rpa run --file-path <TestCase>.xaml` is runnable without `--input-arguments`. Use the canonical root-attribute syntax — see [xaml/xaml-editing-catalog.md § Setting Default Values for Arguments](xaml/xaml-editing-catalog.md#setting-default-values-for-arguments). The wrong forms (bare attribute, `<x:Property.Value>`, `<InArgument>` child of `<x:Property>`) all produce confusing `member not supported` errors — the doc explicitly lists them so you don't waste time trying. An argument bound to a Data Service entity takes no default ([§ Data Service Entity](#data-service-entity)).

### XAML Structure — Execution Template Placeholder

The `ui:Placeholder` sits in the execution template, where the case runs ([§ Execution Templates](#execution-templates)); a bound case is an ordinary Given-When-Then file:

```xml
<Sequence DisplayName="Run case">
  <ui:Placeholder
    Description="This placeholder activity will be replaced at build time and can only be used within an execution template." />
</Sequence>
```

### Passing Arguments to Invoked Workflows

If the workflow has arguments, pass them as entries of `InvokeWorkflowFile.Arguments`:

```xml
<ui:InvokeWorkflowFile WorkflowFileName="CalculateDiscount.xaml" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <InArgument x:TypeArguments="x:Decimal" x:Key="amount">
      <CSharpValue x:TypeArguments="x:Decimal">1500.00m</CSharpValue>
    </InArgument>
    <InArgument x:TypeArguments="x:Decimal" x:Key="discountRate">
      <CSharpValue x:TypeArguments="x:Decimal">0.10m</CSharpValue>
    </InArgument>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

### project.json Registration

Register every XAML test case in `designOptions.fileInfoCollection` — this is **Common Rule 10** in SKILL.md and applies to both XAML and coded test cases. Test cases live **only** in `fileInfoCollection`, never in `entryPoints` — `entryPoints` is for executable workflow files in Process projects (e.g. `Main.xaml`), and test cases are not workflow entry points regardless of project type.

Copy-paste JSON snippet (including `publishAsTestCase` for coded test cases and `dataVariationFilePath` for data-driven): [../assets/json-template.md](../assets/json-template.md).

**Required keys per entry:**

- `editingStatus` — `"InProgress"` on creation; `"Publishable"` only on explicit user request (see lifecycle note below).
- `testCaseId` — fresh GUID, lowercase 8-4-4-4-12 hex (e.g. `2d81aebd-fbc1-4a66-8418-be77a34a3a21`). Generate via `[guid]::NewGuid()` in PowerShell or `uuidgen` on Unix.
- `testCaseType` — `"TestCase"`.
- `executionTemplateInvokeIsolated` — `false` unless the test runs under an execution template that requires isolation.
- `fileName` — relative path of the `.xaml` or `.cs` test case file from the project root.

**Template keys:** an execution template is registered as its own entry (`templateType` `ExecutionTemplate`), a new-test-case template with `templateType` `TestCase`, and a case is bound to its execution template with `executionTemplatePath` and `executionTemplateType` on its entry. Shapes: [../assets/json-template.md](../assets/json-template.md); behaviour: [§ Execution Templates](#execution-templates).

> **`editingStatus` lifecycle:** Set to `"InProgress"` when creating a new test case. Update to `"Publishable"` only when the user explicitly asks to mark the test case as ready.

### What NOT to Do

- Do NOT place verification activities in the **When** container, except a mid-flow check ([§ XAML Structure — Test Case Invoking a Workflow](#xaml-structure--test-case-invoking-a-workflow))
- Do NOT forget to add the `xmlns:ui` namespace when using `InvokeWorkflowFile`

---

## Data-Driven Testing

Data-driven testing executes the same test case multiple times with different input data sets. Each data row represents a separate test scenario.

### Data Sources Overview

| Source | Where Data Lives | Best For | Agent Support |
|--------|-----------------|----------|---------------|
| **Variations files** | `.variations/` folder in project | File-based test data committed with the project | CLI: `test-data add-variation` |
| **Test Data Queues** | UiPath Orchestrator | Large-scale distributed testing, parallel execution. [To be deprecated](https://docs.uipath.com/overview-guide/docs/deprecation-timeline) at a later date | CLI: `test-data add-queue` |
| **Data Service** | Data Fabric entity | Centralized, shared test data, filtered per test case; records change without a republish | Files: [§ Data Service Entity](#data-service-entity) |

> For coded data-driven tests using default parameters, see [coded/operations-guide.md § Add a Test Case File](coded/operations-guide.md).

### Variations Files (Coded & XAML)

Store test data in the `.variations/` folder at the project root. Each JSON file maps to a test case and contains rows of input data.

```
MyProject/
├── .variations/
│   └── TestProcessInvoice.json
├── TestProcessInvoice.cs
└── project.json
```

The `.variations/` directory is available in all project types (Process, Tests, Library). Data files must be in **JSON format**.

### Adding Test Data via CLI

Two commands attach file and queue sources to a test case. Both register the data source in project metadata, extract arguments from the source schema, and add them to the test case (via Studio's workflow management API for XAML, via Roslyn for coded test cases). A Data Service source is written as files ([§ Data Service Entity](#data-service-entity)).

#### `test-data add-variation` — File-based (JSON)

```bash
uip rpa test-data add-variation --test-case-path "<TEST_CASE_FILE>" --data-variation-path "<DATA_FILE>" --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-path` | Yes | Relative path to the test case file (`.xaml` or `.cs`) |
| `--data-variation-path` | Yes | Relative path to the JSON data file in `.variations/` |

Parses fields from the JSON file and creates one argument per field with matching type and a default value from the first entry.

**Example:**
```bash
uip rpa test-data add-variation --test-case-path "TestProcessInvoice.cs" --data-variation-path ".variations/InvoiceData.json" --project-dir "C:\MyProject" --output json
```

#### `test-data add-queue` — Orchestrator Test Data Queue

> **Prerequisite:** Use the **uipath-platform** skill to discover queue details (name, ID, folder) before calling this command.

```bash
uip rpa test-data add-queue --test-case-path "<TEST_CASE_FILE>" --queue-name "<QUEUE_NAME>" --folder-path "<FOLDER>" --queue-id <ID> --project-dir "<PROJECT_DIR>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-path` | Yes | Relative path to the test case (`.xaml` or `.cs`) |
| `--queue-name` | Yes | Name of the Test Data Queue in Orchestrator |
| `--folder-path` | Yes | Orchestrator folder path |
| `--queue-id` | Yes | Orchestrator ID of the queue |

Creates an `IDictionary<string, object>` argument named after the queue (camelCase).

**Example:**
```bash
uip rpa test-data add-queue --test-case-path "TestLoanApproval.cs" --queue-name "loan_applications" --folder-path "Shared" --queue-id 123 --project-dir "C:\MyProject" --output json
```

> **Critical:** Do NOT rename the auto-generated test data queue argument. If you change its name, data retrieval silently fails.

### Data Service Entity

Every record matching the test case's filter is one variation: Test Manager runs the case once per record. Records are queried when the run starts, so records added or edited later need no republish.

> **Prerequisites:**
> 1. **Discover / verify entities** — run `uip rpa data-fabric-entities list --project-dir "<PROJECT_DIR>" --output json` to see what is installed and what is available in the connected tenant. (Alternatively, the `uipath-platform` skill can discover entities directly in Orchestrator.)
> 2. **Install the target entity into the project** if not already installed — `uip rpa data-fabric-entities install --add "<ENTITY_NAME>" --project-dir "<PROJECT_DIR>" --output json`. The test case uses the entity's generated type. See [cli-reference.md § Data Fabric Entities](cli-reference.md#commands----data-fabric-entities).

Write the binding as the four files below. Do not use `uip rpa test-data add-entity`: it runs only in Studio Desktop, takes no filter, leaves the argument and the `project.json` entry unsaved in the open designer, and writes the entity's first record (user names and emails included) as the argument's default.

`<NAMESPACE>` = `project.json` → `entitiesStores[0].namespace`. `<ARG>` = entity name in camelCase; keep it exactly, the data binds by this name.

1. **`.variations/<ENTITY>_<NAME>.json`** — `<NAME>` names the filter (short: the generated setup workflow is named after the file):
   ```json
   {"EntityName":"<ENTITY>","TypeName":"<NAMESPACE>.<ENTITY>","Filters":"<BASE64_QUERY>","TestCaseId":"<UUID_V4>","Name":"<NAME>"}
   ```
   `TestCaseId` is a fresh GUID, not the case's. At pack, Studio generates from this file a setup workflow with that id (`.generated/.setup/Fetch <ENTITY>_<NAME> Test Data.xaml`); it queries the entity and passes each record to the case.
2. **`.variations/config.json`** — append `{"filePath": ".variations\\<ENTITY>_<NAME>.json", "dataVariationType": "Entity"}` to `dataVariationFileInfo` (create `{"dataVariationFileInfo": [...]}` when absent).
3. **`project.json`** — the case's `fileInfoCollection` entry gets `"dataVariationFilePath": ".variations\\<ENTITY>_<NAME>.json"`, after `testCaseId` (Studio's order).
4. **Test case argument**, typed as the entity, no default:
   - XAML: `<x:Property Name="<ARG>" Type="InArgument(local:<ENTITY>)" />` with `xmlns:local="clr-namespace:<NAMESPACE>;assembly=DataService.<NAMESPACE>"`, namespace import `UiPath.DataService.Definition` and `<NAMESPACE>`, assembly references `UiPath.DataService.Definition` and `DataService.<NAMESPACE>`.
   - Coded: `[TestCase] public void Execute(<NAMESPACE>.<ENTITY> <ARG>)`.
   - `UiPath.DataService.Activities` is not needed for the data source alone.

**`Filters`** = Base64 of the UTF-8 JSON Studio's Query Builder saves. Written in that form, the builder opens it and saves it unchanged:

```json
{"SelectedFields":null,"Start":0,"Limit":1000,"SortOptions":null,"Expansions":null,"FilterGroup":{"LogicalOperator":0,"QueryFilters":[{"FieldName":"<FIELD>","Operator":"=","Value":"<VALUE>"}],"FilterGroups":[]}}
```

- `LogicalOperator`: `0` = All (AND), `1` = Any (OR). `FilterGroups` nests groups of the same shape. Operators are the Data Service query API's ([query endpoint](https://docs.uipath.com/data-service/automation-cloud/latest/api-guide/query-entity-endpoint)).
- `Limit`: 1000 is the most a run gets; a higher value returns 1000, `0` or unset returns 100. Records beyond the limit are dropped without error.
- `SortOptions`: leave `null`. The builder neither shows nor keeps a sort, and each record runs as its own job. Unsorted records come in `Id` order.
- `Filters` empty → every record of the entity.

**Run-time behaviour:**
- No record matches → Test Manager marks the case Failed without running it ("could not fetch any data"). It runs once a record matches.
- A local `uip rpa run` skips the setup workflow, so the argument is null. Bind one record with `--input-arguments-file <FILE>`, the file holding `{"<ARG>": {"<FIELD>": <VALUE>, ...}}` keyed by field names.

#### One Entity for a Project's Test Data

A test project keeps all its Data Service test data in one entity, one record per data row, with three fields:

| Field | Type | Holds |
|---|---|---|
| Data set | text | name of the data set the row belongs to, unique within the project |
| Row order | number, no decimals | row's position in its data set, from 1 |
| Row | long text (`MULTILINE_TEXT`) | the row as one JSON object of text values, every field of its data set present, an empty value as `""` |

Name the entity after the project and its fields under Data Fabric's naming rules (`uipath-platform`). Do not type the row field `MULTILINE_MAX`: list and query reads return only a preview of it (`uipath-platform`). One entity is one definition, one install and one load, and a data set that gains a field changes no entity; Data Fabric cannot filter on a value inside the row, so criteria on row values run in code after the parse.

- **Data source.** A case's data source filters the entity on its data set's name (`=`); its argument is the entity type.
- **Rows read during a run.** Query Entity Records filters on the data-set field, sorts by the row-order field and pages per the activity's doc; the rows are parsed before use.
- **Parse.** One coded helper per project (a coded source file) turns a record into its values and reads each as text, number, whole number or flag. It is strict, because a silent default hides a data error: an empty or invalid row, a field the row lacks, or a value that does not convert raises an `ArgumentException` naming the calling workflow, the data set, the row order, the field and the raw value — a credential-like field's value left out — with the original exception as `InnerException`. A workflow that receives a record or queries rows parses them at its start, before any step uses a value, so a data error fails there and not later as a bare `FormatException`.
- **Load.** Insert the records from JSON files in batches the record insert accepts, never through a CSV import, which loses text holding line breaks or quotes (`uipath-platform`). Check the load by the record count per data set, read back from the server.

### Data-Driven Testing Best Practices

1. **Separate test data from test logic** — keep data in external sources, not hardcoded in test cases
2. **Include both positive and negative scenarios** — test expected failures too (invalid inputs, boundary values)
3. **Name data fields descriptively** — use field names like `ExpectedResult`, `Scenario` for traceability
4. **Keep data sets small and focused** — each data set should test one concern; avoid combinatorial explosion
5. **Use JSON format** for `.variations/` data files

---

## XAML Test Activities

The `UiPath.Testing.Activities` package provides XAML-specific test activities beyond what the coded `testing` service offers.

### Verification Activities

| Activity | Purpose | Key Properties |
|----------|---------|---------------|
| **VerifyExpression** | Assert a boolean expression is true | `Expression`, `OutputMessageFormat` |
| **VerifyExpressionWithOperator** | Assert two values with a comparison operator | `FirstExpression`, `SecondExpression`, `Operator` |
| **VerifyRange** | Assert a value is within (or not within) inclusive bounds | `Expression`, `LowerLimit`, `UpperLimit`, `VerificationType` |
| **VerifyControlAttribute** | Assert an output of the one UI activity it wraps | `ActivityToTest`, `OutputArgument`, `Operator`, `Expression` |

**Choose by the check**, so the assertion's default message shows the values compared:

| The check | Activity |
|---|---|
| A UI element's value or state against an expected value | VerifyControlAttribute around the activity that reads it: Get Text, Get Attribute, or Check App State's `Exists` for "is shown" — never a read into a variable and a separate assertion |
| Two values: equal, not equal, contains, a regex, greater or less | VerifyExpressionWithOperator |
| A value inside or outside two bounds | VerifyRange |
| Anything else — starts with, does not contain, case-insensitive, several conditions | VerifyExpression, with an `OutputMessageFormat` showing the values |

### VerifyExpressionWithOperator

Compares two expressions using a comparison operator from the `Comparison` enum. Both `FirstExpression` and `SecondExpression` are `InArgument<Object>` — they accept any type; relational comparisons rely on the runtime types implementing `IComparable`.

**Properties:**
- `FirstExpression` — left-hand value (`InArgument<Object>`, the actual)
- `SecondExpression` — right-hand value / expected (`InArgument<Object>`)
- `Operator` — `Comparison` enum. Exact supported values: `Equality`, `Inequality`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `Contains`, `RegexMatch`. Any other identifier (e.g. `StartsWith`, `EndsWith`, `DoesNotContain`, `Matches`) is invalid and rejected at `build` time — `validate` does NOT catch invalid enum values.
- `OutputMessageFormat` — custom format string for the result message; placeholders `{LeftExpression}`, `{LeftExpressionText}`, `{RightExpression}`, `{RightExpressionText}`, `{Result}`, `{Operator}`
- `TakeScreenshotInCaseOfFailingAssertion` (Boolean) — capture screenshot on assertion failure
- `TakeScreenshotInCaseOfSucceedingAssertion` (Boolean) — capture screenshot on success

Authoritative reference: `{projectRoot}/.local/docs/packages/UiPath.Testing.Activities/activities/VerifyExpressionWithOperator.md`. Read the activity doc whenever this skill summary disagrees with it — the activity doc wins.

> **No "starts with" / "ends with" / "does not contain" operators.** For substring containment, use `Contains` (asserts `FirstExpression` contains `SecondExpression`). For prefix/suffix or "does not contain" assertions, use `VerifyExpression` with a boolean C#/VB expression (e.g. `actualValue.StartsWith("foo")`, `Not actualValue.Contains("bar")`). For regex, use `RegexMatch` and pass the pattern in `SecondExpression`.

> **Text operands are compared as patterns, with case.** `Equality` and `Inequality` match `SecondExpression` as a wildcard pattern against the whole text: `*` any characters, `?` one character, `#` one digit, `\` escaping each. An expected value holding `*`, `?` or `#` escapes them (`PO \#123`), or `PO #123` also matches `PO 1123` and not itself. `Equality`, `Inequality` and `Contains` are case-sensitive; `RegexMatch` is too unless the pattern starts with `(?i)`. A case-insensitive check is `RegexMatch` with `(?i)` and the escaped value, or a `VerifyExpression`. `VerifyControlAttribute` compares the same way.

### VerifyControlAttribute

Wraps exactly one UI Automation activity and asserts one of its output properties against an expected value: the read and the check are one activity.

> **Requires UI automation targets.** The wrapped activity inspects live UI elements at runtime. The UIA package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) MUST be read IN FULL first (SKILL.md Rule 7). The agent must configure the wrapped activity's target using `uia-configure-target`. The test case must run against a live application instance.

**Properties:**
- `ActivityToTest` — the one UI activity whose output is asserted (`NGetText`, `NGetAttribute`, `NCheckState`), its target configured via `uia-configure-target`
- `OutputArgument` — the name of that activity's output property (`TextString` for Get Text, `Exists` for Check App State), a plain name, not an expression
- `Operator` — comparison operator from the same `Comparison` enum as `VerifyExpressionWithOperator`
- `Expression` — expected value, a non-generic `InArgument` in element syntax with `x:TypeArguments`
- `TakeScreenshotInCaseOfFailingAssertion` defaults to `True` here, `False` on the other verify activities

Element syntax, validation constraints and example: the activity's own doc (`{projectRoot}/.local/docs/packages/UiPath.Testing.Activities/activities/VerifyControlAttribute.md`), read before authoring.

**Constraints:**
- No verify activity may sit inside `ActivityToTest` — causes validation error
- Windows projects only — hidden in cross-platform projects

### Assertion Results

Each verification activity records one assertion in the test case result. Shared properties and their per-activity defaults: package overview § Shared Assertion Properties.

- **Title and message** — Test Manager stores the assertion's `Message` from `AlternativeVerificationTitle` (else the `DisplayName`) and its `Payload` from `OutputMessageFormat` (else the activity's default sentence, e.g. `Verification failed. The expression '"abc"' was not containing the expression '"z"'.`). Name the check in the title; show the actual values in the format.
- **Screenshots** — `TakeScreenshotInCaseOfFailingAssertion` / `TakeScreenshotInCaseOfSucceedingAssertion` attach a screenshot to that assertion: on Windows the whole desktop, every monitor of the robot's session with every window on it, not the target application; inside a Mobile Automation scope the device screen; on a Linux robot the application of the last UI action. Both are optional (`validate` and `analyze` stay silent when missing); set both explicitly when screenshots are wanted.
- **Screenshot files** — the project settings Testing › Generic `KeepScreenshots` (`True`) and `ScreenshotsPath` keep each screenshot as a file in that folder (empty: the temp folder) and log `Screenshot available: <path>`; otherwise the file is deleted once taken. Every verify activity reads them through hidden arguments of the same names, which Studio writes as `{x:Null}`.
- **Logs** — each verification logs its own `Payload`: `Info` on pass, `Error` on fail. A `Log Message` repeating a verification's result is redundant.
- **Failure** — a check failing with `ContinueOnFailure` `True` (default) marks the case Failed without stopping it, and a local run's verdict does not show it ([debugging.md § Output Format](debugging.md#output-format)).

### Given-When-Then in XAML

The Given-When-Then structure is three nested `<Sequence>` elements — not separate activity types. See [§ XAML Test Case Structure](#xaml-test-case-structure-given-when-then) above for the full XAML patterns and agent workflow.

Place verification activities inside the `"... Then"` Sequence, mid-flow checks excepted ([§ XAML Structure — Test Case Invoking a Workflow](#xaml-structure--test-case-invoking-a-workflow)).

### XAML Test Activity Gotchas

- **BookmarkResumptionHelper** — assert activities require this extension. Studio adds it automatically, but manual XAML construction must include `metadata.RequireExtension<BookmarkResumptionHelper>()` in CacheMetadata
- **VerifyControlAttribute nesting** — cannot nest one inside another
- **Platform restrictions** — `VerifyControlAttribute` and some testing activities are Windows-only and may not work in Portable projects

---

## Execution Templates

Execution templates wrap test cases at runtime with predefined execution conditions. They let you reuse the same test case logic across different environments, configurations, or application states without duplicating test code. Setup, teardown, a timeout and failure capture written in the template apply to every case it wraps.

### When to Use Execution Templates

- Run the same test case against **multiple environments** (dev, staging, prod)
- Apply **different browser/application configurations** per run
- Set up **common preconditions** (login, navigation) shared across many test cases
- Override **argument values** at runtime without modifying the test case
- Apply a **timeout, failure capture or teardown** (closing the application) to every case

### How Execution Templates Work

1. Create an execution template: right-click the **Templates** folder → **Add → Execution Template**. On disk it is a workflow in `.templates\` holding one `ui:Placeholder` ([§ Execution Template Placeholder](#xaml-structure--execution-template-placeholder)), registered as an `ExecutionTemplate` entry; each case it wraps names it with `executionTemplatePath` and `executionTemplateType` `"Local"` ([§ project.json Registration](#projectjson-registration)). A case whose entry names no template runs bare.
2. Define variables and arguments in the template that match names in the test case
3. At runtime, Studio **merges** the test case and template into a temporary file:
   - Arguments with matching names are **linked** — template values override test case defaults
   - Variables with matching names are **linked** — template values take precedence
   - Non-overlapping arguments/variables from both files are included as-is
4. `uip rpa pack` writes `.generated\<case path>.xaml` for each bound case: the template with its Placeholder replaced by an Invoke Workflow File of the case. These generated files are the package's entry points (each `uniqueId` is the case's `testCaseId`), so Orchestrator and Test Manager runs execute each bound case inside its template. In the generated file only arguments reach the case, by name; a template variable does not — state the template sets up for the cases goes through global variables ([xaml/xaml-editing-catalog.md § Global Variables](xaml/xaml-editing-catalog.md#global-variables)).

### Test Automation Framework

The Official Test Automation Framework template (`uip rpa templates search --query "Test Automation Framework"`) is the starting point for a test project, as the REFramework is for a transactional process; it ships Windows and cross-platform variants in both expression languages. Its execution template runs every bound case inside one root TryCatch:

1. **Try** — a coded initializer loads the project's configuration files into one `Config` dictionary (a global variable), the run's test name is added to it, then a Timeout Scope bounded by the test-timeout setting runs the setup hook and the case.
2. **Catch** — any exception, from the configuration load, the setup hook or the case, is recorded as a failed Verify Expression with its failure screenshot, the finalize step runs with the exception, and the exception is rethrown, so the case fails with evidence.
3. **Finally** — the finalize step runs after a pass. A rethrow from a workflow's root TryCatch skips its Finally ([error-handling-guide.md](error-handling-guide.md) rule 5), which is why the Catch calls the finalize step itself.

The finalize step runs the teardown hook within its own timeout and logs a teardown failure without failing the case. Cleanup such as closing the application goes in the teardown hook, preconditions in the setup hook; a case keeps no failure wrapper and no configuration load of its own.

**Configuration.** Settings and constants are entries with a text value; assets are entries naming an Orchestrator asset or credential asset, read when the case starts. Entry names are unique across the files, and each entry is read by name from `Config` ([xaml/xaml-editing-catalog.md § Global Variables](xaml/xaml-editing-catalog.md#global-variables)). The file formats, the reserved and required entries, and the `example_` entries to remove or replace before a run are in the scaffolded `README.md`; read it and the scaffolded files before changing them.

**After `init`,** check two things and fix what is missing:
- `fileInfoCollection` holds the template's two template entries (`ExecutionTemplate`, `TestCase`) and the sample case bound to the execution template, as the template package's own `project.json` lists them, each case with a fresh `testCaseId` ([§ project.json Registration](#projectjson-registration)).
- Every coded file's namespace is the project's ([coded/operations-guide.md](coded/operations-guide.md)): a coded file in another namespace does not find the project's generated `CodedWorkflow` base class (`CS0246`), which per-file `validate` reports.

### Execution Template Structure

```
MyProject/
├── .templates/
│   ├── StagingEnvironment.xaml       ← sets environment-specific variables
│   └── ProductionEnvironment.xaml    ← different config for prod
├── TestCases/
│   └── TestInvoiceProcessing.xaml    ← generic test, environment-agnostic
└── project.json
```

### Key Rules

1. **Name matching is exact** — argument/variable names in the template must match the test case exactly (case-sensitive) for linking to work
2. **Templates do not execute independently** — they only run when associated with a test case
3. **One template per execution** — a test case runs with one execution template at a time; select it in Test Explorer before running
4. **Template arguments override test case defaults** — use this to inject environment-specific values (URLs, credentials, timeouts)
### What NOT to Do with Execution Templates

- Do NOT put a case's own checks in an execution template — the template's assertion records exceptions only
- Do NOT create templates with arguments that do not match any test case — they will be ignored
- Do NOT rely on execution templates for data-driven testing — use data sources (variations, Data Service, Queues) instead

---

## Mock Testing (XAML Only) — WIP

> **This section is a work in progress.** Full agent support for mock testing requires a CLI command to create mock copies of workflows (e.g., `uip rpa create-mock --file-path <WORKFLOW> --project-dir <DIR>`). Until that command exists, the agent can generate the test case XAML but cannot reliably create mock files programmatically.

Mock testing replaces selected activities or entire invoked workflows with lightweight stand-ins during a test run, isolating the code under test from side effects (database writes, API calls, UI interactions).

> **Coded test cases have no built-in mock framework.** There is no coded equivalent. To isolate dependencies in coded tests, design workflows with injectable parameters or test individual workflows in isolation.

### How Mocking Works

1. The test case's **When** container invokes a **mock copy** instead of the original workflow
2. The mock copy lives at `Mocks/<workflow>_mock.xaml` (mirrors source folder structure)
3. Inside the mock, specific activities are replaced with stand-ins that return predefined values
4. At runtime, mocked activities skip their real logic and return the configured test data

### Test Case with Mock — XAML Structure

```xml
<!-- When container invokes the mock copy instead of the original -->
<Sequence DisplayName="... When">
  <ui:InvokeWorkflowFile
    DisplayName="Main_mock - Invoke Workflow File (Mocks\Main_mock.xaml)"
    WorkflowFileName="Mocks\Main_mock.xaml"
    UnSafe="False">
    <ui:InvokeWorkflowFile.Arguments>
      <scg:Dictionary x:TypeArguments="x:String, Argument" />
    </ui:InvokeWorkflowFile.Arguments>
  </ui:InvokeWorkflowFile>
</Sequence>
```

### Mocks Folder Structure

```
MyProject/
├── Main.xaml                         ← original workflow
├── Mocks/
│   └── Main_mock.xaml                ← mock copy of Main.xaml
├── TestCase.xaml                     ← test case invoking Mocks\Main_mock.xaml
├── TestCaseNoMock.xaml               ← test case invoking Main.xaml directly
└── project.json
```

For workflows in subdirectories, the Mocks folder mirrors the source path:
```
MyProject/
├── Workflows/
│   └── ProcessInvoice.xaml
├── Mocks/
│   └── Workflows/
│       └── ProcessInvoice_mock.xaml
```

### Mock File Behavior

- **Auto-sync:** Changes to the source workflow are applied to the mock file when the project is saved in Studio
- **Edit scope:** In mock files opened in Studio, only mocked activities are editable — non-mocked activities are read-only
- **Multiple mocks:** You can have multiple mock files for the same workflow (different test scenarios)

### What the Agent Cannot Do Yet

1. **Create mock files** — there is no `uip rpa create-mock` CLI command. The mock file must be created via Studio's "Create Test Case" dialog with the **"Mock workflow under test"** checkbox, or manually copied (but Studio manages internal mock metadata that a raw file copy may miss).
2. **Surround with Mock** — wrapping individual activities in mock containers is a Studio GUI action. The agent cannot replicate this in XAML without the internal mock activity schema.

### Constraints

1. **Process projects only** — mocking is NOT available in Test Automation (`Tests`) projects
2. **XAML only** — no mock framework for coded test cases
3. **When container only** — mock invocations go inside the `"... When"` Sequence
4. **No nested mocks** — a mock container cannot be nested inside another mock container
5. **Package dependency** — requires `UiPath.Testing.Activities` installed
