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
uipcli solution new "MySolution" --format json
```

This creates `MySolution.uipx` in the current directory.

### 2. Add Projects to the Solution

Add existing automation projects to the solution:

```bash
# Add a project (auto-discovers nearest .uipx)
uipcli solution project add ./ProjectA --format json

# Add with explicit solution file
uipcli solution project add ./ProjectB ./MySolution.uipx --format json
```

The project folder must contain `project.uiproj` or `project.json`.

### 3. Remove Projects from a Solution

```bash
uipcli solution project remove ./ProjectA --format json
```

### 4. Pack the Solution

Pack the solution into a deployable .zip package:

```bash
uipcli solution pack ./MySolution ./output --format json
```

With version and custom name:

```bash
uipcli solution pack ./MySolution ./output --name "MySolution" --version "2.0.0" --format json
```

### 5. Publish the Package

Upload the packed solution to UiPath (requires authentication):

```bash
uipcli login --format json
uipcli solution publish ./output/MySolution.1.0.0.zip --format json
```

With tenant and location override:

```bash
uipcli solution publish ./output/MySolution.1.0.0.zip --tenant "Production" --format json
```

---

## Solution Deployment (In Progress)

The following commands are being actively developed and will enable full solution deployment lifecycle:

### Deploy a Solution

Deploy supports three input modes:

**From source directory (auto-packs):**
```bash
uipcli solution deploy --folder "Finance" --format json
# or with explicit path:
uipcli solution deploy --path ./MySolution --folder "Finance" --format json
```

**From local package:**
```bash
uipcli solution deploy --package ./output/MySolution.1.0.0.zip --folder "Finance" --format json
```

**From previously uploaded package:**
```bash
uipcli solution deploy --name "MySolution" --version "1.0.0" --folder "Finance" --format json
```

**Key options:**

| Option | Description |
|---|---|
| `--folder <path>` | Target folder path (e.g., "Finance/Invoicing") |
| `--folder-id <id>` | Target folder ID (alternative to --folder) |
| `--deployment <name>` | Name of existing deployment to upgrade |
| `--config <path>` | Configuration file for environment-specific settings |
| `--version <ver>` | Version override |
| `--what-if` | Dry-run preview — show what would change without deploying |
| `--no-pack` | Skip auto-pack step |
| `--no-build` | Skip auto-build step |
| `--no-activate` | Deploy without activating |

### Activate a Deployment

```bash
uipcli solution activate --deployment "MySolution" --folder "Finance" --format json
```

### Check Deployment Status

```bash
uipcli solution status --deployment "MySolution" --folder "Finance" --format json
```

### List Deployed Solutions

```bash
uipcli solution list --folder "Finance" --format json
```

### Uninstall a Solution

```bash
uipcli solution uninstall --deployment "MySolution" --folder "Finance" --format json
```

### Download Configuration

```bash
uipcli solution download-config --deployment "MySolution" --folder "Finance" --output ./config.json --format json
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

      - name: Install uipcli
        run: npm install -g @uipath/cli

      - name: Authenticate
        run: |
          uipcli login \
            --client-id "${{ secrets.UIPATH_CLIENT_ID }}" \
            --client-secret "${{ secrets.UIPATH_CLIENT_SECRET }}" \
            --tenant "${{ secrets.UIPATH_TENANT }}" \
            --format json

      - name: Pack solution
        run: uipcli solution pack ./MySolution ./output --version "${{ github.sha }}" --format json

      - name: Publish solution
        run: uipcli solution publish ./output/MySolution.*.zip --format json
```

### Environment Promotion Pattern

```bash
#!/bin/bash
# promote.sh - Promote a solution package through environments

PACKAGE=$1  # e.g., ./output/MySolution.1.0.0.zip

# Deploy to Staging
echo "Deploying to Staging..."
uipcli login tenant set "Staging" --format json
uipcli solution publish "$PACKAGE" --format json

# After manual approval, deploy to Production
echo "Deploying to Production..."
uipcli login tenant set "Production" --format json
uipcli solution publish "$PACKAGE" --format json
```

---

## Common Patterns

### Full End-to-End Workflow

```bash
# 1. Create solution
uipcli solution new "InvoiceAutomation" --format json

# 2. Add projects
uipcli solution project add ./InvoiceProcessor --format json
uipcli solution project add ./InvoiceReporter --format json

# 3. Pack
uipcli solution pack . ./output --version "1.0.0" --format json

# 4. Login and publish
uipcli login --format json
uipcli login tenant set "Production" --format json
uipcli solution publish ./output/InvoiceAutomation.1.0.0.zip --format json
```

### Version Bumping

Always increment version when republishing:

```bash
# Initial release
uipcli solution pack ./MySolution ./output --version "1.0.0" --format json

# Bug fix
uipcli solution pack ./MySolution ./output --version "1.0.1" --format json

# New feature
uipcli solution pack ./MySolution ./output --version "1.1.0" --format json

# Breaking change
uipcli solution pack ./MySolution ./output --version "2.0.0" --format json
```

---

## Legacy CLI Pack & Deploy

The legacy `uipcli` (v25.10.x) uses different commands for packing and deploying:

### Pack a Project

```bash
uipcli package pack "<PROJECT_DIR>" -o "<OUTPUT_DIR>" -v "1.0.0" --traceLevel Information
```

This produces a `.nupkg` file.

**Important:** Studio locks the project database. If packing fails with "project is already opened in another Studio instance", close the project first:
```bash
rpa-tool close-project --project-dir "<PROJECT_DIR>" --format json
```

### Deploy a Package

```bash
uipcli package deploy "<NUPKG_PATH>" "<ORCHESTRATOR_URL>" "<TENANT>" \
  -A "<ORG_NAME>" \
  -I "<APPLICATION_ID>" \
  -S "<APPLICATION_SECRET>" \
  --applicationScope "OR.Folders OR.BackgroundTasks OR.Settings.Read OR.Robots.Read OR.Machines.Read OR.Execution OR.Assets OR.Users.Read OR.Jobs OR.Monitoring" \
  -o "<FOLDER_NAME>" \
  --traceLevel Information
```

### Alternative: REST API Deploy

If legacy CLI auth is not available but you have a token from the new CLI's `~/.uipcli/.env`:

```bash
source ~/.uipcli/.env

# Upload .nupkg package
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.UploadPackage" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -F "file=@./MyProject.1.0.0.nupkg"

# Create process from uploaded package
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"Name":"MyProcess","ProcessKey":"MyProject","ProcessVersion":"1.0.0"}'
```
