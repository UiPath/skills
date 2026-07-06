# Investigation State Schema

File: `.local/investigations/state.json`

Written during: TRIAGE
Read during: all phases
Updated: at phase transitions (`phase` field) and on scope adjustment

## Structure

```json
{
  "id": "inv-YYYY-MM-DD-NNN",
  "created_at": "ISO8601 timestamp",
  "phase": "triage | hypotheses | test | evaluate | deepen | depth_check | resolution | complete",
  "scope": {
    "level": "platform | product | feature | process | activity",
    "domain": ["orchestrator", "maestro", "integration-service", "ui-automation"],
    "confidence": "high | medium | low"
  },
  "entry_point": {
    "type": "job_id | error_message | queue_name | natural_language",
    "value": "the raw identifier or description the user provided"
  },
  "triage_summary": "One-paragraph classification of the problem",
  "user_context": "Original problem description from the user",
  "investigation_guides": [
    "references/investigation_guide.md",
    "references/products/orchestrator/investigation_guide.md",
    "references/products/maestro/investigation_guide.md"
  ],
  "matched_playbooks": [
    {
      "confidence": "low",
      "path": "references/products/maestro/playbooks/bpmn-job-stuck.md",
      "signal_match_count": 3,
      "signals_matched": ["job state is Running", "runtime type is ProcessOrchestration", "no incident error code"]
    },
    {
      "confidence": "low",
      "path": "references/products/orchestrator/playbooks/job-stuck.md",
      "signal_match_count": 2,
      "signals_matched": ["job state is Running", "no error logs present"]
    }
  ],
  "eliminated_playbooks": [
    {
      "path": "references/activity-packages/system-activities/playbooks/get-asset-not-found.md",
      "contradicting_signal": "playbook signature requires asset absent / HTTP 404 / error code 1002; evidence shows asset exists in the resolved folder"
    }
  ],
  "requirements": {
    "folder_id": 2157426,
    "source_code_path": "/path/to/project"
  },
  "plan": [
    {
      "n": 1,
      "action": "uip <subcommand> --output json | tee raw/<file>.json",
      "purpose": "what signal the step yields",
      "feeds": "which downstream step / playbook / decision the result routes to",
      "revise_if": "observed-field condition that mutates the remaining plan (empty if unconditional)",
      "status": "pending"
    }
  ]
}
```

## Investigation Guides

Resolved during TRIAGE. Always includes the generic guide (`references/investigation_guide.md`). Includes the product-specific guide if one exists. Later phases use these resolved paths — they do NOT scan the references folder themselves.

## Matched Playbooks

Resolved during TRIAGE. Full paths to every playbook that matches the symptoms, with per-playbook signal-match data.

Fields per entry:

- `path` — relative path to the playbook from the skill root.
- `confidence` — the playbook's frontmatter confidence (`high | medium | low`). **This is a cap on how decisively the playbook can pin a root cause when matched** — `high` means the playbook describes a specific error with a known cause; `medium` means concrete troubleshooting steps but the conclusion depends on inspection of uncertain fields; `low` provides general context. **Confidence is not a ranking input — see signal_match_count.** Do NOT modify the frontmatter confidence.
- `signal_match_count` — integer count of how many distinct signature signals from the playbook's `## Context` and `## Investigation` sections the gathered evidence actually satisfies. A signal is a discrete fact: an exception class, a specific error code, a verbatim error fragment, an entity-state assertion, a package version, an activity-instance label, etc.
- `signals_matched` — array of short labels naming each signal that was satisfied (audit trail for `signal_match_count`).

**Ranking.** Matched playbooks are ordered by `signal_match_count` DESCENDING — highest specificity first, regardless of frontmatter confidence. A `medium`-confidence playbook with 3 matched signals ranks above a `high`-confidence playbook with 1 matched signal. GENERATE drafts H1 from the top-ranked playbook, H2 from the second-ranked, etc. Ties on signal count are broken by frontmatter confidence (`high > medium > low`).

**Three categories of evidence-vs-playbook relationship:**

