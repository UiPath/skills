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
| Root processes (called by nobody) that share one ordered callee signature and differ only by recordset | One **data-driven test case** with a data table, inside the business area's test-case group | `uipath-rpa` (folder of the single test project) | Same behaviour, different data |
| Root processes with distinct callee signatures in one business area | One **test-case group** (component) with one test case per root | `uipath-rpa` (folder of the single test project) | Regression scenarios of one domain |
| All test-case groups of the export together | One **test project** `<ProcessName>.Tests` with one folder per group and a shared `Config/` workflow | `uipath-rpa` (Test project) | One library dependency, one configuration, one set of asset names; documented in the process genome's Project layout table, never as one project per group |
| Root leaf processes (call nothing, called by nobody) outside sandbox | Candidate orphans | Source Map note; include in the library only when their name matches a scenario need | Usually superseded copies |
| `OutOfScope`, `Sandbox`, personal-name folders | Excluded | Source Map inventory only | Team convention for retired or in-progress work |

Process **status** (`ProcessStatusID`) distinguishes approved from in-progress work in the customer's convention; report the distribution and flag the meaning `*[Inferred]*` unless the customer confirms it.

Test execution and reporting of the resulting test project belongs to `uipath-test` (Platform Dependencies, one test set per folder), not to Build With.

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
| `EditBox.Input` (Key = None), `PasswordBox.Input` | Enter {value} into {field} |
| `EditBox.Input` (Key = `{ENTER}` / `{TAB}`), `EditBox.Input Autocomplete`, `EditBox.Type Keys` | **Composite** — type-ahead pick or type-and-confirm; wording per § Composite actions |
| `PushButton.Press` / `Send Click`, `Link.Press` / `Send Click`, `Cell.Send Click`, `htmlHeader.Send Click` | Click {control} (`Ver`/`Hor` are click offsets in %, ignore unless far from 50/50) |
| `Page.Click`, `Window.Mouse Click At`, `Active Window Actions.Click Object` | **Composite** — click without a mapped control; wording per § Composite actions |
| `CheckBox.Set` (`State` On/Off), `RadioButton.Press` | Ensure {box} is ticked/unticked (state, not toggle); select {option} |
| `ListBox.Select`, `ListBox.Select Item`, `DropDown.Select`, `DropDown.Send Click`, `ComboBox.[Select]`, `Tree.Select Node` | **Composite** — option list or menu path; wording per § Composite actions |
| `Table.Find Row`, `Table.Find Row (Advanced)`, `Table.[Find Row]`, `Table.Select Row`, `Table.Select Cell`, `Table.Store Cell`, `Table.Input Into Cell`, `Table.Verify Cell`, `Table.Store Property` | **Composite** — table row by content, table cell, read cell; wording per § Composite actions |
| `*.Visible` (with `Timeout`) | Wait up to N seconds for {control}; a False branch means "if absent, skip to …" |
| `*.Verify`, `Text.Compare`, `Cell.Verify Property` | Assertion → Acceptance Criteria; with a jump → decision → Business Rules |
| `Variable.Set`, `Text.Concatenate`, `Text.Split Text And Extract`, `Text.Text Between`, `Number.Math`, `Number.Get Random Number`, `Date.DateMath` | Data preparation; random values = synthetic test data (names, IDs, emails) |
| `Record Set.Clear RecordSet`, `Import RecordSet`, `Import RecordSet From Excel` | Load test data from a file at run time → Interface input `File Path` |
| `Page.Set Attributes`, `Link.Set Attributes`, `*.Set Attributes` | Parameterise a screen or control locator at run time (e.g. replace `REPLACEME` with the employee name) → Source Map note only |
| `Browser.Set Busy Check`, `Set Scroll Into View`, `Set Object Context Timeout`, `Set Hidden Check` | Automation-engine settings → Error Handling wording ("waits for the page to settle"); never a step |
| `Browser.Set Input Options` (`Input Type` Send Keys / Set Value) | Input-method hint for the fields that follow (§ Composite actions → keystrokes); never a step |
| `Window.Send Keys`, `Window.Send Input Key`, `Window.[SendVKey]`, `*.Key Press`, `*.Type Keys` | **Composite** — keystrokes to the focused element; wording per § Composite actions |
| `Browser.Load Browser`, `Close Browser`, `Close Tab`, `Load URL` | Open/close the browser → session steps |

