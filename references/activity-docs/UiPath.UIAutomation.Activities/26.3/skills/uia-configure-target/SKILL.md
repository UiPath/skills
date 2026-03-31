---
name: uia-configure-target
description: "Primary entry point for configuring a UiPath target — ensures the screen and element exist in the Object Repository, checking for existing entries before creating new ones. Returns the OR reference ID. Supports batch element configuration via pipe-separated list (e.g., --elements \"Five button | Plus button | Equals button\") to avoid redundant window captures and screen lookups. Use when asked to 'configure target', 'configure application', 'set up target', 'set up application', 'create target in OR', 'find or create target', 'get OR reference for an element', 'select application window', 'create window selector', 'add target to object repository', or when an orchestrator agent needs an OR element reference for a UI element. Trigger this whenever building automation workflows that need reliable OR references."
argument-hint: "--window <description> [--elements <descriptions>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>] [--project-dir <path>]"
allowed-tools: Bash, Read, Write, Agent, AskUserQuestion
---

Ensure a UI target (screen + elements) exists in the Object Repository. Checks for existing OR entries first — creates new ones only when needed. Returns the OR reference ID(s).

`$ARGUMENTS` format: `--window <description> [--elements <descriptions>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>] [--project-dir <path>]`

**IMPORTANT: Use forward slashes in ALL paths.**

**IMPORTANT: Follow the steps mechanically. Do NOT add commentary or analysis between steps.**

## CLI

```
CLI="uip rpa uia"
```

If `$PROJECT_DIR` is set, append it: `CLI="uip rpa uia --project-dir \"$PROJECT_DIR\"" --use-studio`. All subsequent `"$CLI" ...` commands will automatically include it.

## Input Parsing

Extract from `$ARGUMENTS`:

- `--window <description>` → `$WINDOW`. Window/tab description to target.
- `--elements <descriptions>` → pipe-separated list of target element descriptions (optional). Use `|` to separate multiple elements (e.g., `"Five button | Plus button | Equals button"`). If omitted, run in **screen-only mode**.
- `--semantic` → `$CONFIGURE_SEMANTIC=true` (default: `false`). Enable Semantic (NLP) secondary targeting. Ignored in screen-only mode.
- `--no-improve` → `$NO_IMPROVE=true` (default: `false`). Skip selector improvement steps.
- `--from-snapshot` → `$FROM_SNAPSHOT=true` (default: `false`). Generate selectors from captured tree snapshot instead of probing the live element.
- `--activity <type>` → `$ACTIVITY_TYPE` (default: `Click`). Valid values: `Click`, `GetText`, `SetText`, `TypeInto`, `Check`, `Hover`, `Highlight`, `SelectItem`, `GetAttribute`, `TakeScreenshot`, `KeyboardShortcut`, `MouseScroll`, `DragAndDrop`, `InjectJsScript`, `ExtractData`, `CheckState`, `FindElements`, `SetFocus`, `CheckElement`, `ElementScope`, `WindowOperations`.
- `--project-dir <path>` → `$PROJECT_DIR` (optional). UiPath project directory. Passed through to all CLI commands and subagent prompts.

If `$WINDOW` is not provided, ask the user which application/window to target.

**Parse elements:** Split the `--elements` value on `|` and trim whitespace from each entry to produce `$ELEMENT_LIST` (array). Derive `$ELEMENT_NAMES` by converting each entry to Title Case (e.g., "add to cart button" → `Add To Cart Button`).

Derive `$SCREEN_NAME` from `$WINDOW` by converting to Title Case (e.g., "google chrome" → `Google Chrome`).

## TARGET-0: Check UIA Package Version

