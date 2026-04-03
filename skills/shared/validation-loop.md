# Validation Loop

Fix-one-thing discipline, the validation iteration loop, and the smoke test procedure.

## Fix One Thing at a Time

When an error occurs, identify the root cause, fix **only** that one thing, and re-run.

- Never bundle a speculative improvement with the actual fix.
- Changing two things at once makes it impossible to verify which change resolved the issue or whether the extra change introduced a new one.
- One fix per iteration, re-run, verify.

## Validation Iteration Loop

After every file create or edit, validate the specific file until clean.

```
REPEAT:
  1. uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio
  2. IF 0 errors -> EXIT to Smoke Test
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

## Smoke Test

`get-errors` (static analysis) and `run-file` (runtime compilation) use different validation paths. Some errors -- such as invalid enum values on activity properties -- pass static validation but fail at runtime. Always treat the smoke test as a critical validation step, not just an optional extra.

After reaching 0 validation errors, run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect:

```bash
# Run with default arguments:
uip rpa run-file --file-path "<FILE>" --output json --use-studio

# Run with input arguments:
uip rpa run-file --file-path "<FILE>" --input-arguments '{"key": "value"}' --output json --use-studio

# Run with verbose logging for debugging:
uip rpa run-file --file-path "<FILE>" --log-level Verbose --output json --use-studio
```

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
