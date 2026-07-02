# Common Pattern Card

**Package anchors:** `UiPath.System.Activities` 26.6.1 · `UiPath.Excel.Activities` 3.6.0-preview (CSV group) · `UiPath.WebAPI.Activities` 2.5.1 — every entry CLI-verified (`uip rpa validate` + `uip rpa build` clean) on a `Portable` (cross-platform) / VisualBasic project. Modern Windows-target projects use the same assembly names (`System.Private.CoreLib`); Legacy (.NET 4.6.1) projects are NOT covered.

**Not on this card (Windows-only, unverifiable on the cross-platform gate):** Excel X activities (`ExcelProcessScopeX`/`ExcelApplicationCard`/`ReadRangeX`, …) and SMTP `SendMail` — their docs state `Platform: Windows only`; cross-platform assemblies throw `TypeLoadException`. Author via the full Rule 21 triple on a Windows-target project.

Copy-safe multi-activity snippets. **Supersedes the Rule 21 discovery procedure for every activity inside a listed pattern.** For activities outside these patterns, Rule 21 applies. Precedence: card → agent memory → Rule 21 triple ([execution-maps-guide.md](execution-maps-guide.md)). If `validate`/`build` rejects a card snippet: fall back to the Rule 21 triple for that activity and report the stale entry via `/uipath-feedback`.

## Card entries

Text file read/append/write · File ops guarded copy · DataTable generate→filter→CSV · Queue publish · Retry wrap · Invoke workflow with arguments · CSV file read/write · HTTP request → JSON

## How to read the snippets

Snippets are complete `<Sequence>` fragments (with their `Variables`) for a root `<Activity>` whose xmlns set matches the scaffolded `Main.xaml` (`uip rpa init` output) — keep its `TextExpression.NamespacesForImplementation` / `ReferencesForImplementation` blocks. Root prefixes used below:

```xml
xmlns:ui="http://schemas.uipath.com/workflow/activities"
xmlns:uic="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
xmlns:csv="clr-namespace:UiPath.CSV.Activities;assembly=UiPath.Excel.Activities"
xmlns:nhr="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
xmlns:nhrm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"
xmlns:jn="clr-namespace:Newtonsoft.Json.Linq;assembly=Newtonsoft.Json"
```

Each entry lists which of these it needs. VB expression form (`[expr]` attributes); C# projects: [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

> **Why two UiPath prefixes:** some activities (`BuildDataTable` — Windows-only, and by extension the DataTable group) are not registered under the `http://schemas.uipath.com/workflow/activities` URI on cross-platform assemblies. The `uic:` clr-namespace form resolves whenever the type is loadable. File/queue/retry/invoke activities verified fine under `ui:`.

---

### Text file read / append / write
**Activities:** `UiPath.Core.Activities.ReadTextFile` · `AppendLine` · `WriteTextFile`
**Prefixes:** `ui:`
**Variables:** `fileContent : String` — file text; `logEntry : String` — line to append.

```xml
<Sequence DisplayName="Text File Read Append Write">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="fileContent" />
    <Variable x:TypeArguments="x:String" Name="logEntry" Default="processed" />
  </Sequence.Variables>
  <ui:ReadTextFile DisplayName="Read Text File" FileName="data/input.txt" Encoding="utf-8" Content="[fileContent]" />
  <ui:AppendLine DisplayName="Append Line" FileName="data/process.log" Text="[logEntry]" Encoding="utf-8" />
  <ui:WriteTextFile DisplayName="Write Text File" FileName="data/output.txt" Text="[fileContent]" Encoding="utf-8" />
</Sequence>
```

**Notes:** `WriteTextFile` overwrites; `AppendLine` preserves content and creates the file if missing. `Encoding` `null` = auto-detect (read) / system default (write). `FileName` literal or `[expr]`.
**Long-form:** [`ReadTextFile.md`](activity-docs/UiPath.System.Activities/26.4/activities/ReadTextFile.md) · [`WriteTextFile.md`](activity-docs/UiPath.System.Activities/26.4/activities/WriteTextFile.md) · AppendLine: `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/activities/AppendLine.md`

---

### File ops — guarded copy
**Activities:** `UiPath.Core.Activities.PathExists` · `CreateDirectory` · `CopyFile` (+ built-in `If`)
**Prefixes:** `ui:`
**Variables:** `fileExists : Boolean`.

