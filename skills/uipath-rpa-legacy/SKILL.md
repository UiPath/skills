---
name: uipath-rpa-legacy
description: "[PREVIEW] Legacy UiPath RPA (.NET Framework 4.6.1, XAML) via uip rpa-legacy CLI. TRIGGER: project.json targetFramework 'Legacy' or absent; user mentions legacy. For Windows/cross-platform→uipath-rpa."
---

# Legacy RPA Workflow Architect

Legacy UiPath RPA projects: .NET Framework 4.6.1, VB.NET expressions, classic activities (no "X" suffix). Uses `uip rpa-legacy` CLI (standalone, no Studio IPC needed).

## Critical Rules

1. **Discover before writing** — for built-in activities (If, Assign, TryCatch, LogMessage, etc.), use XAML from `_BUILT-IN-ACTIVITIES.md` directly. For all others, run `find-activities` + `type-definition` first.
2. **Validate frequently** — for Sequences with well-known activities, write the full XAML then validate once. For Flowcharts/StateMachines/unfamiliar activities, validate after each addition. Always validate after edits to existing files.
3. **Absolute paths only** — store `{projectRoot}` as an absolute path at Phase 0. Pass it to every CLI command. **Never use `cd`.**
4. **Fix by category** — Package → Structure → Type → Properties → Logic. This order prevents cascading errors.
5. **Activity docs for gotchas, CLI for precision** — read package docs (Excel.md, Mail.md) for gotchas before using those packages. Run `find-activities` only for activities not in `_BUILT-IN-ACTIVITIES.md`.
6. **Always use `--output json`** — for any CLI output you need to parse. **Never suppress stderr** (`2>/dev/null`) — error details are in the JSON output.
7. **Never guess enum values or property names** — always use `find-activities` + `type-definition`. CLI discovery is mandatory for valid XAML.
8. **Never use modern assemblies** — use `assembly=mscorlib` (not `System.Private.CoreLib`). Use `[bracket]` expressions in VB.NET projects, `<mca:CSharpValue>` in C# projects.
9. **Never generate Flowchart/StateMachine without ViewState** — Studio stacks all nodes at (0,0) without it.
10. **Never retry failing CLI commands blindly** — diagnose the root cause before retrying.

---

## Request Router

| Request | Action | Key Reference |
|---------|--------|---------------|
| Choose architecture | Sequence vs REFramework vs Dispatcher/Performer | [project-organization-guide.md](./references/project-organization-guide.md) |
| Create workflow | Phase 0 → Discovery → Generate | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Edit workflow | Phase 0 → Discovery → Edit | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Validate file | `uip rpa-legacy validate "{projectRoot}/File.xaml" --output json` | [validation-and-fixing.md](./references/validation-and-fixing.md) |
| Validate project | `uip rpa-legacy validate "{projectRoot}" --output json` | [validation-and-fixing.md](./references/validation-and-fixing.md) |
| Package (optional) | `uip rpa-legacy package "{projectRoot}" -o "{dir}"` | [cli-reference.md](./references/cli-reference.md) |
| Debug | `uip rpa-legacy debug "{projectRoot}/File.xaml"` | [cli-reference.md](./references/cli-reference.md) |
| Create new project | Create project.json with right packages | [project-structure.md](./references/project-structure.md) |
| Create test data | Generate Excel/CSV/JSON/types for testing | [test-data-guide.md](./references/test-data-guide.md) |
| Organize project | Folder structure, naming, libraries | [project-organization-guide.md](./references/project-organization-guide.md) |
| Add error handling | TryCatch, Retry Scope, exception classification | [error-handling-guide.md](./references/error-handling-guide.md) |
| Fix/build selectors | Selector anatomy, dynamic selectors, anchors | [selector-guide.md](./references/selector-guide.md) |
| Create tests | Test design, mock testing, verification | [testing-guide.md](./references/testing-guide.md) |

If unclear which file to edit, **ask the user**.

---

## Phase 0: Environment

