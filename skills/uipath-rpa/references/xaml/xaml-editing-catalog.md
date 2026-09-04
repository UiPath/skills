# XAML Editing Catalog

Per-operation and per-activity catalogs for XAML authoring: editing operations (arguments, variables, imports, assembly references, expressions, resource types) and complete reference workflows. Split out of [xaml-basics-and-rules.md](xaml-basics-and-rules.md) so that file is a plain full read (Rule 22) with no marker to locate first.

**Read contract — per entry, never end-to-end:** Grep `^###` on this file to list the entries with line numbers, then Read ONLY the entries matching the operation or activity at hand. Unsure whether an entry applies → read it. Reading this file top to bottom is the mistake the split removed.

## Common Editing Operations

Common operations for editing and managing workflow XAML files.

### Adding Arguments (In/Out/InOut)

Add `x:Property` elements inside the `<x:Members>` block:

```xml
<x:Members>
  <!-- In argument (input to workflow) -->
  <x:Property Name="in_CustomerName" Type="InArgument(x:String)" />
  <!-- Out argument (output from workflow) -->
  <x:Property Name="out_ProcessedCount" Type="OutArgument(x:Int32)" />
  <!-- InOut argument (both input and output) -->
  <x:Property Name="io_DataTable" Type="InOutArgument(scg:List(x:String))" />
</x:Members>
```

Argument naming convention: `in_`, `out_`, `io_` prefixes.

#### Setting Default Values for Arguments

Defaults go on the root `<Activity>` element using the canonical .NET Workflow Foundation self-namespace syntax:

```xml
<Activity x:Class="TestCase"
          xmlns:this="clr-namespace:"
          this:TestCase.in_FileName="report.pdf"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <x:Members>
    <x:Property Name="in_FileName" Type="InArgument(x:String)" />
  </x:Members>
</Activity>
```

Two parts are mandatory:

1. **`xmlns:this="clr-namespace:"`** — the empty `clr-namespace:` is what makes `this:` resolve to the class declared by `x:Class`.
2. **`this:<ClassName>.<argName>="<value>"`** — the attribute name MUST be qualified with `this:` AND the class name; bare `<argName>="<value>"` is rejected.

The default is baked into the compiled assembly at build time as a `Literal<T>` expression in the generated class's constructor. At runtime, when the workflow is invoked without that argument supplied (e.g. `uip rpa run` without `--input-arguments`), the literal is used.

**Three default-value forms that DO NOT work** — every one of them is rejected by the XAML loader. Authoring agents have repeatedly tried these and lost time to confusing errors — don't:

| Bad form | Error |
|---|---|
| `<Activity in_FileName="...">` (no `xmlns:this`, no class qualifier) | `member (in_FileName) is not supported by DynamicActivity` |
| `<x:Property Name="in_FileName" ...><InArgument>...</InArgument></x:Property>` | `DynamicActivityProperty does not have a content property` |
| `<x:Property.Value>...</x:Property.Value>` | `x:Property member (Value) is not supported by DynamicActivityProperty` |

If you must accept an empty string as a sentinel ("user didn't provide one") and substitute a literal anyway, use a ternary inside each `CSharpValue`/`VisualBasicValue` consumer of the argument:

```xml
<CSharpValue x:TypeArguments="x:String">string.IsNullOrEmpty(in_FileName) ? "report.pdf" : in_FileName</CSharpValue>
```

But the root-attribute default above is the cleaner answer — use it first.

### Adding Variables

Add `Variable` elements inside the workflow container's `.Variables` block:

```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="filePath" />
  <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
  <Variable x:TypeArguments="x:Boolean" Name="isValid" Default="True" />
</Sequence.Variables>
```

Variables are scoped to their containing activity (Sequence, Flowchart, etc.).

**IMPORTANT — `x:` and `s:` are XML namespace aliases, not separate type systems.**
`x:String` and `s:String` both refer to `System.String`; the prefix only determines which namespace schema resolves the name. The `x:` XAML language schema registers a small fixed set of types (`x:String`, `x:Int32`, `x:Int64`, `x:Double`, `x:Boolean`, `x:Byte`, `x:Single`, `x:Decimal`, `x:Char`, `x:Object`, `x:TimeSpan`). Any other CLR type — including `DateTime`, `DateTimeOffset`, `Guid`, etc. — is not registered in that schema and must be reached through `s:` (`xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`).
Using `x:DateTime` or `x:DateTimeOffset` produces `Cannot create unknown type` at load time.
See `common-pitfalls.md` → *"Invalid Use of `x:` Prefix for Non-Builtin CLR Types"* for the full list and examples.

