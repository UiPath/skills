# UiPath Agent Skills

Domain knowledge packages (skills) for building, running, testing, and deploying UiPath automations and agents. Works with Claude Code, OpenAI Codex CLI, and Cursor IDE.

## Repository Structure

```
skills/                          # All skills
  uipath-coded-workflows/        # C# coded automation workflows
  uipath-rpa-workflows/          # XAML RPA workflow generation
  uipath-flow/                   # JSON-based Flow projects
  uipath-development/            # Auth, Orchestrator, deployment, CLI
  uipath-servo/                  # Desktop & browser UI automation/testing
  community/                     # Community-built skills, reviewed by UiPath
  experimental/                  # Experimental (confirm with user first)
    uipath-coded-agents/         # End-to-end coded agents toolkit
references/activity-docs/        # UiPath activity package documentation
hooks/                           # Session hooks (ensure-uip.sh)
.claude-plugin/                  # Claude Code plugin + marketplace registration
.agents/skills -> skills/        # Codex CLI skill discovery (symlink)
.codex/                          # Codex CLI config
.cursor/rules/                   # Cursor IDE project rules
AGENTS.md -> CLAUDE.md           # Codex CLI project instructions (symlink)
```

## Skill Format

Each skill is a directory containing:
- `SKILL.md` — YAML frontmatter (`name`, `description`) + markdown body with instructions
- `references/` — Domain documentation and guides
- `assets/` — Templates and resources (optional)
- `scripts/` — Automation scripts (optional)

## Core Skills

| Skill | Description |
|-------|-------------|
| `uipath-coded-workflows` | Create, edit, build, and run C# coded automations |
| `uipath-rpa-workflows` | Generate and edit XAML RPA workflows |
| `uipath-flow` | Create and debug JSON-based Flow projects |
| `uipath-development` | Authentication, Orchestrator, deployment, CLI tools, Integration Service |
| `uipath-servo` | Desktop and browser UI automation and testing |

## Community Skills

Skills in `skills/community/` are contributed by the UiPath community and reviewed by UiPath.

## Experimental Skills

Skills in `skills/experimental/` are under active development. **Always confirm with the user before using.**

| Skill | Description |
|-------|-------------|
| `uipath-coded-agents` | Scaffold, build, run, evaluate, deploy, and sync UiPath coded agents |

## Multi-Tool Support

This repository is configured for three AI coding tools:

- **Claude Code** — Plugin via `.claude-plugin/`, skills at `skills/`
- **OpenAI Codex CLI** — `AGENTS.md` (symlink to this file), skills via `.agents/skills/` (symlink to `skills/`)
- **Cursor IDE** — Project rules in `.cursor/rules/`

### Symlinks

This repo uses git symlinks for cross-tool compatibility:
- `AGENTS.md` → `CLAUDE.md` (Codex CLI reads AGENTS.md)
- `.agents/skills/` → `skills/` (Codex CLI skill discovery)

On Windows, ensure `core.symlinks=true` in git config, or clone with `git clone -c core.symlinks=true`.
