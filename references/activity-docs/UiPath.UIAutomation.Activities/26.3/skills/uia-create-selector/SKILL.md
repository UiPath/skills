---
name: uia-create-selector
description: Generate a UiPath selector for a UI element by describing it in natural language against a live running application. Use when asked to "create a selector", "get selector for", "find selector", or "selector for <element>". Example phrases "create selector for add to cart button", "selector for the search box in Chrome", "get me a selector for the Submit button"
argument-hint: "--window <description> [--element <description>] [--folder <path>] [--from-snapshot] [--activity <type>] [--no-improve] [--quiet]"
allowed-tools: Bash, Read, Write, Skill, AskUserQuestion
---

Generate a robust UiPath selector for an element described in natural language, using the live running application.

**IMPORTANT: Use forward slashes in ALL paths.**

**IMPORTANT: Follow the steps mechanically. Do NOT add commentary, observations, or analysis between steps or after completion. Only speak to the user when asking a question (e.g., ambiguous window/element match).**

## CLI

```
CLI="uip rpa uia"
```

**IMPORTANT: The CLI resolves relative paths against its own install directory, not the shell's cwd. Always convert folder paths to absolute before passing them to the CLI** (e.g., `"$(pwd)/.local/.uia/.create-selector/..."`).

## Input Parsing

Extract from `$ARGUMENTS`:

- `--window <description>` → `$WINDOW`. Window/tab description to target.
- `--element <description>` → `$ELEMENT` (optional). Target element description.
- `--folder <path>` → `$ELEM_FOLDER` (optional). When provided, **skip folder creation and cleanup** (the caller owns the folder). The folder must already exist.
- `--from-snapshot` → `$FROM_SNAPSHOT=true` (default: `false`). Generate selectors from the captured tree snapshot instead of probing the live element. Passed as `--from-snapshot` to `get-default-selector` calls.
- `--activity <type>` → `$ACTIVITY_TYPE` (default: `Click`). Used in `TargetCapture.json`. Valid values: `Click`, `GetText`, `SetText`, `TypeInto`, `Check`, `Hover`, `Highlight`, `SelectItem`, `GetAttribute`, `TakeScreenshot`, `KeyboardShortcut`, `MouseScroll`, `DragAndDrop`, `InjectJsScript`, `ExtractData`, `CheckState`, `FindElements`, `SetFocus`, `CheckElement`, `ElementScope`, `WindowOperations`. If unrecognized, warn and default to `Click`.
- `--no-improve` → `$IMPROVE=false` (default: `true`). Skips the improve step (CREATE-8).
- `--quiet` → `$QUIET=true` (default: `false`). Suppress all output — just write files and complete. Used when this skill is called as a sub-step by another skill.

If `--window` and `--element` are not found as explicit flags, try parsing the remaining text as natural language:
- `Window: <window>. Element: <element>`
- `Window: <window> Element: <element>`
- `<window> - <element>`

If `$WINDOW` is not determined:
- If `--folder` was provided and the folder contains a `TargetCapture.json` with a non-empty `WindowSelector`, `$WINDOW` is not needed — proceed to CREATE-4.
- Otherwise, ask the user.

If `$ELEMENT` is not provided, run in **window-only mode** — execute CREATE-1–CREATE-3, then skip to Output.

## File Roles

- `TargetCapture.json` — Runtime input consumed by CLI commands (`capture-runtime-data`, `get-default-selector`). Contains the selectors being worked on.
- `TargetDefinition.json` — Output configuration consumed by `configure-target` for Object Repository registration. Contains the final selectors plus metadata (SearchSteps, etc.).

Both files share `WindowSelector` and `PartialSelector` fields, but serve different consumers.

## Error Handling

After every CLI command, check the exit code. If non-zero, show the CLI's stderr/stdout to the user and stop. Common failures:
- **capture-runtime-data**: application not running, window minimized, or not visible on screen
- **filter-tree**: tree file missing (prior capture may have failed)
- **get-default-selector**: invalid ref or element not found in tree

## CREATE-1: Capture Top-Level Tree

**If `--folder` was provided**, skip folder creation — `$ELEM_FOLDER` is already set.

Check if `$ELEM_FOLDER/TargetCapture.json` already exists and contains a non-empty `WindowSelector`. If so:
- Read the existing `WindowSelector` and save as `$WINDOW_SELECTOR`
- If **window-only mode**: ensure `$ELEM_FOLDER/TargetDefinition.json` has `"WindowSelector"` set, then skip to **Output**.
- Otherwise: **skip CREATE-1–CREATE-3** and jump to **CREATE-4**.
- The `PartialSelector` in the existing file may be empty — that's expected, you'll populate it in CREATE-6.

If the file doesn't exist or `WindowSelector` is empty, continue below.

**Otherwise**, create a unique working folder:

```bash
NAME_SRC="${ELEMENT:-$WINDOW}"
ELEM_FOLDER=".local/.uia/.create-selector/$(date +%Y%m%d_%H%M%S)_$(echo "$NAME_SRC" | tr ' /:*?"<>|\\' '_' | head -c 40)"
mkdir -p "$ELEM_FOLDER"
```

Write a minimal `TargetCapture.json` (no window selector yet) using the Write tool:

```json
{
    "WindowSelector": "",
    "PartialSelector": "",
    "ActivityType": "$ACTIVITY_TYPE"
}
```

