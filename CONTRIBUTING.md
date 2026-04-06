# Contributing to UiPath Agent Skills

Thank you for your interest in contributing! Whether you're adding a new skill, improving an existing one, fixing a bug, or enhancing documentation — we appreciate your help.

## Table of Contents

- [Repository Structure](#repository-structure)
- [Adding a New Skill](#adding-a-new-skill)
- [Modifying an Existing Skill](#modifying-an-existing-skill)
- [Hooks](#hooks)
- [Quality Checklist](#quality-checklist)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Repository Structure

```
.
├── .claude-plugin/            # Plugin manifest and marketplace config
│   ├── plugin.json            # Plugin name, version, skills directory pointer
│   └── marketplace.json       # Claude Code marketplace registration
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
├── CODEOWNERS                 # GitHub ownership by skill/path
├── README.md                  # Project overview and quick start
├── CONTRIBUTING.md            # This file
└── LICENSE                    # MIT
```

### Key Principles

- **Skills are self-contained.** Each skill is an independent folder under `skills/`. Skills cannot reference or depend on other skills.
- **SKILL.md is the entry point.** The AI agent reads `SKILL.md` first. Everything the agent needs to know must be reachable from there.
- **References are supplementary.** Large reference material goes in `references/` subdirectories, linked from SKILL.md.
- **No build system.** This is a documentation and skill-definitions repository. There is no compilation, bundling, or package publishing from this repo.

## Adding a New Skill

### 1. Choose a Name

Skill folders follow the naming convention: `uipath-<domain>` or `uipath-<tool>`.

- Use **kebab-case** (lowercase, hyphens between words)
- Prefix with `uipath-` for UiPath-related skills
- Be descriptive but concise: `uipath-coded-workflows`, `uipath-servo`, `uipath-maestro-flow`

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

SKILL.md is the most important file. It uses YAML frontmatter followed by markdown content.

#### Frontmatter Format

```yaml
---
name: uipath-<your-skill>
description: "<identity> (<unique signal>). <core actions>. For <confusing-case>→<correct-skill>."
---
```

> **250-character limit.** Claude Code truncates non-bundled skill descriptions at 250 characters in the system prompt — anything beyond is invisible to the model. The pre-commit hook enforces this. Front-load the skill identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`, `servo`) within the first ~100 characters.

**Required frontmatter fields:**

| Field | Description |
|-------|-------------|
| `name` | Exact skill identifier, must match the folder name |
| `description` | Under 250 chars. Front-load identity and unique signals, then core actions, then compact `→` redirects for commonly confused sibling skills. Do NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — they waste characters. |

**Optional frontmatter fields:**

| Field | Description |
|-------|-------------|
| `allowed-tools` | Restricts which tools the skill can use (e.g., `Bash, Read, Write, Glob, Grep`) |
| `user-invocable` | Defaults to `true`. Set to `false` if the skill should only be discoverable by the agent, not directly invocable by users |

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

## Hooks

Hooks are defined in `hooks/hooks.json` and run during plugin lifecycle events (e.g., `SessionStart`).

- Hook scripts must work **cross-platform** (Windows, macOS, Linux)
- Use `bash` as the shell — avoid OS-specific commands
- Keep hooks idempotent — safe to run multiple times
- Set appropriate timeouts (default: 180 seconds)

### Git Hooks

This repository uses pre-commit hooks to validate skill descriptions (250-character limit). To enable them:

```bash
bash scripts/setup-hooks.sh
```

This configures git to use `.githooks/` and enables the skill description validator.

## Quality Checklist

Before submitting your PR, verify:

### SKILL.md
- [ ] Frontmatter has `name` matching the folder name
- [ ] Frontmatter `description` is under 250 characters (enforced by pre-commit hook)
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

### General
- [ ] CODEOWNERS updated with your GitHub handle
- [ ] No secrets, tokens, or personal paths in any file
- [ ] No auto-generated or binary files committed (check `.gitignore`)
- [ ] Markdown is well-formed (no broken links, proper heading hierarchy)

## Pull Request Process

1. **Fork** this repository
2. **Create a feature branch** from `main` (e.g., `feat/add-my-skill`, `fix/servo-snapshot-docs`)
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
| Skill improvement | `feat/<skill-name>-<description>` | `feat/servo-add-drag-support` |
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
| Skill folder | `uipath-<kebab-case>` | `uipath-coded-workflows` |
| SKILL.md | Exactly `SKILL.md` (uppercase) | `SKILL.md` |
| Reference files | `kebab-case.md` | `commands-reference.md` |
| Guide files | `<topic>-guide.md` | `orchestrator-guide.md` |
| Template files | `<name>-template.md` | `codedworkflow-template.md` |
| Reference subdirs | `kebab-case/` | `integration-service/` |
| Asset subdirs | `kebab-case/` | `templates/` |

## Questions?

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/uipath-claude-plugins/issues).