The `uip rpa uia` subcommands require **`UiPath.UIAutomation.Activities` >= 26.3.1-beta.11555873**. Check the installed version:

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --project-dir "$PROJECT_DIR" --output json --use-studio
```

Also check `project.json` in `$PROJECT_DIR` for the currently installed version under `dependencies`.

**If the installed version is below `26.3.1-beta.11555873`:** ask the user whether to upgrade using AskUserQuestion:

> "The project's `UiPath.UIAutomation.Activities` package (currently `<installed_version>`) is below the minimum required for `uip rpa uia` CLI features (`26.3.1-beta.11555873`). This upgrade enables object repository management, snapshot capture, and selector intelligence. May I upgrade it?"

If the user approves, run:

```bash
uip rpa install-or-update-packages --packages '[{"id": "UiPath.UIAutomation.Activities", "version": "26.3.1-beta.11555873"}]' --project-dir "$PROJECT_DIR" --output json
```

Wait for restore to complete, then continue. If the user declines, warn that `uip rpa uia` commands will fail and fall back to the indication tools (Step 3 in the UI Automation Guide).

## TARGET-1: Prepare Working Folder

Clean and create:

```bash
rm -rf .local/.uia/.configure-target
mkdir -p .local/.uia/.configure-target
```

Set `$WORK_FOLDER` to the **absolute path** of `.local/.uia/.configure-target` (the CLI requires absolute paths).

Write initial `$WORK_FOLDER/TargetDefinition.json` using the Write tool:

```json
{
    "SelectionStrategy": "Default"
}
```

## TARGET-2: Create Window Selector

Spawn a general-purpose subagent with the prompt below. Use `model: "sonnet"`. Replace all `$VARIABLES` with their actual values. Use forward slashes in all paths.

---

You are creating a window selector for a UiPath target. Follow the instructions in the skill file mechanically.

1. Read `../uia-create-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `--window $WINDOW --folder $WORK_FOLDER --quiet` (add `--from-snapshot` if `$FROM_SNAPSHOT` is true; add `--project-dir $PROJECT_DIR` if `$PROJECT_DIR` is set).
3. The folder already exists and contains `TargetDefinition.json`. Write all output files there.

---

Wait for the subagent to complete, then continue.

**If `$ELEMENT_LIST` is not empty**, capture the app-level tree now (the window selector is set, so this produces the full app tree and screenshot):

```bash
"$CLI" snapshot capture --folder-path "$WORK_FOLDER"
```

This produces `ApplicationLevelNodeTreeInfo.json`, `ApplicationLevelApplicationMetadata.json`, and `ApplicationScreenshot.jpg` in `$WORK_FOLDER`. Every element shares this tree.

## TARGET-3: Search for Screen in OR

Search for matching screens using the definition file (avoids shell escaping issues with raw XML selectors):

```bash
"$CLI" object-repository get-screens --definition-file-path "$WORK_FOLDER/TargetDefinition.json"
```

The output is a table with columns including: Name, ReferenceId, Selector, and possibly others.

Initialize `$SCREEN_REF_ID` to empty.

**If the table has rows:** compare each row against `$WINDOW` to find the best match:

- **Name match** (case-insensitive): strong signal. E.g., screen named "Google Chrome" matches window description "google chrome".
- **Selector match**: if the stored window selector targets the same application and window title, strong signal.

**Confident match found:** save the screen's `ReferenceId` as `$SCREEN_REF_ID`.

**Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.

**If the table is empty or the command fails** — no matching screen exists. Leave `$SCREEN_REF_ID` empty.

**Screen-only mode** (no `--elements`): skip to TARGET-6.

## TARGET-4: Search for Existing Elements in OR

