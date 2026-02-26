# Running UiPath Agents

Execute your UiPath agent with interactive, schema-driven input collection.

## Project Verification

Before running an agent, your project should have:
- `uipath.json` - Project configuration
- `entry-points.json` - Agent entry points with schemas

If missing, create an agent first. See the [Creating Agents](/uipath-coded-agents:build) guide for setup instructions.

## Agent Discovery

The tool reads `entry-points.json` to find all available agents and their schemas:
- **File path** and **entry point** (e.g., main.py:main)
- **Input schema** with field types and descriptions
- **Output schema** with expected return fields

If multiple agents exist, you'll be prompted to select one.

## Input Collection

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

## Execution

Your agent runs with:
```bash
uv run uipath run <entrypoint> '<json-input>'
```

The agent runs with your provided inputs and returns structured output.

## Results Display

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

## Supported Input Types

The skill supports all JSON schema types:
- **string** - Text input
- **number** - Decimal numbers
- **integer** - Whole numbers
- **boolean** - Yes/No toggle
- **array** - List of items
- **object** - Complex nested data
- **enum** - Choice from predefined options

## Error Handling

If execution fails, you'll see:
- Error message from the agent
- Stack trace for debugging
- Suggestions for fixing the issue
- Option to re-run with modified inputs

## Integration

Execution traces are automatically collected and can be:
- Viewed in UiPath Cloud
- Analyzed for performance
- Used for debugging and optimization
