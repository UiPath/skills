# Deploy UiPath Agents

> **Agent type: Both coded and low-code agents.** The `deploy`, `pack`, `publish`, and `invoke` commands work for both types. Coded agents require a `pyproject.toml` with `name`/`version`/`authors` and version bumping before re-deploy. Low-code agents only need `agent.json` and `entry-points.json` — no Python packaging.

Package, publish, and invoke your agents in UiPath Cloud.

## Quick Reference

```bash
# Pack + publish in one command (recommended)
uip codedagent deploy --my-workspace

# Note: uip codedagent pack and uip codedagent publish as standalone
# commands are blocked by the CLI wrapper. Use deploy instead.

# Invoke published agent — use entrypoint name from entry-points.json, NOT project name
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

## Documentation

- **[Authentication](authentication.md)** — Set up credentials before deploying
- **[Running Agents](running-agents.md)** — Test locally before deploying
- **[File Sync](file-sync.md)** — Push to Studio Web before deploying for the first time

## Prerequisites

- Authentication configured — if not authenticated, use the [authentication reference](authentication.md) first
- `entry-points.json` exists (run `uip codedagent init`)
- `pyproject.toml` has `name`, `version`, `description`, `authors` (**coded agents only** — low-code agents do not need this)

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Pack failed: missing fields` | `pyproject.toml` incomplete | Ensure `name`, `version`, `description`, and `authors` are all set |
| `Version already exists` | Same version already published | Bump the patch version in `pyproject.toml` before re-deploying |
| `401 Unauthorized` | Auth expired or not configured | Re-run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` |

## Additional Instructions

- Read the [deployment reference](deployment.md) for details on pack options and feed selection.
- Always test locally with `uip codedagent run <ENTRYPOINT>` before deploying.

---

# Deployment

Package, publish, and invoke your UiPath coded agent in the cloud.

## Deployment Workflow

```
uip codedagent init → uip codedagent run (test) → uip codedagent deploy → uip codedagent invoke
                                                     (pack + publish combined)
```

## Pack

Package your project into a `.nupkg` file for deployment.

> **Low-code agents:** The `pack` step is handled automatically by `deploy`. No `pyproject.toml` version bumping is needed.

> **⚠️ `uip codedagent pack` as a standalone command is blocked** by the CLI wrapper and will return an error. Use `uip codedagent deploy` instead — it runs pack and publish internally. If you need the `.nupkg` file without publishing, use `uip codedagent deploy` and retrieve it from `.uipath/`.

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

> **Low-code agents:** The `.nupkg` contains `agent.json`, `entry-points.json`, `bindings_v2.json`, and `operate.json` — no `main.py`, `pyproject.toml`, or `uv.lock`. The `Pack` step also does not require a version bump; only coded agents need version bumping before re-deploy.

The package is saved as `.uipath/my-agent.0.1.0.nupkg`.

---

## Publish

Upload a packaged project to a UiPath feed.

> **⚠️ `uip codedagent publish` as a standalone command is blocked** by the CLI wrapper and will return an error. Use `uip codedagent deploy` which combines pack + publish in one step.

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
| `bindings.json` | `uip codedagent init` | `pack` | Developer-facing runtime bindings (converted to `bindings_v2.json` inside the `.nupkg` by `pack`) |

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `UIPATH_URL` | publish, deploy, invoke | UiPath instance base URL |
| `UIPATH_ACCESS_TOKEN` | publish, deploy, invoke | Bearer token for API auth |
| `UIPATH_FOLDER_PATH` | optional | Default folder context |

These are set automatically by `uip login`.

## Version Bumping

Publishing fails with `409 Conflict` (shown as "Version already exists" in some CLI versions) if the version was already published. **Before re-deploying, bump the patch version** in `pyproject.toml`:

```toml
[project]
version = "0.0.2"  # was 0.0.1
```

On re-deploy, always increment the patch number (e.g., `0.0.1` → `0.0.2` → `0.0.3`). Only bump minor/major for breaking or feature changes.

## Typical Deployment Flow

1. Authenticate with `uip login --format json` then `uip login tenant set "<TENANT>" --format json`
2. Test locally: `uip codedagent run main '<input-json>'`
3. Bump version in `pyproject.toml` if re-deploying
4. Deploy: `uip codedagent deploy --my-workspace`
5. Invoke published agent: `uip codedagent invoke main '<input-json>'`

> **Note:** Use `uip codedagent run` for local testing and `uip codedagent invoke` for cloud execution.
