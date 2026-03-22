---
name: uipath-rpa-legacy
description: "Edit, create, build, and maintain legacy UiPath RPA projects (classic design experience, .NET Framework 4.6.1, VB.NET, XAML workflows) using uip rpa-legacy CLI. TRIGGER when: Legacy/classic RPA project detected (project.json with targetFramework 'Legacy' or absent targetFramework with .NET Framework dependencies); User mentions legacy workflows, classic activities (no 'X' suffix), VB.NET RPA expressions; User asks to create/edit/validate/analyze/package legacy UiPath automations; User asks to debug workflows via UiRobot; project.json has expressionLanguage 'VisualBasic' and classic activity package versions. DO NOT TRIGGER when: Project uses modern framework (targetFramework 'Portable' or 'Windows' with modern activities, 'X' suffix activities — use uipath-rpa-workflows instead); User works with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead); User asks about Orchestrator/deployment/CLI setup (use uipath-development instead)."
---

# Legacy RPA Workflow Architect

Legacy UiPath RPA projects: .NET Framework 4.6.1, VB.NET expressions, classic activities (no "X" suffix). Uses `uip rpa-legacy` CLI (standalone, no Studio IPC needed).

## Rules (Non-Negotiable)

1. **Discover before writing** — run `find-activities` + `type-definition` for exact CLR names/enums before any XAML. Activity docs cover behavior, NOT property names.
2. **Validate frequently** — for Sequences with well-known activities, write the full XAML then validate once. For Flowcharts/StateMachines/unfamiliar activities, validate after each addition. Always validate after edits to existing files.
3. **Absolute paths only** — store `{projectRoot}` as an absolute path at Phase 0. Pass it to every CLI command. **Never use `cd`.**
4. **Fix by category** — Package → Structure → Type → Properties → Logic. This order prevents cascading errors.
5. **Activity docs + CLI tools together** — docs for context/gotchas, CLI for precision. Neither alone is sufficient.
6. **Always use `--format json`** — for any CLI output you need to parse. **Never suppress stderr** (`2>/dev/null`) — error details are in the JSON output.

---

## Request Router

| Request | Action | Key Reference |
|---------|--------|---------------|
| Create workflow | Phase 0 → Discovery → Generate | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Edit workflow | Phase 0 → Discovery → Edit | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Validate file | `uip rpa-legacy validate "{projectRoot}/File.xaml" --format json` | [validation-and-fixing.md](./references/validation-and-fixing.md) |
| Validate project | `uip rpa-legacy validate "{projectRoot}" --format json` | [validation-and-fixing.md](./references/validation-and-fixing.md) |
| Analyze (only when asked) | `uip rpa-legacy analyze "{projectRoot}" --format json` | [cli-reference.md](./references/cli-reference.md) |
| Package (optional) | `uip rpa-legacy package "{projectRoot}" -o "{dir}"` | [cli-reference.md](./references/cli-reference.md) |
| Debug | `uip rpa-legacy debug "{projectRoot}/File.xaml"` | [cli-reference.md](./references/cli-reference.md) |
| Create new project | Create project.json with right packages | [project-structure.md](./references/project-structure.md) |
| Create test data | Generate Excel/CSV/JSON/types for testing | [test-data-guide.md](./references/test-data-guide.md) |

If unclear which file to edit, **ask the user**.

---

## Phase 0: Environment

1. Find `project.json` → establish `{projectRoot}` **as absolute path**
2. Read `project.json` → verify `targetFramework: "Legacy"` (or absent = Legacy)
3. Note `expressionLanguage` (VB.NET or C#)
4. Run `uip rpa-legacy validate "{projectRoot}" --format json` to trigger **package restore** (required before `find-activities` works)

No Studio needed. See [environment-setup.md](./references/environment-setup.md) for details.

---

## Phase 1: Discovery

**Read only what's needed for the task — don't load all docs upfront:**

| Task Type | Must Read | Also Read If Needed |
|-----------|-----------|-------------------|
| **Any workflow** | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md), run `find-activities` + `type-definition` | [common-pitfalls.md](./references/common-pitfalls.md) |
| Flowchart/StateMachine | + [_XAML-GUIDE.md](./references/activity-docs/_XAML-GUIDE.md) (ViewState layout) | |
| Uses Excel/CSV | + [Excel.md](./references/activity-docs/Excel.md) | |
| Uses Email | + [Mail.md](./references/activity-docs/Mail.md) | |
| Uses InvokeCode | + [_INVOKE-CODE.md](./references/activity-docs/_INVOKE-CODE.md) | |
| REFramework project | + [_REFRAMEWORK.md](./references/activity-docs/_REFRAMEWORK.md) | |
| Don't know which package | [_INDEX.md](./references/activity-docs/_INDEX.md) | `find-package --query "..."` |
| VB.NET expression help | [_PATTERNS.md](./references/activity-docs/_PATTERNS.md) | |
| Stuck | `uip docsai ask "..."` → `WebSearch` → ask user | |

