# Running UiPath Agents

Execute your UiPath agent locally or in the cloud.

## Run vs Invoke

| Aspect | Run (Local) | Invoke (Cloud) |
|--------|-----------|---|
| **Purpose** | Test agents locally during development | Execute deployed agents in UiPath Cloud |
| **Location** | Your machine | UiPath Cloud workspace |
| **When to Use** | Before deployment, debugging, testing | After publishing to the cloud |
| **Command** | `uv run uipath run` | `uv run uipath invoke` |
| **Requirements** | Local project setup | Published agent in workspace |

---

## Run (Local Execution)

Test your agent locally before deploying to the cloud.

### Project Verification

Before running an agent, your project should have:
- `uipath.json` - Project configuration
- `entry-points.json` - Agent entry points with schemas

If missing, create an agent first. See the [Creating Agents](/uipath-coded-agents:build) guide for setup instructions.

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
uv run uipath run <entrypoint> '<json-input>'
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
- Agent is published to your workspace (see [Deployment](/uipath-coded-agents:deploy))
- You're authenticated with UiPath Cloud (see [Authentication](/uipath-coded-agents:authentication))
- Project has `pyproject.toml` with the correct project name and version

### Execution

Run a published agent in the cloud with:
```bash
uv run uipath invoke <entrypoint> '<json-input>'
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

> **Important:** `invoke` creates an asynchronous UiPath job that runs in the cloud. The command immediately returns a monitoring URL. You must open this link to view the job execution status, logs, and results in real-time on UiPath Cloud.
