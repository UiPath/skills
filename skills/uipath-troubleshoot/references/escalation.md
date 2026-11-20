# Escalation — Competitive Hypotheses

Load only when a SKILL.md escalation trigger fires. The fast path handles one dominant playbook match; escalation handles ambiguity: no match, co-equal matches, deep cross-domain chains, exhausted decision trees, or contradicted matches.

## 1. Enumerate candidates

Draft 2–4 candidates in `.local/investigations/notes.md`:

1. Draft one per candidate playbook using playbook grep matches, the no-signature routing table in `references/summary.md` (silent failures), and cross-domain signals. Do not draft candidates eliminated by contradicting evidence; record each elimination and disproving datum in `notes.md`.
2. Always add "originating fault is upstream/elsewhere": a match may be a consequence of an unfetched domain/entity. Probe it via the strongest cross-domain signal (wrapped inner exception, child job key, connection ID, parent instance).
3. Rank by fault signal. If an explicit fault signal exists (exception stack, error code, faulted state, incident), rank first the candidate explaining what CAUSED it; rank persistence, propagation, cleanup, and recovery-gap candidates afterward.
4. Record each candidate's description, source playbook path, supporting signals, `to_confirm`, and `to_eliminate`. Zero supporting signals is speculation and must not be drafted. One candidate equals one playbook at signature level; do not split a playbook's "What can cause it" list—the decision tree resolves those branches.

## 2. Probe in parallel

Spawn one read-only probe subagent per candidate (2–4, concurrently, in one message). Probes gather evidence; they never conclude, present, or ask the user.

Use this prompt, filling every `{slot}`:

```
Gather evidence for ONE troubleshooting hypothesis. Read-only: fetch and report data; do not conclude the investigation, modify files, or ask the user anything.

Hypothesis: {description}
Playbook: {absolute path} — read its ## Context and ## Investigation sections first.
Confirm items: {to_confirm list}
Eliminate items: {to_eliminate list — you MUST attempt every one; elimination evidence is first-class}

Rules:
1. Run ONLY uip commands documented in the playbook's ## Investigation section or the product overview's CLI section ({overview path}). No --help discovery, guessed flags, or REST/curl workarounds.
2. Redirect every CLI response: `uip ... --output json > .local/investigations/raw/h{n}-{command-name}.json`. Read only needed fields. Before fetching, check .local/investigations/raw/ and reuse existing fetches of the same entity. (Probes deliberately use `>` uniformly—narrower than Invariant 4's conditional `tee`—to keep probe context minimal.)
3. Every datum must match the reported entity, folder/tenant, and time window. Empty ≠ absent—verify the container exists. Live state ≠ historical state for incidents older than 24h.
4. Max 2 retries per command; after 3 distinct command failures, stop and report the failures.
5. Data unavailable → report the gap. Never invent or substitute.

Return (structured): per confirm/eliminate item — supported / contradicted / no data, with the raw file path and specific field values; open gaps; and any signal pointing at a DIFFERENT domain or entity (report it—do not chase more than one hop).
```

Probes may run concurrently because each writes to its own `raw/h{n}-*` namespace and nothing else.

### Serial fallback — no subagent tool

If the harness has no subagent-spawning tool, execute each probe sequentially here, preserving the prompt's protocol, budget, read-only behavior, documented-command restriction, retry caps, and `raw/h{n}-*` namespace:

1. Take candidates in §1 rank order and execute the probe-prompt rules.
2. **Close each probe before opening the next**: write its structured return (per confirm/eliminate item—supported / contradicted / no data, raw file plus field; open gaps; cross-domain signals) into `notes.md` under `## Probe h{n}`. Adjudication reads ONLY these blocks, not separately remembered fetches.
3. A different-domain signal stops at one hop; record it for adjudication and do not chase it mid-probe.
4. Do not adjudicate early. Complete every candidate; later elimination evidence separates siblings.
5. **Single-candidate collapse:** if only one viable candidate remains (the upstream/elsewhere candidate has no concrete signal to chase), collapse the round to targeted fetches for that candidate's confirm/eliminate items. Still record per-item verdicts in `notes.md`, then run the verifier.