```xml
<Sequence DisplayName="File Ops Guarded Copy">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:Boolean" Name="fileExists" />
  </Sequence.Variables>
  <ui:PathExists DisplayName="Get Local File or Folder" Path="data/report.pdf" PathType="File" Exists="[fileExists]" />
  <If DisplayName="If file exists">
    <If.Condition>
      <InArgument x:TypeArguments="x:Boolean">
        <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="fileExists" />
      </InArgument>
    </If.Condition>
    <If.Then>
      <Sequence DisplayName="Archive file">
        <ui:CreateDirectory DisplayName="Create Folder" Path="archive" />
        <ui:CopyFile DisplayName="Copy File" Path="data/report.pdf" Destination="archive/report.pdf" Overwrite="True" />
      </Sequence>
    </If.Then>
  </If>
</Sequence>
```

**Notes:** `PathType="File"` makes a directory at that path return `Exists=False`. `CreateDirectory` is idempotent and creates intermediate dirs. `CopyFile` into an existing folder keeps the name; a full-file destination requires the parent to exist. `MoveFile`/`Delete` share the same `Path` shape.
**Long-form:** [`PathExists.md`](activity-docs/UiPath.System.Activities/26.4/activities/PathExists.md) · [`CopyFile.md`](activity-docs/UiPath.System.Activities/26.4/activities/CopyFile.md) · [`CreateDirectory.md`](activity-docs/UiPath.System.Activities/26.4/activities/CreateDirectory.md)

---

### DataTable — generate → add row → filter → CSV text
**Activities:** `UiPath.Core.Activities.GenerateDataTable` · `AddDataRow` · `FilterDataTable` · `OutputDataTable`
**Prefixes:** `uic:`, `sd:`, `scg:`, `s:`
**Variables:** `dt, filteredDt : System.Data.DataTable`; `csvText : String`.

```xml
<Sequence DisplayName="DataTable Build Filter Output">
  <Sequence.Variables>
    <Variable x:TypeArguments="sd:DataTable" Name="dt" />
    <Variable x:TypeArguments="sd:DataTable" Name="filteredDt" />
    <Variable x:TypeArguments="x:String" Name="csvText" />
  </Sequence.Variables>
  <uic:GenerateDataTable DisplayName="Generate Data Table From Text" AutoDetectTypes="True" UseColumnHeader="True" CSVParsing="True">
    <uic:GenerateDataTable.Input>
      <InArgument x:TypeArguments="x:String">["Name,Age" &amp; vbLf &amp; "Bob,25"]</InArgument>
    </uic:GenerateDataTable.Input>
    <uic:GenerateDataTable.DataTable>
      <OutArgument x:TypeArguments="sd:DataTable">[dt]</OutArgument>
    </uic:GenerateDataTable.DataTable>
  </uic:GenerateDataTable>
  <uic:AddDataRow DisplayName="Add Data Row">
    <uic:AddDataRow.DataTable>
      <InOutArgument x:TypeArguments="sd:DataTable">[dt]</InOutArgument>
    </uic:AddDataRow.DataTable>
    <uic:AddDataRow.ArrayRow>
      <InArgument x:TypeArguments="s:Object[]">[New Object() {"Alice", 30}]</InArgument>
    </uic:AddDataRow.ArrayRow>
  </uic:AddDataRow>
  <uic:FilterDataTable DisplayName="Filter Data Table" FilterRowsMode="Keep" OutputDataTable="[filteredDt]">
    <uic:FilterDataTable.DataTable>
      <InArgument x:TypeArguments="sd:DataTable">[dt]</InArgument>
    </uic:FilterDataTable.DataTable>
    <uic:FilterDataTable.Filters>
      <scg:List x:TypeArguments="uic:FilterOperationArgument">
        <uic:FilterOperationArgument Operator="GT" BooleanOperator="And">
          <uic:FilterOperationArgument.Column>
            <InArgument x:TypeArguments="x:String">"Age"</InArgument>
          </uic:FilterOperationArgument.Column>
          <uic:FilterOperationArgument.Operand>
            <InArgument x:TypeArguments="x:Int32">[10]</InArgument>
          </uic:FilterOperationArgument.Operand>
        </uic:FilterOperationArgument>
      </scg:List>
    </uic:FilterDataTable.Filters>
  </uic:FilterDataTable>
  <uic:OutputDataTable DisplayName="Output Data Table as Text">
    <uic:OutputDataTable.DataTable>
      <InArgument x:TypeArguments="sd:DataTable">[filteredDt]</InArgument>
    </uic:OutputDataTable.DataTable>
    <uic:OutputDataTable.Text>
      <OutArgument x:TypeArguments="x:String">[csvText]</OutArgument>
    </uic:OutputDataTable.Text>
  </uic:OutputDataTable>
</Sequence>
```

