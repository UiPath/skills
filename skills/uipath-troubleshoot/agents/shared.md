# Shared Agent Instructions

All troubleshooting sub-agents follow these rules.

## Invariants

ALL agents, ALL phases, ALL confidence levels. Never override.

1. **No fabrication.** Data unavailable → STOP and say so. Never invent data or substitute unrelated data.
2. **Evidence-to-problem correlation.** Every piece of evidence must match the reported process, entity, and time window. Filter before fetching. Discard unrelated data.
3. **Reference browsing.** Only triage, scope-checker, presenter, and depth-verifier browse `references/`. All others use paths from `state.json`.
4. **No inference from undocumented fields.** If a field's behavior isn't in a playbook or docsai result, don't guess. Flag it as unverified.
5. **No CLI discovery.** Before running ANY CLI command, verify the exact command exists in either: (a) the product overview CLI section, or (b) a matched playbook's `## Investigation` section. If the command is not documented in either source, do NOT run it. Do NOT guess command names, flags, or subcommands. Do NOT use `--help` to discover commands.
6. **Empty ≠ absent.** If a query returns empty or 404, verify the container still exists before concluding. Deleted/inaccessible container = data gap, not proof of absence.
7. **Live state ≠ historical state.** Current infrastructure snapshots (machine status, licenses, connections) cannot prove what happened during past incidents. Context only for incidents older than 24 hours.
8. **CLI retry cap.** Max 2 retries per unique command (3 attempts total). If the same command fails 3 times with the same error, stop trying it. After 3 distinct command failures in a single agent session, write `needs_input.json` and stop — something is fundamentally wrong (wrong folder, wrong entity, missing permissions).
9. **Symptom ≠ cause.** A hypothesis is "confirmed as root cause" only when the underlying cause from the matched playbook's cause list ("What can cause it", under `## Context`) is named with cause-specific evidence. Symptom matches alone (e.g., the right error string, an expected non-zero exit code) confirm the *playbook match*, not the *cause*. The depth-verifier sub-agent enforces this gate before resolution.

## Confidence-Level Behavior

Every agent must follow this table. Do not redefine confidence behavior locally.

| Confidence | Generator | Tester | Elimination | Exec-path required? |
|---|---|---|---|---|
| **High** | 1 hypothesis per matched playbook; skip docsai unless matched playbooks are empty | 1-2 verification steps only | Quick check only | No |
| **Medium** | 1-2 hypotheses per matched playbook; docsai for additional context | Follow all troubleshooting steps in playbook | All `to_eliminate` items | Yes |
| **Low** | 2-5 hypotheses per matched playbook + docsai | Free-form reasoning | All `to_eliminate` items | Yes |

**Single-round coverage rule.** Across all confidence levels, the generator drafts hypotheses for *every* matched playbook in one invocation. Deferring medium/low playbooks to a later round forces an orchestrator re-spawn cycle (~minutes of pure latency) when the first-tier hypothesis is inconclusive. The originating-fault hypothesis (per `hypothesis-generator.md` step 5) is still drafted *first* and ranked highest — the others sit beneath it in the same round.

**Playbook-signature granularity rule.** One hypothesis = one playbook match at its signature level. Do NOT enumerate the playbook's "What can cause it" list (under `## Context`) as separate hypotheses — those are sub-cause branches the playbook's `## Resolution` section narrows once the playbook-level signature is confirmed.

## Plan Loop

Triage and the hypothesis-tester operate from a single growing plan. Plan location is per-agent: triage → `state.json.plan`; tester → per-hypothesis `test_plan`.

The plan is an array of objects with the keys in `schemas/state.schema.md` § Plan: `{n, action, purpose, feeds, revise_if, status}`. An array of strings, a single string, or omitting the field are contract violations — downstream tooling parses by field name.

1. **Seed** the plan with the steps you can already foresee (see your agent's Required steps).
2. **Execute** the first pending step. Record the result. Mark `status: done`.
3. **Evaluate `revise_if`** against observed data; mutate the remaining plan (append/drop steps).
4. **Append discoveries.** If a completed step reveals a requirement `revise_if` didn't anticipate, append step(s) with a one-line `purpose`. Never run an unplanned command.
5. **Repeat** until all steps are `done`.
6. **Write outputs** (see your agent's Outputs) and return to the orchestrator.

## Startup

1. Create `.local/investigations/`, `.local/investigations/evidence/`, `.local/investigations/raw/` if they don't exist

## Available Tools

### uip CLI
The primary tool for interacting with the UiPath platform. Output defaults to json in non-interactive mode. Use `--output json` if you need to force json output explicitly.
- Commands are documented in each product's overview CLI section and in playbook `## Investigation` sections. See invariant #5.

### Documentation Search
`uip docsai ask "<question>" --source <source>`
- `--source docs` (default) — official product docs: feature behavior, configuration, API reference.
- `--source technical_solution_articles` — support KB: known bugs, workarounds, troubleshooting from support cases.

## Reading Playbooks and Guides

Read files from paths in `state.json`:
- `state.json.investigation_guides` — data correlation rules and testing prerequisites
- `state.json.matched_playbooks` — playbooks matched to the issue, with confidence level

**Confidence is a cap on root-cause certainty, not a ranking input** — rank by `signal_match_count` (see `state.schema.md` § Matched Playbooks). Do NOT modify a playbook's frontmatter confidence.

## Raw Data Rule

- **Redirect CLI output to file:** `uip ... --output json > .local/investigations/raw/{filename}.json` (or `-o .local/investigations/raw/`). Read back only the fields you need — never load full responses into context. The raw file is the record.
- Evidence files reference raw files via `raw_data_ref`.
- Before fetching, check `raw/` and `evidence/` — reuse if the entity was already queried.

## Requesting User Input

Write `.local/investigations/needs_input.json`, then STOP:

```json
{
  "agent": "triage | generator | tester",
  "needs_user_input": true,
  "user_question": "The specific question to ask the user",
  "context": "What you found so far that led to this question"
}
```

`needs_input.json` is the signaling mechanism — the orchestrator detects it, asks the user via `AskUserQuestion`, and re-spawns you with the answer. The `needs_user_input` fields in the evidence/hypotheses schemas are record-keeping only; always write `needs_input.json` to actually request input.

## Constraints

- Never generate or execute code (no Python, no inline code). Shell commands for file I/O and uip are fine.
- Stay within your role (see your agent file for boundaries).

## Output Schemas

See `schemas/` for the canonical JSON schemas: `state.schema.md`, `hypotheses.schema.md`, `evidence.schema.md`, `scope-check.schema.md`.
