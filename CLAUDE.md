# UiPath Agent Skills — Project Rules

This repository contains self-contained AI agent skills for UiPath automation development. Skills are installed as a Claude Code plugin and teach AI agents how to build, run, test, and deploy UiPath automations.

## Architecture

- **Skills are self-contained.** Each skill under `skills/` must function on its own: it MUST NOT import, inline, or read another skill's files, and MUST still deliver its core value if sibling skills are absent. A skill MAY delegate a task to a sibling skill in this same plugin at runtime (e.g., spawn a subagent that hands an artifact edit to the artifact's owning domain skill) when that work is the sibling's domain — provided the delegation degrades gracefully (the skill still presents an actionable result when the sibling is unavailable).
- **SKILL.md is the contract.** Every skill folder must have a `SKILL.md` with valid YAML frontmatter. This is the only file the plugin system reads to discover and activate skills.
- **No build system.** This repo contains only markdown documentation and scripts. There is no compilation or packaging step.
- **Twin hook scripts — keep in sync.** Every session hook exists twice: `hooks/<name>.sh` (bash — macOS, Linux, Windows with Git Bash) and `hooks/<name>.ps1` (PowerShell 5.1/7+ — Windows without Git Bash). The two files are behavioral twins: **any change to one REQUIRES the equivalent change to the other in the same PR.** `hooks/hooks.json` registers a single bash/PowerShell polyglot command per event that dispatches to the twin matching the executing shell — do not add a `shell` field to these entries; the polyglot depends on Claude Code's default shell selection.

## Contribution Rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Key rules:

1. **Skill folder naming:** `uipath-<kebab-case>` under `skills/`
2. **SKILL.md frontmatter is required:** must include `name` (matching folder name) and `description` (with TRIGGER/DO NOT TRIGGER conditions)
3. **References use kebab-case filenames** with `-guide.md` and `-template.md` suffixes
4. **Update CODEOWNERS** when adding or modifying skill ownership
5. **No structural cross-skill dependencies** — a skill must work in isolation (never import or read another skill's files); runtime delegation to a same-plugin sibling skill is allowed when it degrades gracefully
6. **No secrets or personal paths** in committed files
7. **CLI commands must use `--output json`** when output is parsed programmatically

## File Conventions

| File | Convention |
|------|-----------|
| `SKILL.md` | Required. Uppercase. YAML frontmatter + markdown body. |
| `references/*.md` | Kebab-case. Guides end with `-guide.md`. |
| `assets/templates/*` | Templates end with `-template.md` or `-template.<ext>`. |
| `hooks/*.sh` + `hooks/*.ps1` | Session hooks ship as twin implementations with the same basename — bash and PowerShell (5.1 and 7+ compatible). The twins MUST stay behaviorally identical: a change to one requires the same change to the other in the same PR. Dispatched by the polyglot commands in `hooks/hooks.json`. |

## When Reviewing or Editing Skills

- Read the existing SKILL.md before making changes
- Preserve the Critical Rules section — these prevent expensive agent mistakes
- Validate YAML frontmatter — broken frontmatter breaks skill discovery
- Ensure `description` field has both TRIGGER and DO NOT TRIGGER conditions

## When Writing or Modifying Tests

Tests live in `tests/tasks/<skill-name>/` as coder_eval task YAMLs. Before authoring or editing a task, read [tests/README.md](tests/README.md) for the full framework: tag taxonomy, experiment configs, success-criteria types, weight guidance, and the `/generate-task` and `/test-coverage` slash commands. Repo-specific authoring constraints (workflow, required tags, sandbox rules, anti-patterns) are in [.claude/rules/test-writing.md](.claude/rules/test-writing.md).
