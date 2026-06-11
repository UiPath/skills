# Validation & Fixing Guide

Fix-one-thing discipline, the validation iteration loop, smoke test procedure, and RPA-specific fix procedures.

## Pre-generation: List Analyzer Rules

Before creating or editing any workflow file (`.cs` with `[Workflow]`/`[TestCase]`, or `.xaml`), list the enabled Workflow Analyzer rules so generated code satisfies them on the first attempt instead of round-tripping through `validate` fixes:

```bash
uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json
```

Apply every rule whose `severity` is `error` or `warning` during authoring. `info` rules are advisory.

**When to run:**
1. Once at the start of every task that will generate or edit a workflow file.
2. Re-run after adding or updating a NuGet package — package-shipped rules (`MA-*`) change with the dependency set.

**When NOT to run:**
1. Pure read-only / Q&A tasks that do not produce or modify workflow files.
2. Edits that only touch non-workflow files (`project.json`, docs, plain `.cs` source files without workflow attributes).

Rule prefixes and full schema: [cli-reference.md § analyzer-rules list](cli-reference.md).

## Fix One Thing at a Time

When an error occurs, identify the root cause, fix **only** that one thing, and re-run.

- Never bundle a speculative improvement with the actual fix.
- Changing two things at once makes it impossible to verify which change resolved the issue or whether the extra change introduced a new one.
- One fix per iteration, re-run, verify.

## Validation Iteration Loop

Phase 1 — per-file `validate` after every edit. Phase 2 — one project-level `build` per edit session.

```
PHASE 1 — validate-clean (per-file):
  FOR each file created or edited in this session:
    REPEAT:
      1. uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json
      2. IF validate has errors -> fix one root cause, GOTO 1
      3. EXIT inner loop when validate is clean

PHASE 2 — build-clean (per-project, once per edit session):
  REPEAT:
    1. uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
    2. IF build has errors -> identify offending file from build output
       a. uip rpa validate --file-path "<OFFENDER>" --project-dir "<PROJECT_DIR>" --output json   # cheap targeted re-check
       b. fix one root cause, GOTO 1
    3. EXIT to Smoke Test
```

**Why both phases.** `validate` is static analysis: catches structural XAML, missing references, analyzer rules, schema violations. `build` is the compiler: catches **unknown member names** (e.g. `NGetText.Value` when the property is `Text`), **invalid enum values** (e.g. `Operator="StartsWith"` when the enum has no such member), **member resolution / CacheMetadata failures**, and attribute-form C# expression JIT failures. `validate` returns "no diagnostics found" for these; `build` flags them at compile time. Per-file `validate` plus one end-of-session `build` covers both error classes — trusting only `validate` ships broken workflows.

**Target the specific file:** `validate --file-path` validates only the file you changed (faster than whole-project). `build` is project-scoped (no `--file-path`); when it errors, the output names the offending file — re-run `validate --file-path` on it as part of Phase 2's fix loop.

**5-attempt cap per loop** — 5 attempts for each file's Phase 1 `validate` loop; a separate 5 attempts for the Phase 2 `build` loop. After a loop exhausts its budget, present the remaining errors to the user. They may require domain knowledge or environment-specific fixes. Each loop's counter resets when you start a new loop (e.g., new file, new user prompt, or resuming after user input).

### Rules

1. DO NOT stop until all errors are resolved (or cannot be resolved automatically).
2. DO NOT obsess on one error -- if it cannot be resolved, skip it, continue, and defer to the user through an informative, step-by-step message at the end.
3. DO NOT skip validation steps.
4. DO NOT assume edits worked without checking.
5. DO NOT bundle multiple fixes in one iteration. Fix the root cause, re-run, verify. Never add a speculative change alongside the actual fix -- changing two things at once makes it impossible to tell which one resolved the issue or whether the extra change introduced a new problem.

See [cli-reference.md](cli-reference.md) for full `validate` and `run` command documentation.

## Project Build Verification (Required Before Returning a Project)

