---
name: uipath-session-logs
description: "[PREVIEW] Opt-in session capture for Claude Code + UiPath skills. Set UIPATH_SESSION_LOG=1 to log tool calls, prompts, and .uis/solution snapshots to ./.uipath-logs/<session-id>/ for bug reproduction. For live issue triage→uipath-diagnostics."
---

# UiPath Session Logs

Capture a structured record of a Claude Code session that invoked UiPath skills so you can trace bugs, reproduce failing flows, and attach evidence to support tickets. Capture is **opt-in** — nothing is written unless you set `UIPATH_SESSION_LOG=1` before starting `claude`.

Logs land at `./.uipath-logs/<session-id>/` relative to the current working directory and contain tool calls, user prompts, a snapshot of any UiPath solution (`.uis`, `solution.json`, `project.json`) that existed at session start, and a summary on exit.

## 1. When to Use This Skill

Trigger this skill when the user asks:

- "Capture logs of this session / of a UiPath skill run"
- "Record what Claude did while building / publishing / debugging the project"
- "Give me a trace I can attach to the bug report"
- "How do I enable UiPath session capture?"
- "Where are the session logs stored?"

Do NOT trigger for live hypothesis-driven debugging of a running automation (Orchestrator jobs, queue items, selector failures) — that is `uipath-diagnostics`.

## 2. Critical Rules

1. **Capture is opt-in.** The hook writes nothing unless `UIPATH_SESSION_LOG=1` is exported before Claude Code starts. Restart the session after setting it.
2. **Logs are per-session**, keyed by the Claude Code session id. Directory: `<cwd>/.uipath-logs/<session-id>/`.
3. **Never commit `.uipath-logs/`.** Add it to `.gitignore` — see `assets/templates/gitignore-template.md`. Captured payloads may contain orchestrator tokens, PATs, tenant URLs, or customer data.
4. **Always scrub secrets before sharing** a capture. See `references/share-guide.md` for the redaction checklist.
5. **The hook never fails the session.** If something goes wrong inside the logger, it emits a `[uipath-session-logger]` line to stderr and exits 0 so your actual work is never blocked.
6. **Oversized payloads are truncated** (single JSON field > 64 KB) to `{"truncated":true,"bytes":N}`. The session transcript Claude Code writes under `~/.claude/projects/` still has the full content if you need it.

## 3. Quick Start

Enable capture, reproduce the issue, then inspect the log.

### Enable

```bash
# bash / zsh
export UIPATH_SESSION_LOG=1
claude

# Windows PowerShell
$env:UIPATH_SESSION_LOG = "1"
claude
```

### Verify the hook fired

Inside Claude Code, after your first tool call:

```bash
ls .uipath-logs/
# -> <session-id>/
ls .uipath-logs/*/
# session.json  prompts.jsonl  tools.jsonl  project-snapshot/   (no summary.json yet)
```

### Inspect a capture

```bash
# last user prompt
tail -1 .uipath-logs/*/prompts.jsonl | jq .

# every Bash command the agent ran
jq 'select(.phase=="pre" and .tool=="Bash") | .input.command' \
   .uipath-logs/*/tools.jsonl

# tool calls that returned an error response
jq 'select(.phase=="post" and (.response|tostring|test("error";"i")))' \
   .uipath-logs/*/tools.jsonl
```

More recipes in `references/analyze-guide.md`.

### Disable

```bash
unset UIPATH_SESSION_LOG        # bash / zsh
Remove-Item Env:UIPATH_SESSION_LOG   # PowerShell
```

## 4. Layout of a Capture

```
.uipath-logs/<session-id>/
├── session.json              # session_id, cwd, start_ts, plugin_version, filtered UIPATH_* env
├── prompts.jsonl             # one line per UserPromptSubmit
├── tools.jsonl               # one line per PreToolUse (phase=pre) and PostToolUse (phase=post)
├── project-snapshot/         # copy of *.uis / solution.json / project.json at SessionStart
└── summary.json              # written on Stop / SessionEnd: counts, duration, error_count
```

## 5. Reference Navigation

| File | Use when |
|------|---------|
| `references/capture-guide.md` | You want details on what each hook writes, env-var gating, and the on-disk schema. |
| `references/analyze-guide.md` | You have a capture and want `jq`/`grep` recipes to answer specific debugging questions. |
| `references/share-guide.md` | You want to attach a capture to a bug report — redaction checklist and packaging steps. |
| `assets/templates/gitignore-template.md` | You need the exact line to add to `.gitignore`. |

## 6. Anti-patterns

- **Do not** assume capture is on. It defaults off. Check `.uipath-logs/` exists after your first tool call.
- **Do not** hand-edit `tools.jsonl` before sharing — instead copy to a new dir and redact there. The originals are useful for local replays.
- **Do not** assume any non-empty value enables capture. Recognized on: `1`, `true`, `yes`, `on` (case-insensitive). Anything else (including unset, empty, `0`, `false`) disables capture. Use `unset UIPATH_SESSION_LOG` to turn it off cleanly.
- **Do not** rely on the capture for live diagnostics of a running UiPath job — use `uipath-diagnostics` for that.
- **Do not** commit the `.uipath-logs/` directory. Logs contain raw tool payloads.
