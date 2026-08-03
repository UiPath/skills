---
confidence: medium
---

# Transition Issue — Transition Fails Or Is Rejected

## Context

What this looks like:
- A `Transition Issue` activity faults when moving a Jira ticket to a new status (e.g. to `Done` / `Resolved` / `In Progress`). Common shapes:
  - `Transition '<id>' is not valid for the current status of issue <KEY>` (or HTTP `400`).
  - `Field '<name>' is required` / a `400` whose body lists required fields.
  - The transition button works for some users but the robot's call is rejected.
  - `Error converting value '...' to type 'Atlassian.Jira.IssueFieldEditMetadataOperation'`.
- The same transition often "works when I click it in the browser" — because the UI supplies screen fields, runs as a different user, or the package builds the request differently.

What can cause it (four sub-cases):
- **T1 — required field on the transition screen not supplied.** The target transition (e.g. → `Done`) has a screen that makes fields mandatory (`Resolution`, `Fix Version/s`, `Assignee`). `Transition Issue` moves the status without those values, so Jira rejects the call with a `Field '<name>' is required` / `400`.
- **T2 — invalid / outdated transition ID.** A static transition ID was hardcoded in the activity (e.g. `31`), but the ticket's **current** status has no legal transition with that ID. Transition IDs are per-status edges, not global constants — the same target reached from a different starting status has a different ID. Jira rejects with `Transition '<id>' is not valid ...`.
- **T3 — workflow Condition / Validator (rule or permission) blocks it.** The Jira admin attached a **Condition** or **Validator** to the workflow (only the assignee may close; a worklog must exist; a specific resolution must be set), or the robot account lacks the project-level permission to perform the transition. Jira rejects even with a valid ID and all fields supplied.
- **T4 — deserialization / package-version type mismatch.** `Error converting value '...' to type 'Atlassian.Jira.IssueFieldEditMetadataOperation'`. A known JSON metadata-parsing bug in **older** `UiPath.Jira.Activities` releases when handling complex transition-screen fields (attachments, radio/option lists). The transition metadata round-trip fails to deserialize before the call even completes.

What to look for:
- The exact error: `is not valid` (T2) vs `is required` (T1) vs a permission/rule rejection (T3) vs `Error converting value ... IssueFieldEditMetadataOperation` (T4).
- In the `.xaml`: whether `Transition Issue` uses a **hardcoded** `TransitionId` literal vs a value pulled from `Get Transitions` at runtime, and whether any screen fields are being set before the transition.
- The `UiPath.Jira.Activities` version in `project.json` (T4 is version-bound).

## Investigation

1. Read the error from job evidence and classify it: `is not valid` → T2; `is required` / `400` listing fields → T1; rule/permission rejection with a valid request → T3; `Error converting value ... IssueFieldEditMetadataOperation` → T4.
2. Read the `Transition Issue` configuration in the `.xaml`: is `TransitionId` a hardcoded literal (e.g. `"31"`), or resolved from a `Get Transitions` result? Are any fields supplied with the transition?
3. For T1 / T2: confirm whether the workflow uses `Get Transitions` to discover the legal transitions (and their required fields) for the issue's **current** status before transitioning. A hardcoded ID with no `Get Transitions` is the T2 signature; a transition to a screen state with no field values is the T1 signature.
4. For T4: read the `UiPath.Jira.Activities` version from `project.json`; an older release plus the `IssueFieldEditMetadataOperation` conversion error is the signature.
5. For T3: the decisive proof is off-host — reproduce the exact transition manually in the Jira UI **as the robot's service account**.

## Resolution

- **T1 — supply the required fields:** call `Get Transitions` for the issue to see which fields the target transition's screen requires, then either set them on the transition call or set them with `Update Issue` immediately before `Transition Issue` (e.g. set `Resolution` before moving to `Done`).
- **T2 — resolve the transition ID dynamically:** never hardcode a transition ID. Call `Get Transitions` for the issue at runtime, loop the returned transitions, match the one whose `name` is your target status (e.g. `In Progress`), and pass its runtime `.Id` into `Transition Issue`. This survives different starting statuses.
- **T3 — fix the rule or the permission:** reproduce the transition in the Jira UI as the robot's **service account**. If the button is greyed out or errors, the account lacks the project-level workflow/transition permission, or a Condition/Validator blocks it — have the Jira admin grant the permission or adjust the rule (or satisfy the validator, e.g. assign the ticket / add the worklog, before transitioning).
- **T4 — upgrade the package:** upgrade `UiPath.Jira.Activities` (Manage Packages) to the latest stable release; the `IssueFieldEditMetadataOperation` conversion bug is fixed in newer versions. If the project is cloud-targeted, prefer migrating the Jira calls to the **Integration Service** Jira connector activities, which use standard REST structures and are not subject to this legacy deserialization path.

### Verification (hand to the user — off-host)
- Run `Get Transitions` for the issue and confirm the target transition's ID and required fields against what the activity sends.
- For T3, attempt the transition manually as the service account in the Jira UI.

This is medium-confidence: T1, T2, and T4 are each clearly signalled by the error string plus the activity / package configuration. T3 is confirmed only by reproducing the transition as the service account, so treat a rule/permission cause as a hypothesis to confirm off-host rather than a finished diagnosis.
