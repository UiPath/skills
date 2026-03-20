# Test Manager Tool Guide

Comprehensive guide for the UiPath Test Manager CLI tool (`uip tm`) — managing test projects, test sets, test cases, executions, results, reports, and attachments.

## Overview

The Test Manager tool provides CLI access to UiPath Test Manager for organizing and executing test automation. All commands use the `tm` prefix and require authentication (`uip login`).

```
uip tm
  ├── project
  │     ├── list              ← List test projects
  │     ├── create            ← Create test project
  │     ├── update            ← Update project name/description
  │     ├── delete            ← Delete a project
  │     ├── set-default-folder← Set default Orchestrator folder
  │     └── clear-default-folder ← Clear default folder
  ├── testset
  │     ├── list              ← List test sets in a project
  │     ├── create            ← Create test set
  │     ├── update            ← Update test set
  │     ├── delete            ← Delete test set
  │     ├── add-testcases     ← Add test cases to set
  │     ├── remove-testcases  ← Remove test cases from set (BUGGY)
  │     ├── list-testcases    ← List test cases in a set (BUGGY)
  │     └── execute           ← Execute a test set
  ├── testcase
  │     ├── list              ← List test cases
  │     ├── create            ← Create test case
  │     ├── update            ← Update test case (BUGGY)
  │     ├── delete            ← Delete test case
  │     ├── link-automation   ← Link Orchestrator automation
  │     ├── unlink-automation ← Unlink automation
  │     ├── list-testsets     ← List test sets containing case (BUGGY)
  │     └── list-automations  ← List available test entry points
  ├── execution     ← Test execution management and retry
  ├── wait          ← Wait for execution to reach terminal state
  ├── result        ← Test execution results
  ├── report        ← Test execution reports
  └── attachment    ← Test execution attachments
```

> **Always use `--format json`** when calling commands programmatically.

---

## Global Options

All `uip tm` commands accept:

| Option | Description | Default |
|--------|-------------|---------|
| `-t, --tenant <name>` | Tenant override | Current tenant |
| `--log-level <level>` | Logging level | Information |
| `--format <format>` | Output format (table, json, yaml, plain) | table |

---

## Projects

Test projects are top-level containers that organize all test artifacts (test sets, test cases, results).

### `uip tm project list`

List all test projects.

```bash
uip tm project list [options] --format json
```

| Option | Description |
|--------|-------------|
| `--filter <text>` | Filter projects by name |

**Example:**
```bash
uip tm project list --format json
uip tm project list --filter "Invoice" --format json
```

### `uip tm project create`

Create a new test project.

```bash
uip tm project create --name <name> --project-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--name <name>` | Project display name | Yes |
| `--project-key <key>` | Unique project key (e.g., MYPROJ) | Yes |
| `--description <text>` | Project description | No |

**Examples:**
```bash
# Create a test project
uip tm project create --name "Invoice Automation Tests" --project-key "INVTEST" --format json

# With description
uip tm project create \
  --name "Order Processing Tests" \
  --project-key "ORDTEST" \
  --description "End-to-end tests for order processing workflows" \
  --format json
```

### `uip tm project update`

Update project name or description.

> **NOTE:** May fail with RBAC error on some tenants.

```bash
uip tm project update --project-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Project key | Yes |
| `--name <name>` | New project name | No |
| `--description <text>` | New project description | No |

**Example:**
```bash
uip tm project update --project-key "INVTEST" --name "Invoice Tests v2" --format json
```

### `uip tm project delete`

Delete a test project.

```bash
uip tm project delete --project-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Project key to delete | Yes |

**Example:**
```bash
uip tm project delete --project-key "INVTEST" --format json
```

### `uip tm project set-default-folder`

Set the default Orchestrator folder for a project.

```bash
uip tm project set-default-folder --project-key <key> --folder-key <uuid> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Project key | Yes |
| `--folder-key <uuid>` | Orchestrator folder key (UUID) | Yes |

**Example:**
```bash
uip tm project set-default-folder \
  --project-key "INVTEST" \
  --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --format json
```

### `uip tm project clear-default-folder`

Clear the default Orchestrator folder for a project.

```bash
uip tm project clear-default-folder --project-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Project key | Yes |

**Example:**
```bash
uip tm project clear-default-folder --project-key "INVTEST" --format json
```

---

## Test Sets

Test sets group test cases for batch execution.

### `uip tm testset list`

List test sets in a project.

```bash
uip tm testset list --project-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--folder-key <uuid>` | Filter by Orchestrator folder key | No |
| `--filter <text>` | Filter by name | No |

