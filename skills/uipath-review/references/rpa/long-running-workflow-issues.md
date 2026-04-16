# Long-Running Workflow / Persistence Issues

Antipatterns specific to UiPath Orchestration Processes (long-running workflows with persistence bookmarks) and any XAML that uses `Suspend`, `Wait and Resume`, `Create Form Task`, `Wait for Form Task and Resume`, or similar persistence activities.

> Applies when `project.json` has `"projectType": "Orchestration"` OR any workflow file uses persistence activities.

## Persistence Activities Outside Main.xaml

**Symptom:** `Wait for Form Task and Resume`, `Create Form Task`, `Wait for External Event`, or `Suspend` activities placed in invoked sub-workflows (`Process.xaml`, etc.) instead of the Main.xaml entry point.

**Impact:** Runtime failure with `"An extension of type IPersistenceBookmarks must be configured"`. Persistence bookmarks only work from the Orchestration Process entry point.

**Detection:** Grep all `.xaml` files for `WaitForFormTaskAndResume`, `CreateFormTask`, `WaitForExternalEvent`, `Suspend`. If found in any file other than the entry point, flag.

**Fix:** Move persistence activities to Main.xaml. Invoke sub-workflows between persistence points — sub-workflows should return control to Main before the next `Wait`.

**Severity:** Critical

## Delay or Retry Scope in Orchestration Process Main.xaml

**Symptom:** `Delay` or `Retry Scope` activities placed directly in Main.xaml of an Orchestration Process, NOT wrapped in a `No Persist Scope`.

**Impact:** `Delay` causes the workflow to suspend but Orchestrator cannot resume it (no persistence bookmark). `Retry Scope` behaves unpredictably — the workflow suspends instead of retrying, requiring manual resumption per attempt. Long-standing bug (~5 years).

**Detection:** If `project.json` has `"projectType": "Orchestration"`, grep Main.xaml for `RetryScope` or `Delay` that are not inside a `NoPersistScope`.

**Fix:** Wrap `Delay` and `Retry Scope` inside `No Persist Scope`. For retries that span suspend boundaries, rearchitect to loop at the workflow level with state stored in variables.

**Severity:** Critical

## Persistence Activity Inside For Each Loop

**Symptom:** `Wait for Form Task and Resume` (or any `Wait*AndResume` activity) inside a `For Each` / `For Each Row` loop body.

**Impact:** Workflow suspends after the first iteration and never processes subsequent items. The persistence mechanism serializes state after the first loop body execution, effectively turning a multi-item loop into a single-item processor.

**Detection:** In Orchestration Process projects, check if any `Wait*AndResume` activity is nested inside `ForEach` or `ForEachRow`.

**Fix:** Redesign so the loop runs over pre-generated task IDs and waits for task completion OUTSIDE the loop, or use a dispatcher-performer pattern with one queue item per sub-task.

**Severity:** Critical

## Non-Serializable Variables Across Suspend Boundaries

**Symptom:** Variables of non-serializable types (freshly-instantiated `new System.Data.DataTable()`, custom classes without `[Serializable]`, `IWebDriver`, `BrowserScope` references, stream handles) in scope when a persistence activity executes.

**Impact:** Runtime crash during suspend: the workflow state cannot be serialized to storage.

**Detection:** Run Workflow Analyzer rules `ST-DBP-025` (variables) and `ST-DBP-028` (arguments). For coded workflows, check variables in scope of `WaitFor*` calls for serializable types. Serializable-safe types: Text, Boolean, Number, Array of primitives, DateTime, DataTable loaded via Read Range (not `new DataTable()`), GenericValue.

**Fix:** Replace non-serializable types with serializable alternatives or marshal data to strings/JSON before suspend. Close browser/file handles before suspend; re-open after resume.

**Severity:** Critical

## Retry Scope Wrapping Persistence Activities Without No Persist Scope

**Symptom:** `Retry Scope` wrapping a `Delay`, `Wait*AndResume`, or any persistence-aware activity without a `No Persist Scope` guard inside.

**Impact:** Retry Scope interacts destructively with persistence. Each retry attempt triggers a suspend, which Orchestrator treats as the workflow's final state rather than as a retry step. Manual resumption required per attempt.

**Detection:** Grep XAML for `RetryScope` activities; inspect whether they contain persistence activities and whether a `NoPersistScope` is present inside.

**Fix:** Wrap the activity inside `NoPersistScope` within the Retry Scope, OR rearchitect to retry at the workflow level rather than via Retry Scope.

**Severity:** Warning

## Action Center Tasks Without Deadlines

**Symptom:** `Create Form Task` or `Create Action Task` activities with no deadline configured.

**Impact:** Task sits in Action Center forever if assignee is unavailable (vacation, disabled account, left company). Workflow consumes persistence storage indefinitely with no escalation.

**Detection:** Check `Create*Task` activities for `DeadlineValue` / `DeadlineUnit` properties. Flag if unset or absent.

**Fix:** Set deadline (hours/days). Configure escalation policy (reassign to manager after N hours) or timeout handling (auto-reject after X days).

**Severity:** Warning

## Human Tasks Assigned to Disabled or Unknown Users

**Symptom:** `Create Form Task` with `Assignee` pointing to a specific user account, rather than a role or group.

**Impact:** When the user is disabled (left company, rotation), tasks pile up in their queue with no one to action them. Business process blocked until someone manually reassigns.

**Detection:** Check `Create*Task` activities for hardcoded user emails/accounts in `Assignee`. Prefer role-based or group-based assignment.

**Fix:** Assign to a role, group, or shared queue. If individual assignment is required, configure reassignment rules on deadline breach.

**Severity:** Warning

## Suspend Without Timeout Handling

**Symptom:** `Wait for External Event` or similar suspend points with no timeout configured and no timer boundary to force completion.

**Impact:** Workflow can remain suspended indefinitely if the expected event never arrives. Consumes storage, prevents job completion metrics, blocks downstream processes waiting on this workflow.

**Detection:** Check `Wait*` activities for `Timeout` property. Flag if unset.

**Fix:** Set a timeout aligned with the process SLA. Handle timeout expiration with an explicit error path or escalation.

**Severity:** Warning
