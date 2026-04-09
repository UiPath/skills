# Code Review Guidelines

This repository contains markdown skill definitions for the UiPath Claude Code plugin. There is no source code, build system, or runtime — only markdown files, YAML frontmatter, shell scripts, and coder_eval task YAMLs.

Review PRs against the criteria below, ordered by severity.

## 1. Frontmatter Validation

Every `SKILL.md` has YAML frontmatter that the plugin system parses to discover and match skills. Broken frontmatter silently breaks skill activation.

**Checks:**
- `name` field exactly matches the parent folder name (e.g., `skills/uipath-rpa/` → `name: uipath-rpa`)
- `description` is under 250 characters (run `bash hooks/validate-skill-descriptions.sh skills/<name>/SKILL.md`)
- `description` front-loads the skill identity and unique file/domain signals (`.cs`, `.xaml`, `.flow`, `servo`) in the first ~100 chars
- `description` uses compact `→` redirects for sibling skills (e.g., `For XAML→uipath-rpa`) — NOT verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses
- New skills start `description` with `[PREVIEW]`
- All frontmatter fields (`name`, `description`, `allowed-tools`, `user-invocable`) are at the top level — NOT nested under `metadata:`
- Frontmatter is valid YAML: no tabs, strings with colons are quoted

**Severity:** Critical if broken, High if conventions violated.

## 2. E2E Test Coverage

> **Every new skill MUST have coder_eval tests in `tests/tasks/<skill-name>/`.**

This repo uses [coder_eval](https://github.com/UiPath/coder_eval) to verify that skills guide an AI agent to use the correct CLI commands and produce valid output. Tests run in CI via `.github/workflows/e2e-skills.yml`.

**When a PR adds a new skill folder under `skills/`:**

1. Verify `tests/tasks/<skill-name>/` exists with at least one `.yaml` task file
2. Verify each task file follows conventions (see `tests/README.md`):
   - `task_id` matches the pattern `skill-<domain>-<capability>`
   - `tags` includes `smoke` (required for CI) and the skill domain
   - `agent.plugins` references `$SKILLS_REPO_PATH` so the plugin loads in the sandbox
   - `initial_prompt` is minimal — describes the goal, not the steps (the skill should teach the agent)
   - `success_criteria` validates key CLI commands (`command_executed`), output files (`file_exists`, `file_contains`, `json_check`), or both
   - `max_iterations: 2` and `llm_reviewer.enabled: true` are set
3. If tests are entirely missing, flag as **Critical** — the PR cannot merge

**When a PR substantially changes an existing skill** (new CLI workflows, changed commands):
- Check whether existing tasks in `tests/tasks/<skill-name>/` still cover the updated behavior
- Flag new capabilities that lack a test task as **Medium**

## 3. Skill Body Structure

The markdown body of SKILL.md is what the AI agent reads. Poor structure → agent mistakes → wasted compute.

**Required sections (in order):**
1. **Title** (`# Skill Title`)
2. **When to Use This Skill** — bullet list of activation scenarios
3. **Critical Rules** — numbered, actionable constraints the agent MUST follow
4. **Quick Start / Workflow** — step-by-step for the primary use case
5. **Reference Navigation** — links to files in `references/` (if any)

**Checks:**
- Critical Rules section exists and rules are numbered (not bullet points)
- CLI commands are copy-paste ready with all required flags
- CLI commands use `--output json` when the agent needs to parse output
- Placeholders use `<UPPER_SNAKE_CASE>` in angle brackets
- Error handling is specified: what the agent should do when a command fails, max retries
- Anti-patterns / "What NOT to Do" section exists for non-trivial skills
- No cross-skill references — each skill must work in complete isolation
- SKILL.md is not excessively long — large reference material should be extracted to `references/` files

**Severity:** High if Critical Rules are missing or removed. Medium for other structural issues.

## 4. Reference & Asset Files

**Checks:**
- Reference files use kebab-case naming: `<topic>-guide.md`, `<topic>-reference.md`
- Template files use `-template` suffix: `<name>-template.md`, `<name>-template.cs`
- Every file under `references/` and `assets/` is reachable via a link from SKILL.md (no orphaned files)
- All relative links in SKILL.md actually resolve to files that exist in the repo
- Heading hierarchy does not skip levels (no `##` followed by `####`)
- Code blocks have language identifiers: ` ```bash `, ` ```yaml `, ` ```csharp `, ` ```json `
- No copy-pasted content between SKILL.md and reference files — SKILL.md should link to references for detail
- No two reference files with >50% overlapping content

**Severity:** High for broken links or orphaned files. Medium for naming/formatting.

## 5. Repository Hygiene

**Checks:**
- `CODEOWNERS` has an entry for any new or moved skill path (e.g., `/skills/uipath-<name>/`)
- No secrets, tokens, API keys, or personal filesystem paths in any file
- No binary files or images committed (use text formats: ASCII diagrams, markdown tables, mermaid)
- Shell scripts in `hooks/` are cross-platform (bash, not cmd.exe or PowerShell-specific)
- Changes are scoped to the skill being modified — no drive-by changes to unrelated skills
- `.claude-plugin/plugin.json` is only modified for version bumps, not in skill PRs

**Severity:** Critical for leaked secrets. High for missing CODEOWNERS. Medium for scoping issues.

## Severity Levels

| Level | Meaning | Examples |
|-------|---------|---------|
| **Critical** | Blocks skill discovery or leaks secrets — must fix | Broken frontmatter, name mismatch, missing e2e tests for new skills, committed credentials |
| **High** | Skill will work but poorly or breaks conventions — must fix | Missing Critical Rules, cross-skill dependencies, broken links, no CODEOWNERS entry |
| **Medium** | Quality gap — should fix | No anti-patterns section, inconsistent placeholders, missing error handling, weak test criteria |
| **Low** | Polish — nice to have | Section ordering, minor wording, formatting |

## Output Format

Post review as a **single PR comment** (not inline comments):

```markdown
## Summary

<1-2 sentences: what this PR does>

## Change-by-Change Review

#### 1. <file path or logical change>
<Severity: Critical / High / Medium / Low / OK>
<What changed, whether it's correct, specific issues with file:line references>

#### 2. <file path or logical change>
...

## What's Missing

<Things that should have been added/changed but weren't. Always include this section.>
- Example: Missing e2e tests in tests/tasks/<skill-name>/
- Example: CODEOWNERS not updated for new skill path
- Example: No anti-patterns section in SKILL.md
- If nothing: "Nothing identified."

## Area Ratings

| Area | Status | Notes |
|------|--------|-------|
| Frontmatter | OK / Issue | - |
| E2E Tests | OK / Issue | - |
| Skill Body | OK / Issue | - |
| References & Assets | OK / Issue | - |
| Repo Hygiene | OK / Issue | - |

## Issues for Manual Review

<Things the automated reviewer cannot verify — e.g., whether CLI commands are correct for the tool's actual API, whether the skill conflicts with another skill's trigger scope, domain-specific accuracy of instructions. If none: "None found.">

## Conclusion

<Overall: approve, request changes, or note concerns>
```

**Rules for the review output:**
- Only report real issues — reference file path and line number for each
- Only elaborate on Medium or above — mark clean items as OK
- If the PR is fully clean: just post Summary + Conclusion with "No issues found."
- Read existing PR comments before posting to avoid repeating resolved issues
