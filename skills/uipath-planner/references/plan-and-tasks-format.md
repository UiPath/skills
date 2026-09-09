# Plan and Tasks Format

Format two artifacts:

- `<feature>.md`: non-PDD plan with architecture notes and tasks.
- `<process>-tasks.md`: PDD-driven task list; architecture remains in the SDD.

Both use the task schema below; only the prelude differs.

## Headers

### Non-PDD lane (`<feature>.md`)

```markdown
# <Feature Name> Implementation Plan

**Goal:** <one sentence summarizing what the automation does>
**Source:** None — planned from user request
**Project type:** <XAML / C# coded / AI Agent / Flow / Application>
**Expression language:** VB.NET (XAML only; N/A for coded / AI Agent / Flow / Application)
**Approach:** <explore-first / simultaneous>
**Execution autonomy:** <autonomous / interactive>
**Delivery model:** <cloud / automation-suite <version> / standalone>  <!-- only when delivery signals were present in the request; omit otherwise -->
**App type:** <web / desktop / citrix / N/A>
**App state:** <open-and-ready / user-will-open / skip-discovery / N/A>
**UI targeting:** <agent-builds-you-review / user-indicates / N/A>

## Understanding

<2–4 sentences: interpretation, key inputs and outputs, and resolved assumptions or ambiguities.>

## Decisions & Trade-offs

- Why this project type
- Why skills are loaded in this order
- Trade-offs and risks

## Stop conditions

<Populate only when `Execution autonomy` is `autonomous`. List concrete hard blockers that MUST interrupt execution; everything else continues without asking. Examples:
- Authentication fails and cannot be recovered without user credentials
- The target application is unresponsive after a reasonable retry window
- A UI element cannot be captured reliably after 3 selector-improvement attempts
- A referenced file, package, or resource does not exist and cannot be created
- A pre-existing record blocks idempotent execution and cleanup is ambiguous

In `interactive` mode this section is optional. "Scope feels large", "many tool calls used", "natural pause point", and "partial result looks usable" are NOT stop conditions.>
```

### PDD-driven: `<process>-tasks.md`

```markdown
# <Process Name> — Implementation Tasks

**Source SDD:** `<process>-sdd.md`
**SDD scope:** <single-product / solution>
**Execution autonomy:** <autonomous / interactive>
**Delivery model:** <cloud / automation-suite <version> / standalone / unspecified>
**Generation date:** <YYYY-MM-DD>

> Tasks below are derived from the SDD. The SDD remains the architectural source of truth.
> When `Execution autonomy: interactive`, the planner enters plan mode for review before execution.
```

## Task schema

Every task in either file uses:

```markdown
## Task T<N> — <skill-name> — <short description>

**Identity:** `<skill>:<project>:<subject>`
**Status:** [ ] pending  *(or [~] in_progress / [x] completed / [!] blocked)*
**Completed:** <YYYY-MM-DD by agent|human>  *(only when Status = [x])*
**Blocked by:** <T1, T2 / none>
**Skill prompt:**

> <Imperative prompt activating the specialist skill. Include exact SDD section references in the PDD-driven lane. End with the anti-hallucination rule.>

- [ ] <concrete sub-step: action + file paths / activity names / commands>
- [ ] <concrete sub-step: expected outcome or verification>
- [ ] **Validate:** <compile / build / lint / run check>
```

### Field rules

- `Task T<N>` is required, sequential within the file, and renumbered on regeneration.
- `<skill-name>` is one of `uipath-rpa`, `uipath-platform`, `uipath-solution`, `uipath-agents`, `uipath-coded-apps`, `uipath-functions`, `uipath-maestro-flow`, `uipath-maestro-bpmn`, `uipath-maestro-case`, `uipath-api-workflow`, `uipath-connector-builder`, `uipath-ixp`, `uipath-mcp-servers`, `uipath-human-in-the-loop`, `uipath-test`. Emit this skill in the live `TaskCreate` call.
- `Identity` is the stable tuple `<skill>:<project>:<subject>` used across regenerations. Split on the first two colons only; `<subject>` may contain colons, including typed-resource form `<kind>:<name>`. Examples: `rpa:VendorInvoice_Performer:Process/CalculateTotal.xaml`, `platform:VendorInvoice:queue:VendorQueue`, `agents:InvoiceClassifier:tools/extract_amount.py`, `rpa:VendorInvoice:testing`.
- `Status` is `[ ]` pending, `[~]` in_progress, `[x]` completed, or `[!]` blocked.
- Include `Completed:` only for `[x]`, using `YYYY-MM-DD by agent` or `YYYY-MM-DD by human`; use `agent` when `TaskUpdate` flips the checkbox and `human` only for manual edits.
- `Blocked by` is required, comma-separated task IDs or `none`, and drives live `addBlockedBy`.
- Paste `Skill prompt` verbatim into `TaskCreate.description`; end it with the anti-hallucination rule.
- Sub-steps are concrete, checkable, one action per checkbox, with no `TBD` or `as needed`.
- Every generation task ends with a `Validate:` sub-step using a build/lint/compile check.

## Anti-hallucination rule

Append this exact line to every `Skill prompt`, filling in the SDD path for PDD-driven tasks:

```text
Use values, mappings, and structure exactly as documented in the SDD at <sdd-path>. Do not infer or guess.
```

For non-PDD tasks, reference the plan by path, never “this plan”:

```text
Use values, mappings, and structure exactly as documented in the plan at <PLAN_FILE_PATH>. Do not infer or guess.
```

## Mandatory testing and artifact validation

