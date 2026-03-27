---
name: uipath-maestro
description: "[EXPERIMENTAL] End-to-end toolkit for UiPath Maestro: create a Maestro project from a .bpmn file, pack it, upload to Orchestrator, create a release, run the job, and monitor it. TRIGGER when: User wants to create and run a Maestro process; User mentions 'create and run maestro', 'end-to-end maestro', 'deploy and run bpmn', 'maestro init', 'maestro pack', 'maestro process'; User wants the full pipeline from maestro init to job execution; User asks about uip maestro CLI commands, BPMN orchestration, entry-points.json, or Maestro project lifecycle. DO NOT TRIGGER when: User is working with Flow projects (.flow files — use uipath-flow instead); User is working with coded workflows (.cs files — use uipath-coded-workflows instead); User is working with XAML/RPA workflows (use uipath-rpa-workflows instead); User asks about Orchestrator management without Maestro context (use uipath-platform instead); User is working with coded apps (use uipath-coded-apps instead)."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
disable-model-invocation: true
---

# UiPath Maestro

Comprehensive guide for creating, packaging, publishing, deploying, running, and monitoring UiPath Maestro processes using the `uip` CLI.

## When to Use This Skill

- User wants to **create a Maestro project** from a `.bpmn` file with `uip maestro init`
- User wants to **pack a Maestro project** into a `.nupkg` for Orchestrator
- User wants to **publish, deploy, and run** a Maestro process end-to-end
- User wants to **monitor a running Maestro job** and check traces or status
- User asks about `uip maestro` commands, `.bpmn` orchestration, or the Maestro project lifecycle
- User mentions "create and run maestro", "end-to-end maestro", or "deploy and run bpmn"

## Critical Rules

- **Always check login status before any cloud command.** Run `uip login status --output json` first. If not authenticated, ask the user for their environment and run `uip login`.
- **The Maestro project must reside inside the solution folder.** Create the solution first with `uip solution new`, then init the Maestro project inside it. If the project is outside the solution folder, `solution project add` will fail with "must reside within".
- **Pack before publish, publish before deploy.** The commands form a pipeline — each step depends on the previous one producing its output.
- **Maestro project files live at the project root** (e.g., `<projectName>.bpmn`, `entry-points.json`, `package-descriptor.json`), NOT in a `content/` subfolder. This differs from Flow projects which use a `content/` folder.
- **Version must be bumped for re-publish.** If the same version already exists in Orchestrator, publish will fail. Bump the version in the `pack` step.
- **`uip maestro process list` requires `--folder-key`** — it is not optional.
- **`uip maestro job status` requires `--folder-key`** — it is not optional.
- **Do NOT run jobs without explicit user consent** — running a Maestro process executes real automations.
- **Always use `--output json`** when you need to parse output programmatically.

## Lifecycle Stages

| Stage | Description | CLI Command |
|-------|-------------|-------------|
| **Auth** | Authenticate with UiPath Cloud | `uip login` |
| **Solution New** | Create a solution container | `uip solution new <name>` |
| **Init** | Create a Maestro project | `uip maestro init <name>` |
| **Pack** | Package project into `.nupkg` | `uip maestro pack <project> <output> --version <v>` |
| **Add Project** | Add project to solution | `uip solution project add <project> <solution>` |
| **Solution Pack** | Package solution into `.zip` | `uip solution pack <solution> <output>` |
| **Publish** | Upload solution to Orchestrator | `uip solution publish <zip>` |
| **Configure** | Create a configuration (API call) | Direct API call (no CLI yet) |
| **Deploy Config** | Generate deploy config file | `uip solution deploy config <name>` |
| **Deploy** | Deploy solution to Orchestrator | `uip solution deploy run` |
| **Run** | Execute the Maestro process | `uip maestro process run` |
| **Monitor** | Check job traces and status | `uip maestro job traces` / `uip maestro job status` |

## Quick Start

