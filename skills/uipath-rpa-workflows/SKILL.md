---
name: uipath-rpa-workflows
description: "Generate, edit, test, and run RPA workflows (XAML files) in UiPath Studio Desktop using uip CLI and filesystem operations. TRIGGER when: RPA project detected (project.json with UiPath dependencies AND .xaml workflow files); User mentions XAML workflows, RPA workflows, .xaml files, or UiPath Studio Desktop workflows; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, transaction processing, queue items, API calls, etc.) and a UiPath RPA/XAML project exists nearby; User asks about fixing XAML errors or workflow validation issues. DO NOT TRIGGER when: User is working with coded workflows (.cs files with [Workflow]/[TestCase] attributes -- use uipath-coded-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-platform instead)."
---

# RPA workflow architect

Edit and create UiPath XAML workflows using `uip rpa` CLI commands and filesystem tools.

---

## Rules (never violate)

1. NEVER generate XAML properties from memory. Use `get-default-activity-xaml` or activity docs.
2. NEVER guess activity class names. Use `find-activities` to search.
3. ALWAYS validate after every XAML change: `uip rpa get-errors --file-path "relative/path.xaml"`
4. ALWAYS read `project.json` before writing any XAML (need expression language and deps).
5. ALWAYS use relative paths with `get-errors`. Use absolute paths with `run-file`.
6. The command is `create-project`, NOT `new`. There is no `uip rpa new`.
7. Build one activity at a time. Never generate a large workflow in one shot.
8. Default CLI output is JSON. Use `--format table` only when showing results to the user.
9. If a CLI command fails, run it with `--help` to see correct parameters.
10. Fix errors in order: Package (missing deps) > Structure (bad XML) > Type (wrong types) > Properties > Logic.

---

## Decision tree

Read `project.json` first. Then pick the matching task:

```
User wants to...
|
+-- Add/edit an activity in existing file --> Task A
+-- Create a new workflow from scratch -----> Task B
+-- Fix validation errors ------------------> Task C
+-- Run or test a workflow -----------------> Task D
+-- Install or update a package ------------> Task E
+-- Create a new project -------------------> Task F
+-- Build UI automation --------------------> Task G (read ui-automation-guide.md)
+-- Use Integration Service connectors -----> Task H (read connector-capabilities.md)
+-- Something else -------------------------> Read cli-reference.md for full command list
```

---

## Task A: Add or edit an activity in an existing workflow

Step 1. Read the target XAML file to understand the current structure.

Step 2. Find the activity class name:
```bash
uip rpa find-activities --query "log message"
```
Look at the `className` field in the result. Use that exact value in step 3.

Step 3. Get the default XAML template:
```bash
uip rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.LogMessage"
```

Step 4. Edit the XAML file. Insert the activity at the correct position inside a `<Sequence>`.
- VB expressions use brackets: `Message="[&quot;Hello&quot;]"`
- C# expressions use CSharpValue: `<InArgument x:TypeArguments="x:String"><mca:CSharpValue x:TypeArguments="x:String">"Hello"</mca:CSharpValue></InArgument>`
- Each activity needs a unique `sap2010:WorkflowViewState.IdRef` (e.g., `LogMessage_1`)

Step 5. Validate:
```bash
uip rpa get-errors --file-path "Main.xaml"
```

Step 6. If errors, fix and validate again. If stuck after 3 attempts, tell the user.

---

## Task B: Create a new workflow from scratch

Step 1. Read `project.json` for expression language and installed packages.

