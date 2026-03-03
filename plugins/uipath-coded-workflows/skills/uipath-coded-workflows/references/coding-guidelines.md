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
- **When writing UI automation code** — follow the **Finding Descriptors** hierarchy (see ui-automation.md) in strict order. Do NOT write any UI code until descriptors are resolved:
  1. Read `ObjectRepository.cs` — use existing descriptors if present
  2. Inspect UILibrary/descriptor NuGet packages in `project.json` (e.g. `*.Descriptors`, `*.UILibrary`) using inspect-package tool. **If inspect-package returns 404** (private/local feed), check the local NuGet cache at `~/.nuget/packages/<package-name>/<version>/` — read `.metadata` files under `contentFiles/any/any/.objects/` to discover App/Screen/Element hierarchy
  3. If descriptors are still missing — use `indicate-application` / `indicate-element` to capture them. `indicate-application` can be called without `--parent-id` or `--parent-name` — when no App exists in `.objects/`, it creates one automatically. No need to ask the user to manually create an App in Studio
  4. UITask (ScreenPlay) is ONLY for when indicated selectors are genuinely brittle/unreliable — NEVER as a first approach
  5. NEVER bypass Object Repository by constructing `TargetAppModel` with raw URL/BrowserType
- Use inspect-package tool for API discovery when documentation is unclear

### Code Quality
- **Start simple, iterate** — Create minimal working version first, then refine
- **Only include using statements for packages in project.json** — Adding unused usings causes compile errors
- **Match input parameter names exactly** — Execute method signature must match `--input` arguments (case-sensitive)
- **Escape backslashes in paths** — Use `C:\\path\\file.txt` not `C:\path\file.txt` in input arguments

### Validation Loop (Critical Rule #14)
After every create or edit, validate the specific file until clean (max 5 fix attempts):
```bash
rpa-tool validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```
- `validate` forces Studio to re-analyze the file AND returns errors in its JSON response — a single command for both
- If errors are returned: fix the code, then run `validate` again on the same file
- A file is only considered valid when `validate` returns zero errors
- **Stop after 5 failed fix attempts** — present the remaining errors to the user; they may require domain knowledge or environment-specific fixes
- Use `--file-path` to target the specific file you changed — faster than validating the whole project
- `get-errors` only returns cached state — prefer `validate` when files have been changed outside Studio

### Error Handling
- **Fix compilation errors methodically** — Categorize: Syntax → Type → Logic. Use the validation loop above to iterate until clean.
- **Retry on execution failures** — Attempt to fix and retry up to 2 times before asking user
- **Analyze errors carefully** — Read error messages, identify root cause, make targeted fixes
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

- Never manually write `project.json` or `project.uiproj` when creating a new project — use `rpa-tool create-project` (Critical Rule #1)
- Never generate C# code without first searching for existing .cs files (API Discovery)
- Never edit files without reading them first
- Never skip the `[Workflow]` or `[TestCase]` attribute on the Execute method (Critical Rule #4)
- Never forget to inherit from `CodedWorkflow` (except Coded Source Files) (Critical Rule #3)
- Never add `using` statements for packages not in `project.json` — causes CS errors
- Never guess service method names — verify with existing code or inspect-package tool

### UI Automation

- Never hardcode UI selectors — use Object Repository descriptors
- Never write UI code referencing descriptors without first reading `ObjectRepository.cs`
- Never skip the indicate step when a descriptor is missing — use `indicate-application` / `indicate-element`
- Never use UITask (ScreenPlay) as the primary approach — resolve descriptors via Finding Descriptors hierarchy first (Critical Rule #15)
- Never skip indicating elements because it "seems tedious" — indicate ALL missing elements
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
- Never make unrelated changes during retry — only fix the specific error
- Never execute a workflow with parameters without providing `--input` arguments
- Never use parameter names in `--input` that don't match the Execute method signature (case-sensitive)

### Shell & Environment

- Never redirect output to `nul` — use `> /dev/null 2>&1` instead (`nul` creates a literal file on Windows)
- Never use Windows shell commands (`del`, `dir`, `copy`) in bash — use `rm`, `ls`, `cp`

## Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| **"Studio X.X.X does not have interop support"** | Auto-detected Studio is too old (< 26.2) | Always pass `--studio-dir "<STUDIO_DIR>"` pointing to the dev build |
| **No Studio instances found** | Studio is not running | Run `rpa-tool start-studio --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>"` |
| **Stale pipe / ENOENT** | Studio instance crashed or was closed | The tool retries automatically; if persistent, restart Studio |
| **Workflow cannot be found** | Entrypoint not in project.json | Verify project.json entrypoint has the file listed |
| **Service property not available** | Missing package dependency | Add required package to project.json dependencies |
| **Timeout** | Studio took too long to start | Increase timeout: `--timeout 600` |
| **`rpa-tool` command not found** | Not linked globally | Run `cd RpaTool/rpa-tool && bun run build && bun link` |
| **"Target name 'X' is not part of the current screen"** | Element descriptor used on wrong screen handle | Use the `UiTargetApp` handle from `Open`/`Attach` for the screen that owns the element |
| **"Cannot select item. It was not found among existing items"** | `SelectItem` fails on web dropdowns | Use `TypeInto` instead of `SelectItem` for web `<select>` elements |
| **inspect-package returns 404 for UILibrary package** | Package is on a private/local NuGet feed | Check local NuGet cache: `~/.nuget/packages/<name>/<version>/contentFiles/any/any/.objects/` |
| **Studio rejects manually created project** | Missing metadata dirs, wrong schema/version | Always use `rpa-tool create-project` instead of writing `project.json` manually |
| **"No application version found matching parentId=..."** | AppVersion reference is stale (OR was reset/cleared in Studio) or App was never properly created | Re-read `.objects/` metadata to get fresh AppVersion reference. If `.objects/` has no App, call `indicate-application` without `--parent-id` — it creates the App automatically |
| **`.objects/` has subdirectories but no `.metadata` files** | Corrupted/incomplete App structure from a previous failed or partial creation | Clear the orphan directories and run `indicate-application` without `--parent-id` to create a fresh App |
