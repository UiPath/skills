# Presenting the Resolution

Rules for the final user-facing resolution — formatting, entity naming, cross-domain fix completeness, evidence gating, and interactive fixes. Load this file when the verification checklist has passed (or a reduced-confidence / diagnostic-recommendation terminal applies) and you are ready to present.

## Inputs

- `.local/investigations/notes.md` — anchor, signals, matched playbook(s), branch decisions, checklist verdicts
- `.local/investigations/raw/` — authoritative field values; quote entity names and values from here
- Matched playbook(s) — `## Resolution` sections
- `uip docsai ask "<question>" --source docs|technical_solution_articles` — for domains missing a playbook resolution

## 1. Load presentation rules

For each domain in the causal chain, read `references/products/{domain}/presentation.md` or `references/activity-packages/{domain}/presentation.md` if it exists. These define entity naming and field labels.

## 2. Assemble fixes across all domains

Classify each domain in the causal chain: **root cause domain** (failure originated) or **propagation domain** (failure surfaced or was relayed).

### Root cause domain

1. Matched playbook's `## Resolution` — if present, use the branch keyed to the verified cause.
2. No `## Resolution` — run `uip docsai ask` targeted at the domain's fix. Use the result if concrete and actionable.
3. Docsai returns nothing useful — write: "No documented fix found for the {domain} layer — check UiPath documentation or consult UiPath support."

### Propagation domains

For each domain that relayed or surfaced the fault:

1. Matched playbook's `## Resolution` — if present, use it.
2. Otherwise run `uip docsai ask` for that domain's error-handling / resilience patterns. Frame the query around the domain's role, not the specific root cause (e.g., "error boundary events for service tasks in Maestro", "retry policies for faulted jobs in Orchestrator", "fallback configuration for Integration Service connectors").
3. Concrete pattern found → include as a preventive fix for that layer, citing the docsai result.
4. Nothing useful → write: "No documented error handling pattern found for the {domain} layer — check UiPath documentation for resilience options."

Do NOT write "No configuration change needed" for a propagation domain. Every domain in the causal chain gets either a fix or an explicit no-documented-pattern note.

### Source gating

Every fix step cites its source (playbook section, docsai result, or raw data file).

- Preserve docsai URLs — full URL, not just a title.
- Step with no documented source → drop it, or mark `[Unverified]` visibly.
- Undocumented field/setting behavior → do NOT include. Write: "Check UiPath documentation for [{field/setting}] behavior before proceeding."

### Discriminator carry

The final answer states the discriminating datum, not just the verdict:

- Name the datum that separates the confirmed cause from its sibling causes (the same evidence the verification checklist pinned) — "the recovered label matches the unchanged live button, so this is a mistyped selector, not a page change", not just "fix the selector".
- Upstream "why" unproven after the checklist AND after every reachable evidence source is exhausted — including workflow source present in the working directory (check its top level; if the project is there, read it, do not enumerate around it) → enumerate the candidate explanations ranked by evidence (most likely first, one line each, each tagged by what would confirm it) instead of only flagging the gap. Enumeration is never a substitute for reading available source.

## 3. Format

```
Root Cause: {description}

What went wrong: {one sentence}

Why: {root cause explanation — trace the full causal chain across all domains}

Evidence:

### {Domain} (Root Cause)
- {bullets — quote specific field values, error messages, IDs, timestamps, state, per this domain's presentation rules}

### {Domain} (Propagation)
- {bullets}

Immediate fix:

### {Domain} (Root Cause)
1. {What to do — concrete action with exact navigation path or command}
  - Why: {cite evidence that makes this step necessary}
  - Where: {exact file, UI path, setting, or command}
  - Who: {RPA developer | admin | platform team | process owner}
  - Source: {playbook path or docsai URL}

### {Domain} (Propagation)
1. {same structure}

Preventive fix:

1. {Domain} -- {What to change — concrete action}
  - Why: {cite specific evidence showing the gap this fix addresses}
  - Where: {exact file, UI path, setting}
  - Who: {RPA developer | admin | platform team}
  - Source: {playbook path or docsai URL}
2. {next domain, same structure}
```

**Reduced-confidence terminal** (checklist gap survived the re-fetch): present the same structure, name the gap explicitly next to the cause statement, and lead the Immediate fix with the playbook's diagnostic recommendation (e.g., a byte-compare snippet) instead of a guessed branch. Recommending the discriminating diagnostic IS the deliverable when evidence cannot separate sibling causes — never silently pick one.

**No root cause found**: present what was investigated and ruled out (from notes.md), and recommend providing more data or opening a UiPath support ticket.

## 4. Apply presentation rules

Check every entity name against the presentation guides and raw data:

- Display names from raw data, not API property names or paraphrases
- IDs only where needed for commands
- UI labels, not API field names

## 5. Investigation summary table

| # | What was checked | Verdict | Key Evidence | Resolution |
|---|------------------|---------|--------------|------------|

One row per playbook/branch/candidate checked (from notes.md), including eliminated ones.

## 6. Interactive resolutions — the approval gate

If a matched playbook's `## Resolution` is **interactive** — it prescribes printing concrete values and asking the user before applying a fix (the Healing Agent apply-fix flow via `activity-packages/ui-automation/interpretations/healing-agent-data.md` is the canonical example) — execute this protocol after presenting. This applies even when the cause label was refined or downgraded: cause label and remediation path are separable; the playbook's remediation procedure remains authoritative.

For each interactive action, in order:

1. **Print the user-facing data as plain text** — NOT inside AskUserQuestion options or previews. E.g. for a selector fix:

   ```
   Failed selector:
   {failed_selector_xml from raw data}

   Recovered Partial selector:
   {recovered_partial_selector_xml — or "(not available)"}

   Recovered Fuzzy selector:
   {recovered_fuzzy_partial_selector_xml — or "(not available)"}
   ```

2. **Print required warnings verbatim.** E.g. when `OrchestratorEnableHeal=false`: "Healing Agent was running in recommendation-only mode (OrchestratorEnableHeal=false) — the recovered selector was inferred from the UI tree after the failure but was not validated at runtime. There is no guarantee it will work." Analogous wording for `RecoverySuccessful=false`.

3. **Ask via AskUserQuestion** — the exact apply/dismiss question, plus a project-path follow-up if the path is not already known.

4. **On accept:** follow the playbook's linked procedure (e.g., `activity-packages/ui-automation/interpretations/healing-agent-data.md` § Applying `update-target` Fixes: prefer a package-provided skill like `uia-improve-selector` under `<PROJECT_DIR>/.local/docs/packages/`; otherwise edit the XAML activity matched by `ActivityRefId` with the playbook's XAML Selector Encoding rules; then validate with `uip rpa validate --file-path "<WORKFLOW_FILE>" --output json`). **After applying, the confirmation message must restate the confirmed root cause and the complete resolution** — it must stand alone as the investigation's summary for a user returning to only that message; never let it read as if the applied edit were the primary or only fix.

5. **On decline or non-answer: do not modify files.** If AskUserQuestion is unavailable, present the proposed edit as plain text and stop — never fall through to editing.

Pull every value from raw data. A required value missing (e.g., `recovered_partial_selector_xml`) → do NOT fabricate; surface the action as blocked, naming the missing evidence, and offer it as a follow-up.

## Boundaries

- Do NOT fabricate fix steps from undocumented field behavior — cite sources or flag `[Unverified]`.
- `uip docsai ask` is the only CLI command this phase may add beyond what the playbook documents.
- Diagnosis is autonomous; **mutation of user source files requires explicit in-channel approval** — no exceptions.
