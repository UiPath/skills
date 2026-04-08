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

# (Optional) Enable git pre-commit hooks — validates skill descriptions on commit.
# CI runs the same check on PRs, so this is a convenience, not a requirement.
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

There is no test suite, linter, or type checker — this repo contains only markdown and shell scripts. There is no test framework (e.g., Athena, Jest, pytest) in use. Validation happens via:

- **Pre-commit hook** (optional): Runs `hooks/validate-skill-descriptions.sh` to enforce the 250-character limit on SKILL.md `description` fields
- **CI workflow**: `.github/workflows/validate-skills.yml` runs the same validation on pull requests — this is the authoritative check

## Try It Out

Install skills into your Claude Code environment to see them in action:

```bash
# Install skills via the CLI wizard
uip skills install

# Or add the marketplace plugin to Claude Code
claude plugin marketplace add https://github.com/UiPath/skills
claude plugin install uipath@uipath-marketplace
```

### Try a Skill

Once installed, give your coding agent a prompt that matches a skill's domain. Examples:

| Prompt | Skill triggered |
|--------|-----------------|
| "Create a new Flow that sends a Slack message when an email arrives" | `uipath-maestro-flow` |
| "Build a coded workflow in C# that reads a CSV and posts to an API" | `uipath-rpa` |
| "Scaffold a new coded agent using LangGraph" | `uipath-agents` |
| "Click the Submit button on the login page" | `uipath-servo` |
| "Publish my solution to Orchestrator" | `uipath-platform` |

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

- **How skills get triggered.** Each skill has a `description` field in its SKILL.md frontmatter (max 250 chars). Claude Code matches user prompts against these descriptions to decide which skill to activate. The description front-loads identity and unique signals (e.g., `.flow`, `.cs`, `.xaml`, `servo`) so the model can distinguish between skills. Compact `→` redirects (e.g., `For XAML→uipath-rpa`) steer the agent to the correct skill when domains overlap.

- **How an agent uses a skill.** Once triggered, the agent reads the full SKILL.md — Critical Rules first, then the workflow steps. Reference docs in `references/` are loaded on demand when the agent needs detailed schemas, CLI flags, or examples. The agent follows the prescriptive instructions ("Run this command") rather than making its own decisions about tooling.

- **Skills are self-contained.** Each `skills/uipath-<name>/` folder is independent. Skills cannot reference, import, or depend on other skills. Everything the AI agent needs must be reachable from that skill's `SKILL.md`.

- **SKILL.md is the contract.** The plugin system reads only `SKILL.md` frontmatter to discover and activate skills. The `name` field must match the folder name, and the `description` field (max 250 chars) determines when the skill triggers.

- **This repo's audience is AI agents, not humans.** Documentation is prescriptive ("Run this command") not descriptive ("You could run this command"). CLI commands are copy-paste ready with all required flags. Anti-patterns sections prevent expensive agent mistakes.

- **The `uip` CLI is the primary tool.** Skills teach agents to use `uip` subcommands (`uip rpa`, `uip flow`, `uip orchestrator`, etc.) with `--output json` for programmatic parsing.

- **Hooks run automatically.** The `SessionStart` hook (`ensure-uip.sh`) auto-installs required tools when a Claude Code session begins. The pre-commit hook validates description lengths before each commit.

## Skill Deep Dive: `uipath-maestro-flow`

This section walks through one skill end-to-end to illustrate how skills work in practice.

### How It Gets Triggered

The skill is activated by its `description` field in the SKILL.md frontmatter:

```
[PREVIEW] UiPath Flow projects (.flow files) — orchestrate RPA, agents, apps.
Create, edit, validate, run flows via uip CLI: nodes, variables, subflows, triggers.
For XAML or C# workflows→uipath-rpa.
```

Claude Code matches user prompts against this description. The key signals are: **`.flow` files**, **Flow projects**, **orchestrate**, **nodes/edges/subflows/triggers**, and **`uip flow`** CLI commands. If the user mentions XAML or C#, the `→uipath-rpa` redirect steers the agent to the correct skill instead.

### How a Coding Agent Uses It

Once triggered, the agent reads the SKILL.md and follows the workflow:

1. **Existing flow** — uses the "Common Edits" recipes (add/remove nodes, change scripts, add branches)
2. **New flow** — follows Steps 0–8: resolve CLI → login → create project → plan (2-phase) → build → validate → optionally debug/publish

The agent loads reference docs from `references/` on demand (file format, CLI commands, planning guides, node catalogs).

### Example Prompts That Would Activate It

**Creating flows:**
- "Create a new UiPath Flow that sends a Slack message when an email arrives"
- "Build a .flow project that orchestrates an RPA process and an agent"
- "Initialize a Flow project with a scheduled trigger that runs every hour"

**Editing flows:**
- "Add a decision branch after the HTTP node in my .flow file"
- "Add a script node that transforms the API response"
- "Wire a new Slack notification node between the filter and the end node"

**Operations:**
- "Validate my Flow project"
- "Debug this .flow file"
- "Publish my flow to Studio Web"

**Discovery:**
- "What connector nodes are available for Salesforce?"
- "Show me the node types I can use in a Flow"
- "How do I add variables to a .flow file?"
