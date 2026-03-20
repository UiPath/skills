---
name: uipath-rpa-legacy
description: "Edit, create, build, and maintain legacy UiPath RPA projects (classic design experience, .NET Framework 4.6.1, VB.NET, XAML workflows) using uip rpa-legacy CLI. TRIGGER when: Legacy/classic RPA project detected (project.json with targetFramework 'Legacy' or absent targetFramework with .NET Framework dependencies); User mentions legacy workflows, classic activities (no 'X' suffix), VB.NET RPA expressions; User asks to create/edit/validate/analyze/build legacy UiPath automations; User asks to debug workflows via UiRobot; project.json has expressionLanguage 'VisualBasic' and classic activity package versions. DO NOT TRIGGER when: Project uses modern framework (targetFramework 'Portable' or 'Windows' with modern activities, 'X' suffix activities — use uipath-rpa-workflows instead); User works with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead); User asks about Orchestrator/deployment/CLI setup (use uipath-development instead)."
---

# Legacy RPA Workflow Architect

Edit, create, and maintain legacy UiPath RPA projects using a **discovery-first approach** with **iterative validation-driven refinement**. Legacy projects use the classic design experience (.NET Framework 4.6.1), primarily VB.NET expressions, and classic activities (no "X" suffix).

This skill uses `uip rpa-legacy` CLI commands (via `Bash`) and Claude Code's built-in tools (`Read`, `Write`, `Edit`, `Glob`, `Grep`) to interact with legacy UiPath projects and manage workflow files.

## Core Principles

