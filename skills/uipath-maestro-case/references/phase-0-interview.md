# Phase 0 — Interview Mode (sdd.md generation)

Phase 0 generates `sdd.md` interactively when none is provided. Output is approved by the user, then handed to Phase 1 unchanged. Lightweight by design: complex/multi-product processes redirect to `uipath-solution-design`.

> **Authoritative for the interview path only.** Trigger detection, round shape, threshold redirect, hard-stop, resumption. Phase 1 logic stays in [planning.md](planning.md). Phases 2–6 stay in [phased-execution.md](phased-execution.md).

## When Phase 0 runs

Strict binary trigger. **Any `sdd.md` present at the resolved path → no interview.** Phase 1 trusts the file as written (Rule 2).

```
Step 1. Skill invoked.
Step 2. If user did not pass an sdd.md path: ask path. Default proposed = ./sdd.md.
Step 3. Resolve path. Stat the file.
Step 4. File exists → exit Phase 0. Hand to Phase 1.
Step 5. File absent →
        Step 5a. Check for sdd.draft.md at same path. If present → resume prompt (§Resumption).
        Step 5b. No draft → entry prompt (§Entry).
```

### Entry prompt

AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Interview to generate sdd.md` | Begin Round 1. |
| `I'll provide an sdd.md path` | Re-prompt for path. Loop to Step 3. |
| `Switch to uipath-solution-design` | Print plain-text suggestion. Exit skill. |

Never auto-invoke `uipath-solution-design` (Rule 15). Print the skill name and one-line guidance only.

## The four rounds

Each round produces or updates `sdd.draft.md`. Final approval renames `sdd.draft.md` → `sdd.md` (atomic). The `assets/templates/sdd-template.md` is the structural reference — fill its sections from interview answers.

| Round | Goal | Output | Threshold check |
|---|---|---|---|
| 1 — Open describe | Identity + free-text process description + archetype hint + rough counts | In-memory only | Upfront triage (rough counts) |
| 2 — Skeleton + gap-fill | Drafted `sdd.md` skeleton, blocking gaps resolved | `sdd.draft.md` written | Mid-check (counted from skeleton) |
| 3 — Registry resolution | Concrete tenant resources picked per task | `sdd.draft.md` updated, `tasks/registry-resolved.json` written | — |
| 4 — Review + HARD STOP | User approves, edits, restarts, or aborts | `sdd.md` finalized | Re-check on edit |

### Round 1 — Open describe

Single user-facing message. Three asks bundled:

1. **Free-text description.** "Describe the process. Who starts it? What stages does it go through? Where does it end?"
2. **Archetype hint** (AskUserQuestion, 4 options — hint only, used to seed stage skeleton). Render each option with its example so the user is not guessing at jargon:
   - `Approval` — one decision gate, end-to-end (e.g., expense approval, leave request, PTO)
   - `Intake & Routing` — incoming items get classified, then routed to the right handler (e.g., support ticket triage, lead qualification, IT request routing)
   - `Multi-stage Orchestration` — sequential stages with handoffs across roles or systems (e.g., employee onboarding, candidate interview pipeline, loan origination)
   - `Other / not sure` — describe in free-text (Round 1 ask 1); agent infers shape from description
3. **Upfront triage counts.** "Roughly how many stages? How many systems integrated? How many distinct user roles?"

#### Upfront triage redirect

If the rough counts already exceed any threshold (see §Thresholds), trigger soft redirect (§Soft redirect). Do NOT proceed to Round 2 until user picks `Continue lightweight anyway` or `Abort`.

### Round 2 — Skeleton + gap-fill

Agent drafts `sdd.draft.md` from Round 1 answers, using `assets/templates/sdd-template.md` as the structural mold. Fill what was provided. Mark the rest:

- Optional fields the user did not touch → `—` (template-native placeholder).
- **Required-but-unknown** fields → `<UNRESOLVED: question>` marker.

After writing, inspect blocking gaps. **Required fields (block until answered):**

| Field | Source |
|---|---|
| Case Name (PascalCase) | Round 1 free-text |
| Case Identifier prefix (2-4 char UPPER) | Ask if absent |
| ≥1 Trigger (Manual / Timer / Connector Event) | Ask if absent |
| ≥1 Stage with name | Round 1 free-text |
| ≥1 Task per stage with name + type | Walk stages, ask per stage |
| ≥1 Case exit condition | Ask if absent |

Ask blocking gaps via AskUserQuestion (multi-choice) or plain-text follow-up (open answer). Update `sdd.draft.md` after each answered gap.

