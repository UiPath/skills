# Activate & Manage

Activate deployed solutions, uninstall deployments, and manage published solution packages.

> For full option details on any command, use `--help` (e.g., `uip solution deploy activate --help`).

## When to Use

- Activating a deployment that was not auto-activated
- Upgrading an existing deployment to a newer package version in place (when a redeploy is blocked because the deployment already exists)
- Cleaning up old or failed deployments
- Managing published package versions in the solution feed
- Removing solutions from Studio Web

## Prerequisites

- Authenticated — verify with `uip login status`; if not logged in, ask the user to run `uip login` (it opens an interactive browser flow)
- Solution deployed (see [pack-and-deploy.md](pack-and-deploy.md))

## Flow

```mermaid
graph LR
    A[deploy activate] --> B[deploy status]
    C[deploy list] --> D[deploy uninstall]
    C --> E[packages list]
    E --> F[packages delete]
    G[solution delete]
```

---

## Step 1: Activate a Deployment

`solution deploy run` activates by default. Use `deploy activate` only when:
- the deploy was started with `--skip-activate`, or
- the previous activation failed (e.g. missing config) and you've fixed the cause and want to retry without redeploying.

Activation provisions all solution components (processes, queues, assets, etc.) in the target folder:

```bash
uip solution deploy activate "MyDeployment" --output json

# With custom polling
uip solution deploy activate "MyDeployment" --timeout 600 --poll-interval 10000 --output json
```

| Option | Description | Default |
|--------|-------------|---------|
| `<deployment-name>` | Name of the deployment to activate (required) | -- |
| `--timeout <seconds>` | Polling timeout | 360 |
| `--poll-interval <ms>` | Polling interval | 5000 |

## Step 2: Check Deployment Status

After activation (or any deployment operation), verify the state:

```bash
# By pipeline deployment ID (returned by deploy run)
uip solution deploy status <pipeline-deployment-id> --output json

# Or list all deployments and inspect
uip solution deploy list --output json
```

> `deploy status` reads the pipeline run against the **tenant** feed and takes
> no feed flag, so it cannot see a run in a Personal Workspace or a folder
> feed. For those, use `uip solution deploy list --personal-workspace` or
> `--feed <name-or-key>`, which do scope.

## Upgrade a Deployment In Place

`deploy run` fails with HTTP 400 when a deployment for the solution **already exists** — you can't redeploy over it, you have to upgrade it in place (the same as the Orchestrator UI's "Upgrade" button). `deploy upgrade` does that from the CLI, so you don't have to open the UI:

```bash
# Upgrade to the newest published version (default), waiting for it to finish
uip solution deploy upgrade --name <deployment-name> --package-name <pkg> --output json

# A specific version — the CI/CD form: one install call, no lookups
uip solution deploy upgrade --name <deployment-name> --package-name <pkg> \
  --version 2.0.0 --output json

# A deployment in your Personal Workspace feed
uip solution deploy upgrade --name <deployment-name> --package-name <pkg> \
  --personal-workspace --output json

# Start it and return immediately
uip solution deploy upgrade --name <deployment-name> --package-name <pkg> \
  --no-wait --output json
```

Find the deployment name and its package with `uip solution deploy list`. On success the output is `Code: SolutionDeployUpgrade`, `Data: { Status, Operation, DeploymentName, ToVersion, PipelineDeploymentId, DeploymentKey }`. `Status` is the pipeline run's terminal status — `DeploymentSucceeded` once the upgrade landed, or `Accepted` with `--no-wait` (where `Operation` and `DeploymentKey` are absent, because no run has finished to report them). `PipelineDeploymentId` is what `uip solution deploy status` reads.

