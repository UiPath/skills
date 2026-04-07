# Onboarding Guide

Get from zero to a working local setup for contributing to UiPath Agent Skills.

## Prerequisites

| Tool | Required | Install |
|------|----------|---------|
| **Git** | Yes | [git-scm.com](https://git-scm.com/) |
| **Node.js** (LTS) | Yes — needed for `uip` CLI | [nodejs.org](https://nodejs.org/) or `brew install node` / `winget install OpenJS.NodeJS.LTS` |
| **npm** | Yes — ships with Node.js | Included with Node.js |

No other runtimes, compilers, or package managers are required. This is a documentation-only repository — there is no build step.

## Clone and Install

```bash
# Clone the repository
git clone https://github.com/UiPath/skills.git
cd skills

# Install the UiPath CLI globally
npm install -g @uipath/cli

# Enable git pre-commit hooks (validates skill descriptions on commit)
bash scripts/setup-hooks.sh
```

> **Windows users:** Clone with symlinks enabled: `git clone -c core.symlinks=true https://github.com/UiPath/skills`

## Verify Setup

```bash
# Verify Node.js and npm
node -v
npm -v

# Verify the UiPath CLI
uip --version

# Verify git hooks are configured
git config core.hooksPath
# Expected output: .githooks
```

There is no test suite, linter, or type checker — this repo contains only markdown and shell scripts. Validation happens via:

- **Pre-commit hook**: Runs `hooks/validate-skill-descriptions.sh` to enforce the 250-character limit on SKILL.md `description` fields
- **CI workflow**: `.github/workflows/validate-skills.yml` runs on pull requests

## Try It Out

Install skills into your Claude Code environment to see them in action:

```bash
# Install skills via the CLI wizard
uip skills install

# Or add the marketplace plugin to Claude Code
claude plugin marketplace add https://github.com/UiPath/skills
claude plugin install uipath@uipath-marketplace
```

## Code Formatting

No formatter or linter is configured for markdown. Follow the style conventions in [CONTRIBUTING.md](../CONTRIBUTING.md#style-guide):

- ATX-style headers (`#`, `##`, `###`)
- Fenced code blocks with language identifiers
- Tables for structured data
- `<UPPER_SNAKE_CASE>` in angle brackets for placeholders

## Project Structure

```
.
├── skills/                    # Individual skill implementations
│   └── uipath-<name>/        #   One folder per skill
│       ├── SKILL.md           #   Skill definition (required)
│       ├── references/        #   Supporting reference docs (optional)
│       └── assets/            #   Templates, examples (optional)
├── agents/                    # Standalone agent definitions
├── references/                # Shared reference docs
│   └── activity-docs/         #   Per-package, per-version activity API docs
├── hooks/                     # Plugin lifecycle hooks
│   ├── hooks.json             #   Hook definitions (SessionStart)
│   ├── ensure-uip.sh         #   Auto-installs uip, servo, rpa-tool
│   └── validate-skill-descriptions.sh  # 250-char description validator
├── scripts/                   # Developer utilities
│   └── setup-hooks.sh         #   Enables git pre-commit hooks
├── .claude-plugin/            # Claude Code plugin manifest
│   ├── plugin.json            #   Plugin name, version, skills pointer
│   └── marketplace.json       #   Marketplace registration
├── .claude/rules/             # Project-level Claude Code rules
├── .githooks/                 # Git pre-commit hook scripts
├── .github/workflows/         # CI validation
├── CLAUDE.md                  # Project instructions for Claude Code
├── CONTRIBUTING.md            # Contribution guide
├── CODEOWNERS                 # GitHub ownership by path
└── LICENSE                    # MIT
```

## Key Concepts

- **Skills are self-contained.** Each `skills/uipath-<name>/` folder is independent. Skills cannot reference, import, or depend on other skills. Everything the AI agent needs must be reachable from that skill's `SKILL.md`.

- **SKILL.md is the contract.** The plugin system reads only `SKILL.md` frontmatter to discover and activate skills. The `name` field must match the folder name, and the `description` field (max 250 chars) determines when the skill triggers.

- **This repo's audience is AI agents, not humans.** Documentation is prescriptive ("Run this command") not descriptive ("You could run this command"). CLI commands are copy-paste ready with all required flags. Anti-patterns sections prevent expensive agent mistakes.

- **The `uip` CLI is the primary tool.** Skills teach agents to use `uip` subcommands (`uip rpa`, `uip flow`, `uip orchestrator`, etc.) with `--output json` for programmatic parsing.

- **Hooks run automatically.** The `SessionStart` hook (`ensure-uip.sh`) auto-installs required tools when a Claude Code session begins. The pre-commit hook validates description lengths before each commit.
