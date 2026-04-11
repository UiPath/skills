# Code Review Guidelines

This repository contains markdown skill definitions for the UiPath Claude Code plugin. There is no source code, build system, or runtime — only markdown files, YAML frontmatter, shell scripts, and coder_eval task YAMLs.

## Review Criteria

Apply the scoring dimensions from [`.claude/rules/skill-review.md`](../.claude/rules/skill-review.md) to all changed skill files. That file defines the full evaluation framework (Structure, Consistency, Logic & Completeness, Duplication, LLM Usability, Marketplace & Integration).

In addition to those dimensions, enforce the PR-specific checks below.

## PR-Specific Checks

### E2E Test Coverage

This repo uses [coder_eval](https://github.com/UiPath/coder_eval) to verify that skills guide an AI agent to use the correct CLI commands and produce valid output. Tests run in CI via `.github/workflows/e2e-skills.yml`.

**When a PR adds a new skill folder under `skills/`:**

1. Check whether `tests/tasks/<skill-name>/` exists with at least one `.yaml` task file
2. If tests exist, verify:
   - At least one task tagged `smoke` and at least one tagged `e2e` (both required per CONTRIBUTING.md)
   - Each task's `tags` uses only valid test types: `smoke`, `integration`, or `e2e` — no other test-type tags (e.g., `activation` is not a valid tag)
   - Each task's `tags` includes the skill directory name (e.g., `uipath-maestro-flow`) as the first tag
   - `task_id` matches the pattern `skill-<domain>-<capability>`
   - The plugin loads in the sandbox — either via `agent.plugins` in the task YAML or inherited from the experiment config in `tests/experiments/default.yaml`
   - `initial_prompt` is minimal — describes the goal, not the steps (the skill should teach the agent)
   - `success_criteria` validates key CLI commands (`command_executed`), output files (`file_exists`, `file_contains`, `json_check`), or both
3. If tests are missing entirely, flag as **Medium** — most skills are not yet test-compliant
4. If tests exist but are missing a `smoke` or `e2e` task, flag as **Medium**

**When a PR substantially changes an existing skill** (new CLI workflows, changed commands):
- Check whether existing tasks in `tests/tasks/<skill-name>/` still cover the updated behavior
- Flag new capabilities that lack a test task as **Medium**

### Repository Hygiene

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
| **Critical** | Blocks skill discovery or leaks secrets — must fix | Broken frontmatter, name mismatch, committed credentials |
| **High** | Skill will work but poorly or breaks conventions — must fix | Missing Critical Rules, cross-skill dependencies, broken links, no CODEOWNERS entry |
| **Medium** | Quality gap — should fix | Missing e2e tests, no anti-patterns section, inconsistent placeholders, missing error handling |
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
