# UI Automation Package Guide

Extension `UiAutomationActivities`. Applies when `project.json` lists `UiPath.UIAutomation.Activities`. Classic activities live in the `ui:` namespace (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`, shared with classic System and Excel activities); modern ones in `UiPath.UIAutomationNext.Activities` under `uix:` (`NClick`, `NTypeInto`, `NApplicationCard`, `NCheckState`). Do not pre-scan the XAML for classic activities: no grep can be exhaustive and the `ui:` prefix over-matches. The `analyze` run is the detector, it reports every classic UI activity per file with a rule ID.

The migration logic is not in the CLI. The extension loads the migration service shipped inside the **target** UIAutomation package, so what migrates and how depends on `--uia-package-version`. Newer patches migrate more.

## Hook 1 — Before analyze

### Flags

Availability and defaults come from `"<MIGRATOR_EXE>" analyze --help` on the installed build (Step 0). This table says what each flag does and when to use it. Other `--uia-*` flags may exist in a newer build; Step 0 says when an unlisted flag may be used.

| Flag | Use |
|---|---|
| `--uia-package-version=<VER>` | Pass the resolved `<UIA_VERSION>`; omit the flag when Step 2 fell back to the tool default. A value below the tool's built-in minimum is refused and the minimum used instead, reported under `UIAUTOMATION-PACKAGE-UPGRADE` at warning level as `Cannot use version … Minimum required version is … Using minimum version.`; Step 3 relays that to the user |
| `--uia-fix-selector-strategy=true` | Only on rerun, when the build fails with an ambiguous `SelectorStrategy` (`CS0104` / `BC30561`). Fully qualifies the enum in pre-existing expressions |
| `--uia-enable-partial-migration=true` | Only when the user asks and `--help` lists it. Emits the closest modern activity even when fidelity is lost; the result needs manual review. Needs a package that supports it (see version gates); older packages ignore the flag |

All three are extension options: pass them as `--name=value`. The space-separated form is accepted and silently ignored ([tool-behavior-guide.md § Option binding](../tool-behavior-guide.md#option-binding)).

### Version gates

Known thresholds at the time of writing; the tool's own minimum is the one it reports when it clamps.

| Package version | Unlocks |
|---|---|
| `25.10.21` | Minimum the tool accepted in build `25.10.0`; use as `--min` for the line resolver |
| `25.10.29` | WaitActive / WaitNotActive property migration |
| `25.10.38` | `--uia-enable-partial-migration` honored |

### Resolve the target line

Goal: the latest stable patch of the release line the client's robots run.

1. If the user named a line or version, resolve that and skip the question. A bare line ("26.10") means the highest stable patch of that line.
2. Resolve candidate lines from the official UiPath NuGet feed:

   ```bash
   node "<SKILL_DIR>/scripts/resolve-package-lines.mjs" --package UiPath.UIAutomation.Activities --min 25.10.21
   ```

   The script drops prerelease versions, groups by `major.minor`, keeps LTS lines (minor `10`), takes the highest stable patch per line, drops lines below the minimum, and returns the two most recent lines. Do not use `uip rpa packages versions` for this: it starts the headless Studio host, which refuses Legacy projects and needs a project folder. Set `UIPATH_ACTIVITY_MIGRATOR_FEED_URL` to a mirror's NuGet v3 flat-container base when the public feed is blocked.
3. The newest candidate is the recommendation. Compatibility runs one way: a package version works on Studio and robots at or above the minimum its release notes list, and an older package always works on a newer host. Do not use `studioVersion` from `project.json` as a signal; it records the Studio that last saved the Legacy project, not the one that will open the result or the robots that will run it.
4. Ask once with `AskUserQuestion`. Newest line first, labeled `(Recommended)`. Option label: `<line>.x → <resolved version>`. Option description for the newest: "Longest support ahead; requires Studio and robots at or above the minimum this package version lists in its release notes." For the older: "Safe pick when the fleet is behind that minimum."
5. Script prints `error` (feed unreachable): pass no version and let the tool pin its built-in default; do not ask. Step 3 sets `<UIA_VERSION>` from the version the tool reports, and the report line carries the suffix "(tool default, feed unreachable)".

### Stop conditions specific to this package

None before analyze. Project setting conflicts and unsupported languages surface in the analyze results (Hook 2).

## What the extension does

1. **Package bump.** Replaces the `UiPath.UIAutomation.Activities` dependency in place with `[<UIA_VERSION>]` before restore (`UIAUTOMATION-PACKAGE-UPGRADE`, note). Adds and removes nothing else. The package still ships the classic activities, so anything left unmigrated keeps compiling.
2. **Activity migration**, per workflow, depth-first. Which classic type becomes which modern type is decided by the migration service inside the pinned package, so it varies with `<UIA_VERSION>`. Do not describe the mapping from memory. The SARIF names each affected activity by display name and classic type (`sourceActivity`, `activityType`); its `destinationActivity` is only the display name again, which the migrator keeps unchanged. The modern type is visible in the output XAML: find the activity by display name and read the element tag (Hook 3).
3. **Selectors.** Each classic selector is split into a window part (the target's scope selector) and an element part (its full selector). When the window differs from the enclosing scope, the migrator wraps the activity in a generated Use Application/Browser card (open and close mode Never, attach mode single window) or a loose element scope, then merges adjacent generated cards inside a sequence.
4. **Selectors held in variables** cannot be split statically. They are wrapped in a marker expression (`.ToStringWithDelimiter()`) that the runtime splits. Some resulting shapes fail at runtime; Hook 3 delegates their repair.
5. **Object Repository** descriptors are carried over by content hash and reference. No repository files are authored.
6. **Properties.** Timeouts and delays convert from milliseconds to seconds; click type, mouse button, key modifiers, wait-for-ready, and input mode (Send Window Messages / Simulate → interaction mode) map to the modern enums; classic project-setting defaults are written only when they differ from the modern defaults.
7. **Project settings.** The classic runtime browser setting is copied to the modern one when unset. If the modern one is already set to a different browser, the whole UIA migration is aborted for that project (`UIAUTOMATION-PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED`).
8. **Screenshots** for image targets and informative screenshots are written to `<OUTPUT_DIR>/.screenshots/*.png` after the project copy.
9. **Left classic.** Activities the pinned package cannot migrate stay in place unchanged and keep compiling, since the package still ships the classic activities. Each is reported with reason `MigrationNotImplemented`; the analyze results are the only authoritative list for a given project and package version.

## Hook 2 — Triage

Classify by rule ID, never by level: an activity left classic arrives as `UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-<Reason>` at note or warning level, so a level-only reading calls a run with unmigrated activities a success.

Rule IDs follow one grammar: `UIAUTOMATION-` + scope (`PACKAGE`, `WORKFLOW`, `ACTIVITY`, `ACTIVITY-PROPERTY`, or a project-level condition such as `INVALID-UIA-PACKAGE`, `LANGUAGE-NOT-SUPPORTED`, `PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED`) + outcome (`SUCCESS`, `WARNING`, `ERROR`, `PARTIAL`) + optional `-<Reason>`. The summarizer buckets results by these tokens; a project-level error is a blocker and stops the run. New scopes, outcomes, or reasons appear with package versions and still fit the grammar.

For the meaning of any rule or reason, use the rule's `fullDescription` in `tool.driver.rules` and the result's `message.text`, written by the migrator for that exact case. Quote the message in the report and derive the manual step from it. Do not keep lists of rule IDs or reasons in this guide.

## Hook 3 — After upgrade

Actions, in this order, once the Step 5 build passed:

1. **Annotations.** Migrated activities carry design-time annotations, one line per message: `[PostMigration Action Required]: <TYPE>: <message>`, followed by `[Existing annotation]: <user text>` when the classic activity had one. List them per file; they are the needs-attention items of the report:

   ```bash
   grep -rn "PostMigration Action Required" --include=*.xaml "<OUTPUT_DIR>"
   ```

2. **Expression-selector defects.** When the output contains `.ToStringWithDelimiter()` markers, run the full procedure in [uia-post-migration-fix-guide.md](../uia-post-migration-fix-guide.md) with `<OUTPUT_DIR>` as its `<MIGRATED_DIR>`: scan, classify each variable's value, present the findings table, confirm once, apply Fix 1 and Fix 2 with targeted edits, validate each edited file, then rebuild. Never rework or "improve" a selector that carries the marker; the defects are structural, and a selector rewrite destroys the variable binding.

Report inputs:

- **Left classic.** Activities the pinned package could not migrate compile and run as classic. They are the `<L>` count on the status line, and the summarizer's "UIA not migrated" section is their inventory (SKILL.md Step 6). Never name a modern equivalent for one: several classic activities (Wait Attribute, Anchor Base, Start Process among them) have no one-to-one counterpart. Never count `<ui:` elements as a cross-check: that prefix also covers classic System and Excel activities and property elements such as `<ui:Highlight.Target>`.
- **Runtime prerequisites.** Studio 2024.10 or later to open the project. Robots at or above the minimum `<UIA_VERSION>` requires. Only when the project automates a browser: the UiPath browser extension must be installed on the robot machines.

Not part of this hook: a build error that calls for a rerun with a flag is handled in Step 5 by [build-verification-guide.md](../build-verification-guide.md) with the flags of Hook 1, and package versions on the output are never edited (Rule 7).

On request only, never in the report. When the user asks what a specific activity became, find it by the display name the SARIF reported; the nearest opening tag above it is its modern type. The second command counts the modern activity elements the run produced (opening tags only, property elements such as `<uix:NClick.Target>` excluded); generated Use Application/Browser cards appear in it too, so it can exceed the number of migrated activities:

```bash
grep -rn -B6 "DisplayName=\"<SOURCE_ACTIVITY_DISPLAY_NAME>\"" --include=*.xaml "<OUTPUT_DIR>" | grep -oE "<[a-z]+:[A-Za-z]+" | tail -1
grep -rhoE "<uix:N[A-Za-z]+([[:space:]]|/?>)" --include=*.xaml "<OUTPUT_DIR>" | sed -E 's/[[:space:]\/>]+$//' | sort | uniq -c | sort -rn
```
