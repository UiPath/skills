# XAML Activity Gotchas

Common pitfalls that cause validation errors or runtime failures.

## Container/Scope Requirements

These activities **must** be placed inside a specific parent scope:

| Activity | Required Parent | Package |
|----------|----------------|---------|
| Read Range, Write Range, Read Cell, etc. | `ExcelApplicationScope` or `ExcelApplicationCard` | UiPath.Excel.Activities |
| Click, Type Into, Get Text, Check/Uncheck, etc. | `Use Application/Browser` (`NApplicationCard`) | UiPath.UIAutomation.Activities |
| All Word interop activities | `WordApplicationScope` | UiPath.Word.Activities |
| PivotTableFieldX | `CreatePivotTableX` | UiPath.Excel.Activities |
| InvokeVBA (classic) | `ExcelApplicationScope` or `ExcelApplicationCard` | UiPath.Excel.Activities |
| All Office 365 child activities | `Office365ApplicationScope` | UiPath.MicrosoftOffice365.Activities |
| All GSuite child activities | Corresponding GSuite scope | UiPath.GSuite.Activities |

**Additional parent constraints (warnings, not errors):**

| Activity | Recommended Parent | Notes |
|----------|-------------------|-------|
| ExcelApplicationCard | `ExcelProcessScopeX` | Warning if outside process scope |
| DeleteRowsX | NOT inside `ExcelForEachRowX` | Deleting rows during iteration causes unexpected behavior |

**Nesting restrictions:**

| Activity | Cannot Be Inside | Notes |
|----------|-----------------|-------|
| SequenceX | Another `SequenceX` or `ExcelProcessScopeX` | Validation error |
| VerifyControlAttribute | Another `VerifyControlAttribute` | Validation error |
| InvokeVBAX | Max 20 child `InvokeVBAArgumentX` | Validation error if exceeded |

## Conflicting Property Pairs

Setting both properties in these pairs causes a **validation error**:

| Property A | Property B | Activity |
|-----------|-----------|----------|
| `Password` | `SecurePassword` | ExcelApplicationScope, PDF, Mail activities |
| `EditPassword` | `SecureEditPassword` | ExcelApplicationScope |
| `SimulateClick` | `SendWindowMessages` | Click, ExtractData (UIAutomation) |

Only set one from each pair, never both.

## OverloadGroup Patterns (Mutually Exclusive Properties)

Many activities use `[OverloadGroup]` to define mutually exclusive property sets. Setting properties from more than one group causes a **validation error**.

| Activity | Group A | Group B | Group C |
|----------|---------|---------|---------|
| LookupDataTable | `LookupColumnIndex` | `LookupColumnName` | `LookupDataColumn` |
| ExchangeScope | `Server` (manual) | `EmailAutodiscover` | `ExistingExchangeService` |
| ReadCsvFile, AppendWriteCsvFile | `FilePath` (string) | `PathResource` (ILocalResource) | — |
| CopyFile, Delete, ExtractFiles | `Path` (string) | `PathResource` / `File` (IResource) | — |
| WorkbookActivityBase | `Workbook` (use open) | `WorkbookPath` (file string) | `WorkbookPathResource` (IResource) |
| WordDocumentActivity | `FilePath` (string) | `PathResource` (ILocalResource) | — |

**Key rule**: Exactly ONE group must have values. Setting properties from multiple groups OR no groups both cause validation errors.

## Conditional Property Requirements

Some properties are only required when another property has a specific value:

| Activity | Condition | Required Property |
|----------|-----------|-------------------|
| ExcelApplicationCard | `SensitivityOperation = Add` | `SensitivityLabel` must be set |
| WordApplicationScope | `SensitivityOperation = Add` | `SensitivityLabel` must be set |
| DeleteRowsX | `DeleteRowsOption = Specific` | `RowPositions` must be set with valid format (e.g. "1,3,5-7") |
| FilterX | `ClearFilter = false` | `FilterArgument` and `ColumnName` must be set |
| WordInsertHyperlink | `InsertRelativeTo = Text` | `TextToSearchFor` must be set |
| ExchangeScope (Interactive auth) | `AuthenticationMode = Interactive` | `ApplicationId` must be set |
| ExchangeScope | `ApplicationId` is set | `DirectoryId` must also be set (and vice versa — both or neither) |
| WordApplicationScope | `CreateNewFile = true` | Path must be local (not a URL) |