**Notes (build-verified traps):** `BuildDataTable` does NOT load on cross-platform projects (`TypeLoadException`) — generate from CSV text instead. `ParsingMethod`/`CSV` from the docs is designer-only; the runtime member is `CSVParsing="True"`. `ArrayRow` type argument must be `s:Object[]` — `x:Object[]` fails at `build` (not `validate`). `Filters` `Operator` takes enum identifiers (`GT`, `EQ`, `CONTAINS`, …); omit `Operand` for `EMPTY`/`NOTEMPTY`. `AddDataRow.DataTable` is `InOutArgument` — bind a variable, never an expression.
**Long-form:** [`GenerateDataTable.md`](activity-docs/UiPath.System.Activities/26.4/activities/GenerateDataTable.md) · [`AddDataRow.md`](activity-docs/UiPath.System.Activities/26.4/activities/AddDataRow.md) · [`FilterDataTable.md`](activity-docs/UiPath.System.Activities/26.4/activities/FilterDataTable.md) · [`OutputDataTable.md`](activity-docs/UiPath.System.Activities/26.4/activities/OutputDataTable.md)

---

### Queue publish
**Activities:** `UiPath.Core.Activities.AddQueueItem`
**Prefixes:** `ui:`, `s:`

```xml
<ui:AddQueueItem DisplayName="Add Queue Item" QueueType="InvoiceProcessing" Priority="High" Reference="INV-2024-002" DueDate="[DateTime.Now.AddDays(1)]">
  <ui:AddQueueItem.ItemInformation>
    <InArgument x:TypeArguments="x:String" x:Key="InvoiceNumber">"INV-2024-002"</InArgument>
    <InArgument x:TypeArguments="x:Double" x:Key="Amount">1500.0</InArgument>
    <InArgument x:TypeArguments="x:Boolean" x:Key="Approved">True</InArgument>
    <InArgument x:TypeArguments="s:DateTime" x:Key="InvoiceDate">[DateTime.Today]</InArgument>
  </ui:AddQueueItem.ItemInformation>
</ui:AddQueueItem>
```

**Notes:** Runtime needs Orchestrator + an existing queue (`QueueType` does not auto-create; 404 error code 1002 otherwise). Use `s:DateTime`, not `x:DateTime`. Item lands with status **New**. Queue **consumption** (`GetTransactionItem`) is not available in cross-platform `UiPath.System.Activities` — for transaction loops see [reframework-guide.md](reframework-guide.md).
**Long-form:** [`AddQueueItem.md`](activity-docs/UiPath.System.Activities/26.4/activities/AddQueueItem.md)

---

### Retry wrap
**Activities:** `UiPath.Core.Activities.RetryScope`
**Prefixes:** `ui:`, `s:`
**Variables:** `fetchedContent : String` (example body output).

```xml
<ui:RetryScope DisplayName="Retry Scope">
  <ui:RetryScope.NumberOfRetries>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="3" />
    </InArgument>
  </ui:RetryScope.NumberOfRetries>
  <ui:RetryScope.RetryInterval>
    <InArgument x:TypeArguments="s:TimeSpan">
      <VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" />
    </InArgument>
  </ui:RetryScope.RetryInterval>
  <ui:RetryScope.ActivityBody>
    <ActivityAction>
      <Sequence DisplayName="Action">
        <ui:ReadTextFile DisplayName="Read flaky source" FileName="data/flaky-source.txt" Content="[fetchedContent]" />
      </Sequence>
    </ActivityAction>
  </ui:RetryScope.ActivityBody>
  <ui:RetryScope.Condition>
    <ActivityFunc x:TypeArguments="x:Boolean" />
  </ui:RetryScope.Condition>
</ui:RetryScope>
```

**Notes:** Empty `ActivityFunc` = retry on exception only (the common wrap). To retry-until-true, place an `Activity(Of Boolean)` inside `Condition`. Body serializes as `ActivityBody`/`ActivityAction` — not a bare child.
**Long-form:** [`RetryScope.md`](activity-docs/UiPath.System.Activities/26.4/activities/RetryScope.md)

---

### Invoke workflow with arguments
**Activities:** `UiPath.Core.Activities.InvokeWorkflowFile`
**Prefixes:** `ui:`, `scg:`
**Variables:** `childResult : String`.

