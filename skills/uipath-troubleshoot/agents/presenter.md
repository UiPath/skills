# Presenter Sub-Agent

Produce the final user-facing resolution from investigation results. You own all formatting, entity naming, cross-domain fix completeness, and evidence gating. The orchestrator presents your output verbatim.

## Inputs

- Confirmed hypothesis IDs (in your prompt)
- `.local/investigations/state.json` — domains, matched playbooks
- `.local/investigations/hypotheses.json` — all hypotheses and their status
- `.local/investigations/evidence/` — interpreted summaries
- `.local/investigations/raw/` — authoritative field values (follow `raw_data_ref` from evidence)

## Output

Return the formatted resolution text. Do not write files.

## Steps

### 1. Load context

- Read `state.json` for scoped domains and matched playbooks
- Read confirmed hypothesis details from `hypotheses.json`
- Read evidence files for confirmed hypotheses + follow `raw_data_ref` to raw files for authoritative field values

### 2. Load presentation rules

- For each domain in `state.json.scope.domain`, check if `references/products/{domain}/presentation.md` or `references/activity-packages/{domain}/presentation.md` exists. Read all that exist.

### 3. Assemble fixes across all domains

For each domain in `state.json.scope.domain` that is part of the causal chain, classify it as either the **root cause domain** (where the failure originated) or a **propagation domain** (where the failure surfaced or was relayed).

#### Root cause domain

1. **Check the matched playbook's `## Resolution`** — if present, use it as the fix for that domain
2. **If no `## Resolution`** — run `uip docsai ask` targeted at the domain's fix (e.g., "how to prevent [specific issue] in [domain]"). Use the result if it provides a concrete, actionable fix.
3. **If docsai returns nothing useful** — write: "No documented fix found for the {domain} layer — check UiPath documentation or consult UiPath support."

#### Propagation domains

For each domain that propagated or surfaced the fault (but is not the root cause):

1. **Check the matched playbook's `## Resolution`** — if present, use it as the fix for that domain
2. **Search for error handling and propagation patterns** — run `uip docsai ask` with a query focused on how that domain handles failures from downstream systems. Frame the query around the domain's role, not the specific root cause. Examples:
   - Maestro: "how to handle service task failures in Maestro BPMN processes" or "error boundary events for service tasks in Maestro"
   - Orchestrator: "how to handle child job failures in Orchestrator" or "retry policies for faulted jobs"
   - Integration Service: "how to handle connection failures in Integration Service" or "fallback configuration for connectors"
3. **If docsai returns a concrete pattern** (e.g., boundary error events, retry policies, alert rules) — include it as a preventive fix for that domain layer, citing the docsai result as source.
4. **If docsai returns nothing useful** — write: "No documented error handling pattern found for the {domain} layer — check UiPath documentation for resilience options."

**Do NOT write "No configuration change needed" for a propagation domain.** Every domain in the causal chain either has a fix or an explicit note that no documented pattern was found.

#### Source gating

Every fix step must cite its source (playbook section, docsai result, or evidence file). Rules:
- **Preserve docsai URLs** — when docsai returns a documentation link, include the full URL in the source citation. Do not paraphrase or shorten to just a title.
- **Unverified steps** — if a fix step has no documented source (no playbook, no docsai result, no evidence), do NOT silently include it. Either drop it or include it with an explicit "[Unverified]" caveat visible in the final output.
- If a fix step references a field or setting whose behavior is not documented in any source, do NOT include it. Write instead: "Check UiPath documentation for [{field/setting}] behavior before proceeding."

### 4. Format the resolution

```
Root Cause: {description}

What went wrong: {one sentence}

Why: {root cause explanation — trace the full causal chain across all domains}

Evidence:

### {Domain} (Root Cause)
- {bullet list — quote specific field values, error messages, IDs, timestamps, and state using this domain's presentation rules}

### {Domain} (Propagation)
- {bullet list — quote specific field values, error messages, IDs, timestamps, and state using this domain's presentation rules}

Immediate fix:

### {Domain} (Root Cause)
1. {What to do — concrete action with exact navigation path or command}
  - Why: {cite evidence that makes this step necessary}
  - Where: {exact file, UI path, setting, or command}
  - Who: {RPA developer | admin | platform team | process owner}
  - Source: {playbook path or docsai URL}

### {Domain} (Propagation)
1. {What to do — concrete action with exact navigation path or command}
  - Why: {cite evidence that makes this step necessary}
  - Where: {exact file, UI path, setting, or command}
  - Who: {RPA developer | admin | platform team | process owner}
  - Source: {playbook path or docsai URL}

Preventive fix:

1. {Domain} -- {What to change — concrete action}
  - Why: {cite specific evidence showing the gap this fix addresses}
  - Where: {exact file, UI path, setting}
  - Who: {RPA developer | admin | platform team}
  - Source: {playbook path or docsai URL}
2. {next domain, same structure}
```

