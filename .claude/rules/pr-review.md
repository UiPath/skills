# Pull Request Review Rules

When reviewing or creating pull requests for this repository, enforce these rules.

## Before Approving a PR

### New Skill Checklist

- [ ] Folder is under `skills/` and named `uipath-<kebab-case>`
- [ ] `SKILL.md` exists with valid YAML frontmatter
- [ ] `name` field matches the folder name exactly
- [ ] `description` has under 1024 characters and is concise
- [ ] Critical Rules section exists with numbered rules
- [ ] No structural cross-skill dependencies (does not import or read another skill's files; runtime delegation to a same-plugin sibling that degrades gracefully is allowed)
- [ ] Reference files use kebab-case naming
- [ ] All relative links resolve to existing files
- [ ] CODEOWNERS has been updated with the new skill path
- [ ] No secrets, tokens, or personal paths committed

### Existing Skill Modification Checklist

- [ ] SKILL.md frontmatter is still valid after changes
- [ ] Critical Rules have not been removed without justification in the PR description
- [ ] No new structural cross-skill dependencies (runtime delegation to a same-plugin sibling that degrades gracefully is allowed)
- [ ] Reference file naming conventions preserved
- [ ] Changes are scoped to the skill being modified (no unrelated changes)

### Hook Changes Checklist

- [ ] Script works cross-platform (Windows, macOS, Linux)
- [ ] **Twin updated:** session hooks exist as `.sh` + `.ps1` pairs — a change to one file includes the equivalent change to its twin in the same PR
- [ ] `.ps1` scripts use PowerShell syntax compatible with BOTH Windows PowerShell 5.1 and PowerShell 7+ (no `&&`/`||` pipeline chains, no ternary or null-conditional operators)
- [ ] `hooks.json` entries keep the bash/PowerShell polyglot command shape (see CONTRIBUTING.md § Hooks): no `shell` field, the sh branch never contains the sequence `#>`, and the PowerShell branch stays wrapped in the `: <<'POLYEOF' … POLYEOF` heredoc (zsh parses the whole command up front and fails on unwrapped PowerShell syntax)
- [ ] Is safe to run multiple times
- [ ] Has appropriate timeout configured in hooks.json
- [ ] Does not hardcode OS-specific paths

## Commit and Branch Conventions

- Branch names: `feat/<description>`, `fix/<description>`, `docs/<description>`
- Commit messages: concise, imperative mood, describe the "why" not just the "what"
- One logical change per PR — don't mix new skills with fixes to existing ones
