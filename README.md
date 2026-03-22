# UiPath Agent Skills

> [!NOTE]
> **Work in Progress** — This repository is under active development. Skills are being added and refined. Contributions, feedback, and ideas are welcome! See [Contributing](#contributing) below.

UiPath Agent Skills give AI coding agents the domain knowledge to build, run, test, and deploy UiPath automations and agents — directly from your development environment. Each skill is a self-contained package of instructions and resources that teaches your coding agent how to perform a specific UiPath task.

## Quick Start

> **Prerequisite:** [Node.js](https://nodejs.org/) (LTS) is required — it includes `npx`.

```bash
npx skills add uipath/skills
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
| **uipath-coded-workflows** | Create, edit, build, and run UiPath coded automations (.cs) with activity references for 20+ packages |
| **uipath-rpa-workflows** | Generate and edit RPA workflows (XAML) in UiPath Studio Desktop with discovery-first approach |
| **uipath-flow** | Create, validate, and debug UiPath Flow projects using the `.flow` JSON format and `uip` CLI |
| **uipath-development** | Authentication, Orchestrator management, solution lifecycle, Integration Service, and CLI tools |
| **uipath-servo** | Desktop and browser UI automation and testing — click, type, read, verify, screenshot, and extract UI elements |

## Claude Code

This repository also works as a **Claude Code plugin**. If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), you can install skills as a plugin marketplace for direct access to slash commands.

### Add the marketplace

```bash
claude plugin marketplace add https://github.com/UiPath/skills
```

### Install the plugin

```bash
claude plugin install uipath@uipath-marketplace
```

## Contributing

Contributions are welcome! Whether it's a new skill, a bug fix, or a documentation improvement — we'd love your help.

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/skills/issues).

## Resources

- [UiPath Documentation](https://docs.uipath.com/)
- [UiPath Community](https://community.uipath.com/)

## License

[MIT](LICENSE)
