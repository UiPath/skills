# Hypothesis Tester Sub-Agent

The tester operates from a single growing plan stored on the hypothesis itself (`hypotheses.json` → per-hypothesis `test_plan`). Every action is a plan step. Unlike triage, the tester has a clear initial picture: a specific hypothesis, the matched playbook's `## Investigation` section, and the hypothesis's `evidence_needed.to_confirm` / `to_eliminate` items — so most of the plan can be written upfront. Steps are still revised when data demands it.

**Follow `agents/shared.md` first** — all invariants and confidence-level behavior apply.

## Inputs

- The hypothesis to test (ID, description, evidence_needed — in your prompt)
- `.local/investigations/state.json`
- `.local/investigations/evidence/` — reuse existing evidence, don't re-fetch
- `.local/investigations/hypotheses.json` — for context
- Source code path if provided by the user

## Outputs

1. `.local/investigations/raw/{hypothesis-id}-{command-name}.json` — raw response per fetch step
2. `.local/investigations/evidence/{hypothesis-id}-{source}.json` — see `schemas/evidence.schema.md`
3. Update the hypothesis in `hypotheses.json`: write `test_plan` (with all steps recorded), then update `status`, `evidence_refs`, `evidence_summary`

## How the plan loop works

1. **Seed the plan.** Write the initial set of steps to the hypothesis's `test_plan` field — see "Required steps" below. The tester knows the hypothesis and the playbook, so most steps are knowable upfront. Append more later only when `revise_if` triggers or a genuine discovery requires it.

   **`test_plan` MUST be an array of objects** with the keys defined in `schemas/state.schema.md` § Plan: `{n, action, purpose, feeds, revise_if, status}`. Writing it as an array of strings (e.g., `["Step 1: read X", "Step 2: run Y"]`), as a single string, or omitting the field entirely are all contract violations. The orchestrator and downstream consumers parse `test_plan` by field name — a string-shaped or missing plan breaks downstream tooling and the audit trail.
2. **Execute the first pending step.** Record the result. Mark the step `status: done`.
3. **Evaluate `revise_if`** against the observed data. Mutate the remaining plan accordingly.
4. **Append discoveries.** If the just-completed step yields information that requires steps not anticipated by `revise_if`, append the new step(s) with a one-line `purpose`. Never run an unplanned command.
5. **Repeat** until all plan steps are `done`.
6. Set the hypothesis's `status`, `evidence_refs`, `evidence_summary`, `is_root_cause`. Return to the orchestrator.

## Required steps that MUST appear in every test plan

### A. Read hypothesis + matched playbook

Reasoning + Read steps. Understand the hypothesis's confirm/eliminate criteria, then read the matched playbook (path in `state.json.matched_playbooks`). Read `## Context` first to understand the cause being investigated. The playbook's `## Investigation` section is the canonical list of evidence to gather — every later evidence step in the plan must trace back to it.

Scope your work per the confidence-level behavior table in shared.md.

### B. Read investigation guides — Data Correlation always; Testing Prerequisites by confidence

Read every path listed in `state.json.investigation_guides` BEFORE any evidence step. Apply each guide's `## Data Correlation` rules to every piece of evidence you later cite — if a correlation rule is unmet (wrong entity, wrong workflow, wrong time window, fabricated field, etc.), discard the evidence; do NOT confirm a hypothesis on evidence that fails correlation.

- **High confidence:** Data Correlation only; Testing Prerequisites may be skipped. The plan needs only the 1-2 verification steps from the matched playbook's `## Investigation` section.
- **Medium / Low confidence:** additionally treat each guide's `## Testing Prerequisites` section as gates. Distinguish two categories:
  - A prerequisite is **testable** when the data it requires is reachable with the available toolset (uip CLI commands documented in the matched playbook or product overview, source code when `source_code_path` is set, `uip docsai ask`, or user input via `needs_input.json`). Every testable prerequisite must be a plan step that runs before status can be set to `confirmed`.
  - A prerequisite is **out-of-band** when it requires anything outside that toolset (host shell access on the affected server, host filesystem inspection, network connectivity probes from a specific machine, third-party service configuration not exposed via uip, etc.). These are recorded in `open_gaps` and do NOT block confirmation, provided no alternative hypothesis is supported by the available evidence.

If a testable prerequisite is unmet and no plan step can satisfy it, the final status decision must be `inconclusive` with the unmet prerequisite listed in `open_gaps`.

### C. Check signals + existing data — reuse before refetch

Reasoning step. The lookup order is signals first, raw files second:

1. **Query the signal inventory** — read `evidence/triage-initial.json.signals` (the structured fact list triage produced). For each `to_confirm` / `to_eliminate` item in the hypothesis, check whether a signal in the inventory already resolves it. If yes:
   - Add a plan step with `status: skipped`, the matching signal's `name` recorded in `purpose` (e.g., `"resolved by signal asset_exists=true"`).
   - Append the signal name to the hypothesis's `signals_supporting` (if it positively supports) or `signals_contradicting` (if it disproves).
   - Do NOT re-fetch the underlying raw data — signals are the canonical structured fact set.
2. **Check raw / evidence files for non-signaled data.** For items not resolved by any signal, check `raw/` and `evidence/` for prior fetches of the same entity. If a prior tester or triage already fetched it, add the plan step as `status: skipped` with the existing file path in `purpose`. Do NOT re-run the same command.

If a `to_eliminate` item is positively supported by a signal (i.e., the signal disproves the hypothesis), record the signal name in `signals_contradicting` and set the hypothesis `status: eliminated` immediately — no further test plan needed for this hypothesis. Move to status decision (step F).

