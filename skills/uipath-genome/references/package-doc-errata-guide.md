# Package Doc and Tool Errata — TEMPORARY

The owning skill's contract reads the installed package's per-activity doc for every activity kind a build uses ([execution-guide.md § 2.2](execution-guide.md)). **Precedence.** While the installed doc still says what a row's second column quotes, the row wins, because it was checked against the activity's source and a validate or build. Once the doc carries the corrected text, the doc wins and the row is obsolete. Check the installed doc every run: the version a project pins decides which text it ships.

## `UiPath.System.Activities` — docs shipped with 26.8.2 and earlier

| Activity | Installed doc says | The activity does |
|---|---|---|
| Add Data Row | the example types `ArrayRow` as `<InArgument x:TypeArguments="x:Object[]">` | `x:Object[]` fails to load (`Cannot create unknown type …InArgument(…Object[])`); the type argument is `s:Object[]`, with `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` |
| Append Line | a newline is added after the existing content; `UseDefaultEncoding` `true` ignores `Encoding` | Writes a line break (`Environment.NewLine`) **before** the text whenever the file is not empty, never after it: two appends to a new file give `a`, a line break, `b`, with no trailing break. A file counts as empty at 0 bytes, or when its size equals the resolved encoding's byte-order mark (3 bytes UTF-8, 2 UTF-16). Creating the file, or appending to an empty one, writes the byte-order mark. A set `Encoding` always wins; `UseDefaultEncoding` applies only when `Encoding` is empty, and then writes UTF-8 without a byte-order mark |
| Copy Folder (`CopyFolderX`) | `To` is the destination path of the copy (`To="C:\archive\reports"`) | `To` is an existing folder the source folder is copied **into**: the copy is `<To>\<source folder name>`. Both folders must exist (`Source or destination folder missing.`), and `To` may be neither the parent of `From` nor a folder inside it |
| Delete File (`DeleteFileX`) | a missing file raises nothing | A missing file fails (`The file was not found at the provided path.`): check with Path Exists first when the file may be absent. `FileResource` (`IResource`) is the overload used when `Path` is empty |
| For Each (`ForEach`) | `Values` is an optional `IEnumerable<T>`; the example binds `scg:IEnumerable(x:String)` | `Values` is required and non-generic: `<InArgument x:TypeArguments="sc:IEnumerable">` with `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"`. `T` is the activity's `x:TypeArguments` and types the iterator variable; a generic type on `Values` fails to load. An optional `Condition` (`Activity<bool>`, no `<InArgument>` wrapper) exists and is undocumented |
| Kill Process | `AppliesTo` members `All`, `User`, `Session`, `Desktop` | Members are `All`, `OnlyCurrentUser`, `OnlyCurrentSession`, `OnlyCurrentDesktop`; any other value (`Session`) fails to load the workflow |
| Log Message, Message Box | the example sets `Message` / `Text` (`InArgument<Object>`) as an attribute | An attribute value on an `InArgument<Object>` is compiled as a VB expression. A C# library compiles only C# expressions, so every consumer fails at run time with ``…'VisualBasicValue`1 (…)' requires compilation in order to run``, while the library validates, builds and packs. In a C# project the value goes in element form: `<InArgument x:TypeArguments="x:Object"><CSharpValue x:TypeArguments="x:Object">"text"</CSharpValue></InArgument>` |
| While (`InterruptibleWhile`) | `Condition` is an optional `InArgument<bool>`; the example wraps it in `<InArgument>` | `Condition` is a required `Activity<bool>`: the expression goes directly inside `<ui:InterruptibleWhile.Condition>`. An `<InArgument>` wrapper fails to load, and a missing condition fails validation |
| Do While (`InterruptibleDoWhile`) | no `Condition` row | As While, inside `<ui:InterruptibleDoWhile.Condition>` |

## `UiPath.Excel.Activities` — docs shipped with 3.6.1 and earlier

