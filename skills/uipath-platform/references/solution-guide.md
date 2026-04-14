# Solution Guide

Guide to UiPath Solutions — creating, packing, publishing, deploying, and managing solution packages.

## What is a Solution?

A UiPath Solution is a container that groups multiple related automation projects (processes, libraries, tests) into a single deployable unit. Solutions enable:

- **Bundled deployment** — Deploy multiple projects together as a single package
- **Version management** — Track and version the entire solution as one entity
- **Configuration management** — Apply environment-specific configuration at deploy time
- **Multi-environment promotion** — Move solutions through dev → staging → production

### Solution File Structure

```
MySolution/
├── MySolution.uipx              ← Solution definition file
├── ProjectA/                    ← Automation project
│   ├── project.json
│   ├── project.uiproj
│   └── *.cs / *.xaml
├── ProjectB/                    ← Another project in the solution
│   ├── project.json
│   └── ...
└── config.json                  ← Optional: environment configuration
```

---

## Solution Lifecycle

```
Create → Add Projects → Pack → Publish → Deploy → Activate
```

### 1. Create a Solution

Create a new empty solution file:

```bash
uip solution new "MySolution" --output json
```

This creates a `MySolution/` directory containing `MySolution.uipx`.

### 2. Add Projects to the Solution

Add existing automation projects to the solution:

```bash
# Add a project (auto-discovers nearest .uipx)
uip solution project add ./ProjectA --output json

# Add with explicit solution file
uip solution project add ./ProjectB ./MySolution.uipx --output json
```

The project folder must contain `project.uiproj` or `project.json`.

### 3. Remove Projects from a Solution

```bash
uip solution project remove ./ProjectA --output json
```

### 4. Pack the Solution

Pack the solution into a deployable .zip package:

```bash
uip solution pack ./MySolution ./output --output json
```

With version and custom name:

```bash
uip solution pack ./MySolution ./output --name "MySolution" --version "2.0.0" --output json
```

### 5. Publish the Package

Upload the packed solution to UiPath (requires authentication):

```bash
uip login --output json
uip solution publish ./output/MySolution.1.0.0.zip --output json
```

With tenant and location override:

```bash
uip solution publish ./output/MySolution.1.0.0.zip --tenant "Production" --output json
```

---

## Solution Deployment

### Deploy a Solution

```bash
uip solution deploy run -n "MyDeployment" \
  --package-name "MySolution" --package-version "1.0.0" \
  --folder-name "MySolutionFolder" --output json
```

| Option | Description | Default |
|---|---|---|
| `-n, --name <name>` | Name for the deployment (required) | -- |
| `--package-name <name>` | Solution package name to deploy (required) | -- |
| `--package-version <version>` | Solution package version (required) | -- |
| `--folder-name <name>` | Orchestrator folder to create for deployment (required) | -- |
| `--folder-path <path>` | Parent folder path (solution folder created under this) | -- |
| `--folder-key <key>` | Parent folder key (GUID, alternative to --folder-path) | -- |
| `--config-file <path>` | JSON config file (from `deploy config get`) | -- |
| `--timeout <seconds>` | Deployment polling timeout | 360 |
| `--poll-interval <ms>` | Polling interval | 5000 |
| `-t, --tenant <name>` | Tenant override | Current tenant |

### Deployment Lifecycle

| Command | Description |
|---------|-------------|
| `uip solution deploy run -n <name>` | Deploy a solution package (`--package-name`, `--package-version`, `--folder-name` required) |
| `uip solution deploy status <id>` | Check deployment status by pipeline deployment ID |
| `uip solution deploy list` | List deployments (filter by `--folder-path`, `--take`) |
| `uip solution deploy activate <name>` | Activate a deployment that was deployed without auto-activation |
| `uip solution deploy uninstall <name>` | Uninstall a deployment (removes resources and folder) |

### Deploy Config — Customize Before Deploying

The config workflow lets you customize resource settings before deployment:

```bash
# 1. Fetch default config for a published package
uip solution deploy config get "MySolution" -d config.json --output json

# 2. Customize: set a property on a resource
uip solution deploy config set config.json MyQueue maxNumberOfRetries 5

# 3. Customize: link a solution resource to an existing Orchestrator resource
uip solution deploy config link config.json MyQueue --name ProductionQueue --folder-path "Shared/Production"

# Or: remove a link so resource is created fresh
uip solution deploy config unlink config.json MyQueue

# 4. Customize: set conflict resolution for all resources
uip solution deploy config set config.json --all conflictFixingAction UseExisting

# 5. Deploy with the customized config
uip solution deploy run -n "MyDeployment" --package-name "MySolution" --package-version "1.0.0" \
  --folder-name "ProdFolder" --config-file config.json --output json
```

| Config Command | Description |
|----------------|-------------|
| `config get <package-name>` | Fetch default config (`-d <file>` to save, `--package-version` optional) |
| `config set <file> <resource> <property> <value>` | Set a resource property (or `--all` for all resources) |
| `config link <file> <resource> --name <name>` | Link to existing Orchestrator resource (`--folder-path` optional) |
| `config unlink <file> <resource>` | Remove a resource link |

### Solution Packages

| Command | Description |
|---------|-------------|
| `uip solution packages list` | List published solution packages (`--take`, `--order-by`, `--order-direction`) |
| `uip solution packages delete <name> <version>` | Delete a specific package version |

### Other Commands

| Command | Description |
|---------|-------------|
| `uip solution bundle <solutionPath>` | Bundle solution directory into a .uis file (`-d` for destination) |
| `uip solution upload <solutionPath>` | Upload solution to UiPath Studio Web (directory, .uipx, or .uis) |
| `uip solution resource refresh [solutionPath]` | Re-scan projects and sync resource declarations from bindings |
| `uip solution project import --source <path>` | Copy external project into solution and register in .uipx |

---

## CI/CD Pipeline Setup

### GitHub Actions Example

```yaml
name: Deploy UiPath Solution
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uip
        run: npm install -g @uipath/cli

      - name: Authenticate
        run: |
          uip login \
            --client-id "${{ secrets.UIPATH_CLIENT_ID }}" \
            --client-secret "${{ secrets.UIPATH_CLIENT_SECRET }}" \
            --tenant "${{ secrets.UIPATH_TENANT }}" \
            --output json

      - name: Pack solution
        run: uip solution pack ./MySolution ./output --version "${{ github.sha }}" --output json

      - name: Publish solution
        run: uip solution publish ./output/MySolution.*.zip --output json
```

### Environment Promotion Pattern

```bash
#!/bin/bash
# promote.sh - Promote a solution package through environments

PACKAGE=$1  # e.g., ./output/MySolution.1.0.0.zip

# Deploy to Staging
echo "Deploying to Staging..."
uip login tenant set "Staging" --output json
uip solution publish "$PACKAGE" --output json

# After manual approval, deploy to Production
echo "Deploying to Production..."
uip login tenant set "Production" --output json
uip solution publish "$PACKAGE" --output json
```

---

## Common Patterns

### Full End-to-End Workflow

```bash
# 1. Create solution
uip solution new "InvoiceAutomation" --output json

# 2. Add projects
uip solution project add ./InvoiceProcessor --output json
uip solution project add ./InvoiceReporter --output json

# 3. Pack
uip solution pack . ./output --version "1.0.0" --output json

# 4. Login and publish
uip login --output json
uip login tenant set "Production" --output json
uip solution publish ./output/InvoiceAutomation.1.0.0.zip --output json
```

### Version Bumping

Always increment version when republishing:

```bash
# Initial release
uip solution pack ./MySolution ./output --version "1.0.0" --output json

# Bug fix
uip solution pack ./MySolution ./output --version "1.0.1" --output json

# New feature
uip solution pack ./MySolution ./output --version "1.1.0" --output json

# Breaking change
uip solution pack ./MySolution ./output --version "2.0.0" --output json
```

