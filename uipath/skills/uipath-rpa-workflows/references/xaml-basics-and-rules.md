# XAML Basics and Rules

Core concepts for UiPath workflow XAML files and rules for generating and/or editing XAML content.

## XAML File Anatomy

Every UiPath XAML workflow file has this structure:

```xml
<Activity mc:Ignorable="sap sap2010 sads" x:Class="ProjectName.FileName"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:sads="http://schemas.microsoft.com/netfx/2010/xaml/activities/debugger"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  <!-- Additional xmlns for activity packages -->
  >

  <!-- TextExpression.NamespacesForImplementation (C# imports) -->
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <x:String>System</x:String>
      <x:String>System.Collections.Generic</x:String>
      <x:String>System.Linq</x:String>
      <!-- More namespace imports -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>

  <!-- TextExpression.ReferencesForImplementation (assembly references) -->
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <AssemblyReference>System</AssemblyReference>
      <!-- More assembly references -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>

  <!-- x:Members (arguments) -->
  <x:Members>
    <x:Property Name="in_Name" Type="InArgument(x:String)" />
    <x:Property Name="out_Result" Type="OutArgument(x:Int32)" />
    <x:Property Name="io_Data" Type="InOutArgument(x:String)" />
  </x:Members>

  <!-- Main workflow body -->
  <Sequence DisplayName="Main Sequence">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="tempVar" Default="hello" />
    </Sequence.Variables>
    <!-- Activities go here -->
  </Sequence>

  <!-- ViewState (designer metadata - DO NOT EDIT) -->
  <sap2010:WorkflowViewState.ViewStateManager>
    <!-- ... -->
  </sap2010:WorkflowViewState.ViewStateManager>
</Activity>
```

## Workflow Types

### Sequence
Linear, step-by-step execution. Best for straightforward processes.
```xml
<Sequence DisplayName="My Sequence">
  <!-- Activities execute top to bottom -->
</Sequence>
```

### Flowchart
Branching logic with decision nodes. Best for complex decision flows.
```xml
<Flowchart DisplayName="My Flowchart">
  <Flowchart.StartNode>
    <FlowStep x:Name="__ReferenceID0">
      <!-- Start activity and connections -->
    </FlowStep>
  </Flowchart.StartNode>
  <!-- FlowStep, FlowDecision, FlowSwitch nodes -->
</Flowchart>
```

### State Machine
State-based workflow with transitions. Best for long-running processes with distinct states.
```xml
<StateMachine DisplayName="My State Machine">
  <StateMachine.States>
    <State DisplayName="Initial State">
      <State.Transitions>
        <Transition DisplayName="To Next" To="{x:Reference __ReferenceID1}" />
      </State.Transitions>
    </State>
  </StateMachine.States>
</StateMachine>
```

## XAML Safety Rules

Critical rules to follow when editing XAML files to prevent validation errors and workflow corruption.

### NEVER Touch ViewState
The `<sap2010:WorkflowViewState.ViewStateManager>` section contains designer layout metadata. **Never modify it.** UiPath Studio manages this automatically. Corrupting ViewState can break the workflow in the visual designer.

### Preserve xmlns Declarations
Never remove existing `xmlns` attributes from the root `<Activity>` element. Only add new ones as needed. Removing a namespace declaration that is referenced anywhere in the file will cause validation errors.

### Respect Expression Language
Always check the project's expression language before writing expressions:
- **CSharp**: Use C# syntax (`+` for string concat, `==` for equality)
- **VB**: Use VB syntax (`&` for string concat, `=` for equality)

Mixing expression languages causes build failures.

### Use `uipcli rpa get-default-activity-xaml` Output
Never construct activity XAML from memory. The `uipcli rpa get-default-activity-xaml` command returns the exact XAML needed for the installed package version, including:
- Correct element names and namespaces
- Required properties and their types
- Default values
- Assembly references to add

Use `uipcli rpa find-activities` to find the activity's fully qualified class name, type ID, and `isDynamicActivity` flag. Then use `uipcli rpa get-default-activity-xaml` with the appropriate parameters.

Use `uipcli rpa list-workflow-examples` and `uipcli rpa get-workflow-example` to see example usages of the given activity, in addition to searching existing local `.xaml` files.

### Preserve Existing Structure
When editing XAML:
- Do not reformat or re-indent the entire file
- Only modify the specific section you need to change
- Use the `Edit` tool for targeted replacements (match exact `old_string`, replace with `new_string`)

### Validate After Every Change
Run `uipcli rpa get-errors` after every XAML modification. Do not batch multiple edits without validation — catching errors early is much easier than debugging compound issues.

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

#### C# Projects (default)
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

#### VB Projects
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

**In XAML**, resource-typed properties are typically set via expressions that create the resource:
```xml
<!-- LocalResource from a file path (C# expression) -->
<InArgument x:TypeArguments="upr:ILocalResource">
  <CSharpValue x:TypeArguments="upr:ILocalResource">LocalResource.FromPath(filePath)</CSharpValue>
</InArgument>
```

