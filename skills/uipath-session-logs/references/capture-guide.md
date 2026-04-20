# Capture Guide

Details of what the UiPath session logger captures, when it fires, and the on-disk schema.

## Enablement

Capture runs inside Claude Code plugin hooks. It is active only when the `UIPATH_SESSION_LOG` environment variable is set to one of: `1`, `true`, `yes`, `on` (case-insensitive). Any other value — including unset, empty, `0`, `false` — leaves the hooks as no-ops.

The environment variable is read inside each hook invocation. Toggling it mid-session **does not** retroactively capture earlier events, and does **not** affect an already-running session's already-captured events.

## Hook events

All events come from Claude Code plugin hooks declared in `hooks/hooks.json`. Each event invokes `hooks/uipath-session-logger.sh <EVENT>` and receives the event JSON on stdin.

| Event | Fires on | Output |
|-------|----------|--------|
| `SessionStart` | Claude Code session start | Creates `.uipath-logs/<session-id>/`, writes `session.json`, copies `*.uis` / `solution.json` / `project.json` from `cwd` into `project-snapshot/` |
| `UserPromptSubmit` | Every user prompt | Appends to `prompts.jsonl` |
| `PreToolUse` | Before every tool call | Appends `{phase:"pre", ...}` to `tools.jsonl` |
| `PostToolUse` | After every tool call | Appends `{phase:"post", ...}` to `tools.jsonl` |
| `Stop` | Claude turn stop | Computes and writes `summary.json` |
| `SessionEnd` | Session exit | Finalizes `summary.json` |

The logger never returns non-zero — if anything fails inside, a `[uipath-session-logger]` diagnostic is sent to stderr and the script exits 0 so it cannot block the user's session.

## Directory layout

```
<cwd>/.uipath-logs/<session-id>/
├── session.json
├── prompts.jsonl
├── tools.jsonl
├── project-snapshot/
│   ├── *.uis
│   ├── solution.json
│   └── project.json
└── summary.json            # only present after Stop / SessionEnd
```

`<session-id>` is Claude Code's own session id, taken from the hook's stdin payload (`.session_id`). Using Claude's session id means resumed sessions (`claude --resume`) continue appending to the same folder.

## Schemas

### `session.json`

```json
{
  "session_id": "01HZ...",
  "cwd": "/abs/path/to/project",
  "hook_event_name": "SessionStart",
  "start_ts": "2026-04-20T07:33:11Z",
  "plugin_version": "0.0.18",
  "env": {
    "UIPATH_SESSION_LOG": "1",
    "UIPATH_URL": "https://cloud.uipath.com/...",
    "UIPATH_TENANT_ID": "<redacted-by-caller>"
  }
}
```

Only environment variables whose name begins with `UIPATH_` are captured. Values are written verbatim — scrub before sharing.

### `prompts.jsonl`

One JSON object per line:

```json
{"ts":"2026-04-20T07:33:42Z","session_id":"01HZ...","prompt":"Publish the InvoiceProcessor package"}
```

### `tools.jsonl`

One JSON object per line, interleaved `pre` and `post` entries:

```json
{"ts":"...","session_id":"...","phase":"pre","tool":"Bash","input":{"command":"uip pack --output json"}}
{"ts":"...","session_id":"...","phase":"post","tool":"Bash","response":{"exit_code":0,"stdout":"..."},"duration_ms":812}
```

Pairing pre/post: match by position (the nth `pre` in the file is the nth `post`). Claude Code does not expose a tool-call id in hook payloads, so positional pairing is the contract.

### `summary.json`

Written on `Stop` (and overwritten on `SessionEnd` with the final values):

```json
{
  "session_id": "01HZ...",
  "start_ts": "2026-04-20T07:33:11Z",
  "end_ts": "2026-04-20T07:49:02Z",
  "duration_ms": 951000,
  "prompt_count": 4,
  "tool_counts": {"Bash": 18, "Read": 7, "Edit": 3},
  "error_count": 2,
  "total_bytes": 41822
}
```

`error_count` counts `post` entries whose response contains an `error`, `is_error:true`, or non-zero `exit_code`.

## Truncation

To keep logs reasonable, the hook truncates any single JSON string field larger than 64 KB. The truncated field is replaced with:

```json
{"truncated": true, "bytes": 1048576}
```

The full content is still available in Claude Code's own transcript under `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`.

## Dependencies

The hook uses `jq`. If `jq` is not on `PATH`, the logger emits a single warning line to stderr and becomes a no-op for the rest of the session. Install instructions:

```bash
# Debian / Ubuntu
sudo apt-get install -y jq
# macOS
brew install jq
# Windows (Git Bash)
winget install jqlang.jq
```
