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

## Idempotent re-deploy: pre-existing tenant state

`deploy` is not always a fresh install. When the goal is "ensure a published version of this agent exists in the tenant" (so a downstream flow / agent can consume it), and a prior publish already satisfies that goal, treat the deploy step as **done** and move on. Do not loop on the failure trying to land a brand-new artifact when the existing one already serves the purpose.

Three conflicts fall in this "already satisfied" bucket:

| Conflict | Server response | Meaning |
|---|---|---|
| Version already exists | `409 Package already exists` | A package with this exact `name@version` is already published. The downstream consumer can resolve the agent by name/version. |
| Package type mismatch | e.g. `now is Function` vs prior `Agent` | A package with the same name was previously published under a different project type. Tenant feeds key on name; the existing entry is what consumers will see. |
| Missing `--my-workspace` scope | Token lacks `OrchestratorApiUserAccess` | The caller's token cannot publish to the personal workspace. If a prior call already established a published version (in the personal workspace or the tenant feed), the consumer can use that. |

In all three cases, when the downstream goal is consumption rather than upgrade:

- **The deploy command's own JSON output is the authoritative source** for the package key — it prints the Orchestrator-assigned GUID directly. Use it as the consumer's `resourceKey` and move on. Don't run a separate discovery call to re-fetch what `deploy` already returned.
- Always run `uip maestro flow registry pull --force` after a deploy (success OR conflict) to refresh the local flow registry cache. This is the only registry call worth making post-deploy. Do NOT use `uip maestro flow registry search` for verification — that search only enumerates built-in node types (`uipath.agent.autonomous`, `uipath.agent.resource.escalation`, etc.); user-deployed coded agents do NOT appear there, so an empty result is the *expected* state and is NOT a signal that anything went wrong.
- If the deploy command's output is unavailable, try `uip or packages list --search "<agent-name>" --output json` (returns 404 on tenants where the caller lacks `Orchestrator.Packages.View` scope) — at most one fallback attempt, not a loop.
- Do NOT bump the version, switch deploy target, edit `project.uiproj` to flip the project type, or re-`uip login` to acquire a broader scope.
- Do NOT delete the existing tenant entry — these are shared resources others may depend on.

**Hard rule — at most ONE re-deploy attempt on a conflict.** If the first `deploy` fails with any of the three conflicts above, do NOT immediately bump and retry. Stop, capture the package key from the conflict response or fall back to `uip or packages list --search "<agent-name>"` once, and move on. A re-deploy is only justified when the explicit intent is to publish a *new* version (a real upgrade), in which case bump the patch in `pyproject.toml` once and re-`deploy` exactly once. Looping `deploy → conflict → bump → deploy` more than once burns turns without changing the outcome.

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
