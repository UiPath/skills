# UiPath Agent Skills — Project Rules

This repository contains self-contained AI agent skills for UiPath automation development. Skills are installed as a Claude Code plugin and teach AI agents how to build, run, test, and deploy UiPath automations.

## Architecture

- **Skills are fully independent.** Each skill under `skills/` is self-contained. Skills cannot reference, import, or depend on other skills.
- **SKILL.md is the contract.** Every skill folder must have a `SKILL.md` with valid YAML frontmatter. This is the only file the plugin system reads to discover and activate skills.
- **No build system.** This repo contains only markdown documentation and shell scripts. There is no compilation or packaging step.

## Contribution Rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Key rules:

1. **Skill folder naming:** `uipath-<kebab-case>` under `skills/`
2. **SKILL.md frontmatter is required:** must include `name` (matching folder name) and `description` (with TRIGGER/DO NOT TRIGGER conditions)
3. **References use kebab-case filenames** with `-guide.md` and `-template.md` suffixes
4. **Update CODEOWNERS** when adding or modifying skill ownership
5. **No cross-skill references** — each skill must work in isolation
6. **No secrets or personal paths** in committed files
7. **CLI commands must use `--format json`** when output is parsed programmatically

## File Conventions

| File | Convention |
|------|-----------|
| `SKILL.md` | Required. Uppercase. YAML frontmatter + markdown body. |
| `references/*.md` | Kebab-case. Guides end with `-guide.md`. |
| `assets/templates/*` | Templates end with `-template.md` or `-template.<ext>`. |
| `hooks/*.sh` | Must be cross-platform (Windows/macOS/Linux). |

## When Reviewing or Editing Skills

- Read the existing SKILL.md before making changes
- Preserve the Critical Rules section — these prevent expensive agent mistakes
- Validate YAML frontmatter — broken frontmatter breaks skill discovery
- Ensure `description` field has both TRIGGER and DO NOT TRIGGER conditions
