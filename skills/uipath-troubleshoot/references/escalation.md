# Escalation — Competitive Hypotheses

Load this file only when a SKILL.md escalation trigger fires. The fast path handles one dominant playbook match; escalation handles ambiguity: no match, co-equal matches, deep cross-domain chains, exhausted decision trees, or contradicted matches.

## 1. Enumerate candidates

Draft 2–4 candidate hypotheses in `.local/investigations/notes.md`:

1. **One candidate per candidate playbook.** Candidates come from playbook grep matches, the no-signature routing table in `references/summary.md` (for silent failures), and cross-domain signals. Never draft a candidate from a playbook already eliminated by contradicting evidence — record eliminations in notes.md with the disproving datum.
2. **Always add one "originating fault is upstream/elsewhere" candidate** — the possibility that every matched playbook describes a consequence and the true origin is a domain or entity not yet fetched. This candidate's probe follows the strongest cross-domain signal (wrapped inner exception, child job key, connection ID, parent instance).
3. **Fault-signal-first ordering.** If any explicit fault signal exists (exception stack, error code, faulted state, incident), the candidate explaining what CAUSED that fault ranks first. Persistence, propagation, cleanup, or recovery-gap candidates rank after it.
4. Each candidate records: description, source playbook path, supporting signals (a candidate with zero supporting signals is speculation — do not draft it), `to_confirm` evidence, and `to_eliminate` evidence. One candidate = one playbook at signature level; do NOT split a playbook's "What can cause it" list into separate candidates — those are branches its decision tree resolves.

## 2. Probe in parallel

Spawn one read-only probe subagent per candidate (2–4, concurrently, in one message). Probes gather evidence; they never conclude for you, never present, never ask the user.

Probe prompt template — fill every {slot}:

```
Gather evidence for ONE troubleshooting hypothesis. Read-only: you fetch data and report; you do not conclude the investigation, modify files, or ask the user anything.

Hypothesis: {description}
Playbook: {absolute path} — read its ## Context and ## Investigation sections first.
Confirm items: {to_confirm list}
Eliminate items: {to_eliminate list — you MUST attempt every one; elimination evidence is first-class}

Rules:
1. Run ONLY uip commands documented in the playbook's ## Investigation section or the product overview's CLI section ({overview path}). No --help discovery, no guessed flags, no REST/curl workarounds.
2. Redirect every CLI response: `uip ... --output json > .local/investigations/raw/h{n}-{command-name}.json`. Read back only needed fields. Before fetching, check .local/investigations/raw/ — reuse existing fetches of the same entity. (Probes deliberately use `>` uniformly — narrower than Invariant 4's conditional `tee` — to keep probe context minimal.)
3. Every datum must match the reported entity, folder/tenant, and time window. Empty ≠ absent — verify the container exists. Live state ≠ historical state for incidents older than 24h.
4. Max 2 retries per command; after 3 distinct command failures, stop and report the failures.
5. Data unavailable → report the gap. Never invent or substitute.

Return (structured): per confirm/eliminate item — supported / contradicted / no data, with the raw file path and the specific field values; open gaps; any signal pointing at a DIFFERENT domain or entity (report it — do not chase more than one hop).
```

Probes may run concurrently because each writes to its own `raw/h{n}-*` namespace and nothing else.

### Serial fallback — no subagent tool

Harness has no subagent-spawning tool → execute each probe yourself, sequentially, in this context. Same protocol, same budget; only the execution changes:

1. Take candidates in §1 rank order. Per candidate, execute the probe-prompt rules verbatim (read-only, documented commands only, `raw/h{n}-*` namespace, retry caps).
2. **Close each probe before opening the next**: write its structured return block (per confirm/eliminate item — supported / contradicted / no data, raw file + field; open gaps; cross-domain signals) into notes.md under `## Probe h{n}`. Adjudication reads ONLY these blocks — not your memory of the fetches.
3. A probe surfacing a different-domain signal still stops at one hop — record it for adjudication; do not chase it mid-probe.
4. Do not adjudicate early. A dominant-looking first probe does not skip the remaining candidates — elimination evidence from later probes is what separates siblings.
5. **Single-candidate collapse:** when only one viable candidate exists (the upstream/elsewhere candidate has no concrete signal to chase), the probe round collapses to targeted fetches for that candidate's confirm/eliminate items. The structure still applies: per-item verdicts in notes.md, then the verifier.

