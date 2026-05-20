# Legacy Project Structure

Understanding the layout and configuration of a legacy UiPath RPA project.

---

## Directory Layout

```
{projectRoot}/
├── project.json              # Project metadata and dependencies
├── Main.xaml                 # Entry point workflow
├── *.xaml                    # Additional workflows (flat or in folders)
├── Workflows/                # (Optional) Sub-folder for organized workflows
├── Data/                     # (Optional) Input/output data files
├── .screenshots/             # (Optional) Studio screenshot captures
├── .settings/                # (Optional) Studio settings profiles
└── .tmh/                     # (Optional) Test Manager data
```

**Notable absences compared to modern projects:**
- No `.local/docs/packages/` — no auto-generated activity documentation
- No `.codedworkflows/` — no coded automation support
- No `.objects/` — no Object Repository
- No `.project/JitCustomTypesSchema.json` — no JIT custom types

---

## Creating a project.json from Scratch

### Minimal Template

Start with this — only `UiPath.System.Activities` is required. Add other packages as needed.

```json
{
  "name": "MyProject",
  "description": "",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[24.10.8]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "25.10.0.0",
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
      "uniqueId": "00000000-0000-0000-0000-000000000000",
      "input": [],
      "output": []
    }
  ]
}
```

### Package Selection Guide

**Add packages based on what the workflow needs.** Only `UiPath.System.Activities` is required — everything else is optional.

| Need | Package | Latest Legacy Version |
|------|---------|----------------------|
| **Core (always include)** | `UiPath.System.Activities` | **24.10.8** |
| UI automation (click, type, selectors) | `UiPath.UIAutomation.Activities` | **25.10.28** |
| Excel (read/write, macros, CSV) | `UiPath.Excel.Activities` | **2.24.4** |
| Email (SMTP, IMAP, POP3, Outlook) | `UiPath.Mail.Activities` | **1.24.18** |
| HTTP/REST/SOAP/JSON/XML | `UiPath.WebAPI.Activities` | **1.21.1** |
| Testing and assertions | `UiPath.Testing.Activities` | **25.10.1** |
| PDF (read text, OCR, merge, split) | `UiPath.PDF.Activities` | **3.25.2** |
| Office 365 (Graph API) | `UiPath.MicrosoftOffice365.Activities` | **2.9.13** |
| Word documents | `UiPath.Word.Activities` | **1.20.3** |
| PowerPoint presentations | `UiPath.Presentations.Activities` | **1.14.2** |
| Database (SQL queries) | `UiPath.Database.Activities` | **1.10.1** |
| Windows Credential Manager | `UiPath.Credentials.Activities` | **2.1.0** |
| FTP/SFTP file transfer | `UiPath.FTP.Activities` | **2.4.0** |
| Encryption/hashing (AES, HMAC, PGP) | `UiPath.Cryptography.Activities` | **1.6.1** |
| Python script execution | `UiPath.Python.Activities` | **1.10.0** |
| Java method invocation | `UiPath.Java.Activities` | **1.3.1** |
| Document Understanding/OCR | `UiPath.IntelligentOCR.Activities` | **6.27.3** |
| Forms (FormIo/HTML) | `UiPath.Form.Activities` | **2.0.8** |
| Terminal emulation (3270/5250/VT) | `UiPath.Terminal.Activities` | **2.9.0** |
| Google Suite (Gmail, Drive, Sheets) | `UiPath.GSuite.Activities` | **2.8.28** |
| NLP (sentiment, translation) | `UiPath.Cognitive.Activities` | **2.2.4** |
| StudioX scenario templates | `UiPath.ComplexScenarios.Activities` | **1.5.1** |
| OmniPage OCR engine | `UiPath.OmniPage.Activities` | **1.22.2** |
| Persistence (long-running workflows) | `UiPath.Persistence.Activities` | **1.8.1** |
| Mobile automation (iOS/Android) | `UiPath.MobileAutomation.Activities` | **25.10.0** |
| SAP BAPI function calls | `UiPath.SAP.BAPI.Activities` | **3.0.4** |

**Example:** A workflow that reads Excel, sends email, and calls a REST API needs:
```json
"dependencies": {
  "UiPath.System.Activities": "[24.10.8]",
  "UiPath.Excel.Activities": "[2.24.4]",
  "UiPath.Mail.Activities": "[1.24.18]",
  "UiPath.WebAPI.Activities": "[1.21.1]"
}
```

### Packages Can Be Added Later

You don't need all packages upfront. Add them to `dependencies` as you discover what the workflow needs.

**Important:** `find-activities` only searches packages listed in `dependencies`. If you add a package to project.json, re-run `find-activities` to discover its activities.

### Searching for Packages

When the known packages above don't cover a need, search configured NuGet feeds:

```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```

This searches all configured feeds (UiPath official + any custom feeds) by name and description. Add the discovered package to `dependencies`, then `find-activities` will index it.

### Arbitrary .NET Packages

Any NuGet package can be added to `dependencies` for custom .NET classes, methods, and types. Examples:
- `CsvHelper` — advanced CSV parsing
- `ClosedXML` — .xlsx manipulation without COM
- `HtmlAgilityPack` — HTML parsing

Use these via `InvokeCode` with the appropriate namespace imports.

**Avoid adding packages already bundled with Studio** (e.g., `Newtonsoft.Json`) — version conflicts can cause runtime issues.

---

## project.json Key Fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used as package ID when packaged) |
| `main` | Entry point XAML file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `"VisualBasic"` (most legacy) or `"CSharp"` |
| `targetFramework` | `"Legacy"` for .NET Framework 4.6.1 projects |
| `designOptions.outputType` | `"Process"` (standalone) or `"Library"` (reusable) |
| `studioVersion` | Studio version that created the project |

### Version Constraints

| Syntax | Meaning |
|--------|---------|
| `[1.2.3]` | Exact version 1.2.3 |
| `[1.2.3, )` | Minimum version 1.2.3 |
| `[1.0, 2.0)` | Range: >= 1.0, < 2.0 |

---

## Library Project Template

To create a **Library** project (reusable workflows published as a NuGet package), set `outputType` to `"Library"`:

```json
{
  "name": "Acme.Finance.InvoiceUtilities",
  "description": "Reusable invoice processing workflows",
  "dependencies": {
    "UiPath.System.Activities": "[24.10.8]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "25.10.0.0",
  "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic",
  "targetFramework": "Legacy",
  "runtimeOptions": {
    "autoDispose": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false,
    "supportsPersistence": false,
    "workflowSerialization": "DataContract",
    "excludedLoggedData": ["Private:*", "*password*"],
    "executionType": "Workflow"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Library"
  }
}
```

**Key differences from Process projects:**
- **No `main` field** — libraries have no entry point
- **No `entryPoints` array** — all workflows are callable individually
- **`outputType: "Library"`** — published as activity package, not deployed as process
- Workflows marked **Public** become activities when consumed; **Private** workflows are internal helpers

For full library design guidance (naming, versioning, patterns), see [project-organization-guide.md](./project-organization-guide.md).
