# Deploy UiPath Agents

Package, publish, and invoke your agents in UiPath Cloud.

## Quick Reference

```bash
# Pack + publish in one command
uip codedagent deploy --my-workspace

# Or step by step
uip codedagent pack
uip codedagent publish --my-workspace

# Invoke published agent — use entrypoint name from entry-points.json, NOT project name
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

## Documentation

- **[Deployment Guide](deployment.md)** — Complete deployment workflow
  - `uip codedagent pack` — Package into .nupkg with validation
  - `uip codedagent publish` — Upload to Orchestrator feed (--my-workspace, --tenant, --folder)
  - `uip codedagent deploy` — Combined pack + publish
  - `uip codedagent invoke` — Execute published agents in cloud
  - Pack options (`packOptions` in `uipath.json`)
  - Configuration files and environment variables

## Prerequisites

- Authentication configured — if not authenticated, use the [authentication reference](../../authentication.md) first
- `entry-points.json` exists (run `uip codedagent init`)
- `pyproject.toml` has `name`, `version`, `description`, `authors`

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Pack failed: missing fields` | `pyproject.toml` incomplete | Ensure `name`, `version`, `description`, and `authors` are all set |
| `Version already exists` | Same version already published | Bump the patch version in `pyproject.toml` before re-deploying |
| `401 Unauthorized` | Auth expired or not configured | Re-run `uip login --output json` then `uip login tenant set "<TENANT>" --output json` |

## Additional Instructions

- Read the [deployment reference](deployment.md) for details on pack options and feed selection.
- Always test locally with `uip codedagent run <ENTRYPOINT>` before deploying.

---

# Deployment

Package, publish, and invoke your UiPath coded agent in the cloud.

## Deployment Workflow

```
uip codedagent init → uip codedagent run (test) → uip codedagent pack → uip codedagent publish → uip codedagent invoke
                                       \___________ uip codedagent deploy ___________/
```

## Pack

Package your project into a `.nupkg` file for deployment.

```bash
uip codedagent pack
```

### What It Does

1. Validates project structure (`uipath.json`, `pyproject.toml`, `entry-points.json`)
2. Runs `uv lock` to lock dependencies
3. Generates metadata files (`operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`)
4. Creates a `.nupkg` file in `.uipath/`

### Options

| Option | Description |
|--------|-------------|
| `root` | Project root directory (default: `.`) |
| `--nolock` | Skip `uv lock` and exclude `uv.lock` from package |

### Package Contents

The generated `.nupkg` (NuGet package) contains:

```
content/
├── operate.json           # Operation configuration
├── entry-points.json      # Entry point definitions
├── bindings_v2.json       # Runtime bindings
├── package-descriptor.json # File manifest
├── main.py                # Your source files
├── pyproject.toml
└── uv.lock                # (unless --nolock)
```

### Controlling Included Files

Use `packOptions` in `uipath.json` to control which files are packaged:

```json
{
  "packOptions": {
    "fileExtensionsIncluded": [".py", ".json"],
    "filesIncluded": ["config.yaml"],
    "filesExcluded": ["test_*.py"],
    "directoriesExcluded": ["tests", "__pycache__"],
    "includeUvLock": true
  }
}
```

### Output

```
Name:        my-agent
Version:     0.1.0
Description: UiPath Coded Agent - My agent description
Authors:     Your Name
```

The package is saved as `.uipath/my-agent.0.1.0.nupkg`.

---

## Publish

Upload a packaged project to a UiPath feed.

```bash
uip codedagent publish
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--tenant` | `-t` | Publish to the tenant package feed |
| `--my-workspace` | `-w` | Publish to your personal workspace |
| `--folder` | `-f` | Specify folder name (skips interactive selection) |

### Examples

```bash
# Publish to personal workspace
uip codedagent publish --my-workspace

# Publish to tenant feed
uip codedagent publish --tenant

# Publish to a specific folder
uip codedagent publish --folder "Finance"
```

### Feed Selection

If no flag is specified, the CLI displays an interactive menu to select the target feed. Feed matching is case-insensitive and strips common prefixes/suffixes (e.g., "Orchestrator My Folder Feed" matches "My Folder").

### Authentication

Authentication configures these environment variables:
- `UIPATH_URL` - Base URL of your UiPath instance
- `UIPATH_ACCESS_TOKEN` - Bearer token for authorization

---

## Deploy

Shorthand that runs **pack + publish** in one command.

```bash
uip codedagent deploy
```

### Options

Combines all options from pack and publish:

| Option | Short | Description |
|--------|-------|-------------|
| `root` | | Project root directory (default: `./`) |
| `--tenant` | `-t` | Publish to tenant feed |
| `--my-workspace` | `-w` | Publish to personal workspace |
| `--folder` | `-f` | Specify folder name |

### Examples

```bash
# Deploy to personal workspace
uip codedagent deploy --my-workspace

# Deploy to a specific folder
uip codedagent deploy --folder "Finance"

# Deploy from a subdirectory
uip codedagent deploy ./my-agent --my-workspace
```

---

## Execute

To run and test your published agent, use `uip codedagent invoke <entrypoint> '<json-input>'`. This is async — it returns a monitoring URL immediately. There is NO `--wait` flag.

---

## Configuration Files

### Files Used During Deployment

| File | Created By | Used By | Purpose |
|------|-----------|---------|---------|
| `uipath.json` | `uip codedagent init` | `pack` | Runtime options, pack options |
| `pyproject.toml` | You | `pack`, `invoke` | Project name, version, dependencies |
| `entry-points.json` | `uip codedagent init` | `pack`, `invoke` | Entry point definitions with schemas |
| `bindings.json` | `uip codedagent init` | `pack` | Runtime bindings |

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `UIPATH_URL` | publish, deploy, invoke | UiPath instance base URL |
| `UIPATH_ACCESS_TOKEN` | publish, deploy, invoke | Bearer token for API auth |
| `UIPATH_FOLDER_PATH` | optional | Default folder context |

These are set automatically by `uip login`.

## Version Bumping

Publishing fails with `409 Package already exists` if the version was already published. **Before re-deploying, bump the patch version** in `pyproject.toml`:

```toml
[project]
version = "0.0.2"  # was 0.0.1
```

On re-deploy, always increment the patch number (e.g., `0.0.1` → `0.0.2` → `0.0.3`). Only bump minor/major for breaking or feature changes.

## Typical Deployment Flow

1. Authenticate with `uip login --output json` then `uip login tenant set "<TENANT>" --output json`
2. Test locally: `uip codedagent run main '<input-json>'`
3. Bump version in `pyproject.toml` if re-deploying
4. Deploy: `uip codedagent deploy --my-workspace`
5. Invoke published agent: `uip codedagent invoke main '<input-json>'`

> **Note:** Use `uip codedagent run` for local testing and `uip codedagent invoke` for cloud execution.
