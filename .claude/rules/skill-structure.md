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

Every SKILL.md MUST begin with valid YAML frontmatter. All fields MUST be at the top level — NOT nested under a `metadata:` key (Claude Code only reads top-level keys).

This section is the **single source of truth** for the SKILL.md frontmatter contract. CLAUDE.md and CONTRIBUTING.md defer to this file.

### Required fields (enforced by `hooks/validate-skill-descriptions.sh`)

| Field | Rule |
|-------|------|
| `name` | MUST exactly match the parent folder name (kebab-case, `uipath-<domain>`). |
| `description` | ≤ 1024 characters. Front-load identity and unique file/domain signals (e.g., `.cs`, `.xaml`, `.flow`, `interact`, `BYO LLM`) within the first ~100 characters — that prefix carries the most matching signal. Use `→` redirects for sibling disambiguation (`For XAML→uipath-rpa`). MUST NOT use verbose `TRIGGER when:` / `DO NOT TRIGGER when:` clauses — replaced by `→` redirects. |

### Optional fields (recognized; used in real skills today)

| Field | Use |
|-------|-----|
| `when_to_use` | Standalone trigger sentence (e.g., "User says 'X', 'Y'…"). Useful when the `description` is identity/capability-focused and you want a separate, scannable trigger phrasing. Claude Code truncates the combined `description` + `when_to_use` at 1,536 characters in the skill listing ([source](https://code.claude.com/docs/en/skills.md)); 1024 chars on `description` leaves ~500 chars of headroom for `when_to_use`. |
| `allowed-tools` | Comma-separated tool list (e.g., `Bash, Read, Write, Glob, Grep, AskUserQuestion`). Restricts which tools the skill is allowed to call. Bash invocations may be scoped (e.g., `Bash(uip:*)`). |
| `user-invocable` | Defaults to `true`. Set `false` to make the skill agent-only (not directly invocable as `/uipath:<name>` by users). |

### Style guidance (SHOULD, not enforced)

- **Front-load the brand/domain identity** ("UiPath …") when natural. Most skills do, and it places the strongest matching signal first. Action verbs ("Manage", "Send", "Always invoke") are acceptable when they make the skill's purpose clearer in the first ~100 chars.
- **Avoid metadata prefixes** like `[PREVIEW]` / `[BETA]` at the start of `description` — they displace high-value matching tokens. Indicate preview status in the SKILL.md body instead, with a `> **Preview**` or `> **Experimental**` callout under the H1.
- **Frontmatter MUST be valid YAML** — no tabs, proper quoting of strings containing colons.

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

## Cross-Skill Boundaries

Skills are **runtime-independent**: a skill MUST NOT import, link to, or rely on content from another skill's `references/` or `assets/`. Each `skills/uipath-*/` folder is fully self-contained at runtime.

However, **disambiguation pointers in the `description` are required, not violations.** Every skill SHOULD include `→` redirects for sibling skills it commonly gets confused with. These tell the matcher which skill is correct:

- `For Python agents→uipath-agents`
- `For .flow files→uipath-maestro-flow`
- `For Test Manager→uipath-test`

Routing skills (e.g., `uipath-planner`) explicitly delegate to specialist skills by name — that is the routing skill's purpose, not a cross-dependency.

## Content Rules

- CLI commands MUST include `--output json` when output is parsed programmatically
- All file links MUST use relative paths from the SKILL.md location
- All file links MUST point to files that actually exist in the repo
- No secrets, tokens, credentials, or personal filesystem paths