For every plan with a generation skill (`uipath-rpa`, `uipath-maestro-flow`, `uipath-maestro-bpmn`, `uipath-agents`, `uipath-coded-apps`), add a dedicated Testing task for each generation skill immediately after its generation tasks and before deployment (`uipath-solution` for `.uipx`-bundled solutions; `uipath-platform` for non-solution Orchestrator operations).

For a custom connector (`uipath-connector-builder`) or IXP model (`uipath-ixp`), add one validation task per artifact immediately after the build task and before any consumer build task: connector validate/import check or IXP model metrics review.

```markdown
## Task T<N> — <generation-skill> — Testing (MANDATORY)

**Identity:** `<skill>:<project>:testing`
**Status:** [ ] pending
**Blocked by:** <generation task IDs>
**Skill prompt:**

> Load <generation-skill> and run its testing workflow end-to-end. Always thorough:
> happy path + edge cases + error scenarios + (for Master Projects) end-to-end pipeline tests.
> See that skill's testing references for commands, test-case authoring, and best practices.
> Do not describe the testing procedure here — the specialist owns it.

- [ ] Run testing workflow per <generation-skill>'s testing reference
- [ ] **Validate:** all tests pass; record results
```

## Regenerate logic (PDD-driven lane only)

When the user chooses “Regenerate from the SDD” on the planner's resume question:

1. Read old `<process>-tasks.md` and list `(identity_tuple, status, completed_by, completed_date)`.
2. Parse the possibly updated SDD and list new tasks with identities.
3. Match new tasks to old tasks by identity tuple:
   - `[x]` completed: preserve status and `Completed` line.
   - `[~]` in_progress: preserve status.
   - `[ ]` pending: keep pending.
   - Unmatched new task: pending.
4. Put old tasks unmatched in the new SDD in the Archive footer below.
5. Renumber tasks `T1..TN` in new order.
6. Write the new `<process>-tasks.md`.
7. Show a summary diff with preserved, added, and archived counts.
8. Emit live `TaskCreate` calls for the new tasks file.

### Archive footer

If the new SDD removes old tasks, append:

```markdown
---

## Archive — Tasks removed from plan

| Old ID | Identity | Status before removal | Removed on |
|---|---|---|---|
| T7 | `rpa:VendorInvoice_OldReporting:Main.xaml` | [x] completed | <YYYY-MM-DD> |

> These tasks existed in a previous version of this file but are no longer in the SDD.
> Completed work is not deleted — historical record only.
```

### Summary message

After regeneration, output:

```text
Regenerated <process>-tasks.md from SDD.
- 4 tasks preserved as completed
- 1 task preserved as in_progress
- 3 tasks unchanged pending
- 2 tasks added (new in SDD)
- 1 task archived (removed from SDD)
- SDD content may have changed since completed tasks ran. Sanity-check those
  implementations against the current SDD before continuing.
```

## TaskCreate / TaskUpdate mapping

| File field | Live task field |
|---|---|
| `Task T<N> — <skill> — <description>` | `subject` = `<skill> — <description>` |
| `Status: [ ] pending` | initial status `pending` |
| `Status: [~] in_progress` | status `in_progress` |
| `Status: [x] completed` | status `completed` |
| `Identity:` | `metadata.identity` |
| `Skill prompt:` | `description` verbatim, including anti-hallucination rule |
| `Blocked by:` | `addBlockedBy` after all tasks are created |
| `Completed:` | `metadata.completed_by`, `metadata.completed_date` |

Rule G-8 applies (defined in [sdd-generation-guide.md](sdd-generation-guide.md) Phase 1 Step 0.5): if any `TaskCreate` or `TaskUpdate` fails, log one warning, continue without live tasks, and do not retry. The markdown plan/tasks file is authoritative.

## Plan-mode integration

Both files are valid `EnterPlanMode` payloads:

- Non-PDD `explore-first`: call `EnterPlanMode` with the full `<feature>.md`; after approval, `ExitPlanMode`, then emit live `TaskCreate` calls.
- PDD-driven `interactive`: call `EnterPlanMode` with the full `<process>-tasks.md`; after approval, `ExitPlanMode`, then emit live `TaskCreate` calls.
- Non-PDD `simultaneous` and PDD-driven `autonomous`: skip `EnterPlanMode`; emit the file as text, then immediately emit live `TaskCreate` calls.

## Quality rules

1. **No placeholders:** every sub-step has concrete details; never `TBD`, `as needed`, or `similar to Task N`.
2. **Granularity:** use one clear action per step.
3. **Checkboxes:** every sub-step uses `- [ ]`.
4. **Stable identity:** identities are unique within the file.
5. **Generation validation:** every generation task ends with `Validate:`.
6. **Mandatory testing:** every generation skill has a dedicated Testing task before deployment; testing never substitutes for `Validate:`.
7. **Anti-hallucination:** append the required rule to every Skill prompt.
8. **Skill order:** RPA precedes platform deployment; integrated components precede consumers; testing precedes deployment.
9. **No specialist-internal flow leakage:** state which skill loads and in what order, not target configuration, Orchestrator registration, XAML authoring, authentication, or testing procedures; specialist documents own those details.
10. **Autonomous stop conditions:** populate concrete hard blockers for autonomous plans, including realistic authentication, app-state, element-capture, and missing-resource blockers. Never use a generic placeholder.
11. **No authoring-surface fields:** Studio, Studio Web, and VS Code are presentation layers. Do not use them in plan headers, task conditions, or routing; carry user surface preferences as ordinary requirement prose in the relevant task prompt.