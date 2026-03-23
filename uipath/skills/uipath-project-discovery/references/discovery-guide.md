# Project Discovery Guide

Step-by-step procedure for analyzing a UiPath automation project and extracting context.

## Step 1: Read Project Definition

Read `project.json` and extract:

| Field | Location in JSON | What to Record |
|-------|-----------------|----------------|
| Project name | `.name` | Project identity |
| Description | `.description` | Project purpose |
| Project type | `.designOptions.outputType` | Process / Tests / Library |
| Target framework | `.targetFramework` | Windows / Portable |
| Expression language | `.expressionLanguage` | CSharp / VisualBasic |
| Schema version | `.schemaVersion` | Compatibility level |
| Entry points | `.entryPoints[]` | File paths, input/output arguments |
| Dependencies | `.dependencies` | Package names and version ranges |
| Runtime options | `.runtimeOptions` | isAttended, isPausable, etc. |
| Test cases | `.designOptions.fileInfoCollection[]` | Test case files (if Tests project) |

## Step 2: Inventory Files

Use Glob to discover all project files:

```
**/*.cs       → coded workflow / source files
**/*.xaml      → RPA workflow files
**/*.cs.json   → coded workflow metadata files
```

Categorize the results:
- **Coded workflows**: .cs files that have companion .cs.json files or are listed as entry points
- **Coded source files**: .cs files WITHOUT .cs.json (helpers, models, utilities)
- **RPA workflows**: .xaml files
- **Test cases**: files listed in `fileInfoCollection`
- **Object Repository**: `.objects/` directory contents

Record:
- Total file count per category
- Directory structure (top-level folders and their purpose)
- Notable organizational patterns (e.g., Workflows/ subfolder, Models/ subfolder)

## Step 3: Analyze Dependencies

From `project.json` dependencies, categorize:

| Category | Package Pattern | Meaning |
|----------|----------------|---------|
| Core | UiPath.System.Activities | Core system activities |
| Testing | UiPath.Testing.Activities | Test framework |
| UI Automation | UiPath.UIAutomation.Activities | UI interaction |
| Excel | UiPath.Excel.Activities | Excel file manipulation |
| Mail | UiPath.Mail.Activities | Email (SMTP/IMAP/Outlook) |
| Office 365 | UiPath.MicrosoftOffice365.Activities | Microsoft Graph |
| Database | UiPath.Database.Activities | SQL database access |
| Web | UiPath.WebAPI.Activities | HTTP/REST API calls |
| PDF | UiPath.PDF.Activities | PDF processing |
| Other UiPath | UiPath.* (not matched above) | Other UiPath packages |
| Third-party | Non-UiPath packages | External NuGet packages |

Note the version ranges — these indicate compatibility requirements.

## Step 4: Sample Code Files

Read a representative sample of source files. Selection strategy:

1. **Always read**: Main.cs or Main.xaml (primary entry point)
2. **Read entry points**: Up to 10 entry point files from `project.json`
3. **Read diverse files**: Pick files from different directories/categories
4. **Read helpers/models**: If coded source files exist, read 2-3 of them
5. **Maximum**: 20 files total

For each **coded (.cs) file**, extract:
- Namespace used
- Base class (CodedWorkflow, custom base, none)
- Attributes ([Workflow], [TestCase], none)
- Services used (system.*, excel.*, uiAutomation.*, etc.)
- Method signatures (Execute parameters and return types)
- Patterns (error handling style, logging, variable naming)

For each **RPA (.xaml) file**, extract:
- Workflow type (Sequence, Flowchart, StateMachine)
- Top-level activity types used
- Arguments (input/output with types)
- Expression language (VB or C#)

## Step 5: Detect Naming Conventions

From the sampled files, identify:
- **File naming**: PascalCase, camelCase, kebab-case, snake_case? Prefixes/suffixes?
- **Class naming**: Matches file name? Any prefix/suffix pattern?
- **Namespace**: Derived from project name? Subfolder-aware?
- **Variable naming**: camelCase locals? PascalCase properties?
- **Method naming**: Patterns beyond Execute?

## Step 6: Check for Existing Documentation

Look for existing context files:
- `CLAUDE.md` at project root
- `AGENTS.md` at project root
- `.claude/` directory
- `README.md` at project root

Note existing content to avoid duplicating what is already documented.

## Step 7: Identify Object Repository & UILibrary Packages

The Object Repository provides strongly-typed UI element descriptors accessed via `Descriptors.<App>.<Screen>.<Element>`. There are two sources of descriptors to check:

### 7a: Project Object Repository (`.objects/` directory)

If `.objects/` directory exists at the project root:
- Read `.metadata` files to discover the App → AppVersion → Screen → Element hierarchy
- List applications defined (app names, noting that spaces become underscores in code)
- Count screens and elements per application
- Note that the auto-generated file `.local/.codedworkflows/ObjectRepository.cs` provides the typed descriptors
- Record the using statement pattern: `using <ProjectNamespace>.ObjectRepository;`

### 7b: UILibrary NuGet Packages

Check `project.json` dependencies for UILibrary packages. These are external packages containing pre-built Object Repository descriptors:
- **Naming patterns**: packages matching `*.UILibrary`, `*.ObjectRepository`, `*.Descriptors`, or `*.UIAutomation` (non-UiPath packages)
- **Example**: `MyCompany.SalesApp.UILibrary`, `MultipleApps.Descriptors`
- **Inspection**: Use `uip rpa inspect-package --package-name <PackageName>` to discover apps, screens, and elements inside the package
- **Using statement pattern**: `using <PackageName>.ObjectRepository;`

Record for the context output:
- Which applications are available (project-local vs UILibrary package)
- Total screen and element counts
- The correct using statements for each descriptor source

### 7c: Integration Service Connections

If Integration Service connections are referenced in code:
- Note connector types used (e.g., Salesforce, SAP, ServiceNow)
- List connection identifiers found in source files

## Step 8: Assess Project Complexity

Based on all gathered data, assess:
- **Size**: Small (1-5 files), Medium (6-20), Large (20+)
- **Architecture**: Single workflow, multi-step orchestrated, library, test suite, REF/Dispatcher
- **Integration depth**: Number of external services/packages used
