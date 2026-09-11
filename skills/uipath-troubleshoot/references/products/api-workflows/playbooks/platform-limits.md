---
confidence: medium
---

# API Workflow Stopped by a Platform Ceiling, Not by Its Own Logic

## Context

What this looks like:
- The run ends without an exception that explains the ending: no thrown activity, no `Response` with `markJobAsFailed: true`, nothing in the category ladder (Structure > Expression > Activity Config > Logic) that accounts for it
- It is **input-dependent**: the same workflow succeeds on a small payload and stops on a large one, or succeeded for months and started stopping as upstream data grew
- Re-running with the same input reproduces it at roughly the same point

These are ceilings the platform imposes on any API workflow. None of them is a defect in the workflow JSON, so none is reachable by `validate`, and the fix is never a JSON repair.

| Ceiling | Value | Scope | Discriminator |
|---|---|---|---|
| **Script activity execution** | **30 seconds** of JavaScript execution | One `Script` activity | The run stops inside a Script activity; a smaller input completes. Documented on the Script activity page |
| **Do While iterations** | The activity's own `Limit` property | One `Do While` loop | The loop exits at exactly `Limit` iterations. Commonly hit by an HTTP pagination loop whose page count grew past the guard |
| **Serverless job execution** | **15 minutes** per job | The whole job | `EndTime − StartTime` ≈ 15 min and the job reached `Running`. → Orchestrator `serverless-time-limit-exceeded.md` |
| **Robot Units / Personal Automation quota** | Tenant or user allocation | Job never starts | Near-zero runtime, job rejected at allocation. → Orchestrator `serverless-license-quota.md` |

The last two are Orchestrator-owned and already have playbooks — API workflows inherit them because they run on serverless infrastructure. Route there rather than re-diagnosing here.

**Undocumented behaviour — do not assume.** UiPath's docs state that the Script timeout is 30 seconds and that `Do While` takes a `Limit`, but they do **not** document the user-facing error string for the Script timeout, nor whether reaching `Limit` faults the run or exits the loop silently. Per SKILL.md invariant 9, determine both empirically from the run output and record what you observed; do not grep for, quote, or infer a message the docs do not define.

What to look for:
- **Which activity the run stopped at**, from the per-activity output. A Script activity that is the last thing to produce output, with no error attributable to its code, points at the timeout
- **Whether the loop's iteration count equals its `Limit` exactly.** An exact match is the signature; one short of it is not
- **Total run duration.** ≈15 minutes is the serverless ceiling, not anything in the workflow
- **Payload size trend.** A ceiling fault correlates with input volume; a logic fault usually does not

## Investigation

1. Reproduce locally with the input that fails: `uip api-workflow run <Workflow.json> --no-auth --output json`. The Script 30-second cap and the `Do While` `Limit` are properties of the workflow, so both reproduce locally. The serverless 15-minute ceiling and the quota rejection are cloud-only and will **not** reproduce — that split is itself diagnostic.
2. Identify the last activity to produce output, and whether the run stopped inside it or after it. Do not rely on the envelope status; read the per-activity results.
3. **Suspected Script timeout:** time the activity. Re-run with a deliberately smaller input; if it completes and the large input does not, the cap is the cause. Confirm the Script is doing work proportional to input size (a loop over records, a large parse) and not blocked on something it cannot do at all — a `Script` **cannot make outbound API calls**, which is a different fault with a different fix (move the call to an HTTP activity).
4. **Suspected `Do While` limit:** read the loop's `Limit` from the workflow JSON and count the iterations actually performed in the run output. Equal → the guard fired.
5. **Cloud-only stop:** get the job and compute the duration: `uip or jobs get <job-key> --output json`. ≈15 min with the job having reached `Running` → Orchestrator `serverless-time-limit-exceeded.md`. Near-zero runtime with an allocation-time rejection → Orchestrator `serverless-license-quota.md`.
6. Before concluding a ceiling, rule out an ordinary fault at the same point: `uip or jobs logs <job-key> --output json`. A ceiling verdict is only admissible once you have shown nothing in the logs explains the stop on its own.

## Resolution

- **If the Script 30-second cap:** move the work out of one Script activity. Split the transform across several Scripts, push per-item work into a `For Each` body so each invocation is small, or reduce what reaches the Script (filter or page upstream). Raising the cap is not an option — it is a platform limit.
- **If a Script is blocked on an outbound call:** replace it with an `HTTP` or Connector activity. Script runs only against existing workflow data.
- **If the `Do While` `Limit` fired:** decide which of the two is true before editing. Either the limit is genuinely too low for current data volume — raise it, or make it a dynamic expression over the real page count — or the loop is not terminating and the guard is doing its job, in which case fix the exit condition. Raising a limit that is masking a non-terminating loop converts a fast failure into a 15-minute one.
- **If the serverless 15-minute ceiling:** → Orchestrator `serverless-time-limit-exceeded.md`. For an API workflow specifically, the usual fix is to batch: cap the records processed per run and let the trigger fire more often, rather than one long run.
- **If Robot Units / quota:** → Orchestrator `serverless-license-quota.md`. Tenant-level allocation, recommendation-only — no workflow change applies.
