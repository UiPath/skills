---
name: uia-configure-target
description: "Primary entry point for configuring a UiPath target — ensures the screen and element exist in the Object Repository, checking for existing entries before creating new ones. Returns the OR reference ID. Supports batch element configuration via pipe-separated list (e.g., --elements \"Five button | Plus button | Equals button\") to avoid redundant window captures and screen lookups. Use when asked to 'configure target', 'configure application', 'set up target', 'set up application', 'create target in OR', 'find or create target', 'get OR reference for an element', 'select application window', 'create window selector', 'add target to object repository', or when an orchestrator agent needs an OR element reference for a UI element. Trigger this whenever building automation workflows that need reliable OR references."
argument-hint: "--window <description> [--elements <descriptions>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>]"
allowed-tools: Bash, Read, Write, Agent, AskUserQuestion
---

Ensure a UI target (screen + elements) exists in the Object Repository. Checks for existing OR entries first — creates new ones only when needed. Returns the OR reference ID(s).

`$ARGUMENTS` format: `--window <description> [--elements <descriptions>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>]`

**IMPORTANT: Use forward slashes in ALL paths.**

**IMPORTANT: Follow the steps mechanically. Do NOT add commentary or analysis between steps.**

## CLI

```
CLI="uip rpa uia"
```

**IMPORTANT: The CLI resolves relative paths against its own install directory, not the shell's cwd. Always convert folder paths to absolute before passing them to the CLI** (e.g., `"$(pwd)/.local/.uia/.configure-target"`).

## Input Parsing

Extract from `$ARGUMENTS`:

- `--window <description>` → `$WINDOW`. Window/tab description to target.
- `--elements <descriptions>` → pipe-separated list of target element descriptions (optional). Use `|` to separate multiple elements (e.g., `"Five button | Plus button | Equals button"`). If omitted, run in **screen-only mode**.
- `--semantic` → `$CONFIGURE_SEMANTIC=true` (default: `false`). Enable Semantic (NLP) secondary targeting. Ignored in screen-only mode.
- `--no-improve` → `$NO_IMPROVE=true` (default: `false`). Skip selector improvement steps.
- `--from-snapshot` → `$FROM_SNAPSHOT=true` (default: `false`). Generate selectors from captured tree snapshot instead of probing the live element.
- `--activity <type>` → `$ACTIVITY_TYPE` (default: `Click`). Valid values: `Click`, `GetText`, `SetText`, `TypeInto`, `Check`, `Hover`, `Highlight`, `SelectItem`, `GetAttribute`, `TakeScreenshot`, `KeyboardShortcut`, `MouseScroll`, `DragAndDrop`, `InjectJsScript`, `ExtractData`, `CheckState`, `FindElements`, `SetFocus`, `CheckElement`, `ElementScope`, `WindowOperations`.

If `$WINDOW` is not provided, ask the user which application/window to target.

**Parse elements:** Split the `--elements` value on `|` and trim whitespace from each entry to produce `$ELEMENT_LIST` (array). Derive `$ELEMENT_NAMES` by converting each entry to Title Case (e.g., "add to cart button" → `Add To Cart Button`).

Derive `$SCREEN_NAME` from `$WINDOW` by converting to Title Case (e.g., "google chrome" → `Google Chrome`).

## TARGET-1: Prepare Working Folder

Clean and create:

```bash
rm -rf .local/.uia/.configure-target
mkdir -p .local/.uia/.configure-target
```

Set `$WORK_FOLDER=.local/.uia/.configure-target`.

Write initial `$WORK_FOLDER/TargetDefinition.json` using the Write tool:

```json
{
    "SelectionStrategy": "Default"
}
```

## TARGET-2: Create Window Selector

Spawn a general-purpose subagent with the prompt below. Replace all `$VARIABLES` with their actual values. Use forward slashes in all paths.

---

You are creating a window selector for a UiPath target. Follow the instructions in the skill file mechanically.

