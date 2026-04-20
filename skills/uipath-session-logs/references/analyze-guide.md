# Analyze Guide

`jq` and shell recipes for extracting answers from a capture.

All examples assume you are in the project root and `.uipath-logs/<session-id>/` exists. Replace `<session-id>` or use `*/` when you have a single capture.

## Pick the most recent capture

```bash
LATEST=$(ls -1dt .uipath-logs/*/ | head -1)
echo "$LATEST"
```

## Overview

```bash
jq . "$LATEST/session.json"
jq . "$LATEST/summary.json"        # only after the session has stopped
```

## Every Bash command the agent ran

```bash
jq -r 'select(.phase=="pre" and .tool=="Bash") | .input.command' \
   "$LATEST/tools.jsonl"
```

## Every `uip` CLI invocation

```bash
jq -r 'select(.phase=="pre" and .tool=="Bash")
       | .input.command
       | select(test("^(uip|npx\\s+uip)\\b"))' \
   "$LATEST/tools.jsonl"
```

## Tool calls that returned an error

```bash
jq 'select(.phase=="post")
    | select((.response | tostring | test("\"is_error\"\\s*:\\s*true"))
          or (.response.exit_code? // 0) != 0)' \
   "$LATEST/tools.jsonl"
```

## Files Claude wrote or edited

```bash
jq -r 'select(.phase=="pre" and (.tool=="Write" or .tool=="Edit" or .tool=="NotebookEdit"))
       | "\(.tool)\t\(.input.file_path)"' \
   "$LATEST/tools.jsonl"
```

## Timeline of tool calls (1 line each)

```bash
jq -r 'select(.phase=="pre")
       | "\(.ts)  \(.tool)  \(.input | tostring | .[0:120])"' \
   "$LATEST/tools.jsonl"
```

## Slowest 10 tool calls

```bash
jq -r 'select(.phase=="post")
       | "\(.duration_ms // 0)\t\(.tool)"' \
   "$LATEST/tools.jsonl" \
 | sort -rn | head -10
```

## Replay the prompts in order

```bash
jq -r '.prompt' "$LATEST/prompts.jsonl"
```

## Diff two captures (e.g. passing vs failing run)

```bash
diff \
  <(jq -r 'select(.phase=="pre") | "\(.tool): \(.input|tostring)"' .uipath-logs/PASS/tools.jsonl) \
  <(jq -r 'select(.phase=="pre") | "\(.tool): \(.input|tostring)"' .uipath-logs/FAIL/tools.jsonl)
```

## Find truncated payloads

```bash
jq 'select(.. | objects | select(.truncated? == true))' \
   "$LATEST/tools.jsonl"
```

If you need the full content of a truncated payload, open Claude Code's own transcript:

```bash
ls ~/.claude/projects/
# find the entry matching your cwd, then jq through <session-id>.jsonl
```

## Archive a capture

```bash
tar -czf "capture-$(basename "$LATEST").tgz" -C .uipath-logs "$(basename "$LATEST")"
```

Review `references/share-guide.md` before sending the archive anywhere.
