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

This creates `MySolution.uipx` in the current directory.

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
uip solution deploy run -n "<deployment-name>" -c "<configuration-key>" [options] --output json
```

| Option | Description | Default |
|---|---|---|
| `-n, --name <name>` | Name for the deployment (required) | -- |
| `-c, --configuration-key <key>` | Configuration key (required) | -- |
| `-f, --folder-path <path>` | Fully qualified folder path (e.g. 'Shared') | -- |
| `-k, --folder-key <guid>` | Installation folder key (GUID) | -- |
| `--no-force-activate` | Disable force activation | Force activate |
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--poll-interval <ms>` | Polling interval for status | 2000 |

### Check Deployment Status

```bash
uip solution deploy status "<deployment-key>" --output json
```

### List Published Packages

```bash
uip solution packages list --output json
```

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