1. Read `../uia-create-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `--window $WINDOW --folder $WORK_FOLDER --quiet` (add `--from-snapshot` if `$FROM_SNAPSHOT` is true).
3. The folder already exists and contains `TargetDefinition.json`. Write all output files there.

---

Wait for the subagent to complete, then continue to TARGET-3.

## TARGET-3: Search for Screen in OR

Search for matching screens using the definition file (avoids shell escaping issues with raw XML selectors):

```bash
"$CLI" object-repository get-screens --definition-file-path "$(pwd)/$WORK_FOLDER/TargetDefinition.json"
```

The output is a table with columns including: Name, ReferenceId, Selector, and possibly others.

Initialize `$SCREEN_REF_ID` to empty.

**If the table has rows:** compare each row against `$WINDOW` to find the best match:

- **Name match** (case-insensitive): strong signal. E.g., screen named "Google Chrome" matches window description "google chrome".
- **Selector match**: if the stored window selector targets the same application and window title, strong signal.

**Confident match found:** save the screen's `ReferenceId` as `$SCREEN_REF_ID`.

**Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.

**If the table is empty or the command fails** — no matching screen exists. Leave `$SCREEN_REF_ID` empty.

**Screen-only mode** (no `--elements`): skip directly to TARGET-8.

## Element Loop

Process each element in `$ELEMENT_LIST`. For each `$ELEMENT` at index `$INDEX` in the list:

1. Set `$ELEMENT_NAME = $ELEMENT_NAMES[$INDEX]`.
2. Set `$ELEMENT_WORK_FOLDER = $WORK_FOLDER/elements/$INDEX`.
3. Prepare the element work folder:

```bash
mkdir -p $ELEMENT_WORK_FOLDER
cp $WORK_FOLDER/TargetCapture.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/TargetDefinition.json $ELEMENT_WORK_FOLDER/
cp $WORK_FOLDER/TopLevelNodeTreeInfo.json $ELEMENT_WORK_FOLDER/
```

4. Execute TARGET-4 through TARGET-8 below using `$ELEMENT_WORK_FOLDER` as the working folder for this element.

After all elements are processed, skip to **Output**.

## TARGET-4: Search for Element in OR

**Skip if `$SCREEN_REF_ID` is empty** (no screen found — element can't exist). Proceed to TARGET-5.

Get all elements registered under this screen:

```bash
"$CLI" object-repository get-elements --screen-reference-id "$SCREEN_REF_ID"
```

The output is a table with columns including: Name, ReferenceId, Screenshot file path, Selector, Semantic selector.

**If the table is empty or the command fails:** no existing elements — proceed to TARGET-5.

**If elements exist:** compare each row against `$ELEMENT` to find a match:

- **Name match** (case-insensitive, allowing minor wording differences): strong signal. E.g., element named "Add To Cart Button" matches description "add to cart button".
- **Semantic selector match**: if the stored semantic description refers to the same UI element as `$ELEMENT`, strong signal.
- **Selector match**: if the stored selector targets the same control type with similar identifying attributes (aaname, name, automationid), supporting signal.
- If a screenshot file path is present and the match is uncertain, read the screenshot for visual confirmation.

**Confident match found:** save the element's `ReferenceId` as `$ELEMENT_REF_ID`. Record `{$ELEMENT_NAME, $ELEMENT_REF_ID, found}` and **continue to the next element** in the loop (skip TARGET-5 through TARGET-8 for this element).

**Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.

**No match found:** proceed to TARGET-5.

## TARGET-5: Create Element Selector

Spawn a general-purpose subagent with the prompt below. Replace all `$VARIABLES` with their actual values. Use forward slashes in all paths.

---

You are creating an element selector for a UiPath target. Follow the instructions in the skill file mechanically.

1. Read `../uia-create-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `--window $WINDOW --element $ELEMENT --folder $ELEMENT_WORK_FOLDER --activity $ACTIVITY_TYPE --quiet` (add `--from-snapshot` if `$FROM_SNAPSHOT` is true).
3. The folder already exists and contains `TargetCapture.json` with `WindowSelector` set. This means the skill skips CREATE-1 through CREATE-3 and starts at CREATE-4 (element capture).

---

Wait for the subagent to complete, then continue to TARGET-6.

## TARGET-6: Improve Selectors

**Skip if `$NO_IMPROVE` is true.**

