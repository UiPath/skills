---
confidence: medium
---

# API Workflow Stopped by a Platform Limit, Not by Its Own Logic

## Context

What this looks like:
- The run ends and nothing explains why it ended: no activity threw, no `Response` set `markJobAsFailed: true`, and nothing in the category ladder (Structure > Expression > Activity Config > Logic) accounts for it
- It depends on the size of the input: a small payload succeeds, a large one stops. Or it worked for months and started stopping as the upstream data grew
- Running it again with the same input stops in roughly the same place

These limits come from the platform, not from the workflow file. `validate` will never catch one, and editing the JSON will never fix one.

| Limit | Value | Applies to | How you recognise it |
|---|---|---|---|
| **Script run time** | **10 seconds** per Script task (`evaluateScript(code, taskName, 1e4)`). Executor builds since 2026-07 allow 100 s if the code uses `$helpers` | One `Script` activity | The failing activity's error title is `Script execution failed timed out` |
| **Loop iterations** | The loop's `limit`, capped at `MAX_ITERATIONS = 10000`. No `limit`, or a non-numeric one, also means 10000 | One `Do While` or `While` loop | A **Warning** in the log: `DoWhileTask '<taskName>' reached iteration limit (<limit>)`, or `WhileTask` for a while loop. **The run does not fail** |
| **Serverless job run time** | 15 minutes per job | The whole job | The job record says `RuntimeType` Serverless, the job reached `Running`, and `EndTime − StartTime` is about 15 min → Orchestrator `serverless-time-limit-exceeded.md` |
| **Allocation quota** | Tenant or user allocation | Jobs that never start | Almost no runtime, plus a Robot Units or Personal Automation quota message on the job record → Orchestrator `serverless-license-quota.md` |

**Scripts get 10 seconds, not the 30 the docs say.** The Script activity page documents a 30-second timeout. That number is real, but it belongs to `executeScriptLocal` in `@uipath/api-workflow-commons`, which Script activities don't go through. They all go through the executor's `DefaultScriptTaskHandler`, which allows 10 seconds — confirmed in the shipped `@uipath/api-workflow-tool` 1.201.0 and in `UiPath/API-Workflow` `main`. The same handler runs in the Studio Web designer, in `uip api-workflow run`, and in the cloud runtime, and none of them replaces it. So match on the error, not on a stopwatch.

**A loop that hits its limit stops quietly.** It does not fail. The loop breaks, returns the last iteration's result as a success, and writes one Warning. The workflow then carries on with whatever that last iteration produced — so the user sees wrong or partial output with no error anywhere, which is a different thing to look for than a fault.

The last two rows belong to Orchestrator and already have playbooks — send them there instead of diagnosing them here. Both depend on `RuntimeType` on the job record, so read it from `uip or jobs get` rather than assuming the job ran as serverless.

API workflows are billed in **Integration Activities**, separately from all of this — 1 for starting the job, 1 per HTTP Request, 1 per successful connector call, and nothing for Script or control flow ([licensing](https://docs.uipath.com/studio-web/automation-cloud/latest/user-guide/api-workflows-licensing)). Running out of allowance is a licensing problem, and it looks like neither limit above.

**A `Script` cannot call an API.** The sandbox replaces `fetch` with something that throws, so you get `fetch is not allowed in scripts`. That is a different problem with a different fix — move the call to an HTTP or Connector activity — not a limit.

## Investigation

1. Reproduce it locally with the input that fails: `uip api-workflow run <Workflow.json> --no-auth --output json`. The Script budget and the loop limit are enforced by the executor, so both reproduce locally. The 15-minute ceiling and the quota rejection only happen in the cloud and won't — that difference alone tells you which half you are in.
2. Find the last activity that produced output, and whether the run stopped inside it or after it. Read the per-activity results; don't go by the overall status.
3. **If you suspect the Script timeout:** check the error title is `Script execution failed timed out`. It is translated, so match on its shape if the run isn't in English. Then re-run with a deliberately smaller input — if the small one finishes and the large one doesn't, the time limit is your answer.
4. **If you suspect a loop limit:** search the logs for the warning — `uip or jobs logs <JOB_KEY> --level Warning --output json`. `reached iteration limit` is the only signal you get; the run reports success either way. Then read the loop's `limit` in the workflow file (no `limit` means the implicit 10000).
5. **If it only fails in the cloud:** `uip or jobs get <JOB_KEY> --output json`, then read `RuntimeType` and work out `EndTime − StartTime`.
6. Before you settle on a platform limit, rule out an ordinary failure in the same place: `uip or jobs logs <JOB_KEY> --level Error --output json`. Only call it a limit once you have looked and found nothing in the logs that explains the stop by itself.

## Resolution

- **Script ran out of time:** move work out of that one Script — split it across several, push per-item work into a `For Each` body so each run is small, or filter and page upstream so less data reaches it. The limit cannot be changed from the workflow.
- **Script is trying to call an API:** replace it with an `HTTP` or Connector activity. Script only works on data the workflow already has.
- **Loop hit its limit:** work out which of two things is true before you edit anything. Either the limit is genuinely too low for the current volume — raise it, or make it an expression based on the real page count — or the loop isn't terminating and the guard is doing its job, in which case fix the exit condition. Raising a limit that is hiding a runaway loop turns a quick, quiet truncation into a 15-minute one.
- **15-minute serverless ceiling:** → Orchestrator `serverless-time-limit-exceeded.md`. For an API workflow the usual answer is to work in batches — cap how many records each run handles and let the trigger fire more often.
- **Allocation quota:** → Orchestrator `serverless-license-quota.md`. This is set at tenant level; recommend it, and expect no workflow change to help.
