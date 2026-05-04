# Plan and Tasks Format

Format spec for the planner's two output artifacts:

- `<feature>.md` — non-PDD lane plan file (combines lightweight architecture notes + task list)
- `<process>-tasks.md` — PDD-driven lane task file (task list only; architecture lives in the SDD)

Both share the same task row schema. The difference is the prelude — `<feature>.md` carries an architecture summary; `<process>-tasks.md` does not (the SDD is the architecture).

## Header schema

### Non-PDD lane (`<feature>.md`)

```markdown
# <Feature Name> Implementation Plan

**Goal:** <one sentence summarizing what the automation does>
**Source:** None — planned from user request
**Project type:** <XAML / C# coded / AI Agent / Flow / Application>
**Expression language:** VB.NET (XAML only; N/A for coded / AI Agent / Flow / Application)
**Approach:** <explore-first / simultaneous>
**Execution autonomy:** <autonomous / interactive>
**App type:** <web / desktop / citrix / N/A>
**App state:** <open-and-ready / user-will-open / skip-discovery / N/A>
**UI targeting:** <agent-builds-you-review / user-indicates / N/A>

## Understanding

<2–4 sentences: interpretation of the request, key inputs and outputs, assumptions
or ambiguities resolved during elicitation.>

## Decisions & Trade-offs

- Why this project type
- Why specific skills are loaded in this order
- Trade-offs and risks
```

### PDD-driven lane (`<process>-tasks.md`)

```markdown
# <Process Name> — Implementation Tasks

**Source SDD:** `<process>-sdd.md`
**SDD scope:** <single-product / solution>
**Execution autonomy:** <autonomous / interactive>
**Generation date:** <YYYY-MM-DD>

> Tasks below are derived from the SDD. The SDD remains the architectural source of truth.
> When `Execution autonomy: interactive`, the planner enters plan mode for review before execution.
```

## Task row schema

Every task — in both file types — uses this exact structure. The fields below are load-bearing for the regenerate-with-preservation flow (see "Regenerate logic" below).

```markdown
## Task T<N> — <skill-name> — <short description>

**Identity:** `<skill>:<project>:<subject>`
**Status:** [ ] pending  *(or [~] in_progress / [x] completed / [!] blocked)*
**Completed:** <YYYY-MM-DD by agent|human>  *(only present when Status = [x])*
**Blocked by:** <T1, T2 / none>
**Skill prompt:**

> <Imperative prompt that activates the specialist skill. Include exact SDD section
>  references when in PDD-driven lane. End with the anti-hallucination rule.>

- [ ] <concrete sub-step: action + file paths / activity names / commands>
- [ ] <concrete sub-step: expected outcome or verification>
- [ ] **Validate:** <compile / build / lint / run check>
```

### Field rules

| Field | Required | Notes |
|---|---|---|
| `Task T<N>` | yes | Sequential within the file. Renumber on regeneration. |
| `<skill-name>` | yes | One of `uipath-rpa`, `uipath-platform`, `uipath-agents`, `uipath-coded-apps`, `uipath-maestro-flow`, `uipath-maestro-case`, `uipath-human-in-the-loop`, `uipath-test`, `uipath-rpa-legacy`, `uipath-interact`. The planner emits this skill in the live `TaskCreate` call. |
| `Identity` | yes | Stable tuple `<skill>:<project>:<subject>`. Used to match tasks across regenerations. Examples: `rpa:VendorInvoice_Performer:Process/CalculateTotal.xaml`, `platform:VendorInvoice:queue:VendorQueue`, `agents:InvoiceClassifier:tools/extract_amount.py`. |
| `Status` | yes | One of `[ ]` pending, `[~]` in_progress, `[x]` completed, `[!]` blocked. |
| `Completed` | only when `[x]` | `YYYY-MM-DD by agent` or `YYYY-MM-DD by human`. The planner sets `agent` when its TaskUpdate flips the checkbox; `human` only when the user manually edits the file. |
| `Blocked by` | yes | Comma-separated task IDs, or `none`. Drives the live `addBlockedBy` calls. |
| `Skill prompt` | yes | Imperative prompt the planner pastes into the TaskCreate `description`. Must end with the anti-hallucination rule (below). |
| Sub-steps | yes | Concrete, checkable actions. One clear action per checkbox. No "TBD", no "as needed". |
| `Validate:` sub-step | yes | Every generation task ends with a build/lint/compile check. |

