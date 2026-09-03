# Verification Guide

Step 5 of the workflow. The migrated project is a Windows project, so the modern RPA CLI applies. Verification proves the output compiles; it does not prove runtime behavior.

## Prerequisites

- `uip` CLI installed and logged in (`uip login status --output json`). Without it, skip verification and state in the report that the output was not built.
- `<OUTPUT_DIR>` absolute. `uip rpa` fails to open a project given a relative path.
- First `uip rpa` call on a machine starts a headless Studio host and takes 30–90 s. Do not treat that as a hang.

## Build

```bash
uip rpa build "<OUTPUT_DIR>" --output json
```

Build compiles every workflow, applies project-scope analyzer rules, and restores packages. Restoring also installs package documentation under `<OUTPUT_DIR>/.local/docs/packages/<PackageId>/`, which the UIA package guide relies on in Hook 3.

| Build result | Action |
|---|---|
| Success, no errors | Verified. Continue to Step 6 |
| Success with `[WARN]` lines | Verified. Classify warnings per the table below; carry relevant ones into the report |
| Errors | Enter the fix loop |

## Expected warnings after migration

| Warning | Meaning | Report as |
|---|---|---|
| `ST-AMG-001` | Post-migration annotations present; a migrated activity still carries `[PostMigration Action Required]` | Manual work, per activity. Available from Studio 2025.10.8 LTS / 2026.0.189 STS; absent on older hosts |
| `[WARN] [Process] [<project>] <activity>: ERROR: Migration not implemented.` | An activity the migrator left classic, surfaced through its annotation | Already in the "not migrated" list; do not double-report |
| `<activity> does not have the verification feature enabled` | Modern UIA activities default to no verification | Not an issue; omit |
| Analyzer rule IDs already present before migration | Pre-existing project debt | Mention once, do not fix |

## Package versions are frozen

Do not change any dependency version on the output during verification, and never raise `UiPath.UIAutomation.Activities` to reach a requested release line. The migration logic ships inside that package, so the migrated workflows are the product of the exact version the tool pinned; a later version was never run against them. Moving to a newer line is a deliberate upgrade the user performs in Studio after the migration is accepted.

## Fix loop

At most 3 iterations. Each iteration:

1. Take the first failing file from the build output and validate it alone:

   ```bash
   uip rpa validate --project-dir "<OUTPUT_DIR>" --file-path "<REL_XAML>" --min-severity error --output json
   ```

   `--min-severity error` matters: migrated projects routinely carry pre-existing warnings.

2. Classify the error:

   | Error pattern | Cause | Fix |
   |---|---|---|
   | `CS0104` / `BC30561` ambiguous `SelectorStrategy` | Classic and modern enums with the same name both imported | Not a hand fix. Delete `<OUTPUT_DIR>`, rerun Step 4 with `--uia-fix-selector-strategy true` |
   | Missing type from a package reported as `TYPE-MISSING` or `RESTORE-INCOMPATIBLE-PACKAGE` | Package has no Windows version | Manual work. Report the activities; do not stub them |
   | Expression compile error in an unchanged expression (`BC30451`, `CS0103` on a variable) | Legacy-only API or implicit `mscorlib` type | Fix the expression with the equivalent .NET 8 API. Keep the change minimal |
   | Error inside an activity the migrator generated (Assign, Sequence, Application Card) | Migration defect | Report as manual work with the activity name; do not rewrite the generated construct blind |
   | Anything else | Unknown | One targeted fix attempt; then report |

3. Apply the fix with targeted edits only. Never rewrite a whole XAML file, never re-serialize it with a script, never reintroduce a classic activity.
4. Rebuild.

When the RPA authoring skill is available in this plugin, delegate the XAML edit of iteration 2 to it and continue with its result. When it is unavailable, apply the minimal fix directly under the same rules.

After 3 iterations, or when a fix would change what the migrator produced beyond the failing construct, stop and list the remaining errors per file as manual work.

## Runtime checks the user should run

Report these; do not run them unattended:

- Open `<OUTPUT_DIR>` in Studio 2024.10 or later and let it restore.
- Run the main workflow once in Debug against the real applications.
- For UI Automation, set the project setting "Log target & anchor search steps" to Info before the run; healthy targets log `Searching for target …` then `Target was found with the selector method`.
- Package-specific runtime prerequisites are listed in each package guide's Hook 3 (for example Integration Service connections for Mail).
