# Validation & Fixing (Phase 3 Details)

Detailed procedures for package resolution, dynamic types, debugging, iteration, and smoke testing.

## Package Error Resolution

```
Read: file_path="{projectRoot}/project.json"     -> check current dependencies

Bash: uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]'
```

Omit `version` to automatically resolve the latest compatible version (preferred — gets newest docs and features). Only pin a specific version when you have a reason to (e.g., known compatibility constraint).

**If `install-or-update-packages` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uip rpa find-activities` to discover the correct package name from an activity's assembly
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

## Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa get-default-activity-xaml` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

## Focus Activity for Debugging

When `get-errors` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio designer. This helps the user see the problematic activity in context and verify fixes visually:

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"

# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity
```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected

## Iteration Loop

```
REPEAT:
  1. uip rpa get-errors --file-path "path/to/workflow.xaml" --format json
  2. IF 0 errors (or errors cannot be resolved automatically) -> EXIT to Phase 4
  3. Identify highest-priority error category
  4. Apply appropriate fix
  5. (Optional) Focus the fixed activity: uip rpa focus-activity --activity-id "..."
  6. GOTO 1

DO NOT stop until all activities are resolved (recognized).
DO NOT obsess on one error. If it can't be resolved, skip it, continue, and defer to an user action through an informative, step-by-step message at the end.
DO NOT skip validation steps.
DO NOT assume edits worked without checking.
```

Expect multiple iteration cycles for complex workflows.

## Smoke Test (Optional but Recommended)

**Important:** `get-errors` (Studio validation) and `run-file` (runtime compilation) use different validation paths. Some errors — such as invalid enum values on activity properties — pass Studio validation but fail at runtime. Always treat the smoke test as a critical validation step, not just an optional extra.

After reaching 0 errors, optionally run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect:

```bash
# Run with default arguments:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --format json

# Run with input arguments:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --input-arguments '{"recipientEmail": "test@example.com", "subject": "Test"}' --format json

# Run with verbose logging for debugging:
uip rpa run-file --file-path "Workflows/MyWorkflow.xaml" --log-level Verbose --format json
```

**When to run:**
- The workflow has no compilation errors but you want to verify runtime behavior
- The workflow involves file I/O, API calls, or data transformations that could fail at runtime
- The user specifically asks to test the workflow

**When NOT to run:**
- The workflow has side effects (sends emails, modifies databases, calls external APIs) — warn the user first
- The workflow requires interactive input (UI automation, attended triggers)
- Compilation errors still exist (fix those first)

If `run-file` reveals runtime errors, analyze the output and loop back to fix them.
