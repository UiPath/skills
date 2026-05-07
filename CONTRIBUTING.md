# Contributing to UiPath Agent Skills

Thank you for your interest in contributing! Whether you're adding a new skill, improving an existing one, fixing a bug, or enhancing documentation — we appreciate your help.

## Table of Contents

- [Repository Structure](#repository-structure)
- [Canonical SKILL.md Contract](#canonical-skillmd-contract)
- [Adding a New Skill](#adding-a-new-skill)
- [Modifying an Existing Skill](#modifying-an-existing-skill)
- [Developing Experimental Skills](#developing-experimental-skills)
- [Hooks](#hooks)
- [Quality Checklist](#quality-checklist)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Repository Structure

```
.
├── .claude/                   # Claude Code project-level configuration
│   └── commands/              # Project-only slash commands (e.g., /test-coverage)
├── .claude-plugin/            # Plugin manifest and marketplace config
│   ├── plugin.json            # Plugin name, version, skills directory pointer
│   └── marketplace.json       # Claude Code marketplace registration
├── .gemini/                   # Google Gemini CLI project-level configuration
│   ├── settings.json          # context.fileName → [GEMINI.md, AGENTS.md, CLAUDE.md]
│   └── commands/              # Gemini custom slash commands (*.toml)
├── .cursor/                   # Cursor IDE project-level configuration
│   └── rules/                 # Cursor MDC rule files (one per concern, scoped by globs)
├── .agents/                   # Codex CLI skill-discovery root
│   └── skills -> ../skills    # Symlink (Codex scans .agents/skills for SKILL.md)
├── AGENTS.md -> CLAUDE.md     # Symlink; read by Codex, Copilot coding agent, others
├── commands/                  # Plugin-namespaced slash commands shipped to end users
│   └── *.md                   # Each file becomes /uipath:<filename>
├── hooks/                     # Session-initialization hooks
│   ├── hooks.json             # Hook definitions (SessionStart, etc.)
│   └── ensure-uip.sh         # Cross-platform tool installation script
├── references/                # Shared documentation and activity references
│   └── activity-docs/         # Per-package, per-version activity API docs
├── skills/                    # Individual skill implementations
│   └── uipath-<name>/        # One folder per skill
│       ├── SKILL.md           # Skill definition (required)
│       ├── references/        # Supporting reference documents (optional)
│       └── assets/            # Templates, examples, static files (optional)
├── tests/                     # Skill evaluation tests (coder_eval)
│   ├── experiments/           # Experiment configs (smoke, integration, e2e)
│   ├── tasks/                 # Test tasks organized by skill
│   │   └── <skill-name>/     # One folder per skill
│   └── reports/               # Generated coverage reports (/test-coverage)
├── CLAUDE.md                  # Root project rules (source of truth)
├── CODEOWNERS                 # GitHub ownership by skill/path
├── README.md                  # Project overview and quick start
├── CONTRIBUTING.md            # This file
└── LICENSE                    # MIT
```

### Key Principles

- **Skills are runtime-independent.** Each skill is an independent folder under `skills/`. A skill MUST NOT import or link to another skill's `references/` or `assets/`. Sibling-disambiguation pointers in the `description` field (`For X→uipath-other-skill`) are required for the matcher, not violations — see [Cross-skill boundaries](#cross-skill-boundaries).
- **SKILL.md is the entry point.** The AI agent reads `SKILL.md` first. Everything the agent needs to know must be reachable from there.
- **References are supplementary.** Large reference material goes in `references/` subdirectories, linked from SKILL.md.
- **No build system.** This is a documentation and skill-definitions repository. There is no compilation, bundling, or package publishing from this repo.

### Multi-Tool Compatibility

Skills work with **Claude Code**, **Google Gemini CLI**, **OpenAI Codex CLI**, **Cursor IDE**, and **GitHub Copilot coding agent**. Keep every `SKILL.md` file tool-agnostic markdown — no references to Claude-specific tool names, Anthropic-only plugin features, or vendor-specific slash commands inside skill bodies.

Tool wiring lives outside `skills/`:

| Tool | Integration file | Mechanism |
|------|------------------|-----------|
| Claude Code | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Plugin marketplace discovers `skills/` via plugin manifest |
| Google Gemini CLI | `.gemini/settings.json` (`context.fileName`), `.gemini/commands/*.toml` | Gemini loads `GEMINI.md` / `AGENTS.md` / `CLAUDE.md` as project context; discovers `SKILL.md` files on-demand via `.agents/skills/` |
| OpenAI Codex CLI | `AGENTS.md` (symlink → `CLAUDE.md`), `.agents/skills/` (symlink → `skills/`) | Codex scans `.agents/skills/` for `SKILL.md` files, reads `AGENTS.md` as project instructions |
| Cursor IDE | `.cursor/rules/*.mdc` | Scoped MDC rules: `token-optimization` (always-apply), `skill-structure` + `content-quality` (glob-scoped), `skill-review` + `pr-review` (agent-requested) |
| GitHub Copilot coding agent | `AGENTS.md` (symlink → `CLAUDE.md`) | Copilot reads `AGENTS.md` natively (since Aug 2025) |

When adding a skill, only touch files under `skills/uipath-<name>/` — the root integration files already wire every tool up automatically.

## Canonical SKILL.md Contract

This section is the single source of truth for the SKILL.md frontmatter contract in this repo. Both `CLAUDE.md` and `.claude/rules/skill-structure.md` defer to this section. Validators enforce the **Required** rules; **Optional** fields are recognized and used in real skills today; **Style guidance** is a SHOULD.

### Required fields (enforced)

| Field | Rule |
|-------|------|
| `name` | MUST match the parent folder name exactly (kebab-case, `uipath-<domain>`). |
| `description` | ≤ 1024 characters. Front-load identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`, `interact`, `BYO LLM`) within the first ~100 chars. Use `→` redirects for sibling disambiguation (`For XAML→uipath-rpa`). MUST NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — those have been replaced by `→` redirects. |

### Optional fields (recognized; in use across real skills)

| Field | Use |
|-------|-----|
| `when_to_use` | Standalone trigger sentence ("User says 'X'…"). Useful when the `description` is identity/capability-focused and you want a separate trigger phrasing. Combined `description + when_to_use` is truncated by Claude Code at 1,536 chars in the skill listing — the 1024 cap on `description` leaves ~500 chars of headroom for `when_to_use`. |
| `allowed-tools` | Comma-separated tool list (e.g., `Bash, Read, Write, Glob, Grep, AskUserQuestion`). Restricts which tools the skill is allowed to call. Bash invocations may be scoped (e.g., `Bash(uip:*)`). |
| `user-invocable` | Defaults to `true`. Set `false` to make the skill agent-only — not directly invocable as `/uipath:<name>` by users. |

### Style guidance (SHOULD, not enforced)

- **Front-load the brand/domain identity** ("UiPath …") when natural. Most skills do, and it places the strongest matching signal first. Action verbs ("Manage", "Send", "Always invoke for `.flow` files") are acceptable when they make the skill's purpose clearer in the first ~100 chars.
- **Avoid metadata prefixes** like `[PREVIEW]` / `[BETA]` at the start of `description` — they displace high-value matching tokens. Indicate preview / experimental status in the SKILL.md body instead, with a `> **Preview**` or `> **Experimental**` callout under the H1.
- **All frontmatter fields MUST be at the top level** — never nested under a `metadata:` key. Claude Code only reads top-level keys.
- **Frontmatter MUST be valid YAML** — no tabs, proper quoting of strings containing colons.

### Cross-skill boundaries

Skills are **runtime-independent**. A skill MUST NOT import, link to, or rely on content from another skill's `references/` or `assets/`. Each `skills/uipath-*/` folder is fully self-contained when an agent loads it.

However, **disambiguation pointers in `description` are required, not violations.** Every skill SHOULD include `→` redirects for sibling skills it commonly gets confused with — these tell the matcher which skill is correct:

- `For Python agents→uipath-agents`
- `For .flow files→uipath-maestro-flow`
- `For Test Manager→uipath-test`

Routing skills (e.g., `uipath-planner`) explicitly delegate to specialist skills by name — that is the routing skill's purpose, not a cross-dependency.

### What the validator enforces today

`hooks/validate-skill-descriptions.sh` (run by the pre-commit hook and the [Validate Skills](.github/workflows/validate-skills.yml) CI job) enforces:

- `name` field is present
- `name` matches the parent folder name
- `description` field is present
- `description` ≤ 1024 chars
- Combined `description + when_to_use` ≤ 1,500 chars (warning when exceeded)

Style guidance (brand identity, `→` redirects, metadata prefixes) is reviewer-enforced, not validator-enforced. New validators should be proposed via a PR that updates this section, the rules, and the script together.

## Adding a New Skill

### 1. Choose a Name

Skill folders follow the naming convention: `uipath-<domain>` or `uipath-<tool>`.

- Use **kebab-case** (lowercase, hyphens between words)
- Prefix with `uipath-` for UiPath-related skills
- Be descriptive but concise: `uipath-rpa`, `uipath-interact`, `uipath-maestro-flow`

### 2. Create the Folder Structure

At minimum, a skill needs:

```
skills/uipath-<your-skill>/
└── SKILL.md
```

For skills with substantial reference material:

```
skills/uipath-<your-skill>/
├── SKILL.md
├── references/
│   ├── commands-reference.md
│   ├── api-guide.md
│   └── <subdomain>/
│       └── detailed-topic.md
└── assets/
    └── templates/
        └── template-file.ext
```

### 3. Write SKILL.md

SKILL.md is the most important file. It uses YAML frontmatter followed by markdown content. The full schema is documented in the [Canonical SKILL.md Contract](#canonical-skillmd-contract) section below — this section gives the quick view.

#### Frontmatter Format

```yaml
---
name: uipath-<your-skill>
description: "<identity> (<unique signal>). <core actions>. For <confusing-case>→<correct-skill>."
---
```

> **1024-character limit.** Claude Code truncates the combined `description` + `when_to_use` at 1,536 characters in the skill listing ([source](https://code.claude.com/docs/en/skills.md)). This repo caps `description` at 1024 chars to leave headroom and keep descriptions focused; the pre-commit hook enforces it. Front-load the skill identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`, `interact`) within the first ~100 characters.

**Required frontmatter fields:**

| Field | Description |
|-------|-------------|
| `name` | Exact skill identifier, MUST match the folder name. Enforced by `hooks/validate-skill-descriptions.sh`. |
| `description` | ≤ 1024 chars (enforced). Front-load identity and unique signals, then core actions, then compact `→` redirects for commonly confused sibling skills. Do NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — they waste characters. |

**Optional frontmatter fields** (all in current use across real skills):

| Field | Description |
|-------|-------------|
| `when_to_use` | Standalone trigger phrasing ("User says 'X', 'Y'…"). Useful when `description` is identity/capability-focused and you want a separate, scannable trigger sentence. The combined `description + when_to_use` is truncated by Claude Code at 1,536 chars in the skill listing. |
| `allowed-tools` | Restricts which tools the skill can use (e.g., `Bash, Read, Write, Glob, Grep`). Bash invocations may be scoped (e.g., `Bash(uip:*)`). |
| `user-invocable` | Defaults to `true`. Set to `false` if the skill should only be discoverable by the agent, not directly invocable by users via `/uipath:<name>`. |

> **No nested `metadata:` key.** All fields above MUST be at the top level of the frontmatter. Claude Code only reads top-level keys; anything nested under `metadata:` is invisible to the matcher.

#### Content Structure

Follow this structure in the markdown body:

```markdown
# Skill Title

Brief description of what the skill does.

## When to Use This Skill

- Bullet list of scenarios that should activate this skill

## Critical Rules

Numbered list of rules the AI agent MUST follow. These are the most important
part of your skill — they prevent the agent from making mistakes.

1. **Rule name** — Explanation and rationale
2. **Another rule** — ...

## Quick Start / Workflow

Step-by-step instructions for the most common use case.

## Reference Navigation

Links to reference documents in the `references/` folder for detailed topics.
```

**Tips for writing effective skills:**

- **Lead with rules.** The Critical Rules section prevents the agent from making expensive mistakes. Put the most important constraints first.
- **Be prescriptive, not descriptive.** Tell the agent exactly what to do, not just what's possible.
- **Include CLI commands verbatim.** Show the exact commands with flags. Agents work best with copy-paste-ready instructions.
- **Specify `--output json`** for any CLI commands whose output needs to be parsed programmatically.
- **Include anti-patterns.** A "What NOT to Do" section saves more time than a "What to Do" section.
- **Link to references for depth.** Keep SKILL.md focused on workflow and rules. Move detailed API docs, schemas, and examples into `references/`.

### 4. Add Reference Documents (Optional)

Reference files go in `references/` and follow these conventions:

- **File naming:** `kebab-case.md` (e.g., `commands-reference.md`, `api-guide.md`)
- **Guide files:** Use the `-guide.md` suffix (e.g., `orchestrator-guide.md`)
- **Organize by subdomain** when a skill covers multiple areas (e.g., `references/integration-service/`, `references/lifecycle/`)
- **Link from SKILL.md** so the agent can discover them

### 5. Add Templates/Assets (Optional)

Static files like code templates go in `assets/`:

- **Templates:** Use the `-template` suffix (e.g., `codedworkflow-template.md`)
- **Nested folders** are fine for organization (e.g., `assets/templates/`)

## Modifying an Existing Skill

1. **Read before editing.** Understand the existing SKILL.md and references before making changes.
2. **Preserve the Critical Rules section.** These exist for a reason. If you need to change a rule, explain why in your PR description.
3. **Don't break frontmatter.** The `name` and `description` fields are parsed by the plugin system. Validate your YAML.
4. **Test your changes.** After editing, verify the skill still activates correctly for its intended scenarios.
5. **Coordinate with CODEOWNERS.** Check who owns the skill and tag them in your PR.

## Developing Experimental Skills

Some skills take weeks to reach a usable state — for example, large new product surfaces or skills that need an unreleased CLI feature to land first. This section covers how to develop those in this repository without disrupting users who install the published plugin.

> **This repository is public.** Branches, commits, PR titles, and review comments are visible to everyone, including customers and competitors. Treat every push as a public statement.

### Default: build in the open

Develop directly in this repository on a feature branch off `main`. Skills are largely self-contained, so a long-lived `develop` integration branch is not useful here — each experimental skill gets its own branch and merges into `main` independently when ready.

Only develop in a private fork when the feature must stay confidential before release (e.g., tied to an unannounced product). In that case, fork this repository, develop privately, and open the PR back here once the feature can be public.

### Branch naming

| Type | Pattern | Example |
|------|---------|---------|
| New experimental skill | `feat/experimental/<skill-name>` | `feat/experimental/uipath-maestro-bpmn` |
| Experimental change to existing skill | `feat/experimental/<skill-name>-<topic>` | `feat/experimental/uipath-rpa-coded-codegen` |

### Workflow

1. **Branch from `main`.** `git checkout -b feat/experimental/<skill-name>`.
2. **Push the branch early and iterate on it.** Push intermediate commits to your branch, not to `main`. The branch is publicly visible — that is expected and fine.
3. **Stay current with `main`.** Merge or rebase `main` into your branch regularly so the eventual integration PR stays small. Rebase if your branch has not been shared for review yet; merge once others are reviewing or building on it.
4. **Mark the skill as experimental in `SKILL.md`.** Preview / experimental status goes in the SKILL.md body, not in frontmatter (per [.claude/rules/skill-structure.md](.claude/rules/skill-structure.md)). Example callout under the H1:

   ```markdown
   # UiPath My New Skill

   > **Experimental.** This skill is under active development. Behavior, CLI flags, and reference structure may change without notice. Not recommended for production use.
   ```

5. **Merge to `main` only when the skill is usable end-to-end.** Do not merge work-in-progress commits straight to `main` just to keep the branch short — `main` is what users install. Open the integration PR when the skill triggers correctly, has at least the smoke + e2e tests required by the [Quality Checklist](#quality-checklist), and follows the rest of the contribution guidelines.

### Public-repo discipline

- **Never commit secrets, tokens, internal hostnames, customer data, or unreleased product/feature names that have not been publicly announced.** Use placeholders (`<TOKEN>`, `<TENANT_URL>`) in examples.
- **Write commit messages and PR titles as if a customer is reading them** — because they are.
- **If you accidentally commit a secret or confidential reference**, rotate the secret immediately, then contact a maintainer to coordinate history rewrite. Do not force-push over it yourself; the leaked value still needs to be rotated regardless.
- **Avoid screenshots of internal tools** in PR descriptions or skill assets.

## Hooks

Hooks are defined in `hooks/hooks.json` and run during plugin lifecycle events (e.g., `SessionStart`).

- Hook scripts must work **cross-platform** (Windows, macOS, Linux)
- Use `bash` as the shell — avoid OS-specific commands
- Keep hooks idempotent — safe to run multiple times
- Set appropriate timeouts (default: 180 seconds)

### Git Hooks

This repository uses pre-commit hooks to validate skill descriptions (1024-character limit). To enable them:

```bash
bash scripts/setup-hooks.sh
```

This configures git to use `.githooks/` and enables the skill description validator.

## Testing Skills

Skills are tested using [coder_eval](https://github.com/UiPath/coder_eval) — a framework that runs an AI agent against a task and scores the result. Tests live in `tests/tasks/<skill-name>/` and verify that the skill guides the agent to use the correct CLI commands, follow critical rules, and produce valid output.

There are three test types, distinguished by tags:

| Tag | Purpose | Cadence |
|-----|---------|---------|
| `smoke` | Skill triggers correctly, CLI produces valid output (1-5 simple scenarios) | Every PR |
| `integration` | Correct output across diverse scenarios, error paths, anti-patterns | Daily |
| `e2e` | Full lifecycle: Explore -> Plan -> Build -> Validate -> Deploy -> Run | Daily/weekly (check [Dashboard](https://dataexplorer.azure.com/dashboards/20cc55fe-33ae-4973-a951-855e76528219)) |

### Running Tests

```bash
cd tests
make install       # one-time: install coder-eval from GitHub
make all           # run all tests (smoke + integration + e2e)
make smoke         # run all smoke tests
make integration   # run all integration tests
make e2e           # run all end-to-end tests
make test-uipath-maestro-flow  # run all tests for a specific skill
```

### Adding Tests for a Skill

1. Create `tests/tasks/<skill-name>/` matching your skill folder name
2. Add at minimum **1 smoke test** and **1 e2e test** (required for every new skill PR)
3. Use minimal prompts — the goal is to test the skill's guidance quality, not hand-hold the agent
4. Tag every task appropriately: `smoke`, `integration`, or `e2e`
5. Follow the task ID pattern: `skill-<domain>-<capability>`
6. **Do not score self-reports.** Don't ask the agent to write a `report.json` / `recommendation.json` summary and then have `success_criteria` read that file back — the agent can write any value. Score real artifacts (`.flow` content, generated CSVs), real operations (`run_command` re-executes a validation), or behavior signals (`command_executed`, `command_not_executed`, `skill_triggered`).

See `tests/README.md` for the full task YAML template, success criteria reference, and examples from existing tests.

### Analyzing Test Coverage

Use the `/test-coverage` slash command to see what a skill's tests cover and where gaps exist:

```bash
/test-coverage uipath-maestro-flow   # single skill
/test-coverage all                    # all skills
```

This produces a markdown report in `tests/reports/` with component coverage, rule coverage, priority-ranked gaps, and concrete recommendations for new tests to write. Run this before and after adding tests to measure your progress.

### Scaffolding Tests with `/generate-tasks`

Use the `/generate-tasks` command to scaffold task YAML files from coverage gaps:

```bash
/generate-tasks uipath-platform              # generate tasks for highest-priority gaps
/generate-tasks uipath-platform authentication  # target a specific area
```

Generated tasks are **starting points for reference only** — review and improve them before relying on them for CI. Verify that CLI commands, success criteria, and prompts match the skill's actual behavior, and adjust weights and thresholds based on what matters most for your skill.

## Quality Checklist

Before submitting your PR, verify:

### SKILL.md
- [ ] Frontmatter has `name` matching the folder name
- [ ] Frontmatter `description` is under 1024 characters (enforced by pre-commit hook)
- [ ] Frontmatter `description` front-loads identity and unique signals, uses `→` redirects (not verbose TRIGGER/DO NOT TRIGGER)
- [ ] Critical Rules section exists with numbered, actionable rules
- [ ] CLI commands include exact flags and `--output json` where appropriate
- [ ] Anti-patterns / "What NOT to Do" section is included for non-trivial skills
- [ ] No references to other skills (skills must be self-contained)
- [ ] All links to reference files use relative paths and point to existing files

### References
- [ ] File names use kebab-case
- [ ] Guide files use `-guide.md` suffix
- [ ] Templates use `-template` suffix
- [ ] No duplicate content already covered in another skill's references

### Tests
- [ ] At least 1 smoke test in `tests/tasks/<skill-name>/`
- [ ] At least 1 e2e test in `tests/tasks/<skill-name>/`
- [ ] All tests tagged appropriately (`smoke`, `integration`, or `e2e`)

### General
- [ ] CODEOWNERS updated with your GitHub handle
- [ ] No secrets, tokens, or personal paths in any file
- [ ] No auto-generated or binary files committed (check `.gitignore`)
- [ ] Markdown is well-formed (no broken links, proper heading hierarchy)

## Pull Request Process

1. **Fork** this repository
2. **Create a feature branch** from `main` (e.g., `feat/add-my-skill`, `fix/uia-snapshot-docs`)
3. **Make your changes** following the guidelines above
4. **Run through the Quality Checklist**
5. **Submit a pull request** against `main`
   - Use a clear, descriptive title
   - Explain what your skill does and why it's needed
   - If modifying an existing skill, explain the motivation for the change
   - Tag relevant CODEOWNERS as reviewers

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| New skill | `feat/add-<skill-name>` | `feat/add-uipath-data-service` |
| Skill improvement | `feat/<skill-name>-<description>` | `feat/uia-add-drag-support` |
| Experimental / long-running work | `feat/experimental/<skill-name>` | `feat/experimental/uipath-maestro-bpmn` |
| Bug fix | `fix/<skill-name>-<description>` | `fix/flow-validate-edge-ports` |
| Documentation | `docs/<description>` | `docs/update-platform-cli-reference` |

### What to Expect

- A maintainer will review your PR, typically within a few business days
- CODEOWNERS for the affected paths will be automatically requested for review
- You may be asked to make changes — this is normal and collaborative
- Once approved, a maintainer will merge your PR

## Style Guide

### Markdown

- Use ATX-style headers (`#`, `##`, `###`)
- Use fenced code blocks with language identifiers (` ```bash `, ` ```yaml `, ` ```csharp `)
- Use tables for structured data (flags, options, mappings)
- Use `>` blockquotes for important notes and warnings
- Keep line lengths reasonable (no hard wrap requirement, but break long paragraphs)

### CLI Commands

- Always show the full command with all required flags
- Use `--output json` when the output needs to be parsed
- Use placeholders in angle brackets for user-provided values: `<PROJECT_DIR>`, `<FILE_PATH>`
- Show expected output format when it helps understanding

### Naming Conventions Summary

| Item | Convention | Example |
|------|-----------|---------|
| Skill folder | `uipath-<kebab-case>` | `uipath-rpa` |
| SKILL.md | Exactly `SKILL.md` (uppercase) | `SKILL.md` |
| Reference files | `kebab-case.md` | `commands-reference.md` |
| Guide files | `<topic>-guide.md` | `orchestrator-guide.md` |
| Template files | `<name>-template.md` | `codedworkflow-template.md` |
| Reference subdirs | `kebab-case/` | `integration-service/` |
| Asset subdirs | `kebab-case/` | `templates/` |

## Questions?

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/uipath-claude-plugins/issues).
