---
name: uipath-rpa-legacy
description: "Edit, create, build, and maintain legacy UiPath RPA projects (classic design experience, .NET Framework 4.6.1, VB.NET, XAML workflows) using uip rpa-legacy CLI. TRIGGER when: Legacy/classic RPA project detected (project.json with targetFramework 'Legacy' or absent targetFramework with .NET Framework dependencies); User mentions legacy workflows, classic activities (no 'X' suffix), VB.NET RPA expressions; User asks to create/edit/validate/analyze/build legacy UiPath automations; User asks to debug workflows via UiRobot; project.json has expressionLanguage 'VisualBasic' and classic activity package versions. DO NOT TRIGGER when: Project uses modern framework (targetFramework 'Portable' or 'Windows' with modern activities, 'X' suffix activities — use uipath-rpa-workflows instead); User works with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead); User asks about Orchestrator/deployment/CLI setup (use uipath-development instead)."
---

# Legacy RPA Workflow Architect

Legacy UiPath RPA projects: .NET Framework 4.6.1, VB.NET expressions, classic activities (no "X" suffix). Uses `uip rpa-legacy` CLI (standalone, no Studio IPC needed).

## Rules (Non-Negotiable)

1. **Discover before writing** — run `find-activities` + `type-definition` for exact CLR names/enums before any XAML. Activity docs cover behavior, NOT property names.
2. **One activity at a time** — write ONE activity → `validate` → fix → next. Never batch-write.
3. **Validate after every change** — `uip rpa-legacy validate` after every XAML edit. No exceptions.
4. **Fix by category** — Package → Structure → Type → Properties → Logic. This order prevents cascading errors.
5. **Activity docs + CLI tools together** — docs for context/gotchas, CLI for precision. Neither alone is sufficient.
6. **Always use `--format json`** — for any CLI output you need to parse.

---

## Request Router

| Request | Action | Key Reference |
|---------|--------|---------------|
| Create workflow | Phase 0 → Discovery → Generate | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Edit workflow | Phase 0 → Discovery → Edit | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) |
| Validate | `uip rpa-legacy validate "{projectRoot}/File.xaml" --format json` | [validation-and-fixing.md](./references/validation-and-fixing.md) |
| Analyze | `uip rpa-legacy analyze "{projectRoot}" --format json` | [cli-reference.md](./references/cli-reference.md) |
| Build | `uip rpa-legacy build "{projectRoot}" -o "{dir}"` | [cli-reference.md](./references/cli-reference.md) |
| Debug | `uip rpa-legacy debug "{projectRoot}/File.xaml"` | [cli-reference.md](./references/cli-reference.md) |
| Create test data | Generate Excel/CSV/JSON/types for testing | [test-data-guide.md](./references/test-data-guide.md) |

If unclear which file to edit, **ask the user**.

---

## Phase 0: Environment

1. Find `project.json` → establish `{projectRoot}`
2. Read `project.json` → verify `targetFramework: "Legacy"` (or absent = Legacy)
3. Note `expressionLanguage` (VB.NET or C#)

No Studio needed. See [environment-setup.md](./references/environment-setup.md) for details.

---

## Phase 1: Discovery

**What you need → Where to find it:**

| Need | Tool / File |
|------|------------|
| Project structure, packages, expression language | `Glob **/*.xaml` + `Read project.json` |
| What an activity does, gotchas, patterns | `references/activity-docs/{PackageName}.md` |
| Which package for a capability | [activity-docs/_INDEX.md](./references/activity-docs/_INDEX.md) |
| VB.NET expression syntax | [activity-docs/_PATTERNS.md](./references/activity-docs/_PATTERNS.md) |
| XAML structure, templates, ViewState layout | [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) + [_XAML-GUIDE.md](./references/activity-docs/_XAML-GUIDE.md) |
| Dangerous defaults, scope requirements | [common-pitfalls.md](./references/common-pitfalls.md) |
| **Exact class names, argument types** | `uip rpa-legacy find-activities "{projectRoot}" --query "..." --format json` **← MANDATORY** |
| **Exact enum values, type members** | `uip rpa-legacy type-definition "{projectRoot}" --type "TypeName" --format json` **← MANDATORY** |
| InvokeCode patterns | [activity-docs/_INVOKE-CODE.md](./references/activity-docs/_INVOKE-CODE.md) |
| REFramework structure | [activity-docs/_REFRAMEWORK.md](./references/activity-docs/_REFRAMEWORK.md) |
| Document Understanding pipeline | [activity-docs/_DU-PROCESS.md](./references/activity-docs/_DU-PROCESS.md) |
| Official UiPath docs (fallback) | `uip docsai ask "question" --format json` |
| Community solutions (last resort) | `WebSearch` — UiPath Forum, Stack Overflow, GitHub, Reddit |

**Activity docs cover behavior. CLI tools give precision. Both are mandatory.**

See [discovery-workflow.md](./references/discovery-workflow.md) for detailed step-by-step procedure with examples.

---

## Phase 2: Generate or Edit

### Before Writing ANY XAML

- [ ] Read relevant activity doc (behavioral context)
- [ ] Run `find-activities` for every activity (exact class names)
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
- [ ] Standard namespace imports and assembly references
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
LOOP:
  validate → 0 errors? → DONE
           → errors?   → categorize → fix highest category → validate again
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

## Phase 4-5: Build & Debug

```bash
# Build to .nupkg
uip rpa-legacy build "{projectRoot}" -o "{dir}" --version "1.0.0"

# Debug via UiRobot (CAUTION: performs real actions)
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --timeout 120
```

See [cli-reference.md](./references/cli-reference.md) for all options.

---

## Phase 6: Response Checklist

- [ ] File path of created/edited workflow
- [ ] Brief description of what the workflow does
- [ ] Key activities and logic
- [ ] Packages required (note manual installs)
- [ ] Validation result (0 errors or documented remaining)
- [ ] Limitations and next steps
- [ ] Manual actions needed (package install, connection setup)

---

## Quick Reference

### CLI Commands

| Command | Purpose |
|---------|---------|
| `uip rpa-legacy find-activities <path> --query "..." --format json` | Find activities, class names, arguments |
| `uip rpa-legacy type-definition <path> --type "..." --format json` | Inspect types, enum values, properties |
| `uip rpa-legacy validate <xaml-path> --format json` | Check XAML for compilation errors |
| `uip rpa-legacy analyze <path> --format json` | Run workflow analyzer rules |
| `uip rpa-legacy build <path> -o <dir>` | Package into .nupkg |
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

- Batch-write multiple activities before validating
- Guess enum values or property names — always use `find-activities` + `type-definition`
- Skip discovery steps 4-5 (CLI tools are mandatory for valid XAML)
- Use modern "X" suffix activities in legacy projects
- Use `assembly=System.Private.CoreLib` — legacy uses `assembly=mscorlib`
- Use `[bracket]` expressions in C# projects — use `<mca:CSharpValue>` instead
- Generate Flowchart/StateMachine without ViewState
- Retry failing CLI commands without diagnosing root cause