### Value syntax

Certify values embed variable references: `T[Name]` text, `N[Row_1]` number, `D[Date#1]` date, `D[(System)\Date]` = today; `&`-prefixed and `%` forms do not occur in the JSON export because the binding is carried by `VariableID`. Literal values are the defaults for Configuration Questions. Never copy values from variables named `*Password*`, `*PWD*`, `*Secret*`, `*Token*`; Certify stores them in plain text in `Recordsets.json`.

### Composite actions (no single UiPath equivalent)

A Certify step is one row, but several actions bundle a multi-step interaction into their parameters: type *and* pick a suggestion, open a menu *and* walk a path, find a row *and* act on it, send keys to *whatever has focus*. The first migration built these naively — type-ahead as "type, then click the first popup entry", custom Workday lists as a native select, a two-level menu as one click — and the result did nothing useful. Two obligations follow:

1. **Extraction writes the full interaction contract into the Workflow substep.** Behavioural wording only, but complete: what is typed, how the suggestion is matched, which key confirms, the path levels, the row rule. "Enter Voluntary into Primary Reason" is a data loss; "type Voluntary into Primary Reason and pick the suggestion that equals Voluntary" is the step. The parameters below are what the wording must carry. The `targets` script records every action applied to each control (`actions` per control) so execution can see the contract next to the locator.
2. **Execution builds the pattern named in the last column** ([source-migration-guide.md § Composite interactions](../source-migration-guide.md)), never the nearest single activity. The map holds only the anchor control (the input, the menu root, the table); the popup entries, menu items, and option rows Certify clicked are **not map objects** and must be derived.

