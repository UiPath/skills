# Coding Guidelines Reference

Detailed coding rules, best practices, anti-patterns, and troubleshooting for UiPath coded workflows.

## Using Statements Rules

**CRITICAL: Only include `using` statements for namespaces actually used in the file.** Adding usings for packages not in `project.json` will cause compile errors.

**Minimal using statements** (always safe in any workflow/test case file):
```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
```

**Add based on actual usage** — only include these when the file uses the corresponding types/services AND the package is in `project.json`:
```csharp
// If using system.* service (UiPath.System.Activities package):
using UiPath.Core;
using UiPath.Core.Activities.Storage;       // only if using storage APIs
using UiPath.Orchestrator.Client.Models;    // only if using Orchestrator models

// If using testing.* service (UiPath.Testing.Activities package):
using UiPath.Testing;
using UiPath.Testing.Enums;                 // only if using testing enums
using UiPath.Testing.Activities.TestData;   // only if using test data queues

// If using uiAutomation.* service (UiPath.UIAutomation.Activities package):
using UiPath.UIAutomationNext.API.Contracts;
using UiPath.UIAutomationNext.API.Models;
using UiPath.UIAutomationNext.Enums;

// If using Object Repository descriptors (Descriptors.App.Screen.Element):
using <ProjectNamespace>.ObjectRepository;  // e.g. using RoboticEnterpriseFramework.ObjectRepository;
// OR if descriptors come from a UILibrary NuGet package (not the project's own OR):
// using <PackageNamespace>.ObjectRepository;  // e.g. using MultipleApps.Descriptors.ObjectRepository;
// CRITICAL: Without this, you get CS0103: The name 'Descriptors' does not exist in the current context
// NOTE: When descriptors come from a UILibrary package, use the PACKAGE namespace, not the project namespace

// If using excel.* service (UiPath.Excel.Activities package):
using UiPath.Excel;
using UiPath.Excel.Activities;
using UiPath.Excel.Activities.API;
using UiPath.Excel.Activities.API.Models;

// If using word.* service (UiPath.Word.Activities package):
using UiPath.Word;
using UiPath.Word.Activities;
using UiPath.Word.Activities.API;
using UiPath.Word.Activities.API.Models;

// If using powerpoint.* service (UiPath.Presentations.Activities package):
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

// If using mail.* service (UiPath.Mail.Activities package):
using UiPath.Mail.Activities.Api;

// If using office365.* service (UiPath.MicrosoftOffice365.Activities package):
using UiPath.MicrosoftOffice365.Activities.Api;

// If using google.* service (UiPath.GSuite.Activities package):
using UiPath.GSuite.Activities.Api;

// Standard .NET (add as needed):
using System.Data;           // DataTable
using System.Linq;           // LINQ
using System.IO;             // file operations
using System.Text.RegularExpressions;  // regex
```

**When adding a file that uses a service:**
1. Check `project.json` to confirm the required package is listed in `dependencies` — add it if missing
2. Add only the `using` statements needed for the types actually referenced in the file
3. Add the entry point or fileInfoCollection to `project.json` (for workflow or test case files only)

## Best Practices

### API Discovery
- **ALWAYS search for existing .cs files BEFORE generating new code** — Learn from existing patterns
- Read at least 5 existing workflow files (or all if fewer) to understand project conventions
- **When writing UI automation code** — follow the **Finding Descriptors** hierarchy (see [ui-automation-guide.md](../ui-automation-guide.md)) in strict order. Do NOT write any UI code until descriptors are resolved:
  1. Read `ObjectRepository.cs` — use existing descriptors if present
  2. Inspect UILibrary/descriptor NuGet packages in `project.json` (e.g. `*.Descriptors`, `*.UILibrary`) using `uip rpa inspect-package --use-studio`. The tool checks the local NuGet cache automatically. If the package is still not found, read `.metadata` files manually at `~/.nuget/packages/<package-name>/<version>/contentFiles/any/any/.objects/` to discover App/Screen/Element hierarchy
  3. If descriptors are still missing — use the `uia-configure-target` skill flow (found in the UIA activity-docs) to create targets. This handles snapshot capture, element discovery, selector generation, selector improvement, and OR registration. Do NOT manually call low-level `uip rpa uia` CLI commands outside of the skill flow. Fallback: `indicate-application` / `indicate-element` if the skill docs are unavailable
  4. UITask (ScreenPlay) is ONLY for when selectors are genuinely brittle/unreliable — NEVER as a first approach
  5. NEVER bypass Object Repository by constructing `TargetAppModel` with raw URL/BrowserType