### Adding Namespace Imports

Add `<x:String>` entries:

```xml
<x:String>System.Data</x:String>
<x:String>System.IO</x:String>
<x:String>UiPath.Excel</x:String>
```

### Adding Assembly References

Add `<AssemblyReference>` entries:

```xml
<AssemblyReference>System.Data</AssemblyReference>
<AssemblyReference>UiPath.Excel.Activities</AssemblyReference>
```

### Expressions

#### C# Expressions (`expressionLanguage: CSharp`)

Applies to XAML workflow files in projects whose `project.json` has `expressionLanguage: CSharp`. These rules govern expressions inside XAML — they are unrelated to coded workflows (`.cs` files), which are plain C# and do not use `CSharpValue` / `CSharpReference` elements.

Expressions use explicit `<CSharpValue>` (for read/evaluate) or `<CSharpReference>` (for write/lvalue) elements inside `<InArgument>` / `<OutArgument>`:
```xml
<Assign DisplayName="Set Name">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">fullName</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">firstName + " " + lastName</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>
```

**Important**: Do NOT use `[bracket]` shorthand for expressions. Brackets create `VisualBasicValue` nodes at deserialization time, causing validation failures for C#-only syntax (`null`, `?.`, `??`, `typeof()`, etc.).

**Expression-tree limits**: each C# expression compiles as a lambda expression tree — no statements, no `out var` (`TryParse`), no optional-argument overloads (`CS0854`), and no calls into the project's coded source file types ([common-pitfalls.md § C# XAML Expressions Compile as Expression Trees](common-pitfalls.md)). When a transform outgrows single expressions, escalate per [data-manipulation-guide.md § Exception](../data-manipulation-guide.md) — Invoke Code, or a coded workflow via Invoke Workflow File.

**Stronger rule for attribute-form bindings on `InArgument<T>` / `OutArgument<T>`:** in XAML projects with `expressionLanguage: CSharp`, any **non-literal** attribute value (`Message="variableName"`, `Text="&quot;Hello &quot; + name"`) is not evaluated as an expression. Where the property type accepts a string the text survives as a literal and the workflow validates, builds, and runs with the wrong value and no error; where it does not, the file fails to deserialize. Use `<CSharpValue>` / `<CSharpReference>` child elements for anything that isn't a plain literal. See [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md) (includes § C# Expression Pitfalls).

**Safe attribute-form values** (no expression evaluator involved, type converter handles them directly):
- Literal strings on `InArgument<String>`: `Text="Book trip"`, `DisplayName="Open file"`
- Enums: `Level="Info"`, `ClickType="Single"`, `MouseButton="Left"`
- Numbers, booleans, `{x:Null}`
- `TimeSpan` literals: `Duration="00:00:02"`

**For activity-specific recipes** (`LogMessage.Message` as `InArgument<Object>`, `NGetText.TextString` as `OutArgument<String>`, `StartProcess.FileName` with composed paths, `Assign`, `If.Condition`, etc.), see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md). That file is the canonical lookup for the binding form per common activity property.

#### VB Expressions (`expressionLanguage: VisualBasic`)
Expressions use VB syntax with `[bracket]` shorthand (VB is the default deserialization target for brackets):
```xml
<InArgument x:TypeArguments="x:String">[firstName & " " & lastName]</InArgument>
```

**Check `project.json` `expressionLanguage` field to determine which syntax to use.**

### Resource Types (IResource / ILocalResource)

Some activity properties accept `IResource` or `ILocalResource` types instead of plain strings for file inputs. These are part of UiPath's resource abstraction model:

| Type | Description | When Used |
|------|-------------|-----------|
| `IResource` | Generic resource (local file, remote file, cloud attachment) | Activities that accept any file source |
| `ILocalResource` | Local file on disk (has `LocalPath` property) | Activities that need a file on the local filesystem |
| `IRemoteResource` | Remote resource with a URI and a local copy | Cloud/API-sourced files |

