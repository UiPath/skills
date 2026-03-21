# Phase 3: Validate, Analyze & Fix Loop

Detailed procedures for validating legacy workflows, analyzing project quality, and fixing errors iteratively.

---

## Step 3.1: Validate

Use `uip rpa-legacy validate` to check a single XAML file for compilation errors.

```bash
# Validate a specific workflow (always use full path)
uip rpa-legacy validate "{projectRoot}/Main.xaml" --format json

# Strict mode
uip rpa-legacy validate "{projectRoot}/Workflows/Process.xaml" --treat-warnings-as-errors --format json
```

**Notes:**
- Takes a **full path** to the XAML file (not relative)
- Checks: missing arguments, broken references, type mismatches, unknown activities, invalid XML
- Run after **every** XAML edit — do not batch multiple edits without validation

---

## Step 3.2: Analyze (Optional, Project-Wide)

Use `uip rpa-legacy analyze` to run workflow analyzer rules on the entire project.

```bash
# Analyze entire project
uip rpa-legacy analyze "{projectRoot}" --format json

# Skip naming rules
uip rpa-legacy analyze "{projectRoot}" --ignored-rules "ST-NMG-001,ST-NMG-002" --format json
```

**Common analyzer rule categories:**
- **ST-NMG-***: Naming conventions (variable naming, argument naming)
- **ST-USG-***: Usage rules (unused variables, unused dependencies)
- **ST-DBP-***: Design best practices (empty catch, hardcoded delays)
- **ST-SEC-***: Security rules (credential handling)

Use `--stop-on-rule-violation` for strict enforcement. Use `--ignored-rules` to skip rules that don't apply to the project's conventions.

---

## Step 3.3: Categorize and Fix Errors

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
  uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --format json
  ```
- Example: InvokeCode `Language` property accepts `VBNet` (not `VisualBasic`, not `VB`)
- Common fixes: wrong `x:TypeArguments`, missing namespace prefix (`sd:DataTable` vs `x:String`), VB vs C# expression syntax mismatch
- Consult activity reference docs for behavioral context, but rely on `type-definition` for exact values

### 4. Activity Properties Errors — Unknown properties, misconfigured settings

- **Always use `find-activities --include-type-definitions`** to discover exact property names
  ```bash
  uip rpa-legacy find-activities "{projectRoot}" --query "activity name" --include-type-definitions --format json
  ```
- Activity reference docs describe behavior but may not list exact CLR property names — the CLI output is authoritative
- Common issues: properties that exist in modern but not legacy versions, misspelled property names, wrong enum values

### 5. Logic Errors — Wrong behavior, incorrect expressions, business logic issues

- `Read` the XAML to understand current flow → `Edit` to correct
- Verify expression syntax matches project language (VB.NET vs C#)
- Consult [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md) for VB.NET expression patterns
- Use `uip rpa-legacy debug` for runtime validation if static checks pass

---

## Step 3.4: Iteration Loop

```
REPEAT:
  1. Run: uip rpa-legacy validate "{projectRoot}/{file}.xaml" --format json
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

## Step 3.5: Build Verification (Optional)

After validation passes, optionally build to verify the project compiles and packages correctly:

```bash
uip rpa-legacy build "{projectRoot}" -o "{outputDir}" --format json
```

A successful build confirms:
- All dependencies resolve correctly
- All XAML files compile without errors
- The project produces a valid `.nupkg` package

---

## Step 3.6: Smoke Test with Debug (Optional)

For workflows that are safe to run locally, use `debug` as a smoke test:

```bash
# Run with test input
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}'

# Run with timeout to prevent hanging
uip rpa-legacy debug "{projectRoot}/Main.xaml" --timeout 60
```

**Caution:** `debug` executes the workflow via UiRobot — it will perform real actions. Only use when safe, with appropriate test inputs.

For test data creation (Excel files, CSV, JSON, common UiPath types), see **[test-data-guide.md](./test-data-guide.md)**.

---

## Common Error Scenarios

### Wrong enum value
**Symptom:** "Cannot create unknown type" or "is not a member of" for an enum property.
**Fix:** `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --format json`. Example: InvokeCode `Language` accepts `VBNet` and `CSharp` — not `VisualBasic` or `VB`.

### Activity class name not found
**Symptom:** Unknown activity type or missing namespace.
**Fix:** `uip rpa-legacy find-activities "{projectRoot}" --query "..." --format json`, add xmlns + assembly ref.

### Multiple errors after batch editing
**Symptom:** Many errors after writing multiple activities at once.
**Fix:** Revert to last good state. Re-add one activity at a time, validating after each.

### Activity docs don't match XAML property names
**Symptom:** Properties from reference docs don't work in XAML.
**Fix:** `find-activities --include-type-definitions` for exact CLR property names from compiled assemblies.

### Stuck on unfamiliar problem
**Escalation:** `uip docsai ask "..."` → `WebSearch` (UiPath Forum, Stack Overflow, GitHub) → ask user.