Every project returned to the user must compile. Phase 2 of the iteration loop above is this gate — when Phase 2 exits clean, the gate is satisfied. The standalone command below also satisfies it (for example, when re-verifying after a small fix outside an iteration loop):

```bash
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

`validate` is static analysis and misses compile-time failures: unknown member names, invalid enum values, member resolution / CacheMetadata failures, and JIT failures like `JIT compilation is disabled for non-Legacy projects` — see [xaml/csharp-expression-pitfalls.md](xaml/csharp-expression-pitfalls.md). If `build` fails, apply the Phase 2 fix loop (fix one root cause, re-run, cap at 5 attempts). A successful `run` smoke test substitutes for `build` — `run` compiles internally. Prefer the `run --skip-build` form when `build` has just passed (see Smoke Test below).

### Errors `build` catches that `validate` misses

| Error class | Example | Why `validate` misses it |
|-------------|---------|----------------------------|
| Unknown member name | `<uix:NGetText Value="[x]" />` (correct: `Text`) | `validate` does not resolve property names against activity assemblies |
| Invalid enum value | `Operator="StartsWith"` on `VerifyExpressionWithOperator` (enum has no such member) | Enum membership is checked at CacheMetadata / compile time, not static parse |
| CacheMetadata / member resolution | Required-extension misses, type-mismatch on `InArgument<T>` | Surfaces only when the runtime instantiates the activity |
| Attribute-form C# expressions | `Value="x + y"` in `expressionLanguage: CSharp` projects | JIT compiler needs the expression in element form — see [xaml/csharp-expression-pitfalls.md](xaml/csharp-expression-pitfalls.md) |

When you see "no diagnostics found" from `validate`, you have not validated the file. Run `build` next.

## Smoke Test

`validate` (static analysis) and `run` (runtime compilation) use different validation paths. Some errors -- such as invalid enum values on activity properties -- pass static validation but fail at runtime. Always treat the smoke test as a critical validation step, not just an optional extra.

After reaching 0 validation errors AND a clean project-level build (Phase 2), run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect. Use `--skip-build` because the project has just been built clean — default `run` re-validates and re-builds internally, repeating ~10s of compilation:

```bash
# Run with default arguments (post-build, skip the redundant rebuild):
uip rpa run --file-path "<FILE>" --skip-build --output json
# Run with input arguments (repeat --input-arguments per key; = string, := raw JSON):
uip rpa run --file-path "<FILE>" --skip-build --input-arguments key=value --output json
# Run with verbose logging for debugging:
uip rpa run --file-path "<FILE>" --skip-build --log-level Verbose --output json
```

Use bare `run` (without `--skip-build`) whenever the build artifact may be stale: **(a)** no recent project-level `build` has been performed, OR **(b)** any file has been edited between the last successful `build` and this `run`. `--skip-build` executes the existing compiled artifact, so any post-build edit is silently ignored until a fresh `build` runs.

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

Bash: uip rpa packages install --packages id=UiPath.Excel.Activities```

Omit `version` to automatically resolve the latest compatible version (preferred — gets newest docs and features). Only pin a specific version when you have a reason to (e.g., known compatibility constraint).

**If `packages install` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uip rpa activities find` to discover the correct package name from an activity's assembly
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

### Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa activities get-default-xaml` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Focus Activity for Debugging

When `validate` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio Desktop designer. This helps the user see the problematic activity in context and verify fixes visually.

> **Studio Desktop required.** `focus-activity` does not run against headless Studio — it manipulates the Studio Desktop designer UI. Before invoking it, ensure Studio Desktop is up via `uip rpa studio start --project-dir "<PROJECT_DIR>"` (see [environment-setup.md § Edge case: requiring Studio Desktop](environment-setup.md#edge-case-requiring-studio-desktop)). Skip this step entirely on headless-only setups — `validate` already includes the IdRef and file:line in its output, which is enough to locate the activity.

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1"
# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected
