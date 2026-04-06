# CLI Commands Reference

Use `--output json` on all `uip` commands when parsing output.

## Agent Commands

### `uip low-code-agent init`

Scaffold a new agent project inside a solution directory.

```bash
uip low-code-agent init "<AGENT_NAME>" --output json
```

Run from the solution directory. Creates agent.json, entry-points.json, project.uiproj, and default eval/feature/resource directories.

#### `--inline` flag

Scaffold an inline agent inside a flow project directory.

```bash
uip low-code-agent init --inline --output json
```

Run from the flow project directory. Creates only agent.json, resources/, and features/ — no entry-points.json, no project.uiproj. The inline agent is governed by the parent flow project.

### `uip low-code-agent validate`

Validate agent project structure and schemas.

```bash
uip low-code-agent validate --output json
```

Run from the agent project directory. Checks schema validity and consistency between agent.json and entry-points.json. Run after every change.

#### `--inline` flag

Validate an inline agent inside a flow project.

```bash
uip low-code-agent validate --inline --output json
```

Run from the inline agent's subdirectory within the flow project. Validates agent.json without requiring entry-points.json or project.uiproj.

## Solution Commands

### Create Solution

```bash
uip solution new "<SOLUTION_NAME>" --output json
```

### Register Project with Solution

```bash
uip solution project add --project-path "<AGENT_PROJECT_DIR>" --output json
```

Run from the solution directory.

### Bundle and Upload to Studio Web

Bundle packages the solution directory into a `.uis` file; upload sends it to Studio Web.

```bash
uip solution bundle "<SOLUTION_PATH>" -d "<OUTPUT_DIR>" --output json
uip solution upload --output json
```

Run from the solution directory. Bundle first, then upload. Requires login.

### Pack Solution for Orchestrator

```bash
uip solution pack "<SOLUTION_PATH>" "<OUTPUT_DIR>" -v "<VERSION>" --output json
```

Produces a `.zip` package. Run from any directory.

### Publish Package to Orchestrator

```bash
uip solution publish "<PACKAGE_PATH>" --output json
```

Publishes the `.zip` to Orchestrator. Requires login.

### Deploy Solution

```bash
uip solution deploy run \
  --name "<DEPLOYMENT_NAME>" \
  --package-name "<SOLUTION_NAME>" \
  --package-version "<VERSION>" \
  --folder-name "<FOLDER_NAME>" \
  --folder-path "<ORCHESTRATOR_FOLDER>" \
  --output json
```

Creates folder, provisions resources, and activates. Polls until `DeploymentSucceeded`.

### Activate Existing Deployment

```bash
uip solution deploy activate "<DEPLOYMENT_NAME>" --output json
```

### Uninstall Deployment

```bash
uip solution deploy uninstall "<DEPLOYMENT_NAME>" --output json
```

## Authentication

```bash
uip login --output json          # Interactive OAuth login
uip login status --output json   # Check current auth state
```

## End-to-End Lifecycle Example

```bash
# 1. Login check
uip login status --output json

# 2. Create solution and scaffold agent
uip solution new "MySolution" --output json
cd MySolution
uip low-code-agent init "MyAgent" --output json
uip solution project add --project-path "MyAgent" --output json

# 3. Edit agent.json, then validate
cd MyAgent
uip low-code-agent validate --output json
cd ..

# 4. Bundle + upload to Studio Web (for visual development)
uip solution bundle . -d ./dist --output json
uip solution upload --output json

# 5. Pack + publish + deploy to Orchestrator
uip solution pack . ./dist -v "1.0.0" --output json
uip solution publish ./dist/MySolution.1.0.0.zip --output json
uip solution deploy run \
  --name "MySolution-prod" \
  --package-name "MySolution" \
  --package-version "1.0.0" \
  --folder-name "MySolution" \
  --folder-path "Shared" \
  --output json
```

## Quick Reference

| Task | Command | Run From |
|------|---------|----------|
| Create solution | `uip solution new "<NAME>" --output json` | Any directory |
| Scaffold agent | `uip low-code-agent init "<NAME>" --output json` | Solution directory |
| Scaffold inline agent | `uip low-code-agent init --inline --output json` | Flow project directory |
| Register project | `uip solution project add --project-path "<PATH>" --output json` | Solution directory |
| Validate | `uip low-code-agent validate --output json` | Agent project directory |
| Validate inline agent | `uip low-code-agent validate --inline --output json` | Inline agent subdirectory |
| Bundle for Studio Web | `uip solution bundle . -d ./dist --output json` | Solution directory |
| Upload to Studio Web | `uip solution upload --output json` | Solution directory |
| Pack | `uip solution pack . ./dist -v "1.0.0" --output json` | Solution directory |
| Publish | `uip solution publish ./dist/<PKG>.zip --output json` | Any directory |
| Deploy | `uip solution deploy run --name ... --output json` | Any directory |
| Activate | `uip solution deploy activate "<NAME>" --output json` | Any directory |
| Login check | `uip login status --output json` | Any directory |