**Behavior and limits:**
- The deployment's **existing configuration is preserved** — the server carries each unchanged resource's configuration forward and takes only changed specs from the new package, so an upgrade does not regenerate a credential asset's secret. Resources the new version adds are created. This is the reason to use `deploy upgrade` rather than uninstall-and-redeploy.
- **It takes a deployment name, not a key, and that is what makes it usable from CI/CD.** The Pipelines route addresses a deployment by name; the only thing that could translate a key is an Automation Solutions read that accepts user tokens only. So an upgrade addressed by key cannot run under an external app (client-credentials) at all. Addressed by name, every call on the path is external-app capable. `--package-name` is required for the same reason: nothing in the platform maps a deployment name to its package. Supply `--version` as well and the whole upgrade is a single install call plus its status poll — no lookups.
- **`Operation` is what tells you a version moved.** The install endpoint is unified, so asking for the version *already* deployed is a configuration change, not an upgrade. `Operation: "VersionChange"` means the version moved; `"ConfigurationChange"` means it did not and the configuration was re-applied instead. Read it rather than treating `DeploymentSucceeded` as proof of a new version — there is no pre-flight refusal, because comparing the deployed version would need the user-token-only read above.
- **The package is validated against the target before anything is installed.** The upgrade goes through the same Pipelines install as `deploy run`, which the server treats as an in-place upgrade when the deployment name already exists with the same package and a different version. Validation runs first, so a configuration the target rejects ends the run at `Status: ValidationFailed` with the per-resource errors in `Instructions` and **the deployment still on its current version** — nothing is half-installed. Earlier CLI versions installed straight away and a late validation failure could strand the deployment in a state that offered only *Uninstall*.
- By default the command **waits** for the install to reach a terminal state (`--timeout <seconds>`, default 300; `--poll-interval <ms>`, default 5000). Pass `--no-wait` to return as soon as the install is accepted.
- A failure reports the server's reason (for example `Solution folder not found` when the deployment's solution folder was deleted), not a bare status. The reason normally comes from the pipeline run itself; when the run record has already been recycled the CLI reads the deployment's validation result instead, and says `the server reported no reason.` only when the server genuinely gives none.
- After a successful upgrade the deployment can land in `ReadyToActivate` rather than `Active`. Check with `uip solution deploy list` and run `uip solution deploy activate <deployment-name>` if activation is pending.
- **Any published version of the same package is a valid target.** Omit `--version` to take the newest (one extra lookup), or pass `--version <version>` for a specific one — including an older version, to step back. Requesting the version already deployed is not refused; it comes back as `Operation: "ConfigurationChange"` (see above).
- The server decides what may be upgraded, and refuses synchronously — before any `PipelineDeploymentId` exists — when the deployment name does not exist, when it belongs to a different package than `--package-name`, when an operation is already in progress on it, or when it is not in an upgradeable state. A deployment whose validation failed *is* upgradeable on current Orchestrator, which is how you fix its configuration and move on; on an older Automation Solutions build the same deployment is refused, and uninstall-and-redeploy is the only way out.

## Step 3: Uninstall a Deployment

Remove a deployment, including all provisioned resources and the Orchestrator folder:

```bash
uip solution deploy uninstall "MyDeployment" --output json

# With custom polling
uip solution deploy uninstall "MyDeployment" --timeout 600 --poll-interval 10000 --output json
```

| Option | Description | Default |
|--------|-------------|---------|
| `<deployment-name>` | Name of the deployment to uninstall (required) | -- |
| `--timeout <seconds>` | Polling timeout | 360 |
| `--poll-interval <ms>` | Polling interval | 5000 |

This is destructive -- it removes the Orchestrator folder and all resources that were provisioned by the deployment.

## Step 4: List Published Packages

View all solution packages that have been published to the feed:

```bash
uip solution packages list --output json

# Paginate and sort
uip solution packages list --limit 20 --sort-by "Name" --sort-order "Ascending" --output json
uip solution packages list --limit 50 --offset 50 --output json   # page 2

# Filter by name (server-side substring match on the package name, case-insensitive)
uip solution packages list --name "Invoice" --output json
```

| Option | Description | Default |
|--------|-------------|---------|
| `--limit <n>` | Number of results to return | 50 |
| `--offset <n>` | Number of results to skip (page start) | 0 |
| `--name <pattern>` | Server-side substring match on the package name | -- |
| `--sort-by <field>` | Sort field | -- |
| `--sort-order <dir>` | `Ascending` or `Descending` | -- |

