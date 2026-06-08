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
| PDF activities (ReadPDFText, GetPDFPageCount, ExtractPDFPageRange, ManagePDFPassword, ExportPDFPageAsImage, ExtractImagesFromPDF, ReadXPSText) | `FileName` (string) | `ResourceFile` (IResource) | — |

**Key rule**: Exactly ONE group must have values. Setting properties from multiple groups OR no groups both cause validation errors.

### ItemArgument and `.Item` Child Elements in OverloadGroup Activities

`uip rpa activities get-default-xaml` returns activities with `.Item` child elements containing `ItemArgument` nodes. These are internal scaffolding for the FileName/ResourceFile overload group switching mechanism. **Do NOT include `.Item` child elements when writing XAML manually.** Simply set the desired overload group property (e.g., `FileName`) directly on the activity element and omit the `.Item` child entirely. Studio will auto-generate the internal `.Item` structure when it loads the workflow.

**Example — correct (no `.Item` child):**
```xml
<upap:GetPDFPageCount DisplayName="Get PDF Page Count"
    FileName="[pdfPath]" ResourceFile="{x:Null}" PageCount="[pageCount]" />
```

**Example — avoid (`.Item` child from `activities get-default-xaml`):**
```xml
<upap:GetPDFPageCount FileName="[pdfPath]" ResourceFile="{x:Null}" PageCount="[pageCount]">
    <upap:GetPDFPageCount.Item>
      <upap:ItemArgument x:TypeArguments="upr:IResource" FileName="{x:Null}" ResourceFile="{x:Null}" />
    </upap:GetPDFPageCount.Item>
</upap:GetPDFPageCount>
```

Including the `.Item` child with misconfigured `ItemArgument` properties can cause `"None of the overload groups have all their required/optional activity arguments configured"` validation errors. This applies to all activities that use the `ItemArgument` pattern, including PDF, Excel, and other file-based activities.

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
| ConvertHtmlToPDF, ConvertTextToPDF | `InputMode = File` | `FileName` or `ResourceFile` must be set |
| ConvertHtmlToPDF | `InputMode = Content` | `Html` must be set |
| ConvertTextToPDF | `InputMode = Content` | `Text` must be set |

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

## NTypeInto `Text` with literal `[k(...)]` special-key tokens

When `Text` contains literal `[k(...)]`, `[d(...)]`, or `[u(...)]` special-key tokens, use the long-form element — never the attribute form. The attribute form runs correctly but the value does not render in Studio, so the workflow looks empty even though it works.

**Wrong:** `Text="[&quot;13700132[k(enter)]&quot;]"` → runs, but `Text` shows blank in Studio.

**Correct:**
```xml
<uix:NTypeInto ...>
  <uix:NTypeInto.Text>
    <InArgument x:TypeArguments="x:String">["13700132[k(enter)]"]</InArgument>
  </uix:NTypeInto.Text>
</uix:NTypeInto>
```

Alternatives:
- Build the bracket characters with `ChrW(91)` / `ChrW(93)` so the string carries no literal `[` / `]`: `Text="[&quot;13700132&quot; &amp; ChrW(91) &amp; &quot;k(enter)&quot; &amp; ChrW(93)]"`.
- Split the input: one `NTypeInto` for the digits, one `NKeyboardShortcuts` (or a second `NTypeInto`) for `[k(enter)]`.

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

## IResource / ILocalResource — String Path Conversion

Many activities (O365, GSuite, Mail, file operations, Document Understanding) require `IResource` or `ILocalResource` properties, not string paths. Passing a string where `IResource` is expected causes a validation error. `LocalResource(string)` constructor is internal — you cannot call it directly.