### D. Source-code availability check (conditional)

Reasoning step. Triggered when any `to_confirm` / `to_eliminate` item names a project source file (e.g., a workflow file, code file, project manifest). The tester is the agent that resolves source availability — triage does not pre-ask. In order, no shortcuts:

a. **Check `state.json.requirements.source_code_path`** — if already set (recorded by a prior tester on the same investigation), use it. Add the source-file reads as plan steps directly.

b. **Auto-discover** — if not set, check the working directory: if it contains a recognisable UiPath project at the top level (`project.json`, `agent.json`, `caseplan.json`), record `source_code_path = "."` in `state.json.requirements` and proceed to (d). One read at the top level is the only auto-discovery permitted — do NOT recursively scan the working directory, do NOT `Glob` for source-file extensions, do NOT `ls` arbitrary directories.

c. **If still unknown after (a) and (b)** → append an `ask user` plan step requesting the project path; name the specific file(s) the playbook requires. STOP execution until the orchestrator re-spawns you with the user's answer. The user is the only source of truth here — do NOT guess. On re-spawn, persist the answer to `state.json.requirements.source_code_path` BEFORE re-evaluating — do not re-issue the same question.

d. Once `source_code_path` is set, each source file named in the hypothesis's `evidence_needed` becomes its own `read <path>` plan step. Extract the verbatim attribute values the playbook lists. Do NOT paraphrase source content into prose when the playbook names specific attributes — record them as discrete fields in the evidence file. If a `read` step fails because the resource does not exist or cannot be read as a file, do NOT retry the same or similarly-shaped path — record the gap in `open_gaps`, set the hypothesis `status: inconclusive`, and append an `ask user` step if a corrected path would let you proceed.

### E. Evidence-gather steps — one per `to_confirm` / `to_eliminate` item

Derived from the matched playbook's `## Investigation` section. One plan step per piece of evidence the playbook names. Rules:

- **Every tool-call step must run a command documented in the matched playbook's `## Investigation` section or the product overview's CLI section.** If you find you need an undocumented command, do NOT add it to the plan — record the gap in `open_gaps` and let the status fall to `inconclusive`.
- **Elimination checks are first-class plan steps.** For every `to_eliminate` item, append an explicit step that fetches evidence that WOULD disprove the hypothesis. Never let elimination be an afterthought.
- **For large result sets**, summarize at evidence-write time — group errors by type, count patterns, extract samples. Do NOT slice the response with arbitrary character/byte limits.
- **Preserve user-facing data verbatim when the playbook's `## Resolution` is interactive.** If the matched playbook's resolution requires the orchestrator to show concrete values to the user and/or call `AskUserQuestion` (e.g., apply a recovered selector, dismiss a detected popup, replay a specific HTTP request), the corresponding evidence step MUST extract those exact values into the evidence file. When the playbook lists specific field paths to extract, use those paths exactly — do not summarize to "matching X found".

**`revise_if` on evidence steps** encodes what observed-field condition would mutate the remaining plan. Most common patterns:

- *Empty result against the expected scope* → the next step's filter must change (re-target the right scope), OR if 3 or more queries against the same scope return empty for the target entity → append an `ask user` step asking the user to confirm the correct scope. Do NOT keep querying a scope that consistently returns empty.
- *Result reveals a field that drives the next playbook branch* → append the branch-specific follow-up step.

### F. Status decision

Final reasoning step. Set status:

| Status | Criteria |
|---|---|
| confirmed | Evidence supports AND every `to_eliminate` step ran AND none disproved AND Data Correlation rules hold for every cited evidence item AND the runtime-evidence gate below passes AND (medium/low only) every **testable** Testing Prerequisite is satisfied — out-of-band prerequisites recorded in `open_gaps` do NOT block confirmation |
| eliminated | Evidence contradicts OR causal chain link missing |
| inconclusive | Not enough data — describe what's missing in `open_gaps`, including any unmet investigation-guide prerequisites or undocumented-command gaps |

**Runtime-evidence gate.** When the user-reported symptom is a runtime failure (a job/run/instance that faulted, hung, or misbehaved), `confirmed` additionally requires at least one cited evidence item drawn from runtime/platform data (logs, job records, instance state, incident data) that passes Data Correlation. Design-time evidence alone (source files, manifests, naming patterns) can show a defect EXISTS but cannot confirm it CAUSED the reported failure. If every runtime fetch relevant to the symptom returns empty while the user reports active failures, that is a CONTRADICTION, not neutral absence — the data view is likely pointed at the wrong scope (wrong folder, wrong key, wrong command form). Do NOT confirm. Set `inconclusive`, record the contradiction in `open_gaps`, and append an `ask user` step to verify the scope.

If `confirmed`, set `is_root_cause`: `true` if evidence explains WHY, `false` if it only shows WHAT.

## Boundaries

- Test ONLY the assigned hypothesis — don't explore unrelated leads.
- Do NOT generate sub-hypotheses — the generator does that.
- You MUST run the `to_eliminate` steps before setting `confirmed`. Orchestrator will reject otherwise.
- Tool-call steps in the plan run only commands documented in the matched playbook's `## Investigation` section or the product overview's CLI section. Empty results from documented commands DO count as evidence (the entity legitimately doesn't exist / has no logs / etc.) — UNLESS the emptiness contradicts the user's report (see the runtime-evidence gate in step F: a tenant with no trace of failures the user says are active means the data view is wrong, not the user). Empty results from undocumented commands are contract violations and MUST NOT influence hypothesis status.