Capture the top-level tree:

```bash
"$CLI" selector-intelligence capture-runtime-data --runtime-data-folder-path "$ELEM_FOLDER"
```

This produces only `TopLevelNodeTreeInfo.json` (top-level windows).

## CREATE-2: Choose a Window

View the window tree:

```bash
"$CLI" selector-intelligence filter-tree --runtime-data-folder-path "$ELEM_FOLDER" --source window
```

Read the output file (path printed to stdout). Match `$WINDOW` against window titles and app names (partial, case-insensitive). Browser tabs are labeled `BrowserTab` with `b` prefix refs (e.g., `b3`) — prefer those over native browser windows for web apps. Regular windows use `w` prefix refs (e.g., `w3`).

Save the matching ref as `$WREF` (e.g., `b3` for a browser tab, `w3` for a native window).
If no match, present the list and ask the user.

## CREATE-3: Get Window Selector

```bash
"$CLI" selector-intelligence get-default-selector --runtime-data-folder-path "$ELEM_FOLDER" --ref $WREF  # append --from-snapshot if $FROM_SNAPSHOT is true
```

Save the stdout output as `$WINDOW_SELECTOR`.

Update `TargetCapture.json` using the Write tool:

```json
{
    "WindowSelector": "$WINDOW_SELECTOR",
    "PartialSelector": "",
    "ActivityType": "$ACTIVITY_TYPE"
}
```

Write or update `$ELEM_FOLDER/TargetDefinition.json`: if the file already exists, read it first and preserve all existing fields. Set `"WindowSelector"` to `$WINDOW_SELECTOR`.

**If window-only mode** (no `$ELEMENT`):
- If `$IMPROVE` is `true`: invoke the `/uia-improve-selector` skill with `$ELEM_FOLDER --mode improve` as the argument. Then stop (the improve skill handles output).
- Otherwise: skip to **Output**.

## CREATE-4: Capture App-Level Tree

```bash
"$CLI" selector-intelligence capture-runtime-data --runtime-data-folder-path "$ELEM_FOLDER"
```

This time `WindowSelector` is set, so it produces:
- `ApplicationLevelNodeTreeInfo.json` (full app tree)
- `ApplicationScreenshot.jpg` (app screenshot, no highlight)

## CREATE-5: Find the Element

Read the screenshot for visual context:

```
Read "$ELEM_FOLDER/ApplicationScreenshot.jpg"
```

Get a high-level view of the app tree:

```bash
"$CLI" selector-intelligence filter-tree --runtime-data-folder-path "$ELEM_FOLDER" --max-depth 40
```

Read the output file to understand the structure. Search for the target element using keywords from `$ELEMENT`:

```bash
"$CLI" selector-intelligence filter-tree --runtime-data-folder-path "$ELEM_FOLDER" --query "add to cart"
```

Refine with role filters if needed:

```bash
"$CLI" selector-intelligence filter-tree --runtime-data-folder-path "$ELEM_FOLDER" --query "cart" --role "button,link"
```

The tree format shows each element as:
```
  Button "Add to cart" [ref=e42]
```

Cross-reference the screenshot (visual) with the tree results (structural).
Save the ref as `$EREF` (e.g., `e42`).

If ambiguous, list candidates and ask the user.

## CREATE-6: Get Partial Selector

```bash
"$CLI" selector-intelligence get-default-selector --runtime-data-folder-path "$ELEM_FOLDER" --ref $EREF  # append --from-snapshot if $FROM_SNAPSHOT is true
```

Save the stdout output as `$PARTIAL_SELECTOR`.

Update `TargetCapture.json` using the Write tool:

```json
{
    "WindowSelector": "$WINDOW_SELECTOR",
    "PartialSelector": "$PARTIAL_SELECTOR",
    "ActivityType": "$ACTIVITY_TYPE"
}
```

Write or update `$ELEM_FOLDER/TargetDefinition.json`: if the file already exists, read it first and preserve all existing fields. Set `"WindowSelector"` to `$WINDOW_SELECTOR`, `"PartialSelector"` to `$PARTIAL_SELECTOR`, `"ActivityType"` to `$ACTIVITY_TYPE`.

## CREATE-7: Capture Highlighted Screenshot

Now that the partial selector is set, re-capture to get a screenshot with the target element highlighted. The app tree already exists so this only takes the screenshot.

```bash
"$CLI" selector-intelligence capture-runtime-data --runtime-data-folder-path "$ELEM_FOLDER"
```

This overwrites `ApplicationScreenshot.jpg` with a highlighted version. Skips both tree extractions since the files already exist.

## CREATE-8: Improve the Selector

**Skip this step if `$IMPROVE` is `false` (`--no-improve` was set).**

Otherwise, invoke the `/uia-improve-selector` skill with `$ELEM_FOLDER --mode improve` as the argument.

## Output Rules

**If `$QUIET` is `true`: The calling skill will continue with its next step.**

**Do NOT add commentary, analysis, or opinions about the selectors.** Just present the final selectors in the format below. The improve skill handles its own output when used.

**Window-only mode** (no `$ELEMENT`):

```
**Window:**
\`\`\`xml
<window selector>
\`\`\`
```

**Element mode with `--no-improve`:**

```
**Window:**
\`\`\`xml
<window selector>
\`\`\`

**Target:**
\`\`\`xml
<partial selector>
\`\`\`
```