**Approach 1 — Path Exists activity (recommended, works in VB and C# projects):**

Use the "Path Exists" activity with a file path as input. The output property **"Reference if path exists"** returns an `ILocalResource` (which also satisfies `IResource`). This both verifies the file exists and gives you the resource reference.

**Approach 2 — `LocalResource.FromPath()` expression (works in VB and C# projects):**

Use as an expression directly in activity properties — no existence check, creates the reference regardless:
```
LocalResource.FromPath(filePath)
```

In XAML (C# expression project):
```xml
<InArgument x:TypeArguments="upr:ILocalResource">
  <CSharpValue x:TypeArguments="upr:ILocalResource">LocalResource.FromPath(filePath)</CSharpValue>
</InArgument>
```

Requires namespace `UiPath.Platform.ResourceHandling` in the XAML header:
```xml
<x:String>UiPath.Platform.ResourceHandling</x:String>
```

This pattern applies to: `UploadFilesConnections`, `DownloadFileConnections`, `SendMail` attachments, `MoveFile`, `CopyFile`, `CompressZipFiles`, `ExtractDocumentData`, and any other activity with `IResource`/`ILocalResource` properties.

## InvokeWorkflow Gotchas

- **Auto-appends .xaml**: If the `WorkflowFileName` has no file extension, `.xaml` is appended automatically. Passing `"workflow.txt"` becomes `"workflow.txt.xaml"`.
- **TargetSession validation**: `TargetSession.Secondary` (or any non-Current value) requires `UnSafe=True`. Without it, validation fails.
- **Persistence with isolation**: Using `ResumeInstanceId` with Safe mode (`UnSafe=false`) without persistence support throws `NotSupportedException`.

### WorkflowFileName Must Be a Plain String Path

`WorkflowFileName` accepts a **plain string literal**, not a VB/C# expression. Use the relative path directly — do NOT wrap it in expression brackets or string-literal quotes.

**Correct:**
```xml
<ui:InvokeWorkflowFile WorkflowFileName="ResetSpotify.xaml" />
<ui:InvokeWorkflowFile WorkflowFileName="Workflows\ProcessData.xaml" />
```

**Wrong — VB expression string literal (common agent mistake):**
```xml
<!-- Studio silently accepts this but the path resolution may break -->
<ui:InvokeWorkflowFile WorkflowFileName="[&quot;Workflows\ProcessData.xaml&quot;]" />
```

The path is relative to the project root directory. Use backslashes for subfolder paths (e.g., `Workflows\SendEmail.xaml`). If the file is at the project root, use just the filename (e.g., `ResetSpotify.xaml`).

### Arguments Must NOT Use a Dictionary Wrapper

`uip rpa activities get-default-xaml` returns an empty `scg:Dictionary` as the default container for `InvokeWorkflowFile.Arguments`. This is correct for the **empty state only**. When you populate arguments, drop the Dictionary wrapper and use direct `InArgument`/`OutArgument`/`InOutArgument` child elements instead.

Studio silently clears any Dictionary-wrapped argument entries on load — the arguments appear mapped in the designer but are empty at runtime, with no validation error.

**Correct — direct child elements (what Studio actually serializes):**
```xml
<ui:InvokeWorkflowFile WorkflowFileName="ResetSpotify.xaml"
    DisplayName="ResetSpotify - Invoke Workflow File (ResetSpotify.xaml)" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <InArgument x:TypeArguments="x:String" x:Key="argument1">someValue</InArgument>
    <InArgument x:TypeArguments="x:String" x:Key="argument2">anotherValue</InArgument>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

**Wrong — Dictionary wrapper (from `activities get-default-xaml` empty state):**
```xml
<ui:InvokeWorkflowFile WorkflowFileName="ResetSpotify.xaml"
    DisplayName="ResetSpotify - Invoke Workflow File (ResetSpotify.xaml)">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="argument1">someValue</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="argument2">anotherValue</InArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

**Rules for argument bindings:**
1. Each argument key (`x:Key`) must match the argument name defined in the callee workflow's `x:Members` exactly (case-sensitive)
2. Use the correct argument direction: `InArgument` for `in_*`, `OutArgument` for `out_*`, `InOutArgument` for `io_*`
3. The `x:TypeArguments` must match the callee's argument type
4. For literal string values, place the text directly in the element content (e.g., `<InArgument ...>someValue</InArgument>`)
5. For variable bindings, follow the expression language rules in [xaml-basics-and-rules.md](xaml-basics-and-rules.md#expression-language): VB uses `[bracket]` shorthand, C# uses `<CSharpValue>`/`<CSharpReference>` elements

### OutArgument Bindings Must Be Variable References

`OutArgument` and `InOutArgument` bindings on `InvokeWorkflowFile.Arguments` require a variable reference (lvalue), not a constructed expression. The callee writes its output into the variable; an inline-constructed `OutArgument` has no destination.

**Wrong** — fails with `BC30035: Syntax error`:
```xml
<OutArgument x:TypeArguments="x:Boolean" x:Key="out_Discard">[New OutArgument(Of Boolean)()]</OutArgument>
```

**Correct** — declare a discard variable in the caller's scope:
```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:Boolean" Name="discardShouldContinue" />
</Sequence.Variables>
...
<OutArgument x:TypeArguments="x:Boolean" x:Key="out_Discard">[discardShouldContinue]</OutArgument>
```

If the caller does not consume an output but the callee declares it as required, declare a `discard*` variable per unused output and reference it. Omitting the binding fails validation when the callee has required out-arguments.

## Empty Argument Values

`<InArgument>` and `<OutArgument>` with **empty content** pass per-file `uip rpa validate` but fail project-level `uip rpa analyze` with `Value for a required activity argument 'Value' was not supplied` — no file or activity pointer.

**Wrong:**
```xml
<Assign.Value>
  <InArgument x:TypeArguments="x:String"></InArgument>
</Assign.Value>
```

**Correct:**
```xml
<Assign.Value>
  <InArgument x:TypeArguments="x:String">[String.Empty]</InArgument>
</Assign.Value>
```

Or attribute form with explicit literal:
```xml
<Assign Value="[String.Empty]" />
```

**Detection rule.** When project-level `analyze` reports the missing-Value error with no activity ID, grep for `<InArgument [^>]*></InArgument>` and `<OutArgument [^>]*></OutArgument>` across all XAML files first.

## Variable.Default — Attribute or Literal Content Only

`<Variable.Default>` accepts an expression literal as element content or as the `Default` attribute. It does NOT accept a wrapped `<InArgument>` element — that form throws at activity load with `Set property 'System.Activities.Variable(...).Default' threw an exception. Value for a required activity argument 'Value' was not supplied.`

**Wrong** — throws at activity load:
```xml
<Variable x:TypeArguments="scg:Dictionary(x:String, x:String)" Name="data">
  <Variable.Default>
    <InArgument x:TypeArguments="scg:Dictionary(x:String, x:String)">[New Dictionary(Of String, String)()]</InArgument>
  </Variable.Default>
</Variable>
```

**Correct — attribute form (preferred):**
```xml
<Variable x:TypeArguments="scg:Dictionary(x:String, x:String)" Name="data" Default="[New Dictionary(Of String, String)()]" />
```

**Correct — content form (no `InArgument` wrapper):**
```xml
<Variable x:TypeArguments="scg:Dictionary(x:String, x:String)" Name="data">
  <Variable.Default>[New Dictionary(Of String, String)()]</Variable.Default>
</Variable>
```

Or omit `Default` entirely if the variable is assigned before its first read.

## InvokeCode Language Property

The `Language` property on `InvokeCode` uses the `UiPath.Core.Activities.NetLanguage` enum, which has **only two valid values**: `VBNet` and `CSharp`.

**Critical:** The project-level `expressionLanguage` in `project.json` uses `"VisualBasic"`, but InvokeCode's `Language` attribute requires `"VBNet"` instead. Do NOT use `"VisualBasic"` or `"VB"` — neither is a valid `NetLanguage` value. `"CSharp"` is the same in both.

**What happens:** `Language="VisualBasic"` (or `"VB"`) passes Studio validation but fails at runtime:
```
Failed to create a 'Language' from the text 'VisualBasic'.
System.FormatException: VisualBasic is not a valid value for NetLanguage.
```

**Prevention:** Omit the `Language` attribute entirely — InvokeCode infers it from the project's expression language. If you must set it explicitly, use `"VBNet"` or `"CSharp"`.

## `Chr()` / `Asc()` Break at Runtime in Modern Projects — Use `ChrW()` / `AscW()`

`Chr(n)` / `Asc(c)` go through ANSI code page 1252, which .NET 6+ does not register. For `n ≥ 128` they throw `System.NotSupportedException: No data is available for encoding 1252` at runtime — after passing both `validate` and `build`. Use `ChrW(n)` / `AscW(c)` (Unicode, no code page) instead, or the BCL `Convert.ToChar(n)` / `CInt(c)`.

`Chr`/`ChrW`/`Asc`/`AscW` live in `Microsoft.VisualBasic`, which is not auto-imported — `BC30451: 'ChrW' is not declared` means you must add `Microsoft.VisualBasic` to both `NamespacesForImplementation` and `ReferencesForImplementation`. The `Convert.*` BCL forms avoid this.

`ContinueOnError=True` silently swallows the runtime exception (workflow looks successful, output is wrong/empty) — set it to `False` while debugging.

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

**Studio re-expansion injects default expressions that need imports (CLI-clean, Studio-red).** `validate`/`build` accept a minimally-authored `NetHttpRequest`. When the file is later opened in Studio / Studio Web, Studio re-serializes the activity with its full default property set — including default expressions for `FormDataParts` (`New List(Of FormDataPart) From {New FileFormDataPart(), New BinaryFormDataPart(), New TextFormDataPart()}`) and `RetryStatusCodes`. `FormDataParts` names types from `UiPath.Web.Activities.Http.Models`, so Studio reports `BC30002: Type 'FormDataPart' is not defined` though the CLI was clean — even when `RequestBodyType="None"`. **Fix:** add `UiPath.Web.Activities.Http.Models` to `TextExpression.NamespacesForImplementation`. A type referenced by simple name in a VB expression must be **imported** there; an `xmlns:` prefix on the root element only resolves element/attribute type names, not expression compilation.

**Two related Studio Web round-trip behaviors to author for.** On save, Studio Web (a) rewrites child-element argument bindings to attribute form — e.g. `<Throw.Exception><InArgument x:TypeArguments="s:Exception">[…]</InArgument></Throw.Exception>` becomes `Exception="[…]"` — and (b) prunes unused root `xmlns` declarations. Prefer attribute-form bindings where they work; it keeps round-trip diffs minimal and matches the shape Studio Web will produce anyway.

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

## IS `ConnectorActivity` Gotchas

Full authoring flow: [../is-connector-xaml-guide.md](../is-connector-xaml-guide.md).

### JIT `OutArgument` from Studio Designer Breaks Fresh Loads

When Studio's designer touches an IS `ConnectorActivity`, it can inject a JIT-typed `OutArgument` on the `Jit_<operation>` `FieldObject`:

```xml
<isactr:FieldObject Name="Jit_send_message_to_channel_v2" Type="FieldArgument">
  <isactr:FieldObject.Value>
    <OutArgument x:TypeArguments="uiascb:send_message_to_channel_v2_Create" />
  </isactr:FieldObject.Value>
</isactr:FieldObject>
```

The `uiascb:` namespace points at a Studio-session-local dynamically-compiled assembly (e.g. `C35283077FA_send_mes.<hash>`). On any **fresh load** (new Studio session, Helm, CI), that assembly doesn't exist, compile fails with:

```
[Error] Unable to create activity builder for <workflow>.xaml.
Reason was 'Cannot create unknown type '{...}OutArgument({...}<op>_Create)'.'
```

**Fix** — strip the injected `OutArgument` back to bare form:

```xml
<isactr:FieldObject Name="Jit_send_message_to_channel_v2" Type="FieldArgument" />
```

Also remove the `xmlns:uiascb` namespace declaration from the root `<Activity>` element if no other reference uses it. Tracked as PILOT-4812.

### Field Names Come From the Schema, Not Memory

`FieldObject Name` values are connector-specific and schema-driven. Never guess. Always read:

```bash
uip is resources describe <connector-key> <operation-name> --operation Create --output json
cat ~/.uipath/cache/integrationservice/<connector-key>/_static/<operation>.Create.json
```

Guessed names (e.g. `method`/`path`/`body` for an HTTP operation that actually expects connector-specific names) trigger a `Configuration contains a breaking change` runtime error.

### `Configuration` Attribute Is Opaque

The `Configuration` attribute on `ConnectorActivity` is a base64 + gzip JSON blob encoding connector + operation identity (`ConnectorKey`, `ObjectName`, `HttpMethod`, `Operation`, `ActivityType`). **Never hand-edit.** Always take the value verbatim from `uip rpa activities get-default-xaml --activity-type-id <GUID> --connection-id <GUID>`.

### `FieldObject.Value` Attribute Does Nothing

Putting a literal in the attribute form — `<isactr:FieldObject Name="channel" Value="hello" />` — is silently ignored. The runtime only reads the element form:

```xml
<isactr:FieldObject Name="channel" Type="FieldArgument">
  <isactr:FieldObject.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">"hello"</CSharpValue>
    </InArgument>
  </isactr:FieldObject.Value>
</isactr:FieldObject>
```

## Deprecated Activities (Do Not Use)

| Deprecated | Replacement | Notes |
|-----------|-------------|-------|
| Old trigger activities (`ClickTriggerActivity`, `KeyPressTriggerActivity`, etc.) | New trigger framework | Marked `[Browsable(false)]`, kept for backward compat only |
| `ReplayUserEvent` | `ReplayUserEventV2` | Old version still loads but shouldn't be used |
| `UiPath.<Vendor>.IntegrationService.Activities` packages | Generic `ConnectorActivity` via IS | Vendor-specific IS packages are deprecated |

## Common Activity Name Confusions

Activity tag names rarely match Studio display names. Guessing the tag from the display name fails at `build` (`Cannot create unknown type '...'`). Two examples:

| Display Name | Wrong guess | Correct tag |
|--------------|-------------|-------------|
| Delete File | `ui:DeleteFile` | `ui:DeleteFileX` |
| Wait | `ui:Wait` | `Delay` (MWF primitive — no prefix) |

### `InvokeProcess` vs `StartProcess`

To launch a local executable (`.exe`/`.cmd`/`.bat`), use `ui:StartProcess` (property `FileName` + `Arguments`). `ui:InvokeProcess` runs an Orchestrator process/package (property `ProcessName`) and has **no `FileName`** — reaching for one means you picked the wrong activity. Don't work around it with `Shell()`, `Process.Start`, or `InvokeCode`; for PowerShell use `InvokePowerShell<T>`.

### Tag Verification Gate

Before writing any `<prefix:Tag>` not already in the file:

- **Doc check.** `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Tag>.md`, or `references/activity-docs/<PackageId>/<closest-version>/activities/<Tag>.md`. No file → no such tag.
- **CLI lookup.** `uip rpa activities find --query "<verb>" --output json` → use the returned `ClassName`.

Skipping both produces `Cannot create unknown type` at `build`.

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

Use `uip rpa activities get-default-xaml` to get correct xmlns declarations — never guess namespace mappings.

### `Delay` — no namespace prefix

`Delay` is a Microsoft Workflow Foundation primitive (`System.Activities.Statements.Delay`), reached via the root `<Activity>` default xmlns and written unprefixed:

```xml
<Delay Duration="00:00:02" DisplayName="Wait for server" />
```

`<ui:Delay .../>` fails with `Cannot create unknown type '{...uipath...}Delay'`. The `ui:` prefix maps to `UiPath.Core.Activities`, which has no `Delay` override.

**For other primitives** (`Sequence`, `If`, `Assign`, `ForEach`, `While`, `TryCatch`, `Switch`, …) UiPath provides `ui:`-prefixed overrides for many — which one to use depends on the behavior you want. Check with `uip rpa activities find --query "<name>"` before assuming MWF or UiPath; don't generalize from `Delay`.

## Portable vs Windows Framework Limitations

- Activities in `/Windows/` or `/NetFramework/` source folders are **Windows-only** and won't work in Portable projects
- Some activities are explicitly hidden (`[Browsable(false)]`) when compiled for cross-platform (`XPLAT`)
- Excel encryption activities, some interop-based activities, and `VerifyControlAttribute` (testing) have platform restrictions
- Check `project.json` `targetFramework` before using Windows-only activities

## DataTable Activity Gotchas

- **LookupDataTable column resolution**: When multiple column identifiers are set (shouldn't happen due to OverloadGroups), only the first non-null is used: `LookupColumnIndex ?? LookupColumnName ?? LookupDataColumn`
- **FilterDataTable**: Column must exist AND be type-compatible with the filter operator. Filtering a DateTime column with "Contains" fails at CacheMetadata validation.
- **BuildDataTable**: Uses a security-related allowed types list. DataTables with certain .NET types may fail to serialize/deserialize.
- **BuildDataTable — `TableInfo` is designer-only.** The required `TableInfo` property is a serialized string with no documented format; activity docs say "configure through the designer instead". **Cannot be authored in agent-written XAML.** Skip the activity. Build the DataTable inline with `Assign` + `InvokeMethod` instead. Requires the standard `sd` namespace alias (matches the rest of the activity-docs corpus — see `ForEachRow.md` and `AddDataRow.md`) and `xmlns:s`.

  **VB XAML** (`expressionLanguage: VisualBasic` — bracket shorthand `[expr]`, `New T()`, `GetType(T)`):
  ```xml
  <!-- Modern (Windows/Portable):
       xmlns:sd="clr-namespace:System.Data;assembly=System.Data"
       xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib" -->
  <!-- Legacy (.NET Framework 4.6.1):
       xmlns:sd="clr-namespace:System.Data;assembly=System.Data"
       xmlns:s="clr-namespace:System;assembly=mscorlib" -->
  <Variable x:TypeArguments="sd:DataTable" Name="dt" Default="[New System.Data.DataTable()]" />
  ...
  <InvokeMethod TargetObject="[dt.Columns]" MethodName="Add">
    <InArgument x:TypeArguments="x:String">Name</InArgument>
    <InArgument x:TypeArguments="s:Type">[GetType(System.String)]</InArgument>
  </InvokeMethod>
  <InvokeMethod TargetObject="[dt.Columns]" MethodName="Add">
    <InArgument x:TypeArguments="x:String">Amount</InArgument>
    <InArgument x:TypeArguments="s:Type">[GetType(System.Decimal)]</InArgument>
  </InvokeMethod>
  ```
  **C# XAML** (`expressionLanguage: CSharp`): replace bracket-shorthand expressions with `<CSharpValue x:TypeArguments="T">...</CSharpValue>` / `<CSharpReference x:TypeArguments="T">...</CSharpReference>` wrappers inside the `<InArgument>`/`<Default>` elements. See [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md) for the full binding form per property.

  Note the `s:Type` argument — `x:Type` resolves to `TypeExtension` and fails (see § Invalid Use of `x:` Prefix). `assembly=System.Data` works in both targets via .NET type forwarding; `System.Data.Common` is the canonical home in modern .NET but the bundled UiPath docs standardize on `System.Data`.
- **GetRowItem**: Must specify at least one of `Column`, `ColumnIndex`, or `ColumnName` — all three empty causes validation error.

## Testing Activity Gotchas

- **VerifyControlAttribute**: Cannot be nested inside another `VerifyControlAttribute` — validation error
- **Assert activities** require `BookmarkResumptionHelper` extension (added via `metadata.RequireExtension<BookmarkResumptionHelper>()` in CacheMetadata)
- **TakeScreenshotInCaseOfSucceedingAssertion** and **TakeScreenshotInCaseOfFailingAssertion** are `[RequiredArgument]` on assert activities even though they default to `false`

## Enum-Valued Properties Are a `validate` Blind Spot

Activity properties typed as enums (e.g. `Operator`, `ClickType`, `KeyModifiers`, `EmptyFieldMode`, comparison/filter strategies) are checked at compile time against the activity's enum, **not** during `validate` static analysis. An invalid identifier on an enum-typed attribute returns "no diagnostics found" from `validate` and surfaces only at `build` / `CacheMetadata` time. Two consequences:

1. Always read `{projectRoot}/.local/docs/packages/<PackageId>/activities/<Activity>.md` for the exact, package-version-specific enum members before authoring an enum-valued attribute. Do not infer values from naming intuition or from prose in this skill.
2. Always run `uip rpa build` after `validate` clears — it is the only validator that catches invalid enum identifiers (see [../validation-guide.md § Validation Iteration Loop](../validation-guide.md#validation-iteration-loop)).

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
5. Use `uip rpa validate` to validate after changes

**Prevention:** When using `uip rpa activities get-default-xaml`, the output matches the currently installed package version. Never copy XAML snippets from projects using different package versions.

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

### C# expression pitfalls — separate file

Applies only to XAML projects with `expressionLanguage: CSharp` — not to VB XAML, and not to coded workflows (`.cs` files). Attribute-form expressions, `OutArgument<T>` parse failures, and `ThrowIfNotInTree` all have root causes specific to that configuration. See [csharp-expression-pitfalls.md](csharp-expression-pitfalls.md) and [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md).

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

**Note:** If you're adding activities manually or the references are missing from an existing file, you may need to add them through `uip rpa packages install`.

## Workflow Argument Declarations Use `<x:Members>`, Not `<Activity.Properties>`

**Error pattern (Studio refuses to open the file):**
```
Cannot create unknown type '{http://schemas.microsoft.com/netfx/2009/xaml/activities}Property'
```

**Root cause:** Workflow arguments (In/Out/InOut) must be declared in `<x:Members>` with `<x:Property>` children — both prefixed with `x:` (the XAML language schema, `http://schemas.microsoft.com/winfx/2006/xaml`). Writing `<Activity.Properties>` with bare `<Property>` elements resolves `Property` against the **default** xmlns (the activities namespace), where no such type exists — so the file fails to load entirely.

**Wrong** — Studio cannot open the workflow:
```xml
<Activity.Properties>
  <Property Name="in_Username" Type="InArgument(x:String)" />
  <Property Name="out_LoginSuccess" Type="OutArgument(x:Boolean)" />
</Activity.Properties>
```

**Correct:**
```xml
<x:Members>
  <x:Property Name="in_Username" Type="InArgument(x:String)" />
  <x:Property Name="out_LoginSuccess" Type="OutArgument(x:Boolean)" />
</x:Members>
```

This is a hard-load error, not a validation warning — the file cannot even be opened in the designer. If a hand-written or generated workflow shows this symptom, search-and-replace `<Activity.Properties>` → `<x:Members>` and `<Property ` → `<x:Property ` (and the matching closing tags). The `<x:Members>` form appears in every starter from `uip rpa activities get-default-xaml` and in the canonical anatomy at [xaml-basics-and-rules.md § XAML File Anatomy](xaml-basics-and-rules.md#xaml-file-anatomy).

---

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
| `x:Exception` | `s:Exception` | `<Catch x:TypeArguments="s:Exception">`, `Throw` argument types |
| `x:Type` | `s:Type` | `<InArgument x:TypeArguments="x:Type">` silently resolves to `System.Activities.XamlIntegration.TypeExtension`, NOT `System.Type`. Passing `[GetType(System.String)]` fails with `BC30311: Value of type 'Type' cannot be converted to 'TypeExtension'`. Required by `InvokeMethod` calls into APIs that take `System.Type` (e.g. `DataColumnCollection.Add(name, type)`). |

For types outside of `System`, add the matching CLR namespace alias. Examples:
```xml
xmlns:sio="clr-namespace:System.IO;assembly=System.Private.CoreLib"
<Variable x:TypeArguments="sio:FileInfo" Name="file" />
```

**Do NOT use dotted full CLR names in `x:TypeArguments`** — `x:TypeArguments` accepts only XML-prefix-qualified names, never dotted full names. The XAML parser does not resolve dotted CLR identifiers; each subnamespace requires its own `xmlns` alias.

Wrong — fails with `Cannot create unknown type` at load time:
```xml
<Variable x:TypeArguments="System.Security.SecureString" Name="var_SecurePass" />
<OutArgument x:TypeArguments="System.Security.SecureString">[var_SecurePass]</OutArgument>
```

Correct — declare the alias once on the root `<Activity>`, then use it everywhere the type appears:
```xml
xmlns:ss="clr-namespace:System.Security;assembly=System.Private.CoreLib"
<Variable x:TypeArguments="ss:SecureString" Name="var_SecurePass" />
<OutArgument x:TypeArguments="ss:SecureString">[var_SecurePass]</OutArgument>
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

## Array Types in `Variable` Declarations

The XAML parser rejects CLR array syntax in `<Variable x:TypeArguments="...">`. `<Variable x:TypeArguments="x:String[]">` fails to load with `Cannot create unknown type ... Variable(String[])`. The error message does not hint at the fix.

**Use `scg:List(<T>)` instead of `<T>[]`** for variable declarations. Required `xmlns:scg` declaration depends on `targetFramework`:

- **Modern (Windows/Portable):** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"`
- **Legacy (.NET Framework 4.6.1):** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"`

Wrong:
```xml
<Variable x:TypeArguments="x:String[]" Name="paths" />
```

Correct — **VB XAML** (`expressionLanguage: VisualBasic`, bracket shorthand for the default expression):
```xml
<Variable x:TypeArguments="scg:List(x:String)" Name="paths" Default="[New List(Of String)()]" />
```

Correct — **C# XAML** (`expressionLanguage: CSharp`): drop the `Default` attribute and use `<Variable.Default>` with `<CSharpValue>` instead; see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md).

**`InArgument` with array `x:TypeArguments` — context-dependent.** The canonical XAML for `AddDataRow.ArrayRow` (see [`../activity-docs/UiPath.System.Activities/26.4/activities/AddDataRow.md`](../activity-docs/UiPath.System.Activities/26.4/activities/AddDataRow.md)) uses `<InArgument x:TypeArguments="x:Object[]">[New Object() { ... }]</InArgument>` and Studio accepts it. Some agent-authored variants of the same form have been reported to fail at parse time — root cause unverified. **If `InArgument x:TypeArguments="x:Object[]"` fails in your project, fall back to calling the underlying params overload via `InvokeMethod`** (only safe when the target method has a `ParamArray Object()` / `params object[]` overload — `DataRowCollection.Add` does):

```xml
<InvokeMethod TargetObject="[dt.Rows]" MethodName="Add">
  <InArgument x:TypeArguments="x:String">Alice</InArgument>
  <InArgument x:TypeArguments="x:Int32">42</InArgument>
</InvokeMethod>
```

This pattern is NOT a general substitute for fixed-arity array parameters — only for `ParamArray`/`params` overloads where the runtime builds the array from N positional arguments. For non-params arrays (e.g. `Method(int[] arr)`), `InvokeMethod` with N separate `<InArgument>` children does not work; the array must be constructed in a preceding `Assign`.

---

## Array Types in `Variable` Declarations

The XAML parser rejects CLR array syntax in `<Variable x:TypeArguments="...">`. `<Variable x:TypeArguments="x:String[]">` fails to load with `Cannot create unknown type ... Variable(String[])`. The error message does not hint at the fix.

**Use `scg:List(<T>)` instead of `<T>[]`** for variable declarations. Required `xmlns:scg` declaration depends on `targetFramework`:

- **Modern (Windows/Portable):** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"`
- **Legacy (.NET Framework 4.6.1):** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"`

Wrong:
```xml
<Variable x:TypeArguments="x:String[]" Name="paths" />
```

Correct — **VB XAML** (`expressionLanguage: VisualBasic`, bracket shorthand for the default expression):
```xml
<Variable x:TypeArguments="scg:List(x:String)" Name="paths" Default="[New List(Of String)()]" />
```

Correct — **C# XAML** (`expressionLanguage: CSharp`): drop the `Default` attribute and use `<Variable.Default>` with `<CSharpValue>` instead; see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md).

**`InArgument` with array `x:TypeArguments` — context-dependent.** The canonical XAML for `AddDataRow.ArrayRow` (see [`../activity-docs/UiPath.System.Activities/26.4/activities/AddDataRow.md`](../activity-docs/UiPath.System.Activities/26.4/activities/AddDataRow.md)) uses `<InArgument x:TypeArguments="x:Object[]">[New Object() { ... }]</InArgument>` and Studio accepts it. Some agent-authored variants of the same form have been reported to fail at parse time — root cause unverified. **If `InArgument x:TypeArguments="x:Object[]"` fails in your project, fall back to calling the underlying params overload via `InvokeMethod`** (only safe when the target method has a `ParamArray Object()` / `params object[]` overload — `DataRowCollection.Add` does):

```xml
<InvokeMethod TargetObject="[dt.Rows]" MethodName="Add">
  <InArgument x:TypeArguments="x:String">Alice</InArgument>
  <InArgument x:TypeArguments="x:Int32">42</InArgument>
</InvokeMethod>
```

This pattern is NOT a general substitute for fixed-arity array parameters — only for `ParamArray`/`params` overloads where the runtime builds the array from N positional arguments. For non-params arrays (e.g. `Method(int[] arr)`), `InvokeMethod` with N separate `<InArgument>` children does not work; the array must be constructed in a preceding `Assign`.

---

## Generic Type Arguments Cannot Wrap Array Types

`<Variable x:TypeArguments="scg:List(x:Object[])">` fails with *"Cannot create unknown type … List(Object[])"*. The XAML type system refuses to construct `List<Object[]>` — an array element type nested inside a generic. Same for `<InArgument x:TypeArguments="scg:IEnumerable(x:Object[])">` on `ForEach.Values`. This blocks the natural shape for projecting LINQ rows into `AddDataRow.ArrayRow` (which is `InArgument<Object[]>`).

**Fix — box each row as `Object` so the collection's element type is non-array:**

- Variable: `<Variable x:TypeArguments="scg:List(x:Object)" Name="rows" />`
- Producing LINQ: `… .Select(Function(g) DirectCast(New Object(){g.Key, mean}, Object)).ToList()`
- `ForEach`: `<ForEach x:TypeArguments="x:Object">` over `scg:IEnumerable(x:Object)`
- Consumer cast: `<ui:AddDataRow ArrayRow="[CType(row, Object())]" …>`

The boxed array reaches `ArrayRow` (whose property type is `Object[]`) correctly because `CType(row, Object())` unboxes it.

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

Flowcharts, State Machines, and Long Running Workflows (ProcessDiagram) use `x:Name="__ReferenceID0"` and `<x:Reference>__ReferenceID0</x:Reference>` to link nodes.

### Where `<x:Reference>` Goes

`<x:Reference>` is used ONLY inside property elements to create cross-references between nodes:

| Property Element | Container | Purpose |
|-----------------|-----------|---------|
| `Flowchart.StartNode` | Flowchart | Points to the first node |
| `FlowStep.Next` | Flowchart | Links to the next node |
| `FlowDecision.True` / `.False` | Flowchart | Branch targets |
| `Transition.To` | State Machine | Transition destination state |
| `StateMachine.InitialState` | State Machine | Starting state (attribute form: `{x:Reference ...}`) |
| `ProcessDiagram.StartNode` | ProcessDiagram | Points to start event |
| `EventNode.Next` / `TaskNode.Next` | ProcessDiagram | Links to next node |
| `DecisionNode.True` / `.False` | ProcessDiagram | Branch targets |

### Node Registration Rule

All nodes in a Flowchart/ProcessDiagram must be registered as children of the container element. Two scenarios:

1. **Direct children** of the container (e.g., `<FlowStep>` directly under `<Flowchart>`) — already registered. Do NOT also add a trailing `<x:Reference>`.
2. **Inline definitions** inside property elements (e.g., `<FlowStep>` inside `<FlowDecision.True>`) — MUST add a trailing `<x:Reference>` entry as a direct child of the container.

**Correct — inline node registered with trailing `<x:Reference>`:**
```xml
<Flowchart>
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  <FlowDecision x:Name="__ReferenceID0">        <!-- direct child — no trailing ref -->
    <FlowDecision.True>
      <FlowStep x:Name="__ReferenceID1">         <!-- inline definition -->
        ...
      </FlowStep>
    </FlowDecision.True>
  </FlowDecision>
  <x:Reference>__ReferenceID1</x:Reference>      <!-- register inline node -->
</Flowchart>
```

**Wrong — re-listing a direct child:**
```xml
<Flowchart>
  <FlowStep x:Name="__ReferenceID0">             <!-- direct child -->
    ...
  </FlowStep>
  <x:Reference>__ReferenceID0</x:Reference>      <!-- WRONG — already a direct child -->
</Flowchart>
```

The same registration rules apply to `<upa:ProcessDiagram>` and its node types (`EventNode`, `TaskNode`, `DecisionNode`, `EndNode`, `BoundaryNode`).

### Other Gotchas

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
- When `uip rpa activities get-default-xaml` outputs properties with `{x:Null}`, preserve them — removing them may change behavior

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

### `validate --file-path` requires relative paths

The `--file-path` parameter of `uip rpa validate` must be a path **relative to the project directory**:
- Correct: `--file-path "Workflows/SendEmail.xaml"`
- Wrong: `--file-path "C:\Users\me\Projects\MyProject\Workflows\SendEmail.xaml"`

Using an absolute path will result in a "file not found" error even if the file exists.

### `--project-dir` defaults to CWD

All `uip rpa` commands default to the current working directory as the project root. If you are running commands from a parent directory or monorepo root, every command will silently target the wrong location. Always verify the CWD contains `project.json`, or pass `--project-dir` explicitly.

### Studio IPC connection failures

`uip rpa` commands communicate with Studio over IPC. By default this is a **headless Studio** that auto-launches from a NuGet package — no Studio Desktop required. Recovery steps when commands fail with connection errors:

1. **Re-run the command.** Headless Studio relaunches automatically on the next call; transient pipe errors clear on retry.
2. **Raise the timeout for the first call.** Cold NuGet restore of the headless Studio package can take 30–90 s — `uip rpa --timeout 600 <command>`.
3. **`uip rpa project open --project-dir "..."`** — open the project explicitly if Studio reports no project loaded.
4. **Studio Desktop only** — if the failing command is `diff` or `focus-activity` (or the user set `UIPATH_RPA_TOOL_USE_STUDIO=1`), check Studio Desktop with the hidden `uip rpa instances list --output json` and run `uip rpa studio start --project-dir "..."` if no instance is up.

### CLI output format for parsing

Always use `--output json` when you need to parse CLI output programmatically. The default `table` format is human-readable but unreliable for parsing (column alignment varies, long values may be truncated). JSON output is structured and unambiguous.

### DataTable.Select numeric comparisons on Excel-sourced data

When reading Excel data with `ReadRangeX`, column types in the resulting `DataTable` may be `String` even when the Excel cells contain numbers. This causes `DataTable.Select("[Amount] > 1000")` to perform string comparison instead of numeric comparison (e.g., `"4200" < "800"` alphabetically), silently dropping rows.

**Workarounds:**
- Use LINQ with explicit conversion: `dtData.AsEnumerable().Where(Function(row) CDbl(row("Amount")) > 1000).CopyToDataTable()`
- Convert the column type after reading: loop through rows and convert values, or clone the DataTable with the correct column types
