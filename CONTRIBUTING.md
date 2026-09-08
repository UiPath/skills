# Contributing to UiPath Agent Skills

Thank you for your interest in contributing! Whether you're adding a new skill, improving an existing one, fixing a bug, or enhancing documentation — we appreciate your help.

## Table of Contents

- [Repository Structure](#repository-structure)
- [Adding a New Skill](#adding-a-new-skill)
- [Modifying an Existing Skill](#modifying-an-existing-skill)
- [Hooks](#hooks)
- [Quality Checklist](#quality-checklist)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Repository Structure

```
.
├── .claude/                   # Claude Code project-level configuration
│   ├── commands/              # Project-only slash commands (e.g., /test-coverage)
│   └── skills/                # Contributor-only repository workflows
├── .claude-plugin/            # Plugin manifest and marketplace config
│   ├── plugin.json            # Plugin name, version, skills directory pointer
│   └── marketplace.json       # Claude Code marketplace registration
├── .gemini/                   # Google Gemini CLI project-level configuration
│   ├── settings.json          # context.fileName → [GEMINI.md, AGENTS.md, CLAUDE.md]
│   └── commands/              # Gemini custom slash commands (*.toml)
├── .cursor/                   # Cursor IDE project-level configuration
│   └── rules/                 # Cursor MDC rule files (one per concern, scoped by globs)
├── .agents/                   # Codex CLI skill-discovery root
│   └── skills -> ../skills    # Symlink (Codex scans .agents/skills for SKILL.md)
├── AGENTS.md -> CLAUDE.md     # Symlink; read by Codex, Copilot coding agent, others
├── commands/                  # Plugin-namespaced slash commands shipped to end users
│   └── *.md                   # Each file becomes /uipath:<filename>
├── hooks/                     # Session-initialization hooks
│   ├── hooks.json             # Hook definitions (SessionStart, etc.) — polyglot dispatch
│   ├── send-telemetry.sh      # Telemetry hook (bash twin)
│   └── send-telemetry.ps1     # Telemetry hook (PowerShell twin — keep in sync)
├── references/                # Shared documentation and activity references
│   └── activity-docs/         # Per-package, per-version activity API docs
├── skills/                    # Individual skill implementations
│   └── uipath-<name>/        # One folder per skill
│       ├── SKILL.md           # Skill definition (required)
│       ├── references/        # Supporting reference documents (optional)
│       └── assets/            # Templates, examples, static files (optional)
├── skill-flavors/             # Sparse build-time exceptions for custom hosts
│   └── <flavor>/
│       └── uipath-<name>/     # Sparse overrides mirroring skills/uipath-<name>/
├── tests/                     # Skill evaluation tests (coder_eval)
│   ├── experiments/           # Experiment configs (smoke, integration, e2e)
│   ├── tasks/                 # Test tasks organized by skill
│   │   └── <skill-name>/     # One folder per skill
│   └── reports/               # Generated coverage reports (/test-coverage)
├── CLAUDE.md                  # Root project rules (source of truth)
├── CODEOWNERS                 # GitHub ownership by skill/path
├── README.md                  # Project overview and quick start
├── CONTRIBUTING.md            # This file
└── LICENSE                    # MIT
```

### Key Principles

- **Skills are self-contained.** Each skill is an independent folder under `skills/`. Skills cannot reference or depend on other skills.
- **SKILL.md is the complete default entry point.** Standard integrations read it directly, and reviewers can understand the default/local behavior without a build manifest.
- **Custom flavors contain exceptions, not skill copies.** Mark only the canonical passages that actually differ, then provide sparse replacement blocks under `skill-flavors/<flavor>/`.
- **References are supplementary.** Large reference material goes in `references/` subdirectories, linked from SKILL.md.
- **Files are built before packages.** Build and validate complete default/custom skill trees first. Package staging consumes those finished trees; hosts do not resolve variants at runtime.

### Multi-Tool Compatibility

Skills work with **Claude Code**, **Google Gemini CLI**, **OpenAI Codex CLI**, **Cursor IDE**, and **GitHub Copilot coding agent**. Keep every `SKILL.md` file tool-agnostic markdown — no references to Claude-specific tool names, Anthropic-only plugin features, or vendor-specific slash commands inside skill bodies.

Tool wiring lives outside `skills/`:

| Tool | Integration file | Mechanism |
|------|------------------|-----------|
| Claude Code | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Plugin marketplace discovers `skills/` via plugin manifest |
| Google Gemini CLI | `.gemini/settings.json` (`context.fileName`), `.gemini/commands/*.toml` | Gemini loads `GEMINI.md` / `AGENTS.md` / `CLAUDE.md` as project context; discovers `SKILL.md` files on-demand via `.agents/skills/` |
| OpenAI Codex CLI | `AGENTS.md` (symlink → `CLAUDE.md`), `.agents/skills/` (symlink → `skills/`) | Codex scans `.agents/skills/` for `SKILL.md` files, reads `AGENTS.md` as project instructions |
| Cursor IDE | `.cursor/rules/*.mdc` | Scoped MDC rules: `token-optimization` (always-apply), `skill-structure` + `content-quality` (glob-scoped), `skill-review` + `pr-review` (agent-requested) |
| GitHub Copilot coding agent | `AGENTS.md` (symlink → `CLAUDE.md`) | Copilot reads `AGENTS.md` natively (since Aug 2025) |

When adding a skill, put its canonical files under `skills/uipath-<name>/`.
Every custom flavor includes that canonical skill automatically. Review the
complete skill for each flavor and add the smallest sparse override wherever
canonical guidance is not safe for that environment. No flavor manifest or
inclusion list is required.

## Adding a New Skill

### 1. Choose a Name

Skill folders follow the naming convention: `uipath-<domain>` or `uipath-<tool>`.

- Use **kebab-case** (lowercase, hyphens between words)
- Prefix with `uipath-` for UiPath-related skills
- Be descriptive but concise: `uipath-rpa`, `uipath-platform`, `uipath-maestro-flow`

### 2. Create the Folder Structure

At minimum, a skill needs:

```
skills/uipath-<your-skill>/
└── SKILL.md
```

For skills with substantial reference material:

```
skills/uipath-<your-skill>/
├── SKILL.md
├── references/
│   ├── commands-reference.md
│   ├── api-guide.md
│   └── <subdomain>/
│       └── detailed-topic.md
└── assets/
    └── templates/
        └── template-file.ext
```

### 3. Write SKILL.md

SKILL.md is the most important file. It uses YAML frontmatter followed by markdown content.

#### Frontmatter Format

```yaml
---
name: uipath-<your-skill>
description: "<identity> (<unique signal>). <core actions>. For <confusing-case>→<correct-skill>."
---
```

> **1024-character limit.** Claude Code truncates the combined `description` + `when_to_use` at 1,536 characters in the skill listing ([source](https://code.claude.com/docs/en/skills.md)). This repo caps `description` at 1024 chars to leave headroom and keep descriptions focused; the pre-commit hook enforces it. Front-load the skill identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`) within the first ~100 characters.

**Required frontmatter fields:**

| Field | Description |
|-------|-------------|
| `name` | Exact skill identifier, must match the folder name |
| `description` | Under 1024 chars. Front-load identity and unique signals, then core actions, then compact `→` redirects for commonly confused sibling skills. Do NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — they waste characters. |

**Optional frontmatter fields:**

| Field | Description |
|-------|-------------|
| `allowed-tools` | Restricts which tools the skill can use (e.g., `Bash, Read, Write, Glob, Grep`) |
| `user-invocable` | Defaults to `true`. Set to `false` if the skill should only be discoverable by the agent, not directly invocable by users |

#### Content Structure

Follow this structure in the markdown body:

```markdown
# Skill Title

Brief description of what the skill does.

## When to Use This Skill

- Bullet list of scenarios that should activate this skill

## Critical Rules

Numbered list of rules the AI agent MUST follow. These are the most important
part of your skill — they prevent the agent from making mistakes.

1. **Rule name** — Explanation and rationale
2. **Another rule** — ...

## Quick Start / Workflow

Step-by-step instructions for the most common use case.

## Reference Navigation

Links to reference documents in the `references/` folder for detailed topics.
```

**Tips for writing effective skills:**

- **Lead with rules.** The Critical Rules section prevents the agent from making expensive mistakes. Put the most important constraints first.
- **Be prescriptive, not descriptive.** Tell the agent exactly what to do, not just what's possible.
- **Include CLI commands verbatim.** Show the exact commands with flags. Agents work best with copy-paste-ready instructions.
- **Specify `--output json`** for any CLI commands whose output needs to be parsed programmatically.
- **Include anti-patterns.** A "What NOT to Do" section saves more time than a "What to Do" section.
- **Link to references for depth.** Keep SKILL.md focused on workflow and rules. Move detailed API docs, schemas, and examples into `references/`.

### 4. Register Lifecycle Status

Every skill must declare its maturity in [`assets/skill-status.json`](assets/skill-status.json) — the single source of truth (status is NOT stored in SKILL.md). Add an entry under `skills`:

```json
"uipath-<your-skill>": {
  "status": "preview",
  "confluence": { "page_id": null, "url": null },
  "last_synced": null
}
```

Use one of: `stable`, `preview`, `in-development`. Then regenerate the README status table and validate:

```bash
python3 scripts/check-skill-status.py --write-readme
python3 scripts/check-skill-status.py
```

CI (`validate-skill-status.yml`) fails if a skill is missing from the manifest, has an invalid status, leaves a stale `[PREVIEW]` / `> **Preview**` marker in SKILL.md, or if the README table is out of date.

### 5. Register the skills.sh Grouping

Add the skill to a section in [`skills.sh.json`](skills.sh.json). This controls how the skill is grouped on the repository's [skills.sh page](https://www.skills.sh/uipath/skills) — it does **not** affect what `uip skills install` or the `skills` CLI installs.

```json
{
  "title": "Authoring",
  "skills": ["uipath-<your-skill>"]
}
```

Pick the section that matches the skill's purpose — the same four the README catalog uses (Authoring, Solution & Planning, Platform & Operations, Diagnostics & Feedback). Then validate:

```bash
python3 scripts/check-skills-sh.py
```

CI (`validate-skills-sh.yml`) fails if a skill is in no grouping, is listed in two, or is grouped but no longer exists on disk. `--fix` removes entries for deleted skills but will not place new ones — that is an editorial call.

#### Renaming or removing a skill

`skills.sh.json` is not derived from disk, so a rename or a deletion leaves it stale with no other symptom. Update it in the **same PR** as the folder change:

| Change to `skills/` | Required edit |
|---|---|
| Add `skills/<new>/` | Add `<new>` to the matching grouping |
| Rename `skills/<old>/` → `skills/<new>/` | Replace `<old>` with `<new>` — both halves (old name gone, new name ungrouped) are reported |
| Delete `skills/<name>/` | Remove `<name>`, and drop the grouping if nothing survives in it |

```bash
python3 scripts/check-skills-sh.py --fix   # drops stale entries; will not place new ones
python3 scripts/check-skills-sh.py         # confirm: "OK — N skills grouped across M section(s)."
```

The check reads the whole tree, so it also reports drift that was already on `main`. Those findings are labelled **pre-existing** and do not fail your PR — `--baseline-ref` scopes the exit code to drift your change introduces. Fixing pre-existing drift is welcome; being blocked by it is not the intent.

### 6. Add Reference Documents (Optional)

Reference files go in `references/` and follow these conventions:

- **File naming:** `kebab-case.md` (e.g., `commands-reference.md`, `api-guide.md`)
- **Guide files:** Use the `-guide.md` suffix (e.g., `orchestrator-guide.md`)
- **Organize by subdomain** when a skill covers multiple areas (e.g., `references/integration-service/`, `references/lifecycle/`)
- **Link from SKILL.md** so the agent can discover them

### 6a. Add a Custom Flavor Exception (Only When Needed)

Before editing flavor sources or build/package logic, read
`.claude/skills/manage-skill-flavors/SKILL.md` completely. It is the
repository-local contributor workflow for this contract.

Use a flavor exception only when a host's capabilities materially change an
instruction. Keep the complete default behavior in the canonical file and
wrap the smallest differing passage with a named block:

```markdown
<!--skill-flavor:project-creation:start-->
Create the project with the default/local workflow.
<!--skill-flavor:project-creation:end-->
```

Create a file at the matching path under
`skill-flavors/<flavor>/<skill>/` and put only the replacement block in it:

```markdown
<!--skill-flavor:project-creation:start-->
Create the project with the host capability exposed in this environment.
<!--skill-flavor:project-creation:end-->
```

- Use lowercase kebab-case block names and keep each name unique within its file.
- Use compact `<!--skill-flavor:<name>:start|end-->` boundaries with no internal, leading, or trailing whitespace; keep Markdown indentation on the content inside the block.
- Keep shared content outside blocks; do not create a second full `SKILL.md`.
- For a host-only addition to a shared table, list, or navigation section, keep the shared content unmarked and add an empty canonical `<name>-extra` block for the flavor to fill. If one existing item differs, mark only that item.
- An override must contain complete marked blocks and no unmarked prose.
- Mirror the canonical relative path, including nested `references/` paths.
- Every flavor contains every canonical skill. If no override exists for a file, its canonical content is intentionally reused unchanged.
- A new flavor directory must contain at least one real sparse override. If a host needs no exceptions, consume the default package rather than creating an identical empty flavor.
- Do not check generated flavor trees into source control; build them into the ignored `build/` directory for validation and package staging.

Validate the source contract, then build the final Markdown trees:

```bash
npm run skills:validate
npm run skills:build
npm run skills:pack
```

The build writes complete, marker-free trees to `build/skills/default/` and
`build/skills/<flavor>/`. Packaging consumes those trees, stages
`build/packages/default/` plus `build/packages/<flavor>/`, and creates real
tarballs under `build/npm/`; it must not read sparse override sources directly.
The package convention is `default` → `@uipath/skills` and `<flavor>` →
`@uipath/skills-<flavor>`. Adding a valid flavor directory with sparse
overrides automatically adds its complete-catalog package—do not add an
allowlist, registry JSON, flavor-specific npm build script, or generic
validation-CI branch. Registry publication remains an explicit, isolated
decision per published flavor.

The existing root `npm pack` and `npm publish` commands remain default-only
entry points. Their npm lifecycle temporarily composes the marker-free default
tree and restores canonical `skills/` afterward. The default release jobs keep
using those root commands. `npm run skills:pack` is the separate all-flavor
build and verification command used by CI and isolated flavor publishers; a
publisher must select one exact package by manifest rather than publish a
tarball wildcard. Adding a flavor makes it buildable but does not publish it
automatically. For a flavor that intentionally uses GitHub Packages `dev` or
`preview`, add an explicit `publish.yml` caller of
`.github/workflows/publish-skill-flavor.yml` with that flavor and channel; do
not hardcode a flavor inside the reusable workflow or matrix-publish every
discovered flavor. Generated custom manifests pin both the default and
`@uipath` scoped registry to GitHub Packages and omit the
`package.json.repository` field, but package
visibility is an independent administrator setting. Complete the Internal
package bootstrap and publication-gate steps in `docs/RELEASE.md` before
enabling a new caller. If a root package operation fails or is interrupted and
`build/.root-pack-transaction` remains, confirm its npm process has ended and
run `npm run skills:recover`. Unexpected overlay edits are preserved under
`build/.root-pack-recovery-*` for review. Do not use `--ignore-scripts` for
source-repository packaging because that bypasses composition.

### 7. Add Templates/Assets (Optional)

Static files like code templates go in `assets/`:

- **Templates:** Use the `-template` suffix (e.g., `codedworkflow-template.md`)
- **Nested folders** are fine for organization (e.g., `assets/templates/`)

## Modifying an Existing Skill

1. **Read before editing.** Understand the existing SKILL.md and references before making changes.
2. **Preserve the Critical Rules section.** These exist for a reason. If you need to change a rule, explain why in your PR description.
3. **Don't break frontmatter.** The `name` and `description` fields are parsed by the plugin system. Validate your YAML.
4. **Test your changes.** After editing, verify the skill still activates correctly for its intended scenarios.
5. **Coordinate with CODEOWNERS.** Check who owns the skill and tag them in your PR.

## Hooks

Hooks are defined in `hooks/hooks.json` and run during plugin lifecycle events (e.g., `SessionStart`).

- **Every session hook ships as twin scripts**: `hooks/<name>.sh` (bash — macOS, Linux, Windows with Git Bash) and `hooks/<name>.ps1` (PowerShell — Windows without Git Bash, or pwsh where installed). No shell ships by default on both Windows and macOS, so both twins are required for zero-install coverage
- **The twins MUST stay behaviorally identical** — any change to one requires the equivalent change to the other in the same PR. The telemetry contract guards in `tests/scripts/` run both twins against the same assertions
- `hooks.json` registers one **bash/PowerShell polyglot command** per event: sh-family shells execute the `.sh` branch and see the PowerShell branch only as heredoc data; PowerShell block-comments the sh branch via `<# … #>` and executes the `.ps1` branch. Canonical shape (replace `<name>`):

  ```
  echo `# <#` >/dev/null
  bash "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"
  exit $?
  : <<'POLYEOF' #> > $null
  & "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.ps1"
  if ($null -eq $LASTEXITCODE) { exit 1 } else { exit $LASTEXITCODE }
  POLYEOF
  ```

  Constraints: do not add a `shell` field; never put the sequence `#>` in the sh branch; keep the PowerShell branch inside the `: <<'POLYEOF' … POLYEOF` heredoc — shells that parse the whole command up front (zsh, used by Codex on macOS via `$SHELL -lc`) otherwise fail on PowerShell syntax. Verified under bash, dash (`sh -c`), zsh, and Windows PowerShell 5.1
- `.ps1` scripts must stay compatible with **both** Windows PowerShell 5.1 and PowerShell 7+ — no `&&`/`||` pipeline chains, no ternary/null-conditional operators
- Keep hooks idempotent — safe to run multiple times
- Set appropriate timeouts (default: 180 seconds)

### Git Hooks

This repository uses pre-commit hooks to validate skill descriptions (1024-character limit). To enable them:

```bash
bash scripts/setup-hooks.sh
```

This configures git to use `.githooks/` and enables the skill description validator.

## Testing Skills

Skills are tested using [coder_eval](https://github.com/UiPath/coder_eval) — a framework that runs an AI agent against a task and scores the result. Tests live in `tests/tasks/<skill-name>/` and verify that the skill guides the agent to use the correct CLI commands, follow critical rules, and produce valid output.

There are three test types, distinguished by tags:

| Tag | Purpose | Cadence |
|-----|---------|---------|
| `smoke` | Skill triggers correctly, CLI produces valid output (1-5 simple scenarios) | Every PR |
| `integration` | Correct output across diverse scenarios, error paths, anti-patterns | Daily |
| `e2e` | Full lifecycle: Explore -> Plan -> Build -> Validate -> Deploy -> Run | Daily/weekly (check [Dashboard](https://dataexplorer.azure.com/dashboards/20cc55fe-33ae-4973-a951-855e76528219)) |

### Running Tests

```bash
cd tests
make install       # one-time: install coder-eval from GitHub
make all           # run all tests (smoke + integration + e2e)
make smoke         # run all smoke tests
make integration   # run all integration tests
make e2e           # run all end-to-end tests
make test-uipath-maestro-flow  # run all tests for a specific skill
```

### Adding Tests for a Skill

1. Create `tests/tasks/<skill-name>/` matching your skill folder name
2. Add at minimum **1 smoke test** and **1 e2e test** (required for every new skill PR)
3. Use minimal prompts — the goal is to test the skill's guidance quality, not hand-hold the agent
4. Tag every task appropriately: `smoke`, `integration`, or `e2e`
5. Follow the task ID pattern: `skill-<domain>-<capability>`
6. **Do not score self-reports.** Don't ask the agent to write a `report.json` / `recommendation.json` summary and then have `success_criteria` read that file back — the agent can write any value. Score real artifacts (`.flow` content, generated CSVs), real operations (`run_command` re-executes a validation), or behavior signals (`command_executed`, `command_not_executed`, `skill_triggered`).

See `tests/README.md` for the full task YAML template, success criteria reference, and examples from existing tests.

### Analyzing Test Coverage

Use the `/test-coverage` slash command to see what a skill's tests cover and where gaps exist:

```bash
/test-coverage uipath-maestro-flow   # single skill
/test-coverage all                    # all skills
```

This produces a markdown report in `tests/reports/` with component coverage, rule coverage, priority-ranked gaps, and concrete recommendations for new tests to write. Run this before and after adding tests to measure your progress.

### Scaffolding a Test with `/generate-task`

Use the `/generate-task` command to scaffold a single task YAML from a free-form description. The command always infers the target skill from the description — do not pass a skill name.

```bash
/generate-task smoke test for folder listing via uip orchestrator
/generate-task e2e flow that uses HITL with an approval gate and write-back
/generate-task cover the new uip flow registry get subcommand
```

Generated tasks are **unverified scaffolds**. Before merging, run the task end-to-end with `coder-eval` and add a passing-run claim to the PR description (the lint workflow flags missing claims as High severity). Verify that CLI commands, success criteria, and prompts match the skill's actual behavior, and adjust weights and thresholds based on what matters most for your skill.

## Quality Checklist

Before submitting your PR, verify:

### SKILL.md
- [ ] Frontmatter has `name` matching the folder name
- [ ] Frontmatter `description` is under 1024 characters (enforced by pre-commit hook)
- [ ] Frontmatter `description` front-loads identity and unique signals, uses `→` redirects (not verbose TRIGGER/DO NOT TRIGGER)
- [ ] Critical Rules section exists with numbered, actionable rules
- [ ] CLI commands include exact flags and `--output json` where appropriate
- [ ] Anti-patterns / "What NOT to Do" section is included for non-trivial skills
- [ ] No references to other skills (skills must be self-contained)
- [ ] All links to reference files use relative paths and point to existing files
- [ ] Lifecycle status registered in `assets/skill-status.json` and README table regenerated (run `python3 scripts/check-skill-status.py`)
- [ ] Grouped in `skills.sh.json` (run `python3 scripts/check-skills-sh.py`) — and on a rename or removal, the old name is gone from it too

### References
- [ ] File names use kebab-case
- [ ] Guide files use `-guide.md` suffix
- [ ] Templates use `-template` suffix
- [ ] No duplicate content already covered in another skill's references

### Skill flavors

- [ ] The canonical `SKILL.md` is still complete and useful as the default/local skill
- [ ] Only genuinely different passages are enclosed in flavor blocks
- [ ] Every marker boundary uses the compact whitespace-free form at column 1, with any required indentation kept on its enclosed Markdown
- [ ] Host-only additions use an additive empty canonical block instead of copying a shared table, list, or navigation section
- [ ] Custom override files contain matching complete blocks and no unmarked content
- [ ] Every canonical skill has been reviewed for every custom flavor; add sparse overrides wherever canonical guidance is unsafe
- [ ] Complete default and custom file trees build and validate before package staging
- [ ] `npm run skills:pack` creates one correctly named tarball per discovered flavor
- [ ] Root `npm pack` creates one marker-free `@uipath/skills` default tarball and leaves canonical sources unchanged
- [ ] Root `npm publish --dry-run` selects only the default package and leaves canonical sources unchanged
- [ ] Custom tarballs pin both default and scoped publication to GitHub Packages and omit `package.json.repository`
- [ ] Built trees, staged packages, and actual tarballs contain no flavor marker comments or sparse override sources

### Tests
- [ ] At least 1 smoke test in `tests/tasks/<skill-name>/`
- [ ] At least 1 e2e test in `tests/tasks/<skill-name>/`
- [ ] All tests tagged appropriately (`smoke`, `integration`, or `e2e`)

### General
- [ ] CODEOWNERS updated with your GitHub handle
- [ ] No secrets, tokens, or personal paths in any file
- [ ] No auto-generated or binary files committed (check `.gitignore`)
- [ ] Markdown is well-formed (no broken links, proper heading hierarchy)

## Pull Request Process

1. **Fork** this repository
2. **Create a feature branch** from `main` (e.g., `feat/add-my-skill`, `fix/uia-snapshot-docs`)
3. **Make your changes** following the guidelines above
4. **Run through the Quality Checklist**
5. **Submit a pull request** against `main`
   - Use a clear, descriptive title
   - Explain what your skill does and why it's needed
   - If modifying an existing skill, explain the motivation for the change
   - Tag relevant CODEOWNERS as reviewers

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| New skill | `feat/add-<skill-name>` | `feat/add-uipath-data-service` |
| Skill improvement | `feat/<skill-name>-<description>` | `feat/uia-add-drag-support` |
| Bug fix | `fix/<skill-name>-<description>` | `fix/flow-validate-edge-ports` |
| Documentation | `docs/<description>` | `docs/update-platform-cli-reference` |

### What to Expect

- A maintainer will review your PR, typically within a few business days
- CODEOWNERS for the affected paths will be automatically requested for review
- You may be asked to make changes — this is normal and collaborative
- Once approved, a maintainer will merge your PR

## Style Guide

### Markdown

- Use ATX-style headers (`#`, `##`, `###`)
- Use fenced code blocks with language identifiers (` ```bash `, ` ```yaml `, ` ```csharp `)
- Use tables for structured data (flags, options, mappings)
- Use `>` blockquotes for important notes and warnings
- Keep line lengths reasonable (no hard wrap requirement, but break long paragraphs)

### CLI Commands

- Always show the full command with all required flags
- Use `--output json` when the output needs to be parsed
- Use placeholders in angle brackets for user-provided values: `<PROJECT_DIR>`, `<FILE_PATH>`
- Show expected output format when it helps understanding

### Naming Conventions Summary

| Item | Convention | Example |
|------|-----------|---------|
| Skill folder | `uipath-<kebab-case>` | `uipath-rpa` |
| Default entrypoint | Exactly `SKILL.md` (uppercase) | `SKILL.md` |
| Reference files | `kebab-case.md` | `commands-reference.md` |
| Flavor override | `skill-flavors/<flavor>/<skill>/<canonical-path>` | `skill-flavors/studioweb/uipath-api-workflow/SKILL.md` |
| Flavor block | Lowercase kebab-case name | `skill-flavor:project-creation:start` |
| Guide files | `<topic>-guide.md` | `orchestrator-guide.md` |
| Template files | `<name>-template.md` | `codedworkflow-template.md` |
| Reference subdirs | `kebab-case/` | `integration-service/` |
| Asset subdirs | `kebab-case/` | `templates/` |

## Questions?

For questions, ideas, or feedback, please [open an issue](https://github.com/UiPath/uipath-claude-plugins/issues).
