---
name: uia-improve-selector
description: "Fix, improve, or recover a UiPath selector using runtime data. **Use when** (1) a selector stopped working and user has runtime data, (2) user asks to fix/improve/recover a selector, (3) user mentions 'element not found' with a snapshot or runtime data folder, (4) user wants to make an existing selector more robust, (5) a selector needs to be fixed after a failure. **Example phrases** 'fix this selector', 'selector stopped working', 'improve the selector', 'element not found, here\\'s the runtime data', 'make this selector more robust', 'recover this selector', 'element not found'"
argument-hint: "<folder> [--mode <recover|improve>] [--quiet] | --window <selector> [--partial <selector>] [--mode <recover|improve>] [--quiet]"
allowed-tools: Bash, Read, Write, Agent, AskUserQuestion
---

Fix or improve a UiPath selector using the UiAutomation CLI and runtime data.

The user provides either a runtime data folder path, or `--window` and `--partial` flags with raw selectors. Supports both full selector (window + partial) and window-only modes — when `TargetCapture.json` has an empty `PartialSelector`, the flow targets only the window selector.

**IMPORTANT: Use forward slashes in ALL paths** (including paths passed to subagents). Backslash paths break the subagent's Read tool.

## CLI

```
CLI="uip rpa uia"
```

**IMPORTANT: The CLI resolves relative paths against its own install directory, not the shell's cwd. Always convert folder paths to absolute before passing them to the CLI** (e.g., `"$(pwd)/.local/.uia/.improve-selector/..."`).

## Input Parsing

Extract from `$ARGUMENTS`:

- `--mode recover` or `--mode improve` → `$MODE`. If not specified, infer from phrasing:
  - **recover** (default): "fix", "broken", "stopped working", "element not found", "recover", "failed"
  - **improve**: "improve", "robust", "optimize", "strengthen", "harden", "resilient"
  - If unclear, default to `recover`.
- `--quiet` → `$QUIET=true` (default: `false`). Suppress all output — just write files and complete. Used when this skill is called as a sub-step by another skill.
- `--window <selector>` → `$WINDOW_SELECTOR` (optional). The window selector XML.
- `--partial <selector>` → `$PARTIAL_SELECTOR` (optional). The partial selector XML.

**If `--window` is provided (with or without `--partial`):** create a fresh working folder, write TargetCapture.json, and capture live runtime data:

Extract a short name from the window selector's `title` or `app` attribute for the folder name:

```bash
NAME_SRC="<title or app from window selector>"
WORK_FOLDER=".local/.uia/.improve-selector/$(date +%Y%m%d_%H%M%S)_$(echo "$NAME_SRC" | tr ' /:*?"<>|\\' '_' | head -c 40)"
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
"$CLI" selector-intelligence capture-runtime-data --runtime-data-folder-path "$WORK_FOLDER"
```

Set `$WORK_FOLDER` to the created path and continue to IMPROVE-1.

**Otherwise:** extract `$WORK_FOLDER` from `$ARGUMENTS` by stripping flags. If `$WORK_FOLDER` is not provided, ask for it.

## IMPROVE-1: Get Instructions

Run the CLI to get tagged instructions. The output contains `<system_prompt>`, `<user_message>`, and `<schema_config>` tags. 

```bash
"$CLI" selector-intelligence get-instructions --runtime-data-folder-path "$WORK_FOLDER" --mode $MODE > "$WORK_FOLDER/selector-instructions.md" 2>&1
```

Do NOT read this file yourself — the subagent will read it directly.

Wrap long lines so no single line exceeds the Read tool's token limit:

```bash
fold -s -w 500 "$WORK_FOLDER/selector-instructions.md" > "$WORK_FOLDER/selector-instructions-wrapped.md" && mv "$WORK_FOLDER/selector-instructions-wrapped.md" "$WORK_FOLDER/selector-instructions.md"
```

## IMPROVE-2: Generate Selectors via Subagent

Delete the output file first so the subagent's Write tool doesn't require a prior Read:

```bash
rm -f "$WORK_FOLDER/selector-output-claude.json"
```

Spawn a general-purpose subagent (model: opus). Use this prompt (replace `$WORK_FOLDER` with the actual forward-slash path):

---
TOOLS: You may ONLY use the Read tool and the Write tool. Do NOT use Bash, Python, or any other tool. Read files with Read. Write files with Write. Nothing else.

Read these files using the Read tool:

1. `$WORK_FOLDER/selector-instructions.md` — contains `<system_prompt>` (selector optimization rules — follow strictly), `<user_message>` (your task with all input data), and `<schema_config>` (JSON schema for your output). This file is large — you MUST read it in chunks of **150 lines** at a time (e.g., `offset=1, limit=150`, then `offset=151, limit=150`, etc.). Do NOT try to read more than 150 lines per call.
2. `$WORK_FOLDER/ApplicationScreenshot.jpg` — visual context of the application (optional — read it if it exists, skip if not)

Execute the task from `<user_message>` following the rules from `<system_prompt>`. Write the JSON result (conforming to `<schema_config>`) to `$WORK_FOLDER/selector-output-claude.json` using the Write tool.

STOP IMMEDIATELY after writing the JSON file. Do not read it back, do not validate, do not summarize. Just write and stop.

ONLY read the files listed above. No other files.

---

After the subagent completes, verify `$WORK_FOLDER/selector-output-claude.json` exists. If it doesn't, re-spawn the subagent (max 2 retries, so 3 total attempts). If it still fails, stop and tell the user.

## IMPROVE-3: Validate

```bash
"$CLI" selector-intelligence validate --runtime-data-folder-path "$WORK_FOLDER" --improve-selector-response-file-path "$WORK_FOLDER/selector-output-claude.json" --mode $MODE > "$WORK_FOLDER/validation-result.txt" 2>&1
```

**At least one valid:** Read `$WORK_FOLDER/validation-result.txt` to check results (ignore any warning lines before the JSON). Pick the selector with the highest FinalScore. Then read the top-level `reasoning` field from `$WORK_FOLDER/selector-output-claude.json` to extract the root cause and strategy.

Write or update `$WORK_FOLDER/TargetDefinition.json`: if the file already exists, read it first and preserve all existing fields. Set `"WindowSelector"` to the winning candidate's WindowSelector. If the winning candidate has an EditablePartialSelector, also set `"PartialSelector"` to it.

**If `$QUIET` is `true`: The calling skill will continue with its next step, you are not done.**

Read `$WORK_FOLDER/TargetCapture.json` to get the original selectors (`WindowSelector` and `PartialSelector`). Present using this template (fixed selector LAST so it's visible in terminal):

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

**None valid:** Read the error feedback, re-spawn the subagent, validate again. **Max 3 attempts.** After 3 failures, save the last validation result and present what you have with the errors.