- Use `uip rpa inspect-package --use-studio` for API discovery when documentation is unclear

### IResource / ILocalResource — Converting File Paths

Many activities (O365, GSuite, Mail, file operations) require `IResource` or `ILocalResource` instead of a string path. NEVER pass a raw string where `IResource` is expected — it will fail at runtime. NEVER try to construct `LocalResource(string)` directly — the constructor is internal.

| Method | Signature | Use when |
|--------|-----------|----------|
| `GetResourceForLocalPath` | `system.GetResourceForLocalPath(string path, PathType pathType)` → `IResource` | You have a path and need an `IResource` (no existence check needed) |
| `PathExists` (with out param) | `system.PathExists(string path, PathType pathType, out ILocalResource resource)` → `bool` | You need to verify the file exists AND get an `ILocalResource` |

```csharp
// Direct conversion — preferred when you know the file exists
IResource file = system.GetResourceForLocalPath(@"C:\Reports\report.pdf", PathType.File);
IResource folder = system.GetResourceForLocalPath(@"C:\Archive", PathType.Folder);

// With existence check
if (system.PathExists(@"C:\Reports\report.pdf", PathType.File, out ILocalResource localFile))
{
    // use localFile
}
```

`PathType` values: `PathType.File`, `PathType.Folder`

### Code Quality
- **Start simple, iterate** — Create minimal working version first, then refine
- **NEVER use C# `out` or `ref` keywords in `[Workflow]` methods** — The auto-generated `*+Activity.cs` wrapper does not handle them correctly, causing compile error CS1620. Studio regenerates the wrapper on every save, so manual fixes are reverted. Use return values or tuples for outputs instead
- **Only include using statements for packages in project.json** — Adding unused usings causes compile errors
- **Match input parameter names exactly** — Execute method signature must match `--input` arguments (case-sensitive)
- **Escape backslashes in paths** — Use `C:\\path\\file.txt` not `C:\path\file.txt` in input arguments

### Validation Loop (Critical Rule #14)
uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --output json --use-studio

@../validation-guide.md

### Error Handling
- **Fix compilation errors methodically** — Categorize: Syntax → Type → Logic. Use the validation loop above to iterate until clean.
- **Retry on execution failures** — Attempt to fix and retry up to 2 times before asking user
- **Analyze errors carefully** — Read error messages, identify root cause, make targeted fixes
- **Fix one thing at a time** — When a runtime error occurs, identify the root cause, fix ONLY that, and re-run. Never bundle a speculative "improvement" (e.g., switching from TypeInto to KeyboardShortcut) with the actual fix (e.g., correcting a selector). Changing two things at once makes it impossible to verify which change resolved the issue — or whether the speculative change introduced a new one.
- **Don't give up too early** — But stop after 2 failed retries and present the user with options:
```
Workflow execution failed after 2 retry attempts.

**Error Details:** <specific error message and location>
**Suggested Fix:** <analysis of what went wrong>
**Next Steps:** Would you like me to:
A) <recommended fix approach>
B) <alternative approach>
C) <user-driven approach>
```

### File Operations
- **ALWAYS use Read tool before Edit tool** — Understand current state before making changes
- **Prefer editing over creating new files** — Build on existing work, avoid file bloat
- **Use Glob for file discovery** — Never guess file locations

## Anti-Patterns (What NOT to Do)

> Many of these reinforce SKILL.md Critical Rules. They are grouped by category for quick scanning.

### Project & Code Structure