Then adjudicate per §3 unchanged.

## 3. Adjudicate

You—not the probes—decide in `notes.md`:

1. **Eliminate first.** Any contradicted `to_eliminate` item eliminates the candidate; record the disproving datum.
2. **Upstream precedence.** A propagation/persistence/state-transition candidate cannot win while an upstream "why did the presupposed condition occur" candidate is untested or supported. If the upstream probe finds a new domain signal, re-grep the playbooks; when it matches a new playbook, run that playbook's decision tree (fast-path §5) before concluding.
3. **Runtime-evidence gate.** For runtime failures, the winner needs ≥1 correlated runtime datum (logs, job records, instance state, incidents). Design-time evidence proves only a defect exists, not that it caused this failure. If all runtime queries are empty while the user reports active failures, treat that as contradiction—wrong scope; re-verify scope or ask the user, do not conclude.
4. Apply the SKILL.md verification checklist to the winner.

If no candidate survives, present findings and ruled-out candidates per `presenting.md` ("no root cause found" terminal). Do not generate new candidates more than once; a second full round requires new evidence or new user input.

## 4. Fresh-eyes verifier (conditional)

Spawn ONE read-only verifier subagent before presenting when ANY applies:

- conclusion confidence is medium or low;
- the winning branch is the playbook's default/fallback branch (the tree's "none of the above");
- co-equal candidates were adjudicated (trigger 2 fired).

Use this prompt:

```
Verify a troubleshooting conclusion with fresh eyes. Read-only: no CLI or file edits. Read .local/investigations/notes.md, the raw files it references, and the playbook at {path}.

Conclusion under test: {cause statement + chosen resolution branch}

Check:
1. Specific cause named — the conclusion names ONE item from the playbook's "What can cause it" list (## Context), verbatim or tight paraphrase—not a category or vague generalization.
2. Evidence pinned — cited raw data contains a datum singling out THIS cause from its siblings in that list. Symptom-level data fitting multiple causes is insufficient.
3. Resolution alignment — the chosen fix is the ## Resolution branch keyed to that exact cause.
4. Causal precedence — list every event treated as given and ask "why did that occur?" A persistence/state-transition narrative presupposes an upstream condition ("state X didn't transition" presupposes "X was entered for a reason worth investigating"). Any unexplained upstream event not addressed in notes.md → fail this check.

Return: verdict `verified` or `shallow`; for each failed check, whether the gap is FACTUAL (missing datum—a targeted re-fetch could fix it; name the exact datum) or TEXTUAL (imprecise cause naming / wrong branch label—re-fetching cannot fix it); one line per gap.
```

Route the verdict:

- `verified` → present.
- `shallow` with factual gaps → perform ONE targeted re-fetch of the named datum (yourself or with a single probe), then re-check. If it still fails, treat it as textual.
- `shallow` with textual gaps → present at reduced confidence with the gap named. **Cause label and remediation path are separable**: an imprecise cause name does NOT invalidate the matched playbook's `## Resolution` procedure—an interactive resolution (e.g., apply recovered selector) still runs; never switch playbook resolutions merely because another names the cause better. Only a resolution-alignment gap (check 3) changes the fix branch.

If no subagent tool exists, run the verifier's four checks yourself: re-read `notes.md` and every cited raw file, answer each check in writing in `notes.md` under `## Self-verify`, then route as above. Independence is lost—present one confidence level lower than adjudication assigned unless every check passes with a cited datum.

## Boundaries

- Probes and verifier never talk to the user; ask every user question directly after they return.
- Total spawn budget per investigation: one probe round (2–4 probes) + optionally one verifier + at most one factual re-fetch round. Beyond that, present known facts with named gaps. The budget counts probes, not subagents; serial-fallback probes consume it identically.
