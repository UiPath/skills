# Project structure

Read this file when: you need to understand the UiPath project layout, project.json fields, or common activity packages.

## Directory layout

```
MyProject/
├── project.json          # Project manifest (name, dependencies, settings)
├── Main.xaml             # Default entry point (XAML mode)
├── Main.cs               # Default entry point (coded mode)
├── *.xaml                # Additional XAML workflow files
├── *.cs                  # Coded workflows, test cases
├── .local/               # Local cache (restored packages, compiled artifacts, activity docs)
│   └── docs/packages/    # Auto-generated activity documentation (primary source)
├── .objects/             # Object repository (UI element descriptors)
├── .project/             # Project metadata (JitCustomTypesSchema.json)
├── .settings/            # Project-level settings
└── .storage/             # Activity resource storage
    ├── .design/          # Design-time only (NOT packed)
    └── .runtime/         # Runtime resources (packed into NuPkg)
```

## project.json key fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used in package output) |
| `main` | Entry point workflow file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `CSharp` or `VisualBasic`. Determines expression syntax in XAML. |
| `designOptions.outputType` | `Process`, `Library`, or `Tests` |
| `targetFramework` | `Windows` (best compatibility) or `Portable` (cross-platform) |

## Rules

- Use CLI for dependencies: `uip rpa install-or-update-packages`. Do not manually edit the `dependencies` section.
- Do not edit `.local/` or `.objects/`. These are managed by the build system.
- All `uip rpa` commands default to CWD as project root. Pass `--project-dir` if CWD is not the project root.
- Create new projects with `uip rpa create-project --name "ProjectName" --location "/parent/dir"`.

## Common activity packages

| Package ID | Description |
|------------|-------------|
| `UiPath.System.Activities` | Core: Assign, If, ForEach, While, Invoke Workflow, Log Message |
| `UiPath.UIAutomation.Activities` | UI: Click, Type Into, Get Text, Use Application/Browser |
| `UiPath.Excel.Activities` | Excel: Read Range, Write Range, Read Cell, Format Range |
| `UiPath.Mail.Activities` | Email: Send Mail, Get Mail, Save Attachments |
| `UiPath.Database.Activities` | DB: Execute Query, Execute Non Query |
| `UiPath.WebAPI.Activities` | HTTP: HTTP Request, Deserialize JSON |
| `UiPath.PDF.Activities` | PDF: Read PDF Text, Extract Data From PDF |
| `UiPath.Word.Activities` | Word: Read Text, Replace Text, Export to PDF |
| `UiPath.Testing.Activities` | Test: Verify Expression, Generate Test Data |
| `UiPath.IntegrationService.Activities` | IS: Generic ConnectorActivity for all IS connectors |

## Version constraint syntax

| Syntax | Meaning |
|--------|---------|
| `[1.0.0]` | Exact version |
| `[1.0.0, )` | 1.0.0 or higher |
| `[1.0.0, 2.0.0)` | Between 1.0.0 inclusive and 2.0.0 exclusive |
