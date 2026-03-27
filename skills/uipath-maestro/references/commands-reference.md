# Maestro CLI Command Reference

Complete reference for all `uip maestro` and related `uip solution` commands used in the Maestro workflow.

## Authentication

### `uip login`

Authenticate with UiPath Cloud Platform via interactive OAuth (opens browser).

```bash
uip login                                          # Production
uip login --authority https://alpha.uipath.com     # Alpha
uip login --authority https://staging.uipath.com   # Staging
```

**Important:** The login command is interactive and may prompt for folder selection. Use a generous timeout (120s).

### `uip login status`

Check current authentication status.

```bash
uip login status --output json
```

**Output fields:** `Status`, `ExpiresAt`, `Organization`, `Tenant`

---

## Maestro Project Commands

### `uip maestro init`

Create a new Maestro project. Must be run inside a solution folder.

```bash
uip maestro init <projectName>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `projectName` | Yes | Alphanumeric, underscores, hyphens only |
| `--force` | No | Overwrite existing project directory |

**Generated files:**
- `<projectName>.bpmn` — BPMN process definition
- `entry-points.json` — Auto-populated with start event details
- `package-descriptor.json` — Package metadata
- `operate.json` — Runtime configuration

### `uip maestro pack`

Package a Maestro project into a `.nupkg` file.

```bash
uip maestro pack <projectPath> <outputPath> --version <version>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `projectPath` | Yes | Path to the Maestro project directory |
| `outputPath` | Yes | Directory for the output `.nupkg` file |
| `--version` | No | Package version (default: `1.0.0`) |

**Output:** `<projectName>.processOrchestration.ProcessOrchestration.<version>.nupkg`

---

## Maestro Process Commands

### `uip maestro process list`

List Maestro processes in a folder.

```bash
uip maestro process list --folder-key "<folderKey>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--folder-key` | **Yes** | Folder GUID (from `uip or folders list`) |
| `--output` | No | Output format (`json` recommended) |

**Output fields:** `processKey`, `releaseKey`, `folderKey`

### `uip maestro process run`

Execute a Maestro process.

```bash
uip maestro process run "<processKey>" "<folderKey>" \
  --release-key "<releaseKey>" \
  --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `processKey` | Yes | Process GUID (from `process list`) |
| `folderKey` | Yes | Folder GUID (from `process list`) |
| `--release-key` | Yes | Release GUID (from `process list`) |
| `--output` | No | Output format (`json` recommended) |

**Output fields:** `jobKey`

---

## Maestro Job Commands

### `uip maestro job traces`

Stream execution traces for a running or completed job.

```bash
uip maestro job traces "<jobKey>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `jobKey` | Yes | Job GUID (from `process run`) |
| `--output` | No | Output format (`json` recommended) |

**Note:** Traces may fail or be unavailable. Always fall back to `job status`.

### `uip maestro job status`

Check the status of a Maestro job.

```bash
uip maestro job status "<jobKey>" --folder-key "<folderKey>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `jobKey` | Yes | Job GUID (from `process run`) |
| `--folder-key` | **Yes** | Folder GUID |
| `--output` | No | Output format (`json` recommended) |

**Job states (in `Data.state`):**
- `Successful` — Job completed. Check `startTime`, `endTime`.
- `Faulted` — Job failed. Check `Data.info` for error details.
- `Pending` — Job queued, not yet started.
- `Running` — Job in progress. Poll again in 10-15 seconds.

**Important:** The outer `"Result": "Success"` means the API call succeeded. The actual job state is inside `Data.state`.

---

## Solution Commands

### `uip solution new`

Create a new solution container.

```bash
uip solution new <solutionName>
```

### `uip solution project add`

Add a project to an existing solution. The project must reside inside the solution folder.

```bash
uip solution project add <projectPath> <solutionFilePath>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `projectPath` | Yes | Path to the project directory |
| `solutionFilePath` | Yes | Path to the `.uipx` solution file |

### `uip solution pack`

Package a solution into a `.zip` for publishing.

```bash
uip solution pack <solutionPath> <outputPath>
```

### `uip solution publish`

Upload a solution package to Orchestrator.

```bash
uip solution publish <zipFilePath> --output json
```

**Output fields:** `PackageVersionKey`

### `uip solution deploy config`

Generate a default deploy configuration file.

```bash
uip solution deploy config <solutionName> --package-version <version> -d <configFilePath> --output json
```

### `uip solution deploy run`

Deploy a solution to Orchestrator. Polls automatically until terminal status.

```bash
uip solution deploy run \
  --name "<deploymentName>" \
  --package-name "<solutionName>" \
  --package-version "<version>" \
  --folder-name "<folderName>" \
  --folder-path "Shared" \
  --config-file <configFilePath> \
  --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | Yes | Deployment name |
| `--package-name` | Yes | Solution package name |
| `--package-version` | Yes | Package version |
| `--folder-name` | Yes | Target folder name |
| `--folder-path` | Yes | Parent folder path (e.g., `Shared`) |
| `--config-file` | Yes | Path to deploy config JSON file |
| `--output` | No | Output format (`json` recommended) |

**Note:** There is NO `--configuration-key` option. Use `--config-file` instead.

**Terminal statuses:** `DeploymentSucceeded`, `SuccessfulInstall`, `SuccessfulActivate`, `FailedInstall`, `FailedUpgrade`

**Output fields:** `DeploymentKey`

---

## Orchestrator Folder Commands

### `uip or folders list`

List Orchestrator folders with optional filtering.

```bash
uip or folders list --filter "contains(FullyQualifiedName, '<folderName>')" --output json
```

**Output fields:** `Key` (folder GUID), `Id` (folder numeric ID), `FullyQualifiedName`
