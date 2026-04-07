# File Synchronization

> **Agent type: Both coded and low-code agents.** The same `uip codedagent push` / `pull` commands work for both. For coded agents the primary files synced are `main.py`, `pyproject.toml`, `uv.lock`, and config JSONs. For low-code agents the primary file is `agent.json` (no `pyproject.toml` or `uv.lock`).

Sync project files between local development and remote Studio Web storage.

## Quick Reference

```bash
# Pull remote files to local
uip codedagent pull

# Push local files to remote (mirrors local state)
uip codedagent push

# Force overwrite without prompts
uip codedagent push --overwrite
uip codedagent pull --overwrite
```

## Documentation

- **[Authentication](authentication.md)** — Required before push or pull
- **[Deployment](deployment.md)** — Deploy after syncing
- **[Running Agents](running-agents.md)** — Test locally before pushing changes

## Prerequisites

- Authentication configured — if not authenticated, use the [authentication reference](authentication.md) first
- `UIPATH_PROJECT_ID` set in `.env` or environment — also required by the [evaluate reference](evaluate.md) when reporting evaluation results to Studio Web (`--report` flag)

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `UIPATH_PROJECT_ID environment variable not found` | Missing project ID in `.env` | Create a Coded Agent project in Studio Web, copy its ID, add `UIPATH_PROJECT_ID=<id>` to `.env` |
| `Your local version is behind the remote version. Aborted!` | Push requires interactive confirmation that CLI cannot provide | Use `uip codedagent push --overwrite` to force push |
| Push deleted unexpected files | Push mirrors local state — removes remote files not present locally | This is by design. Review local files before pushing |
| `Conflict on pull` | Remote and local both changed | Use `uip codedagent pull --overwrite` to force remote, or manually resolve differences |
| `401 Unauthorized` | Auth expired | Re-run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` |

## Additional Instructions

- Read the [file sync reference](file-sync.md) before making assumptions about push/pull behavior.
- Push **deletes** remote files not present locally. It mirrors local state.

---

# File Synchronization

Sync UiPath project files between your local development environment and remote storage (Studio Web).

## Synchronization Workflow

```
Setup Project ID → Pull Remote Files → Make Local Changes → Push Local Files
                      (optional)                           to Remote
```

## Prerequisites

Before syncing files, ensure:

1. **UiPath Account**: Active UiPath Cloud or on-premise account
2. **Authentication**: Configured credentials via `uip login`
3. **Project ID**: Identify your project's ID in Studio Web
4. **Python Environment**: Python 3.11+ with `uv` package manager

## Environment Setup

### Set Project ID

The `UIPATH_PROJECT_ID` is required for both push and pull operations. Create a `.env` file in your project directory:

```env
UIPATH_PROJECT_ID=12345
```

Alternatively, set it as an environment variable:

```bash
export UIPATH_PROJECT_ID=12345
```

Or inline for a single command:

```bash
UIPATH_PROJECT_ID=12345 uip codedagent push
```

### Authentication

Run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` to configure your credentials. This sets up:
- `UIPATH_URL` - Your UiPath instance URL
- `UIPATH_ACCESS_TOKEN` - Bearer token for API access
- `UIPATH_TENANT_NAME` - Your tenant identifier

---

## Pull Command

Download remote project files to your local environment.

```bash
uip codedagent pull
```

### What It Does

1. Fetches all files from the remote project (Studio Web)
2. Downloads them to your local workspace
3. Preserves directory structure and file organization
4. Overwrites local files if `--overwrite` flag is used

### Options

| Option | Description |
|--------|-------------|
| `--overwrite` | Automatically replace conflicting local files without confirmation |

### Examples

**Pull remote files (with confirmation on conflicts):**
```bash
uip codedagent pull
```

**Pull and automatically overwrite local changes:**
```bash
uip codedagent pull --overwrite
```

### Use Cases

- **Clone existing project**: Get a fresh copy of a remote project locally
- **Sync team changes**: Pull updates made by team members
- **Restore files**: Recover local files from remote backup
- **Start collaboration**: Begin working on a shared project

---

## Push Command

Upload local project files to remote storage, keeping remote in sync with local state.

```bash
uip codedagent push
```

### What It Does

1. **Updates** - Overwrites remote files with your local versions if they differ
2. **Uploads** - Adds new local files to remote storage
3. **Deletes** - Removes remote files that no longer exist locally
4. Ensures remote is an exact mirror of your local project

### Options

| Option | Description |
|--------|-------------|
| `--overwrite` | Skip confirmation prompts when overwriting remote files |
| `--nolock` | Skip `uv lock` and don't include lock file in sync |
| `--ignore-resources` | Skip importing resources during push |

### Examples

**Push with confirmation prompts:**
```bash
uip codedagent push
```

**Push and skip confirmation (batch/automation):**
```bash
uip codedagent push --overwrite
```

**Push without updating dependencies lock:**
```bash
uip codedagent push --nolock
```

> **Low-code agents:** The `--nolock` flag is not relevant (no `uv.lock` file).

**Push without syncing resources:**
```bash
uip codedagent push --ignore-resources
```

### Use Cases

- **Save work**: Persist your local changes to remote storage
- **Publish updates**: Share changes with team members
- **Backup**: Create a remote backup of your project
- **CI/CD**: Automate project sync in deployment pipelines

---

## Conflict Resolution