**Stuck-round detector.** If 3 unanswerable / contradictory / off-topic replies accumulate within Round 2, soft prompt (§Soft redirect). User picks `Continue with skeletons` (mark remaining as `<UNRESOLVED>`, proceed) / `Switch to uipath-solution-design` / `Abort`.

#### Mid-check threshold

After the skeleton is written, count from `sdd.draft.md`:

- Stages
- Tasks total
- Distinct integrations (connectors mentioned)
- Distinct personas
- `case-management` tasks (child cases)
- Exception stages — **counted but never triggers redirect** (allowed regardless of count)

If any quantitative threshold breached → §Soft redirect.

### Round 3 — Registry resolution

For each task in `sdd.draft.md`, search the matching cache file under `~/.uip/case-resources/` by name keywords. Filename varies by component type — common cases:

- `process-index.json`, `agent-index.json`, `api-index.json`, `processOrchestration-index.json`, `caseManagement-index.json` — `<type>-index.json` shape
- `action-apps-index.json` — kebab + plural for HITL action apps
- `typecache-activities-index.json` — for `execute-connector-activity` (`CONNECTOR_ACTIVITY`)
- `typecache-triggers-index.json` — for `wait-for-connector` (`CONNECTOR_TRIGGER`)

Run `uip maestro case registry pull` first if cache absent. See [registry-discovery.md § Cache File Index](registry-discovery.md#cache-file-index) for the authoritative file list, identifier fields, and cross-type fallback rules.

Per-task AskUserQuestion (4 options max):

| Option | Effect |
|---|---|
| `<top match — name + version + type>` | Record selection. |
| `<second match>` (if available) | Record selection. |
| `Skeleton — resolve later` | Keep `<UNRESOLVED>` marker on `taskTypeId` / `typeId` / `connectionId`. Phase 1 emits skeleton task per Rule 8. |
| `Something else` | Free-text re-search keyword, retry. |

After all picks, write `tasks/registry-resolved.json` matching the shape Phase 1 produces (search query, all matched results, selected result, rationale per Rule 9). Update `sdd.draft.md` with concrete resource names.

> **Phase 1 handoff.** Phase 1 reads `tasks/registry-resolved.json` and skips re-search for resolved entries. It still extends the file with any resolutions Phase 0 deferred. No artifact replay; sdd.md is the contract.

### Round 4 — Review + HARD STOP

1. Rename `sdd.draft.md` → `sdd.md`. Atomic.
2. Print plain-text summary:

```
Phase 0 complete.

Path:    ./sdd.md
Stages:  N
Tasks:   N
  - process: N
  - agent: N
  - ...
Integrations: N
Personas:     N
Child cases:  N
Threshold status: WITHIN | EXCEEDED (<which>)
```

3. AskUserQuestion (4 options):

| Option | Next |
|---|---|
| `Approve and proceed to Phase 1` | Exit Phase 0. Begin [planning.md](planning.md) Step 1. |
| `I edited sdd.md — re-validate` | Re-read sdd.md. Re-validate structure. Re-run mid-check threshold. If valid + within thresholds → re-show summary + re-ask. If invalid or threshold breached → block with errors / soft redirect. |
| `Restart interview` | Wipe `sdd.md`, `sdd.draft.md`, `tasks/registry-resolved.json`. Loop to Round 1. |
| `Abort / switch to uipath-solution-design` | Print suggestion. Exit skill. Leave artifacts in place for the user. |

#### Edit-loop validation

On `Re-validate`, structural checks:

- Required fields per Round 2 §Required (case name, prefix, ≥1 trigger, ≥1 stage, ≥1 task per stage with type, ≥1 case exit)
- Every stage has ≥1 task entry
- Every task has a `Type:` from the closed 9-value schema enum (`process` | `agent` | `rpa` | `action` | `api-workflow` | `case-management` | `execute-connector-activity` | `wait-for-connector` | `wait-for-timer`). Reject `external-agent`, `connector-activity`, `connector-trigger`, or any other value (SKILL.md Rule 16).
- Every task has at minimum a `Description:` line
- **Exit Condition WHEN ↔ Marks Complete pairing** (sdd-template.md Key Rule 4 — applies to both stage exit and case exit):
  - **Stage exit:** `Marks Stage Complete: Yes` → must use `required-tasks-completed` / `required-stages-completed`; `No` → may use `selected-tasks-completed(...)`. Flag any `Yes + selected-tasks-completed` pair as error.
  - **Case exit:** `Marks Case Complete: Yes` → must use `required-stages-completed` / `wait-for-connector`; `No` → may use `selected-stage-completed(...)` / `selected-stage-exited(...)` / `wait-for-connector`. Flag any `Yes + selected-stage-*` pair as error.

Validation fail → list specific issues, AskUserQuestion `Re-edit and re-validate` / `Restart interview` / `Abort`.

Threshold breach on edit → §Soft redirect (user can override or switch).

## Thresholds

Hard quantitative caps. Breach triggers §Soft redirect (not hard refuse).

| Threshold | Cap |
|---|---|
| Stages | > 7 |
| Tasks total | > 14 |
| Distinct integrations | > 3 |
| Distinct personas | > 3 |
| Child cases (`case-management` tasks) | ≥ 1 |

**Exception stages are NOT a threshold.** They may appear freely.

## Soft redirect

AskUserQuestion (3 options):

| Option | Effect |
|---|---|
| `Switch to uipath-solution-design (recommended)` | Print plain-text suggestion. Exit skill. Preserve `sdd.draft.md`. |
| `Continue lightweight anyway` | Proceed. **Set warning header in generated sdd.md** (§Warning header). |
| `Abort` | Exit. No file changes beyond what already exists. |

### Warning header

When user chose override, prepend the following to the generated `sdd.md` immediately under the H1 title:

```markdown
> **⚠️ Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: <stages> stages, <tasks> tasks, <integrations> integrations,
> <personas> personas, <child-cases> child cases.
> Review carefully before approving. Consider regenerating via `uipath-solution-design`.
```

The header is informational. Phase 1 ignores it (markdown comments / blockquotes are not parsed as structural fields).

## Resumption

When `sdd.draft.md` is detected at Step 5a:

AskUserQuestion (4 options):

| Option | Effect |
|---|---|
| `Resume from draft (round N)` | Re-read `sdd.draft.md`, infer last completed round (presence of all required fields = Round 2 done; presence of `tasks/registry-resolved.json` = Round 3 done). Continue from next round. |
| `Discard draft, restart` | Delete `sdd.draft.md` + `tasks/registry-resolved.json`. Begin Round 1. |
| `Use draft as-is, finalize` | Run Round 4 hard-stop on the draft as it stands. Edit-loop validation may flag missing required fields. |
| `Abort` | Exit. No file changes. |

**Round 1 is in-memory only — never persisted.** Resumption can only resume from Round 2 onward.

## Failure modes

| Symptom | Action |
|---|---|
| User says "skip" / "I don't know" on optional field | Write `—`. |
| User says "skip" on required field | Write `<UNRESOLVED: <agent's question>>`. Phase 1 + post-build loop will revisit. |
| 3 unanswerable replies in single round | Trigger §Soft redirect. |
| Registry pull fails (CLI error, no auth) | Skip Round 3. All tasks marked `<UNRESOLVED>`. Phase 1 emits skeletons. Inform user. |
| User edits `sdd.md` to add stages exceeding threshold | Edit-loop validation fires §Soft redirect. |
| `sdd.md` already exists at path when interview begins | Should not happen — Step 4 exits Phase 0 first. If it does (race), abort with error. Never overwrite. |

## Output contract — what Phase 1 sees

After Phase 0 approval, the working directory contains:

- `sdd.md` — fully written, may include warning header, may contain `<UNRESOLVED>` markers, may contain `—` placeholders.
- `tasks/registry-resolved.json` — resolutions persisted from Round 3 (matches Phase 1's artifact shape per Rule 9).
- `sdd.draft.md` — deleted (renamed to `sdd.md` at Round 4 step 1).

Phase 1 (planning.md Step 2) reads `sdd.md` exactly as it would a user-provided file. Rule 2 applies from this point: trust as written, no further gap-fill.

## Anti-patterns

- **Do NOT overwrite an existing `sdd.md`.** Strict binary trigger; presence = trust-as-written.
- **Do NOT auto-invoke `uipath-solution-design`.** Print the suggestion; user re-invokes manually (Rule 15).
- **Do NOT persist Round 1 transcripts.** In-memory only. Restart wipes cleanly.
- **Do NOT use `sed`/`awk`/`python`/`node` to mutate `sdd.draft.md` or `tasks/registry-resolved.json`.** Read + Write/Edit only (Rule 13).
- **Do NOT silently auto-pick a registry match in Round 3.** AskUserQuestion every task; never infer (Rule 2 spirit).
- **Do NOT proceed past upfront triage when counts already exceed thresholds.** Force soft-redirect prompt before drafting.
- **Do NOT skip the warning header when user overrode threshold.** Future agents reading the file must see the override flag.
