# Validation & Fixing Guide

Fix-one-thing discipline, the validation iteration loop, smoke test procedure, and RPA-specific fix procedures.

## Fix One Thing at a Time

When an error occurs, identify the root cause, fix **only** that one thing, and re-run.

- Never bundle a speculative improvement with the actual fix.
- Changing two things at once makes it impossible to verify which change resolved the issue or whether the extra change introduced a new one.
- One fix per iteration, re-run, verify.

## Validation Iteration Loop

After every file create or edit, validate the specific file until clean.

```
REPEAT:
  1. uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json  2. IF 0 errors -> EXIT to Smoke Test
  3. Identify the highest-priority error
  4. Fix one thing (see rule above)
  5. GOTO 1
```

**Target the specific file:** Use `--file-path` to validate only the file you changed -- faster than validating the whole project.

**Cap at 5 fix attempts.** After 5 failed validation fix attempts, present the remaining errors to the user. They may require domain knowledge or environment-specific fixes.

### Rules

1. DO NOT stop until all errors are resolved (or cannot be resolved automatically).
2. DO NOT obsess on one error -- if it cannot be resolved, skip it, continue, and defer to the user through an informative, step-by-step message at the end.
3. DO NOT skip validation steps.
4. DO NOT assume edits worked without checking.
5. DO NOT bundle multiple fixes in one iteration. Fix the root cause, re-run, verify. Never add a speculative change alongside the actual fix -- changing two things at once makes it impossible to tell which one resolved the issue or whether the extra change introduced a new problem.

See [cli-reference.md](cli-reference.md) for full `get-errors` and `run-file` command documentation.

## Standalone Compile Verification (Optional)

Between `get-errors` and `run-file`, `uip rpa build` offers a middle checkpoint: it compiles the whole project (XAML expression evaluation included) without actually running any workflow. Useful when `run-file` would have side effects you want to avoid, or when you want to catch expression-compilation failures earlier than runtime.

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --format json
```

This catches errors like `JIT compilation is disabled for non-Legacy projects` (attribute-form expressions parsed as VB on C# projects) that pass static `get-errors` validation but only surface at `CacheMetadata` time. See [xaml/common-pitfalls.md § C# Attribute-Form Expressions Are Parsed as VB](xaml/common-pitfalls.md#c-attribute-form-expressions-are-parsed-as-vb--jit-failure-at-runtime).

**Not a prerequisite for `run-file`** — `run-file` performs its own compilation. Use `build` when you want compile verification without execution.

## Smoke Test

`get-errors` (static analysis) and `run-file` (runtime compilation) use different validation paths. Some errors -- such as invalid enum values on activity properties -- pass static validation but fail at runtime. Always treat the smoke test as a critical validation step, not just an optional extra.

After reaching 0 validation errors, run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect:

```bash
# Run with default arguments:
uip rpa run-file --file-path "<FILE>" --output json
# Run with input arguments:
uip rpa run-file --file-path "<FILE>" --input-arguments '{"key": "value"}' --output json
# Run with verbose logging for debugging:
uip rpa run-file --file-path "<FILE>" --log-level Verbose --output json```

**When to run:**
1. Workflow has no compilation errors but you want to verify runtime behavior
2. Workflow involves file I/O, API calls, or data transformations that could fail at runtime
3. User specifically asks to test the workflow

**When NOT to run:**
1. Workflow has side effects (sends emails, modifies databases, calls external APIs) -- warn the user first
2. Workflow requires interactive input (UI automation, attended triggers)
3. Compilation errors still exist (fix those first)

**If runtime errors occur:** Analyze the output, apply the fix-one-thing rule, and loop back to fix. Stop after 2 failed runtime retry attempts and present the user with error details, a suggested fix, and options:

```
Workflow execution failed after 2 retry attempts.

**Error Details:** <specific error message and location>
**Suggested Fix:** <analysis of what went wrong>
**Next Steps:** Would you like me to:
A) <recommended fix approach>
B) <alternative approach>
C) <user-driven approach>
```

---

## RPA-Specific Fix Procedures

### Package Error Resolution

```
Read: file_path="{projectRoot}/project.json"     -> check current dependencies

Bash: uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]'```

Omit `version` to automatically resolve the latest compatible version (preferred — gets newest docs and features). Only pin a specific version when you have a reason to (e.g., known compatibility constraint).

**If `install-or-update-packages` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uip rpa find-activities` to discover the correct package name from an activity's assembly
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

### Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa get-default-activity-xaml` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Focus Activity for Debugging

When `get-errors` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio designer. This helps the user see the problematic activity in context and verify fixes visually:

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"
# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected
