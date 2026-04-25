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
description: "<identity> (<unique signal>). <core actions>. For <confusing-case>→<correct-skill>."
---
```

### Validation Rules

- `name` MUST exactly match the parent folder name
- `description` MUST be under 1024 characters. Claude Code truncates `description` + `when_to_use` at 1,536 chars in the skill listing ([source](https://code.claude.com/docs/en/skills.md)); 1024 is the repo cap to keep descriptions focused and leave headroom
- `description` MUST start with `[PREVIEW]` when the skill is first created. Remove the tag only when the skill is considered stable
- `description` MUST front-load the skill identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`, `interact`) within the first ~100 characters
- `description` MUST include compact redirects for commonly confused sibling skills using `→` notation (e.g., `For XAML→uipath-rpa`)
- `description` MUST NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — these waste characters and get truncated
- All frontmatter fields (`allowed-tools`, `user-invocable`, etc.) MUST be at the top level — NOT nested under a `metadata:` key (Claude Code only reads top-level fields)
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
| Skill folder | `uipath-<kebab-case>` | `uipath-rpa` |
| Reference files | `<topic>-<type>.md` | `commands-reference.md` |
| Guide files | `<topic>-guide.md` | `orchestrator-guide.md` |
| Template files | `<name>-template.<ext>` | `codedworkflow-template.md` |
| Subdirectories | `kebab-case/` | `integration-service/` |

## Content Rules

- Skills MUST be self-contained — no references to other skills
- CLI commands MUST include `--output json` when output is parsed programmatically
- All file links MUST use relative paths from the SKILL.md location
- All file links MUST point to files that actually exist in the repo
- No secrets, tokens, credentials, or personal filesystem paths

## Sharing Content Across Skills

Skills MUST be self-contained: no `../<other-skill>/...` paths in any markdown file. When a plugin user installs a skill, sibling skills may not be co-located, may not be installed at all, or may resolve to different paths than the agent expects. Cross-skill links break in those cases.

When the same content genuinely needs to appear in two or more skills, register a synced copy:

```bash
bash scripts/sync-files.sh --add <source-path> <copy-path>
```

This appends an entry to `.github/synced-files.yml` and creates `<copy-path>` as a byte-for-byte clone of `<source-path>`. From that point on:

1. **Always edit the source.** Never edit a copy directly.
2. **Run `bash scripts/sync-files.sh --apply`** after editing the source to refresh every copy.
3. **Commit the source and the refreshed copies together.**

CI (`.github/workflows/validate-synced-files.yml`) blocks any PR where a copy diverges from its source. The local `.githooks/pre-commit` chain runs the same check and fails the commit early for contributors who ran `bash scripts/setup-hooks.sh`.

Copies are pure clones — no headers, no markers, no transformations — so the agent reads them identically to the canonical version. The manifest is the only place that records the sync relationship; the copy file itself stays pristine.
