# UiPath Coded Agents

End-to-end toolkit for building, testing, and deploying UiPath coded agents with Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Auth** | `/uipath-coded-agents:auth` | Authenticate with UiPath Cloud (OAuth or client credentials) |
| **Setup** | `/uipath-coded-agents:setup` | Scaffold and initialize agent projects |
| **Build** | `/uipath-coded-agents:build` | Implement agent logic with framework-specific patterns |
| **Run** | `/uipath-coded-agents:run` | Run agents locally or invoke published agents in the cloud |
| **Evaluate** | `/uipath-coded-agents:evaluate` | Create and run evaluations with built-in evaluators |
| **Deploy** | `/uipath-coded-agents:deploy` | Package and publish agents to Orchestrator |
| **Sync** | `/uipath-coded-agents:sync` | Push/pull project files to/from Studio Web |
| **UiPath** | `/uipath-coded-agents:uipath` | Full lifecycle orchestrator — runs all stages end-to-end |

## Quick Start

```bash
# Full lifecycle — create, build, and deploy an agent in one prompt
/uipath-coded-agents:uipath
> "Build me a UiPath agent that summarizes documents"

# Or use individual skills for specific tasks
/uipath-coded-agents:auth       # Set up authentication
/uipath-coded-agents:setup      # Scaffold a new project
/uipath-coded-agents:build      # Implement agent logic
/uipath-coded-agents:run        # Test locally
/uipath-coded-agents:evaluate   # Run evaluations
/uipath-coded-agents:deploy     # Ship to production
```

## Supported Frameworks

| Framework | Dependency | Best For |
|-----------|-----------|----------|
| Simple Function | `uipath` | Deterministic logic, no LLM needed |
| LangGraph | `uipath-langchain` | Tool calling, multi-step orchestration |
| LlamaIndex | `uipath-llamaindex` | RAG and knowledge retrieval |
| OpenAI Agents | `uipath-openai-agents` | Lightweight LLM agents with handoffs |

## Project Structure

```
my-agent/
├── pyproject.toml          # Dependencies (no [build-system] section)
├── main.py                 # Agent entry point
├── uipath.json             # UiPath project metadata
├── entry-points.json       # Generated schemas (via uipath init)
├── .env                    # Auth tokens and config
└── evaluations/
    ├── eval-sets/          # Test case definitions
    └── evaluators/         # Evaluator configurations
```

## Key CLI Commands

```bash
uv run uipath new <name>                    # Scaffold agent
uv run uipath init                          # Generate entry-points.json
uv run uipath run <ENTRYPOINT> '<input>'    # Run locally
uv run uipath eval <ENTRYPOINT> <eval-set>  # Run evaluations
uv run uipath deploy --my-workspace         # Pack + publish
uv run uipath push                          # Sync to Studio Web
uv run uipath auth --cloud --tenant <NAME>  # Authenticate
```

**Note:** `<ENTRYPOINT>` is the name from `entry-points.json`, not the project name.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code CLI

## Resources

- [UiPath Python SDK](https://uipath.github.io/uipath-python/)
- [UiPath Evaluations](https://uipath.github.io/uipath-python/eval/)
- [GitHub Issues](https://github.com/UiPath/uipath-python/issues)

## License

MIT