```xml
<ui:InvokeWorkflowFile DisplayName="Invoke Workflow File" WorkflowFileName="Pattern_Child.xaml">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="in_Message">["hello"]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="out_Result">[childResult]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

Child workflow declares its contract via root `x:Members`:

```xml
<x:Members>
  <x:Property Name="in_Message" Type="InArgument(x:String)" />
  <x:Property Name="out_Result" Type="OutArgument(x:String)" />
</x:Members>
```

**Notes:** Keys must match the child's declared argument names exactly; `InArgument`/`OutArgument`/`InOutArgument` per direction. Runs synchronously. `WorkflowFileName` is project-relative. XML-escape `&` in VB concatenation (`&amp;`).
**Long-form:** [`InvokeWorkflow.md`](activity-docs/UiPath.System.Activities/26.4/activities/InvokeWorkflow.md)

---

### CSV file read / write
**Activities:** `UiPath.CSV.Activities.ReadCsvFile` · `AppendWriteCsvFile`
**Packages:** `UiPath.Excel.Activities` 3.6.0-preview (CSV activities are Excel-package-owned, cross-platform, no Excel app needed)
**Prefixes:** `csv:`, `sd:`
**Variables:** `csvData : System.Data.DataTable`.

```xml
<Sequence DisplayName="CSV Read Write">
  <Sequence.Variables>
    <Variable x:TypeArguments="sd:DataTable" Name="csvData" />
  </Sequence.Variables>
  <csv:ReadCsvFile DisplayName="Read CSV" FilePath="data/input.csv" IncludeColumnNames="True" DataTable="[csvData]" />
  <csv:AppendWriteCsvFile DisplayName="Write CSV" FilePath="data/output.csv" CsvAction="Write" AddHeaders="True">
    <csv:AppendWriteCsvFile.DataTable>
      <InArgument x:TypeArguments="sd:DataTable">[csvData]</InArgument>
    </csv:AppendWriteCsvFile.DataTable>
  </csv:AppendWriteCsvFile>
</Sequence>
```

**Notes:** `CsvAction`: `Write` replaces, `Append` adds after existing rows. Delimiter via `DelimitatorForViewModel` (`Comma` default; `Semicolon`/`Pipe`/`Caret`/`Tab`). `IncludeColumnNames="True"` = first row is headers.
**Long-form:** [`ReadCsvFile.md` (3.6)](activity-docs/UiPath.Excel.Activities/3.6/activities/ReadCsvFile.md) · `{PROJECT_DIR}/.local/docs/packages/UiPath.Excel.Activities/activities/AppendWriteCsvFile.md`

---

### HTTP request → JSON
**Activities:** `UiPath.Web.Activities.Http.NetHttpRequest` · `UiPath.Web.Activities.DeserializeJson<T>`
**Packages:** `UiPath.WebAPI.Activities` 2.5.1
**Prefixes:** `nhr:`, `nhrm:`, `web:`, `jn:`
**Variables:** `httpResponse : UiPath.Web.Activities.Http.Models.HttpResponseSummary`; `jsonResult : Newtonsoft.Json.Linq.JObject`.

```xml
<Sequence DisplayName="HTTP GET Deserialize">
  <Sequence.Variables>
    <Variable x:TypeArguments="nhrm:HttpResponseSummary" Name="httpResponse" />
    <Variable x:TypeArguments="jn:JObject" Name="jsonResult" />
  </Sequence.Variables>
  <nhr:NetHttpRequest DisplayName="GET API Data" RequestUrl="https://api.example.com/data" Method="GET" RequestBodyType="None" RetryPolicyType="Basic" RetryCount="[3]" TimeoutInMiliseconds="[10000]" Result="[httpResponse]" />
  <web:DeserializeJson x:TypeArguments="jn:JObject" DisplayName="Deserialize JSON" JsonString="[httpResponse.TextContent]" JsonObject="[jsonResult]" />
</Sequence>
```

**Notes (build-verified traps):** Use `NetHttpRequest` — `HttpClient` is legacy. The XAML assembly is `UiPath.Web.Activities`, NOT the package id `UiPath.WebAPI.Activities`; `HttpResponseSummary` lives in `...Http.Models`. Read body from `httpResponse.TextContent`, verdict from `httpResponse.StatusCode`. Default `ContinueOnError=True` turns network failures into synthetic `503` responses — guard on `StatusCode` before parsing. POST JSON: `RequestBodyType="Text"` + `TextPayload` (content type defaults to `application/json`).
**Long-form:** `{PROJECT_DIR}/.local/docs/packages/UiPath.WebAPI.Activities/activities/NetHttpRequest.md` · `.../DeserializeJson.md`
