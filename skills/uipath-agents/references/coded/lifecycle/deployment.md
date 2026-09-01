# Deploy UiPath Agents

Build and publish a coded agent to UiPath Cloud with one command.

## Prerequisites

- Verify authentication: run `uip login status` and confirm `Logged in`; see [authentication](../../authentication.md).
- Ensure `entry-points.json` exists; run `uip codedagent init` if needed.
- Ensure `pyproject.toml` defines `name`, `version`, `description`, and `authors`.
- Run `uip codedagent run <ENTRYPOINT> '<input>'` successfully before deploying.

## Deploy

Run:

```bash
uip codedagent deploy --my-workspace
```

`deploy` validates the project, runs `uv lock`, builds a `.nupkg`, and uploads it. Run this standard path; do not call the disabled `pack` or `publish` subcommands directly.

In non-interactive shells, pass exactly one deployment target or the CLI prompts and fails:

| Option | Short | Description |
|---|---|---|
| `--my-workspace` | `-w` | Personal workspace |
| `--tenant` | `-t` | Tenant package feed |
| `--folder <name>` | `-f` | Specific folder feed |
| `root` | positional | Project root when deploying from a parent directory |

Examples:

```bash
uip codedagent deploy --my-workspace
uip codedagent deploy --tenant
uip codedagent deploy --folder "<folder-name>"
uip codedagent deploy ./my-agent --my-workspace
```

## Invoke a Deployed Agent

Run:

```bash
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

Use the key from `entry-points.json` for `<ENTRYPOINT>`, not the project name. `invoke` is asynchronous and immediately returns a monitoring URL; it has no `--wait` flag. Run `uip codedagent run` for local testing.

## Package Contents and Options

The `.nupkg` produced by `deploy` contains:

```text
content/
├── operate.json
├── entry-points.json
├── bindings_v2.json
├── package-descriptor.json
├── main.py                # your source files
├── pyproject.toml
└── uv.lock
```

Configure inclusion with `packOptions` in `uipath.json`:

| Property | Type | Required | Default | Description |
|---|---|---|---|---|
| `fileExtensionsIncluded` | `string[]` | No | `[".py", ".mermaid", ".json", ".yaml", ".yml", ".md"]` | File extensions included |
| `filesIncluded` | `string[]` | No | `["pyproject.toml"]` | Files always included |
| `filesExcluded` | `string[]` | No | `[]` | Files excluded |
| `directoriesExcluded` | `string[]` | No | `[]` | Directories excluded |
| `includeUvLock` | `boolean` | No | `false` | Whether to include `uv.lock` |

Example:

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

Publishing the same version twice returns `409 Package already exists`. Before each re-deploy intended to publish a new artifact, increment the patch in `pyproject.toml`; increment minor or major only for feature or breaking changes.

```toml
[project]
version = "0.0.2"
```

## Idempotent Re-deploy and Existing Tenant State

When ensuring that a published version exists for downstream consumption, treat an existing publication that satisfies the goal as complete; do not loop to create another artifact.

These conflicts are already-satisfied states:

| Conflict | Server response | Meaning |
|---|---|---|
| Version already exists | `409 Package already exists` | The exact `name@version` is published |
| Package type mismatch | e.g. `now is Function` vs prior `Agent` | The same name was previously published under another project type; tenant feeds key on name |
| Missing `--my-workspace` scope | Token lacks `OrchestratorApiUserAccess` | The token cannot publish to the personal workspace; an existing personal-workspace or tenant publication may still satisfy consumption |

For these conflicts when consumption, rather than upgrade, is intended:

- Use the deploy command’s own JSON output as authoritative for the package key. Use its Orchestrator-assigned GUID as the consumer’s `resourceKey` without a separate discovery call.
- Always run `uip maestro flow registry pull --force` after deploy, whether it succeeds or conflicts, to refresh the local flow registry cache.
- Do not run `uip maestro flow registry search` for verification. It enumerates only built-in node types (`uipath.agent.autonomous`, `uipath.agent.resource.escalation`, etc.); user-deployed coded agents do not appear there, so an empty result is expected.
- If deploy output is unavailable, run `uip or packages list --search "<agent-name>" --output json` at most once. It returns 404 when the caller lacks `Orchestrator.Packages.View` scope.
- Do not bump the version, switch deployment target, edit `project.uiproj` to flip project type, re-run `uip login` for a broader scope, or delete the existing tenant entry.

**Hard rule — at most ONE re-deploy attempt on a conflict.** After a first deploy fails with one of these conflicts, do not immediately bump and retry. Stop, capture the package key from the conflict response, or make the one permitted `uip or packages list --search "<agent-name>"` fallback, then move on. Re-deploy only for explicit intent to publish a new version: bump the patch once and run `deploy` exactly once. Never loop `deploy → conflict → bump → deploy` more than once.

## Configuration Files

| File | Created By | Purpose |
|---|---|---|
| `uipath.json` | `uip codedagent init` | Runtime and pack options |
| `pyproject.toml` | You | Project name, version, dependencies |
| `entry-points.json` | `uip codedagent init` | Entry points and input/output schemas |
| `bindings.json` | `uip codedagent init` | Runtime bindings |
| `.env` | You | Local-run environment variables and `UIPATH_PROJECT_ID`; neither packaged nor pushed — see [environment-variables.md](environment-variables.md) |

`uip codedagent deploy` and `invoke` read `UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, and org/tenant identifiers from the active `uip login` session; no manual `.env` wiring is required.

A deployed agent receives environment variables from Orchestrator at process or job level, not from `.env`. To resolve an asset value at dispatch, set it to `%ASSETS/<ASSET_NAME>%`; resolution uses the **job’s** folder. See [environment-variables.md](environment-variables.md).

## Typical Flow

1. Run `uip codedagent run <ENTRYPOINT> '<input>'` to verify locally.
2. If publishing a new version, bump the patch version.
3. Run `uip codedagent deploy --my-workspace`, `--tenant`, or `--folder` with the appropriate target.
4. Run `uip codedagent invoke <ENTRYPOINT> '<input>'` to trigger the cloud agent.

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` |
| `Pack failed: missing fields` | Incomplete `pyproject.toml` | Set `name`, `version`, `description`, and `authors` |
| `Version already exists` / `409` | Same version already published | For a genuine upgrade, bump the patch version; otherwise follow the existing-tenant conflict rules |
| `401 Unauthorized` | Session expired | Re-authenticate; see [authentication](../../authentication.md) |
| `The 'pack'/'publish' command is disabled` | Disabled subcommand called directly | Run `uip codedagent deploy` instead |
