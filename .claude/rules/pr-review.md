# Pull Request Review Rules

When reviewing or creating pull requests for this repository, enforce these rules.

## Before Approving a PR

### New Skill Checklist

- [ ] Folder is under `skills/` and named `uipath-<kebab-case>`
- [ ] `SKILL.md` exists with valid YAML frontmatter
- [ ] `name` field matches the folder name exactly
- [ ] `description` field includes TRIGGER and DO NOT TRIGGER conditions
- [ ] Critical Rules section exists with numbered rules
- [ ] No cross-skill references (skill is fully self-contained)
- [ ] Reference files use kebab-case naming
- [ ] All relative links resolve to existing files
- [ ] CODEOWNERS has been updated with the new skill path
- [ ] No secrets, tokens, or personal paths committed

### Existing Skill Modification Checklist

- [ ] SKILL.md frontmatter is still valid after changes
- [ ] Critical Rules have not been removed without justification in the PR description
- [ ] No new cross-skill dependencies introduced
- [ ] Reference file naming conventions preserved
- [ ] Changes are scoped to the skill being modified (no unrelated changes)

### Hook Changes Checklist

- [ ] Script works cross-platform (Windows, macOS, Linux)
- [ ] Uses `bash` shell syntax (not cmd.exe or PowerShell-specific)
- [ ] Is safe to run multiple times
- [ ] Has appropriate timeout configured in hooks.json
- [ ] Does not hardcode OS-specific paths

## Commit and Branch Conventions

- Branch names: `feat/<description>`, `fix/<description>`, `docs/<description>`
- Commit messages: concise, imperative mood, describe the "why" not just the "what"
- One logical change per PR — don't mix new skills with fixes to existing ones