| Activity | Installed doc says | The activity does |
|---|---|---|
| Read Range Workbook (cross-platform) | nothing on empty cells | An empty cell of a text column comes back as empty text, not as no value. A source that leaves empty cells out of a row (a workflow tool's spreadsheet read) is matched only when the build treats empty text as absent |

## `UiPath.MicrosoftOffice365.Activities` — docs shipped with 3.12.10 and earlier

| Activity | Installed doc says | The activity does |
|---|---|---|
| Get Email List; coded `GetEmails` | nothing on `OrderByDate`, which the default XAML carries (`OrderByDate="NewestFirst"`); the coded doc says `OrderBy.OldestFirst` returns the oldest emails first | Neither applies the order: no value changes the order of the returned emails or which ones `MaxResults` / `maxResults` keeps. To process the oldest email first, retrieve the list and sort it by `ReceivedDateTime` (`Item.ReceivedDateTime` on a coded `IMail`) |
| Get File List, Upload Files | declare the `Result` / `AllResults` variable as `scg:List(umo365fm:O365DriveRemoteItem)` | Both are `OutArgument<O365DriveRemoteItem[]>`: bind a `umo365fm:O365DriveRemoteItem[]` variable. A `List` variable fails to load (`Set property '…Result' threw an exception`) |
| Set Email Categories | `CategoriesToAssign` / `SpecificCategoriesToRemove` only as a VB flat attribute, since an `InArgument` cannot be typed `String[]` | `<InArgument x:TypeArguments="s:String[]">` works in VB and C# projects; only `x:String[]` fails to load |

## Tools — defects seen in builds, until fixed

Each row was met in a build that validated and packed, or in a live search against the application; the third column is what that build did instead. Versions: Flow builder SDK `@uipath/maestro-builder-sdk` 6.15.3, `uip` 1.204.

| Tool | Defect | What the build does |
|---|---|---|
| Flow SDK doc comments | `onError` and managed HTTP name `h.rejoin('<step>')`; no such method exists | Rejoins with `stepToRef` |
| Flow SDK serializer | Two child flows of the same shape, each handing off with `stepToRef`, get the same edge ids: `check`, `compile` and `validate` pass, then `flow debug` and `flow pack` fail with `Cannot read properties of undefined (reading 'get')` | Gives each child flow one call site, or changes one child's shape |
| Flow SDK, in-solution calls | No factory calls a sibling RPA process or Flow of the same solution: `rpaWorkflow()` addresses a deployed process, the sibling's manifest from `registry get --local` declares no arguments and no `output`, only `error`, its node type changes after `solution resources refresh`, and `check` refuses a failure path on the call (`ONERROR_NO_ERROR_PORT`). Seen again on SDK 6.16.2 | Places the call as a node carrying that manifest and the sibling's two process bindings, read after the last resource refresh; declares the process's output arguments as the node's `output`, so a later step reads them by name; and wraps the call in a child flow when it needs a failure path |
| `uip maestro flow validate` (SDK 6.16.2) | Type-checks scripts against a JavaScript library without `String.prototype.replaceAll`: a call on a value it types as text warns `EXPRESSION_DIAGNOSTIC … Property 'replaceAll' does not exist on type 'string'` | Removes the characters with `split(…).join('')`, which gives the same text |
| Flow runtime | A flow or child-flow input named `source` arrives empty, with no diagnostic | Names the input otherwise (`sourceName`) |
| Flow runtime, Data Fabric read | An `in` filter with a list value fails (`valueList[0] … System.String`) | Reads without that filter and narrows the rows in a script step |
| `uip maestro registry prepare` on Windows | Fails with `ENOENT`: the SDK spawns `uip` without a shell, and `uip` is a `.cmd` shim | Writes the bindings file by hand from `uip is connections list --all-folders --output json` |
| `uip maestro flow check` | Warns `RPA_FOLDER_NOT_PATH` on a personal-workspace folder, a valid single-segment path | Reviews and accepts the warning |
| `uip api-workflow run` | Prints `fast-json-patch MODULE_NOT_FOUND` stack traces when the working directory has no `node_modules`; the result is correct | Judges the run by its envelope |
| `uip rpa uia target-anchorable update-definition`, `UiPath.UIAutomation.Activities` 26.10.3 | Rejects `idx` bound to a selector variable at the first call, on every tag (checked on `java` and `webctrl`); 26.10.4 registers it | Probes once per run, before the first element is defined: one `update-definition` with `idx='{{Row}}'` on a seed copy, against the project, the answer recorded in the brief. Where it is rejected, every positional selector variable takes [offline-definition-workarounds-guide.md § Selector variables in number attributes](offline-definition-workarounds-guide.md), with a literal in the variable's place at its first step |
| `uip tm testcases link-package` | Requests a page larger than 100 and fails with HTTP 400 (`Page size cannot be greater than 100`) | Creates each test case and links it with `testcases link-automation`, one by one |
| `uip rpa run` | Prints a Log Message at Fatal as `[Verbose]`; Orchestrator records it as Fatal | Reads a log line's level from the workflow, not from the printed tag |
| UI Automation driver, `UiPath.UIAutomation.Activities` 26.10.4 and earlier | `colName` on a SAP GUI table control's column or cell matches nothing: the search rejects it | Takes the column from `colTooltip`, checked against a live listing, or from `tableCol` |