**In XAML**, resource-typed properties are set via expressions that create the resource — `LocalResource.FromPath(filePath)` or the Path Exists activity. Both approaches, the XAML forms, and the required `UiPath.Platform.ResourceHandling` namespace: [common-pitfalls.md § IResource / ILocalResource](common-pitfalls.md#iresource--ilocalresource--string-path-conversion).

**Activity Storage**: Some activities use a bucket-based storage system (`.storage/` folder in the project). Resources stored at design-time in `.storage/.runtime/<bucket>/` are packed into the published NuPkg and available at runtime. This is managed automatically — you don't need to edit storage resources directly in XAML.

## XAML Reference Examples

Complete workflow examples demonstrating proper XAML structure and patterns.

### Example 1: Basic Activities (LogMessage, If/Else, Assign)

VB project with core workflow activities. Shows If/Then/Else branching and Assign pattern.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Main"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
  xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib"
  xmlns:ui="http://schemas.uipath.com/workflow/activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <x:Members>
    <x:Property Name="isWeekend" Type="InArgument(x:String)" />
  </x:Members>
  <VisualBasic.Settings>
    <x:Null />
  </VisualBasic.Settings>
  <sap2010:WorkflowViewState.IdRef>ActivityBuilder_1</sap2010:WorkflowViewState.IdRef>
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String">
      <!-- Standard system namespaces -->
      <x:String>System</x:String>
      <x:String>System.Collections.Generic</x:String>
      <x:String>System.Linq</x:String>
      <x:String>UiPath.Core</x:String>
      <x:String>UiPath.Core.Activities</x:String>
      <!-- ... other standard imports ... -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <AssemblyReference>System</AssemblyReference>
      <AssemblyReference>System.Activities</AssemblyReference>
      <AssemblyReference>UiPath.System.Activities</AssemblyReference>
      <!-- ... other standard references ... -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:Boolean" Name="isWeekend" />
    </Sequence.Variables>
    <!-- LogMessage activity -->
    <ui:LogMessage DisplayName="Log Message" sap2010:WorkflowViewState.IdRef="LogMessage_1"
      Message="[DateTime.Now.ToString() + &quot; - Execution started&quot;]" />
    <!-- If/Then/Else with Assign activities -->
    <If Condition="[DateTime.Now.DayOfWeek = DayOfWeek.Saturday OrElse DateTime.Now.DayOfWeek = DayOfWeek.Sunday]"
      sap2010:WorkflowViewState.IdRef="If_1">
      <If.Then>
        <Sequence DisplayName="Then" sap2010:WorkflowViewState.IdRef="Sequence_2">
          <Assign sap2010:WorkflowViewState.IdRef="Assign_1">
            <Assign.To>
              <OutArgument x:TypeArguments="x:Boolean">[isWeekend]</OutArgument>
            </Assign.To>
            <Assign.Value>
              <InArgument x:TypeArguments="x:Boolean">[True]</InArgument>
            </Assign.Value>
          </Assign>
        </Sequence>
      </If.Then>
      <If.Else>
        <Sequence DisplayName="Else" sap2010:WorkflowViewState.IdRef="Sequence_3">
          <Assign sap2010:WorkflowViewState.IdRef="Assign_2">
            <Assign.To>
              <OutArgument x:TypeArguments="x:Boolean">[isWeekend]</OutArgument>
            </Assign.To>
            <Assign.Value>
              <InArgument x:TypeArguments="x:Boolean">[False]</InArgument>
            </Assign.Value>
          </Assign>
        </Sequence>
      </If.Else>
    </If>
  </Sequence>
</Activity>
```

**Key patterns:**
- `ui:LogMessage` uses `xmlns:ui="http://schemas.uipath.com/workflow/activities"`
- VB expressions: `OrElse` instead of `||`, no brackets on simple values
- `If.Then` and `If.Else` each wrap content in a `Sequence` — required, not optional. See [xaml-basics-and-rules.md § Container Activity Bodies — Wrap in Sequence](xaml-basics-and-rules.md#container-activity-bodies--wrap-in-sequence) for the full slot list
- `Assign` uses `Assign.To` (OutArgument) and `Assign.Value` (InArgument) with explicit `x:TypeArguments`

### Example 2: Package Connector Activity (Office 365 Get Newest Email)

Shows a package-based activity with `ConnectionId` for Integration Service.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="GetNewestEmail"
  VisualBasic.Settings="{x:Null}"
  sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"
  <!-- standard xmlns omitted — see Example 1 -->
  xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:umamm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Models;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <!-- Namespaces include package-specific imports -->
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String">
      <!-- Standard imports + package-specific -->
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Enums</x:String>
      <x:String>UiPath.MicrosoftOffice365.Models</x:String>
      <x:String>UiPath.Shared.Services.Graph.Mail.Models</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Filters</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Models</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail</x:String>
      <x:String>UiPath.Shared.Activities</x:String>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <!-- Standard refs + package-specific -->
      <AssemblyReference>UiPath.MicrosoftOffice365.Activities</AssemblyReference>
      <AssemblyReference>UiPath.MicrosoftOffice365</AssemblyReference>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <Sequence DisplayName="GetNewestEmail" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <!-- Activity with ConnectionId for Integration Service -->
    <umam:GetNewestEmail
      ConnectionAccountName="{x:Null}" ContinueOnError="{x:Null}" Filter="{x:Null}"
      FolderIdBackup="{x:Reference __ReferenceID0}" FreeTextFilter="{x:Null}"
      Mailbox="{x:Null}" MailboxBackup="{x:Reference __ReferenceID1}"
      ManualEntryFolder="{x:Null}" QueryFilter="{x:Null}" Result="{x:Null}"
      AuthScopesInvalid="False" BodyAsHtml="False"
      BrowserFolder="Inbox" BrowserFolderId="Inbox"
      ConnectionId="6265de1b-4264-ed11-ade6-e42aac668fcd"
      DisplayName="Get Newest Email"
      FilterSelectionMode="ConditionBuilder"
      sap2010:WorkflowViewState.IdRef="GetNewestEmail_1"
      Importance="Any" MarkAsRead="False" SelectionMode="Browse"
      UnreadOnly="False" UseConnectionService="True"
      UseSharedMailbox="False" WithAttachmentsOnly="False">
      <!-- Complex nested configuration objects (BackupSlot, MailFolderArgument, etc.) -->
      <umam:GetNewestEmail.MailFolderArgument>
        <umamm:MailFolderArgument ConnectionDescriptor="{x:Null}" ManualEntryFolder="{x:Null}"
          BrowserFolder="Inbox" BrowserFolderId="Inbox"
          ConnectionKey="d04f100e-8b4e-ec11-981f-e42aac66a34d"
          SelectionMode="Browse">
          <umamm:MailFolderArgument.Backup>
            <usau:BackupSlot x:TypeArguments="umame:ItemSelectionMode"
              x:Name="__ReferenceID0" StoredValue="Browse">
              <usau:BackupSlot.BackupValues>
                <scg:Dictionary x:TypeArguments="umame:ItemSelectionMode, scg:List(x:Object)" />
              </usau:BackupSlot.BackupValues>
            </usau:BackupSlot>
          </umamm:MailFolderArgument.Backup>
        </umamm:MailFolderArgument>
      </umam:GetNewestEmail.MailFolderArgument>
      <!-- GetNewestEmail.MailboxArg: analogous MailboxArgument with its own BackupSlot
           (x:Name="__ReferenceID1", x:TypeArguments="umame:MailboxSelectionMode") -->
    </umam:GetNewestEmail>
  </Sequence>
</Activity>
```

**Key patterns:**
- `ConnectionId` attribute holds the Integration Service connection GUID
- Nullable properties use `{x:Null}` explicitly
- Complex sub-objects (MailFolderArgument, MailboxArgument) with `BackupSlot` pattern
- `x:Reference` / `x:Name` for cross-referencing objects within the XAML
- Multiple package-specific xmlns prefixes (`umam`, `umame`, `umamm`, `usau`)

### Example 3: Integration Service `ConnectorActivity`

The generic IS `ConnectorActivity` pattern — activity shape, worked example, editing rules, JIT-generated assemblies: [../is-connector-xaml-guide.md](../is-connector-xaml-guide.md).