**Example:**
```bash
uip tm testset list --project-key "INVTEST" --format json
uip tm testset list --project-key "INVTEST" --filter "Smoke" --format json
```

### `uip tm testset create`

Create a new test set within a project.

```bash
uip tm testset create --project-key <key> --name <name> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--name <name>` | Test set name | Yes |
| `--description <text>` | Test set description | No |

**Example:**
```bash
uip tm testset create \
  --project-key "INVTEST" \
  --name "Smoke Tests" \
  --description "Quick validation of critical invoice flows" \
  --format json
```

### `uip tm testset delete`

Delete a test set.

```bash
uip tm testset delete --test-set-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`, e.g., `INVTEST:42`) | Yes |

**Example:**
```bash
uip tm testset delete --test-set-key "INVTEST:42" --format json
```

### `uip tm testset update`

Update a test set's name or description.

```bash
uip tm testset update --test-set-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`) | Yes |
| `--name <name>` | New test set name | No |
| `--description <text>` | New test set description | No |

**Example:**
```bash
uip tm testset update --test-set-key "INVTEST:42" --name "Regression Suite v2" --format json
```

### `uip tm testset add-testcases`

Add test cases to a test set.

```bash
uip tm testset add-testcases --test-set-key <key> --test-case-keys <keys> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`) | Yes |
| `--test-case-keys <keys>` | Comma-separated test case keys (e.g., `DEMO:1,DEMO:2`) | Yes |

**Example:**
```bash
uip tm testset add-testcases \
  --test-set-key "INVTEST:42" \
  --test-case-keys "INVTEST:1,INVTEST:2,INVTEST:3" \
  --format json
```

### `uip tm testset remove-testcases`

Remove test cases from a test set.

> **BUG:** Currently fails with tool error: `testSetsApi.testSetsUnassignTestCases is not a function` (test-manager-tool 0.1.2).

```bash
uip tm testset remove-testcases --test-set-key <key> --test-case-keys <keys> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`) | Yes |
| `--test-case-keys <keys>` | Comma-separated test case keys to remove | Yes |

**Example:**
```bash
uip tm testset remove-testcases \
  --test-set-key "INVTEST:42" \
  --test-case-keys "INVTEST:1,INVTEST:2" \
  --format json
```

### `uip tm testset list-testcases`

List test cases assigned to a test set.

> **BUG:** Currently fails with tool error: `testSetsApi.testSetsGetAssignedTestCaseIds is not a function` (test-manager-tool 0.1.2).

```bash
uip tm testset list-testcases --test-set-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`) | Yes |

**Example:**
```bash
uip tm testset list-testcases --test-set-key "INVTEST:42" --format json
```

### `uip tm testset execute`

Execute a test set and return an execution ID.

```bash
uip tm testset execute --test-set-key <key> [options] --format json
```

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--test-set-key <key>` | Test set key (format: `PROJECT:ID`) | Yes | -- |
| `--execution-type <type>` | Execution type: automated, manual, mixed, none | No | automated |
| `--input-path <file>` | Path to JSON file with parameter overrides | No | -- |

**Example:**
```bash
# Basic execution
uip tm testset execute --test-set-key "INVTEST:42" --format json

# With execution type and input parameters
uip tm testset execute \
  --test-set-key "INVTEST:42" \
  --execution-type automated \
  --input-path ./test-params.json \
  --format json
```

---

## Test Cases

Individual test cases within a project.

### `uip tm testcase create`

Create a new test case.

```bash
uip tm testcase create --project-key <key> --name <name> [options] --format json
```

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--project-key <key>` | Parent project key | Yes | -- |
| `--name <name>` | Test case name | Yes | -- |
| `--description <text>` | Test case description | No | -- |
| `--version <version>` | Test case version | No | 1.0.0 |

**Example:**
```bash
uip tm testcase create \
  --project-key "INVTEST" \
  --name "Validate Invoice Total Calculation" \
  --description "Verify that invoice line items sum to the correct total" \
  --format json
```

### `uip tm testcase list`

List test cases in a project.

```bash
uip tm testcase list --project-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--filter <text>` | Filter by name | No |

**Example:**
```bash
uip tm testcase list --project-key "INVTEST" --format json
uip tm testcase list --project-key "INVTEST" --filter "Invoice" --format json
```

### `uip tm testcase delete`

Delete a test case.

```bash
uip tm testcase delete --project-key <key> --test-case-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--test-case-key <key>` | Test case key (format: `PROJECT:ID`) | Yes |

**Example:**
```bash
uip tm testcase delete --project-key "INVTEST" --test-case-key "INVTEST:5" --format json
```

