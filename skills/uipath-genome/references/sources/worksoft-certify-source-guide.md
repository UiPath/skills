# Worksoft Certify Source Guide

Framework-specific knowledge for extracting a genome from a Worksoft Certify database export. Follows [source-framework-contract.md](source-framework-contract.md); the pipeline lives in [extraction-guide.md](../extraction-guide.md).

A Certify export is a folder of JSON tables (one file per database table) plus `Manifest.txt`. `Processes.json` routinely reaches tens of megabytes; never read it as text. Run the bundled inventory script first and work from its output:

```bash
python3 <SKILL_DIR>/scripts/certify-export-inventory.py profile "<EXPORT_DIR>" --out "<WORK_DIR>"
python3 <SKILL_DIR>/scripts/certify-export-inventory.py cards   "<EXPORT_DIR>" --out "<WORK_DIR>"
python3 <SKILL_DIR>/scripts/certify-export-inventory.py dump    "<EXPORT_DIR>" "<PROCESS_NAME>"
python3 <SKILL_DIR>/scripts/certify-export-inventory.py targets "<EXPORT_DIR>" --out "<GENOME_DIR>/source"
python3 <SKILL_DIR>/scripts/certify-export-inventory.py data    "<EXPORT_DIR>" --out "<GENOME_DIR>/source"
```

`profile` writes the vocabulary, call graph, roots, root clusters, layouts, and screen map; `cards` writes one compact card per process (objective, inputs, callees, screens, phases, checks, branches); `dump` prints one process step by step in execution order. Read the profile and cards in full; dump only the processes whose card is not enough. `targets` and `data` write the source artifacts every Certify extraction ships with the genome (`certify-targets.json`, `certify-test-data.json`, `certify-process-data.json` plus readable `.md` twins) — see § UI Target Locators and § Test Data.

## Detection

| Signal | Meaning |
|---|---|
| Folder containing `Manifest.txt` with `Certify Version:` plus `Processes.json`, `Layouts.json`, `MapObjects.json`, `Components.json`, `ComponentActions.json` | Worksoft Certify export. Multi-component: a Certify project is a **library of processes**, so the export is a **process genome** whose components are clusters of root processes plus a shared library (see § Component Detection). |
| `Manifest.txt` `Process Count` and the `Processes:` list with folder paths | Scope and folder tree; the same information is in `ProcessFolders.json` |
| `Manifest.txt` `Database:` / `SQL Server:` | Tenant identity for the Source Map; never a Target Application |
| Missing `Manifest.txt` but the JSON tables present | Still an export; take the project name from the top folder in `ProcessFolders.json` and flag `*[Inferred]*` |

Every JSON row omits null-valued keys, so every field read must tolerate absence. Files start with a UTF-8 BOM.

## Inventory and Exclusions

| File | Contents | Use |
|---|---|---|
| `Processes.json` | Processes with nested `TestSteps[]`, each with `TestStepActions[]` (parameters) and `TestStepResults[]` (branching) | Steps, control flow, call graph, data |
| `ProcessFolders.json` | Folder tree (`ChildFolders` recursive) | Scope: Transaction / Utility / Integration / Sandbox / OutOfScope folders |
| `Components.json`, `ComponentActions.json`, `ComponentActionParms.json` | The action vocabulary: component (control type) → actions → parameters | Translate every step to behaviour |
| `Layouts.json`, `Variables.json`, `Recordsets.json`, `RecordsetFilters.json` | Data-driving: layout = variable schema, recordset = rows of values | Interface, Configuration Questions, data-driven variants; **test data artifact** (§ Test Data) |
| `MapObjects.json` | Application map: windows (`Name`, `PhysicalName`) with `ChildTrackObjects[]` controls, each carrying a Certify locator in `ObjectIdParmValues[].CertifyValue` | Target Applications, screen names for Source Map; **UI target catalog** (§ UI Target Locators) |
| `Applications.json`, `InterfaceLibraries.json` | Applications under test and the technology libraries (Web, Silverlight, System) | Target Applications |
| `Attributes.json` | Custom attributes (e.g. Process Type: Process / Sub-Process) | Rarely populated; do not rely on it for root detection |
| `Users.json` | Author accounts | Source Map only; never in the genome body |
| `Requirements*.json`, `Groups.json`, `ExceptionHandlers.json`, `DataTypeMasks.json` | Usually empty | Skip when empty |