Required namespace for resource types:
```xml
<x:String>UiPath.Platform.ResourceHandling</x:String>
```

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
- `If.Then` and `If.Else` each wrap content in a `Sequence`
- `Assign` uses `Assign.To` (OutArgument) and `Assign.Value` (InArgument) with explicit `x:TypeArguments`

### Example 2: Package Connector Activity (Office 365 Get Newest Email)

Shows a package-based activity with `ConnectionId` for Integration Service.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="GetNewestEmail"
  VisualBasic.Settings="{x:Null}"
  sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
  xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib"
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
      <umam:GetNewestEmail.MailboxArg>
        <umamm:MailboxArgument SharedMailbox="{x:Null}" UseSharedMailbox="False">
          <umamm:MailboxArgument.Backup>
            <usau:BackupSlot x:TypeArguments="umame:MailboxSelectionMode"
              x:Name="__ReferenceID1" StoredValue="NoMailbox">
              <usau:BackupSlot.BackupValues>
                <scg:Dictionary x:TypeArguments="umame:MailboxSelectionMode, scg:List(x:Object)" />
              </usau:BackupSlot.BackupValues>
            </usau:BackupSlot>
          </umamm:MailboxArgument.Backup>
        </umamm:MailboxArgument>
      </umam:GetNewestEmail.MailboxArg>
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

### Example 3: Integration Service Connector Activity (GitHub Search Repositories)

Shows the generic `ConnectorActivity` pattern used for Integration Service connectors.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Sequence"
  VisualBasic.Settings="{x:Null}"
  sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:isactr="http://schemas.uipath.com/workflow/integration-service-activities/isactr"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
  xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib"
  xmlns:uiascb="clr-namespace:UiPath.IntegrationService.Activities.SWEntities.CDF573A04A6_search_repositories.Bundle;assembly=CDF573A04A6_search_r.VeKd1XI2qK1X56UO2Br3Ui3"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <!-- Namespaces include Integration Service runtime + connector-specific -->
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String">
      <!-- Standard imports + IS-specific -->
      <x:String>UiPath.IntegrationService.Activities.Runtime.Models.FilterBuilder</x:String>
      <x:String>UiPath.IntegrationService.Activities.Runtime.Models</x:String>
      <x:String>UiPath.IntegrationService.Activities.Runtime.Helpers.TypeDetailsCustomization</x:String>
      <x:String>UiPath.IntegrationService.Activities.Runtime.Activities</x:String>
      <x:String>UiPath.Platform.Activities</x:String>
      <x:String>UiPath.IntegrationService.Activities.SWEntities.CDF573A04A6_search_repositories.Bundle</x:String>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <!-- Standard refs + IS-specific -->
      <AssemblyReference>UiPath.IntegrationService.Activities.Runtime</AssemblyReference>
      <AssemblyReference>UiPath.Platform</AssemblyReference>
      <AssemblyReference>CDF573A04A6_search_r.VeKd1XI2qK1X56UO2Br3Ui3</AssemblyReference>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <Sequence DisplayName="Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <!-- Generic ConnectorActivity for Integration Service -->
    <isactr:ConnectorActivity
      Configuration="H4sIAAAAAAAACr1W70/bSBD9V1b+dCcFXwgtPSHx..."
      ConnectionId="93c89540-f260-4150-afbd-43df573a04a6"
      DisplayName="Search Repositories"
      sap2010:WorkflowViewState.IdRef="ConnectorActivity_2"
      UiPathActivityTypeId="f340077e-3684-33c4-b956-b9aa7eb0ea7c">
      <isactr:ConnectorActivity.FieldObjects>
        <!-- Input field -->
        <isactr:FieldObject Name="query" Type="FieldArgument">
          <isactr:FieldObject.Value>
            <InArgument x:TypeArguments="x:String">in:name (a* OR b* OR c*)</InArgument>
          </isactr:FieldObject.Value>
        </isactr:FieldObject>
        <!-- Output field (typed array from generated assembly) -->
        <isactr:FieldObject Name="Jit_search_repositories" Type="FieldArgument">
          <isactr:FieldObject.Value>
            <OutArgument x:TypeArguments="uiascb:search_repositories[]" />
          </isactr:FieldObject.Value>
        </isactr:FieldObject>
        <!-- Optional fields (no value set) -->
        <isactr:FieldObject Name="sort" Type="FieldArgument" />
        <isactr:FieldObject Name="order" Type="FieldArgument" />
      </isactr:ConnectorActivity.FieldObjects>
    </isactr:ConnectorActivity>
  </Sequence>
