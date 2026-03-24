---
name: uia-create-cv
description: "Determine CV (Computer Vision) targeting properties for a UiPath target element. Use when asked to \"create CV target\", \"add CV targeting\", \"get CV properties\", or when configuring a target that needs Computer Vision as a secondary targeting method. Takes an element description and/or selector plus a runtime data folder with a screenshot."
argument-hint: "<element description> [--folder <path>] [--quiet]"
allowed-tools: Bash, Read, Write, AskUserQuestion
---

Determine the CV (Computer Vision) properties — `CvType` and `CvText` — for a UiPath target element by analyzing the application screenshot and element context.

`$ARGUMENTS` format: `<element description> [--folder <path>]`

**IMPORTANT: Use forward slashes in ALL paths.**

**IMPORTANT: Follow the steps mechanically. Do NOT add commentary or analysis between steps.**

## CLI

```
CLI="uip rpa uia"
```

**IMPORTANT: The CLI resolves relative paths against its own install directory, not the shell's cwd. Always convert folder paths to absolute before passing them to the CLI** (e.g., `"$(pwd)/.local/.uia/..."`).

## Input Parsing

Extract from `$ARGUMENTS`:

- `$ELEMENT_DESC` (required) — natural-language description of the target element (e.g., `"Submit button"`, `"search input field"`, `"Accept terms checkbox"`).
- `--folder <path>` → `$ELEM_FOLDER` (optional). Path to a runtime data folder containing `ApplicationScreenshot.jpg` and optionally tree data. If not provided, ask the user.
- `--quiet` → `$QUIET=true` (default: `false`). Suppress all output — just write files and complete. Used when this skill is called as a sub-step by another skill.

If `$ELEMENT_DESC` is not provided, ask the user to describe the element.

If `$ELEM_FOLDER/TargetDefinition.json` exists and contains a `PartialSelector` field, read it and save as `$SELECTOR`. Otherwise `$SELECTOR` is empty.

## CV-1: Analyze the Screenshot

Read `$ELEM_FOLDER/ApplicationScreenshot.jpg` for visual context.

Visually identify the element matching `$ELEMENT_DESC`. Note:
- Its visual appearance (shape, style, color)
- Any text on or next to the element
- The UI control type it resembles (button, text field, checkbox, etc.)

If `$SELECTOR` is provided, use attributes from it (aaname, name, id, tag, role) to help locate the element in the screenshot.

## CV-2: Determine CvType

Map the element's visual appearance to a `UIVisionCategoryType` value:

| Visual appearance | CvType |
|---|---|
| Clickable button with text/icon | `Button` |
| Text input field, search box, textarea | `InputBox` |
| Checkbox (square toggle) | `CheckBox` |
| Radio button (circular toggle) | `RadioButton` |
| Window close button (X) | `CloseButton` |
| Window maximize button | `MaximizeButton` |
| Window minimize button | `MinimizeButton` |
| Small icon/glyph without text | `Icon` |
| Arrow/chevron/expand button | `ArrowButton` |
| Table/grid cell | `Cell` |
| Static text label | `Text` |
| Image/picture/logo | `Image` |
| Generic region/container | `Area` |
| Any text (OCR-based) | `AnyText` |
| Group of words | `AnyWordGroup` |
| Any icon (generic icon match) | `AnyIcon` |
| Data table/grid | `Table` |
| Specific table cell | `TableCell` |

If the element could match multiple types, prefer the most specific one (e.g., `Button` over `Area`).

## CV-3: Determine CvText

Identify the visible text that CV should use to locate the element:

- **Buttons**: use the button label text (e.g., `"Submit"`, `"Add to cart"`)
- **Input fields**: use the placeholder text or adjacent label (e.g., `"Search..."`, `"Email address"`)
- **Checkboxes/radios**: use the label text next to the control (e.g., `"I agree to terms"`)
- **Text elements**: use the text content itself
- **Icons without text**: leave `$CV_TEXT` empty — CV will match by visual type only

If the selector has an `aaname` or `name` attribute, that's often the same text CV should use.

If the tree data exists, optionally check it:

```bash
"$CLI" selector-intelligence filter-tree "$ELEM_FOLDER" --query "$ELEMENT_DESC" --max-depth 5
```

Read the output to confirm the element's text/name.

## CV-4: Write TargetDefinition.json and Present Results

Write or update `$ELEM_FOLDER/TargetDefinition.json`: if the file already exists, read it first and preserve all existing fields. Set `"CvType"` to `$CV_TYPE` and `"CvText"` to `$CV_TEXT`. If a `"SearchSteps"` array exists and doesn't already contain `"CV"`, append `"CV"` to it.

**If `$QUIET` is `true`: do not present results below. The files have been written — the caller will read them directly.**

Present the CV properties:

```
**CV Properties:**
- CvType: $CV_TYPE
- CvText: "$CV_TEXT"
```

No additional commentary.