| Action | Parameters that define the interaction | Workflow substep wording | Pattern |
|---|---|---|---|
| `EditBox.Input Autocomplete` | `Typed Value`; `List Item Caption` + `List Item Caption Criteria` (Contains / Is Equal To; caption absent = match the typed value); `List Item Number` / `List Item Instance` (nth match); `Selection Type` (Left-click); `Follow-Up Key` | "Type {Typed Value} into {field}; in the suggestions pick the entry whose text {contains/equals} {caption} ({n}th match); press {Follow-Up Key}". Workday global search: caption `Task` is the suggestion's category label, so the wording is "pick the suggestion of type Task" | Type-ahead pick |
| `EditBox.Input` with `Key` = `{ENTER}` / `{TAB}` on a prompt field (Workday `responsiveMonikerInput`, `promptInput`), `Table.Input Into Cell` with `Follow-up Keystroke` `{ENTER}` on a prompt cell (Country, ID Type) | `Value`, `Key` | "Type {value} into {field} and confirm with Enter — the prompt accepts the matching entry". On a plain text box the same action is "enter {value} and press Enter/Tab" | Type-ahead pick (keyboard confirm) / plain type |
| `Tree.Select Node` | `NodePath` `A\|B` (Workday Related Actions fly-out: `Job Change\|Terminate Employee`), `ClickType`; second signature `Node Path`, `UseNodeText` (desktop tree) | "Open {menu} and follow Job Change > Terminate Employee" — one substep per level when levels reveal one another | Menu / tree path |
| `ListBox.Select`, `ListBox.Select Item`, `DropDown.Select`, `ComboBox.[Select]` | `Item` + `Criteria` (Is Equal To / Contains / Starts With); `Index` (usually repeats `Item`; a number is a position); `Instance`; `CaseSensitive` | "Choose the option {criteria} {Item} in {list}" ("the first option starting with Hire" when the index is positional) | Option list |
| `DropDown.Send Click` followed by `ListBox.Select` / `Active Window Actions.Click Object` | click, then a pick | One substep: "open {dropdown} and choose {item}" | Option list |
| `Active Window Actions.Click Object` | `ControlType` (ListItem), `Name` + `Name Criteria`, `Instance` | "Pick the list entry named {Name}" — Certify searched the active window by accessible name; no control in the map | Option list (popup by accessible name) |
| `Table.Find Row`, `Table.Find Row (Advanced)`, `Table.[Find Row]` | `Row Matching String 1..n` (any cell) or `Match Value n` + `Column Caption n` / `Column Number n` + `Match Criteria n`; `Matching Row Instance` (`1`, `Last`); `Variable` = row index consumed by later steps | "Locate the row of {table} whose {column} {criteria} {value} [and …]" — then every later step with `Row Number` = that variable acts **on that row**, never on a stored number. Tables named `activeListContainer*` are Workday prompt/suggestion popups: Find Row + Select Row there is an option pick and is worded as one | Table row by content |
| `Table.Select Row`, `Table.Select Cell` | `Row Number` (literal, variable, `Last`), `Column Caption` / `Column Number`, `Click Type` (Single / Double), `Follow-up Keystroke` | "Click (double-click) the {column} cell of {row rule}" | Table cell |
| `Table.Input Into Cell` | `Input Type` (Input Text / Set CheckBox / dropdown), `Value`, `Column Caption` / `Column Number`, `Row Number`, `Follow-up Keystroke` | "In the {column} cell of {row rule} enter {value} [and confirm with Enter] / tick the box" | Table cell (+ type-ahead pick when the cell is a prompt) |
| `Table.Store Cell`, `Table.Verify Cell`, `Cell.Store`, `Link.Store`, `Table.Store Property` (`rows.Length`) | `Column Caption` / `Column Number`, `Row Number`, `Store Type` / `Verify Type` (Cell Text), `Property` | "Read the {column} cell of {row rule} into {output}" / "count the rows of {table}" / "read the text of {control}" | Read table cell / row count |
| `Window.Send Keys` (`Caption`, `Keys`), `Window.Send Input Key` (`Key` + Ctrl/Shift/Alt/Win flags), `Window.[SendVKey]`, `*.Key Press`, `*.Type Keys` | key string (translation table below) | The keys go to **whatever has focus after the previous step**. Fold them into that step: a value typed right after a click on a date field is "enter {date} into {field}"; `{ENTER}` after a type is its confirm key; `{PgDn}`/`{PgUp}`/`{Home}`/`{End}` exist only to scroll the next target into view — drop them, UiPath scrolls on its own; `{F5}` is "refresh the page"; `^+{Delete}` in Chrome is "open Clear browsing data" | Keystrokes |
| `Page.Click` (`Click Type`), `Window.Mouse Click At` (`X`, `Y`) | none / screen coordinates | "Click {what the surrounding steps show is being clicked}" — usually dismissing a popup or focusing the page; flag `*[Inferred]*` | Coordinate click |
| `Browser.Set Input Options` `Input Type` = Send Keys | applies until the next Set Input Options | Not a step. The fields that follow need real key events (type-ahead, key handlers); carry "typed with key events" into the substep so execution does not use set-value input for them | Input-method hint |

Certify key tokens (SendKeys convention): `{ENTER}` / `{Enter}` / `(ENTER)` = Enter; `{TAB}` = Tab; `{PgDn n}` / `PageDown` = Page Down n times; `{PgUp}`, `{Home}`, `{End}`, `{F5}`; `{BACKSPACE}` = Backspace; `{Delete}` = Delete; `(DOWN)` = Down arrow; `{A}` = the letter; prefixes `^` = Ctrl, `+` = Shift, `%` = Alt; `Send Input Key` carries the modifiers as booleans. The genome says the key names; execution encodes them in the owning skill's key syntax.

Workday specifics worth knowing while reading: `responsiveMonikerInput` / `promptInput` controls are type-ahead prompts (every "Input + Enter" on them is a pick); `relatedActionsList` is the Related Actions fly-out menu (a tree with hover-revealed levels); `activeListContainer` is the suggestion popup rendered as a table; `Menu List`, `Item List`, `Archive` are custom list widgets, not native selects.

## Target Resolution