Excluded from logic: metadata keys `UniqueKey`, `CreatedDt`, `CreatedBy`, `ModifiedDt`, `ModifiedBy`, `EF6State`; steps with `Skip: true`; `Execution.Wait` and `Operating System.Capture Screen Image` steps (timing and evidence capture, not behaviour); processes in personal sandbox folders unless a root outside the sandbox calls them.

## Component Detection

Certify has one artifact type, the process. Components come from the **call graph**, not from file types:

| Construct | Component type | Skill | Rationale |
|---|---|---|---|
| Processes called by other processes (sub-processes: login, proxy, create position, post job, …) | Shared **UI library** | `uipath-rpa` (Library project, one workflow per sub-process) | Reusable UI sequences invoked by many scenarios |
| Root processes (called by nobody) that share one ordered callee signature and differ only by recordset | One **data-driven test case** with a data table | `uipath-rpa` (Test project) | Same behaviour, different data |
| Root processes with distinct callee signatures in one business area | One **test project** with one test case per root | `uipath-rpa` (Test project) | Regression scenarios of one domain |
| Root leaf processes (call nothing, called by nobody) outside sandbox | Candidate orphans | Source Map note; include in the library only when their name matches a scenario need | Usually superseded copies |
| `OutOfScope`, `Sandbox`, personal-name folders | Excluded | Source Map inventory only | Team convention for retired or in-progress work |

Process **status** (`ProcessStatusID`) distinguishes approved from in-progress work in the customer's convention; report the distribution and flag the meaning `*[Inferred]*` unless the customer confirms it.

Test execution and reporting of the resulting UiPath test projects belongs to `uipath-test` (Platform Dependencies), not to Build With.

## Signals — Process

| Signal | Path | Tells you | Example |
|---|---|---|---|
| `Name`, `ProcessFolderID` | process | Identity and scope folder | `Hire_To_Term_Non_Production_Employee_US` |
| `Description` | process | Author-written **Objective / Process Called / Main Layout / Main Recordset / Input Variables / Output Variables** sections separated by `*****` rules | Primary source for Overview and Interface; verify against the steps |
| `LayoutID`, `RecordSetID`, `RecordSetMode` | process | The process is data-driven by that layout's variables and that recordset's rows | Interface inputs; Configuration Question defaults |
| `ProcessStatusID` | process | Lifecycle status (customer convention) | 3 = approved, 1 = in development `*[Inferred]*` |
| `ResultLogStatusID`, `StatusTimeStamp` | process | Last execution result and when | Evidence of liveness; Source Map |
| `TestSteps[].CertifySequence` | step | **Execution order.** The array is in creation order, not execution order; sort by `CertifySequence` (missing = 0) then `TestStepID` | |
| `TestSteps[].Skip` | step | Step disabled; exclude | |
| `TestSteps[].ComponentActionID` → `ComponentActions.Name` + `Components.LogicalName` | step | What the step does: `EditBox.Input`, `PushButton.Press`, `Table.Find Row`, `Execution.Execute Process`, `Text.Compare`, `Variable.Set` | |
| `TestSteps[].ObjectID` → `MapObjects` window / control | step | Which screen and control the step touches | `Terminate Employee / Primary Reason` |
| `TestSteps[].Narrative` | step | Certify's generated sentence for the step | Fast reading aid; never copy into the genome |
| `TestStepActions[].ComponentActionParmsID` → parm `Name`, `CertifyValue` | action | Parameter values: literals or variable references | `Value='Awaiting Action'` |
| `TestStepActions[].VariableID` | action | Parameter bound to a variable (input) or the variable a `Store`/`Set`/`Math` result goes to (output) | |
| `TestStepActions[].ExecProcessID`, `ExecLayoutID`, `ExecRecordSetID` | action of `Execution.Execute Process` | **Call-graph edge** and the data passed (layout + recordset, `RecordSetMode` Read Only, `RecordSetFilter`) | The `Process` parm text is a folder path and may not match a process name; use the ID |
| `TestStepResults[]` (`Name` True/False, `ResultLogStatusID`, `ExecutionStatusID`, `ExecTestStepID`) | step | **Control flow.** `ExecutionStatusID` 1 = continue; 5 = jump to the `Execution.Label` step named in `ExecTestStepID`; 6 = stop `*[Inferred]*`. `ResultLogStatusID` 2 = pass, 1 = fail, 4 = not logged (a silent decision, not a defect) | `False(log4)→exec5:Skip Close Tour` |

