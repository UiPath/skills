# UiPath Project Structure

## Directory Layout

```
MyProject/
├── project.json          # Project manifest (name, dependencies, settings)
├── Main.xaml             # Default entry point (XAML mode) ─┐ typically one
├── Main.cs               # Default entry point (coded mode) ─┘ or the other
├── *.xaml                # Additional XAML workflow files
├── *.cs                  # Coded workflows, test cases, and source files
├── *.cs.json             # Metadata for coded workflows/test cases (arguments, display name)
├── .codedworkflows/      # Auto-generated coded workflow support files (ConnectionsFactory.cs, ConnectionsManager.cs, etc.)
├── .local/               # Local cache (package restore, compiled artifacts)
│   └── install/          # Restored NuGet packages
│   └── .codedworkflows/  # Auto-generated coded workflow support files (ObjectRepository.cs, CodedWorkflow.cs, WorkflowRunnerService.cs)
├── .objects/             # Build output cache
├── .screenshots/         # Activity screenshots (auto-generated)
├── .settings/            # Project-level settings
├── .autopilot/           # Autopilot service specific files
│   └── skills/           # Base root folder of all the available, project-specific Autopilot skills
└── .storage/             # Activity resource storage (bucket-organized)
    ├── .design/          # Design-time only resources (NOT packed into published package)
    │   └── <bucket>/     # Named bucket to prevent conflicts
    └── .runtime/         # Runtime resources (packed into published NuPkg)
        └── <bucket>/     # Named bucket with resource files
```

## project.json Key Fields

```json
{
  "name": "MyProject",
  "description": "",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[24.12.1]"
  },
  "webServices": [],
  "entitiesStores": [],
  "schemaVersion": "4.0",
  "studioVersion": "25.0.0.0",
  "projectVersion": "1.0.0",
  "runtimeOptions": {
    "autoDispose": false,
    "netFramework": {
      "targetFramework": "net6.0-windows"
    },
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process",
    "libraryOptions": {
      "includeOriginalXaml": false,
      "privateWorkflows": []
    }
  },
  "expressionLanguage": "VisualBasic",
  "entryPoints": [
    {
      "filePath": "Main.xaml",
      "uniqueId": "2f510550-3882-4340-9239-53a24d0717f6",
      "input": [],
      "output": []
    }
  ],
  "isTemplate": false,
  "templateProjectData": {},
  "publishData": {},
  "targetFramework": "Windows"
}
```

### Important Fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used in package output) |
| `main` | Entry point workflow file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `CSharp` or `VisualBasic` — determines expression syntax in XAML. Prefer `VisualBasic` for Windows target framework projects |
| `designOptions.outputType` | `Process`, `Library`, or `Tests` |
| `targetFramework` | `Windows` (.NET 6 Windows, default — best compatibility) or `Portable` (cross-platform .NET 6+ — for serverless/Studio Web) |

## Rules

- **Use CLI for dependencies**: Always use `uip rpa install-or-update-packages` to add/update dependencies. Do not manually edit the `dependencies` section of `project.json`.
- **Do not edit `.local/` or `.objects/`**: These are cache directories managed by the build system.
- **`main` entry point**: The default entrypoint that gets run, if not specified otherwise.
- **`--project-dir` awareness**: All `uip rpa` commands default to the current working directory as the project root. If the CWD is not the project root (e.g., you are in a parent monorepo), pass `--project-dir "{projectRoot}"` explicitly to every `uip rpa` command, or all operations will fail or target the wrong project.
- **Creating new projects**: Use `uip rpa new --name "ProjectName" --location "/parent/dir"` to create projects. After creation, open the project in Studio: `uip rpa open-project --project-dir "/parent/dir/ProjectName"`.

## Common Activity Packages

| Package ID | Description | Key Activities |
|------------|-------------|----------------|
| `UiPath.System.Activities` | Core system activities | Assign, If, ForEach, While, Invoke Workflow, Log Message, Delay |
| `UiPath.UIAutomation.Activities` | UI interaction | Click, Type Into, Get Text, Open Browser, Use Application/Browser |
| `UiPath.Excel.Activities` | Excel automation | Read Range, Write Range, Read Cell, Write Cell, Format Range |
| `UiPath.Mail.Activities` | Email operations | Send Mail, Get Mail, Save Attachments, Forward Mail |
| `UiPath.Database.Activities` | Database operations | Execute Query, Execute Non Query, Connect, Disconnect |
| `UiPath.WebAPI.Activities` | HTTP/REST calls | HTTP Request, Deserialize JSON, Serialize JSON |
| `UiPath.PDF.Activities` | PDF processing | Read PDF Text, Read PDF with OCR, Extract Data From PDF |
| `UiPath.Word.Activities` | Word automation | Read Text, Replace Text, Insert Image, Export to PDF |
| `UiPath.Testing.Activities` | Testing and assertions | Verify Expression, Verify Are Equal, Generate Test Data |
| `UiPath.Presentations.Activities` | PowerPoint automation | Add Slide, Replace Text, Insert Image |
| `UiPath.IntegrationService.Activities` | Integration Service connector runtime | Generic `ConnectorActivity` that consumes metadata from IS connectors (Salesforce, ServiceNow, HubSpot, etc.). Required for any IS connector activity. |
| `UiPath.Cryptography.Activities` | Encryption/hashing | Encrypt Text, Decrypt Text, Hash File |

## Version Constraints

Dependencies use NuGet version constraint syntax:

| Syntax | Meaning |
|--------|---------|
| `[1.0.0]` | Exact version 1.0.0 |
| `[1.0.0, )` | Version 1.0.0 or higher |
| `[1.0.0, 2.0.0)` | Between 1.0.0 (inclusive) and 2.0.0 (exclusive) |

The correct available versions and syntax can be determined by reading the `project.json` dependencies section.
