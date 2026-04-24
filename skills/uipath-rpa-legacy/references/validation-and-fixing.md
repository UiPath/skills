# Phase 3: Validate & Fix Loop

Detailed procedures for validating legacy workflows, analyzing project quality, and fixing errors iteratively.

---

## Step 3.1: Validate

Use `uip rpa-legacy validate` to check a XAML file or entire project for compilation errors. Accepts XAML file path, project.json path, or project folder.

```bash
# Validate a specific file (use during iteration — per activity)
uip rpa-legacy validate "{projectRoot}/Main.xaml" --output json

# Validate entire project (use as FINAL step before completing)
uip rpa-legacy validate "{projectRoot}" --output json
```

**Workflow:**
- **During iteration:** validate per-file after each activity edit (faster, focused feedback)
- **Before completing:** validate the entire project to catch cross-file issues
- Run after **every** XAML edit — do not batch multiple edits without validation

---

## Step 3.2: Categorize and Fix Errors

**Fix order:** Package → Structure → Type → Activity Properties → Logic. Always fix in this order — higher-category fixes often resolve lower-category errors automatically.

### 1. Package Errors — Missing namespace, unknown activity type, unresolved assembly

**The legacy CLI does not have `install-or-update-packages`.** When a missing package is detected:
1. Identify the missing package from the error message
2. Check the [activity reference docs](./activity-docs/_INDEX.md) to confirm the correct package name
3. **Ask the user** to install the package manually in Studio:
   - Studio → Manage Packages → search for the package → Install
   - Or edit `project.json` dependencies directly (advanced — must match NuGet version constraints)
4. Re-validate after the package is installed

### 2. Structural Errors — Invalid XML, malformed elements, missing closing tags

- `Read` the XAML around the error location → `Edit` to fix XML structure
- Cross-check against [xaml-basics-and-rules.md](./xaml-basics-and-rules.md) for correct element nesting and namespace declarations
- Common issues: unclosed elements, mismatched namespace prefixes, duplicate `x:Name` attributes

### 3. Type Errors — Wrong property type, invalid cast, type mismatch

- **Always use `type-definition`** to discover exact enum values and type members — do not guess
  ```bash
  uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json
  ```
- Example: InvokeCode `Language` property accepts `VBNet` (not `VisualBasic`, not `VB`)
- Common fixes: wrong `x:TypeArguments`, missing namespace prefix (`sd:DataTable` vs `x:String`), VB vs C# expression syntax mismatch
- Consult activity reference docs for behavioral context, but rely on `type-definition` for exact values

### 4. Activity Properties Errors — Unknown properties, misconfigured settings

- **Always use `find-activities --include-type-definitions`** to discover exact property names
  ```bash
  uip rpa-legacy find-activities "{projectRoot}" --query "activity name" --include-type-definitions --output json
  ```
- Activity reference docs describe behavior but may not list exact CLR property names — the CLI output is authoritative
- Common issues: properties that exist in modern but not legacy versions, misspelled property names, wrong enum values

### 5. Logic Errors — Wrong behavior, incorrect expressions, business logic issues

- `Read` the XAML to understand current flow → `Edit` to correct
- Verify expression syntax matches project language (VB.NET vs C#)
- Consult [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md) for VB.NET expression patterns
- Use `uip rpa-legacy debug` for runtime validation if static checks pass

---

## Step 3.3: Iteration Loop

```
REPEAT:
  1. Run: uip rpa-legacy validate "{projectRoot}/{file}.xaml" --output json
  2. IF 0 errors → EXIT loop (success)
  3. IF errors exist:
     a. Categorize by type (Package/Structure/Type/Properties/Logic)
     b. Fix highest-category errors first
     c. Apply fix using Read + Edit tools
  4. IF error cannot be auto-resolved:
     a. Document the error for the user
     b. Suggest manual fix steps
     c. Continue fixing other errors
UNTIL: 0 errors OR all remaining errors require user action
```

**When stuck on one error:** Consider deferring to the user if it's a configuration detail (missing package, credential setup, connection string). Inform the user clearly about what needs to be done.

---

## Step 3.4: Package (Optional)

If a deployable `.nupkg` artifact is needed, package the project after validation passes:

```bash
uip rpa-legacy package "{projectRoot}" -o "{outputDir}" --output json
```

Not required for debugging — legacy RPA can be debugged directly without packaging.

---

## Step 3.5: Smoke Test with Debug (Optional)

**Always validate before debugging** — don't debug a file with compilation errors.

```bash
# Basic smoke test
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --timeout 60

# Programmatic: capture result to file, suppress streaming logs
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --result-path /tmp/result.json --log-level error
```

**Reading results:**
- Exit code 0 → success: check `Data.Output` for out-argument values
- Exit code 1 → failure: check `Data.Error` for diagnostics:
  - `Error.ActivityDisplayName` + `Error.XamlFile` → locate the problem
  - `Error.ExceptionType` + `Error.Message` → understand it
  - `Error.StackTrace` → full call chain
  - `Data.ErrorLog` → all error-level log entries for context

**Fix-and-retry:** edit XAML → validate → debug again.

**Caution:** `debug` performs real actions (clicks, emails, file writes). Only use when safe.

For test data creation (Excel files, CSV, JSON, common UiPath types), see **[test-data-guide.md](./test-data-guide.md)**.

---

## Common Error Scenarios

### Wrong enum value
**Symptom:** "Cannot create unknown type" or "is not a member of" for an enum property.
**Fix:** `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`. Example: InvokeCode `Language` accepts `VBNet` and `CSharp` — not `VisualBasic` or `VB`.

### Activity class name not found
**Symptom:** Unknown activity type or missing namespace.
**Fix:** `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, add xmlns + assembly ref.

### Multiple errors after batch editing
**Symptom:** Many errors after writing multiple activities at once.
**Fix:** Revert to last good state. Re-add one activity at a time, validating after each.

### Activity docs don't match XAML property names
**Symptom:** Properties from reference docs don't work in XAML.
**Fix:** `find-activities --include-type-definitions` for exact CLR property names from compiled assemblies.

### Stuck on unfamiliar problem
**Escalation:** `uip docsai ask "..."` → `WebSearch` (UiPath Forum, Stack Overflow, GitHub) → ask user.