### `uip tm testcase update`

Update a test case's name or description.

> **BUG:** Currently fails with tool error: `testCasesApi.testCasesPatch is not a function` (test-manager-tool 0.1.2).

```bash
uip tm testcase update --project-key <key> --test-case-key <key> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--test-case-key <key>` | Test case key (format: `PROJECT:ID`) | Yes |
| `--name <name>` | New test case name | No |
| `--description <text>` | New test case description | No |

**Example:**
```bash
uip tm testcase update \
  --project-key "INVTEST" \
  --test-case-key "INVTEST:5" \
  --name "Validate Invoice Total v2" \
  --format json
```

### `uip tm testcase link-automation`

Link an Orchestrator package automation to a test case.

```bash
uip tm testcase link-automation --project-key <key> --test-case-key <key> --folder-key <uuid> --package-name <name> --test-name <name> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--test-case-key <key>` | Test case key (format: `PROJECT:ID`) | Yes |
| `--folder-key <uuid>` | Orchestrator folder key (UUID) | Yes |
| `--package-name <name>` | Orchestrator package name | Yes |
| `--test-name <name>` | Test entry point name within the package | Yes |

**Example:**
```bash
uip tm testcase link-automation \
  --project-key "INVTEST" \
  --test-case-key "INVTEST:5" \
  --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --package-name "InvoiceTests" \
  --test-name "ValidateInvoiceTotal" \
  --format json
```

### `uip tm testcase unlink-automation`

Unlink automation from a test case.

```bash
uip tm testcase unlink-automation --project-key <key> --test-case-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--test-case-key <key>` | Test case key (format: `PROJECT:ID`) | Yes |

**Example:**
```bash
uip tm testcase unlink-automation \
  --project-key "INVTEST" \
  --test-case-key "INVTEST:5" \
  --format json
```

### `uip tm testcase list-testsets`

List test sets that contain a given test case.

> **BUG:** Currently fails with tool error: `testCasesApi.testCasesGetAssignedTestSets is not a function` (test-manager-tool 0.1.2).

```bash
uip tm testcase list-testsets --project-key <key> --test-case-key <key> --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--test-case-key <key>` | Test case key (format: `PROJECT:ID`) | Yes |

**Example:**
```bash
uip tm testcase list-testsets --project-key "INVTEST" --test-case-key "INVTEST:5" --format json
```

### `uip tm testcase list-automations`

List available test entry points in an Orchestrator folder.

```bash
uip tm testcase list-automations --project-key <key> --folder-key <uuid> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--project-key <key>` | Parent project key | Yes |
| `--folder-key <uuid>` | Orchestrator folder key (UUID) | Yes |
| `--package-name <name>` | Filter by package name | No |

**Example:**
```bash
uip tm testcase list-automations \
  --project-key "INVTEST" \
  --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --format json

# Filter by package
uip tm testcase list-automations \
  --project-key "INVTEST" \
  --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --package-name "InvoiceTests" \
  --format json
```

---

## Executions

Test execution management — run test sets and retry failed executions.

### `uip tm execution retry`

Retry a failed or partial test execution.

```bash
uip tm execution retry --execution-id <uuid> [options] --format json
```

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--execution-id <uuid>` | Execution ID to retry | Yes | -- |
| `--project-key <key>` | Project key | No | -- |
| `--test-set-key <key>` | Test set key | No | -- |
| `--execution-type <type>` | Execution type: automated, manual, mixed, none | No | automated |

**Example:**
```bash
uip tm execution retry \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --execution-type automated \
  --format json
```

---

## Wait

Wait for a test execution to reach a terminal state before proceeding.

### `uip tm wait`

Wait for an execution to complete, fail, or time out.

```bash
uip tm wait --execution-id <uuid> [options] --format json
```

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--execution-id <uuid>` | Execution ID to wait for | Yes | -- |
| `--project-key <key>` | Project key | No | -- |
| `--test-set-key <key>` | Test set key | No | -- |
| `--timeout <seconds>` | Timeout in seconds (0 = no timeout) | No | 1800 (30 min) |

**Examples:**
```bash
# Wait with default timeout (30 minutes)
uip tm wait --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" --format json

# Wait with custom timeout
uip tm wait \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --timeout 600 \
  --format json

# Wait with no timeout
uip tm wait \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --timeout 0 \
  --format json
```

---

## Results

Download and inspect test execution results.

### `uip tm result download`

Download results from a test execution.

