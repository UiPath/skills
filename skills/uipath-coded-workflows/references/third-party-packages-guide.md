# Using Third-Party NuGet Packages in Coded Workflows

When a user needs functionality that **no UiPath built-in activity provides** (e.g. PDF generation, barcode reading, advanced math, specific file formats), find and use a third-party NuGet package.

## Decision Flow

1. **Consider whether a built-in activity or plain .NET is the better fit** — prefer activities for Orchestrator integration, UI automation, and document handling; prefer .NET for data transforms, HTTP to external APIs, parsing, etc.
2. **If no built-in activity fits** — search for a well-known .NET NuGet package that provides the capability
3. **Inspect the package** — run the `uip rpa inspect-package` command with the appropriate flags in order to get exact API signatures before writing code
4. **Add it to `project.json`** — add the package to `dependencies` with bracket-notation version
5. **Write C# code using the package** — use the package's API directly in the `Execute` method (no service proxy needed — just `using` + direct API calls)

## How Third-Party Packages Differ from UiPath Activity Packages

- UiPath packages provide services on the `CodedWorkflow` base class (e.g. `excel.ReadRange(...)`)
- Third-party packages are used as **plain C# libraries** — instantiate classes, call methods directly
- They do NOT get a service property on `CodedWorkflow`
- Add them to `project.json` `dependencies` just like UiPath packages: `"PackageName": "[version]"`

## Example — Using CsvHelper in a Coded Workflow

```csharp
using System;
using System.Globalization;
using System.IO;
using CsvHelper;
using UiPath.CodedWorkflows;

namespace MyProject
{
    public class ProcessCsv : CodedWorkflow
    {
        [Workflow]
        public void Execute(string inputPath)
        {
            using var reader = new StreamReader(inputPath);
            using var csv = new CsvReader(reader, CultureInfo.InvariantCulture);
            var records = csv.GetRecords<dynamic>().ToList();
            Log($"Read {records.Count} records from CSV");
        }
    }
}
```

With `project.json` dependency:
```json
{
  "dependencies": {
    "CsvHelper": "[33.0.1]"
  }
}
```

## How to Search for Packages

- Use web search to find the best .NET NuGet package for the task
- Look for packages with high download counts, active maintenance, and .NET 6+ support
- Common choices:
  - `CsvHelper` (CSV parsing)
  - `QuestPDF` (PDF generation)
  - `ClosedXML` (Excel without UiPath)
  - `HtmlAgilityPack` (HTML parsing)
  - `Dapper` (database access)
  - `RestSharp` (REST APIs)
  - `Polly` (retry/resilience patterns)
  - `Newtonsoft.Json` (JSON parsing - already included in most projects)
- After identifying a package, run the `uip rpa inspect-package --use-studio` command to discover exact APIs before coding
