# Legacy Project Structure

Understanding the layout and configuration of a legacy UiPath RPA project.

---

## Directory Layout

A typical legacy UiPath project:

```
{projectRoot}/
├── project.json              # Project metadata and dependencies
├── Main.xaml                 # Entry point workflow
├── *.xaml                    # Additional workflows (flat or in folders)
├── Workflows/                # (Optional) Sub-folder for organized workflows
│   ├── Process/
│   ├── Framework/
│   └── Tests/
├── Data/                     # (Optional) Input/output data files
├── .screenshots/             # (Optional) Studio screenshot captures
├── .settings/                # (Optional) Studio settings profiles
├── .tmh/                     # (Optional) Test Manager data
└── packages.config           # (Sometimes) NuGet package references (older format)
```

**Notable absences compared to modern projects:**
- No `.local/docs/packages/` — legacy projects do not have auto-generated activity documentation
- No `.codedworkflows/` — no coded automation support
- No `.objects/` — Object Repository is not available in legacy framework
- No `.project/JitCustomTypesSchema.json` — no JIT custom types

---

## project.json Key Fields

```json
{
  "name": "MyLegacyProject",
  "description": "Project description",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[22.10.4]",
    "UiPath.UIAutomation.Activities": "[22.10.4]",
    "UiPath.Excel.Activities": "[2.11.3]",
    "UiPath.Mail.Activities": "[1.12.1]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "22.10.0.0",
  "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic",
  "targetFramework": "Legacy",
  "runtimeOptions": {
    "autoDispose": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": true,
    "supportsPersistence": false,
    "workflowSerialization": "DataContract",
    "excludedLoggedData": ["Private:*", "*password*"],
    "executionType": "Workflow"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process"
  },
  "entryPoints": [
    {
      "filePath": "Main.xaml",
      "uniqueId": "...",
      "input": [],
      "output": []
    }
  ]
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used as package ID when built) |
| `main` | Entry point XAML file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `"VisualBasic"` (most legacy) or `"CSharp"` |
| `targetFramework` | `"Legacy"` for .NET Framework 4.6.1 projects |
| `designOptions.outputType` | `"Process"` (standalone) or `"Library"` (reusable) |
| `studioVersion` | Studio version that created the project |

### Version Constraints

Dependencies use NuGet version constraint syntax:

| Syntax | Meaning |
|--------|---------|
| `[1.2.3]` | Exact version 1.2.3 |
| `[1.2.3, )` | Minimum version 1.2.3 |
| `[1.0, 2.0)` | Range: >= 1.0, < 2.0 |

---

## Common Legacy Activity Packages

| Package | Typical Legacy Versions | Description |
|---------|------------------------|-------------|
| `UiPath.System.Activities` | 20.x - 22.x | Core: Assign, If, For Each, Try-Catch, InvokeWorkflow |
| `UiPath.UIAutomation.Activities` | 20.x - 22.x | UI: Click, TypeInto, GetText, selectors |
| `UiPath.Excel.Activities` | 2.x | Excel: ExcelApplicationScope, ReadRange, WriteRange |
| `UiPath.Mail.Activities` | 1.x | Mail: SMTP, IMAP, POP3, Exchange, Outlook |
| `UiPath.WebAPI.Activities` | 1.x | Web: HTTP Request, SOAP, JSON/XML |
| `UiPath.PDF.Activities` | 3.x | PDF: ReadPDFText, ReadPDFWithOCR |
| `UiPath.Testing.Activities` | 20.x - 22.x | Testing: Assertions, VerifyExpression |
| `UiPath.MicrosoftOffice365.Activities` | 1.x - 2.x | O365: Mail, Calendar, OneDrive, SharePoint |
| `UiPath.Word.Activities` | 2.x | Word: WordApplicationScope, Read/AppendText |
| `UiPath.Presentations.Activities` | 2.x | PowerPoint: Slides, text, media |
| `UiPath.Database.Activities` | 1.x | Database: ExecuteQuery, ExecuteNonQuery |
| `UiPath.Credentials.Activities` | 1.x | Windows Credential Manager |

**Legacy indicator:** Package versions in the low single digits (1.x, 2.x, 3.x) or pre-23.x for System/UIAutomation packages generally indicate legacy projects. Modern projects typically use 23.x+ versions with different package structures.
