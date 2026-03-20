---
name: sync
description: Sync UiPath project files between local and remote storage (Studio Web) using push and pull commands. Handles bidirectional sync, conflict resolution, and selective file operations. Use when the user says "push my code", "pull from remote", "sync with Studio Web", or "upload my project".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# File Synchronization

Sync project files between local development and remote Studio Web storage.

## Quick Reference

```bash
# Pull remote files to local
uv run uipath pull

# Push local files to remote (mirrors local state)
uv run uipath push

# Force overwrite without prompts
uv run uipath push --overwrite
uv run uipath pull --overwrite
```

## Documentation

- **[File Sync Guide](references/file-sync.md)** — Complete sync workflow
  - Push and pull commands with all options
  - `UIPATH_PROJECT_ID` setup
  - Conflict resolution strategies
  - Common workflows (clone, collaborate, CI/CD)
  - Troubleshooting

## Prerequisites

- Authentication configured — if not authenticated, use the [Auth skill](/uipath-coded-agents:auth) first
- `UIPATH_PROJECT_ID` set in `.env` or environment — also required by the [Evaluate skill](/uipath-coded-agents:evaluate) when reporting evaluation results to Studio Web (`--report` flag)

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `UIPATH_PROJECT_ID environment variable not found` | Missing project ID in `.env` | Create a Coded Agent project in Studio Web, copy its ID, add `UIPATH_PROJECT_ID=<id>` to `.env` |
| `Your local version is behind the remote version. Aborted!` | Push requires interactive confirmation that CLI cannot provide | Use `uv run uipath push --overwrite` to force push |
| Push deleted unexpected files | Push mirrors local state — removes remote files not present locally | This is by design. Review local files before pushing |
| `Conflict on pull` | Remote and local both changed | Use `uv run uipath pull --overwrite` to force remote, or manually resolve differences |
| `401 Unauthorized` | Auth expired | Re-run `uv run uipath auth --cloud --tenant <TENANT>` |

## Additional Instructions

- Read the [file sync reference](references/file-sync.md) before making assumptions about push/pull behavior.
- Push **deletes** remote files not present locally. It mirrors local state.