**Skip if `$SCREEN_REF_ID` is empty** (no screen found — elements can't exist). Mark all elements as needing creation and proceed to TARGET-5.

Get all elements registered under this screen (single call, shared across all elements):

```bash
"$CLI" object-repository get-elements --screen-reference-id "$SCREEN_REF_ID"
```

The output is a table with columns including: Name, ReferenceId, Screenshot file path, Selector, Semantic selector.

**If the table is empty or the command fails:** no existing elements — mark all as needing creation and proceed to TARGET-5.

**If elements exist:** compare each row against EVERY element in `$ELEMENT_LIST` to find matches:

- **Name match** (case-insensitive, allowing minor wording differences): strong signal. E.g., element named "Add To Cart Button" matches description "add to cart button".
- **Semantic selector match**: if the stored semantic description refers to the same UI element as `$ELEMENT`, strong signal.
- **Selector match**: if the stored selector targets the same control type with similar identifying attributes (aaname, name, automationid), supporting signal.
- If a screenshot file path is present and the match is uncertain, read the screenshot for visual confirmation.

For each element in `$ELEMENT_LIST`:
- **Confident match found:** record `{$ELEMENT_NAME, $ELEMENT_REF_ID, found}`. This element skips TARGET-5 through TARGET-8.
- **Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.
- **No match found:** mark as needing creation.

Collect elements needing creation into `$ELEMENTS_TO_CREATE` (list of `{$INDEX, $ELEMENT, $ELEMENT_NAME, $ELEMENT_WORK_FOLDER}`).

If `$ELEMENTS_TO_CREATE` is empty, skip to **Output**.

## TARGET-5: Create Element Selectors (parallel)

Prepare element work folders. For each element in `$ELEMENTS_TO_CREATE`, set `$ELEMENT_WORK_FOLDER = $WORK_FOLDER/elements/$INDEX` and run (all in parallel):

```bash
mkdir -p $ELEMENT_WORK_FOLDER
cp $WORK_FOLDER/TargetCapture.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/TargetDefinition.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/TopLevelNodeTreeInfo.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/ApplicationLevelNodeTreeInfo.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/ApplicationLevelApplicationMetadata.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/ApplicationScreenshot.jpg $ELEMENT_WORK_FOLDER/
```

Then spawn one `Agent` per element, **all in a single message** so they run in parallel. Use `model: "sonnet"` for each. Use the prompt below for each, replacing all `$VARIABLES` with actual values. Use forward slashes in all paths.

**IMPORTANT: Each agent must be a separate, self-contained `Agent` tool call.**

---

You are creating an element selector for a UiPath target. Follow the instructions in the skill file mechanically.

1. Read `../uia-create-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `--window $WINDOW --element $ELEMENT --folder $ELEMENT_WORK_FOLDER --activity $ACTIVITY_TYPE --quiet` (add `--from-snapshot` if `$FROM_SNAPSHOT` is true; add `--project-dir $PROJECT_DIR` if `$PROJECT_DIR` is set).
3. The folder already exists and contains `TargetCapture.json` with `WindowSelector` set, plus `ApplicationLevelNodeTreeInfo.json`, `ApplicationLevelApplicationMetadata.json`, and `ApplicationScreenshot.jpg`. This means the skill skips CREATE-1 through CREATE-4 and starts at CREATE-5 (find the element).

---

Wait for ALL agents to complete before proceeding.

## TARGET-6: Improve Selectors

**Skip if `$NO_IMPROVE` is true.** Proceed to TARGET-7.

### Assess selector reliability

Before running improvement, evaluate each selector to decide whether it actually needs it. The goal is to skip improvement for selectors that already reliably and uniquely identify their target.

**Screen-only mode:** Read `$WORK_FOLDER/TargetDefinition.json` and assess the `WindowSelector`.

**Element mode:** For each element in `$ELEMENTS_TO_CREATE`, read `$ELEMENT_WORK_FOLDER/TargetDefinition.json` and assess the `PartialSelector` (element selector). Also assess the `WindowSelector` once (from the first element).

**Assessment criteria — a selector is RELIABLE if ALL of the following hold:**

1. **Uses reliable attributes for its tag type.** Each tag has at least one developer-assigned or semantic identifier (e.g., `automationid`, `name`, `role`, `aria-label`, `id`, `app`, `cls`). Fragile if all identifying attributes are last-resort or unreliable for their tag type.

2. **Not positionally dependent.** The selector does NOT rely solely on `idx`, `tableRow` or `tableCol` without any stable identifier alongside them. A tag with only positional attributes is fragile.

3. **Attribute values are stable.** Watch for auto-generated IDs (purely numeric like `id='89763184740'`), CSS-in-JS hashes (`class='css-1wq41pf'`), component-path IDs with 3+ dot-separated structural segments, or framework hashes in tag names. These indicate the selector will break across environments. Short semantic values (`id='search-form'`, `automationid='btnSubmit'`) are fine.

4. **Activity-appropriate attributes.** For `GetText`/`SetText`/`TypeInto`/`ExtractData`: must NOT use content-reflecting attributes (`text`, `aaname`, `visibleinnertext`, `innertext`) as primary identifiers — these change with the data. Should use structural attributes (`automationid`, `role`, `aria-label`, `id`, `labeledby`). For `Check`/`Uncheck`: must NOT rely on state attributes (`checked`, `aastate`). For `SelectItem`: must NOT rely on `selecteditem` or `value`.

5. **Good structure.** A typical selector has ~2 tags. Selectors with 4+ tags are over-specified and fragile (intermediate containers add breakage points without value). Each tag should have 2-3 meaningful attributes — a tag with only `tag` and no other attribute, or only a generic `role`/`cls` shared by many siblings, is under-specified.

Mark each selector (window + each element) as `RELIABLE` or `NEEDS_IMPROVEMENT`.

**If all selectors are RELIABLE:** skip improvement entirely and proceed to TARGET-7.

**IMPORTANT: Do NOT attempt to fix selectors yourself (e.g., by removing attributes or rewriting tags). Selectors marked `NEEDS_IMPROVEMENT` MUST go through the uia-improve-selector subagent below — it validates candidates against the live application to ensure correctness.**

### Run improvement on fragile selectors only

Collect only the elements marked `NEEDS_IMPROVEMENT` into `$ELEMENTS_TO_IMPROVE`. If the window selector is `NEEDS_IMPROVEMENT`, include it too.

**Screen-only mode (window needs improvement):** Spawn a single subagent to improve `$WORK_FOLDER` (window selector only).

**Element mode:** Spawn one `Agent` per element in `$ELEMENTS_TO_IMPROVE`, **all in a single message** so they run in parallel. Each improves window + element together. If the window selector is `RELIABLE` but some elements need improvement, the subagent still receives the window selector in the folder — it will only change the element selector.

**IMPORTANT: Each agent must be a separate, self-contained `Agent` tool call. Use `model: "sonnet"` for each.**

Use the prompt below for each, replacing `$FOLDER` with `$WORK_FOLDER` (screen-only) or `$ELEMENT_WORK_FOLDER` (per element):

---

You are improving UiPath selectors to make them more robust. Follow the instructions in the skill file mechanically.

1. Read `../uia-improve-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `$FOLDER --mode improve --quiet` (add `--project-dir $PROJECT_DIR` if `$PROJECT_DIR` is set).
3. The folder contains `TargetCapture.json` with the current selectors and `TargetDefinition.json` for output. Improve whatever is present — window selector only or window + element selector together.

---

Wait for all agents to complete.

**Element mode only:** if the window selector was improved, read the `WindowSelector` from the first improved element's `TargetDefinition.json` and update `$WORK_FOLDER/TargetDefinition.json` with it (so TARGET-8 screen creation uses the improved window selector).

## TARGET-7: Configure Semantic Targeting

**Skip if `$CONFIGURE_SEMANTIC` is `false` or screen-only mode.** Proceed to TARGET-8.

For each element in `$ELEMENTS_TO_CREATE`:

Derive a natural-language description of the element from `$ELEMENT` (e.g., `"Submit button in the order form"`). Save as `$SEMANTIC_SELECTOR`.

Read `$ELEMENT_WORK_FOLDER/TargetDefinition.json`, set `"SemanticSelector": "$SEMANTIC_SELECTOR"`. Write back.

## TARGET-8: Register in OR

**If `$SCREEN_REF_ID` is empty** (no matching screen found in TARGET-3), create it:

```bash
"$CLI" object-repository create-screen --definition-file-path "$WORK_FOLDER/TargetDefinition.json" --name "$SCREEN_NAME"
```

The stdout is the screen's reference ID. Save it as `$SCREEN_REF_ID`. If the command fails, show the error and stop.

**Screen-only mode:** skip to **Output**.

**Create elements sequentially.** For each element in `$ELEMENTS_TO_CREATE`:

```bash
"$CLI" object-repository create-element --definition-file-path "$ELEMENT_WORK_FOLDER/TargetDefinition.json" --screen-reference-id "$SCREEN_REF_ID" --name "$ELEMENT_NAME"
```

The stdout is the element's reference ID. Save it as `$ELEMENT_REF_ID`. If the command fails, show the error and stop.

Record `{$ELEMENT_NAME, $ELEMENT_REF_ID, created}`.

## Output

Retrieve XAML for the screen and all elements (found or created) using the CLI:

```bash
"$CLI" object-repository get-screen-xaml --reference-id "$SCREEN_REF_ID"
```

Save the output as `$SCREEN_XAML`.

For each element (both found and created), retrieve its XAML:

```bash
"$CLI" object-repository get-element-xaml --reference-id "$ELEMENT_REF_ID"
```

Save the output as `$ELEMENT_XAML`.

**1. Screen:**

```
**Screen <found|created>:** $SCREEN_REF_ID

\`\`\`xml
$SCREEN_XAML
\`\`\`
```

**2. Window selector** (read from `$WORK_FOLDER/TargetDefinition.json`):

```
**Window:**
\`\`\`xml
<WindowSelector>
\`\`\`
```

**3. Element table** (skip if `$ELEMENT_LIST` is empty):

```
| Element | Status | Reference ID |
|---------|--------|--------------|
| $ELEMENT_NAME_1 | found/created | $ELEMENT_REF_ID_1 |
| ... | ... | ... |
```

**4. Per-element details** (skip if `$ELEMENT_LIST` is empty). For each element: if it was created, read selectors from `$WORK_FOLDER/elements/$INDEX/TargetDefinition.json`. Skip any empty fields:

```
**$ELEMENT_NAME:**
**Target:**
\`\`\`xml
<PartialSelector>
\`\`\`

**Semantic:** "<SemanticSelector>"

**XAML:**
\`\`\`xml
$ELEMENT_XAML
\`\`\`
```

No observations, no quality notes, no suggestions. Just the result.
