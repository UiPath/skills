# UiPath Skills for Coding Agents

Official skills that teach coding agents how to build, test, and deploy UiPath automations. Install these skills into your coding agent and it will know how to scaffold projects, use the UiPath CLI, write coded workflows, build agents, and more.

## Available Skills

### Official

| Skill | Description |
|---|---|
| [**uipath-coded-workflow**](./skills/official/uipath-coded-workflow/SKILL.md) | Create, edit, and test coded workflows (.cs files) |
| [**uipath-rpa-cli**](./skills/official/uipath-rpa/uipath-rpa-cli/SKILL.md) | Scaffold, build, and deploy RPA projects via CLI |
| [**uipath-flow**](./skills/official/uipath-flow/SKILL.md) | Create and edit Flow projects (.flow JSON) |
| [**uipath-coded-agent**](./skills/official/uipath-coded-agent/) | Build, run, evaluate, and deploy coded agents (auth, setup, build, run, evaluate, deploy, sync, bindings) |
| [**uipath-development**](./skills/official/uipath-development/SKILL.md) | UiPath CLI, Orchestrator, and solution lifecycle management |

### Experimental

| Skill | Description |
|---|---|
| [**uipath-servo**](./skills/experimental/uipath-servo/SKILL.md) | Desktop and browser UI automation and testing (Windows) |

## Quick Start

### Claude Code

```bash
# Add the UiPath marketplace (one-time)
claude plugin marketplace add uipath/skills

# Install a plugin
claude plugin install uipath@uipath-marketplace
claude plugin install uipath-coded-agents@uipath-marketplace
```

### Other Agents

- **Cursor** — see `.cursor/rules/`
- **OpenAI Codex** — see `.codex/agents/`
- **Windsurf / Zed / JetBrains** — see `AGENTS.md`

## Repo Structure

```
skills/
├── official/                    # GA skills, maintained by UiPath
│   ├── uipath-coded-workflow/
│   ├── uipath-rpa/
│   ├── uipath-flow/
│   ├── uipath-coded-agent/
│   ├── uipath-coded-apps/      # coming soon
│   └── uipath-development/
├── experimental/                # Beta quality, subject to breaking changes
│   └── uipath-servo/
└── community/                   # Community-contributed (coming soon)
```

## Contributing

Skills follow the open `SKILL.md` standard. See `templates/SKILL-TEMPLATE.md` for the format. New skills start in `experimental/` and promote to `official/` once stable.

## License

MIT