### Pull with Conflicts

If local files differ from remote, you have two options:

**Option 1: Review and confirm each conflict**
```bash
uip codedagent pull
# Interactive prompts will ask about each conflicting file
```

**Option 2: Auto-overwrite local files with remote**
```bash
uip codedagent pull --overwrite
```

### Push with Conflicts

If remote files differ from local, you have two options:

**Option 1: Review and confirm each change**
```bash
uip codedagent push
# Interactive prompts will ask about each file to overwrite
```

**Option 2: Force push local state (overwrite all remote files)**
```bash
uip codedagent push --overwrite
```

---

## Common Workflows

### Workflow 1: Clone and Work on a Project

Create `.env` file:
```env
UIPATH_PROJECT_ID=my-project-123
```

Then work with your project:
```bash
# Pull all remote files to local
uip codedagent pull

# Make changes locally
# ... edit your files ...

# Push changes back to remote
uip codedagent push
```

### Workflow 2: Collaborative Development

Create `.env` file in your project:
```env
UIPATH_PROJECT_ID=shared-project
```

**Developer A:**
```bash
uip codedagent pull          # Get latest from team
# ... make changes ...
uip codedagent push --overwrite  # Push back
```

**Developer B:**
```bash
uip codedagent pull --overwrite  # Get latest from Developer A
# ... make their own changes ...
uip codedagent push --overwrite
```

### Workflow 3: Automated Sync in CI/CD

Create `.env` file or set variables in CI/CD:
```env
UIPATH_PROJECT_ID=$PROJECT_ID
```

Script:
```bash
#!/bin/bash
set -e

# Sync files
uip codedagent pull --overwrite
# ... run tests or build ...
uip codedagent push --overwrite
```

### Workflow 4: Selective Sync (Skip Resources)

Create `.env` file:
```env
UIPATH_PROJECT_ID=my-project
```

Then selectively sync:
```bash
# Push code without syncing resource files
uip codedagent push --ignore-resources

# Later, sync resources separately
uip codedagent push
```

---

## Configuration Files

### Files Involved in Sync

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies |
| `uipath.json` | UiPath project configuration |
| `entry-points.json` | Entry point definitions |
| `main.py` | Main agent/project code |
| `uv.lock` | Dependency lock file (can skip with `--nolock`) |
| `.py`, `.json`, `.yaml` files | Project source files |

> **Low-code agents:** The primary file synced is `agent.json`. No `pyproject.toml`, `main.py`, or `uv.lock` files are involved.

### Files Excluded from Sync

- `__pycache__/` - Python cache
- `.git/` - Git repository
- `.env` - Environment variables (don't sync secrets!)
- `.uipath/` - Build artifacts
- Other files based on `packOptions` in `uipath.json`

> **After pulling on a new machine:** `.env` is excluded from sync for security. After pulling, manually recreate `.env` with `UIPATH_PROJECT_ID=<id>` and re-run `uip login --format json` + `uip login tenant set "<TENANT>" --format json` to restore credentials.

---

## Environment Variables

| Variable | Required | Description | How to Set |
|----------|----------|-------------|-----------|
| `UIPATH_PROJECT_ID` | Yes | ID of the project to sync | Add to `.env` file |
| `UIPATH_URL` | Yes | Base URL of your UiPath instance | Set by `uip login` |
| `UIPATH_ACCESS_TOKEN` | Yes | Bearer token for authentication | Set by `uip login` |
| `UIPATH_TENANT_NAME` | Optional | Your tenant identifier | Set by `uip login` |

See [Environment Setup](#environment-setup) above for how to set these.

---

## Best Practices

1. **Always Pull Before Push**
   - Pull latest remote changes before pushing local changes
   - Reduces conflicts and maintains consistency

2. **Use --overwrite Carefully**
   - In automated workflows (CI/CD), use `--overwrite`
   - In manual workflows, review conflicts first

3. **Don't Sync Secrets**
   - Never include `.env` or credential files in sync
   - Use environment variables or secure vaults instead

4. **Test Before Pushing**
   - Test your local changes with `uip codedagent run`
   - Verify everything works before pushing to remote

5. **Use Version Control Locally**
   - Commit your changes to git before major syncs
   - Allows recovery if something goes wrong

6. **Document Your Project**
   - Include README and comments in your project
   - Helps team members understand the structure

---

## Troubleshooting

### "UIPATH_PROJECT_ID not set"

**Error:** Command fails with "UIPATH_PROJECT_ID environment variable required"

**Solution:** Add to your `.env` file:
```env
UIPATH_PROJECT_ID=your-project-id
```

Or set it as an environment variable:
```bash
export UIPATH_PROJECT_ID=your-project-id
uip codedagent push
```

### "Authentication failed"

**Error:** Command fails with "Unauthorized" or "Invalid token"

**Solution:** Re-run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` to refresh credentials.

### "Files were unexpectedly deleted"

**Error:** Remote files are gone after push

**Solution:** This happens because push deletes remote files not in local. Restore from:
1. Version control backup
2. Previous remote state
3. Pull from another local copy

### "Conflict on multiple files"

**Error:** Many files conflict between local and remote

**Solution:** Choose a strategy:
```bash
# Keep local version (push --overwrite)
uip codedagent push --overwrite

# Keep remote version (pull --overwrite)
uip codedagent pull --overwrite
```
