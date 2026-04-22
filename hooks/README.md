# Plugin Hooks

Shell scripts invoked by Claude Code at plugin lifecycle events. Wired up in [`hooks.json`](./hooks.json).

| Script | Event(s) | Purpose |
|--------|----------|---------|
| [`ensure-uip.sh`](./ensure-uip.sh) | `SessionStart` (once) | Installs/updates `@uipath/cli`, `@uipath/servo`, and `@uipath/rpa-tool` |
| [`uipath-session-logger.sh`](./uipath-session-logger.sh) | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd` | Opt-in session capture for debugging |
| [`validate-skill-descriptions.sh`](./validate-skill-descriptions.sh) | Git pre-commit | Enforces the 250-character limit on skill `description` frontmatter |

## Session Logger — Enable / Disable

The logger is **off by default**. Turn it on by exporting `UIPATH_SESSION_LOG` before starting Claude Code:

```bash
# bash / zsh
export UIPATH_SESSION_LOG=1
claude

# PowerShell
$env:UIPATH_SESSION_LOG = "1"
claude
```

Values that enable capture (case-insensitive): `1`, `true`, `yes`, `on`. Anything else — including unset, empty, `0`, `false` — disables it.

Disable:

```bash
unset UIPATH_SESSION_LOG   # bash / zsh
Remove-Item Env:UIPATH_SESSION_LOG   # PowerShell
```

Toggling mid-session only affects future hook invocations — already-captured events stay on disk.

## Session Logger — What Gets Captured

Logs land at `<cwd>/.uipath-logs/<session-id>/`, keyed by Claude Code's own session id (so `claude --resume` appends to the same folder).

```
.uipath-logs/<session-id>/
├── session.json              # session_id, cwd, start_ts, UIPATH_* env
├── prompts.jsonl             # one line per UserPromptSubmit
├── tools.jsonl               # pre/post entries per tool call
├── project-snapshot/         # *.uis / solution.json / project.json at SessionStart
└── summary.json              # written on Stop / SessionEnd
```

Single JSON string fields larger than 64 KiB are replaced with `{"truncated": true, "bytes": N}`. The full payload is still available in Claude Code's own transcript at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`.

## Session Logger — Quick Recipes

```bash
# Latest capture
LATEST=$(ls -1dt .uipath-logs/*/ | head -1)

# Every Bash command the agent ran
jq -r 'select(.phase=="pre" and .tool=="Bash") | .input.command' \
   "$LATEST/tools.jsonl"

# Tool calls that returned an error
jq 'select(.phase=="post")
    | select((.response | tostring | test("\"is_error\"\\s*:\\s*true"))
          or ((.response.exit_code? // 0) != 0))' \
   "$LATEST/tools.jsonl"

# Summary
jq . "$LATEST/summary.json"
```

## .gitignore

Never commit `.uipath-logs/`. Captured payloads may contain orchestrator tokens, PATs, tenant URLs, or customer data. Add to your project's `.gitignore`:

```gitignore
# UiPath session capture
.uipath-logs/
```

## Dependencies

`uipath-session-logger.sh` requires `jq`. If `jq` is not on `PATH`, the logger emits a single warning to stderr and becomes a no-op for the rest of the session.

```bash
# Debian / Ubuntu
sudo apt-get install -y jq
# macOS
brew install jq
# Windows (Git Bash)
winget install jqlang.jq
```

## Contract

All hook scripts in this directory MUST:

1. Work on Windows (Git Bash / MSYS), macOS, and Linux.
2. Never block the user's session for more than the `timeout` declared in `hooks.json`.
3. Exit 0 for non-fatal failures. Only exit non-zero when the session genuinely cannot continue (e.g., required tooling missing for `ensure-uip.sh`).
4. Be idempotent — safe to invoke multiple times.
