---
confidence: medium
---

# Serverless Automation Cannot Be Started — License / Quota Exceeded

## Context

A **serverless** (cloud robot, `RuntimeType` Serverless / `runtimetype = 9`) job fails to start with one of:

```
Automation cannot be started. Your user's monthly Personal Automation quota has been exceeded.
Automation cannot be started. Your user's assigned Robot Units have been exceeded.
Automation cannot be started. Your tenant's assigned Robot Units have been exceeded. Allocate more Robot Units to your tenant to continue.
```

What this looks like:
- The automation never starts — it is rejected at allocation time, not faulted mid-run. There is **no Windows session, executor, logon, or workflow** involved.
- The message names a **quota / Robot Units** limit at **user** or **tenant** scope.

What causes it (this is a licensing/allocation state, NOT a code/config/robot bug):
- **Personal Automation monthly quota exceeded** — the user's free monthly Personal Automation run allowance is used up for the period.
- **User's Robot Units exceeded** — the serverless capacity **assigned to that user** is exhausted by concurrent/accumulated runs.
- **Tenant's Robot Units exceeded** — the **tenant-level** serverless Robot Unit pool is exhausted; every user in the tenant is affected until more units are allocated.

What to look for:
- **`RuntimeType` = Serverless / `runtimetype = 9`** on the job — confirms this is the serverless surface, not unattended.
- The **scope word** in the message — `user's ... Personal Automation quota` vs `user's ... Robot Units` vs `tenant's ... Robot Units` selects the branch and where the fix is applied.

## Investigation

1. **Get the job:** `uip or jobs get <job-key> --output json` → confirm the quota/Robot-Units message and `RuntimeType` Serverless / `runtimetype = 9`.
2. **Read the scope from the message** — user Personal Automation quota, user Robot Units, or tenant Robot Units.
3. **Check current licensing/allocation state** — tenant Robot Unit allocation and the user's assignment (Automation Cloud → Admin → Licenses / tenant licensing; the specific figures may not be exposed via `uip`). Rule out that this is an infrastructure fault — the message is explicit about quota.

## Resolution

- **Tenant Robot Units exceeded:** allocate more Robot Units to the tenant (Automation Cloud → Admin → tenant → Licenses), or reduce concurrent serverless usage until the pool frees up.
- **User Robot Units exceeded:** raise the user's assigned Robot Units, or spread the workload / reduce concurrency for that user.
- **Personal Automation monthly quota exceeded:** wait for the monthly quota to reset, move the workload to a licensed serverless/unattended allocation, or upgrade the plan — Personal Automation is a capped free tier, not a production allocation.
- This is **not** fixed by rerunning, updating the robot, or fixing credentials — it is a licensing/allocation limit. Rerunning before units free up (or the quota resets) just re-hits the limit.
