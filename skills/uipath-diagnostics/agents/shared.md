# Shared Agent Instructions

All diagnostic sub-agents follow these rules.

## Invariants

These rules apply to ALL agents, ALL phases, ALL confidence levels. Never override them.

1. **No fabrication.** If the data needed is unavailable, STOP and say so. Never invent log entries, timestamps, error codes, or correlations not present in raw data. Never substitute unrelated data as a proxy. Not finding a root cause is a valid outcome — report what was found, what was ruled out, and recommend the user open a support ticket.
2. **Evidence-to-problem correlation.** Every piece of evidence must tie directly to the user's reported symptom — the correct process, queue, entity, and time window. When a data source (folder, queue, tenant) contains items from multiple processes, filter to only the process under investigation before fetching details or drawing conclusions. Discard data from unrelated processes. Do not surface unrelated warnings or errors.
3. **Reference browsing.** Only triage and scope-checker may browse files under `references/`. All other agents use paths from `state.json` (investigation_guides, presentation_guides, matched_playbooks).
4. **Do not infer from unfamiliar fields.** If you encounter a field, setting, or property whose runtime behavior is not documented in a playbook, docsai result, or verified evidence, do not guess what it does. Do not use it in fix steps, explanations, or conclusions. If the field looks relevant, write: "The field `{name}` is present but its runtime behavior is not documented — check UiPath documentation before acting on it."

## Confidence-Level Behavior

Every agent must follow this table. Do not redefine confidence behavior locally.

| Confidence | Generator | Tester | Elimination | Exec-path required? |
|---|---|---|---|---|
| **High** | 1 hypothesis per matching playbook; skip others and docsai | 1-2 verification steps only | Quick check only | No |
| **Medium** | 2-5 hypotheses from all matching playbooks | Follow all diagnostic steps in playbook | All `to_eliminate` items | Yes |
| **Low** | 2-5 hypotheses from all playbooks + docsai | Free-form reasoning | All `to_eliminate` items | Yes |

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
- `state.json.presentation_guides` — product-specific display rules for entity names, IDs, labels
- `state.json.matched_playbooks` — playbooks matched to the issue, with confidence level

**Playbook structure** — all playbooks use `## Context`, `## Investigation` (optional), `## Resolution` (optional). Confidence determines how much structure a playbook provides, but does NOT change the invariants — those always apply.

All agents should follow the presentation guides from `state.json.presentation_guides` when writing evidence summaries and user-facing text.

**Confidence is authoritative.** A playbook's confidence level reflects how structured the playbook is. Do NOT override, upgrade, or downgrade it based on symptom match quality.

## Raw Data Rule

- Write full raw responses to `.investigation/raw/` **immediately**
- Do NOT keep raw data in context — write first, read back only specific fields if needed
- Evidence files reference raw files via `raw_data_ref`

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

## Output Schemas

See `schemas/` for the canonical JSON schemas: `state.schema.md`, `hypotheses.schema.md`, `evidence.schema.md`.
