# File Synchronization

Sync project files between your local environment and remote Studio Web storage.

## Quick Reference

```bash
# Pull remote files to local (interactive prompts on conflict)
uip codedagent pull

# Push local files to remote — mirrors local state, deletes remote files missing locally
uip codedagent push

# Force without prompts
uip codedagent push --overwrite
uip codedagent pull --overwrite

# Push without syncing the dependency lock
uip codedagent push --nolock

# Push without syncing resource files
uip codedagent push --ignore-resources
```

> Push **mirrors** local state — remote files not present locally are deleted. Review before pushing.

## Prerequisites

- Authenticated session (see [authentication](../../authentication.md)).
- `UIPATH_PROJECT_ID` set in `.env` (the CLI does not inject this one — it identifies the target project in Studio Web).

```env
UIPATH_PROJECT_ID=12345
```

`UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, and org/tenant identifiers come from the `uip login` session automatically — do not add them to `.env`.

## Pull

Downloads all files from the remote Studio Web project to your local workspace, preserving directory structure.

| Option | Description |
|--------|-------------|
| `--overwrite` | Replace conflicting local files without prompting |

## Push

Uploads local files to remote storage and keeps remote as an exact mirror of local state: updates differing files, adds new ones, and **removes** remote files absent locally.

| Option | Description |
|--------|-------------|
| `--overwrite` | Skip prompts on conflict |
| `--nolock` | Skip `uv lock` and exclude the lock file from sync |
| `--ignore-resources` | Skip importing resources during push |

## Conflict Resolution

Both `push` and `pull` prompt interactively on conflict. In a non-interactive shell (CI, automation, or Claude's Bash tool) use `--overwrite` to resolve in favour of the source side.

## Common Workflows

**Clone a project**

```bash
echo "UIPATH_PROJECT_ID=my-project-123" > .env
uip codedagent pull
```

**Collaborate with a shared project**

```bash
uip codedagent pull --overwrite        # pick up teammates' changes
# edit files
uip codedagent pull --overwrite        # re-sync immediately before pushing
uip codedagent push --overwrite        # publish
```

`push --overwrite` replaces the remote wholesale — changes teammates pushed while you were editing will be lost. Pull again right before push to minimise the race window, or coordinate via the team instead of relying on sync alone.

**CI/CD pipeline**

```bash
#!/bin/bash
set -e
uip codedagent pull --overwrite
# run tests / build
uip codedagent push --overwrite
```

## Files Involved

| File | Included | Purpose |
|------|----------|---------|
| `pyproject.toml`, `main.py`, `.py`, `.json`, `.yaml` | yes | Project source and metadata |
| `uipath.json`, `entry-points.json`, `bindings.json` | yes | UiPath project configuration |
| `uv.lock` | yes (skip with `--nolock`) | Dependency lockfile |
| `__pycache__/`, `.git/`, `.uipath/`, `.env` | no | Build artifacts, VCS, secrets |

Use `packOptions` in `uipath.json` to refine what gets included.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `UIPATH_PROJECT_ID environment variable not found` | Missing project ID in `.env` | Create a Coded Agent project in Studio Web, copy its ID, add `UIPATH_PROJECT_ID=<id>` to `.env` |
| `Your local version is behind the remote version. Aborted!` | Push needs interactive confirmation | Use `uip codedagent push --overwrite` |
| Push deleted unexpected files | Push mirrors local state | Review local state before pushing; use selective `--ignore-resources` to skip resource files |
| `Conflict on pull` | Both sides changed the same files | Use `--overwrite` to take remote, or resolve manually |
| `401 Unauthorized` | Session expired | Re-authenticate via `uip login` (see [authentication](../../authentication.md)) |
