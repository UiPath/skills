# Shared Agent Instructions

All diagnostic sub-agents follow these rules.

## Invariants

ALL agents, ALL phases, ALL confidence levels. Never override.

1. **No fabrication.** Data unavailable → STOP and say so. Never invent data or substitute unrelated data.
2. **Evidence-to-problem correlation.** Every piece of evidence must match the reported process, entity, and time window. Filter before fetching. Discard unrelated data.
3. **Reference browsing.** Only triage, scope-checker, and presenter browse `references/`. All others use paths from `state.json`.
4. **No inference from undocumented fields.** If a field's behavior isn't in a playbook or docsai result, don't guess. Flag it as unverified.
5. **No CLI discovery.** Read the product overview CLI section, not `--help`. High-confidence playbooks have exact commands — follow them.
6. **Empty ≠ absent.** If a query returns empty or 404, verify the container still exists before concluding. Deleted/inaccessible container = data gap, not proof of absence.
7. **Live state ≠ historical state.** Current infrastructure snapshots (machine status, licenses, connections) cannot prove what happened during past incidents. Context only for incidents older than 24 hours.

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
The primary tool for interacting with the UiPath platform. Output defaults to json in non-interactive mode. Use `--output json` if you need to force json output explicitly.
- Discover commands: `uip --help` or `uip <subcommand> --help`

### Documentation Search
Search UiPath documentation and knowledge base:
```
uip docsai ask "<question>" --source [docs, technical_solution_articles]
```
Use this to look up error messages, features, configuration, and troubleshooting guidance.

## Reading Playbooks and Guides

Read files from paths in `state.json`:
- `state.json.investigation_guides` — data correlation rules and testing prerequisites
- `state.json.matched_playbooks` — playbooks matched to the issue, with confidence level

**Confidence is authoritative.** Do NOT override a playbook's confidence level based on symptom match quality.

## Raw Data Rule

- **Redirect CLI output directly to file.** Use `uip ... --output json > .investigation/raw/{filename}.json` or `uip ... -o .investigation/raw/` so raw responses never enter agent context. Then read back only the specific fields you need.
- Do NOT capture full CLI responses in context. The raw file is the record — read from it selectively.
- Evidence files reference raw files via `raw_data_ref`
- Before fetching data, check `raw/` and `evidence/` for existing files — reuse if the same entity was already queried

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

**`needs_input.json` is the signaling mechanism** — this is how the orchestrator knows you need input. The `needs_user_input` fields in evidence and hypotheses schemas are for record-keeping only (documenting that a data gap existed). Always write `needs_input.json` to actually request user input.

## Constraints

- Do NOT generate or execute code (no Python scripts, no inline code). Shell commands for file I/O and uip are fine.
- Do NOT perform work outside your role (see your agent file for boundaries)

## Output Schemas

See `schemas/` for the canonical JSON schemas: `state.schema.md`, `hypotheses.schema.md`, `evidence.schema.md`, `scope-check.schema.md`.
