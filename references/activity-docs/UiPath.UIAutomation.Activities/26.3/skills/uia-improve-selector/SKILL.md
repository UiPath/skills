---
name: uia-improve-selector
description: "Fix, improve, or recover a UiPath selector using runtime data. **Use when** (1) a selector stopped working and user has runtime data, (2) user asks to fix/improve/recover a selector, (3) user mentions 'element not found' with a snapshot or runtime data folder, (4) user wants to make an existing selector more robust, (5) a selector needs to be fixed after a failure. **Example phrases** 'fix this selector', 'selector stopped working', 'improve the selector', 'element not found, here\\'s the runtime data', 'make this selector more robust', 'recover this selector', 'element not found'"
argument-hint: "<folder> [--mode <recover|improve>] [--quiet] | --window <selector> [--partial <selector>] [--mode <recover|improve>] [--quiet]"
allowed-tools: Bash, Read, Write, AskUserQuestion
---

Fix or improve a UiPath selector using the UiAutomation CLI and runtime data.

The user provides either a runtime data folder path, or `--window` and `--partial` flags with raw selectors. Supports both full selector (window + partial) and window-only modes — when `TargetCapture.json` has an empty `PartialSelector`, the flow targets only the window selector.

**IMPORTANT: Use forward slashes in ALL paths.** Backslash paths break the Read tool.

## CLI

```
CLI="uip rpa uia"
```

## Input Parsing

Extract from `$ARGUMENTS`:

- `--mode recover` or `--mode improve` → `$MODE`. If not specified, infer from phrasing:
  - **recover** (default): "fix", "broken", "stopped working", "element not found", "recover", "failed"
  - **improve**: "improve", "robust", "optimize", "strengthen", "harden", "resilient"
  - If unclear, default to `recover`.
- `--quiet` → `$QUIET=true` (default: `false`). Suppress all output — just write files. Used when this skill is called as a sub-step by another skill.
- `--window <selector>` → `$WINDOW_SELECTOR` (optional). The window selector XML.
- `--partial <selector>` → `$PARTIAL_SELECTOR` (optional). The partial selector XML.

**If `--window` is provided (with or without `--partial`):** create a fresh working folder, write TargetCapture.json, and capture live runtime data:

Extract a short name from the window selector's `title` or `app` attribute for the folder name:

```bash
NAME_SRC="<title or app from window selector>"
WORK_FOLDER="$(pwd)/.local/.uia/.improve-selector/$(date +%Y%m%d_%H%M%S)_$(echo "$NAME_SRC" | tr ' /:*?"<>|\\' '_' | head -c 40)"
mkdir -p "$WORK_FOLDER"
```

Write `$WORK_FOLDER/TargetCapture.json` using the Write tool:

```json
{
    "WindowSelector": "$WINDOW_SELECTOR",
    "PartialSelector": "$PARTIAL_SELECTOR",
    "ActivityType": "Click"
}
```

(If `--partial` was not provided, `$PARTIAL_SELECTOR` is `""` — this is window-only mode.)

Capture runtime data (tree + screenshot):

```bash
"$CLI" snapshot capture --folder-path "$WORK_FOLDER"
```

Set `$WORK_FOLDER` to the created path and continue to IMPROVE-1.

**Otherwise:** extract `$WORK_FOLDER` from `$ARGUMENTS` by stripping flags. If `$WORK_FOLDER` is not provided, ask for it.

## IMPROVE-1: Get Instructions

Run the CLI to get tagged instructions. The output contains `<system_prompt>`, `<user_message>`, and `<schema_config>` tags.

```bash
"$CLI" selector-intelligence get-instructions --folder-path "$WORK_FOLDER" --mode $MODE > "$WORK_FOLDER/selector-instructions.md" 2>&1
```

The DOM JSON can be a single very long line that exceeds the Read tool's context limit. Fold it so each line stays under ~8000 tokens:

```bash
fold -s -w 30000 "$WORK_FOLDER/selector-instructions.md" > "$WORK_FOLDER/selector-instructions-wrapped.md" && mv "$WORK_FOLDER/selector-instructions-wrapped.md" "$WORK_FOLDER/selector-instructions.md"
```

## IMPROVE-2: Read Instructions and Generate Selectors

**Use ONLY the Read tool and Write tool for this step. Do NOT use Bash, Python, or any other tool to parse, process, or extract content from the instructions file.**

1. Read `$WORK_FOLDER/selector-instructions.md` using the Read tool. The file can be large (the DOM JSON is a single long line), so read in chunks using `offset` and `limit` as needed. Parse the `<system_prompt>`, `<user_message>`, and `<schema_config>` sections.
2. Read `$WORK_FOLDER/ApplicationScreenshot.jpg` for visual context (skip if it doesn't exist).
3. Execute the task from `<user_message>` following the rules from `<system_prompt>`. Write the JSON result (conforming to `<schema_config>`) to `$WORK_FOLDER/selector-output-claude.json` using the Write tool.

## IMPROVE-3: Validate and Retry Loop

This step runs a validate→fix loop. **Max 3 iterations total.**

Set `$ATTEMPT = 1`.

### Validate

```bash
"$CLI" selector-intelligence validate --folder-path "$WORK_FOLDER" --improve-selector-response-file-path "$WORK_FOLDER/selector-output-claude.json" --mode $MODE > "$WORK_FOLDER/validation-result.txt" 2>&1
```

Read `$WORK_FOLDER/validation-result.txt`.

### At least one valid → done

Pick the selector with the highest FinalScore. Read the top-level `reasoning` field from `$WORK_FOLDER/selector-output-claude.json` to extract the root cause and strategy.

Write or update `$WORK_FOLDER/TargetDefinition.json`: if the file already exists, read it first and preserve all existing fields. Set `"WindowSelector"` to the winning candidate's WindowSelector. If the winning candidate has an EditablePartialSelector, also set `"PartialSelector"` to it.

Jump to **Output**.

### None valid → fix and retry

If `$ATTEMPT >= 3`: save the last validation result and jump to **Output** with the errors.

Otherwise:

1. Read `$WORK_FOLDER/validation-result.txt` carefully — focus on the `ToolingFeedback` for each candidate to understand what went wrong (schema violations, invalid attributes, missing required fields, etc.).
2. Re-read `$WORK_FOLDER/selector-output-claude.json` to see what you generated.
3. Fix the generation based on the feedback: adjust the selectors to address the specific issues flagged. Write the corrected result to `$WORK_FOLDER/selector-output-claude.json` (overwrite).
4. Increment `$ATTEMPT` and go back to **Validate**.

## Output

**If `$QUIET` is `true`:** stop here. The calling skill will continue with its next step.

**If no valid selectors after 3 attempts:** present the last validation errors and stop.

**Otherwise:** read `$WORK_FOLDER/TargetCapture.json` to get the original selectors (`WindowSelector` and `PartialSelector`). Present using this template (fixed selector LAST so it's visible in terminal):

````
---
### Selector <Fixed|Improved>  (Score: <FinalScore>/1.0)

> **Root cause:** <one sentence — why the original selector broke>  ← recover mode only

> **Strategy:** <one sentence — what makes the selector more robust>

> <If there's a score penalty, add one line explaining it's a structural UI property, not fixable by selector changes.>

**Original:**
```
<WindowSelector from TargetCapture.json>
<each tag on its own line from PartialSelector in TargetCapture.json>  ← omit if empty
```

**Window:**
```xml
<WindowSelector from validation result>
```

**Target:**  ← omit entire block if no EditablePartialSelector
```xml
<each tag on its own line from EditablePartialSelector>
```
---
````

- If the window selector didn't change from the original, omit it from both **Original:** and **Window:** sections.
- Keep it tight — no full analysis dump. The detailed candidate analysis is already saved in the output files if needed.
- Do NOT show all 3 selectors. Do NOT retry for score penalties — they're often structural properties of the UI that can't be fixed by adding tags.
