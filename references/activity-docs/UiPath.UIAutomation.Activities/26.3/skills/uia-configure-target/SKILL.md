---
name: uia-configure-target
description: "Primary entry point for configuring a UiPath target — ensures the screen and element exist in the Object Repository, checking for existing entries before creating new ones. Returns the OR reference ID. Use when asked to 'configure target', 'configure application', 'set up target', 'set up application', 'create target in OR', 'find or create target', 'get OR reference for an element', 'select application window', 'create window selector', 'add target to object repository', or when an orchestrator agent needs an OR element reference for a UI element. Trigger this whenever building automation workflows that need reliable OR references."
argument-hint: "--window <description> [--element <description>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>]"
allowed-tools: Bash, Read, Write, Skill, AskUserQuestion
---

Ensure a UI target (screen + element) exists in the Object Repository. Checks for existing OR entries first — creates new ones only when needed. Returns the OR reference ID.

`$ARGUMENTS` format: `--window <description> [--element <description>] [--semantic] [--no-improve] [--from-snapshot] [--activity <type>]`

**IMPORTANT: Use forward slashes in ALL paths.**

**IMPORTANT: Follow the steps mechanically. Do NOT add commentary or analysis between steps.**

**IMPORTANT: This skill invokes sub-skills (`/uia-create-selector`, `/uia-improve-selector`) in TARGET-2, TARGET-5, and TARGET-6. Each sub-skill call is just one step in THIS flow. After each sub-skill finishes, continue with the next step below — do NOT stop.**

## CLI

```
CLI="uip rpa uia"
```

**IMPORTANT: The CLI resolves relative paths against its own install directory, not the shell's cwd. Always convert folder paths to absolute before passing them to the CLI** (e.g., `"$(pwd)/.local/.uia/.configure-target"`).

## Input Parsing

Extract from `$ARGUMENTS`:

- `--window <description>` → `$WINDOW`. Window/tab description to target.
- `--element <description>` → `$ELEMENT` (optional). Target element description. If omitted, run in **screen-only mode**.
- `--semantic` → `$CONFIGURE_SEMANTIC=true` (default: `false`). Enable Semantic (NLP) secondary targeting. Ignored in screen-only mode.
- `--no-improve` → `$NO_IMPROVE=true` (default: `false`). Skip selector improvement steps.
- `--from-snapshot` → `$FROM_SNAPSHOT=true` (default: `false`). Generate selectors from captured tree snapshot instead of probing the live element.
- `--activity <type>` → `$ACTIVITY_TYPE` (default: `Click`). Valid values: `Click`, `GetText`, `SetText`, `TypeInto`, `Check`, `Hover`, `Highlight`, `SelectItem`, `GetAttribute`, `TakeScreenshot`, `KeyboardShortcut`, `MouseScroll`, `DragAndDrop`, `InjectJsScript`, `ExtractData`, `CheckState`, `FindElements`, `SetFocus`, `CheckElement`, `ElementScope`, `WindowOperations`.

If `$WINDOW` is not provided, ask the user which application/window to target.

Derive two names by converting to Title Case:

- `$SCREEN_NAME` from `$WINDOW` (e.g., "google chrome" → `Google Chrome`)
- `$ELEMENT_NAME` from `$ELEMENT` (e.g., "add to cart button" → `Add To Cart Button`). Only needed if `$ELEMENT` is provided.

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
    "SearchSteps": ["Selector"],
    "SelectionStrategy": "Default"
}
```

## TARGET-2: Create Window Selector

Invoke `/uia-create-selector` with:

```
--window $WINDOW --folder $WORK_FOLDER --no-improve --quiet
```

If `$FROM_SNAPSHOT` is true, append `--from-snapshot`.

The window selector is always created without improvement first — improvement is deferred to TARGET-6.

**→ After the sub-skill completes, your next action is TARGET-3 below.**

## TARGET-3: Search for Screen in OR

Search for matching screens using the definition file (avoids shell escaping issues with raw XML selectors):

```bash
"$CLI" object-repository get-screens --definition "$(pwd)/$WORK_FOLDER/TargetDefinition.json"
```

The output is a table with columns including: Name, ReferenceId, Selector, and possibly others.

Initialize `$SCREEN_REF_ID` to empty.

**If the table has rows:** compare each row against `$WINDOW` to find the best match:

- **Name match** (case-insensitive): strong signal. E.g., screen named "Google Chrome" matches window description "google chrome".
- **Selector match**: if the stored window selector targets the same application and window title, strong signal.

**Confident match found:** save the screen's `ReferenceId` as `$SCREEN_REF_ID`.

**Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.

**If the table is empty or the command fails** — no matching screen exists. Leave `$SCREEN_REF_ID` empty.

## TARGET-4: Search for Element in OR

**Skip if screen-only mode** (no `$ELEMENT`). Proceed to TARGET-6.

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

**Confident match found:** save the element's `ReferenceId` as `$ELEMENT_REF_ID`. Skip to **Output (found)**.

**Multiple plausible matches:** list the candidates with their Name and ReferenceId and ask the user to pick.

**No match found:** proceed to TARGET-5.

## TARGET-5: Create Element Selector

Invoke `/uia-create-selector` with:

```
--window $WINDOW --element $ELEMENT --folder $WORK_FOLDER --activity $ACTIVITY_TYPE --no-improve --quiet
```

If `$FROM_SNAPSHOT` is true, append `--from-snapshot`.

The `$WORK_FOLDER` already contains `TargetCapture.json` with `WindowSelector` set from TARGET-2. Because of this, `uia-create-selector` skips window capture (CREATE-1–CREATE-3) and proceeds directly to element capture and selector generation.

**→ After the sub-skill completes, your next action is TARGET-6 below.**

## TARGET-6: Improve Selectors

**Skip if `$NO_IMPROVE` is true.**

Invoke `/uia-improve-selector` with `$WORK_FOLDER --mode improve --quiet` as the argument.

This single call improves whatever is in `TargetCapture.json` — window selector only (screen-only mode) or window + element selector together. The improve skill writes the winning selectors back to `TargetDefinition.json`.

**→ After the sub-skill completes, your next action is TARGET-7 below.**

## TARGET-7: Configure Semantic Targeting (if --semantic)

**Skip if `$CONFIGURE_SEMANTIC` is `false`.**

Derive a natural-language description of the element from `$ELEMENT` (e.g., `"Submit button in the order form"`). Save as `$SEMANTIC_SELECTOR`.

Read `$WORK_FOLDER/TargetDefinition.json`, set `"SemanticSelector": "$SEMANTIC_SELECTOR"`, and append `"Semantic"` to the `SearchSteps` array. Write back.

## TARGET-8: Register in OR

**If `$SCREEN_REF_ID` is empty** (no matching screen found in TARGET-3), create it:

```bash
"$CLI" object-repository create-screen --definition "$(pwd)/$WORK_FOLDER/TargetDefinition.json" --name "$SCREEN_NAME"
```

Save stdout as `$SCREEN_REF_ID`. If this fails, show the error and stop.

**Screen-only mode** (no `$ELEMENT`): skip to **Output**.

**Create element:**

```bash
"$CLI" object-repository create-element --definition "$(pwd)/$WORK_FOLDER/TargetDefinition.json" --screen-reference-id "$SCREEN_REF_ID" --name "$ELEMENT_NAME"
```

Save stdout as `$ELEMENT_REF_ID`. If this fails, show the error and stop.

## Output

Read `$WORK_FOLDER/TargetDefinition.json` for the final selectors.

**Line 1** — what happened:

- Element found in OR: `**Target found:** $ELEMENT_REF_ID (screen: $SCREEN_REF_ID)`
- Element created: `**Target created:** $ELEMENT_REF_ID (screen: $SCREEN_REF_ID)`
- Screen-only, found: `**Screen found:** $SCREEN_REF_ID`
- Screen-only, created: `**Screen created:** $SCREEN_REF_ID`

**Then show selectors** (skip any that are empty):

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

No observations, no quality notes, no suggestions. Just the result.