- Never manually write `project.json` or `project.uiproj` when creating a new project — use `uip rpa create-project --use-studio` (Critical Rule #1)
- Never generate C# code without first searching for existing .cs files (API Discovery)
- Never edit files without reading them first
- Never skip the `[Workflow]` or `[TestCase]` attribute on the Execute method (Critical Rule #4)
- Never forget to inherit from `CodedWorkflow` (except Coded Source Files) (Critical Rule #3)
- Never add `using` statements for packages not in `project.json` — causes CS errors
- Never guess service method names — verify with existing code or `uip rpa inspect-package --use-studio`

### UI Automation

- Never hardcode UI selectors — use Object Repository descriptors
- Never write UI code referencing descriptors without first reading `ObjectRepository.cs`
- Never manually craft UI selectors by calling low-level `uip rpa uia` CLI commands (`snapshot capture`, `snapshot filter`, `selector-intelligence get-default-selector`) outside of the `uia-configure-target` skill flow — this skips selector improvement and OR registration
- Never skip the target configuration step when a descriptor is missing — use the `uia-configure-target` skill flow (fallback: `indicate-application` / `indicate-element`)
- Never use UITask (ScreenPlay) as the primary approach — resolve descriptors via Finding Descriptors hierarchy first (Critical Rule #15)
- Never skip configuring targets because it "seems tedious" — configure ALL missing elements
- Never launch the target application before running `uia-configure-target` — the skill captures the window tree first; only launch if the app is not found
- Never construct `TargetAppModel` with raw URL/BrowserType to bypass Object Repository
- Never skip checking UILibrary/descriptor NuGet packages in `project.json`
- Never use an element descriptor on the wrong screen handle — each `UiTargetApp` is bound to its screen. Wrong handle gives `"Target name 'X' is not part of the current screen."`
- Never use `SelectItem` on web dropdowns without a `TypeInto` fallback — web `<select>` elements often fail with `"Cannot select item"`
- Never forget `using <ProjectNamespace>.ObjectRepository;` (or `using <PackageName>.ObjectRepository;` for UILibrary packages) when referencing `Descriptors.*`

### Object Repository / Indicate Commands

- Never assume `.objects/` subdirectories mean a valid App exists — verify `.metadata` files are present
- Never cache or reuse AppVersion references across OR resets — always re-read `.objects/` metadata
- Never run indicate commands from outside the project directory — cwd must contain `project.json`
- Never use camelCase flags (`--parentId`) — use kebab-case: `--parent-id`, `--parent-name`
- Never use `--parent-name` with the App display name (e.g. `"Acme"`) — it matches AppVersion names (e.g. `"1.0.0"`). Use `--parent-id` instead
- Never use the App `_reference` from `ObjectRepository.cs` as `--parent-id` — read `.objects/` metadata for the AppVersion reference

### Validation & Execution

- Never assume create/edit succeeded without running the validation loop (Critical Rule #14)
- Never continue retrying indefinitely — stop after 5 validation fix attempts or 2 runtime execution retries
- Never make unrelated changes during retry — identify the root cause, fix only that, re-run and verify. Never bundle a speculative "improvement" with the actual fix (e.g., fixing a broken selector AND switching from TypeInto to KeyboardShortcut in the same edit). One change, one re-run.
- Never execute a workflow with parameters without providing `--input` arguments
- Never use parameter names in `--input` that don't match the Execute method signature (case-sensitive)

### Shell & Environment

- Never redirect output to `nul` — use `> /dev/null 2>&1` instead (`nul` creates a literal file on Windows)
- Never use Windows shell commands (`del`, `dir`, `copy`) in bash — use `rm`, `ls`, `cp`

## Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| **"Studio X.X.X does not have interop support"** | Auto-detected Studio is too old (< 26.2) | Always pass `--studio-dir "<STUDIO_DIR>"` pointing to the dev build |
| **No Studio instances found** | Studio is not running | Run `uip rpa start-studio --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>"` |
| **Stale pipe / ENOENT** | Studio instance crashed or was closed | The tool retries automatically; if persistent, restart Studio |
| **Workflow cannot be found** | Entrypoint not in project.json | Verify project.json entrypoint has the file listed |
| **Service property not available** | Missing package dependency | Add required package to project.json dependencies |
| **Timeout** | Studio took too long to start | Increase timeout: `--timeout 600` |
| **"Target name 'X' is not part of the current screen"** | Element descriptor used on wrong screen handle | Use the `UiTargetApp` handle from `Open`/`Attach` for the screen that owns the element |
| **"Cannot select item. It was not found among existing items"** | `SelectItem` fails on web dropdowns | Use `TypeInto` instead of `SelectItem` for web `<select>` elements |
| **inspect-package cannot find UILibrary package** | Package is on a private/local NuGet feed | Use `--nupkg-path` to inspect the local `.nupkg` directly, or read `.metadata` files manually from `~/.nuget/packages/<name>/<version>/contentFiles/any/any/.objects/` |
| **Studio rejects manually created project** | Missing metadata dirs, wrong schema/version | Always use `uip rpa create-project --use-studio` instead of writing `project.json` manually |