## Input Method Constraints (UIAutomation)

- `SimulateClick` cannot be used with `ClickType=Double` or `MouseButton=Right/Middle` — validation error
- `TypeInto` with `SimulateType=True` **cannot use special keys** (Ctrl, Alt, Shift, etc.) — validation error via `SpecialKeyHelper.IsSpecialKeyUsed()`
- `SimulateClick=True` AND `SendWindowMessages=True` is always invalid — pick one or neither
- Input method resolution: `SendWindowMessages` → WINDOW_MESSAGES; else `SimulateClick` → API; else → HARDWARE_EVENTS (physical)
- These are validated both at design-time (CacheMetadata) and runtime

## NKeyboardShortcuts: `Shortcuts` vs `ShortcutsArgument`

`NKeyboardShortcuts` has **two** shortcut properties — using the wrong one causes VB bracket parsing failures:

- **`Shortcuts`** (`string`) — **Always use this** for hotkey encoding like `[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]`. Brackets are literal text.
- **`ShortcutsArgument`** (`InArgument<string>`) — Only for dynamic/variable-driven values. Brackets here are parsed as VB expressions, so `[d(hk)]` would fail (VB tries to call function `d(hk)`).

**Wrong:** `ShortcutsArgument="[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]"` → VB parser error
**Correct:** `Shortcuts="[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]"` → literal string, works fine

See `ui-automation.md` NKeyboardShortcuts section for the full hotkey encoding reference.

## ActivityAction/ActivityFunc Initialization

Scope activities (like `ExcelApplicationCard`, `Use Application/Browser`) use `ActivityAction` to wrap their child content. The XAML pattern is:

```xml
<scope:ScopeActivity>
  <scope:ScopeActivity.Body>
    <ActivityAction x:TypeArguments="scope:ScopeType">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="scope:ScopeType" Name="ScopeName" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- Child activities here -->
      </Sequence>
    </ActivityAction>
  </scope:ScopeActivity.Body>
</scope:ScopeActivity>
```

**Critical**: The `DelegateInArgument` must match the `x:TypeArguments` of the `ActivityAction`. Missing or mismatched types cause validation errors.

**DelegateInArgument names must be valid identifiers** — validated in CacheMetadata.

**Scope activities and their Body types:**

| Scope Activity | Body Type | DelegateInArgument Type | Default Name |
|---------------|-----------|------------------------|--------------|
| ExcelApplicationCard | `ActivityAction<IWorkbookQuickHandle>` | `IWorkbookQuickHandle` | `"Excel"` |
| ExcelProcessScopeX | `ActivityAction<IExcelProcess>` | `IExcelProcess` | `"ExcelProcessScopeTag"` |
| WordApplicationScope | `ActivityAction<WordDocument>` | `WordDocument` | `"WordDocumentScope"` |
| ExcelForEachRowX | `ActivityAction<CurrentRowQuickHandle, int>` | TWO args: row + index | `"CurrentRow"`, `"CurrentIndex"` |
| ForEachSheetX | `ActivityAction<...>` | Sheet handle | — |

**ExcelForEachRowX special case**: Has TWO delegate arguments (row and index), not one. Both must be initialized.

## ForEach/Iterator Gotchas

- **ForEach body variable scoping**: Variables modified inside a ForEach body don't persist after the loop exits. The DelegateInArgument is scoped to each iteration.
- **ForEachRow**: DelegateInArgument name must be a valid C#/VB identifier — CacheMetadata validates this.
- **DeleteRowsX inside ExcelForEachRowX**: Attempting to delete the current row during iteration throws a runtime error ("Cannot delete current row").

## InvokeWorkflow Gotchas

