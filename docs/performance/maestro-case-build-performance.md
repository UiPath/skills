# Maestro Case Build Performance Investigation

## Status

- **Outcome:** Experiment concluded; accuracy passed, but the efficiency trade-off did not justify merging.
- **Decision:** Close the draft PR and retain this document as the experiment record.
- **Date:** 2026-07-16 (Pacific time)
- **Scope:** `uipath-maestro-case` Golden Expense end-to-end build

## Links

- Draft experiment PR: [UiPath/skills#2098](https://github.com/UiPath/skills/pull/2098)
- Experiment branch: `experiment/maestro-case-llm-build-speed`
- Experiment commit after rebasing onto `main`: `bb0b18340be56979df9824a67a62109a67e449b9`
- Baseline report: [Golden Expense baseline](https://coder-evalboard.uipath-dev.com/runs/2026-07-16_04-24-15/skill-case-golden-rebuild-cm-expense)
- Successful experiment run: [GitHub Actions 29541608582](https://github.com/UiPath/skills/actions/runs/29541608582), attempt 2
- Earlier infrastructure-only failures: [GitHub Actions 29539778252](https://github.com/UiPath/skills/actions/runs/29539778252)

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
