# UiPath Agent Skills

> [!NOTE]
> **Work in Progress** — This repository is under active development. Skills are being added and refined. Contributions, feedback, and ideas are welcome! See [Contributing](#contributing) below.

UiPath Agent Skills give AI coding agents the domain knowledge to build, run, test, and deploy UiPath automations and agents — directly from your development environment. Each skill is a self-contained package of instructions and resources that teaches your coding agent how to perform a specific UiPath task.

## Quick Start

Use the official onboarding installer. It installs Node.js >= 20, `@uipath/cli`, UiPath skills for installed AI coding agents, .NET SDK 8.0, and Python 3.11-3.14.

**macOS/Linux**
```bash
curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash
```

**Windows**
```powershell
irm https://download.uipath.com/uipath-cli/install.ps1 | iex
```

The installer runs `uip skills install --no-interactive` to wire the skills into detected AI coding agents. To re-run manually or install for one agent, use `uip skills install` or pass `--agent <name>` (e.g. `--agent claude`).

For CI or a CLI-only machine, skip agent skills and runtime installs with `--skip-skills --skip-runtimes` on macOS/Linux or `-SkipSkills -SkipRuntimes` on Windows.

## Skill Catalog

The repository ships skills covering authoring, platform operations, and diagnostics for UiPath automations.

### Authoring

| Skill | Description |
|-------|-------------|
| **uipath-rpa** | RPA workflows (`.xaml` and `.cs` coded) — create, edit, build, run, debug, test; UI automation, Object Repository, Integration Service activities. |
| **uipath-maestro-flow** | Maestro Flow (`.flow`) — author, connect nodes, validate, run, publish; triggers, schedules, evals, incidents. |
| **uipath-agents** | UiPath agents end-to-end — coded (Python: LangGraph, LlamaIndex, OpenAI Agents) and low-code (`agent.json`); scaffold, run, evaluate, deploy. |
| **uipath-maestro-bpmn** | Maestro BPMN process orchestration (`.bpmn`) — author XML, validate, package, operate, diagnose. |
| **uipath-maestro-case** | Case Management (`caseplan.json`) authoring from SDD with phased build and validation. |
| **uipath-coded-apps** | Coded Web Apps and Coded Action Apps — scaffold, build, debug, pack, publish, deploy via `uip codedapp`. |
| **uipath-api-workflow** | API Workflow JSON DSL — author, run, package, publish; HTTP and Integration Service connector activities. |
| **uipath-human-in-the-loop** | Human task authoring and operations — design approval gates, escalations, and validation forms in Flow, Maestro, or coded agents; list, assign, complete, and reassign the resulting Action Center tasks. |
| **uipath-ixp** | Document Understanding (IXP) — project setup, labeling, prediction review, prompt improvement, model publishing. |

### Solution & Planning

| Skill | Description |
|-------|-------------|
| **uipath-planner** | Solution planner & designer — turn a Process Design Document into an implementation-ready Solution Design Document (SDD), then derive an executable multi-skill task list across the other skills. |
| **uipath-solution** | Solution lifecycle (`.uipx`) — `uip solution init/pack/publish/deploy/activate`. |
| **uipath-review** | Read-only auditor — structural, quality, and best-practice review across RPA, agents, flows, BPMN, coded apps, and solutions. |

### Platform & Operations

| Skill | Description |
|-------|-------------|
| **uipath-platform** | Platform ops via `uip` CLI — auth, Orchestrator (folders, assets, queues, buckets, jobs, triggers), Integration Service, Data Fabric (entities and records), LLM Gateway, traces, licensing. |
| **uipath-admin** | UiPath Admin — Identity Server, Authorization (custom roles, role assignments, PDP), OMS (org, tenants, services, regions), IP restriction, audit; governance policies (AOps product policies and Access ToolUsePolicy). |
| **uipath-test** | Test Manager — manage projects, cases, sets, executions; generate persona-tailored test reports. |

### Diagnostics & Feedback

| Skill | Description |
|-------|-------------|
| **uipath-troubleshoot** | Root-cause investigation across any UiPath product — errors, failures, regressions, stuck jobs, traces, incidents. |
| **uipath-feedback** | Submit bug reports and improvement suggestions via `uip feedback send`. |

### Lifecycle Status

Every skill's maturity is tracked in [`assets/skill-status.json`](assets/skill-status.json) — the source of truth. The table below is generated; refresh it with `python3 scripts/check-skill-status.py --write-readme`.

<!-- BEGIN GENERATED SKILL STATUS -->
| Skill | Status |
|-------|--------|
| `uipath-admin` | In-development |
| `uipath-agents` | In-development |
| `uipath-api-workflow` | In-development |
| `uipath-automation-discovery` | Preview |
| `uipath-coded-apps` | Preview |
| `uipath-feedback` | Stable |
| `uipath-governance` | In-development |
| `uipath-human-in-the-loop` | In-development |
| `uipath-ixp` | In-development |
| `uipath-maestro-bpmn` | In-development |
| `uipath-maestro-case` | In-development |
| `uipath-maestro-flow` | In-development |
| `uipath-mcp-servers` | In-development |
| `uipath-planner` | Preview |
| `uipath-platform` | Preview |
| `uipath-review` | Preview |
| `uipath-rpa` | Preview |
| `uipath-solution` | Preview |
| `uipath-tasks` | Preview |
| `uipath-test` | In-development |
| `uipath-troubleshoot` | Preview |

**Status legend:**
- **Stable** — Stable, production-ready surface; safe for production.
- **Preview** — Not yet stable; may be broadly available or gated/allowlisted, and surface and behavior may change.
- **In-development** — Skill itself is incomplete or unstable; coverage is partial.
<!-- END GENERATED SKILL STATUS -->

## Agents

| Agent | Description |
|-------|-------------|
| **Project Discovery** (`uipath-project-discovery-agent`) | Auto-discovers UiPath project structure, dependencies, conventions, and generates context files for Claude Code (`.claude/rules/project-context.md`) and UiPath Autopilot (`AGENTS.md`). Triggered automatically when a UiPath project is detected without existing context, or on explicit user request. |

## Multi-Tool Support

This repository works with **Claude Code**, **Google Gemini CLI**, **OpenAI Codex CLI**, and **Cursor IDE**.

### Claude Code

This repository works as a **Claude Code plugin**. Install skills via `uip skills install` (the recommended method above) — this keeps skills updated automatically.

> **Avoid manual plugin installation** (e.g., `claude plugin marketplace add` / `claude plugin install`). Manually installed plugins must be updated manually, and you may miss skill updates and fixes.

If you've already installed manually, uninstall and re-install via `uip skills install` to switch to automatic updates.

#### Reduce permission prompts

By default, Claude Code prompts for approval on every `uip` command, and a realistic Flow or RPA build runs 25+ distinct subcommands. Claude Code plugins cannot ship permission allowlists declaratively, so run this once to install a curated allowlist of safe read-only commands (registry lookups, validation, local scaffolding) while keeping prompts for side-effectful operations (login, debug, publish):

```text
/uipath:install-permissions
```

The command prints the recommended JSON and offers to merge it into your settings (`~/.claude/settings.json` for global, or project-local `.claude/settings.local.json`). You will also see a one-line nudge at session start until an allowlist is installed.

### Google Gemini CLI

Gemini CLI is supported by `uip skills install`. If the Gemini CLI is on your PATH, it's detected automatically and skills are wired up. If no agent is detected, pick **Gemini CLI** when prompted.

### OpenAI Codex CLI

This repository is configured as a Codex CLI skill provider. The `AGENTS.md` file (symlinked to `CLAUDE.md`) provides project instructions, and skills are discovered via `.agents/skills/` (symlinked to `skills/`).

This repository also includes Codex plugin metadata under `.codex-plugin/`. The Codex plugin manifest exposes the same `skills/` directory and shared session hooks.

Install with Codex CLI:

```bash
codex plugin marketplace add UiPath/skills --ref main
codex plugin add uipath@uipath-marketplace
```

The marketplace entry currently uses a `plugins/uipath` symlink so Codex can load the repository root as the plugin root; remove it once [openai/codex#17066](https://github.com/openai/codex/issues/17066) is resolved.

> **Windows users:** This repo uses git symlinks. Clone with symlinks enabled:
> ```bash
> git clone -c core.symlinks=true https://github.com/UiPath/skills
> ```
> If you've already cloned without symlink support, re-enable and re-checkout:
> ```bash
> git config core.symlinks true
> git checkout -- .
> ```

### Cursor IDE

Project rules are provided in `.cursor/rules/` and are automatically loaded by Cursor.

## Contributing

Contributions are welcome! Whether it's a new skill, a bug fix, or a documentation improvement — we'd love your help.

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide, including:
- Repository structure and architecture
- How to add a new skill (folder layout, SKILL.md format, frontmatter)
- Naming conventions and quality checklist
- Pull request process and branch naming

**Quick version:**

1. Fork this repository
2. Create a feature branch (`feat/add-<skill-name>`)
3. Add your skill under `skills/uipath-<name>/` with a `SKILL.md`
4. Submit a pull request

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/uipath-claude-plugins/issues).

### Running coder-eval on demand

[**Run Coder Eval**](https://github.com/UiPath/skills/actions/workflows/run-coder-eval.yml) — GH-hosted workflow that runs `coder-eval` against the skills task tree (`tests/tasks/...`). Use for ad-hoc single-task verification or a folder-scoped sweep on the same infra as the nightly cron. Trigger from the Actions tab → "Run workflow" → fill in `task_globs`. Definition: [`.github/workflows/run-coder-eval.yml`](.github/workflows/run-coder-eval.yml).

## Resources

- [UiPath Documentation](https://docs.uipath.com/)
- [UiPath Community](https://community.uipath.com/)

## License

[MIT](LICENSE)
