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

The repository contains skills for building and managing UiPath automation projects — coded workflows in C#, RPA workflows in XAML, Flow projects in JSON, desktop/browser UI automation, and platform operations.

| Skill | Description |
|-------|-------------|
| **uipath-rpa** | Full assistant for UiPath automations — coded workflows (C#) and low-code RPA workflows (XAML). Create, edit, build, run, and debug automation projects |
| **uipath-maestro-flow** | Create, validate, and debug UiPath Flow projects using the `.flow` JSON format and `uip` CLI |
| **uipath-platform** | Authentication, Orchestrator management, solution lifecycle, Integration Service, and CLI tools |
| **uipath-agents** | End-to-end toolkit for UiPath coded agents: scaffold, build, run, evaluate, deploy (LangGraph, LlamaIndex, OpenAI Agents, Simple Function) |
| **uipath-coded-apps** | Build, sync, package, publish, and deploy UiPath Coded Web Applications — push/pull to Studio Web, pack into .nupkg, publish to Orchestrator, deploy to production |
| **uipath-servo** | Desktop and browser UI automation and testing — click, type, read, verify, screenshot, and extract UI elements |
| **uipath-planner** | Task planner — plans multi-skill execution order, disambiguates overlapping skills, detects project type |
| **uipath-feedback** | Send bug reports or improvement suggestions to UiPath via `uip feedback send` |

## Agents

| Agent | Description |
|-------|-------------|
| **Project Discovery** (`uipath-project-discovery-agent`) | Auto-discovers UiPath project structure, dependencies, conventions, and generates context files for Claude Code (`.claude/rules/project-context.md`) and UiPath Autopilot (`AGENTS.md`). Triggered automatically when a UiPath project is detected without existing context, or on explicit user request. |

## Multi-Tool Support

This repository works with **Claude Code**, **OpenAI Codex CLI**, and **Cursor IDE**.

### Claude Code

This repository works as a **Claude Code plugin**. Install skills as a plugin marketplace for direct access to slash commands.

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/UiPath/skills

# Install the plugin
claude plugin install uipath@uipath-marketplace
```

### OpenAI Codex CLI

Skills can be used with Codex CLI by symlinking the project instructions and skills directory:

```bash
ln -s CLAUDE.md AGENTS.md
mkdir -p .agents && ln -s ../skills .agents/skills
```

> **Windows users:** Clone with symlinks enabled: `git clone -c core.symlinks=true https://github.com/UiPath/skills`

### Cursor IDE

Skills can be used with Cursor by copying project rules into `.cursor/rules/`.

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

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/skills/issues).

## Resources

- [UiPath Documentation](https://docs.uipath.com/)
- [UiPath Community](https://community.uipath.com/)

## License

[MIT](LICENSE)
