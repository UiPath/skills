---
confidence: medium
---

# Maximum Consecutive System Exceptions Reached

## Context

A job (typically REFramework or any retry-looping process) aborts after hitting its consecutive-System-Exception ceiling. **The message is a symptom, not the root cause** — the real fault is the underlying System Exception that recurs on every transaction until the threshold trips.

What this looks like:
- `The maximum number of consecutive system exceptions was reached. Consecutive retry number: <N>`
- Job Faulted after processing 0 (or very few) transactions successfully
- The SAME underlying exception appears N times in the logs just before the abort line
- Common in REFramework processes where a system-level dependency is broken

What can cause it (the underlying recurring exception):
- A broken selector / UI change — `SelectorNotFoundException` on the same activity every transaction
- An application that fails to launch or is not in the expected state
- A down/unreachable dependency (database, API, network share, Orchestrator asset/queue)
- Credential/permission failure repeated per transaction

The threshold itself (`MaxConsecutiveSystemExceptions` in REFramework `Config.xlsx` / an asset) only decides *how many* failures before giving up — it does not cause the failure.

## Investigation

1. Get the failing job and confirm the abort signature:
   `uip or jobs get <job-key> --output json` — `Info` = "maximum number of consecutive system exceptions was reached".
2. **Find the underlying recurring exception** — this is the real target:
   `uip or jobs logs <job-key> --level Error --output json` — look at the errors BEFORE the "max consecutive" line. The same System Exception (type + activity) repeated N times is the root cause.
3. Confirm the repeated failing activity in traces:
   `uip or jobs traces <job-key> --output json` — the same activity Faulted across consecutive transactions.
4. Classify it: is the recurring error a **System** exception (environment/UI/dependency — retried and counted) or a mis-classified **Business** exception? Business rule violations should be thrown as `BusinessRuleException` so they do not consume the system-exception budget.

## Resolution

- **Fix the underlying recurring System Exception** — that is the root cause. Examples:
  - Broken selector → re-indicate the element / use Object Repository / add a reliable anchor; add `Check State` before the action.
  - App not in expected state → fix the init/launch sequence; add `Activate`/wait-for-ready.
  - Down dependency → restore/repoint the database/API/share; verify the asset/credential.
- **Do NOT just raise `MaxConsecutiveSystemExceptions`** — a higher threshold only delays the same abort while burning more attempts. Raise it only after the underlying fault is fixed and you have a legitimate reason to tolerate more transient failures.
- **Re-classify mis-typed exceptions** — throw genuine business-rule violations as `BusinessRuleException` so they route to the business-exception path instead of the system-exception counter.
- **Rerun** after fixing the underlying exception.

Prevention:
- Treat "max consecutive system exceptions" as an alert to investigate the *first* recurring exception, not as the fault itself.
- Keep System vs Business exception classification correct so the counter reflects real environmental failures.
