# Common Pattern Card

**Package anchors:** `UiPath.System.Activities` 26.6.1 · `UiPath.WebAPI.Activities` 2.5.1. Every entry is CLI-verified (`uip rpa validate` + `uip rpa build` clean) on a `Portable` VB project; Windows-target projects use the same assemblies (`System.Private.CoreLib`); Legacy (.NET 4.6.1) is not covered.

**Not on this card — full Rule 21 triple:** Windows-only Excel X activities (`ExcelProcessScopeX`/`ExcelApplicationCard`/`ReadRangeX`, …) and SMTP `SendMail` (`TypeLoadException` on cross-platform assemblies), queue publish (`AddQueueItem`), CSV read/write (`ReadCsvFile`/`AppendWriteCsvFile`).

These snippets supersede Rule 21 discovery for every activity in a listed pattern ([maintenance](../.maintenance/pattern-card-maintenance.md)); otherwise use Rule 21. A hit skips discovery, not the `validate`+`build` gate or the observable-output run check ([execution-maps-guide.md § Gate ≠ runtime proof](execution-maps-guide.md#gate--runtime-proof)). Precedence: card → agent memory → Rule 21 triple. If `validate`/`build` rejects a snippet, fall back to the Rule 21 triple for that activity and report the stale entry via `/uipath-feedback`.

## Card entries

Text file read/append/write · File ops guarded copy · DataTable generate→filter→CSV text · Retry wrap · Invoke workflow with arguments · Invoke Code bulk row processing · HTTP request → JSON

## How to read the snippets

Each snippet is a complete fragment (with `Variables`) for a root matching scaffolded `Main.xaml` (`uip rpa init`; keep its `TextExpression` blocks) plus these prefixes:

```xml
xmlns:ui="http://schemas.uipath.com/workflow/activities"
xmlns:uic="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
xmlns:nhr="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
xmlns:nhrm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"
xmlns:jn="clr-namespace:Newtonsoft.Json.Linq;assembly=Newtonsoft.Json"
```

Add IdRefs per [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) Rule 25. Snippets are VB (`[expr]`); for C# see [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md). DataTable activities need `uic:` (not registered under the `ui:` URI cross-platform); file, retry, invoke use `ui:`.

### Text file read / append / write

**Activities:** `UiPath.Core.Activities.ReadTextFile` · `AppendLine` · `WriteTextFile`

```xml
<Sequence DisplayName="Text File Read Append Write"><Sequence.Variables><Variable x:TypeArguments="x:String" Name="fileContent" /><Variable x:TypeArguments="x:String" Name="logEntry" Default="processed" /></Sequence.Variables><ui:ReadTextFile DisplayName="Read Text File" FileName="data/input.txt" Encoding="utf-8" Content="[fileContent]" /><ui:AppendLine DisplayName="Append Line" FileName="data/process.log" Text="[logEntry]" Encoding="utf-8" /><ui:WriteTextFile DisplayName="Write Text File" FileName="data/output.txt" Text="[fileContent]" Encoding="utf-8" /></Sequence>
```

`WriteTextFile` overwrites; `AppendLine` appends, creating a missing file. Null `Encoding` = auto-detect on read, system default on write. **Explicit `Encoding="utf-8"` on `WriteTextFile` writes a UTF-8 BOM (`EF BB BF`)**: it passes `validate`+`build` but breaks byte-exact consumers — omit `Encoding` for BOM-less output ([xaml/common-pitfalls.md § WriteTextFile Emits a UTF-8 BOM](xaml/common-pitfalls.md#writetextfile-emits-a-utf-8-bom-when-encoding-is-set)).

### File ops — guarded copy

**Activities:** `UiPath.Core.Activities.PathExists` · `CreateDirectory` · `CopyFile` (+ built-in `If`)

```xml
<Sequence DisplayName="File Ops Guarded Copy"><Sequence.Variables><Variable x:TypeArguments="x:Boolean" Name="fileExists" /></Sequence.Variables><ui:PathExists DisplayName="Get Local File or Folder" Path="data/report.pdf" PathType="File" Exists="[fileExists]" /><If DisplayName="If file exists"><If.Condition><InArgument x:TypeArguments="x:Boolean"><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="fileExists" /></InArgument></If.Condition><If.Then><Sequence DisplayName="Archive file"><ui:CreateDirectory DisplayName="Create Folder" Path="archive" /><ui:CopyFile DisplayName="Copy File" Path="data/report.pdf" Destination="archive/report.pdf" Overwrite="True" /></Sequence></If.Then></If></Sequence>
```

`PathType="File"` gives `Exists=False` for a directory. `CreateDirectory` is idempotent, creates intermediates. Copying into an existing folder keeps the name; a full-file destination needs its parent. `MoveFile`/`Delete` take the same `Path`.

### DataTable — generate → add row → filter → CSV text

**Activities:** `UiPath.Core.Activities.GenerateDataTable` · `AddDataRow` · `FilterDataTable` · `OutputDataTable`

```xml
<Sequence DisplayName="DataTable Build Filter Output"><Sequence.Variables><Variable x:TypeArguments="sd:DataTable" Name="dt" /><Variable x:TypeArguments="sd:DataTable" Name="filteredDt" /><Variable x:TypeArguments="x:String" Name="csvText" /></Sequence.Variables><uic:GenerateDataTable DisplayName="Generate Data Table From Text" AutoDetectTypes="True" UseColumnHeader="True" CSVParsing="True"><uic:GenerateDataTable.Input><InArgument x:TypeArguments="x:String">["Name,Age" &amp; vbLf &amp; "Bob,25"]</InArgument></uic:GenerateDataTable.Input><uic:GenerateDataTable.DataTable><OutArgument x:TypeArguments="sd:DataTable">[dt]</OutArgument></uic:GenerateDataTable.DataTable></uic:GenerateDataTable><uic:AddDataRow DisplayName="Add Data Row"><uic:AddDataRow.DataTable><InOutArgument x:TypeArguments="sd:DataTable">[dt]</InOutArgument></uic:AddDataRow.DataTable><uic:AddDataRow.ArrayRow><InArgument x:TypeArguments="s:Object[]">[New Object() {"Alice", 30}]</InArgument></uic:AddDataRow.ArrayRow></uic:AddDataRow><uic:FilterDataTable DisplayName="Filter Data Table" FilterRowsMode="Keep" OutputDataTable="[filteredDt]"><uic:FilterDataTable.DataTable><InArgument x:TypeArguments="sd:DataTable">[dt]</InArgument></uic:FilterDataTable.DataTable><uic:FilterDataTable.Filters><scg:List x:TypeArguments="uic:FilterOperationArgument"><uic:FilterOperationArgument Operator="GT" BooleanOperator="And"><uic:FilterOperationArgument.Column><InArgument x:TypeArguments="x:String">"Age"</InArgument></uic:FilterOperationArgument.Column><uic:FilterOperationArgument.Operand><InArgument x:TypeArguments="x:Int32">[10]</InArgument></uic:FilterOperationArgument.Operand></uic:FilterOperationArgument></scg:List></uic:FilterDataTable.Filters></uic:FilterDataTable><uic:OutputDataTable DisplayName="Output Data Table as Text"><uic:OutputDataTable.DataTable><InArgument x:TypeArguments="sd:DataTable">[filteredDt]</InArgument></uic:OutputDataTable.DataTable><uic:OutputDataTable.Text><OutArgument x:TypeArguments="x:String">[csvText]</OutArgument></uic:OutputDataTable.Text></uic:OutputDataTable></Sequence>
```

Traps: `BuildDataTable` does NOT load on cross-platform projects (`TypeLoadException`) — generate from CSV text instead. The runtime member is `CSVParsing="True"` (`ParsingMethod`/`CSV` are designer-only). `ArrayRow` is `s:Object[]`, never `x:Object[]` ([common-pitfalls.md § `x:` prefix](xaml/common-pitfalls.md#invalid-use-of-x-prefix-for-non-builtin-clr-types)). `Operator` takes enum identifiers (`GT`, `EQ`, `CONTAINS`, …); omit `Operand` for `EMPTY`/`NOTEMPTY`. `AddDataRow.DataTable` is `InOutArgument`: bind a variable, never an expression.

### Retry wrap

**Activities:** `UiPath.Core.Activities.RetryScope`

```xml
<ui:RetryScope DisplayName="Retry Scope"><ui:RetryScope.NumberOfRetries><InArgument x:TypeArguments="x:Int32"><VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="3" /></InArgument></ui:RetryScope.NumberOfRetries><ui:RetryScope.RetryInterval><InArgument x:TypeArguments="s:TimeSpan"><VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" /></InArgument></ui:RetryScope.RetryInterval><ui:RetryScope.ActivityBody><ActivityAction><Sequence DisplayName="Action"><ui:ReadTextFile DisplayName="Read flaky source" FileName="data/flaky-source.txt" Content="[fetchedContent]" /></Sequence></ActivityAction></ui:RetryScope.ActivityBody><ui:RetryScope.Condition><ActivityFunc x:TypeArguments="x:Boolean" /></ui:RetryScope.Condition></ui:RetryScope>
```

Body goes in `ActivityBody`/`ActivityAction`, not a bare child. An empty `Condition` `ActivityFunc` retries on exception only; to retry until true, put an `Activity(Of Boolean)` inside it. (`fetchedContent` is a `String` variable.)

### Invoke workflow with arguments

**Activities:** `UiPath.Core.Activities.InvokeWorkflowFile` · **Variables:** `childResult : String`.

```xml
<ui:InvokeWorkflowFile DisplayName="Invoke Workflow File" WorkflowFileName="Pattern_Child.xaml"><ui:InvokeWorkflowFile.Arguments><InArgument x:TypeArguments="x:String" x:Key="in_Message">["hello"]</InArgument><OutArgument x:TypeArguments="x:String" x:Key="out_Result">[childResult]</OutArgument></ui:InvokeWorkflowFile.Arguments></ui:InvokeWorkflowFile>
```

Declare the child contract in its root `x:Members`:

```xml
<x:Members><x:Property Name="in_Message" Type="InArgument(x:String)" /><x:Property Name="out_Result" Type="OutArgument(x:String)" /></x:Members>
```

Keys must exactly match the declared argument names, with the matching `InArgument`/`OutArgument`/`InOutArgument` direction. Synchronous; `WorkflowFileName` is project-relative. XML-escape VB `&` as `&amp;`.

### Invoke Code — bulk row processing

**Activities:** `UiPath.Core.Activities.InvokeCode` (input from the [DataTable entry](#datatable--generate--add-row--filter--csv-text)) · **Verified:** 26.6.2 validate + build + **run** (silent-no-op activity: the gate alone is not proof) · **Variables:** `dt : System.Data.DataTable`; `validCount : Int32`; `totalAmount : Double`.

```xml
<ui:InvokeCode DisplayName="Process Rows" Language="VBNet" Code="For Each row As System.Data.DataRow In rows.Rows&#xA;  Dim amount As Double&#xA;  If Double.TryParse(row(&quot;Amount&quot;).ToString(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, amount) AndAlso amount &gt; 0 Then&#xA;    validCount += 1&#xA;    totalAmount += amount&#xA;  End If&#xA;Next"><ui:InvokeCode.Arguments><scg:Dictionary x:TypeArguments="x:String, Argument"><InArgument x:TypeArguments="sd:DataTable" x:Key="rows">[dt]</InArgument><OutArgument x:TypeArguments="x:Int32" x:Key="validCount">[validCount]</OutArgument><OutArgument x:TypeArguments="x:Double" x:Key="totalAmount">[totalAmount]</OutArgument></scg:Dictionary></ui:InvokeCode.Arguments></ui:InvokeCode>
```

Use as the default escalation for complex bulk row processing (per-row parse + validate + branch + accumulate; [data-manipulation-guide.md § Code vs activity chains](data-manipulation-guide.md)); a `ForEach` with ONE `If`/`Switch` stays plain XAML. Traps: `Code` MUST be an XML **attribute** (`&#xA;` newlines, `&quot;` quotes) — child/CDATA `<ui:InvokeCode.Code>` loses line breaks (a C# `//` comment swallows later code; VB fails to compile) ([§ InvokeCode Code Property](xaml/common-pitfalls.md#invokecode-code-property--attribute-form-only)). Set `Language` (`CSharp` in C# projects, `VBNet` in VB); without it code compiles as VB.NET ([§ InvokeCode Language Property](xaml/common-pitfalls.md#invokecode-language-property)). Keys must match code identifiers; bind variables, never expressions, to `OutArgument`s. Parse with `InvariantCulture` (bare `Double.TryParse` silently rejects `10.5` under a comma-decimal locale).

### HTTP request → JSON

**Activities:** `UiPath.Web.Activities.Http.NetHttpRequest` · `UiPath.Web.Activities.DeserializeJson<T>`

```xml
<Sequence DisplayName="HTTP GET Deserialize"><Sequence.Variables><Variable x:TypeArguments="nhrm:HttpResponseSummary" Name="httpResponse" /><Variable x:TypeArguments="jn:JObject" Name="jsonResult" /></Sequence.Variables><nhr:NetHttpRequest DisplayName="GET API Data" RequestUrl="https://api.example.com/data" Method="GET" RequestBodyType="None" RetryPolicyType="Basic" RetryCount="[3]" TimeoutInMiliseconds="[10000]" Result="[httpResponse]" /><web:DeserializeJson x:TypeArguments="jn:JObject" DisplayName="Deserialize JSON" JsonString="[httpResponse.TextContent]" JsonObject="[jsonResult]" /></Sequence>
```

**Use `NetHttpRequest`, not legacy `HttpClient`.** The XAML assembly is `UiPath.Web.Activities`, not the package id `UiPath.WebAPI.Activities`; `HttpResponseSummary` is in `...Http.Models`. Body: `httpResponse.TextContent`; status: `httpResponse.StatusCode`. Default `ContinueOnError=True` turns network failures into synthetic `503` responses — guard on `StatusCode` before parsing. POST JSON: `RequestBodyType="Text"` + `TextPayload` (content type defaults to `application/json`).