```bash
uip tm result download --execution-id <uuid> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--execution-id <uuid>` | Execution ID | Yes |
| `--project-key <key>` | Project key | No |
| `--test-set-key <key>` | Test set key | No |
| `--result-path <path>` | Local path to save results | No |

**Example:**
```bash
uip tm result download \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --result-path ./test-results/ \
  --format json
```

---

## Reports

Generate and retrieve test execution reports.

### `uip tm report get`

Get a report for a test execution.

```bash
uip tm report get --execution-id <uuid> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--execution-id <uuid>` | Execution ID | Yes |
| `--project-key <key>` | Project key | No |
| `--test-set-key <key>` | Test set key | No |
| `--query <expr>` | jq-style filter expression for output | No |

**Examples:**
```bash
# Full report
uip tm report get --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" --format json

# Filtered report (jq-style)
uip tm report get \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --query ".testCases[] | select(.status == \"Failed\")" \
  --format json
```

---

## Attachments

Download attachments (screenshots, logs, etc.) from test executions.

### `uip tm attachment download`

Download attachments from a test execution.

```bash
uip tm attachment download --execution-id <uuid> [options] --format json
```

| Option | Description | Required |
|--------|-------------|----------|
| `--execution-id <uuid>` | Execution ID | Yes |
| `--project-key <key>` | Project key | No |
| `--test-set-key <key>` | Test set key | No |
| `--test-case-name <name>` | Filter by test case name (repeatable) | No |
| `--only-failed` | Download attachments only for failed test cases | No |
| `--result-path <path>` | Local path to save attachments | No |

**Examples:**
```bash
# Download all attachments
uip tm attachment download \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --result-path ./attachments/ \
  --format json

# Only failed test cases
uip tm attachment download \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --only-failed \
  --result-path ./failed-attachments/ \
  --format json

# Specific test cases
uip tm attachment download \
  --execution-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --test-case-name "ValidateInvoiceTotal" \
  --test-case-name "ValidatePaymentFlow" \
  --result-path ./attachments/ \
  --format json
```

---

## Common Patterns

### Setting Up a Test Project

```bash
# 1. Create a project
uip tm project create --name "Invoice Tests" --project-key "INV" --format json

# 2. Create test cases
uip tm testcase create --project-key "INV" --name "Validate Invoice Creation" --format json
uip tm testcase create --project-key "INV" --name "Validate Invoice Approval" --format json
uip tm testcase create --project-key "INV" --name "Validate Invoice Payment" --format json

# 3. Create a test set
uip tm testset create --project-key "INV" --name "Regression Suite" --format json

# 4. Add test cases to the test set
uip tm testset add-testcases --test-set-key "INV:1" --test-case-keys "INV:1,INV:2,INV:3" --format json

# 5. Execute the test set and wait for results
uip tm testset execute --test-set-key "INV:1" --format json
uip tm wait --execution-id "<EXEC_ID>" --format json
```

### Reviewing Failed Test Results

```bash
# 1. Get the execution report
uip tm report get --execution-id "<EXEC_ID>" --format json

# 2. Download results for analysis
uip tm result download --execution-id "<EXEC_ID>" --result-path ./results/ --format json

# 3. Download screenshots from failed tests
uip tm attachment download \
  --execution-id "<EXEC_ID>" \
  --only-failed \
  --result-path ./failed-screenshots/ \
  --format json

# 4. Retry the execution
uip tm execution retry --execution-id "<EXEC_ID>" --format json
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Project key conflict | Project key already exists | Use a unique project key |
| Execution not found | Invalid execution ID | Verify the execution ID from the execution list |
| Invalid test-set-key format | Missing PROJECT:ID format | Use format `PROJECTKEY:NUMBER` (e.g., `INV:42`) |
| No attachments found | Test case didn't produce attachments | Check if the automation captures screenshots/logs |
| RBAC error on project update | Insufficient permissions on tenant | Check tenant RBAC settings and user roles |

### Known Bugs (test-manager-tool 0.1.2)

| Command | Error | Status |
|---------|-------|--------|
| `uip tm testcase update` | `testCasesApi.testCasesPatch is not a function` | Bug in test-manager-tool 0.1.2 |
| `uip tm testset list-testcases` | `testSetsApi.testSetsGetAssignedTestCaseIds is not a function` | Bug in test-manager-tool 0.1.2 |
| `uip tm testset remove-testcases` | `testSetsApi.testSetsUnassignTestCases is not a function` | Bug in test-manager-tool 0.1.2 |
| `uip tm testcase list-testsets` | `testCasesApi.testCasesGetAssignedTestSets is not a function` | Bug in test-manager-tool 0.1.2 |
