# UiPath Agent Skills — Project Rules

This repository contains self-contained AI agent skills for UiPath automation development. Skills are installed as a Claude Code plugin and teach AI agents how to build, run, test, and deploy UiPath automations.

## Architecture

- **Skills are runtime-independent.** Each skill under `skills/` is self-contained — no imports from another skill's `references/` or `assets/`. Disambiguation pointers in the `description` field (`For X→uipath-other-skill`) are required for sibling clarity, not violations.
- **SKILL.md is the contract.** Every skill folder must have a `SKILL.md` with valid YAML frontmatter. This is the only file the plugin system reads to discover and activate skills.
- **No build system.** This repo contains only markdown documentation and shell scripts. There is no compilation or packaging step.

## Canonical SKILL.md Contract

The authoritative SKILL.md frontmatter contract lives in **[.claude/rules/skill-structure.md](.claude/rules/skill-structure.md)**. CONTRIBUTING.md ([Canonical SKILL.md Contract](CONTRIBUTING.md#canonical-skillmd-contract)) mirrors it for human contributors. Both are kept in sync; this CLAUDE.md is a brief overview only.

**Required frontmatter:**
- `name` — exactly matches folder name
- `description` — ≤ 1024 chars, front-loads identity, uses `→` redirects for sibling disambiguation

**Optional frontmatter** (all currently used in real skills): `when_to_use`, `allowed-tools`, `user-invocable`.

Do **not** use `TRIGGER when:` / `DO NOT TRIGGER when:` clauses in `description` — they waste characters and have been replaced by `→` redirects.

## Contribution Rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Key rules:

1. **Skill folder naming:** `uipath-<kebab-case>` under `skills/`
2. **SKILL.md frontmatter is required:** `name` (matching folder name) and `description`. See the [Canonical SKILL.md Contract](CONTRIBUTING.md#canonical-skillmd-contract) for the full schema, including supported optional fields.
3. **References use kebab-case filenames** with `-guide.md` and `-template.md` suffixes
4. **Update CODEOWNERS** when adding or modifying skill ownership
5. **No runtime cross-skill imports** — each skill must work in isolation. `→` redirects in `description` are required for disambiguation, not violations.
6. **No secrets or personal paths** in committed files
7. **CLI commands must use `--output json`** when output is parsed programmatically

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
- Run `bash hooks/validate-skill-descriptions.sh skills/<your-skill>/SKILL.md` to check `name` matches the folder, required fields are present, and length caps hold