Then adjudicate per §3 unchanged.

## 3. Adjudicate

You (not the probes) decide, in notes.md:

1. **Eliminate first.** A candidate with any contradicted `to_eliminate` item is out — record the disproving datum.
2. **Upstream precedence.** A propagation/persistence/state-transition candidate cannot win while an upstream "why did the presupposed condition occur" candidate is untested or supported. If the upstream probe surfaced a new domain signal, follow it: re-grep the playbooks, and if it matches a new playbook, run that playbook's decision tree (fast-path §5) before concluding.
3. **Runtime-evidence gate.** For runtime failures, the winning candidate needs ≥1 runtime datum (logs, job records, instance state, incidents) that passes correlation. Design-time evidence alone proves a defect exists, not that it caused this failure. All runtime queries empty while the user reports active failures = contradiction — wrong scope; re-verify scope or ask the user, do not conclude.
4. Apply the SKILL.md verification checklist to the winner.

No candidate survives → present findings and ruled-out candidates per `presenting.md` ("no root cause found" terminal). Do not loop generating new candidates more than once — a second full round requires new evidence or new user input.

## 4. Fresh-eyes verifier (conditional)

Spawn ONE read-only verifier subagent before presenting when ANY of:

- The conclusion's confidence is medium or low
- The winning branch is the playbook's default/fallback branch (the tree's "none of the above")
- Co-equal candidates were adjudicated (trigger 2 fired)

Verifier prompt template:

```
Verify a troubleshooting conclusion with fresh eyes. Read-only: no CLI, no file edits. Read .local/investigations/notes.md, the raw files it references, and the playbook at {path}.

Conclusion under test: {cause statement + chosen resolution branch}

Check:
1. Specific cause named — the conclusion names ONE item from the playbook's "What can cause it" list (## Context), verbatim or tight paraphrase — not a category, not a vague generalization.
2. Evidence pinned — the cited raw data contains a datum that singles out THIS cause from its siblings in the same list. Symptom-level data that fits multiple causes is not enough.
3. Resolution alignment — the chosen fix is the ## Resolution branch keyed to that exact cause.
4. Causal precedence — list every event the conclusion treats as given and ask "why did that occur?". A persistence/state-transition narrative presupposes an upstream condition ("state X didn't transition" presupposes "X was entered for a reason worth investigating"). Any unexplained upstream event that notes.md does not address → fail this check.

Return: verdict `verified` or `shallow`; per failed check: whether the gap is FACTUAL (missing datum — a targeted re-fetch could fix it; name the exact datum) or TEXTUAL (imprecise cause naming / wrong branch label — re-fetching cannot fix it); one line per gap.
```

Route on the verdict:

- `verified` → present.
- `shallow` with factual gaps → ONE targeted re-fetch of the named datum (yourself or a single probe), then re-check. Still failing → treat as textual.
- `shallow` with textual gaps → present at reduced confidence with the gap named. **Cause label and remediation path are separable**: an imprecise cause name does NOT invalidate the matched playbook's `## Resolution` procedure — an interactive resolution (e.g., apply recovered selector) still runs; never switch to another playbook's resolution just because it names the cause better. Only a resolution-alignment gap (check 3) changes the fix branch.

No subagent tool → run the verifier's four checks yourself: re-read notes.md and every raw file the conclusion cites, answer each check in writing in notes.md under `## Self-verify`, then route on the verdict as above. Independence is lost — compensate by presenting at one confidence level lower than the adjudication assigned unless every check passes with a cited datum.

## Boundaries

- Probes and the verifier never talk to the user; every user question is asked by you, directly, after they return.
- Total spawn budget per investigation: one probe round (2–4 probes) + optionally one verifier + at most one factual re-fetch round. Beyond that, present what is known with gaps named. The budget counts probes, not subagents — serial-fallback probes consume it identically.