The response's `Pagination` block reports `Total` (all matches on the server) and `HasMore`. If `HasMore` is `true`, re-run with `--offset <previous offset + Returned>` to fetch the next page — a package missing from the first page is not necessarily absent. The list is tenant-scoped: packages published on another tenant of the same organization do not appear; check the active tenant with `uip login status`.

## Step 5: Download a Package Version

Download a published solution package .zip from the solution feed:

```bash
# Latest ready/active version, saved as ./MySolution.<version>.zip
uip solution packages download "MySolution" --output json

# Specific version, saved to a directory or full file path
uip solution packages download "MySolution" "1.0.0" --destination ./packages/ --output json
uip solution packages download "MySolution" --package-version "1.0.0" --destination ./packages/MySolution.1.0.0.zip --output json
```

Use `--destination <path>` for the local output file or directory. Reserve `--output json` for the CLI response format when you need to parse the command result.

| Option | Description | Default |
|--------|-------------|---------|
| `<package-name>` | Published solution package name | -- |
| `[package-version]` | Package version to download | Latest ready/active version |
| `--package-version <version>` | Version selector alternative to the positional version | Latest ready/active version |
| `--destination <path>` | Local .zip file path or directory | Current directory |

## Step 6: Delete a Package Version

Remove a specific version of a published package from the solution feed:

```bash
uip solution packages delete "MySolution" "1.0.0" --output json
```

Arguments: `<package-name> <package-version>`. This deletes only the specified version, not all versions of the package.

## Step 7: Delete from Studio Web

Remove a solution from Studio Web (browser-based editor). This is separate from deployment management:

```bash
uip solution delete <solution-id> --output json
```

This removes the solution from Studio Web. It does **not** affect any deployed instances in Orchestrator.

---

## Complete Example

List deployments, uninstall an old one, and clean up the published package version:

```bash
# List current deployments
uip solution deploy list --limit 20 --output json

# Uninstall the old deployment
uip solution deploy uninstall "MySolution-v1" --output json

# Verify it was removed
uip solution deploy list --output json

# Clean up the old package version from the feed
uip solution packages list --output json
uip solution packages delete "MySolution" "1.0.0" --output json
```

---

## Variations and Gotchas

### `deploy uninstall` vs `solution delete`

These are different operations targeting different systems:

| Command | What it removes | System |
|---------|----------------|--------|
| `deploy uninstall <name>` | Orchestrator folder, provisioned resources | Orchestrator |
| `solution delete <id>` | Solution project | Studio Web |

Uninstalling a deployment does not remove the package from the solution feed. Deleting from Studio Web does not affect Orchestrator deployments.

### Activation Provisions Components

Activation is not instant. It provisions processes, queues, assets, and other resources in the Orchestrator folder. The command polls until completion or timeout. For large solutions, consider increasing `--timeout`.

### `packages delete` Deletes One Version

`packages delete` takes both a name **and** a version. It deletes only that specific version. To remove all versions, you must delete each one individually.

### `packages download` Uses `--destination` for Files

`--output` is the global CLI response format flag (`json`, `table`, `yaml`, `plain`). For downloaded solution package files, use `--destination <path>` so commands can also keep `--output json` for parseable results.

### Uninstall is Destructive

`deploy uninstall` removes the Orchestrator folder and all resources inside it. There is no undo. Verify the deployment name carefully before running this command.

### Polling Units

Same as `deploy run`: `--poll-interval` is in **milliseconds** (default 5000ms), `--timeout` is in **seconds** (default 360s).

---

## Related

- [pack-and-deploy.md](pack-and-deploy.md) -- Pack, publish, and deploy solutions
- [scenarios.md](scenarios.md) -- Multi-project recipes for resource-handling patterns
- [solution-overview.md](solution-overview.md) -- Solution overview and lifecycle
