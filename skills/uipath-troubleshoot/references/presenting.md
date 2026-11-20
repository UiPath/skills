# Presenting the Resolution

Final user-facing resolution rules for formatting, entity naming, cross-domain fix completeness, evidence gating, and interactive fixes. Load after verification passes or when a reduced-confidence/diagnostic-recommendation terminal applies.

## Inputs

- `.local/investigations/notes.md` — anchor, signals, matched playbook(s), branch decisions, checklist verdicts
- `.local/investigations/raw/` — authoritative values; quote entity names and values from here
- Matched playbook(s) — `## Resolution` sections
- `uip docsai ask "<question>" --source docs|technical_solution_articles` — for domains without a playbook resolution

## 1. Load presentation rules

For every causal-chain domain, read `references/products/{domain}/presentation.md` or `references/activity-packages/{domain}/presentation.md` if it exists; use it for entity names and field labels.

## 2. Assemble fixes across all domains

Classify each causal-chain domain as **root cause domain** (failure originated) or **propagation domain** (failure surfaced or was relayed).

### Root cause domain

1. Use the matched playbook's `## Resolution` branch keyed to the verified cause.
2. If absent, run `uip docsai ask` targeted at the domain's fix and use a concrete, actionable result.
3. If no useful result, write: "No documented fix found for the {domain} layer — check UiPath documentation or consult UiPath support."

### Propagation domains

For each relaying or surfacing domain:

1. Use the matched playbook's `## Resolution` if present.
2. Otherwise run `uip docsai ask` for that domain's error-handling/resilience patterns, framing the query around its role rather than the root cause (e.g., "error boundary events for service tasks in Maestro", "retry policies for faulted jobs in Orchestrator", "fallback configuration for Integration Service connectors").
3. Concrete pattern found → include as a preventive fix for that layer, citing the docsai result.
4. If none is useful, write: "No documented error handling pattern found for the {domain} layer — check UiPath documentation for resilience options."

Never write "No configuration change needed" for a propagation domain: every causal-chain domain gets a fix or an explicit no-documented-pattern note.

### Source gating

Every fix step cites a playbook section, docsai result, or raw data file. Preserve docsai URLs as full URLs, not titles. Drop a step lacking a documented source or mark it visibly `[Unverified]`. Do not include undocumented field/setting behavior; write: "Check UiPath documentation for [{field/setting}] behavior before proceeding."

### Discriminator carry

State the datum distinguishing the confirmed cause from sibling causes—the evidence pinned by the verification checklist—not merely the verdict: "the recovered label matches the unchanged live button, so this is a mistyped selector, not a page change", not just "fix the selector". Upstream "why" unproven after the checklist AND after every reachable evidence source is exhausted — including workflow source present in the working directory (check its top level; if the project is there, read it, do not enumerate around it) → list candidate explanations ranked by evidence, most likely first, one line each, tagged with what would confirm it. Enumeration never substitutes for reading available source.

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

**Reduced-confidence terminal** (checklist gap survived the re-fetch): use the same structure, name the gap beside the cause statement, and lead Immediate fix with the playbook's diagnostic recommendation (e.g., a byte-compare snippet), not a guessed branch. Recommending the discriminating diagnostic is the deliverable when evidence cannot separate sibling causes; never silently choose one.

**No root cause found**: present what notes.md says was investigated and ruled out, and recommend providing more data or opening a UiPath support ticket.

## 4. Apply presentation rules

Check every entity name against presentation guides and raw data:

- Use display names from raw data, not API property names or paraphrases.
- Use IDs only where needed for commands.
- Use UI labels, not API field names.

## 5. Investigation summary table

| # | What was checked | Verdict | Key Evidence | Resolution |
|---|------------------|---------|--------------|------------|

Include one row per playbook/branch/candidate checked from notes.md, including eliminated ones.

## 6. Interactive resolutions — the approval gate

If a matched playbook's `## Resolution` is **interactive**—it prescribes printing concrete values and asking before applying a fix, with the Healing Agent apply-fix flow via `activity-packages/ui-automation/interpretations/healing-agent-data.md` as the canonical example—execute this protocol after presenting. It also applies when the cause label was refined or downgraded: the playbook's remediation procedure remains authoritative and cause label/remediation path are separable.

For each interactive action, in order:

1. **Print user-facing data as plain text**, never in AskUserQuestion options or previews. For a selector fix:

   ```
   Failed selector:
   {failed_selector_xml from raw data}

   Recovered Partial selector:
   {recovered_partial_selector_xml — or "(not available)"}

   Recovered Fuzzy selector:
   {recovered_fuzzy_partial_selector_xml — or "(not available)"}
   ```

2. **Print required warnings verbatim.** When `OrchestratorEnableHeal=false`, print: "Healing Agent was running in recommendation-only mode (OrchestratorEnableHeal=false) — the recovered selector was inferred from the UI tree after the failure but was not validated at runtime. There is no guarantee it will work." Use analogous wording for `RecoverySuccessful=false`.

3. **Ask via AskUserQuestion** using the exact apply/dismiss question, plus a project-path follow-up if the path is unknown.

4. **On accept, delegate the apply; never edit the artifact yourself.** Spawn a subagent that loads the artifact's owning skill (`.xaml`/`.cs`→`uipath-rpa`, which drives the package-bundled selector-recovery flow) and provide the confirmed change: workflow file, activity matched by `ActivityRefId`, before→after value, and `project_dir`. The delegate edits **in place at `project_dir`** (the user's real working copy; do NOT spawn it into a fresh isolated worktree, which forks a throwaway copy the edit never reaches), applies any XML encoding, and validates with `uip rpa validate --file-path "<WORKFLOW_FILE>" --output json`. You run none of those steps and no write-back CLI. After application, confirmation must restate the confirmed root cause and complete resolution, standing alone as the investigation summary for a user seeing only that message; never make the edit appear to be the primary or only fix.

5. **On decline, non-answer, unavailable `AskUserQuestion`, no usable delegate, or delegation failure/error: do not modify files.** Present the proposed edit as plain text and stop. Missing/failed approval or delegation never permits self-editing. If delegation errored or was spawned more than once, first read the target file to verify whether the edit landed; never self-edit to finish or redo delegate work.

Pull every value from raw data. If a required value is missing, such as `recovered_partial_selector_xml`, do not fabricate; state that the action is blocked, name the missing evidence, and offer it as a follow-up.

## Boundaries

- Do NOT fabricate fix steps from undocumented field behavior; cite sources or mark `[Unverified]`.
- `uip docsai ask` is the only CLI command this phase may add beyond what the playbook documents.
- Diagnosis is autonomous, but **you never mutate user source files yourself**. On approval, delegate application to the artifact's owning skill; without approval or a usable delegate, remain recommendation-only. No exceptions.