1. Find `project.json` → establish `{projectRoot}` **as absolute path**
2. Read `project.json` → verify `targetFramework: "Legacy"` (or absent = Legacy)
3. Note `expressionLanguage` (VB.NET or C#)
4. Note project shape: count `.xaml` files, list `dependencies` keys and versions — use this to avoid re-discovering packages and activities already explored earlier in conversation
5. Run `uip rpa-legacy validate "{projectRoot}" --output json` to trigger **package restore** (required before `find-activities` works)

No Studio needed. See [environment-setup.md](./references/environment-setup.md) for details.

---

## Phase 1: Discovery

**Start with the minimum. Add more only as needed.**

1. Read [_BUILT-IN-ACTIVITIES.md](./references/activity-docs/_BUILT-IN-ACTIVITIES.md) — complete XAML for If, Assign, Sequence, TryCatch, ForEach, While, Switch, Throw, LogMessage, InvokeCode, ForEachRow, etc. **No CLI calls needed for these.**

2. Read [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) — XAML structure, baseline assembly references, safety rules.

3. **Only if you need non-built-in activities** (Excel, Mail, HTTP, PDF, etc.):
   - Run `find-activities "{projectRoot}" --query "..." --output json` for each — use returned `XamlSnippet`
   - Run `type-definition` for any enums in the results
   - Read the relevant package doc ([Excel.md](./references/activity-docs/Excel.md), [Mail.md](./references/activity-docs/Mail.md), etc.) for gotchas

4. **Only if Flowchart/StateMachine**: read [_XAML-GUIDE.md](./references/activity-docs/_XAML-GUIDE.md) for ViewState layout

**Stop here.** Don't read more files unless you hit a problem during validation. Additional references if needed: [_PATTERNS.md](./references/activity-docs/_PATTERNS.md) (VB.NET expressions), [common-pitfalls.md](./references/common-pitfalls.md) (gotchas), [_INVOKE-CODE.md](./references/activity-docs/_INVOKE-CODE.md) (InvokeCode details), [_REFRAMEWORK.md](./references/activity-docs/_REFRAMEWORK.md) (REFramework), `uip docsai ask "..."` (official docs), `WebSearch` (community).

5. **If the task involves design decisions**, read the relevant guide on demand:
   - Error handling strategy → [error-handling-guide.md](./references/error-handling-guide.md)
   - UI selectors → [selector-guide.md](./references/selector-guide.md)
   - Project structure / libraries → [project-organization-guide.md](./references/project-organization-guide.md)
   - Advanced data manipulation (RegEx, LINQ, JObject) → [data-manipulation-guide.md](./references/data-manipulation-guide.md)
   - Orchestrator integration (queues, assets, triggers) → [orchestrator-guide.md](./references/orchestrator-guide.md)
   - Test design / debugging → [testing-guide.md](./references/testing-guide.md)

See [discovery-workflow.md](./references/discovery-workflow.md) for the full step-by-step procedure.

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
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx"}' --result-path /tmp/result.json --log-level error
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
| `uip rpa-legacy find-activities <path> --query "..." [--exact] --output json` | Find activities, class names, arguments, **XAML snippet, xmlns** |
| `uip rpa-legacy type-definition <path> --type "..." --output json` | Inspect types, enum values, properties |
| `uip rpa-legacy validate <file-or-project-path> --output json` | Validate single file or entire project |
| `uip rpa-legacy find-package --query "..." --output json` | Search NuGet feeds for packages |
| `uip rpa-legacy package <path> -o <dir>` | Package into .nupkg (optional) |
| `uip rpa-legacy debug <xaml-path> -i '...'` | Execute via UiRobot |
| `uip docsai ask "question" --output json` | Search UiPath documentation |

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
| [validation-and-fixing.md](./references/validation-and-fixing.md) | Validate & fix loop, error scenarios |
| [test-data-guide.md](./references/test-data-guide.md) | Excel, CSV, JSON, top 10 file types and UiPath types |
| [error-handling-guide.md](./references/error-handling-guide.md) | Exception classification, TryCatch patterns, Retry Scope, ContinueOnError |
| [selector-guide.md](./references/selector-guide.md) | Selector anatomy, dynamic selectors, anchors, validation checklist |
| [project-organization-guide.md](./references/project-organization-guide.md) | Folder conventions, naming, Config.xlsx, libraries, single responsibility |
| [data-manipulation-guide.md](./references/data-manipulation-guide.md) | RegEx, advanced LINQ, JObject/JArray, StringBuilder, type conversions |
| [orchestrator-guide.md](./references/orchestrator-guide.md) | Queue lifecycle, asset types, logging levels, triggers, environments |
| [testing-guide.md](./references/testing-guide.md) | Test design, verification activities, mock testing, debugging strategy |

### Activity Docs (`references/activity-docs/`)

| File | Content |
|------|---------|
| `_BUILT-IN-ACTIVITIES.md` | **Top 20 activities with complete XAML — no find-activities needed** |
| `_INDEX.md` | Master index with adoption rankings |
| `_PATTERNS.md` | VB.NET cheat sheet, DataTable ops, error handling |
| `_XAML-GUIDE.md` | XAML internals, Flowchart/StateMachine layout guides |
| `_COMMON-PITFALLS.md` | Real-world gotchas by package |
| `_INVOKE-CODE.md` | InvokeCode: properties, templates, compilation |
| `_REFRAMEWORK.md` | REFramework template structure and customization |
| `_DU-PROCESS.md` | Document Understanding pipeline template |
| `AllActivities.md` | Complete legacy activity catalog |
| `{Package}.md` | Per-package docs (Excel, Mail, System, UIAutomation, etc.) |