These steps are for **creating and running a Maestro process end-to-end**. For individual operations, use the [Task Navigation](#task-navigation) or the [CLI Command Reference](references/commands-reference.md).

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?". Execute the entire flow automatically. Only pause when you genuinely need information from the user (auth credentials, project name, BPMN file). After getting that info, resume immediately.**

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Authenticate

```bash
uip login status --output json
```

If the response shows `"Status": "Logged in"` and the expiration date is in the future, **skip to Step 2**. Display the current org/tenant info and proceed.

**Only if NOT logged in (or session expired)**, ask the user which environment they want to use:

| Environment | Authority URL |
|-------------|--------------|
| Production (default) | `https://cloud.uipath.com` |
| Alpha | `https://alpha.uipath.com` |
| Staging | `https://staging.uipath.com` |

Present this as a question using AskUserQuestion with options: "Production", "Alpha", "Staging", and let them also type a custom URL.

Once the user selects an environment, run:

```bash
# For production (no --authority needed):
uip login

# For alpha:
uip login --authority https://alpha.uipath.com

# For staging:
uip login --authority https://staging.uipath.com
```

**Important:** The login command opens a browser and may prompt for interactive folder selection. Let it run with a generous timeout (120s). Confirm login succeeded by checking the output or re-running `uip login status --output json`.

### Step 2 — Create Solution and Maestro Project

Ask the user for:
- **Project name** — alphanumeric, underscores, and hyphens only (e.g., `MyMaestroProcess`)
- **Directory** — where to create everything (default: `/tmp/maestro-<name>`)
- **BPMN file** — optional path to an existing `.bpmn` file to use

If the user hasn't specified a solution name, derive one from the project name (e.g., `<projectName>_solution`).

```bash
mkdir -p <directory>

# Create the solution first
cd <directory> && uip solution new <solutionName>

# Create the maestro project INSIDE the solution folder
cd <directory>/<solutionName> && uip maestro init <projectName>
```

If the user provided a `.bpmn` file, replace the generated one:

```bash
cp <userBpmnFile> <directory>/<solutionName>/<projectName>/<projectName>.bpmn
```

**Entry-points.json is auto-populated** by `maestro init`. The generated entry-points.json includes `filePath`, `uniqueId`, `type: "processorchestration"`, input/output structures, and `displayName: "Manual trigger"`. No manual editing needed.

### Step 3 — Pack the Maestro Project

```bash
mkdir -p <directory>/output
uip maestro pack <directory>/<solutionName>/<projectName> <directory>/output --version <version>
```

Default version is `1.0.0`. If redeploying, bump the version (e.g., `1.0.1`, `1.0.2`).

This produces a `.nupkg` file with the naming pattern: `<projectName>.processOrchestration.ProcessOrchestration.<version>.nupkg`

### Step 4 — Add Project to Solution

```bash
uip solution project add \
  <directory>/<solutionName>/<projectName> \
  <directory>/<solutionName>/<solutionName>.uipx
```

A warning about `SolutionsMetadataReader` is benign and can be ignored.

### Step 5 — Pack the Solution

```bash
mkdir -p <directory>/solution-output
uip solution pack <directory>/<solutionName> <directory>/solution-output
```

This produces a `.zip` file for publishing.

### Step 6 — Publish to Orchestrator

```bash
uip solution publish <directory>/solution-output/<solutionZipFile> --output json
```

Record the `PackageVersionKey` from the response — it is needed to create a configuration.

### Step 7 — Create a Configuration

There is no CLI command for this yet. Use the auth file and a direct API call:

```bash
source ~/.uipath/.auth && \
BASE_URL="${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/${UIPATH_TENANT_NAME}/automationsolutions_" && \
curl -s -X POST "${BASE_URL}/api/configurations" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"packageVersionKey":"<PACKAGE_VERSION_KEY>","name":"<configName>"}'
```

The response is a quoted GUID string — this is the **configuration key**. Save it for deploy.

### Step 8 — Generate Deploy Configuration and Deploy

First, generate the default deploy configuration file:

```bash
uip solution deploy config <solutionName> --package-version <version> -d <directory>/deploy-config.json --output json
```

Then deploy using `--config-file` (there is NO `--configuration-key` option):

```bash
uip solution deploy run \
  --name "<deploymentName>" \
  --package-name "<solutionName>" \
  --package-version "<version>" \
  --folder-name "<projectName>_folder" \
  --folder-path "Shared" \
  --config-file <directory>/deploy-config.json \
  --output json
```

This command polls automatically and returns a terminal status. Record the `DeploymentKey` from the response.

**Terminal statuses:**
- `DeploymentSucceeded` / `SuccessfulInstall` / `SuccessfulActivate` — proceed to next step
- `FailedInstall` / `FailedUpgrade` — stop and report the error

### Step 9 — Find the Deployed Process

After successful deployment, find the folder key for the newly created folder, then list Maestro processes in it.

```bash
uip or folders list --filter "contains(FullyQualifiedName, '<projectName>_folder')" --output json
```

Record the `Key` (folder key) and `Id` (folder ID). Then list processes:

```bash
uip maestro process list --folder-key "<folderKey>" --output json
```

Record `processKey`, `releaseKey`, and `folderKey` from the response.

### Step 10 — Run the Maestro Process

```bash
uip maestro process run "<processKey>" "<folderKey>" \
  --release-key "<releaseKey>" \
  --output json
```

Record the `jobKey` from the response.

### Step 11 — Monitor and Verify Job

First try streaming traces:

```bash
uip maestro job traces "<jobKey>" --output json
```

If traces return an error or are unavailable, fall back to polling job status (requires `--folder-key`):

```bash
uip maestro job status "<jobKey>" --folder-key "<folderKey>" --output json
```

Parse the response — look for the `state` field in `Data`:
- `"Successful"` — job completed successfully. Report `startTime`, `endTime`, and duration.
- `"Faulted"` — job failed. Report the error info from `Data.info`.
- `"Pending"` / `"Running"` — job still in progress. Wait 10-15 seconds and check again. Maestro jobs with gateways may take longer than simple flows.

**Important:** The outer `"Result": "Success"` only means the API call succeeded. The actual job state is inside `Data.state`.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Create a Maestro project** | [Step 2](#step-2--create-solution-and-maestro-project), [references/commands-reference.md](references/commands-reference.md) |
| **Pack and publish** | [Steps 3-6](#step-3--pack-the-maestro-project), [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Deploy a solution** | [Steps 7-8](#step-7--create-a-configuration), [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Run a Maestro process** | [Steps 9-10](#step-9--find-the-deployed-process), [references/run-and-monitor.md](references/run-and-monitor.md) |
| **Monitor job status** | [Step 11](#step-11--monitor-and-verify-job), [references/run-and-monitor.md](references/run-and-monitor.md) |
| **Full CLI command reference** | [references/commands-reference.md](references/commands-reference.md) |
| **Manage Orchestrator resources** | [/uipath:uipath-platform](/uipath:uipath-platform) |

## Summary Table

After all steps complete, present a recap table:

| Step | Status | Details |
|------|--------|---------|
| Login | - | Org/Tenant info |
| Solution New | - | Solution file path |
| Init | - | Project path |
| Pack | - | NuGet path |
| Add Project | - | Project added |
| Solution Pack | - | Solution zip path |
| Publish | - | PackageVersionKey |
| Configuration | - | Configuration key |
| Deploy Config | - | Config file path |
| Deploy | - | Deployment key + status |
| Run Job | - | Job key |
| Job Result | - | Successful / duration |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Login fails | Invalid credentials or expired session | Check credentials or try a different environment |
| Init fails | Directory exists or invalid project name | Use `--force`, or fix invalid characters in name |
| Pack fails | Missing `package-descriptor.json` or `operate.json` | Verify files exist at the project root |
| `solution project add` fails with "must reside within" | Project directory is outside the solution folder | Re-create: solution first, then init project inside it |
| Publish fails | Expired token or missing permissions | Re-run `uip login`, verify tenant permissions |
| Configuration creation fails | Invalid `packageVersionKey` or stale auth | Verify the key is valid and token is current |
| Deploy config fails | Package name/version mismatch | Verify name and version match what was published |
| Deploy fails | Bad config file, folder path, or permissions | Check package name/version, folder path, config file |
| Deployment stays in progress too long | Complex orchestration or infrastructure issue | After 5 minutes, warn user and ask if they want to continue |
| Process not found after deploy | Activation delay | Wait a moment and re-list processes |
| Job run fails | Invalid release key or missing folder permissions | Check release key, folder permissions, process state |
| Job faults | Process error | Show error info from `Data.info` and suggest checking traces |
| Version already exists | Same version published before | Bump the version in the `pack` step |

## Important Notes

- Always use `uip` (the globally installed CLI), not `bun ./packages/cli/index.ts`
- Use `--output json` when you need to parse output programmatically
- The login command is interactive (opens browser) — allow sufficient timeout (120s)
- If any step fails, stop and report the error before proceeding to the next step
- The configuration creation step uses a direct API call because there is no CLI command for it yet
- The `uip solution deploy run` command does NOT have a `--configuration-key` option. Use `--config-file` with a JSON file generated by `uip solution deploy config`

## References

- **[CLI Command Reference](references/commands-reference.md)** — Every `uip maestro` and `uip solution` command with parameters and examples
- **[Pack / Publish / Deploy Guide](references/pack-publish-deploy.md)** — Full deployment pipeline from pack to deploy
- **[Run and Monitor Guide](references/run-and-monitor.md)** — Running Maestro processes and monitoring job status
- **[Platform Operations](/uipath:uipath-platform)** — Authentication, Orchestrator, solutions (uipath-platform skill)
