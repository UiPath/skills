# Skill Structure Rules

These rules enforce consistency across all skills in this repository.

## Folder Layout

Every skill MUST follow this structure:

```
skills/uipath-<name>/
├── SKILL.md              # Required — skill definition
├── references/           # Optional — supporting docs
│   └── *.md              # Kebab-case filenames
└── assets/               # Optional — templates, static files
    └── templates/        # Optional — code/config templates
```

## SKILL.md Frontmatter

Every SKILL.md MUST begin with valid YAML frontmatter containing at minimum:

```yaml
---
name: uipath-<name>
description: "<what it does>. TRIGGER when: <activation conditions>. DO NOT TRIGGER when: <exclusion conditions>."
---
```

### Validation Rules

- `name` MUST exactly match the parent folder name
- `description` MUST include both "TRIGGER when:" and "DO NOT TRIGGER when:" clauses
- Frontmatter MUST be valid YAML (no tabs, proper quoting of strings with colons)

## SKILL.md Body Structure

The markdown body SHOULD follow this order:

1. **Title** (`# Skill Title`)
2. **When to Use This Skill** — bullet list of activation scenarios
3. **Critical Rules** — numbered list of mandatory constraints
4. **Quick Start / Workflow** — step-by-step common use case
5. **Reference Navigation** — links to files in `references/`
6. **Anti-patterns** (optional) — "What NOT to Do" section

## Naming Conventions

| Item | Pattern | Example |
|------|---------|---------|
| Skill folder | `uipath-<kebab-case>` | `uipath-coded-workflows` |
| Reference files | `<topic>-<type>.md` | `commands-reference.md` |
| Guide files | `<topic>-guide.md` | `orchestrator-guide.md` |
| Template files | `<name>-template.<ext>` | `codedworkflow-template.md` |
| Subdirectories | `kebab-case/` | `integration-service/` |

## Content Rules

- Skills MUST be self-contained — no references to other skills
- CLI commands MUST include `--format json` when output is parsed programmatically
- All file links MUST use relative paths from the SKILL.md location
- All file links MUST point to files that actually exist in the repo
- No secrets, tokens, credentials, or personal filesystem paths
