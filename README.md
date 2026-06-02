# UiPath Agent Skills

> [!NOTE]
> **Work in Progress** — This repository is under active development. Skills are being added and refined. Contributions, feedback, and ideas are welcome! See [Contributing](#contributing) below.

UiPath Agent Skills give AI coding agents the domain knowledge to build, run, test, and deploy UiPath automations and agents — directly from your development environment. Each skill is a self-contained package of instructions and resources that teaches your coding agent how to perform a specific UiPath task.

## Quick Start

> **Prerequisite:** [Node.js](https://nodejs.org/) (LTS) is required — it includes `npm`.

```bash
npm -g install @uipath/cli
uip skills install
```

Select the skills you need from the wizard. Skills are installed into your coding agent's directory and ready to use.

<details>
<summary>Don't have Node.js installed?</summary>

**macOS**
```bash
brew install node
```

**Windows**
```bash
winget install OpenJS.NodeJS.LTS
```

**Linux**
```bash
curl -fsSL https://fnm.vercel.app/install | bash
fnm install --lts
```
See [Installing Node.js via package manager](https://nodejs.org/en/download/package-manager) for other methods.

After installing, verify with `node -v` and then run the quick start command above.

</details>

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
| **uipath-design** | PDD → SDD authoring — turn a Process Design Document into an implementation-ready Solution Design Document. |
| **uipath-solution** | Solution lifecycle (`.uipx`) — `uip solution init/pack/publish/deploy/activate`. |
| **uipath-planner** | Multi-skill task planner — reads SDDs or non-PDD requests and derives an executable task list across the other skills. |
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
| `uipath-admin` | Preview |
| `uipath-agents` | Stable |
| `uipath-api-workflow` | Preview |
| `uipath-coded-apps` | Preview |
| `uipath-data-fabric` | Preview |
| `uipath-feedback` | Stable |
| `uipath-governance` | Preview |
| `uipath-human-in-the-loop` | Preview |
| `uipath-ixp` | Preview |
| `uipath-maestro-bpmn` | Stable |
| `uipath-maestro-case` | Preview |
| `uipath-maestro-flow` | Stable |
| `uipath-planner` | Stable |
| `uipath-platform` | Stable |
| `uipath-review` | Preview |
| `uipath-rpa` | Stable |
| `uipath-solution` | Stable |
| `uipath-tasks` | Preview |
| `uipath-test` | Preview |
| `uipath-troubleshoot` | Stable |

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

Gemini CLI is supported by `uip skills install` — pick **Gemini CLI** when the wizard prompts for a target and skills are wired up automatically.

### OpenAI Codex CLI

This repository is configured as a Codex CLI skill provider. The `AGENTS.md` file (symlinked to `CLAUDE.md`) provides project instructions, and skills are discovered via `.agents/skills/` (symlinked to `skills/`).

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