- **Positively supported** (`signal_match_count >= 1`) → list in `matched_playbooks`.
- **Silent** (evidence neither supports nor contradicts any of the playbook's signals) → do NOT list. The playbook is uninformed by the available evidence; it cannot be tested productively until more data exists.
- **Contradicted** (evidence directly disproves at least one CORE signal of the playbook signature) → do NOT list in `matched_playbooks`; instead record in `eliminated_playbooks` with the contradicting evidence. GENERATE will not draft hypotheses from these.

A "core signal" is one named in the playbook's `## Context` or `## Investigation` as a required precondition for the cause to apply (e.g., "asset is absent / HTTP 404", "robot has no matching credentials", "connection ID returns 'invalid'"). Surface-level signals shared across siblings (e.g., "Get Asset activity") are NOT core signals — they're descriptors, not preconditions.

## Eliminated Playbooks

Playbooks whose signature was contradicted by triage evidence. Each entry records:

- `path` — playbook path.
- `contradicting_signal` — short sentence naming the playbook's required signal AND the contradicting evidence (e.g., "playbook requires asset absent; evidence shows asset exists in folder").

GENERATE MUST exclude these from consideration. DEPTH CHECK MUST NOT verify a hypothesis that maps to an eliminated playbook.

**Why count over confidence.** Multiple playbooks can match the same surface signal (e.g., "Get Asset activity failed" appears in five distinct get-asset playbooks at frontmatter `high`). Ranking purely on frontmatter confidence then surfaces 5-way false positives at HIGH. Counting actual signal hits per playbook discriminates between them: the one whose specific signature is most fully satisfied by the evidence wins. Frontmatter confidence still caps the root-cause certainty downstream (`high` matches can fast-path; `medium`/`low` require deeper testing) — but it does not decide ordering.

## Plan

The investigation plan is the single, growing record of everything the investigation intends to do. TRIAGE starts with a one-step plan (classify the user's message) and appends steps as data arrives. **The plan IS the procedure** — there is no pre-plan or post-plan phase; every action taken is a plan step that is recorded, executed, and audited.

Field semantics:

- `n` — step order (1-indexed; numbering grows as steps are appended).
- `action` — what the agent will do at this step. Action shapes:
  - **Tool call** — an exact CLI command (with output capture), or `read <path>` for a file read.
  - **User interaction** — `ask user: <question>` (free-text) or `ask user (select): <opt> | <opt> | …` (multi-choice surfaced via `AskUserQuestion`).
  - **Reasoning** — a named decision the agent records without calling a tool: `classify (system, entity) from user message`, `re-evaluate scope against gathered evidence`, `match playbooks against in-scope summaries`, etc. The agent's reasoning + result is captured in `purpose` / step output.
- `purpose` — the specific signal or decision the step yields (one short phrase).
- `feeds` — which downstream step or decision consumes the result.
- `revise_if` — observed-field condition that mutates the remaining plan (add/drop steps). Empty if the step is unconditional.
- `status` — `pending | done | skipped`.

**The plan is revisable.** After each step the agent evaluates `revise_if` against the observed data, then appends/modifies remaining steps. If the just-completed step yields information that requires new steps not anticipated by any `revise_if` (a genuine discovery), the agent appends them with a one-line `purpose` before executing. The agent runs ONLY plan steps — never a freestyle command.

**Boundaries on what can appear in a plan:**

- No open-ended enumeration steps (no "search every folder", no tenant-wide sweep). Locate passes are single bounded calls with at least one filter (state, time window, or named anchor).
- No `get <unknown-id>` actions for entities that have not been located. A `get` step requires the id to be resolved by an earlier step.
- No undocumented commands. Every tool-call step must run a command documented in the matched investigation guide or the matched playbook's `## Investigation` section.
- A single Pass 2 extension is permitted when the initial pass yields weak matches; a Pass 3 is not.

The plan structure is reusable: any data-gathering phase (TRIAGE, TEST) writes a plan of its own. For TEST, the plan is stored on the hypothesis itself (`hypotheses.json` → per-hypothesis `test_plan`), not on `state.json`.

## Requirements

Generic key-value store for data gathered during the investigation. Readable in all phases; written during TRIAGE, TEST (e.g., `source_code_path`), and EVALUATE.

- Keys are freeform — use descriptive names (e.g., `folder_id`, `source_code_path`, `queue_name`)
- Values are whatever was collected (string, number, etc.)

## Rules

- TRIAGE creates this file and resolves investigation guides, matched playbooks, and requirements
- Later phases use playbook/guide paths from `state.json` — reference browsing happens in TRIAGE, SCOPE CHECK, DEPTH CHECK, and RESOLUTION
- `phase` is updated as the investigation progresses
- `requirements` is readable in all phases; written during TRIAGE, TEST, and EVALUATE
- `scope` may be updated when scope adjustment occurs
