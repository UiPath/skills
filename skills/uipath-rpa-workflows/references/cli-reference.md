# CLI reference for RPA

Read this file when: you need exact CLI syntax, parameter details, or error recovery for `uip rpa` commands.

@../shared/cli-reference.md

This file covers RPA-specific commands. Shared commands are in the file above.

## Global options

These options are inherited from the `uip rpa` parent group and work on all subcommands:

| Option | Description |
|--------|-------------|
| `--project-dir <path>` | Project directory (defaults to CWD). Must contain `project.json`. |
| `--format <format>` | Output format: `json` (default), `table`, `yaml`, `plain`. Use `table` only for user display. |
| `--timeout <seconds>` | Command timeout (default 300). Place before the subcommand: `uip rpa --timeout 600 get-errors ...` |
| `--verbose` | Enable verbose logging. |

## Project commands

### create-project

Create a new UiPath project. (Note: the command is `create-project`, not `new`.)

```bash
uip rpa create-project \
  --name "MyAutomation" \
  --location "/path/to/parent/dir" \
  --template-id "BlankTemplate" \
  --expression-language "VisualBasic" \
  --target-framework "Windows" \
  --description "Automates invoice processing" \
  --format json
```

| Parameter | Required | Default | Options |
|-----------|----------|---------|---------|
| `--name` | Yes | | Project folder name |
| `--location` | No | CWD | Parent directory for the new project folder |
| `--template-id` | No | `BlankTemplate` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--expression-language` | No | Template default | `VisualBasic`, `CSharp` |
| `--target-framework` | No | Template default | `Legacy`, `Windows`, `Portable` |
| `--description` | No | | Project description |

### open-project

Open a project in Studio Desktop.

```bash
uip rpa open-project --project-dir "{projectRoot}"
```

### close-project

Close the current project in Studio.

```bash
uip rpa close-project --format json
```

### list-instances

Check if Studio Desktop is running.

```bash
uip rpa list-instances --format json
```

### start-studio

Launch Studio Desktop.

```bash
uip rpa start-studio
```

If it fails with a registry key error, pass `--studio-dir` pointing to the Studio installation directory.

## Validation and build commands

### get-errors

Validate workflows and return errors.

```bash
# Validate a specific file (faster):
uip rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --format json

# Validate entire project:
uip rpa get-errors --format json

# Use cached errors (skip re-validation):
uip rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --skip-validation --format json

# Filter by severity:
uip rpa get-errors --min-severity error --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | No | Relative path from project root (e.g., `"Workflows/Send.xaml"`). Must be relative, not absolute. |
| `--skip-validation` | No | Use cached errors. Faster but may be stale. |
| `--min-severity` | No | Filter: `error`, `warning`, `info`, `verbose`. |

### analyze

Run workflow analyzer rules on the project.

```bash
uip rpa analyze --format json
```

### build

Build the project.

```bash
uip rpa build --format json
```

### pack

Package the project into a .nupkg file.

```bash
uip rpa pack --output-dir "./output" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--output-dir` | No | Directory for the output .nupkg file |

### restore

Restore NuGet packages for the project.

```bash
uip rpa restore --project-path "{projectRoot}" --format json
```

Note: `restore` uses `--project-path`, not `--project-dir`.

### diff

Show differences between two project versions or files.

```bash
uip rpa diff --format json
```

## Package commands

### install-or-update-packages

Install or update NuGet packages. The `--packages` parameter is the only subcommand-specific option. `--project-dir` is inherited from the parent.

```bash
# Install latest version:
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Excel.Activities"}]' --format json

# Install specific version:
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Excel.Activities","version":"25.10.21"}]' --format json

# Install multiple packages:
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Excel.Activities"},{"id":"UiPath.Mail.Activities"}]' --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--packages` | Yes | JSON array of `{"id":"...","version":"..."}` objects. Omit `version` for latest. |

### get-versions

List available versions for a package.

```bash
# Include prerelease (default preference):
uip rpa get-versions --package-id "UiPath.Excel.Activities" --include-prerelease --format json

# Stable only:
uip rpa get-versions --package-id "UiPath.Excel.Activities" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--package-id` | Yes | NuGet package ID |
| `--include-prerelease` | No | Include beta/preview versions |

