# Shared Agent Instructions

All diagnostic sub-agents follow these rules.

## Startup

1. Create `.investigation/`, `.investigation/evidence/`, `.investigation/raw/` if they don't exist

## Available Tools

### uip CLI
The primary tool for interacting with the UiPath platform. Always use `--format json` for structured output.
- Discover commands: `uip --help` or `uip <subcommand> --help`
- Some commands support `-o, --output <path>` to save results directly to a directory.

### Documentation Search
Search UiPath documentation and knowledge base:
```
uip docsai ask "<question>" --source [docs, technical_solution_articles]
```
Use this to look up error messages, features, configuration, and troubleshooting guidance.

## Reading Playbooks and Guides

All file paths are resolved by triage and stored in `state.json`. Read files from:
- `state.json.investigation_guides` — data correlation rules and testing prerequisites
- `state.json.matched_playbooks` — playbooks matched to the issue, with confidence level

Do NOT browse `references/` yourself. Use the paths in `state.json`.

**Playbook structure** — all playbooks use `## Context`, `## Investigation` (optional), `## Resolution` (optional). Playbooks vary by confidence level:

| Confidence | `## Context` | `## Investigation` | `## Resolution` |
|---|---|---|---|
| **High** | Match pattern + root cause | Quick verification (1-2 steps) | Concrete fix |
| **Medium** | Causes, patterns | Concrete diagnostic steps | Fixes mapped to findings |
| **Low** | Causes, patterns | General guidance or absent | Optional |

Triage discovers matching playbooks but does not read their contents. Generator reads `## Context` to produce hypotheses — when high-confidence playbooks exist, it generates only from those (1 per playbook) and skips the rest. Tester follows `## Investigation` if present, scoping effort to the playbook's confidence level. Orchestrator reads `## Resolution` to present fixes.

**Confidence is authoritative.** A playbook's confidence level (from its frontmatter and the product summary) reflects how structured and specific the playbook is. Do NOT override, upgrade, or downgrade a playbook's confidence based on how well the symptoms match. A strong symptom match with a low-confidence playbook is still low-confidence — the playbook lacks structured investigation steps regardless of match quality.

## Raw Data Rule

- Write full raw responses to `.investigation/raw/` **immediately**
- Do NOT keep raw data in context — write first, read back only specific fields if needed
- Evidence files reference raw files via `raw_data_ref`

## Data Integrity

Read the investigation guides from `state.json.investigation_guides` and follow their data correlation rules. If data doesn't match the user's reported problem, discard it.

If you cannot retrieve the data you need: set `needs_user_input: true` and explain the gap. Do NOT substitute unrelated data or fabricate findings.

## It Is OK to Not Find a Root Cause

Not every investigation will identify a root cause. If you've exhausted available evidence and hypotheses without a clear answer, that is a valid outcome — not a failure. Report what you found, what was ruled out, and recommend the user open a UiPath support ticket with the evidence gathered.

## Requesting User Input

When you need user input, write a file `.investigation/needs_input.json` and then stop:

```json
{
  "agent": "triage | generator | tester",
  "needs_user_input": true,
  "user_question": "The specific question to ask the user",
  "context": "What you found so far that led to this question"
}
```

The orchestrator reads this file, presents the question via `AskUserQuestion`, and re-spawns you with the answer.

## Constraints

- Do NOT generate or execute code (no Python scripts, no inline code). Shell commands for file I/O and uip are fine.
- Do NOT perform work outside your role (see your agent file for boundaries)
- Do NOT browse `references/` — use paths from `state.json`

## Output Schemas

See `schemas/` for the canonical JSON schemas: `state.schema.md`, `hypotheses.schema.md`, `evidence.schema.md`.