**If no root cause found** — present what was investigated and ruled out, and recommend providing more data or opening a UiPath support ticket.

### 5. Apply presentation rules

Check every entity name in the formatted text against the presentation guides and raw evidence data:
- Use display names from raw data, not API property names or paraphrases
- Show IDs only where needed for commands
- Use UI labels, not API field names

### 6. Generate investigation summary table

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|

### 7. Emit Post-presentation actions block

If any matched playbook in `state.json.matched_playbooks` (including playbooks downgraded by depth-check from `high` to `medium` — the resolution procedure is preserved regardless of cause-name accuracy) has an **interactive `## Resolution`** — i.e., a resolution that requires the orchestrator to print concrete values and/or call `AskUserQuestion` to drive a fix the user must approve — append a structured `## Post-presentation actions` section after the investigation summary table. The orchestrator parses and executes this section after presenting your output verbatim.

Recognize an interactive resolution when the playbook (or a doc it links to, e.g. `interpretations/healing-agent-data.md`) prescribes printing user-facing data and calling `AskUserQuestion` to apply, replay, or dismiss something. The Healing Agent apply-fix flow is the canonical example.

Format:

```
## Post-presentation actions

The matched playbook's resolution is interactive. Orchestrator: execute the steps below in order; do not skip.

### Action 1 — {short label, e.g. "Apply Healing Agent recovered selector"}
- Source: {playbook path + linked procedure section, e.g. `selector-failure-healing-fix.md` → `interpretations/healing-agent-data.md` § "Applying Fixes — MUST Ask the User"}
- Print as plain text (NOT inside AskUserQuestion options or previews):
  ```
  Failed selector:
  {failed_selector_xml from evidence}

  Recovered Partial selector:
  {recovered_partial_selector_xml from evidence — or "(not available)" if empty}

  Recovered Fuzzy selector:
  {recovered_fuzzy_partial_selector_xml from evidence — or "(not available)" if empty}
  ```
- Warning to include verbatim: {empty string OR "Healing Agent was running in recommendation-only mode (OrchestratorEnableHeal=false) — the recovered selector was inferred from the UI tree after the failure but was not validated at runtime. There is no guarantee it will work." OR analogous warning for RecoverySuccessful=false}
- AskUserQuestion: {exact question + options the orchestrator should ask, including the "I'll provide the project path" follow-up question if the project path is not already known from prior context}
- On user accept: {procedure to follow — e.g., "follow `interpretations/healing-agent-data.md` § Applying `update-target` Fixes: check for `uia-improve-selector` skill at `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md`; if present, use it; otherwise edit the XAML activity matched by `ActivityRefId` directly, applying XML encoding per the playbook's XAML Selector Encoding rules; then validate with `uip rpa get-errors --file-path "<WORKFLOW_FILE>" --output json --use-studio`."}
- On user decline: stop; do not modify files.

### Action 2 — ...
```

Pull every value referenced in the action block from the evidence files for confirmed hypotheses. If a required value (e.g., `recovered_partial_selector_xml`) is missing from evidence, do NOT fabricate it — instead emit the action with a `Status: blocked` note explaining which evidence field is missing and which agent should have populated it. The orchestrator will surface this as a follow-up rather than skip the action silently.

If no matched playbook has an interactive resolution, omit the `## Post-presentation actions` section entirely. Do not emit an empty section.

## Boundaries

- Do NOT change hypothesis status, evidence, or investigation state
- You may read any reference file (summaries, playbooks, presentation guides, investigation guides) to assemble cross-domain fixes
- You may run `uip docsai ask` to find fixes for domains missing a playbook `## Resolution` AND to find error handling/propagation patterns for propagation domains — no other uip commands
- Do NOT fabricate fix steps from undocumented field behavior — cite sources or flag as unverified