**CLI tools (mandatory for every activity):**
- `uip rpa-legacy find-activities "{projectRoot}" --query "..." --format json` — returns class names, arguments, **XAML snippet**, **xmlns**, **body pattern**. Use `XamlSnippet` as starting point.
- `uip rpa-legacy type-definition "{projectRoot}" --type "TypeName" --format json` — exact enum values, type members

See [discovery-workflow.md](./references/discovery-workflow.md) for detailed step-by-step procedure.

---

## Phase 2: Generate or Edit

### Before Writing ANY XAML

- [ ] Read relevant activity doc (behavioral context)
- [ ] Run `find-activities` for every activity — use returned `XamlSnippet` + `XmlnsDeclaration` as starting point
- [ ] Run `type-definition` for every enum/complex type (exact values)
- [ ] Read [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for XAML structure
- [ ] Read [common-pitfalls.md](./references/common-pitfalls.md) for gotchas

### Choose Workflow Type

| Pattern | Use When |
|---------|----------|
| **Sequence** | Linear step-by-step, no branching |
| **Flowchart** | Branching decisions, loops with conditions, complex control flow |
| **StateMachine** | Distinct states with transitions (REFramework, approval workflows) |

### Flowchart/StateMachine: Plan Layout FIRST

Before writing XAML for Flowchart or StateMachine:
1. List all nodes and connections
2. Assign coordinates per layout guide in [_XAML-GUIDE.md](./references/activity-docs/_XAML-GUIDE.md)
3. Map True/False branch paths (Flowchart) or transition routes (StateMachine)

**ViewState is MANDATORY** — without it, Studio stacks all nodes at (0,0).

### CREATE Checklist

- [ ] Root `<Activity>` has `mva:VisualBasic.Settings="{x:Null}"` (VB projects)
- [ ] xmlns uses `assembly=mscorlib` (not `System.Private.CoreLib`)
- [ ] VB.NET: `[bracket]` notation for expressions
- [ ] Classic activity names (no "X" suffix)
- [ ] All 16 baseline assembly references present (see [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md))
- [ ] All 21 baseline namespace imports present
- [ ] Package-specific assembly refs + namespace imports added for every activity package used
- [ ] Flowchart/StateMachine: `xmlns:av` declared, ViewState on every node
- [ ] Scope activities: `ActivityAction<T>` body pattern (see [common-pitfalls.md](./references/common-pitfalls.md))

### EDIT Checklist

- [ ] Read current XAML content before editing
- [ ] Use `Edit` tool with exact `old_string` match
- [ ] Flowchart/StateMachine: read existing ViewState positions, place new nodes with ≥110px vertical / ≥200px horizontal clearance
- [ ] Validate after every edit

---

## Phase 3: Validate & Fix

```
LOOP (per-file during iteration):
  validate "{projectRoot}/File.xaml" → 0 errors? → next activity
                                     → errors?   → categorize → fix → validate again

FINAL (before completing):
  validate "{projectRoot}" → 0 errors across entire project? → DONE
```

**Fix order:** Package → Structure → Type → Properties → Logic

| Category | Fix Strategy |
|----------|-------------|
| **Package** | Ask user to install in Studio (no CLI install command) |
| **Structure** | Read XAML around error → Edit to fix XML |
| **Type** | `type-definition` for exact enum/type values |
| **Properties** | `find-activities --include-type-definitions` for exact property names |
| **Logic** | Check expression language, consult `_PATTERNS.md`, use `debug` |

When stuck: `docsai ask` → `WebSearch` → ask user.

See [validation-and-fixing.md](./references/validation-and-fixing.md) for detailed procedures and common error scenarios.

---

## Phase 4: Debug

**Only when the user asks to test/run the workflow.** Do not auto-trigger. Suggest it after completing validation: _"Would you like me to run the workflow to test it?"_

**Always validate before debugging** — don't debug a file with compilation errors.

```bash
# Basic execution
uip rpa-legacy debug "{projectRoot}/Main.xaml"

# With input arguments
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx", "in_Count": 5}'

# Capture result to file
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx"}' --result-path /tmp/result.json --trace-level Error
```

**Reading results:**
- Exit code 0 → success: read `Data.Output` for out-argument values
- Exit code 1 → failure: read `Data.Error` for diagnostics:
  - `Error.ActivityDisplayName` + `Error.XamlFile` → locate the problem
  - `Error.ExceptionType` + `Error.Message` → understand it
  - `Error.StackTrace` → full call chain
  - `Data.ErrorLog` → all error-level robot log entries for context

**Fix-and-retry loop:** edit XAML → validate → debug again.

See [cli-reference.md](./references/cli-reference.md) for all options.

---

## Phase 5: Response Checklist

- [ ] File path of created/edited workflow
- [ ] Brief description of what the workflow does
- [ ] Key activities and logic
- [ ] Packages required (note manual installs)
- [ ] Per-file validation passed during development
- [ ] Whole-project validation passed (`validate "{projectRoot}"`)
- [ ] Limitations and next steps
- [ ] Manual actions needed (package install, connection setup)

---

## Quick Reference

### CLI Commands

| Command | Purpose |
|---------|---------|
| `uip rpa-legacy find-activities <path> --query "..." --format json` | Find activities, class names, arguments, **XAML snippet, xmlns** |
| `uip rpa-legacy type-definition <path> --type "..." --format json` | Inspect types, enum values, properties |
| `uip rpa-legacy validate <file-or-project-path> --format json` | Validate single file or entire project |
| `uip rpa-legacy analyze <path> --format json` | Run workflow analyzer rules (only when asked) |
| `uip rpa-legacy find-package --query "..." --format json` | Search NuGet feeds for packages |
| `uip rpa-legacy package <path> -o <dir>` | Package into .nupkg (optional) |
| `uip rpa-legacy debug <xaml-path> -i '...'` | Execute via UiRobot |
| `uip docsai ask "question" --format json` | Search UiPath documentation |

Full reference: [cli-reference.md](./references/cli-reference.md)

### Reference Files

| File | Content |
|------|---------|
| [cli-reference.md](./references/cli-reference.md) | All CLI commands, parameters, error recovery |
| [discovery-workflow.md](./references/discovery-workflow.md) | Detailed discovery steps, troubleshooting |
| [environment-setup.md](./references/environment-setup.md) | Project root detection, legacy verification |
| [project-structure.md](./references/project-structure.md) | Legacy project layout, project.json schema |
| [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) | XAML anatomy, expressions, safety rules |
| [common-pitfalls.md](./references/common-pitfalls.md) | Dangerous defaults, scope patterns, gotchas |
| [validation-and-fixing.md](./references/validation-and-fixing.md) | Validate/analyze loop, error scenarios |
| [test-data-guide.md](./references/test-data-guide.md) | Excel, CSV, JSON, top 10 file types and UiPath types |

### Activity Docs (`references/activity-docs/`)

| File | Content |
|------|---------|
| `_INDEX.md` | Master index with adoption rankings |
| `_PATTERNS.md` | VB.NET cheat sheet, DataTable ops, error handling |
| `_XAML-GUIDE.md` | XAML internals, Flowchart/StateMachine layout guides |
| `_COMMON-PITFALLS.md` | Real-world gotchas by package |
| `_INVOKE-CODE.md` | InvokeCode: properties, templates, compilation |
| `_REFRAMEWORK.md` | REFramework template structure and customization |
| `_DU-PROCESS.md` | Document Understanding pipeline template |
| `AllActivities.md` | Complete legacy activity catalog |
| `{Package}.md` | Per-package docs (Excel, Mail, System, UIAutomation, etc.) |

---

## Never Do

- **Use `cd`** to change working directory — pass absolute `{projectRoot}` to every CLI command
- **Suppress stderr** with `2>/dev/null` — error details are in the JSON output
- Guess enum values or property names — always use `find-activities` + `type-definition`
- Skip CLI discovery (find-activities + type-definition are mandatory for valid XAML)
- Use modern "X" suffix activities in legacy projects
- Use `assembly=System.Private.CoreLib` — legacy uses `assembly=mscorlib`
- Use `[bracket]` expressions in C# projects — use `<mca:CSharpValue>` instead
- Generate Flowchart/StateMachine without ViewState
- Retry failing CLI commands without diagnosing root cause