## Anti-hallucination rule (mandatory in every Skill prompt)

Append this exact line to every `Skill prompt` block, with the SDD path filled in for PDD-driven lane:

```
Use values, mappings, and structure exactly as documented in the SDD at <sdd-path>. Do not infer or guess.
```

For non-PDD lane, the prompt references the plan file:

```
Use values, mappings, and structure exactly as documented in this plan. Do not infer or guess.
```

## Testing task is mandatory

Every plan with a generation skill (`uipath-rpa`, `uipath-maestro-flow`, `uipath-agents`, `uipath-coded-apps`) gets a dedicated Testing task per generation skill, placed immediately after that skill's generation tasks and **before** any deploy task (`uipath-platform`).

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

When the user picks "Regenerate from the SDD" on the planner's resume question, preserve completed work via identity matching.

### Algorithm

```
1. Read old <process>-tasks.md → list of (identity_tuple, status, completed_by, completed_date)
2. Parse the (possibly updated) SDD → list of new tasks with identities
3. For each new task:
   - Match against old tasks by identity_tuple
   - matched & old status == [x] completed → preserve as completed (carry over Completed line)
   - matched & old status == [~] in_progress → preserve as in_progress
   - matched & old status == [ ] pending → keep pending (no change)
   - unmatched (new in SDD) → pending
4. Old tasks unmatched in new SDD → write to "Archive" footer (see below)
5. Renumber tasks T1..TN in the new order
6. Write the new <process>-tasks.md
7. Show user a summary diff (preserved counts, added, archived)
8. Emit live TaskCreate calls per the new tasks.md
```

### Archive footer format

When the new SDD removes tasks that existed in the old plan, append them to a section at the bottom of the file:

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

After regeneration, output a one-block summary:

```
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

The planner emits live tasks that mirror the file. Mapping rules:

| File field | Live task field |
|---|---|
| `Task T<N> — <skill> — <description>` | `subject` = `<skill> — <description>` |
| `Status: [ ] pending` | initial status `pending` |
| `Status: [~] in_progress` | status `in_progress` |
| `Status: [x] completed` | status `completed` |
| `Identity:` | `metadata.identity` (so future runs can match) |
| `Skill prompt:` | `description` (verbatim, including anti-hallucination rule) |
| `Blocked by:` | `addBlockedBy` (after all tasks are created) |
| `Completed:` | `metadata.completed_by`, `metadata.completed_date` |

**Rule G-8 applies (inherited from solution-design):** if any TaskCreate or TaskUpdate fails, log a single warning, continue without live tasks, and do not retry. The markdown plan / tasks file is the authoritative deliverable.

## Plan-mode integration

Both files are valid `EnterPlanMode` payloads.

- **Non-PDD lane explore-first:** call `EnterPlanMode` with the full `<feature>.md` content. User approves → `ExitPlanMode` → emit live `TaskCreate` calls.
- **PDD-driven lane interactive:** call `EnterPlanMode` with the full `<process>-tasks.md` content. User approves → `ExitPlanMode` → emit live `TaskCreate` calls.
- **Non-PDD lane simultaneous / PDD-driven autonomous:** skip `EnterPlanMode`. Emit the file as text, then immediately emit live `TaskCreate` calls.

## Quality rules (applied during self-review before saving)

1. **No placeholders.** Every sub-step has concrete details. Never "TBD", "as needed", "similar to Task N".
2. **Granular sub-steps.** One clear action per step.
3. **Checkbox syntax.** `- [ ]` on every sub-step.
4. **Identity tuple is stable and unique** within the file.
5. **Every generation task ends with a `Validate:` sub-step.**
6. **Every generation skill has a dedicated Testing task** placed before any deploy task. Testing is mandatory — never a `Validate:` sub-step substitute.
7. **Anti-hallucination rule** appended to every Skill prompt.
8. **Skill order is correct** — RPA before platform deploy; integrated components before consumers; testing before deploy.
9. **No specialist-internal flow leakage.** The plan says WHICH skill to load and IN WHAT ORDER. It does NOT describe the skill's internal flow (target-configuration, OR registration, XAML authoring pipelines, auth flows, testing procedures). Each specialist's own docs own those details.
