---
confidence: medium
---

# Action App: Form Data Not Loading

## Context

Applies to coded **action** apps (Action Center form apps built with `@uipath/coded-action-app`), not web apps.

What this looks like:
- The action app renders but the form is blank — fields that should be pre-filled from the task stay empty
- `codedActionAppService.getTask()` resolves to `null`/`undefined`, or rejects, and the app has no visible error
- Console may show an error thrown from `@uipath/coded-action-app` `getTask`, or nothing at all (silent failure — soft signature)

What can cause it:
- `getTask()` failed and the app swallowed it — no `.catch()` / error handling, so the empty form is the only symptom
- The app was opened **outside an Action Center context** (directly by URL) — `getTask()` requires the Action Center host that injects the task context
- The `@uipath/coded-action-app` package is missing from the app
- The app was published as type `Web` instead of `Action` (`uip codedapp publish -t Action`), so it is not wired into Action Center

What to look for:
- Whether `getTask()` has error handling at all — an unlogged rejection presents identically to "no data"
- Whether the app is being opened from an Action Center task assignment vs. directly
- Whether the package is installed and the app was published as `Action`

## Investigation

1. Confirm error handling exists on the task load. If the code calls `getTask()` without a `.catch`, add logging to surface the real error:

   ```typescript
   codedActionAppService.getTask()
     .then((task) => { console.log('Task loaded:', task); if (task?.data) setFormData(task.data as FormData); })
     .catch((err) => console.error('getTask failed:', err));
   ```

   Read the console output — the thrown error usually names the cause directly.

2. Confirm the app is opened from an Action Center task (an assigned action item), not by pasting the app URL. `getTask()` returns no task without the Action Center context.

3. Confirm the package is installed:

   ```bash
   grep -n "@uipath/coded-action-app" package.json
   ```

4. Confirm the app was published as an Action app (not Web) — an action app published as `Web` never receives a task context. Re-publish with `-t Action` if wrong (see Resolution).

## Resolution

- **If `getTask()` fails silently:** add the `.catch` + logging above so the error is visible, then fix the underlying cause it reports.

- **If opened outside Action Center:** open the app from its Action Center task assignment. Direct-URL access cannot supply a task.

- **If the package is missing:** install it, then rebuild and republish:

  ```bash
  npm install @uipath/coded-action-app --@uipath:registry=https://registry.npmjs.org
  ```

- **If published as the wrong type:** republish and deploy as an action app:

  ```bash
  uip codedapp publish -t Action
  uip codedapp deploy
  ```