- **Auto-appends .xaml**: If the `WorkflowFileName` has no file extension, `.xaml` is appended automatically. Passing `"workflow.txt"` becomes `"workflow.txt.xaml"`.
- **TargetSession validation**: `TargetSession.Secondary` (or any non-Current value) requires `UnSafe=True`. Without it, validation fails.
- **Persistence with isolation**: Using `ResumeInstanceId` with Safe mode (`UnSafe=false`) without persistence support throws `NotSupportedException`.

## HTTP Request Activity Complexity

The HTTP Request activity (`NetHttpRequest`) has extensive configuration:

- **Authentication modes** (each requires different properties):
  - `None`: No fields needed
  - `Basic`: `BasicAuthUsername` required + either `BasicAuthPassword` OR `BasicAuthSecurePassword`
  - `OAuth`: `OAuthToken` required
  - `Negotiated`: OS or custom credentials
- **Request body types**: None, FormData, Text, Binary, FormDataParts, File — each uses different properties
- **ContinueOnError defaults to TRUE** — unusual compared to other activities. HTTP failures don't stop execution by default.
- **Retry policies**: Complex interaction between `RetryPolicyType`, `RetryCount`, `PreferRetryAfterValue`, and `MaxRetryAfterDelay`
- **Default timeout**: 10,000ms (10 seconds)

## Connection Service Pattern (Office 365, GSuite, IS Connectors)

- `ConnectionId` is marked `[Browsable(false)]` — it won't appear in the Properties panel, but it is **required** when `UseConnectionService=True`
- `ConnectionId` must be a **literal string** (not a variable expression) for design-time validation to work. Dynamic ConnectionIds bypass validation and may fail at runtime.
- Missing `ConnectionId` when `UseConnectionService=True` → validation error about missing account/connection name
- Child activities expect their parent scope to have initialized OAuth extensions (`IGraphServiceClient`, `OAuthDataOptions`, etc.) — using them without a parent scope causes `NullReferenceException` at runtime

**Connection lifecycle with CLI:**
- **Discover connections**: `uip is connections list [connector-key] --output json` — find existing connection GUIDs
- **Verify connection health**: `uip is connections ping <connection-id>` — check if a connection is still active
- **Create new connection**: `uip is connections create <connector-key>` — opens OAuth flow for user to authenticate
- **Re-authenticate**: `uip is connections edit <connection-id>` — re-runs OAuth flow for expired/revoked connections
- If no connection exists and you cannot create one interactively, use a placeholder GUID (`00000000-0000-0000-0000-000000000000`) and inform the user they must configure the connection in Studio

## Deprecated Activities (Do Not Use)

| Deprecated | Replacement | Notes |
|-----------|-------------|-------|
| Old trigger activities (`ClickTriggerActivity`, `KeyPressTriggerActivity`, etc.) | New trigger framework | Marked `[Browsable(false)]`, kept for backward compat only |
| `ReplayUserEvent` | `ReplayUserEventV2` | Old version still loads but shouldn't be used |
| `UiPath.<Vendor>.IntegrationService.Activities` packages | Generic `ConnectorActivity` via IS | Vendor-specific IS packages are deprecated |

## Default Values That Matter

| Activity | Property | Default | Impact |
|----------|----------|---------|--------|
| ExcelApplicationScope | `AutoSave` | `True` | File is saved automatically on scope exit |
| ExcelApplicationScope | `Visible` | `True` | Excel window is visible during execution |
| ExcelApplicationScope | `CreateNewFile` | `True` | Creates file if it doesn't exist |
| Click | `ClickType` | `Single` | Single click (not double) |
| Click | `MouseButton` | `Left` | Left mouse button |
| Click | `AlterIfDisabled` | `True` | Alters element even if disabled (legacy compat) |
| All UIAutomation activities | `TimeoutMS` | `30000` (30s) | How long to wait for element before timeout |
| UIAutomation | `DelayBefore` | `200`ms | Delay before action |
| UIAutomation | `DelayAfter` | `300`ms | Delay after action |
| ExtractData | `DelayBetweenPagesMS` | `300`ms | Between pagination clicks |
| HTTP Request | `Timeout` | `10000` (10s) | Request timeout |
| HTTP Request | `ContinueOnError` | `True` | Failures don't stop execution (unusual default) |
| HTTP Request | `MaxRedirects` | `3` | Redirect limit |
| WaitQueueItem | `PollTimeMS` | `30000` | Polling interval |
| WaitQueueItem | `Timeout` | `300000` (5min) | Overall wait timeout |
| LogMessage | `Level` | `Info` | Default log level |
| ExcelApplicationScope | `InstanceCachePeriod` | — | Negative values cause validation error |

