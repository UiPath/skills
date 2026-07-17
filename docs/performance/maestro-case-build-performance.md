# Maestro Case Build Performance Investigation

## Status

- **Outcome:** Experiment 1 concluded negatively. Follow-up Experiment 2 was faster and cheaper, but failed the deterministic grader and did not follow its intended cache/batching contract.
- **Decision:** Keep PR #2098 closed and do not open or merge a follow-up PR. Correct the cache-consumption and semantic-condition fidelity before spending on another benchmark.
- **Date:** 2026-07-17 (Pacific time)
- **Scope:** `uipath-maestro-case` Golden Expense end-to-end build

## Links

- Draft experiment PR: [UiPath/skills#2098](https://github.com/UiPath/skills/pull/2098)
- Experiment branch: `experiment/maestro-case-llm-build-speed`
- Experiment commit after rebasing onto `main`: `bb0b18340be56979df9824a67a62109a67e449b9`
- Baseline report: [Golden Expense baseline](https://coder-evalboard.uipath-dev.com/runs/2026-07-16_04-24-15/skill-case-golden-rebuild-cm-expense)
- Successful experiment run: [GitHub Actions 29541608582](https://github.com/UiPath/skills/actions/runs/29541608582), attempt 2
- Earlier infrastructure-only failures: [GitHub Actions 29539778252](https://github.com/UiPath/skills/actions/runs/29539778252)
- Follow-up branch: `experiment/maestro-case-schema-once-stage-batching`
- Follow-up implementation commit: [`a83cb1eae`](https://github.com/UiPath/skills/commit/a83cb1eae49192334220e1478b887ff61a4ceafa)
- Follow-up run: [GitHub Actions 29596260683](https://github.com/UiPath/skills/actions/runs/29596260683)

## Goal

Reduce the time and cost required for an LLM agent to build a large `caseplan.json`, while preserving the existing deterministic grader result and keeping the LLM as the sole author of the JSON.

This effort intentionally did **not** introduce a deterministic renderer, a helper script, CLI-based JSON mutation, task YAML changes, grader changes, or schema changes.

## Baseline Diagnosis

The baseline completed successfully but took 52m55s and cost $9.73. Model generation dominated the run; tool execution accounted for only about five minutes.

Observed baseline characteristics:

- 217,198 output tokens
- 13,932,735 cache-read tokens
- 578,104 cache-creation tokens
- 41,813 uncached input tokens
- 194 agent turns and 190 tool calls
- Three `caseplan.json` Writes: approximately 0.9 KB, 27.6 KB, and 73.3 KB
- The largest Write required 171 seconds and 27,949 output tokens
- One 32,000-token response emitted no tool call, followed by context reconstruction
- 16 `tasks describe` calls for six resource needs
- Five `case spec` calls for two connector needs
- 42 task-ledger calls

The initial hypothesis was that prohibiting populated whole-file rewrites would eliminate the longest model generations and reduce context reconstruction.

## Experiment

PR #2098 changed only the skill instructions and supporting references:

1. Permit `Write(caseplan.json)` only for the initial T01 root scaffold.
2. Require `Edit` for every later `caseplan.json` mutation.
3. Group changes by a stable target, such as one stage task array, one task I/O array, one condition target, or one SLA target.
4. Limit an Edit replacement payload to 30 KB and split larger targets.
5. Track progress at section level instead of creating a todo for every T-entry.
6. Remove conflicting plugin guidance that could still be interpreted as a later whole-file Write.
7. Preserve the existing phase boundaries, validation commands, hard stops, schema, and deterministic grader.

Local validation passed:

- `git diff --check`
- `quick_validate.py skills/uipath-maestro-case`

## Results

The successful experiment run used `claude-sonnet-4-6`, completed in one iteration, and passed all six weighted criteria with score `1.000`.

| Metric | Baseline | Experiment | Change |
|---|---:|---:|---:|
| Duration | 3,175.0s (52m55s) | 2,983.2s (49m43s) | -191.8s (-6.0%) |
| Cost | $9.7311 | $12.1531 | +$2.4220 (+24.9%) |
| Output tokens | 217,198 | 201,920 | -15,278 (-7.0%) |
| Cache-read tokens | 13,932,735 | 21,103,914 | +7,171,179 (+51.5%) |
| Cache-creation tokens | 578,104 | 703,484 | +125,380 (+21.7%) |
| Uncached input tokens | 41,813 | 51,692 | +9,879 (+23.6%) |
| Agent turns | 194 | 244 | +50 (+25.8%) |
| Tool calls | 190 | 240 | +50 (+26.3%) |

### Accuracy

All deterministic checks passed:

- `uip maestro case validate` returned `Status: Valid`.
- Structure checker confirmed eight stages, fifteen tasks across all nine task types, conditions, timers, SLA, and case identifier.
- Binding checker confirmed all resources, connections, connector types, connector task contracts, and the Stage 5 connector entry rule.
- Semantics checker confirmed SDD dataflow, condition normalization, and approve/reject gate polarity.
- Seed checker confirmed the exact `expenseRequest` object literal.
- No case debug or publish command was executed.

The experiment therefore preserved the tested accuracy contract.

### Mutation Behavior

- Exactly one `caseplan.json` Write was used for the T01 scaffold.
- The agent made 52 `caseplan.json` Edits.
- Average Edit replacement size was 1.83 KB; the largest was 9.88 KB.
- One Edit failed because its target string was stale or mismatched; the agent recovered and the final artifact passed all checks.
- The agent read `caseplan.json` eleven times and `tasks.md` seven times.
- Task-ledger activity did not decrease: 17 `TaskCreate` plus 28 `TaskUpdate` calls, compared with 42 total ledger calls in the baseline.
- Schema lookup duplication remained: 19 `tasks describe` calls and four `case spec` calls.

## Interpretation

The experiment proved that bounded Edits can preserve correctness and prevent populated whole-file Writes. It did **not** prove the intended performance improvement:

- The 6% duration reduction is modest and comes from only one successful run per variant, so it may be within normal model/runtime variance.
- Cost increased 25% because the agent used more turns and replayed substantially more cached context.
- The 7% output-token reduction was outweighed by a 51% increase in cache-read tokens.
- Fifty-two small caseplan Edits replaced a few expensive large generations with many smaller inference round trips.
- Section-level progress guidance did not reduce task-ledger traffic in practice.
- Schema lookup duplication slightly worsened for `tasks describe`.

The accuracy risk shifted rather than disappeared: narrow Edits reduce accidental field deletion, but stale-target failures and cross-Edit consistency become more likely as Edit count grows.

## Decision

Do not merge PR #2098 as written. Close it as a documented negative experiment.

The useful retained finding is that **one scaffold Write plus bounded Edits is accurate, but the Edit granularity must be much coarser**. A follow-up should target fewer inference turns and less context replay, not merely smaller output payloads.

## Follow-up Experiment 2 — Schema Once + Stage Batching

Status: rejected by the first unchanged Golden Expense run. The implementation branch remains a diagnostic artifact, not a merge candidate.

This variant combines the first two recommended follow-ups because they attack separate sources of turns:

1. **Run-scoped exact-request schema cache.** Phase 1 creates `tasks/schema-cache.json`. Every non-connector `tasks describe`, connector `case spec`, and `get-connection` request is keyed by all shape-affecting arguments; exact hits are reused by every consumer. The full response is retained, not a summary. A shared schema never shares generated task/input/output/binding IDs.
2. **Prefer one populated connector request.** When the SDD already carries exact field keys and requires no reference/filter discovery, skip the lean `--skip-case-shape` request and let one populated response serve planning verification plus implementation. A lean request remains available for genuinely ambiguous mappings and is separately deduplicated; accuracy takes precedence over forcing unlike requests into one cache entry.
3. **Stage-level mutation.** T01 remains the only whole-file Write. Phase 2 normally appends all complete stage/task shapes in one `schema.nodes` Edit. Phase 3 performs one final Edit per owning stage, folding connector detail, task I/O, stage/task conditions, SLA, and `$xref` resolution into that replacement. Case-level rules/SLA and bindings use one root finalization Edit.
4. **Bounded exception.** A stage replacement over 30KB may split into at most two slices. The path never falls back to per-task/per-condition Edits or a populated whole-file Write.
5. **Artifact-based progress.** `tasks.md` and `id-map.json` remain the T-by-T audit. Progress tracking stays at phase/stage-pass level instead of adding TaskCreate/TaskUpdate calls for every T-entry.

### Acceptance Criteria

The unchanged Golden Expense task and deterministic grader remain the correctness contract.

| Measure | Previous experiment | Follow-up target |
|---|---:|---:|
| Deterministic score | 1.000 | 1.000 |
| `caseplan.json` Writes | 1 | 1 (T01 only) |
| `caseplan.json` Edits | 52 | 10–13 normal path; ≤16 acceptable |
| `tasks describe` calls | 19 | ≤6 unique non-connector requests |
| `case spec` calls | 4 | 2 populated unique needs on the Golden path; lean calls only if the SDD is ambiguous |
| Task-ledger calls | 45 | Phase/section level; no per-T items |
| Duration | 2,983.2s | At least 15% below the 3,175s baseline |
| Cost | $12.1531 | No higher than the $9.7311 baseline |

Any grader regression rejects the variant regardless of speed. A small duration improvement from a single run is directional only; two successful runs are still required before a merge recommendation.

### Result — GitHub Actions 29596260683

The unchanged Golden Expense task ran on `a83cb1eae` with `claude-sonnet-4-6` in one iteration. It completed in 2,007.4 seconds (33m27s) at $7.4434, but scored `0.500`; this rejects the experiment regardless of the apparent performance improvement.

| Metric | Baseline | Follow-up run | Change |
|---|---:|---:|---:|
| Deterministic score | 1.000 | 0.500 | rejected |
| Duration | 3,175.0s (52m55s) | 2,007.4s (33m27s) | -1,167.6s (-36.8%) |
| Cost | $9.7311 | $7.4434 | -$2.2877 (-23.5%) |
| Output tokens | 217,198 | 125,065 | -92,133 (-42.4%) |
| Cache-read tokens | 13,932,735 | 12,108,691 | -1,824,044 (-13.1%) |
| Cache-creation tokens | 578,104 | 499,853 | -78,251 (-13.5%) |
| Uncached input tokens | 41,813 | 20,135 | -21,678 (-51.8%) |
| Agent turns | 194 | 222 | +28 (+14.4%) |
| Tool calls | 190 | 164 | -26 (-13.7%) |

The generated caseplan did validate and passed the topology and seed-object checks. It failed two required deterministic checks:

- **Connector binding fidelity:** the generated Outlook activity contained the literal placeholder `list-email-activity-type-id`, not the real `5b154ea8-15bb-30a6-b07d-74a8cd1c1688` identifier. The agent had already stored the correct populated `C02.Data.CaseShape` in `tasks/schema-cache.json`, so this was a cache-consumption failure rather than unavailable tenant metadata.
- **Stage-exit semantics:** Stage 1's `required-tasks-completed` condition omitted explicit `type: "exit-only"`. CLI validation accepts the omission, but the semantic checker correctly requires the SDD-derived exit type.

The transcript also shows that the result is **not a valid measurement of the intended mechanism**:

- It made 23 `tasks describe` and 8 `case spec` invocations, missing the targets of at most 6 and 2. The cache was written, but repeated exploratory and implementation fetches continued.
- It made one populated whole-file `caseplan.json` Write followed by seven Edits. The initial Write was not the required T01 root scaffold, so it bypassed the planned Phase 2 stage-array construction.
- It did avoid task-ledger calls, but that improvement cannot compensate for the failed accuracy contract.

Next corrective action before a rerun: make cached connector `CaseShape` consumption mechanically explicit in the activity recipe and require a pre-validation comparison of the cached `UiPathActivityTypeId` and every SDD-declared exit `type` against the composed caseplan. Re-run only after those fidelity fixes pass local skill validation; require two score-1.0 runs before considering a PR.

## Recommended Next Experiments

Run each experiment independently against the same task, model, grader, and tenant inputs.

### 1. Coarser bounded batches

Keep the one-Write rule, but target approximately 8–15 caseplan Edits instead of 52:

- one stage-node batch
- one task-array Edit per stage
- one I/O binding batch per stage or task group
- one condition batch per scope/target group
- one SLA batch per target

Cap payload size, but do not force per-task or per-condition Edits when one stable target can safely hold the complete section.

### 2. Gather each schema once

Fetch the full schema once per unique resolved resource or connector need and retain the complete response:

- six unique non-connector resource schemas, not 19 `tasks describe` calls
- two unique connector schemas, not four `case spec` calls

Do not make an initial summary-only lookup that later requires a second full-detail lookup.

### 3. Reduce progress and narration turns

The instruction-only prohibition on standalone narration was not followed reliably. Add an eval-side behavioral measurement for:

- standalone text turns between tool calls
- task-ledger call count
- duplicate schema calls
- total caseplan mutation calls

Use those as diagnostics first; avoid making them hard correctness gates until stable thresholds are established.

### 4. Measure before merging

For every follow-up variant, record:

- deterministic score and failed criteria
- duration and cost
- uncached, cache-created, cache-read, and output tokens
- number and size of caseplan Writes/Edits
- failed Edit count
- schema lookup count by unique resource
- task-ledger and standalone narration turn counts

Require at least two successful runs before treating a small duration change as meaningful.

## Infrastructure Note

The first workflow experienced five setup-only failures before any agent execution: four attempts in run 29539778252 and attempt 1 in run 29541608582. In each case, `astral-sh/setup-uv@v4` received GitHub's “Unicorn” HTML error page. Attempt 2 of run 29541608582 cleared setup and produced the successful result above. These failures are unrelated to the skill change and are excluded from the performance comparison.
