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
- [ ] Registered in `assets/skill-status.json` and grouped in `skills.sh.json` (run `python3 scripts/check-skill-status.py` and `python3 scripts/check-skills-sh.py`)
- [ ] No secrets, tokens, or personal paths committed

### Existing Skill Modification Checklist

- [ ] SKILL.md frontmatter is still valid after changes
- [ ] Critical Rules have not been removed without justification in the PR description
- [ ] No new structural cross-skill dependencies (runtime delegation to a same-plugin sibling that degrades gracefully is allowed)
- [ ] Reference file naming conventions preserved
- [ ] **If the PR renames or removes a skill folder:** `skills.sh.json` and `assets/skill-status.json` are updated in the same PR — the old name is gone from both and the new one is present. Neither file is derived from disk, so a stale entry has no other symptom than the `Validate skills.sh.json against skills/` check
- [ ] Changes are scoped to the skill being modified (no unrelated changes)

### Hook Changes Checklist

- [ ] Script works cross-platform (Windows, macOS, Linux)
- [ ] **No hook shell scripts:** telemetry entries pipe the raw payload to `uip track --hook` (derivation lives in UiPath/cli `track-hook.ts`); every other session hook is a `hooks/<name>.mjs` run by `node` — no new `.sh`/`.ps1` hook implementations (the retired twins required hand-kept sync and a `.ps1` signing gate, and failed under Group-Policy execution policy)
- [ ] `.mjs` hooks are never-fail (always exit 0), read the payload from stdin, and use only Node.js built-ins (no npm dependencies — the plugin ships no `node_modules`)
- [ ] `hooks.json` entries keep the bash/PowerShell polyglot command shapes (see CONTRIBUTING.md § Hooks): no `shell` field, both branches guard for the missing binary with a silent `exit 0`, the telemetry PowerShell branch resolves `uip.cmd` (never bare `uip` — PowerShell would prefer the policy-blockable `uip.ps1` shim), the sh branch never contains the sequence `#>`, and the PowerShell branch stays wrapped in the `: <<'POLYEOF' … POLYEOF` heredoc (zsh parses the whole command up front and fails on unwrapped PowerShell syntax)
- [ ] Is safe to run multiple times
- [ ] Has appropriate timeout configured in hooks.json
- [ ] Does not hardcode OS-specific paths

## Commit and Branch Conventions

- Branch names: `feat/<description>`, `fix/<description>`, `docs/<description>`
- Commit messages: concise, imperative mood, describe the "why" not just the "what"
- One logical change per PR — don't mix new skills with fixes to existing ones
