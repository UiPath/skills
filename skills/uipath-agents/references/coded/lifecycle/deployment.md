# Deploy UiPath Agents

Build and publish a coded agent to UiPath Cloud with a single command.

## Prerequisites

- Authenticated session (`uip login status` reports `Logged in`). See [authentication](../../authentication.md).
- `entry-points.json` exists (run `uip codedagent init`).
- `pyproject.toml` has `name`, `version`, `description`, `authors`.
- Agent runs cleanly with `uip codedagent run <ENTRYPOINT> '<input>'`.

## Deploy

```bash
uip codedagent deploy --my-workspace
```

`deploy` validates the project, locks dependencies (`uv lock`), builds a `.nupkg`, and uploads it in one step. Use this as the standard path. The underlying `pack` and `publish` subcommands are disabled in the wrapper — do not call them directly.

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--my-workspace` | `-w` | Personal workspace |
| `--tenant` | `-t` | Tenant package feed |
| `--folder <name>` | `-f` | Specific folder feed (e.g., `"Finance"`) |
| `root` | (positional) | Project root when deploying from a parent directory |

If no target flag is provided the CLI prompts interactively, which fails in non-interactive shells — always pass one of `--my-workspace`, `--tenant`, or `--folder`.

### Examples

```bash
# Personal workspace (default for first-time deploys)
uip codedagent deploy --my-workspace

# Tenant feed
uip codedagent deploy --tenant

# Specific folder feed
uip codedagent deploy --folder "Finance"

# Deploy a sibling project without cd'ing
uip codedagent deploy ./my-agent --my-workspace
```

## Invoke a Deployed Agent

```bash
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

`<ENTRYPOINT>` is the key from `entry-points.json` (for example `main`), not the project name. Invoke is asynchronous — it returns a monitoring URL immediately; there is no `--wait` flag. Use `uip codedagent run` for local testing.

## What Goes Into the Package

The `.nupkg` produced by `deploy` contains:

```
content/
├── operate.json
├── entry-points.json
├── bindings_v2.json
├── package-descriptor.json
├── main.py                # your source files
├── pyproject.toml
└── uv.lock
```

Control file inclusion via `packOptions` in `uipath.json`:

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

## Version Bumping

Publishing the same version twice returns `409 Package already exists`. Bump the patch in `pyproject.toml` before each re-deploy:

```toml
[project]
version = "0.0.2"  # was 0.0.1
```

Increment patch for bugfixes; bump minor/major only for feature or breaking changes.

## Configuration Files

| File | Created By | Purpose |
|------|-----------|---------|
| `uipath.json` | `uip codedagent init` | Runtime options, pack options |
| `pyproject.toml` | You | Project name, version, dependencies |
| `entry-points.json` | `uip codedagent init` | Entry points and input/output schemas |
| `bindings.json` | `uip codedagent init` | Runtime bindings |

`uip codedagent deploy` and `invoke` read credentials (`UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, org/tenant identifiers) from your active `uip login` session — no manual `.env` wiring is required.

## Typical Flow

1. `uip codedagent run <ENTRYPOINT> '<input>'` — verify locally.
2. Bump patch version if re-deploying.
3. `uip codedagent deploy --my-workspace` (or `--tenant` / `--folder`).
4. `uip codedagent invoke <ENTRYPOINT> '<input>'` — trigger in cloud.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` |
| `Pack failed: missing fields` | `pyproject.toml` incomplete | Ensure `name`, `version`, `description`, `authors` are all set |
| `Version already exists` / `409` | Same version already published | Bump the patch version in `pyproject.toml` |
| `401 Unauthorized` | Session expired | Re-authenticate; see [authentication](../../authentication.md) |
| `The 'pack'/'publish' command is disabled` | Called the disabled subcommand directly | Use `uip codedagent deploy` instead |
