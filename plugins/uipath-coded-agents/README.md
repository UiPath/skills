# UiPath SDK Assistant

Comprehensive reference guide for creating, running, and evaluating UiPath coded agents with AI-powered assistance in Claude Code.

## Quick Start

### Access the Skills

The UiPath Coded Agents plugin provides focused skills for every stage of development:

```bash
# 1. Set up authentication
/uipath-coded-agents:authentication

# 2. Build your agent
/uipath-coded-agents:build

# 3. Run your agent
/uipath-coded-agents:execute

# 4. Test your agent
/uipath-coded-agents:evaluate

# 5. Deploy your agent
/uipath-coded-agents:deploy

# 6. Sync project files
/uipath-coded-agents:file-sync

# 7. Overview and navigation
/uipath-coded-agents:uipath
```

## Features

- **📚 Complete Documentation**: Comprehensive guides for all SDK features
- **🚀 Agent Creation**: Templates and patterns for building agents
- **▶️ Agent Execution**: Schema-driven input collection and execution
- **🧪 Testing Framework**: Multiple evaluator types (output-based and trajectory-based)
- **📊 Monitoring**: Automatic tracing with `@traced()` decorator

## Skills Overview

| Skill | Description | Purpose |
|-------|-------------|---------|
| `/uipath-coded-agents:authentication` | Authenticate with UiPath Cloud or on-premise | Setup and manage authentication |
| `/uipath-coded-agents:build` | Build UiPath coded agents with Pydantic models and tracing | Create agents with monitoring |
| `/uipath-coded-agents:execute` | Run UiPath coded agents with schema-driven inputs | Execute and test agents |
| `/uipath-coded-agents:evaluate` | Test and evaluate UiPath coded agents | Comprehensive testing framework |
| `/uipath-coded-agents:deploy` | Deploy agents to UiPath Orchestrator | Pack, publish, and invoke agents |
| `/uipath-coded-agents:file-sync` | Sync project files between local and remote | Push/pull bidirectional sync |
| `/uipath-coded-agents:uipath` | Overview and navigation hub | Framework selection and guidance |

## Documentation Structure

### Authentication
- **[Authentication Guide](skills/authentication/references/authentication.md)** - Set up UiPath authentication

### Building Agents
- **[Creating Agents Guide](skills/build/references/simple-agents.md)** - Build agents with Pydantic models
- **[Tracing Guide](skills/build/references/tracing.md)** - Add monitoring and debugging with `@traced()`
- **[pyproject.toml Template](skills/build/assets/templates/pyproject.toml)** - Project template

### Running Agents
- **[Running Agents Guide](skills/execute/references/running-agents.md)** - Execute agents with inputs

### Testing & Evaluation
- **[Evaluations Overview](skills/evaluate/references/evaluations.md)** - Comprehensive testing framework
- **[Creating Evaluations](skills/evaluate/references/evaluations/creating-evaluations.md)** - Design test cases
- **[Evaluators Guide](skills/evaluate/references/evaluations/evaluators/README.md)** - All evaluator types
- **[Evaluation Sets](skills/evaluate/references/evaluations/evaluation-sets.md)** - Test file structure
- **[Running Evaluations](skills/evaluate/references/evaluations/running-evaluations.md)** - Execute tests
- **[Best Practices](skills/evaluate/references/evaluations/best-practices.md)** - Patterns and optimization

## Example Workflow

A typical agent development workflow:

1. **Authenticate** - Set up UiPath authentication via CLI
2. **Build Agent** - Create an agent using the scaffold template
3. **Add Tracing** - Implement monitoring with `@traced()` decorator
4. **Test Locally** - Run your agent with test inputs
5. **Create Evaluations** - Design comprehensive test cases
6. **Validate** - Run evaluations to ensure agent quality

## Project Structure

When you create a UiPath agent project, it generates:

```
my-agent-project/
├── pyproject.toml          # Project dependencies and configuration
├── main.py                 # Agent implementation with Pydantic models
├── uipath.json             # UiPath project metadata
├── entry-points.json       # Agent definitions and JSON schemas
├── README.md               # Generated project documentation
├── .env                    # Environment variables (optional)
└── evaluations/
    ├── eval-sets/          # Test case definitions (JSON files)
    └── evaluators/         # Evaluator configuration files
```

## Requirements

- Python 3.11+
- `uv` (package manager) - https://docs.astral.sh/uv/
- Claude Code CLI
- UiPath SDK (installed automatically via `uv sync`)

## Getting Started

1. **Set up authentication** with `/uipath-coded-agents:authentication`
2. **Build your agent** using `/uipath-coded-agents:build`
   - Review the Creating Agents guide
   - Use the pyproject.toml template
3. **Implement your business logic** in the generated `main.py`
4. **Run your agent** with `/uipath-coded-agents:execute`
5. **Create evaluations** to validate agent behavior using `/uipath-coded-agents:evaluate`
6. **Deploy** to UiPath Cloud or on-premise

## Common Issues

### "UiPath SDK not found"

Ensure dependencies are installed:

```bash
uv sync
uv run uipath --version
```

### Agent creation or execution fails

Verify your project setup:
- Check that `pyproject.toml` exists and is correctly formatted
- Ensure `entry-points.json` is generated with `uv run uipath init`
- Verify Python 3.12+ is available: `python --version`

### Authentication issues

Use `/uipath-coded-agents:authentication` and review the guide for:
- Setting environment variables (UIPATH_URL)
- Using different authentication modes
- Handling proxy configurations

## Learning Resources

- **[UiPath Python SDK Docs](https://uipath.github.io/uipath-python/)** - Official documentation
- **[UiPath Platform](https://www.uipath.com/)** - Main UiPath website
- **[Evaluation Framework](skills/evaluate/references/evaluations.md)** - Comprehensive testing guide
- **[Best Practices](skills/evaluate/references/evaluations/best-practices.md)** - Agent patterns and optimization

## Support

- **GitHub Issues**: https://github.com/UiPath/uipath-python/issues
- **Documentation**: https://uipath.github.io/uipath-python/
- **Community**: https://community.uipath.com/

## License

MIT License - See project LICENSE file for details
