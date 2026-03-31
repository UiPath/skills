# Common pitfalls

Read this file when: you hit a validation error, need to avoid known traps, or want to check constraints before configuring an activity.

## Scope requirements

These activities must be inside a specific parent scope:

| Activity | Required parent |
|----------|----------------|
| Read Range, Write Range, Read Cell, etc. | `ExcelApplicationScope` or `ExcelApplicationCard` |
| Click, Type Into, Get Text, Check/Uncheck | `Use Application/Browser` (`NApplicationCard`) |
| All Word interop activities | `WordApplicationScope` |
| PivotTableFieldX | `CreatePivotTableX` |
| All Office 365 child activities | `Office365ApplicationScope` |
| All GSuite child activities | Corresponding GSuite scope |

Nesting restrictions:
- `SequenceX` cannot be inside another `SequenceX` or `ExcelProcessScopeX`.
- `VerifyControlAttribute` cannot be inside another `VerifyControlAttribute`.
- `InvokeVBAX` allows max 20 child `InvokeVBAArgumentX`.

## Conflicting property pairs

Setting both in a pair causes a validation error:

| Property A | Property B | Activities |
|-----------|-----------|-----------|
| `Password` | `SecurePassword` | ExcelApplicationScope, PDF, Mail |
| `EditPassword` | `SecureEditPassword` | ExcelApplicationScope |
| `SimulateClick` | `SendWindowMessages` | Click, ExtractData |

## OverloadGroup patterns

Activities with `[OverloadGroup]` have mutually exclusive property sets. Exactly ONE group must have values.

| Activity | Group A | Group B |
|----------|---------|---------|
| LookupDataTable | `LookupColumnIndex` | `LookupColumnName` |
| ReadCsvFile | `FilePath` (string) | `PathResource` (ILocalResource) |
| CopyFile, Delete | `Path` (string) | `PathResource` (IResource) |
| WorkbookActivityBase | `Workbook` | `WorkbookPath` |

## Expression language rules

Check `project.json` `expressionLanguage` before writing expressions.

**C# projects**:
- Use `<CSharpValue>` for input, `<CSharpReference>` for output (no namespace prefix).
- Do NOT use `[bracket]` shorthand. Brackets create VB expression nodes, causing "multiple languages" errors.
- String interpolation (`$"..."`) is NOT supported in XAML expressions. Use concatenation.

**VB projects**:
- Use `[bracket]` shorthand for expressions.
- Use `OrElse`/`AndAlso` (short-circuit), not `Or`/`And`.

Mixing expression languages in a project causes build failures.

## `x:` prefix type limits

The `x:` XAML namespace only registers these types: `x:String`, `x:Int32`, `x:Int64`, `x:Double`, `x:Boolean`, `x:Byte`, `x:Single`, `x:Decimal`, `x:Char`, `x:Object`, `x:TimeSpan`.

For `DateTime`, `DateTimeOffset`, `Guid`, `Uri`, use the `s:` prefix with `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`.

Wrong: `<Variable x:TypeArguments="x:DateTime" Name="startTime" />`
Correct: `<Variable x:TypeArguments="s:DateTime" Name="startTime" />`

## ActivityAction initialization

Scope activities use `ActivityAction` to wrap child content. The `DelegateInArgument` must match the `x:TypeArguments`.

| Scope activity | DelegateInArgument type | Default name |
|---------------|------------------------|--------------|
| ExcelApplicationCard | `IWorkbookQuickHandle` | `"Excel"` |
| ExcelProcessScopeX | `IExcelProcess` | `"ExcelProcessScopeTag"` |
| WordApplicationScope | `WordDocument` | `"WordDocumentScope"` |
| ExcelForEachRowX | TWO args: row + index | `"CurrentRow"`, `"CurrentIndex"` |

## NKeyboardShortcuts

Use `Shortcuts` (string) for literal hotkey encoding: `[d(hk)][d(ctrl)]a[u(ctrl)][u(hk)]`.
Do NOT use `ShortcutsArgument` for literals. It is parsed as a VB expression and `[d(hk)]` will fail.

## Variable scope errors

Error: `"'variableName' is not declared"`

Variables in `<Sequence.Variables>` are only visible within that `<Sequence>` and its children. Moving an activity to a different scope breaks references.

## Package version changes break XAML

Upgrading/downgrading packages can break XAML. Common errors:
- `"Failed to create a 'Version' from the text 'V5'"` (version attribute too high)
- `"Cannot set unknown member"` (property does not exist in target version)

Fix: use `get-default-activity-xaml` to get properties matching the installed version. Remove unknown attributes.

## Namespace mapping gotchas

| Expected | Actual | Notes |
|----------|--------|-------|
| `UiPath.UIAutomation.Activities` | `UiPath.UIAutomationNext.Activities` | Modern UI uses "Next" |
| `UiPath.UIAutomation.Activities` (classic) | `UiPath.Core.Activities` | Classic UI is in Core |

Use `get-default-activity-xaml` to get correct xmlns. Never guess.

## Literal curly braces in attributes

Attribute values starting with `{` are parsed as XAML markup extensions. `Search="{FullName}"` fails.
Fix: prefix with `{}` escape: `Search="{}{FullName}"`.

## Selector special characters

XML special characters in selectors must be escaped: `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;`, `"` as `&quot;`.

## ViewState corruption

If `<sap2010:WorkflowViewState.ViewStateManager>` is corrupted, delete the entire section. Studio regenerates it on open.

## CLI-specific pitfalls

- `get-errors --file-path` requires relative paths from the project directory. Absolute paths cause "file not found".
- `--project-dir` defaults to CWD. If CWD is wrong, all commands silently target the wrong project.
- Default output is JSON. Use `--format table` only for user display. Table format truncates values.
- `uip rpa` commands use Studio IPC. If Studio is not running, commands fail with connection errors.

## Default values that matter

| Activity | Property | Default | Notes |
|----------|----------|---------|-------|
| ExcelApplicationScope | `AutoSave` | `True` | Saves on scope exit |
| ExcelApplicationScope | `CreateNewFile` | `True` | Creates if missing |
| All UIAutomation | `TimeoutMS` | `30000` | 30s element wait |
| HTTP Request | `ContinueOnError` | `True` | Unusual: failures do not stop execution |
| HTTP Request | `Timeout` | `10000` | 10s |

## Connection service pattern

- `ConnectionId` is `[Browsable(false)]` but required when `UseConnectionService=True`.
- `ConnectionId` must be a literal string (not a variable) for design-time validation.
- Missing `ConnectionId` with `UseConnectionService=True` causes a validation error.
- Discover connections: `uip is connections list <connector-key> --format json`.

## DataTable.Select on Excel data

Excel columns may be typed as `String` even when cells contain numbers. `DataTable.Select("[Amount] > 1000")` does string comparison (`"4200" < "800"`).
Fix: use LINQ with explicit conversion (`CDbl()` in VB, `double.Parse()` in C#).