Step 2. Read [references/xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for the file template.

Step 3. Write the XAML file. Key rules:
- `x:Class` must use underscores for folder separators: `MyProject_Workflows_MyFile` (NOT dots)
- Include `xmlns:ui="http://schemas.uipath.com/workflow/activities"` for UiPath activities
- Include `xmlns:sap2010` for WorkflowViewState
- Start with a `<Sequence>` containing `<Sequence.Variables>` then your activities
- Add `TextExpression.NamespacesForImplementation` and `TextExpression.ReferencesForImplementation`

Step 4. Validate:
```bash
uip rpa get-errors --file-path "Workflows/MyFile.xaml"
```

Step 5. Fix errors. Common first-time issues:
- Missing assembly references (add to `ReferencesForImplementation`)
- Wrong `x:Class` name (must match file path with underscores)
- Missing xmlns declarations

---

## Task C: Fix validation errors

Step 1. Get the errors:
```bash
uip rpa get-errors --file-path "relative/path.xaml"
```

Step 2. Diagnose by category:
- "Activity package not found" -> install the package (Task E)
- "Cannot create unknown type" -> check [references/common-pitfalls.md](./references/common-pitfalls.md), likely `x:DateTime` should be `s:DateTime`
- "is not defined" -> missing namespace import or assembly reference
- "expression" errors -> check expression language (VB brackets vs C# CSharpValue)
- "missing or could not be loaded" -> wrong activity class name, use `find-activities` to find correct one

Step 3. Fix the specific error in the XAML file.

Step 4. Validate again. Repeat until 0 errors.

Step 5. If stuck after 3 attempts, tell the user the exact error and what you tried.

---

## Task D: Run or test a workflow

```bash
uip rpa run-file --file-path "C:\full\absolute\path\to\file.xaml"
```

For debugging UI automation workflows:
```bash
uip rpa run-file --file-path "C:\full\path\file.xaml" --command StartDebugging
```

Check the `LogEntries` in the result for output messages and errors.

---

## Task E: Install or update a package

Find available versions:
```bash
uip rpa get-versions --package-id "UiPath.Excel.Activities" --include-prerelease
```

Install:
```bash
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Excel.Activities"}]'
```

Install specific version:
```bash
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Excel.Activities","version":"2.24.2"}]'
```

After installing, check if activity docs appeared at `{projectRoot}/.local/docs/packages/{PackageId}/`.

---

## Task F: Create a new project

```bash
uip rpa create-project --name "MyProject" --location "C:\Users\me\Desktop" --expression-language "VisualBasic" --target-framework "Windows"
```

Options for `--expression-language`: `VisualBasic`, `CSharp`
Options for `--target-framework`: `Legacy`, `Windows`, `Portable`

After creation, open it: `uip rpa open-project --project-dir "C:\Users\me\Desktop\MyProject"`

---

## Task G: UI automation

Every UI element target must be configured through the `uia-configure-target` skill flow before writing XAML.

1. Read [references/ui-automation-guide.md](./references/ui-automation-guide.md)
2. Read [shared/uia-configure-target-workflows.md](../shared/uia-configure-target-workflows.md)
3. Follow the indicate-application > indicate-element > write XAML flow

---

## Task H: Integration Service connectors

Read [references/connector-capabilities.md](./references/connector-capabilities.md) for the full flow.

Quick version:
1. `uip is connectors list` to find connector key
2. `uip is connections list <connector-key>` to find connection ID
3. Use `get-default-activity-xaml --activity-type-id "..." --connection-id "..."` for dynamic activities

---

## Finding activity docs

Priority order (use the first one that works):

1. **Installed docs**: `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md`
   Check if this folder exists. If yes, read the activity doc. This is the most accurate source.

2. **CLI template**: `uip rpa get-default-activity-xaml --activity-class-name "ClassName"`
   Always works if the package is installed. Gives you the exact XAML with correct properties.

3. **Bundled docs**: `../../references/activity-docs/{PackageId}/{version}/activities/`
   Fallback when installed docs are missing. Pick the version folder closest to what is installed.

4. **Examples**: `uip rpa list-workflow-examples --tags "service"` then `uip rpa get-workflow-example --key "..."`
   Last resort. Search by service tag (e.g., "excel", "outlook", "jira").

---

## Common activity class names

These are verified. Use them directly with `get-default-activity-xaml`:

| Activity | Class name | Package | Notes |
|----------|-----------|---------|-------|
| Log Message | `UiPath.Core.Activities.LogMessage` | UiPath.System.Activities | |
| Assign | `System.Activities.Statements.Assign` | Built-in | |
| If / Else | `System.Activities.Statements.If` | Built-in | |
| While | `System.Activities.Statements.While` | Built-in | |
| Sequence | `System.Activities.Statements.Sequence` | Built-in | |
| Try Catch | `System.Activities.Statements.TryCatch` | Built-in | Needs `s:Exception` — read [exception-and-type-patterns.md](./references/exception-and-type-patterns.md) |
| WriteLine | `System.Activities.Statements.WriteLine` | Built-in | |
| Invoke Workflow | `UiPath.Core.Activities.InvokeWorkflowFile` | UiPath.System.Activities | `WorkflowFileName`, `Arguments` dict |
| HTTP Request (legacy) | `UiPath.Web.Activities.HttpClient` | UiPath.WebAPI.Activities | Returns string `Result`. Use over `NetHttpRequest` (type resolution issues) |
| Deserialize JSON Array | `UiPath.Web.Activities.DeserializeJsonArray` | UiPath.WebAPI.Activities | `JsonString` in, `JsonArray` out (JArray) |
| Send SMTP Mail | `UiPath.Mail.SMTP.Activities.SendMail` | UiPath.Mail.Activities | Don't set both `Password` and `SecurePassword` |
| Read Range (workbook) | `UiPath.Excel.Activities.ReadRange` | UiPath.Excel.Activities | `WorkbookPath`, `SheetName`, `DataTable` out. Read [excel-workbook-activities.md](./references/excel-workbook-activities.md) |
| Write Range (workbook) | `UiPath.Excel.Activities.WriteRange` | UiPath.Excel.Activities | `WorkbookPath`, `SheetName`, `DataTable` in. Read [excel-workbook-activities.md](./references/excel-workbook-activities.md) |

**ForEach** — generic, `get-default-activity-xaml` cannot generate it. Use this pattern (copy from existing workflow or build manually):
```xml
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each item" sap2010:WorkflowViewState.IdRef="ForEach`1_1" Values="[myList]">
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:String">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:String" Name="item" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- activities here -->
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>
```
Change `x:TypeArguments` for other types (e.g., `njl:JToken` for JSON iteration).

For ANY other activity, use `uip rpa find-activities --query "keyword"` to find the correct class name.

---

## Expression language cheat sheet

Check `project.json` `expressionLanguage` before writing any expression.

### VisualBasic

```xml
<!-- String value -->
Message="[&quot;Hello World&quot;]"

<!-- Variable reference -->
Message="[myVariable]"

<!-- Concatenation -->
Message="[&quot;Name: &quot; &amp; userName]"

<!-- Condition -->
Condition="[age >= 18]"

<!-- Assign -->
<Assign.Value>
  <InArgument x:TypeArguments="x:String">["Hello"]</InArgument>
</Assign.Value>
```

### CSharp

```xml
<!-- String value -->
<InArgument x:TypeArguments="x:String">
  <mca:CSharpValue x:TypeArguments="x:String">"Hello World"</mca:CSharpValue>
</InArgument>

<!-- Condition -->
<mca:CSharpValue x:TypeArguments="x:Boolean">age >= 18</mca:CSharpValue>
```

C# requires `xmlns:mca="clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities"`.

---

## Reference files — progressive loading

### ADVANCED — load when the task matches (MANDATORY for the listed triggers)

These files MUST be loaded before starting the indicated task. Do not skip them.

| File | MANDATORY when | Why |
|------|---------------|-----|
| [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) | Creating or editing any XAML file | File template, expression syntax, property binding rules, XAML examples |
| [common-pitfalls.md](./references/common-pitfalls.md) | Hit a validation error you cannot diagnose in 1 attempt | OverloadGroup patterns, type gotchas, ForEach/Iterator issues, scope errors |
| [cli-reference.md](./references/cli-reference.md) | Need exact parameters for a CLI command not shown above | Full command reference with all options |
| [validation-and-fixing.md](./references/validation-and-fixing.md) | More than 2 fix cycles on the same error | Fix order, package resolution, JIT types, focus-activity debugging |
| [environment-setup.md](./references/environment-setup.md) | Studio is not running, or creating a new project | Project root detection, start-studio, open-project, auth |
| [exception-and-type-patterns.md](./references/exception-and-type-patterns.md) | Using TryCatch, Throw, or `s:` types (DateTime, Exception, Guid) | The `s:` prefix rule, TryCatch XAML pattern (3 places), type mappings |
| [excel-workbook-activities.md](./references/excel-workbook-activities.md) | Working with Excel read/write/filter | Classic vs Business activities, Read/Write/Filter XAML with LINQ |
| [discovery-and-resolution.md](./references/discovery-and-resolution.md) | Stuck on activity resolution, need full discovery workflow | 9-step discovery flow, activity doc lookup, provider disambiguation, examples |

### EXPERT — load only when specifically needed (rare / edge cases)

| File | Load when |
|------|----------|
| [project-structure.md](./references/project-structure.md) | Need to understand project.json fields, folder layout, or package versions |
| [jit-custom-types-schema.md](./references/jit-custom-types-schema.md) | Working with dynamic/connector activities that produce JIT custom types |
| [connector-capabilities.md](./references/connector-capabilities.md) | Building Integration Service connector workflows |
| [ui-automation-guide.md](./references/ui-automation-guide.md) | Building UI automation with screen element targets |

---

## Escape hatches

| Problem | Solution |
|---------|---------|
| Don't know the class name | `uip rpa find-activities --query "keyword"` |
| Don't know the XAML properties | `uip rpa get-default-activity-xaml --activity-class-name "ClassName"` |
| CLI command fails | Run it with `--help` to see correct syntax |
| Activity docs missing | Install/update the package, then check `.local/docs/` again |
| Stuck on error after 3 tries | Tell the user the exact error and ask for guidance |
| Need to see what Studio has open | `uip rpa list-instances` |
| Timeout on CLI command | Add `--timeout 600` before the subcommand |

---

## Anti-patterns (NEVER do these)

- Generate XAML properties from memory (use docs or `get-default-activity-xaml`)
- Use `uip rpa new` (does not exist, use `create-project`)
- Pass absolute paths to `get-errors --file-path` (must be relative)
- Guess activity class names without searching first
- Build a 50-line workflow in one shot without validating incrementally
- Skip reading `project.json` before writing XAML
- Retry a failing command in a loop without reading the error message
