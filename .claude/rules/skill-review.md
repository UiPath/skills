# Skill Review & Audit Rules

When asked to review, audit, or grade a skill (or when reviewing a PR that adds/modifies a skill), apply this strict evaluation framework. Analyze the **entire skill** — SKILL.md, all references, all assets — and produce actionable findings.

## How to Conduct a Review

1. **Read everything.** Read the full SKILL.md, every file in `references/`, every file in `assets/`. Do not skim.
2. **Score each dimension** on a 1-5 scale (1 = failing, 3 = acceptable, 5 = excellent).
3. **List specific findings** per dimension — cite file paths and line numbers.
4. **Provide actionable fixes** — not vague suggestions. Say exactly what to change and where.

## Scoring Dimensions

### 1. Structure (1-5)

Does the skill follow the canonical layout and conventions?

- SKILL.md has valid YAML frontmatter with `name` and `description`
- `name` matches the folder name exactly
- `description` includes TRIGGER and DO NOT TRIGGER conditions
- SKILL.md body follows the expected section order: Title, When to Use, Critical Rules, Workflow/Quick Start, Reference Navigation, Anti-patterns
- Reference files use kebab-case naming with `-guide.md` / `-template.md` suffixes
- Folder organization is logical (references/, assets/, scripts/)
- No orphaned files (every file is reachable from SKILL.md)

**Red flags:** missing frontmatter fields, name mismatch, no Critical Rules section, unreachable files.

### 2. Consistency (1-5)

Is the skill internally consistent and consistent with other skills in this repo?

- CLI commands use `--format json` uniformly when output is parsed
- Placeholder style is consistent (`<UPPER_SNAKE_CASE>` in angle brackets)
- Heading hierarchy does not skip levels
- Code blocks have language identifiers
- Terminology matches other skills (e.g., "validate" not "check", "project directory" not "project folder")
- Frontmatter format matches the convention used across the repo

**Red flags:** mixed placeholder styles, inconsistent flag naming, terminology drift from other skills.

### 3. Logic & Completeness (1-5)

Does the skill actually work end-to-end? Are the instructions correct and complete?

- Workflows cover the full lifecycle (setup through completion)
- Error handling is specified (what to do when commands fail)
- Edge cases are addressed (missing dependencies, auth failures, empty results)
- CLI commands are correct (flags exist, syntax is valid)
- Steps are in the right order (no forward references to undefined concepts)
- Validation loops are present where needed (max retry count specified)
- Anti-patterns section exists and covers real mistakes an agent would make

**Red flags:** steps that assume prior state without checking, missing error paths, commands with wrong flags, no validation after mutations.

### 4. Duplication (1-5)

Is content DRY? No unnecessary repetition within or across files?

- No copy-pasted blocks between SKILL.md and reference files
- No redundant explanations of the same concept in multiple reference files
- SKILL.md links to references for detail instead of inlining everything
- No reference files that overlap significantly in scope
- No instructions repeated verbatim in Critical Rules and in the workflow sections
- Cross-reference where appropriate rather than duplicating

**Red flags:** same CLI command documented with full explanation in 3+ places, reference files with >50% overlapping content, SKILL.md that duplicates its own reference files.

### 5. LLM Usability (1-5)

How effectively can an AI agent follow these instructions?

- Instructions are prescriptive ("Run X") not descriptive ("You could run X")
- Critical Rules are numbered and unambiguous
- Decision trees / branching logic is explicit (if X then Y, else Z)
- CLI commands are copy-paste ready with all required flags
- The agent knows when to stop (max retries, exit conditions, when to ask the user)
- Information is front-loaded (most important rules first, details later)
- SKILL.md is not excessively long — large reference material is extracted to `references/` so the agent loads it on demand
- No ambiguous phrases ("as needed", "if appropriate", "consider") without criteria for when they apply

**Red flags:** vague instructions, prose where a numbered list would work, 3000+ line SKILL.md with no reference extraction, missing stop conditions, decision points without clear criteria.

### 6. Marketplace & Integration (1-5)

Is the skill ready for public use as a plugin?

- `description` in frontmatter is detailed enough for the plugin system to match it correctly — not too broad (false triggers on unrelated requests), not too narrow (misses valid use cases)
- DO NOT TRIGGER conditions prevent conflicts with other skills in the marketplace
- The skill does not assume any state that the plugin's SessionStart hook doesn't guarantee
- No hardcoded paths, tokens, or environment-specific assumptions
- Works on all platforms the skill claims to support
- CODEOWNERS entry exists

**Red flags:** description that triggers on generic terms, missing DO NOT TRIGGER for sibling skills, hardcoded localhost URLs or personal paths, no CODEOWNERS entry.

## Output Format

When reporting a review, use this format:

```
## Skill Review: <skill-name>

| Dimension              | Score | Summary |
|------------------------|-------|---------|
| Structure              | X/5   | ... |
| Consistency            | X/5   | ... |
| Logic & Completeness   | X/5   | ... |
| Duplication            | X/5   | ... |
| LLM Usability          | X/5   | ... |
| Marketplace & Integration | X/5 | ... |
| **Overall**            | **X/5** | **weighted average** |

### Findings

#### [Dimension Name] — X/5
- **[Finding title]** (file:line) — Description of issue. **Fix:** Exact change to make.
- ...

### Top 3 Priority Fixes
1. ...
2. ...
3. ...
```

## When to Apply This Framework

- When explicitly asked to review, audit, or grade a skill
- When reviewing a PR that adds a new skill or substantially modifies an existing one
- When asked to evaluate skill quality, readiness, or marketplace fitness
- When asked to compare skills or identify the weakest skill in the repo