1. **Discover Before You Write** — Never generate XAML without first running `find-activities` (for exact class names and argument signatures) and `type-definition` (for enum values and type details). The bundled activity reference docs cover behavior, gotchas, and patterns — but they do **NOT** contain the exact CLR namespaces, enum values, or property names needed for valid XAML. Guessing these values wastes validation cycles. Always use CLI discovery tools to get the precise information before writing.
2. **Know Before You Write** — Never generate XAML blind. Understand the project structure, installed packages, expression language (VB.NET vs C#), and existing workflow patterns. The deeper your understanding, the fewer validation cycles you'll need.
3. **One Activity at a Time** — Write the XAML for a single activity, validate it immediately with `uip rpa-legacy validate`, fix any errors, then move to the next activity. **Never batch-write multiple activities before validating.** Complex workflows emerge from validated building blocks, not from generating everything at once.
4. **Validate After Every Change** — Never assume an edit succeeded. Confirm with `uip rpa-legacy validate` after every single XAML modification. Do not batch edits. Optionally run `uip rpa-legacy analyze` for project-wide quality checks.
5. **Fix Errors by Category** — Triage errors in order: Package (missing dependencies) → Structure (invalid XML) → Type (wrong property types) → Activity Properties (misconfigured activity) → Logic (wrong behavior). Fixing in this order avoids cascading false errors.
6. **Activity Docs for Context, CLI Tools for Precision** — Use `references/activity-docs/` to understand what an activity does, its gotchas, and usage patterns. Use `find-activities` and `type-definition` to get the exact property names, types, and enum values you need for XAML. Both are essential — neither alone is sufficient.

---

## CLI Output Format

All `uip` commands support `--format <format>` (table, json, yaml, plain).

**Always use `--format json`** for commands whose output you need to parse or act on (e.g., `validate`, `find-activities`, `analyze`). JSON output is structured, unambiguous, and avoids table-formatting surprises.

Use the default (table) only when displaying results directly to the user for readability.

---

## Tool Quick Reference

For the full CLI command reference (all tools, parameters, and error recovery), see **[references/cli-reference.md](./references/cli-reference.md)**.

Key commands: `find-activities`, `type-definition`, `validate`, `analyze`, `build`, `debug`.

**The CLI is fully self-documenting.** Append `--help` at any level: `uip rpa-legacy --help`, `uip rpa-legacy validate --help`, etc.

**Key difference from `uip rpa`:** The `rpa-legacy` CLI is standalone — no Studio Desktop IPC required. It resolves dependencies from NuGet directly and uses UiRobot for execution.

---

## Supporting References

### Procedural Reference Files

- **[cli-reference.md](./references/cli-reference.md)** — Full `uip rpa-legacy` CLI command reference (all 6 commands, parameters, error recovery)
- **[environment-setup.md](./references/environment-setup.md)** — Phase 0 details: project root detection, legacy verification, authentication
- **[validation-and-fixing.md](./references/validation-and-fixing.md)** — Phase 3 details: validate/analyze loop, error categorization, fix strategies

### Domain Reference Files

- **[xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md)** — Legacy XAML file anatomy, VB.NET vs C# expressions, workflow types, safety rules. **CRITICAL: read before generating/editing any XAML.**
- **[project-structure.md](./references/project-structure.md)** — Legacy project directory layout, project.json schema, common packages
- **[common-pitfalls.md](./references/common-pitfalls.md)** — Dangerous defaults, required parent scopes, VB.NET cheat sheet, top gotchas by package

### Activity Reference Docs (Behavioral Knowledge Base)

The bundled activity reference docs at `references/activity-docs/` provide behavioral knowledge about legacy activities: what they do, their gotchas, required parent scopes, and usage patterns.

**CRITICAL LIMITATION:** These docs do **NOT** contain the exact CLR property names, enum values, or namespace paths needed for valid XAML. For those, you **MUST** use:
- `uip rpa-legacy find-activities` — exact class names, argument signatures
- `uip rpa-legacy type-definition` — enum values, type properties, methods

**Example:** The activity docs say InvokeCode has a "Language" property, but don't tell you the valid enum values. Running `type-definition --type "NetLanguage"` reveals `VBNet` and `CSharp` — not `VisualBasic` or `VB` (which are wrong and waste fix cycles).

**Entry points:**

| Need | Read |
|------|------|
| **Find which package covers a capability** | [activity-docs/_INDEX.md](./references/activity-docs/_INDEX.md) — Master index with adoption rankings |
| **VB.NET expression patterns** | [activity-docs/_PATTERNS.md](./references/activity-docs/_PATTERNS.md) — Cheat sheet for strings, dates, DataTables, error handling |
| **XAML structure and templates** | [activity-docs/_XAML-GUIDE.md](./references/activity-docs/_XAML-GUIDE.md) — File structure, VB vs C#, Sequence/Flowchart/StateMachine |
| **Real-world gotchas** | [activity-docs/_COMMON-PITFALLS.md](./references/activity-docs/_COMMON-PITFALLS.md) — Zombie processes, selector failures, dangerous defaults |
| **Complete activity catalog** | [activity-docs/AllActivities.md](./references/activity-docs/AllActivities.md) — Every legacy activity by package |
| **Invoke Code deep reference** | [activity-docs/_INVOKE-CODE.md](./references/activity-docs/_INVOKE-CODE.md) — InvokeCode activity: properties, XAML templates, code examples, compilation details |
| **REFramework template** | [activity-docs/_REFRAMEWORK.md](./references/activity-docs/_REFRAMEWORK.md) — State Machine project template: file structure, arguments, states, Config.xlsx, retry logic, test cases |
| **Document Understanding Process template** | [activity-docs/_DU-PROCESS.md](./references/activity-docs/_DU-PROCESS.md) — DU pipeline template: digitize, classify, extract, validate, train, export with Action Center |
| **Specific package** | `activity-docs/{PackageName}.md` — e.g., `Excel.md`, `Mail.md`, `System.md`, `UIAutomation.md` |

**Decision table:**

| Situation | Action |
|-----------|--------|
| **You know the package** | Read `references/activity-docs/{PackageName}.md` directly |
| **You don't know the package** | Read `references/activity-docs/_INDEX.md` to find it by capability |
| **Need VB.NET expression syntax** | Read `references/activity-docs/_PATTERNS.md` |
| **Need XAML structure guidance** | Read `references/activity-docs/_XAML-GUIDE.md` |
| **Need gotchas for a package** | Read `references/activity-docs/_COMMON-PITFALLS.md` |
| **Need complete activity list** | Read `references/activity-docs/AllActivities.md` |
| **Need InvokeCode patterns** | Read `references/activity-docs/_INVOKE-CODE.md` |
| **Working with REFramework project** | Read `references/activity-docs/_REFRAMEWORK.md` — file structure, arguments, states, Config.xlsx, customization points |
| **Working with Document Understanding** | Read `references/activity-docs/_DU-PROCESS.md` — pipeline steps, taxonomy, classifiers, extractors, Action Center |
| **Activity not in reference docs** | Use `uip rpa-legacy find-activities` to discover it |
| **Need exact property names or enum values for XAML** | **Always** use `find-activities` + `type-definition` — do not guess from activity docs alone |

---

## Core Workflow: Classify Request

**Determine the request type before proceeding:**

| Request Type | Trigger Words | Action |
|--------------|---------------|--------|
| **CREATE** | "generate", "create", "make", "build", "new workflow" | Phase 0 → Discovery → Generate |
| **EDIT** | "update", "change", "fix", "modify", "add to" | Phase 0 → Discovery → Edit |
| **VALIDATE** | "validate", "check errors", "compile" | Phase 0 → Validate |
| **ANALYZE** | "analyze", "check quality", "best practices" | Phase 0 → Analyze |
| **BUILD** | "build", "package", "nupkg" | Phase 0 → Build |
| **DEBUG** | "debug", "run", "test", "execute" | Phase 0 → Debug |

If unclear which file to edit, **ask the user** rather than guessing.

---

## Phase 0: Environment Readiness

Establish the project root and verify the project is legacy. See **[references/environment-setup.md](./references/environment-setup.md)** for the full procedure.

**Quick check:**
1. Find `project.json` to establish `{projectRoot}`
2. Read `project.json` and verify `targetFramework` is `"Legacy"` (or absent, implying Legacy)
3. Note `expressionLanguage` (VB.NET or C#)

**No Studio Desktop required** — `uip rpa-legacy` is a standalone CLI tool.

---

## Phase 1: Discovery

**Goal:** Understand project context, consult activity reference docs, study existing patterns, and discover activities before writing any XAML.

### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze:
- Where should new workflows be placed? (folder conventions)
- What naming pattern is used?
- What similar workflows already exist?
- Should I use VB or C# syntax? (check `expressionLanguage` in `project.json`)
- What packages are already installed? (check `dependencies` in `project.json`)

### Step 1.2: Consult Activity Reference Docs (Behavioral Context)

Read the bundled reference docs at `references/activity-docs/` to understand what activities do, their gotchas, and usage patterns. This gives you the behavioral context you need before writing XAML.

**Workflow:**
1. If you know which package you need, read its doc directly: `references/activity-docs/{PackageName}.md`
2. If you don't know the package, read the index: `references/activity-docs/_INDEX.md`
3. Before writing VB.NET expressions, consult: `references/activity-docs/_PATTERNS.md`
4. Before generating XAML structure, read: [references/xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md)
5. Check for known gotchas: `references/activity-docs/_COMMON-PITFALLS.md`
6. For InvokeCode activities, read: `references/activity-docs/_INVOKE-CODE.md`

**Remember:** These docs tell you *what* activities do and *how* to use them — but NOT the exact CLR property names and enum values for XAML. Steps 1.4 and 1.5 are mandatory for that.

### Step 1.3: Search Current Project

Search existing workflows for reusable patterns and conventions:

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"     → find files matching a pattern
Grep: pattern="ActivityName|pattern" path="{projectRoot}"  → search XAML content for activities
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"      → read a relevant existing workflow
```

**Mature project** (has existing workflows): Prioritize local patterns — they reflect the project's conventions.
**Greenfield project** (empty or near-empty): Skip this step.

### Step 1.4: Discover Activities (MANDATORY Before Writing XAML)

**Run this for every activity you plan to use.** Use `uip rpa-legacy find-activities` to get the exact fully qualified class name, argument signatures, and types:

```bash
# Find activities by capability
uip rpa-legacy find-activities "{projectRoot}" --query "send mail" --format json

# Include full type definitions for argument types
uip rpa-legacy find-activities "{projectRoot}" --query "invoke code" --include-type-definitions --format json
```

**Why this is mandatory:** The activity reference docs describe behavior and gotchas, but they do NOT contain the exact CLR class names, property names, or argument types needed for valid XAML. Skipping this step leads to guessing property names and wasting validation cycles.

**What you get:** Exact fully qualified class name, all argument names with directions (In/Out/InOut) and types, package information. With `--include-type-definitions`, you also get enum values, class properties, and methods.

### Step 1.5: Inspect Types (MANDATORY For Enums and Complex Types)

**Run this for every enum or complex type you encounter.** Use `uip rpa-legacy type-definition` to get exact enum values and type members:

```bash
# Discover enum values (e.g., InvokeCode Language property)
uip rpa-legacy type-definition "{projectRoot}" --type "NetLanguage" --format json
# Returns: VBNet, CSharp (NOT "VisualBasic" or "VB" — those are wrong!)

# Inspect a complex type's properties
uip rpa-legacy type-definition "{projectRoot}" --type "System.Net.Mail.MailMessage" --format json
```

**Why this is mandatory:** Enum values and type members cannot be reliably guessed. For example, the InvokeCode `Language` property accepts `VBNet` (not `VisualBasic`, not `VB`). Each incorrect guess costs a validation-fix cycle. Always use `type-definition` to discover the exact values.

**When to run:**
- Any property that takes an enum value
- Any activity argument with a complex type (not String/Int32/Boolean)
- Any time the activity reference docs mention a type without listing its valid values

---

## Phase 2: Generate or Edit

### Prerequisites — Complete Before Writing ANY XAML

Before writing or editing any activity XAML, confirm you have completed:
1. **Step 1.2** — Read the relevant activity reference doc (behavioral context)
2. **Step 1.4** — Run `find-activities` for every activity you plan to use (exact class names, arguments)
3. **Step 1.5** — Run `type-definition` for every enum and complex type (exact valid values)
4. Read [references/xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for XAML structure
5. Read [references/common-pitfalls.md](./references/common-pitfalls.md) for gotchas

**Do not skip steps 1.4 and 1.5.** Activity reference docs alone are insufficient for generating valid XAML — they cover behavior, not exact CLR property names and enum values.

### For CREATE Requests

**Strategy:** Generate minimal working version, iterate. Build one activity at a time.

Use the `Write` tool to create a new `.xaml` file with proper legacy XAML boilerplate. Refer to [references/xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for the complete XAML file anatomy template.

```
Write: file_path="{projectRoot}/Workflows/DescriptiveName.xaml"
       content=<valid XAML content with proper headers, namespaces, and body>
```

**File path inference:**
- Use folder conventions from project structure exploration
- Create descriptive filename: follow existing project patterns
- Ensure filename ends with `.xaml`

**Legacy XAML checklist:**
- Root `<Activity>` has `mva:VisualBasic.Settings="{x:Null}"` (for VB projects)
- Assembly xmlns uses `assembly=mscorlib` (not `System.Private.CoreLib`)
- VB.NET expressions use `[bracket]` notation
- Classic activity names (no "X" suffix)
- Include standard VB.NET namespace imports and assembly references

### For EDIT Requests

**Strategy:** Always read current content before editing.

```
Read: file_path="{projectRoot}/WorkflowToEdit.xaml"              → understand current structure
Grep: pattern="section to modify" path="{projectRoot}/..."       → OR search for specific sections
```

Then use the `Edit` tool for targeted string replacement:

```
Edit: file_path="{projectRoot}/WorkflowToEdit.xaml"
      old_string=<exact text from file>
      new_string=<modified text>
```

**Critical:** `old_string` must match exactly what's in the file and be unique. Include surrounding context if needed to ensure uniqueness.

---

## Phase 3: Validate, Analyze & Fix Loop

This phase repeats until 0 errors or remaining errors cannot be auto-resolved.

### Step 3.1: Validate

```bash
# Validate a specific workflow (use full path)
uip rpa-legacy validate "{projectRoot}/Main.xaml" --format json
```

**Notes:** Takes a **full path** to the XAML file (not relative). Run after every XAML edit.

### Step 3.2: Analyze (Optional, Project-Wide)

```bash
# Run workflow analyzer rules on the entire project
uip rpa-legacy analyze "{projectRoot}" --format json
```

Use `--stop-on-rule-violation` for strict enforcement. Use `--ignored-rules` to skip specific rules.

### Step 3.3: Categorize and Fix

**Fix order:** Package → Structure → Type → Activity Properties → Logic.

**1. Package Errors** — Missing namespace, unknown activity type
- The legacy CLI **does not have `install-or-update-packages`**
- Identify the missing package from the error message
- Check `references/activity-docs/_INDEX.md` for the correct package name
- **Ask the user** to install the package in Studio manually
- Re-validate after installation

**2. Structural Errors** — Invalid XML, malformed elements
- `Read` the XAML around the error → `Edit` to fix
- Cross-check against [references/xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md)

**3. Type Errors** — Wrong property type, invalid cast
- Consult activity reference docs for correct types
- Use `uip rpa-legacy type-definition` to inspect expected types
- Common: wrong `x:TypeArguments`, missing namespace prefix, VB/C# mismatch

**4. Activity Properties Errors** — Unknown properties, wrong values
- Consult activity reference docs for property names and valid values
- Use `uip rpa-legacy find-activities` to discover correct class names

**5. Logic Errors** — Wrong behavior, incorrect expressions
- Verify expression syntax matches project language
- Consult `references/activity-docs/_PATTERNS.md` for VB.NET patterns
- Use `uip rpa-legacy debug` for runtime validation

**When stuck:** Defer to the user for configuration details (missing package, connection setup). Document what needs manual action.

For detailed procedures, see **[references/validation-and-fixing.md](./references/validation-and-fixing.md)**.

---

## Phase 4: Build (Optional)

Package the project into a deployable `.nupkg` file:

```bash
uip rpa-legacy build "{projectRoot}" -o "{outputDir}" --format json
```

Options:
- `--version "1.2.0"` — set package version
- `--auto-version` — auto-generate version
- `--release-notes "..."` — add release notes
- `--output-type Process|Library|Tests|Objects` — force output type

A successful build confirms all dependencies resolve and all XAML files compile.

---

## Phase 5: Debug (Optional)

Execute a workflow locally via UiRobot:

```bash
# Run a workflow
uip rpa-legacy debug "{projectRoot}/Main.xaml"

# Run with input arguments
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_Name": "John", "in_Count": 5}'

# Run with timeout
uip rpa-legacy debug "{projectRoot}/Main.xaml" --timeout 120
```

**Caution:** `debug` executes the workflow — it performs real actions. Only use when safe to run.

---

## Phase 6: Response

**Provide comprehensive summary:**

1. **File path** of created/edited workflow
2. **Brief description** of what the workflow does
3. **Key activities** and logic implemented
4. **Packages required** (note any that need manual installation)
5. **Validation result** (0 errors, or remaining errors documented)
6. **Analyzer results** (if run)
7. **Limitations** or notes
8. **Suggested next steps** (testing, parameterization, manual configuration)

**Do NOT just say "workflow created"** — give user confidence the request was fully fulfilled.

---

## CLI Error Recovery

For CLI error diagnosis and recovery patterns, see the **CLI Error Recovery** section in **[references/cli-reference.md](./references/cli-reference.md#cli-error-recovery)**.

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

---

## Anti-Patterns

**Never:**
- **Batch-write multiple activities before validating** — write ONE activity, validate, fix, then next. This is the single most important rule. Batching writes compounds errors and makes debugging much harder.
- **Guess enum values or property names from activity docs alone** — always use `find-activities` and `type-definition` to get exact values. Example: InvokeCode Language is `VBNet`, not `VisualBasic` or `VB`. Each wrong guess costs a full validation-fix cycle.
- **Skip discovery steps 1.4 and 1.5** — activity reference docs cover behavior and gotchas, not exact CLR namespaces, property names, or enum values. `find-activities` and `type-definition` are mandatory for valid XAML.
- **Rely solely on activity reference docs for XAML generation** — they are essential for understanding what activities do, but insufficient for writing correct XAML. Combine them with CLI discovery tools.
- Generate large, complex workflows in one go — build incrementally, one activity at a time
- Assume a create/edit succeeded without validating with `uip rpa-legacy validate`
- Guess VB.NET syntax — consult `references/activity-docs/_PATTERNS.md`
- Use modern "X" suffix activities in legacy projects (e.g., `ReadRangeX` instead of `ExcelReadRange`)
- Assume `.local/docs/packages/` exists — legacy projects don't have auto-generated activity docs
- Use `assembly=System.Private.CoreLib` in xmlns — legacy uses `assembly=mscorlib`
- Use `[bracket]` expression notation in C# legacy projects — use `<mca:CSharpValue>` instead
- Retry failing CLI commands in a loop without diagnosing the root cause
- Manually edit `project.json` dependencies without understanding NuGet version constraints

---

## Troubleshooting

### Wrong enum value causes validation error
**Symptom:** `validate` reports "Cannot create unknown type" or "is not a member of" for an enum property.
**Cause:** Guessed enum value instead of discovering it.
**Fix:** Run `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --format json` to get exact valid values. Example: InvokeCode `Language` accepts `VBNet` and `CSharp` — not `VisualBasic`, `VB`, or `Visual Basic`.

### Activity class name not found
**Symptom:** `validate` reports unknown activity type or missing namespace.
**Cause:** Used wrong class name or missing xmlns declaration.
**Fix:** Run `uip rpa-legacy find-activities "{projectRoot}" --query "activity description" --format json` to find the exact fully qualified class name, then add the corresponding xmlns and assembly reference.

### Multiple validation errors after batch editing
**Symptom:** Many errors after writing multiple activities at once.
**Cause:** Skipped the one-activity-at-a-time workflow.
**Fix:** Revert to last known good state. Re-add activities one at a time, validating after each.

### Activity reference docs don't match XAML property names
**Symptom:** Property names from `Excel.md` or similar docs don't work in XAML.
**Cause:** Activity docs cover behavior, not exact CLR property names. XAML property names may differ.
**Fix:** Use `find-activities --include-type-definitions` to get exact property names and types from the compiled assemblies.

---

## Quality Checklist

Before handover, verify:

**Environment:**
- [ ] Project root is correctly identified
- [ ] Confirmed legacy project (`targetFramework: "Legacy"` or absent)
- [ ] Expression language noted (VB.NET or C#)

**Discovery:**
- [ ] Activity reference docs consulted for behavioral context (gotchas, patterns)
- [ ] `_PATTERNS.md` consulted for VB.NET expression patterns
- [ ] Local project explored for existing patterns and conventions
- [ ] `find-activities` run for **every** activity used (exact class names, argument signatures)
- [ ] `type-definition` run for **every** enum and complex type (exact valid values)
- [ ] No property names, enum values, or CLR types were guessed — all verified via CLI tools

**XAML Content Quality:**
- [ ] VB.NET or C# syntax matches project language
- [ ] All namespace declarations present for activities used
- [ ] Variables and arguments properly scoped and named
- [ ] Classic activity names used (no "X" suffix)
- [ ] Legacy xmlns patterns used (`assembly=mscorlib`)
- [ ] Required parent scopes present (Excel Application Scope, etc.)

**Validation & Testing:**
- [ ] Workflow file path is valid and follows project conventions
- [ ] All required activities are present
- [ ] Error handling (Try-Catch) included where appropriate
- [ ] `validate` returns 0 errors (or remaining errors documented for user)
- [ ] `analyze` passed (if run)
- [ ] `debug` smoke test considered (if workflow is safe to run)

**User Communication:**
- [ ] User informed of any limitations
- [ ] Next steps suggested (testing, customization)
- [ ] Manual actions needed documented (package installation, connection setup)