### Step vocabulary → behaviour

| Action (component.action) | Genome wording |
|---|---|
| `Execution.Execute Process` | Invoke sub-process (call-graph edge; in a UiPath library, invoke workflow) |
| `Execution.Comment`, `Execution.Label` | Phase headings and branch targets; comments are the author's section names — use them to name substeps |
| `EditBox.Input`, `EditBox.Type Keys`, `EditBox.Input Autocomplete`, `PasswordBox.Input` | Enter {value} into {field}; autocomplete = pick the matching suggestion |
| `PushButton.Press` / `Send Click`, `Link.Press` / `Send Click`, `Cell.Send Click`, `Page.Click` | Click {control} |
| `ListBox.Select`, `DropDown.Select`, `Tree.Select Node`, `CheckBox.Set`, `RadioButton.Press` | Choose {item}; tick/untick; pick tree path (`A|B` = menu path) |
| `Table.Find Row`, `Table.Find Row (Advanced)`, `Table.Select Row`, `Table.Select Cell`, `Table.Store Cell`, `Table.Input Into Cell`, `Table.Verify Cell` | Locate the row whose cells match {values}; read or act on that row |
| `*.Visible` (with `Timeout`) | Wait up to N seconds for {control}; a False branch means "if absent, skip to …" |
| `*.Verify`, `Text.Compare`, `Cell.Verify Property` | Assertion → Acceptance Criteria; with a jump → decision → Business Rules |
| `Variable.Set`, `Text.Concatenate`, `Text.Split Text And Extract`, `Text.Text Between`, `Number.Math`, `Number.Get Random Number`, `Date.DateMath` | Data preparation; random values = synthetic test data (names, IDs, emails) |
| `Record Set.Clear RecordSet`, `Import RecordSet`, `Import RecordSet From Excel` | Load test data from a file at run time → Interface input `File Path` |
| `Page.Set Attributes`, `Link.Set Attributes`, `*.Set Attributes` | Parameterise a screen or control locator at run time (e.g. replace `REPLACEME` with the employee name) → Source Map note only |
| `Browser.Set Input Options`, `Set Busy Check`, `Set Scroll Into View`, `Set Object Context Timeout`, `Set Hidden Check` | Automation-engine settings → Error Handling wording ("waits for the page to settle"); never a step |
| `Window.Send Keys`, `Window.Send Input Key` | Keyboard input to the window (Enter, shortcuts) |
| `Browser.Load Browser`, `Close Browser`, `Close Tab`, `Load URL` | Open/close the browser → session steps |

### Value syntax

Certify values embed variable references: `T[Name]` text, `N[Row_1]` number, `D[Date#1]` date, `D[(System)\Date]` = today; `&`-prefixed and `%` forms do not occur in the JSON export because the binding is carried by `VariableID`. Literal values are the defaults for Configuration Questions. Never copy values from variables named `*Password*`, `*PWD*`, `*Secret*`, `*Token*`; Certify stores them in plain text in `Recordsets.json`.