Spawn a general-purpose subagent with the prompt below. Replace all `$VARIABLES` with their actual values. Use forward slashes in all paths.

---

You are improving UiPath selectors to make them more robust. Follow the instructions in the skill file mechanically.

1. Read `../uia-improve-selector/SKILL.md` (relative to the directory this file is in) to learn the full procedure.
2. Execute the skill steps with these arguments: `$ELEMENT_WORK_FOLDER --mode improve --quiet`.
3. The folder contains `TargetCapture.json` with the current selectors and `TargetDefinition.json` for output. Improve whatever is present — window selector only or window + element selector together.
4. The skill's IMPROVE-2 step requires spawning its own subagent — follow those instructions as written.

---

Wait for the subagent to complete, then continue to TARGET-7.

## TARGET-7: Configure Semantic Targeting (if --semantic)

**Skip if `$CONFIGURE_SEMANTIC` is `false`.**

Derive a natural-language description of the element from `$ELEMENT` (e.g., `"Submit button in the order form"`). Save as `$SEMANTIC_SELECTOR`.

Read `$ELEMENT_WORK_FOLDER/TargetDefinition.json`, set `"SemanticSelector": "$SEMANTIC_SELECTOR"`. Write back.

## TARGET-8: Register in OR

**If `$SCREEN_REF_ID` is empty** (no matching screen found in TARGET-3), create it:

```bash
"$CLI" object-repository create-screen --definition-file-path "$(pwd)/$ELEMENT_WORK_FOLDER/TargetDefinition.json" --name "$SCREEN_NAME"
```

Save stdout as `$SCREEN_REF_ID`. If this fails, show the error and stop. Once created, `$SCREEN_REF_ID` persists for all subsequent elements in the loop.

**Create element:**

```bash
"$CLI" object-repository create-element --definition-file-path "$(pwd)/$ELEMENT_WORK_FOLDER/TargetDefinition.json" --screen-reference-id "$SCREEN_REF_ID" --name "$ELEMENT_NAME"
```

Save stdout as `$ELEMENT_REF_ID`. If this fails, show the error and stop.

Record `{$ELEMENT_NAME, $ELEMENT_REF_ID, created}` and continue to the next element in the loop.

## Output

**Screen-only mode** (no `--elements`):

- Screen found: `**Screen found:** $SCREEN_REF_ID`
- Screen created: `**Screen created:** $SCREEN_REF_ID`

Then show the window selector:

```
**Window:**
\`\`\`xml
<WindowSelector from $WORK_FOLDER/TargetDefinition.json>
\`\`\`
```

**Single element** (one entry in `$ELEMENT_LIST`):

Read `$ELEMENT_WORK_FOLDER/TargetDefinition.json` for the final selectors.

- Element found in OR: `**Target found:** $ELEMENT_REF_ID (screen: $SCREEN_REF_ID)`
- Element created: `**Target created:** $ELEMENT_REF_ID (screen: $SCREEN_REF_ID)`

Then show selectors (skip any that are empty):

```
**Window:**
\`\`\`xml
<WindowSelector from TargetDefinition.json>
\`\`\`

**Target:**
\`\`\`xml
<PartialSelector from TargetDefinition.json>
\`\`\`

**Semantic:** "<SemanticSelector from TargetDefinition.json>"
```

**Multiple elements** (more than one entry in `$ELEMENT_LIST`):

```
**Batch complete** — $N elements on screen $SCREEN_NAME ($SCREEN_REF_ID):

| Element | Status | Reference ID |
|---------|--------|--------------|
| $ELEMENT_NAME_1 | found/created | $ELEMENT_REF_ID_1 |
| $ELEMENT_NAME_2 | found/created | $ELEMENT_REF_ID_2 |
| ... | ... | ... |
```

Then for each element, show its selectors (read from `$WORK_FOLDER/elements/$INDEX/TargetDefinition.json`):

```
**$ELEMENT_NAME:**

**Target:**
\`\`\`xml
<PartialSelector>
\`\`\`

**Semantic:** "<SemanticSelector>" (if present)
```

No observations, no quality notes, no suggestions. Just the result.