</Activity>
```

**Key patterns:**
- `isactr:ConnectorActivity` is the generic IS activity type (`xmlns:isactr="http://schemas.uipath.com/workflow/integration-service-activities/isactr"`)
- `Configuration` holds a base64-encoded GZip-compressed blob — **never construct this manually**, it comes from `uipcli rpa get-default-activity-xaml`
- `ConnectionId` is the Integration Service connection GUID
- `UiPathActivityTypeId` identifies the specific connector operation
- `FieldObjects` define input/output fields with `isactr:FieldObject` elements
- Output types reference a JIT-generated assembly (e.g., `CDF573A04A6_search_r.VeKd1XI2qK1X56UO2Br3Ui3`)
- The generated assembly name and namespace imports are connector-specific — always use `uipcli rpa get-default-activity-xaml` output

## Property Binding: Attributes vs Child Elements

XAML properties can be set in two ways: as XML attributes or as child elements. Both are valid XAML, but some properties only work reliably in one form.

### Attribute Syntax (Inline)
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```

### Child Element Syntax (Property Element)
```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result>
    <OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument>
  </ui:SomeActivity.Result>
</ui:SomeActivity>
```

### When to Use Which

**Simple values** (strings, enums, booleans, VB expressions in brackets) almost always work as attributes:
```xml
DisplayName="My Activity" Message="[variable]" Level="Info"
```

**Output properties** (`OutArgument`, `Result`) may require child element syntax. Some activities accept `Result="[var]"` as an attribute; others only work with the expanded child element form. If an attribute-form output binding causes a validation error, try the child element form.

**Complex objects** (BackupSlot, MailboxArgument, ActivityAction, dictionaries) always require child element syntax — they cannot be expressed as a single attribute value.

### Version-Sensitive Properties

Properties may exist in one package version but not another. If `get-errors` reports "Could not find member 'PropertyName'":
1. The property may not exist in the installed package version — remove it
2. The property may have been renamed between versions — check examples from the same package version
3. Use `uipcli rpa get-default-activity-xaml` output as the authoritative set of properties for the installed version

## ConnectorActivity Internals

Understanding the structure of `isactr:ConnectorActivity` so you know what you can and cannot edit.

### Properties (What They Are)

| Property | Editable? | Description |
|----------|-----------|-------------|
| `Configuration` | **NEVER** | ZIP-compressed, Base64-encoded JSON blob containing the full activity schema (fields, types, connector metadata). This is obtained and computed for you using the `uipcli rpa get-default-activity-xaml` command. Do not parse, modify, or construct manually. |
| `ConnectionId` | Yes (replace GUID) | Integration Service connection GUID. Use `uipcli is connections list [connector-key]` to discover available connections and their IDs. |
| `UiPathActivityTypeId` | **NEVER** | Identifies the specific connector operation. Obtain using `uipcli rpa get-default-activity-xaml` or `uipcli rpa find-activities`. |
| `DisplayName` | Yes | Human-readable activity name for the designer. |

### FieldObjects (Input/Output Interface)

`FieldObjects` is the collection of input and output fields. Each `isactr:FieldObject` has:

| Attribute | Description |
|-----------|-------------|
| `Name` | Field identifier (maps to the connector API parameter). Must match exactly what `uipcli rpa get-default-activity-xaml` returns. |
| `Type` | One of: `FieldArgument` (contains an Activity Argument), `FieldLiteral` (contains a literal value), `FilterTreeValue` (filter builder criteria), `None` (empty). |

**What you CAN edit in FieldObjects:**
- **Input field values**: Change the `InArgument` value inside a `FieldObject.Value` to set different input data (e.g., change a search query string).
- **Bind to variables**: Replace a literal value with a variable reference using `<CSharpValue>` (e.g., `<CSharpValue x:TypeArguments="x:String">myVariable</CSharpValue>`).

**What you CANNOT edit:**
- Field `Name` values — these must match the connector API schema exactly.
- Field `Type` values — these are determined by the connector metadata.
- Output field structure — the `OutArgument` types reference JIT-generated assemblies.
- Adding/removing FieldObjects — the set of fields comes from `uipcli rpa get-default-activity-xaml`.

### JIT-Generated Assemblies

Output fields often use types from JIT-compiled assemblies with hashed names:
```
CDF573A04A6_search_r.VeKd1XI2qK1X56UO2Br3Ui3
^connection(last10)   ^operation   ^content hash
```

These assembly names are:
- **Unpredictable** — derived from SHA-512 hashes of the type schema
- **Connection-specific** — different connections produce different hashes
- **Generated by the runtime** — you cannot create or reference them without `uipcli rpa get-default-activity-xaml`

The corresponding namespace imports and assembly references MUST come from `uipcli rpa get-default-activity-xaml` output. Never construct them.

### What `uipcli rpa get-default-activity-xaml` Returns for Dynamic Activities

When you call `uipcli rpa get-default-activity-xaml` with `isDynamicActivity: true`, it returns everything needed:
1. The complete `<isactr:ConnectorActivity>` XAML element with `Configuration` blob, `UiPathActivityTypeId`, and `FieldObjects`
2. All required `xmlns` declarations for the root `<Activity>` element
3. All required namespace imports and references

Use this output as-is. The only things you should modify are:
- `DisplayName` — set a meaningful name
- `ConnectionId` — if swapping to a different connection of the same connector type
- Input `FieldObject` values — to set the actual data for your workflow
