# UiPath Agent Skills — Project Rules

This repository contains self-contained AI agent skills for UiPath automation development. Skills are installed as a Claude Code plugin and teach AI agents how to build, run, test, and deploy UiPath automations.

## Architecture

- **Skills are self-contained.** Each skill under `skills/` must function on its own: it MUST NOT import, inline, or read another skill's files, and MUST still deliver its core value if sibling skills are absent. A skill MAY delegate a task to a sibling skill in this same plugin at runtime (e.g., spawn a subagent that hands an artifact edit to the artifact's owning domain skill) when that work is the sibling's domain — provided the delegation degrades gracefully (the skill still presents an actionable result when the sibling is unavailable).
- **SKILL.md is the canonical default contract.** Every skill folder must have a complete `SKILL.md` with valid YAML frontmatter. Local/default consumers can understand it without a flavor manifest or runtime resolver. Shared guidance stays there; only genuinely different passages may be enclosed by named flavor-block comments.
- **Custom flavors inherit the complete catalog and contain only sparse exceptions.** Every flavor ships every canonical skill. Files under `skill-flavors/<flavor>/<skill>/` mirror canonical skill paths and contain only complete replacement blocks. If no override exists, the canonical file is intentionally reused unchanged. Do not duplicate a whole skill merely to change a few paragraphs.
- **Build files before packages.** Build complete `default` and custom-flavor skill trees, validate those final files, and only then stage packages. Consumers must copy a finished tree; they must not interpret flavor markers or compose Markdown at runtime.
- **Twin hook scripts — keep in sync.** Every session hook exists twice: `hooks/<name>.sh` (bash — macOS, Linux, Windows with Git Bash) and `hooks/<name>.ps1` (PowerShell 5.1/7+ — Windows without Git Bash). The two files are behavioral twins: **any change to one REQUIRES the equivalent change to the other in the same PR.** `hooks/hooks.json` registers a single bash/PowerShell polyglot command per event that dispatches to the twin matching the executing shell — do not add a `shell` field to these entries; the polyglot depends on Claude Code's default shell selection.

## Contribution Rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Key rules:

1. **Skill folder naming:** `uipath-<kebab-case>` under `skills/`
2. **SKILL.md frontmatter is required:** must include `name` (matching folder name) and `description` (with TRIGGER/DO NOT TRIGGER conditions)
3. **References use kebab-case filenames** with `-guide.md` and `-template.md` suffixes
4. **Update CODEOWNERS** when adding or modifying skill ownership
5. **Update the two skill registries in the SAME PR that adds, renames, or removes a skill folder.** Adding or renaming `skills/<name>/` requires the matching edit to `assets/skill-status.json` (lifecycle status) AND to `skills.sh.json` (display grouping); removing a skill requires deleting its entry from both. Neither file is discovered from disk, so nothing else in the build notices when they drift. Verify both before opening the PR:

   ```bash
   python3 scripts/check-skill-status.py --write-readme   # regenerates the README table
   python3 scripts/check-skills-sh.py                     # add/rename/remove: must print OK
   ```

   Full change→edit table, the `--fix` limits, and how pre-existing drift is reported: [`.claude/rules/skill-structure.md` § skills.sh Grouping](.claude/rules/skill-structure.md).
6. **No structural cross-skill dependencies** — a skill must work in isolation (never import or read another skill's files); runtime delegation to a same-plugin sibling skill is allowed when it degrades gracefully
7. **No secrets or personal paths** in committed files
8. **CLI commands must use `--output json`** when output is parsed programmatically
9. **Review new skills for every custom flavor.** They are included automatically; add the smallest sparse override wherever canonical guidance is not safe for a target environment

## File Conventions

| File | Convention |
|------|-----------|
| `SKILL.md` | Required. Uppercase. YAML frontmatter + markdown body. |
| `references/*.md` | Kebab-case. Guides end with `-guide.md`. |
| `skill-flavors/<flavor>/<skill>/**/*.md` | Optional sparse overrides at paths relative to `skills/`; contain only named replacement blocks. |
| `<!--skill-flavor:<name>:start\|end-->` | Compact, whitespace-free column-one boundary around the smallest canonical passage that differs by flavor. Names are lowercase kebab-case and unique within a file; indent the enclosed Markdown, never the boundary. |
| `assets/templates/*` | Templates end with `-template.md` or `-template.<ext>`. |
| `skills.sh.json` | Display grouping for the repo's skills.sh page. Every `skills/<name>/` appears in exactly one grouping. Edit it in the same PR that adds, renames, or removes a skill folder — validate with `python3 scripts/check-skills-sh.py`. |
| `assets/skill-status.json` | Lifecycle status (`stable` / `preview` / `in-development`) for every skill — the single source of truth. Edit in the same PR as the skill folder; regenerate the README table with `python3 scripts/check-skill-status.py --write-readme`. |
| `hooks/*.sh` + `hooks/*.ps1` | Session hooks ship as twin implementations with the same basename — bash and PowerShell (5.1 and 7+ compatible). The twins MUST stay behaviorally identical: a change to one requires the same change to the other in the same PR. Dispatched by the polyglot commands in `hooks/hooks.json`. |

## When Reviewing or Editing Skills

- Before changing flavor markers, overrides, discovery, package construction, publishing, or flavor CI, read `.claude/skills/manage-skill-flavors/SKILL.md` completely and follow its reference-routing instructions
- Read the existing SKILL.md before making changes
- Read every matching flavor override before changing a canonical marked passage; prefer an empty additive extension block over replacing a shared table, list, or navigation section
- Preserve the Critical Rules section — these prevent expensive agent mistakes
- Validate YAML frontmatter — broken frontmatter breaks skill discovery
- Ensure `description` field has both TRIGGER and DO NOT TRIGGER conditions
- When canonical flavor blocks or custom overrides change, run `npm run skills:validate`, `npm run skills:build`, and `npm run skills:pack`; inspect the actual generated tarballs before publishing
- Preserve normal root `npm pack` and `npm publish` as backward-compatible default-only commands: they must compose marker-free skills transactionally and restore canonical sources. Keep `npm run skills:pack` as the all-flavor build/verification command used by CI and isolated flavor publishers, not as the default release path

## When Writing or Modifying Tests

Tests live in `tests/tasks/<skill-name>/` as coder_eval task YAMLs. Before authoring or editing a task, read [tests/README.md](tests/README.md) for the full framework: tag taxonomy, experiment configs, success-criteria types, weight guidance, and the `/generate-task` and `/test-coverage` slash commands. Repo-specific authoring constraints (workflow, required tags, sandbox rules, anti-patterns) are in [.claude/rules/test-writing.md](.claude/rules/test-writing.md).

## Codereval Blob Results

- Codereval dashboard results are stored in Azure Blob Storage account `coderevaltests`, container `runs`.
- Run IDs are timestamped like `YYYY-MM-DD_HH-MM-SS`; list today's runs with prefix `YYYY-MM-DD`.
- The run summary is `<run-id>/run.json`; per-task results live under `<run-id>/<variant>/<task-id>/<replicate>/task.json`.
