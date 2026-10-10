# Build Verification Guide

Step 5 of the workflow. The migrated project is a Windows project, so the modern RPA CLI applies. The build proves the output compiles; whether it runs is Step 6, [runtime-verification-guide.md](runtime-verification-guide.md).

## Prerequisites

- `uip` CLI installed and logged in (`uip login status --output json`). Without it, skip verification and state in the report that the output was not built.
- `<OUTPUT_DIR>` absolute. `uip rpa` fails to open a project given a relative path.
- First `uip rpa` call on a machine starts a headless Studio host and takes 30–90 s. Do not treat that as a hang.

## Build

```bash
env -u UIPATH_STUDIO_PID uip rpa build "<OUTPUT_DIR>" --output json
```

Build compiles every workflow, applies project-scope analyzer rules, and restores packages.

| Build result | Action |
|---|---|
| Success, no errors | Verified. Continue to Step 6 |
| Success with `[WARN]` lines | Verified. Apply the two rules under Build warnings below |
| Fails in `Restoring nuget packages` with `SharedAppConfiguration` and `String '<value>' was not recognized as a valid Boolean` | The CLI's headless Studio host crashes on the user's `UIPATH_TELEMETRY_DISABLED` value; the project is not at fault. Rerun this build, and every later `uip rpa` command, with `UIPATH_TELEMETRY_DISABLED=true` after Rule 8's prefix (`env -u UIPATH_STUDIO_PID UIPATH_TELEMETRY_DISABLED=true uip rpa ...`), or `=false` when the value was `0`, `no` or `off`. Never unset it. Not a fix-loop iteration |
| Errors | Enter the fix loop |

## Build warnings

Warnings are Workflow Analyzer output: an open set that depends on the Studio version, the project's analyzer configuration, and the packages' own rules. Two rules cover all of them:

1. A warning that quotes a `[PostMigration Action Required]` annotation or a "Migration not implemented" text is the migrator's own finding surfacing through the analyzer (rule `ST-AMG-001` on recent Studio versions). It is already a needs-attention item; do not report it twice.
2. Any other warning is analyzer output on the project as it was. Mention it once, do not fix it, and never let warnings gate delivery.

## Package versions are not edited here

The skill does not change any dependency version on the output during verification. The target UIAutomation version is settled in Step 2 and a mismatch is handled in Step 3, never by editing the output. What the client does with package versions after the migration is their normal maintenance; it is not a report item.

## Fix loop

At most 3 iterations. Each iteration:

1. Take the first failing file from the build output and validate it alone:

   ```bash
   env -u UIPATH_STUDIO_PID uip rpa validate --project-dir "<OUTPUT_DIR>" --file-path "<REL_XAML>" --min-severity error --output json
   ```

   `--min-severity error` matters: migrated projects routinely carry pre-existing warnings.

2. Classify the error:

   | Error pattern | Cause | Fix |
   |---|---|---|
   | `CS0104` / `BC30561` ambiguous `SelectorStrategy` | Classic and modern enums with the same name both imported | Not a hand fix. Delete `<OUTPUT_DIR>` and rerun Step 4 with `--uia-fix-selector-strategy=true` added to the same flags. The rerun reuses the Step 3 analyze (Rule 4 names it as the exception), counts as one iteration, and needs no question before the delete: the skill created that folder in this session |
   | Missing type from a package reported as `TYPE-MISSING` or `RESTORE-INCOMPATIBLE-PACKAGE` | Package has no Windows version | Needs attention. Report the activities; do not stub them |
   | Expression compile error in an unchanged expression (`BC30451`, `CS0103` on a variable) | Legacy-only API or implicit `mscorlib` type | Fix the expression with the equivalent .NET 8 API. Keep the change minimal |
   | Error inside an activity the migrator generated (Assign, Sequence, Application Card) | Migration defect | Needs attention, with the activity name; do not rewrite the generated construct blind |
   | Anything else | Unknown | Ask one yes/no question: what would change, in which file and activity, and why it should clear the error. Yes applies that one targeted fix and counts one iteration; no makes it a needs-attention item |

3. Apply the fix with targeted edits only. Never rewrite a whole XAML file, never re-serialize it with a script, never reintroduce a classic activity. Mark the edited construct as SKILL.md Rule 12 says: the `Remediated by uipath-activity-migrator on <YYYY-MM-DD>: <what changed>` line replaces the matching `[PostMigration Action Required]` line or is added as a new annotation attribute, never an XML comment.
4. Rebuild.

When the RPA authoring skill is available in this plugin, spawn a subagent that runs it on every XAML edit of this loop and returns the changed file, then continue with its result. Brief it as the Limits sub-step of [runtime-verification-guide.md § Fix and rerun loop](runtime-verification-guide.md#fix-and-rerun-loop) says: intent and constraints, never XAML mechanics; the edited file comes back. When it is unavailable, apply the minimal fix directly under the same rules.

After 3 iterations, or when a fix would change what the migrator produced beyond the failing construct, stop and list the remaining errors per file as needs-attention items. The migration then goes on to Step 6 with `build failed` on the status line: Hook 3 still runs, since its annotations and the fix guide are what the manual follow-up needs, and the runtime check is not offered.