### inspect-package

Inspect contents of a NuGet package.

```bash
uip rpa inspect-package --package-id "UiPath.Excel.Activities" --format json
```

## Activity commands

### find-activities

Search for activities by keyword. Global search, not limited to installed packages.

```bash
uip rpa find-activities --query "send mail" --limit 10 --format json
uip rpa find-activities --query "read range" --tags "excel" --limit 20 --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--query` | Yes | Search keyword |
| `--tags` | No | Filter by tags |
| `--limit` | No | Max results (default 10) |

### get-default-activity-xaml

Get the default XAML template for an activity.

```bash
# Non-dynamic activity:
uip rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.LogMessage" --format json

# Dynamic activity (connector-backed):
uip rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id "6265de1b-4264-ed11-ade6-e42aac668fcd" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--activity-class-name` | One mode | Fully qualified class name (non-dynamic activities) |
| `--activity-type-id` | One mode | Activity type ID (dynamic activities) |
| `--connection-id` | No | Connection ID for dynamic activities |

### focus-activity

Focus an activity in the Studio designer.

```bash
# Focus specific activity:
uip rpa focus-activity --activity-id "Assign_1" --format json

# Focus all activities sequentially:
uip rpa focus-activity --format json
```

## Workflow example commands

### list-workflow-examples

Search example workflows by service tags.

```bash
uip rpa list-workflow-examples --tags "excel" --limit 10 --format json
uip rpa list-workflow-examples --tags "jira,confluence" --prefix "project-management/" --limit 15 --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--tags` | Yes | Comma-separated service tags (AND logic) |
| `--prefix` | No | Filter by name prefix |
| `--limit` | No | Max results (default 10) |

Available tags: `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`

### get-workflow-example

Retrieve full XAML content of an example workflow.

```bash
uip rpa get-workflow-example --key "email-communication/add-new-gmail-emails-to-keap-as-contacts.xaml" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--key` | Yes | Blob path from `list-workflow-examples` results |

## Execution commands

### run-file

Execute or debug a workflow file.

```bash
# Normal execution:
uip rpa run-file --file-path "Main.xaml" --format json

# Debug mode (pauses on error, required for UI automation):
uip rpa run-file --file-path "Main.xaml" --command StartDebugging --format json
```

### get-manual-test-steps

Get manual test steps for test cases.

```bash
uip rpa get-manual-test-steps --test-case-ids '["tc-001","tc-002"]' --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-ids` | Yes | JSON array of test case IDs |

## Discovery tools (non-CLI)

| Action | How |
|--------|-----|
| Explore project files | `Glob` with `**/*.xaml` pattern |
| Search XAML content | `Grep` with regex across `.xaml` files |
| Explore object repository | `Glob **/*` in `{projectRoot}/.objects/` + `Read` metadata |
| Get JIT type definitions | `Read {projectRoot}/.project/JitCustomTypesSchema.json` |
| Activity docs | `Read {projectRoot}/.local/docs/packages/{PackageId}/activities/{Name}.md` |

## Connector commands (Integration Service)

```bash
uip is activities list <connector-key> --format json       # List connector activities
uip is resources list <connector-key> --format json        # List data objects
uip is resources describe <connector-key> <object> --format json  # Describe object fields
uip is connections list <connector-key> --format json      # List connections
uip is connections ping <connection-id>                    # Verify connection health
uip is connections create <connector-key>                  # Create new connection (OAuth)
uip is connections edit <connection-id>                    # Re-authenticate
uip is connectors list --format json                      # List available connectors
```

## CLI error recovery

| Error | Cause | Fix |
|-------|-------|-----|
| IPC connection failure | Studio not running | `uip rpa start-studio` then `uip rpa open-project` |
| 401/403, "not authenticated" | Auth expired | `uip login` |
| "Package not found" | Wrong package ID | Use `uip rpa find-activities` to discover correct ID |
| Command timeout | Large project | Add `--timeout 600` before the subcommand |
| "file not found" on get-errors | Absolute path used | Use relative path from project root |
| Studio unresponsive | IPC hung | User must restart Studio manually |

Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the fix, retry once.