## Namespace Mapping Gotchas

| What You'd Expect | Actual Namespace | Notes |
|-------------------|-----------------|-------|
| `UiPath.UIAutomation.Activities` | `UiPath.UIAutomationNext.Activities` | Modern UI activities use "Next" namespace |
| `UiPath.UIAutomation.Activities` (classic) | `UiPath.Core.Activities` | Classic UI activities are in Core |

Use `uip rpa get-default-activity-xaml --use-studio` to get correct xmlns declarations — never guess namespace mappings.

## Portable vs Windows Framework Limitations

- Activities in `/Windows/` or `/NetFramework/` source folders are **Windows-only** and won't work in Portable projects
- Some activities are explicitly hidden (`[Browsable(false)]`) when compiled for cross-platform (`XPLAT`)
- Excel encryption activities, some interop-based activities, and `VerifyControlAttribute` (testing) have platform restrictions
- Check `project.json` `targetFramework` before using Windows-only activities

## DataTable Activity Gotchas

- **LookupDataTable column resolution**: When multiple column identifiers are set (shouldn't happen due to OverloadGroups), only the first non-null is used: `LookupColumnIndex ?? LookupColumnName ?? LookupDataColumn`
- **FilterDataTable**: Column must exist AND be type-compatible with the filter operator. Filtering a DateTime column with "Contains" fails at CacheMetadata validation.
- **BuildDataTable**: Uses a security-related allowed types list. DataTables with certain .NET types may fail to serialize/deserialize.
- **GetRowItem**: Must specify at least one of `Column`, `ColumnIndex`, or `ColumnName` — all three empty causes validation error.

## Testing Activity Gotchas

- **VerifyControlAttribute**: Cannot be nested inside another `VerifyControlAttribute` — validation error
- **Assert activities** require `BookmarkResumptionHelper` extension (added via `metadata.RequireExtension<BookmarkResumptionHelper>()` in CacheMetadata)
- **TakeScreenshotInCaseOfSucceedingAssertion** and **TakeScreenshotInCaseOfFailingAssertion** are `[RequiredArgument]` on assert activities even though they default to `false`

## Package Version Changes Break XAML

**The #1 cause of XAML breakage.** When upgrading or downgrading activity packages, XAML serialized with one version may not load with another.

**What happens:**
- Newer packages serialize activities with `Version` attributes the older package doesn't recognize (e.g., `Version="V5"` when max is V4)
- Newer packages add properties that don't exist in older versions (e.g., `HealingAgentBehavior`, `ClipboardMode`)
- Assembly names change between versions (e.g., `Box.V2` → `Box.V2.Core`)

**Error messages:**
- `"Failed to create a 'Version' from the text 'V5'"`
- `"Cannot set unknown member 'UiPath.UIAutomationNext.Activities.NApplicationCard.HealingAgentBehavior'"`
- `"Cannot set unknown member"` for any version-gated attribute

**Fix when editing XAML manually:**
1. Replace old assembly references in `xmlns` declarations (e.g., `assembly=Box.V2` → `assembly=Box.V2.Core`)
2. Remove attributes that don't exist in the target version
3. Cap `Version` attributes to the maximum supported by the target package
4. Add `<AssemblyReference>netstandard</AssemblyReference>` if type resolution errors persist
5. Use `uip rpa get-errors --use-studio` to validate after changes

**Prevention:** When using `uip rpa get-default-activity-xaml --use-studio`, the output matches the currently installed package version. Never copy XAML snippets from projects using different package versions.

## Expression Language Mismatch

Every XAML file must use the same expression language as the project (`expressionLanguage` in `project.json`).

**What happens:**
- Error: `"Main.xaml language 'VisualBasic' is incompatible with project's language 'CSharp'. This configuration is not supported"`
- Copying a VB XAML file into a C# project (or vice versa) causes immediate validation failure

**VB-specific gotchas:**
- `Option Strict On` disallows late binding — `item.Body.ToString` fails without explicit casting
- `Option Strict On` disallows implicit type conversions — `Object` to `DataRow` requires explicit `CType()`
- VB uses `OrElse`/`AndAlso` (short-circuit) vs `Or`/`And` (non-short-circuit) — different behavior in XAML expressions

**C#-specific gotchas:**
- Expressions must use explicit `<CSharpValue>` / `<CSharpReference>` elements inside `<InArgument>` / `<OutArgument>` — do NOT use `[bracket]` shorthand (brackets create VB expression nodes)
- String interpolation (`$"..."`) is NOT supported in XAML expressions — use string concatenation

**Prevention:** Always check `project.json` `expressionLanguage` before writing any expression. Never mix languages.

## Missing Assembly References

Common validation error: `"The type 'Dictionary<,>' is defined in an assembly that is not referenced"`.

**Commonly missing assemblies:**
- `System.Collections` (for `Dictionary<,>`, `List<>`)
- `System.Data` (for `DataTable`, `DataRow`)
- `System.Data.Common` (for `DbConnection`)
- `System.ComponentModel.TypeConverter`
- `System.Net.Mail` (for `MailMessage`)
- `netstandard` (general fallback for type resolution)

**Fix:** Add the missing assembly to `TextExpression.ReferencesForImplementation`:
```xml
<AssemblyReference>System.Collections</AssemblyReference>
```

**Note:** If you're adding activities manually or the references are missing from an existing file, you may need to add them through `uip rpa install-or-update-packages --use-studio`.

## Invalid Use of `x:` Prefix for Non-Builtin CLR Types

**Error pattern:**
```
Cannot create unknown type '...Variable(...DateTime)'
Cannot create unknown type '...Variable(...DateTimeOffset)'
Cannot create unknown type '...Variable(...Guid)'
Cannot create unknown type '...InArgument(...DateTime)'
```

**Root cause:** `x:` and `s:` are not two different type systems — they are XML namespace aliases. `x:String` and `s:String` both refer to the same underlying `System.String`. The difference is purely which XML namespace schema registers the mapping:

- `x:` maps to the **XAML language schema** (`http://schemas.microsoft.com/winfx/2006/xaml`), which only registers a small, fixed set of types.
- `s:` maps to the **CLR System namespace** (`clr-namespace:System;assembly=System.Private.CoreLib`), which resolves types directly in `System` (e.g. `DateTime`, `Guid`) — subnamespaces like `System.IO` or `System.Collections.Generic` require their own separate aliases (e.g. `xmlns:sio`, `xmlns:scg`).

The error occurs because the XAML language schema does not register `DateTime`, `DateTimeOffset`, `Guid`, etc. — so `x:DateTime` has no definition, while `s:DateTime` resolves correctly.

**Types registered in the XAML language schema** (the only ones valid with the `x:` prefix):

| Valid `x:` type | C# equivalent |
|-----------------|---------------|
| `x:String` | `string` |
| `x:Int32` | `int` |
| `x:Int64` | `long` |
| `x:Double` | `double` |
| `x:Boolean` | `bool` |
| `x:Byte` | `byte` |
| `x:Single` | `float` |
| `x:Decimal` | `decimal` |
| `x:Char` | `char` |
| `x:Object` | `object` |
| `x:TimeSpan` | `TimeSpan` |

**If a type is not in that list, you cannot use `x:` for it** — even if it is a core .NET type.

**Correct alternative prefixes for common System types** (requires `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`):

| Wrong | Correct | Notes |
|----------|------------|-------|
| `x:DateTime` | `s:DateTime` | — |
| `x:DateTimeOffset` | `s:DateTimeOffset` | Often required by calendar/scheduling activities |
| `x:Guid` | `s:Guid` | — |
| `x:Uri` | `s:Uri` | — |

For types outside of `System`, add the matching CLR namespace alias. Examples:
```xml
xmlns:sio="clr-namespace:System.IO;assembly=System.Private.CoreLib"
<Variable x:TypeArguments="sio:FileInfo" Name="file" />
```

**Fix example:**

Wrong — causes `Cannot create unknown type` at load time:
```xml
<Variable x:TypeArguments="x:DateTime" Name="startTime" />
<Variable x:TypeArguments="x:DateTimeOffset" Name="reminderTime" />
```

Correct — requires `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`:
```xml
<Variable x:TypeArguments="s:DateTime" Name="startTime" />
<Variable x:TypeArguments="s:DateTimeOffset" Name="reminderTime" />
```

The same rule applies anywhere a type argument appears: `x:TypeArguments` on `Variable`, `InArgument`, `OutArgument`, `CSharpValue`, `CSharpReference`, `ActivityAction`, `DelegateInArgument`, etc.

---

## Variable Scope and "Not Declared" Errors

**Error:** `"'variableName' is not declared. It may be inaccessible due to its protection level"`

**Common causes:**
1. Variable declared in a child scope (e.g., inside a `Sequence`) but referenced from a parent or sibling scope
2. Variable name collision — same name in outer and inner scope causes `NullReferenceException` at runtime (UiPath only warns, doesn't error)
3. Global variables defined in `globalVariables.json` that get corrupted or duplicated
4. Activity output variable removed when the activity was deleted, but expressions still reference it

**In XAML terms:** Variables defined inside `<Sequence.Variables>` are only visible within that `<Sequence>` and its children. Moving an activity that references a variable to a different scope breaks the reference.

## "Value cannot be null. Parameter name: expression"

**Error:** `"Value cannot be null. Parameter name: expression"` at validation time.

**Causes:**
- An activity property that expects an expression has been cleared/emptied in the XAML
- The XAML has an `InArgument` or `OutArgument` element with no value or expression inside
- Deleting an activity left behind orphaned argument references

**Fix:** Find the activity with the empty expression in the XAML and either set a valid expression or remove the empty argument element.

## x:Reference / __ReferenceID Naming

Flowcharts and State Machines use `x:Name="__ReferenceID0"` and `{x:Reference __ReferenceID0}` to link nodes.

**Gotchas:**
- `__ReferenceID` values must be unique within the entire XAML file — duplicate IDs cause deserialization errors
- When copy-pasting FlowStep/FlowDecision nodes, duplicate `__ReferenceID` values will be created — Studio auto-renumbers, but manual XAML editing doesn't
- When copying from flowchart to sequence, elements may be ordered backwards due to node ordering in XAML
- `x:Reference` can only refer to elements with `x:Name` in the same XAML file — cross-file references are not supported

**When editing manually:** If adding new FlowStep/FlowDecision nodes, use a `__ReferenceID` number higher than any existing one in the file.

## XAML File Size and Performance

- XAML files over **5 MB** cause significant Studio slowdowns
- Files approaching 7+ MB can take minutes to load
- Very large files can cause Studio to hang during validation

**Prevention:** Split large workflows into smaller XAML files and use `Invoke Workflow` to call them. Keep individual XAML files under ~500 activities.

## {x:Null} vs Omitted Properties

- `PropertyName="{x:Null}"` explicitly sets a property to null — this is serialized and persisted
- Omitting a property entirely means "use the default value" — which may or may not be null
- Some activities behave differently when a property is explicitly null vs absent (e.g., `Filter="{x:Null}"` may disable filtering, while omitting `Filter` uses a default filter)
- When `uip rpa get-default-activity-xaml --use-studio` outputs properties with `{x:Null}`, preserve them — removing them may change behavior

## Literal Curly Braces in Attribute Values

- Attribute values starting with `{` are parsed as XAML markup extensions — `Search="{FullName}"` fails with `Could not find type 'FullName' in namespace '...'`
- This affects **any** literal string property, not just `WordReplaceText.Search` — common with Word/text template placeholders like `{FullName}`, `{Email}`, `{DepartmentName}`
- Expression-wrapped values (`Search="[&quot;{FullName}&quot;]"`) are not affected — the expression engine handles those, not the XAML parser

**Fix:** Prefix with the XAML escape sequence `{}` to indicate a literal string: `Search="{}{FullName}"`

## Selector Special Characters

When writing selectors in XAML, XML special characters must be escaped:

| Character | XAML Escape | Notes |
|-----------|------------|-------|
| `&` | `&amp;` | Most common issue — `&` in window titles/URLs |
| `<` | `&lt;` | Rare in selectors |
| `>` | `&gt;` | Rare in selectors |
| `"` | `&quot;` | Inside attribute values |
| `'` | `&apos;` | Inside single-quoted attributes |

**Double-encoding gotcha:** If a selector value goes through both XML escaping and UiPath's own escaping, you may get `&amp;amp;` instead of `&amp;`. Use `SecurityElement.Escape()` in C# expressions for dynamic selectors.

## ViewState Section Corruption

The `<sap2010:WorkflowViewState.ViewStateManager>` section can become corrupted:
- **Studio crashes during save** can truncate the ViewState, causing "Unexpected end of file" errors
- **Duplicate `sap2010:WorkflowViewState.IdRef`** values cause deserialization failures
- **Manual editing of ViewState** almost always causes problems — it contains serialized designer positions, expanded/collapsed states, and breakpoint info

**Fix:** If ViewState is corrupted, use the `Edit` tool to delete the entire `<sap2010:WorkflowViewState.ViewStateManager>` section. Studio will regenerate it when the file is opened (you'll lose designer layout but not workflow logic).

## Git and Version Control Issues

- **XAML files may be detected as binary** by Git if they contain BOM or unusual characters — add `*.xaml diff` to `.gitattributes`
- **Merge conflicts in XAML** are extremely difficult to resolve manually due to the XML structure and `__ReferenceID` numbering
- **Simply opening a XAML file** in Studio can cause it to report changes (Studio normalizes formatting, updates ViewState) — this creates noise in Git diffs
- **Recommendation:** Avoid parallel editing of the same XAML file. If merge conflicts occur, prefer taking one version entirely rather than manual conflict resolution

## JitCustomTypesSchema.json not found or not updated

The `.project/JitCustomTypesSchema.json` file can be missing or outdated.

**Fix:** Use the `Read` tool to read it one more time only. If this also fails, then read the project structure.

## CLI-Specific Pitfalls

### `get-errors --file-path` requires relative paths

The `--file-path` parameter of `uip rpa get-errors --use-studio` must be a path **relative to the project directory**:
- Correct: `--file-path "Workflows/SendEmail.xaml"`
- Wrong: `--file-path "C:\Users\me\Projects\MyProject\Workflows\SendEmail.xaml"`

Using an absolute path will result in a "file not found" error even if the file exists.

### `--project-dir` defaults to CWD

All `uip rpa` commands default to the current working directory as the project root. If you are running commands from a parent directory or monorepo root, every command will silently target the wrong location. Always verify the CWD contains `project.json`, or pass `--project-dir` explicitly.

### Studio IPC connection failures

`uip rpa` commands communicate with Studio Desktop via IPC. If Studio is not running, not responding, or has no project open, commands will fail with connection errors. Recovery steps:
1. `uip rpa list-instances --output json --use-studio` — check if Studio is running
2. `uip rpa start-studio` — start Studio if not running
3. `uip rpa open-project --project-dir "..." --use-studio` — open the project if Studio has no project loaded
4. If Studio is running but unresponsive, the user may need to restart it manually

### CLI output format for parsing

Always use `--output json` when you need to parse CLI output programmatically. The default `table` format is human-readable but unreliable for parsing (column alignment varies, long values may be truncated). JSON output is structured and unambiguous.

### DataTable.Select numeric comparisons on Excel-sourced data

When reading Excel data with `ReadRangeX`, column types in the resulting `DataTable` may be `String` even when the Excel cells contain numbers. This causes `DataTable.Select("[Amount] > 1000")` to perform string comparison instead of numeric comparison (e.g., `"4200" < "800"` alphabetically), silently dropping rows.

**Workarounds:**
- Use LINQ with explicit conversion: `dtData.AsEnumerable().Where(Function(row) CDbl(row("Amount")) > 1000).CopyToDataTable()`
- Convert the column type after reading: loop through rows and convert values, or clone the DataTable with the correct column types