## Target Resolution

1. `MapObjects[].ApplicationVersionID` → `Applications[].ApplicationVersions[]` → `Applications[].Name` gives the application (e.g. Workday, JIRA_Cloud); `Applications[].Name == "System"` is the automation engine, not a target.
2. `InterfaceLibraries[].Platform` (Web, Silverlight, System) tells the technology; `MapObjects[].PhysicalName` often ends with `_LT` (learned page title).
3. Login URLs live in the login recordset (`Workday_URL`) → Configuration Question "Which environment URL?" with the host only as default.
4. Third-party systems appear as separate applications (a Microsoft sign-in page, a Conga table) → Target Applications rows.

## Call Graph Rules

1. Edge = step with `ComponentActionID` of `Execution.Execute Process` and `TestStepActions[].ExecProcessID` in the export. Order edges by the caller's `CertifySequence`; drop skipped steps.
2. Roots = processes never referenced by an `ExecProcessID`. Leaves = processes with no outgoing edge.
3. Cluster roots by their ordered, de-duplicated callee-name signature. A cluster of size > 1 whose members differ only in recordset is one data-driven test case; record every member's recordset name.
4. The **library** = every process reachable from an in-scope root. Processes only reachable from sandbox or out-of-scope roots stay in the Source Map inventory.
5. Name collisions (same name in Transaction and Sandbox folders, or a `C`-prefixed copy such as `CWorkday_Post_Job` vs `Workday_Post_Job`) are copies; the one reachable from in-scope roots is canonical, the other goes to the Source Map as a duplicate.
6. Recursion via labels (`Start Proxy again`, `Skip to next row`) is a loop inside one process, not a call.

## Expression Translation

Certify has no expression language; conditions are `Text.Compare` / `*.Verify` steps with `Condition` values (`Is Equal To`, `Contains`, `Is Not Empty`, `Starts With`, `Is Empty`) and the True/False result rows decide the jump. Translate the pair as one rule: "If {Value1} {condition} {Value2}, {what the jump skips}; otherwise continue." A `*.Visible` with a False jump reads "If {control} is not shown within N s, skip {label target}."

## Platform Resources

Certify has no queues, assets, or connections. Map:

| Certify | Genome |
|---|---|
| Login recordsets and every `Workday_Username`-style variable (user name + password + URL) | Platform Dependencies → **one credential asset per source account** (`<App>_Login_<USER>`); the account identity and its tenant URL migrate with the data rows, the password never (§ Test Data) |
| Layout + recordset on a root process | Interface inputs; Configuration Questions with the recordset values as defaults; multi-row recordsets = data-driven test data table |
| `Import RecordSet From Excel` / `Import RecordSet` file paths | Interface input `File Path`; Configuration Question for the data file location |
| Result logs (`ResultLogStatusID`, `StatusTimeStamp`) | Deployment → test reporting via `uipath-test` |

## UI Target Locators

Certify learned every control; the recognition data is in `MapObjects.json` → `ChildTrackObjects[].ObjectIdParmValues[].CertifyValue` as XML: `<tagname>`, `<instance>`, `<frame>` and a `<findby>` list of `<n>attribute</n><v criteria="…">value</v>` pairs (criteria `isequalto`, `contains`, `startswith`, case varies). Windows carry `title`/`caption`/`url` criteria. `targets` writes the catalog; execution turns it into Object Repository targets per [source-migration-guide.md](../source-migration-guide.md). Translation:

