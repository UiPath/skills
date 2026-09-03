# UI Automation Package Guide

Extension `UiAutomationActivities`. Applies when `project.json` lists `UiPath.UIAutomation.Activities` and workflows use classic activities from the `ui:` namespace (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`): `<ui:Click`, `<ui:TypeInto`, `<ui:OpenBrowser`, `<ui:BrowserScope`, `<ui:WindowScope`, `<ui:UiElementExists`, `<ui:WaitUiElementAppear`, `<ui:GetValue`, `<ui:SendHotkey`, `<ui:FindChildren`, `<ui:ExtractData` and the rest of the classic set. Modern activities live in `UiPath.UIAutomationNext.Activities`: `NClick`, `NTypeInto`, `NApplicationCard`, `NCheckState`, `NGetText`.

Detect classic usage:

```bash
grep -rlE "<ui:(Click|TypeInto|TypeSecureText|OpenBrowser|OpenApplication|BrowserScope|WindowScope|UiElementExists|WaitUiElementAppear|WaitUiElementVanish|GetValue|SetValue|GetFullText|GetVisibleText|SendHotkey|FindChildren|ElementScope|ExtractData|SelectItem|Check|Hover|Highlight|TakeScreenshot)\b" --include=*.xaml "<PROJECT_DIR>"
```

The migration logic is not in the CLI. The extension loads the migration service shipped inside the **target** UIAutomation package, so what migrates and how depends on `--uia-package-version`. Newer patches migrate more.

## Hook 1 — Before analyze

### Flags

| Flag | Default | Use |
|---|---|---|
| `--uia-package-version=<VER>` | `25.10.21` (also the minimum; lower values are raised to it) | Always pass the resolved `<UIA_VERSION>`, in the `=` form. The space-separated form (`--uia-package-version 25.10.39`) parses without error and is ignored; the tool then pins the default. Confirm from the `UIAUTOMATION-PACKAGE-UPGRADE` message after analyze |
| `--uia-fix-selector-strategy=true` | `false` | Only on rerun, when the build fails with an ambiguous `SelectorStrategy` (`CS0104` / `BC30561`). Fully qualifies the enum in pre-existing expressions |
| `--uia-enable-partial-migration=true` | `false` | Only when the user asks, and only when `--help` lists it (absent in build `25.10.0`). Emits the closest modern activity even when fidelity is lost; the result needs manual review. Ignored by packages older than `25.10.38` |

All three are extension options: pass them as `--name=value`. Core options such as `--project-path` accept both forms.

### Version gates

| Package version | Unlocks |
|---|---|
| `25.10.21` | Minimum accepted by the tool |
| `25.10.29` | WaitActive / WaitNotActive property migration |
| `25.10.38` | `--uia-enable-partial-migration` honored |

### Resolve the target line

Goal: the latest stable patch of the release line the client's robots run.

1. If the user named a line or version, resolve that and skip the question. A bare line ("26.10") means the highest stable patch of that line.
2. Resolve candidate lines from the official UiPath NuGet feed:

   ```bash
   node "<SKILL_DIR>/scripts/resolve-package-lines.mjs" --package UiPath.UIAutomation.Activities --min 25.10.21 --studio-version "<STUDIO_VERSION>"
   ```

   The script drops prerelease versions, groups by `major.minor`, keeps LTS lines (minor `10`), takes the highest stable patch per line, drops lines below the minimum, and returns the two most recent lines. Do not use `uip rpa packages versions` for this: it starts the headless Studio host, which refuses Legacy projects and needs a project folder. Set `UIPATH_ACTIVITY_MIGRATOR_FEED_URL` to a mirror's NuGet v3 flat-container base when the public feed is blocked.
3. `<STUDIO_VERSION>` is `studioVersion` from `project.json` (format `major.minor.build.rev`). When a candidate line equals its `major.minor`, the script recommends that line; otherwise the newest candidate.
4. Ask once with `AskUserQuestion`. Recommended option first, labeled `(Recommended)`. Option label: `<line>.x → <resolved version>`. Option description: "Robots and Studio on the <year>.<minor> release line. <one reason>". Reasons: "matches this project's Studio version" or "newest LTS line, longest support ahead; requires robots on this line".
5. Script prints `error` (feed unreachable): use the tool default, do not ask, and record "target version: tool default (feed unreachable)" for the report.

Mixed-line caution for the report: the core restore step moves every other package to the smallest Windows-compatible line above its current version. Choosing a line far ahead of the rest of the project is legitimate but should be stated.

### Stop conditions specific to this package

None before analyze. Project setting conflicts and unsupported languages surface in the analyze results (Hook 2).

## What the extension does

1. **Package bump.** Replaces the `UiPath.UIAutomation.Activities` dependency in place with `[<UIA_VERSION>]` before restore (`UIAUTOMATION-PACKAGE-UPGRADE`, note). Adds and removes nothing else. The package still ships the classic activities, so anything left unmigrated keeps compiling.
2. **Activity migration**, per workflow, depth-first. Families:

   | Classic | Modern |
   |---|---|
   | Click, Click Image, Click Text, Click OCR Text | `NClick` |
   | Hover and its Image/Text/OCR variants | `NHover` |
   | Type Into, Type Secure Text | `NTypeInto` |
   | Send Hotkey | `NKeyboardShortcut` (or `NTypeInto` when the field is emptied first) |
   | Get Text, Get Full Text, Get Visible Text, Get OCR Text | `NGetText` |
   | Set Text | `NSetText` |
   | Check, Select Item, Set Focus, Highlight, Get Attribute, Get Position, Take Screenshot | `NCheck`, `NSelectItem`, `NSetFocus`, `NHighlight`, `NGetAttribute`, `NGetAttributeGeneric`, `NTakeScreenshot` |
   | Element Exists, Find Element, Wait Element Vanish, On Element Appear/Vanish, Image Exists and image waits, Text Exists, Find Text, OCR Text Exists, Find OCR Text | `NCheckState` with the matching target type |
   | Find Children | `NFindElements` (fuzzy selector) |
   | Element Scope | `NElementScope` |
   | Open Browser, Attach Browser, Open Application, Attach Window, Close Application | `NApplicationCard` with the matching open and close modes |
   | Navigate To, Go Back/Forward/Home, Refresh, Close Tab, Inject JS | `NGoToUrl`, `NNavigateBrowser`, `NInjectJsScript` |
   | Extract Data | `NExtractData` |
   | Window operations (Activate, Maximize, Minimize, Restore, Hide, Show, Close, Move) | `NWindowOperation` |
   | Get/Set Clipboard | `NGetClipboard`, `NSetClipboard` |
   | SAP classic set | `NSAP*` equivalents |

3. **Selectors.** Each classic selector is split into a window part (the target's scope selector) and an element part (its full selector). When the window differs from the enclosing scope, the migrator wraps the activity in a generated Use Application/Browser card (open and close mode Never, attach mode single window) or a loose element scope, then merges adjacent generated cards inside a sequence.
4. **Selectors held in variables** cannot be split statically. They are wrapped in a marker expression (`.ToStringWithDelimiter()`) that the runtime splits. Some resulting shapes fail at runtime; Hook 3 delegates their repair.
5. **Object Repository** descriptors are carried over by content hash and reference. No repository files are authored.
6. **Properties.** Timeouts and delays convert from milliseconds to seconds; click type, mouse button, key modifiers, wait-for-ready, and input mode (Send Window Messages / Simulate → interaction mode) map to the modern enums; classic project-setting defaults are written only when they differ from the modern defaults.
7. **Project settings.** The classic runtime browser setting is copied to the modern one when unset. If the modern one is already set to a different browser, the whole UIA migration is aborted for that project (`UIAUTOMATION-PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED`).
8. **Screenshots** for image targets and informative screenshots are written to `<OUTPUT_DIR>/.screenshots/*.png` after the project copy.
9. **Left classic.** Computer Vision activities, all trigger activities, Anchor Base and Context Aware Anchor, Callout, classic OCR engines, Set Web Attribute / Set Attribute / Wait Attribute, Select Multiple Items, Find Relative, Get Ancestor, Get Active Window, Get Password, Invoke ActiveX, Inject .NET Code, Start Process, Load Image, Find Image Matches, Indicate On Screen, Set Clipping Region, Use Foreground, Block User Input, Monitor Events, Export UI Tree. Each is reported with reason `MigrationNotImplemented` and stays in place as a working classic activity. The analyze results are the authoritative per-project list; this enumeration is for explaining them.

## Hook 2 — Triage

Classify by rule ID, never by level: an activity left classic arrives as `UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-<Reason>` at **note** or warning level, so a level-only reading calls a run with unmigrated activities a success.

| Rule ID | Meaning | Report as |
|---|---|---|
| `UIAUTOMATION-PACKAGE-UPGRADE` | Dependency bumped to `<UIA_VERSION>` | Package versions row |
| `UIAUTOMATION-INVALID-UIA-PACKAGE` | The restored UIA package exposes no migration service (version too old or package broken) | **Stop.** Re-resolve `<UIA_VERSION>`; if the resolved version is at or above `25.10.21`, the feed served a broken package: show the message |
| `UIAUTOMATION-LANGUAGE-NOT-SUPPORTED` | Project expression language not supported by the migrator | **Stop.** Report; no workaround |
| `UIAUTOMATION-PROJECT-SETTINGS-CONFIGURATION-NOT-SUPPORTED` | Modern runtime browser setting conflicts with the classic one | **Stop.** Tell the user which setting to align in Project Settings, then rerun |
| `UIAUTOMATION-WORKFLOW-INFO[-<Reason>]` | Workflow-level information | Omit unless the reason is `UpdatedModernRuntimeBrowser` (report once) |
| `UIAUTOMATION-WORKFLOW-WARNING[-<Reason>]` / `UIAUTOMATION-WORKFLOW-ERROR[-<Reason>]` | Workflow-level issue | Per file, with reason |
| `UIAUTOMATION-ACTIVITY-<Type>-MIGRATION-SUCCESS` | Activity migrated cleanly | Count into "migrated" |
| `UIAUTOMATION-ACTIVITY-MIGRATION-WARNING[-<Reason>]` | Migrated with a caveat | Count into "migrated"; list the reason under manual work when it is one of the reasons marked ✔ below |
| `UIAUTOMATION-ACTIVITY-MIGRATION-PARTIAL` | Migrated with dropped values (partial migration enabled) | Manual work, per activity |
| `UIAUTOMATION-ACTIVITY-MIGRATION-ERROR[-<Reason>]` | Activity left classic | "Not migrated", per activity, with reason |
| `UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-WARNING[-<Reason>]` / `-ERROR[-<Reason>]` | One property could not be carried over | Manual work, per activity and property |

Reason suffixes and what to tell the user:

| Reason | Meaning | Manual work ✔ |
|---|---|---|
| `MigrationNotImplemented` | No modern equivalent in this package version | ✔ Rebuild with modern activities by hand, or keep classic |
| `RequiredTarget` / `ActivityNotConfigured` | Classic activity has no target configured | ✔ Configure before or after migration |
| `AnchorProvider` / `AnchorAction` | Activity is, or is inside, an Anchor Base | ✔ Replace with a modern target anchor |
| `ElementScope` / `ElementScopeNotSupported` / `ElementScopeInsideElementScope` | Element Scope shape not supported | ✔ Restructure the scope |
| `VariableSelector` / `AttachBrowserSelectorWithVar` | Selector held in a variable; runtime split applies | ✔ Hook 3 delegation |
| `UnsupportedOCREngine` / `StandaloneOCREngineNotSupported` / `OCRNotFound` / `OCRWithOutput` | OCR engine or OCR output shape unsupported | ✔ Switch engine or redesign |
| `ClassicExceptionsInTryCatch` | Try Catch catches a classic UIA exception type | ✔ Update catch types |
| `AutomaticallyDownloadWebDriver` | Classic Open Browser option with no modern equivalent | ✔ Configure the driver in project settings |
| `UnsupportedPropertyType` / `PropertyMigrationNotImplemented` / `PropertyWithExpressionNotImplemented` / `ObsoleteProperty` / `PropertyNotFound` | A property was dropped | ✔ Re-set on the modern activity |
| `BrowserNativeScraping` / `StandaloneNotSupported` | Scraping mode or standalone shape unsupported | ✔ Review the migrated activity |
| `UpdatedModernRuntimeBrowser` | Modern runtime browser setting was written from the classic one | Report once; no action |
| `UnexpectedException` / `UnexpectedPropertyException` / `CreateDestination` | Migrator crashed on this activity | ✔ Report the activity; file feedback via the feedback skill if the user agrees |

## Hook 3 — After upgrade

1. **Ambiguous `SelectorStrategy` build errors** (`CS0104`, `BC30561`): delete `<OUTPUT_DIR>`, rerun Step 4 with `--uia-fix-selector-strategy=true`, then rebuild. Do not hand-edit the expressions.
1. **Package version stays as pinned.** Never raise `UiPath.UIAutomation.Activities` on the output to reach `<UIA_VERSION>` when the tool pinned something else. The migration service that produced the workflows lives inside the pinned package; a newer version was never run against them. Report the effective version and leave the upgrade to the user in Studio.
2. **Annotations.** Migrated activities carry design-time annotations, one line per message: `[PostMigration Action Required]: <TYPE>: <message>`, followed by `[Existing annotation]: <user text>` when the classic activity had one. List them per file for the report:

   ```bash
   grep -rn "PostMigration Action Required" --include=*.xaml "<OUTPUT_DIR>"
   ```

3. **Variable-selector defects.** Recent UIAutomation packages ship a fix skill that lands in the project at `<OUTPUT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-post-migration-fix/SKILL.md` once the package docs are installed. Locate it with a direct `Read` after the build; a failed `Read` is the existence check. Do not probe with `Glob` or a directory-wide `Grep`, both skip `.local/`. `uip rpa build` and `validate` against a `25.10.21` package did not create that folder in testing, so expect the fallback below to be the common path.
   - Present: follow that skill with `--project-dir "<OUTPUT_DIR>" --report-only`, fold its findings table into the report, and offer to run it without `--report-only`. It asks for confirmation before editing.
   - Absent: list the affected activities yourself and mark them for manual review:

     ```bash
     grep -rn "ToStringWithDelimiter" --include=*.xaml "<OUTPUT_DIR>"
     ```

     Known failing shapes: a generated Use Application/Browser card whose selector is the marker expression and whose variable holds an element-only selector; a Check App State with `IsLoose="True"` and a marker scope selector inside a real card. Full values (window plus element) work.
4. **Leftover classic activities** compile and run on the Windows framework; they are not broken. Report them as "not migrated" with their reason so the user can plan the manual work.
5. **Runtime prerequisites for the report.** Studio 2024.10 or later to open the project. Robots on the same release line as `<UIA_VERSION>`. Modern UIA needs the browser extensions installed on the robot machines for web targets. Suggest the project setting "Log target & anchor search steps" = Info for the first debug run.
