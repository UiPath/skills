# Run UiPath Agents

Execute agents locally for testing or invoke published agents in UiPath Cloud.

## Quick Reference

```bash
# Run locally — ENTRYPOINT is the name from entry-points.json, NOT the project name
uip codedagents run <ENTRYPOINT> '{"query": "test"}'

# Run with file input
uip codedagents run <ENTRYPOINT> --file input.json

# Invoke published agent in cloud
uip codedagents invoke <ENTRYPOINT> '{"query": "test"}'
```

**IMPORTANT:** The entrypoint name comes from `entry-points.json` (e.g., `main`, `agent`). It is NOT the project or package name. Check `entry-points.json` for the correct name.

## Documentation

- **[Running Agents Guide](running-agents.md)** — Complete execution reference
  - Run vs Invoke comparison
  - Agent discovery from `entry-points.json`
  - Input collection and schema validation
  - Result display and error handling
  - Cloud execution with monitoring URLs

## Prerequisites

- `entry-points.json` must exist (run `uip codedagents init` if missing)
- For `invoke`: agent must be published and auth configured

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Authorization required. Please run uipath auth` | Not authenticated before running | Run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` first |
| `UIPATH_ORGANIZATION_ID...is required` | Missing org ID env variable (OpenAI Agents) | Ensure `.env` has `UIPATH_ORGANIZATION_ID` set after auth |
| `Invalid input` | JSON doesn't match Input schema | Check `entry-points.json` for expected fields and types |
| `Error during initialization: File not found: main` | `main.py` missing or not in project root | Create `main.py` in the project root directory |

## Additional Instructions

- Read the [running agents reference](running-agents.md) before making assumptions about run/invoke behavior.

---

# Running UiPath Agents

Execute your UiPath agent locally or in the cloud.

## Run vs Invoke

| Aspect | Run (Local) | Invoke (Cloud) |
|--------|-----------|---|
| **Purpose** | Test agents locally during development | Execute deployed agents in UiPath Cloud |
| **Location** | Your machine | UiPath Cloud workspace |
| **When to Use** | Before deployment, debugging, testing | After publishing to the cloud |
| **Command** | `uip codedagents run` | `uip codedagents invoke` |
| **Requirements** | Local project setup | Published agent in workspace |

---

## Run (Local Execution)

Test your agent locally before deploying to the cloud.

### Project Verification

Before running an agent, your project should have:
- `uipath.json` - Project configuration
- `entry-points.json` - Agent entry points with schemas

If missing, create an agent first using `uip codedagents new` and `uip codedagents init`.

### Agent Discovery

The tool reads `entry-points.json` to find all available agents and their schemas:
- **File path** and **entry point** (e.g., main.py:main)
- **Input schema** with field types and descriptions
- **Output schema** with expected return fields

If multiple agents exist, you'll be prompted to select one.

### Input Collection

The skill parses the agent's JSON schema and generates interactive prompts for each input field:

**For simple types:**
```
Enter field_name (number) - Description: 42
Enter description (string) - Agent input: hello
```

**For enums:**
```
Select action (string) - Choose an action:
  1. process
  2. analyze
  3. export
Choice: 1
```

**For optional fields:**
```
Enter description (string) - Optional agent description [press Enter to skip]:
```

### Execution

Your agent runs locally with:
```bash
uip codedagents run <entrypoint> '<json-input>'
```

The agent runs with your provided inputs and returns structured output.

> **Note:** The JSON input must conform to the schema defined in `entry-points.json` for the selected entry point.

### Results Display

Results are shown in a formatted output panel:

```
EXECUTION RESULTS
═══════════════════════════════════════════════════════════

Status:           ✅ SUCCESS
Execution Time:   0.45 seconds
Agent:            my-agent (agent.py:run)
Input:            {"action": "process", "data": "sample"}

OUTPUT:
{
  "status": "completed",
  "result": "processed successfully"
}
```

### Supported Input Types

The skill supports all JSON schema types:
- **string** - Text input
- **number** - Decimal numbers
- **integer** - Whole numbers
- **boolean** - Yes/No toggle
- **array** - List of items
- **object** - Complex nested data
- **enum** - Choice from predefined options

### Error Handling

If local execution fails, you'll see:
- Error message from the agent
- Stack trace for debugging
- Suggestions for fixing the issue
- Option to re-run with modified inputs

### Integration

Execution traces are automatically collected and can be:
- Viewed in UiPath Cloud
- Analyzed for performance
- Used for debugging and optimization

---

## Invoke (Cloud Execution)

Execute a published agent in your UiPath Cloud workspace.

### Prerequisites

Before invoking an agent, ensure:
- Agent is published to your workspace (`uip codedagents deploy --my-workspace`)
- You're authenticated with UiPath Cloud (`uip login --format json` then `uip login tenant set "<TENANT>" --format json`)
- Project has `pyproject.toml` with the correct project name and version

### Execution

Run a published agent in the cloud with:
```bash
uip codedagents invoke <entrypoint> '<json-input>'
```

**Arguments:**
- `entrypoint` - Entry point path to invoke (optional, defaults to first entry point)
- `input` - JSON input data (default: `{}`)

> **Note:** The JSON input must conform to the schema defined in `entry-points.json` for the selected entry point.

### What It Does

1. Reads project name and version from `pyproject.toml`
2. Looks up the published release in your UiPath workspace
3. Starts a cloud job with the provided input
4. Returns a monitoring URL to track execution

### Output

```
Job started successfully!
Monitor your job here: ...
```

> **Important:** `invoke` creates an asynchronous UiPath job that runs in the cloud. The command immediately returns a monitoring URL. You must open this link to view the job execution status, logs, and results in real-time on UiPath Cloud. There is NO `--wait` flag — the command always returns immediately.