1. `MapObjects[].ApplicationVersionID` → `Applications[].ApplicationVersions[]` → `Applications[].Name` gives the application (e.g. Workday, JIRA_Cloud); `Applications[].Name == "System"` is the automation engine, not a target.
2. `InterfaceLibraries[].Platform` (Web, SAP, Silverlight, UIA, Java, NetUI, Office, Mainframe, System, Utilities) lists the engines an application version was learned with, but the **locator format** of each map object decides its UiPath technology — the library called Silverlight is Certify's UI Automation desktop engine, and one application mixes web pages, SAP GUI screens and Windows dialogs ([worksoft-certify-selectors-guide.md](worksoft-certify-selectors-guide.md)). `MapObjects[].PhysicalName` often ends with `_LT` (learned page title).
3. The browser is the `Browser` parameter of the process's `Browser.Load Browser` step (`Chrome`, `Edge`, `Internet Explorer`) → Configuration Question "Which browser runs the automation?" with that value as default; SAP GUI sessions come from `Window.Launch SAP`.
4. Login URLs live in the login recordset (`Workday_URL`) → Configuration Question "Which environment URL?" with the host only as default.
5. Third-party systems appear as separate applications (a Microsoft sign-in page, a Conga table) → Target Applications rows.

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

Certify learned every control; the recognition data is in `MapObjects.json` → windows (`ObjectIdParmValues[].CertifyValue`) and `ChildTrackObjects[].ObjectIdParmValues[].CertifyValue`. One export mixes several locator formats — web XML, an SAP GUI scripting string, UI Automation properties for desktop windows, Java object descriptors, and class-only template objects — and the format, not the application's interface library, decides the UiPath technology. `targets` parses every format into one normalized catalog (`technology`, `class`/`tagname`, `instance`, `findby`, `volatile`, `parentpath`, `anchor`); the per-format attribute translation is [worksoft-certify-selectors-guide.md](worksoft-certify-selectors-guide.md), the UiPath-side vocabulary and rules (criteria → wildcards, captions → anchors, position → strict `idx`, confidence tiers) [selector-translation-guide.md](../selector-translation-guide.md), and execution turns the result into Object Repository targets per [source-migration-guide.md](../source-migration-guide.md).

Each control in the catalog carries `actions`: the Certify actions applied to it with their interaction parameters (`Typed Value`, `List Item Caption`, `NodePath`, `Item`/`Criteria`, `Column Caption`/`Row Number`, `Key`, …; variable-bound values as `T[Name]`). Execution reads them to decide the pattern (§ Composite actions) and to derive the elements Certify never mapped: suggestion entries, menu items, option rows, table cells. Those derived elements have no locator of their own — they are built from the anchor control plus the typed or matched text and start at low confidence. "No locator of their own" is literal: no `id` or `data-automation-id` is carried across from a control that merely looks related (§ Framework Pitfalls 11).

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
10. **One step is not one activity.** `Input Autocomplete`, `Select Node`, `ListBox.Select`, `Find Row` + `Select Row`, `Input Into Cell` and the `Send Keys` family bundle multi-step interactions into parameters (§ Composite actions). Translating them to the nearest single UiPath activity produces workflows that validate and do nothing right: the first attempt clicked the first popup entry instead of the matching one, drove custom lists with a native select action, and collapsed a two-level menu into one click.
11. The map holds only what Certify learned: the input, the menu root, the table. Suggestion entries, menu items, option rows and cells were never learned, so the target catalog cannot cover them; execution derives them from the anchor control and the matched text (§ UI Target Locators). Never source a missing element's identifier by searching the catalog for an attribute whose *name* looks related: nothing ties a neighbour's attribute to the element, and a value occurring once against a pattern several sibling controls share is an outlier, not a convention.
12. `EditBox.Input`'s `Key` parameter is a confirm keystroke, and on a Workday prompt field it is the whole selection mechanism; a wording that drops it drops the pick.
13. `Window.Send Keys` steps carry no control. Roughly half are page scrolling (`{PgDn}`, `{PgUp}`, `{Home}`, `{End}`) that UiPath does not need; the rest belong to the field clicked just before them. Read them in sequence context, never as standalone steps.