| Certify (any case) | UiPath `webctrl` | Notes |
|---|---|---|
| `tagname` | `tag` | upper-case |
| `instance` > 1 | `idx` | positional; keep strict, never anchored; analyzer flags large indexes |
| `data-automation-id` | `data-automation-id` | Workday's developer identifier — high confidence |
| `parentElement.data-automation-id` | preceding `<webctrl data-automation-id=…/>` tag | two-level selector |
| `id`, `name`, `aria-label`, `type`, `title`, `href`, `alt`, `placeholder` | same attribute | skip numeric or hash-like ids |
| `role` | `aria-role` | |
| `classname` | `class` | wildcard both sides |
| `innertext`, `normalizedinnertext`, `text`, `alltext`, `outertext` | `innertext` | never the primary identifier of a text field; move to the anchor for TypeInto/GetText |
| `label`, `LeftTextAnchor`, `RightTextAnchor` | **anchor** on the visible label (`aaname`) and the semantic text | Certify's label is the associated caption, not an attribute of the control; skip numeric/one-character labels |
| `isdisplayed`, `IsVisible`, `ControlType`, `value`, `innerhtml`, `outerHTML`, `XPath` | none | `innerhtml startswith <button` means the real control is a child button (trailing `BUTTON` tag); XPath/outerHTML go to the semantic text only |
| window `title`/`caption` startswith / contains, `url` contains | `<html app='chrome.exe' title='X*' />`, `title='*X*'`, `url='*X*'` | the common window's caption is rewritten at run time by `Page.Set Attributes` (e.g. `Workday_Common` → `Workday`) |
| `Set Attributes` with `REPLACEME`/`replaceme` | selector variable `{{Argument}}` | the process substitutes a person name, job title or requisition title at run time |

Windows exist under duplicate names (two `View Worker`, two `Sign in to your account` for different apps); resolve by the control's own parent. Controls with no locator (Windows file dialog) become semantic-only targets.

## Test Data

`Layouts.json` is the schema (`LayoutVariables[]` ordered by `CertifySequence`, names via `Variables.json`), `Recordsets.json` the rows: `RecordSetDatas[]` cells keyed by `LayoutVariablesID`; a multi-row recordset repeats each variable's cell in row order. `data` decodes both into named rows plus the process → layout/recordset links (roots hold the data; wrapper roots with a `File Path` layout delegate to the inner process). Rules:

1. Recordset names duplicate (two `NonProduction`, two `HR - I - 1437 …`, one of each empty): pick the copy with rows, or by id.
2. `Workday_Username`, `Workday_Password`, `Workday_URL` (and any `*Password*`/`*PWD*`) are credentials: the user name becomes the credential asset name and, through the login recordset (`UTL_Workday_Login`: user → tenant URL), the environment URL of the row; the password is never copied. Scenarios sign in as different accounts on different tenants — keep that per row.
3. `^` means "not provided"; `Org (Manager)` strings carry two values; `On`/`Off` are booleans; dates are the values of the last recorded run and go stale.
4. Multi-row recordsets carry `ToBeExecuted` per row; the source flags win over any generated pattern.
5. Certify quirks are carried over and flagged, not silently corrected (manager typed into an organisation prompt, hourly rate in a salary column, malformed amounts).

## Framework Pitfalls

1. `TestSteps` is not in execution order; sort by `CertifySequence`.
2. The `Process` parameter of Execute Process holds a folder path (often stale, e.g. pointing at a Sandbox path while `ExecProcessID` resolves to the Transaction copy); trust `ExecProcessID`.
3. Roots are not marked; the `Process Type` attribute is unreliable (every process may be "Sub-Process"). Derive roots from the call graph.
4. `Wait` and `Capture Screen Image` are ~30% of all steps; exclude them before counting complexity.
5. `Set Attributes` steps rewrite locators at run time; they explain how one screen object serves many pages, not what the business does.
6. Sandbox folders hold near-duplicates of library processes at different step counts; do not merge their content into the canonical description.
7. `Description` sections drift from the steps (a Canada objective on a US process, a callee list that omits proxies); the steps are the truth.
8. Plaintext credentials in `Recordsets.json`; count them, never copy the passwords, keep the account identity per row (§ Test Data), and tell the user.
9. The `Execute Process` actions of many roots carry no `ExecRecordSetID`; the data-driving recordset is the root's own `RecordSetID`.
