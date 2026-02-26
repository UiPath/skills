# Deployment

Package, publish, and invoke your UiPath coded agent in the cloud.

## Deployment Workflow

```
uipath init  →  uipath run (test)  →  uipath pack  →  uipath publish  →  uipath invoke
                                       \___________ uipath deploy ___________/
```

## Pack

Package your project into a `.nupkg` file for deployment.

```bash
uv run uipath pack
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
uv run uipath publish
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
uv run uipath publish --my-workspace

# Publish to tenant feed
uv run uipath publish --tenant

# Publish to a specific folder
uv run uipath publish --folder "Finance"
```

### Feed Selection

If no flag is specified, the CLI displays an interactive menu to select the target feed. Feed matching is case-insensitive and strips common prefixes/suffixes (e.g., "Orchestrator My Folder Feed" matches "My Folder").

### Authentication

Requires these environment variables (set via `uv run uipath auth`):
- `UIPATH_URL` - Base URL of your UiPath instance
- `UIPATH_ACCESS_TOKEN` - Bearer token for authorization

---

## Deploy

Shorthand that runs **pack + publish** in one command.

```bash
uv run uipath deploy
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
uv run uipath deploy --my-workspace

# Deploy to a specific folder
uv run uipath deploy --folder "Finance"

# Deploy from a subdirectory
uv run uipath deploy ./my-agent --my-workspace
```

---

## Invoke

Execute a published agent in your personal workspace.

```bash
uv run uipath invoke [entrypoint] [input]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `entrypoint` | Entry point path to invoke (optional) |
| `input` | JSON input data (default: `{}`) |

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | JSON file for input (overrides positional input) |

### Examples

```bash
# Invoke with inline input
uv run uipath invoke main '{"query": "What is UiPath?"}'

# Invoke with input from file
uv run uipath invoke main --file input.json

# Invoke default entrypoint
uv run uipath invoke
```

### What It Does

1. Reads `pyproject.toml` for project name and version
2. Looks up the published release in your personal workspace
3. Starts a job with the provided input
4. Returns a monitoring URL to track execution

### Output

```
Job started successfully!
Monitor your job here: https://cloud.uipath.com/...
```

---

## Configuration Files

### Files Used During Deployment

| File | Created By | Used By | Purpose |
|------|-----------|---------|---------|
| `uipath.json` | `uipath init` | `pack` | Runtime options, pack options |
| `pyproject.toml` | You | `pack`, `invoke` | Project name, version, dependencies |
| `entry-points.json` | `uipath init` | `pack`, `invoke` | Entry point definitions with schemas |
| `bindings.json` | `uipath init` | `pack` | Runtime bindings |

### Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `UIPATH_URL` | publish, deploy, invoke | UiPath instance base URL |
| `UIPATH_ACCESS_TOKEN` | publish, deploy, invoke | Bearer token for API auth |
| `UIPATH_FOLDER_PATH` | optional | Default folder context |

These are set automatically by `uv run uipath auth`.

## Typical Deployment Flow

```bash
# 1. Authenticate
uv run uipath auth --alpha

# 2. Test locally
uv run uipath run main '{"query": "test"}'

# 3. Deploy to personal workspace
uv run uipath deploy --my-workspace

# 4. Invoke the published agent
uv run uipath invoke main '{"query": "What is UiPath?"}'
```

## Next Steps

- **Set up a project**: See [Project Setup](setup.md) for prerequisites
- **Build an agent**: See [Creating Agents](creating-agents.md) for development workflow
- **Test locally**: See [Running Agents](running-agents.md) before deploying
- **Add evaluations**: See [Evaluations](evaluations.md) to validate agent quality
