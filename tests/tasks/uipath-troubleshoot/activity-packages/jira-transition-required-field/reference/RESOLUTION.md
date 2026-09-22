# Final Resolution

---

**Root Cause:** The `Done` transition has a transition **screen** that makes
`Resolution` a mandatory field, but the `Transition Issue` activity moves the
issue to `Done` without supplying any field values. Jira rejects the call with
`400 (Bad Request)` and a body of `{"errors":{"resolution":"Field 'resolution'
is required"}}`.

**What went wrong:** The `JiraTicketCloser` job (started 2026-06-16T15:40:02Z)
authenticated and opened the Jira session (Trace log: "session opened"), then
faulted on `Transition Issue` moving `OPS-1530` to `Done` (Trace: "transitioning
issue OPS-1530 to 'Done'"). The error is `400 (Bad Request).
{"errors":{"resolution":"Field 'resolution' is required"}}`. The transition
itself is valid (it was found and attempted); Jira rejected it because the
mandatory `Resolution` field on the transition screen was not provided.

**Why:** This is sub-case **T1** of the transition-issue playbook. In Jira, a
transition can have a screen that requires fields (`Resolution`, `Fix Version/s`,
`Assignee`). The Jira UI prompts for them — which is why "closing by hand works"
(the human fills in the resolution box) — but `Transition Issue` only changes the
status and sends no field values unless you provide them, so the mandatory field
is missing and the API call is rejected. This is not an invalid transition ID
(the error names a required field, not "transition is not valid"), not a
permission/validator denial, and not a deserialization bug.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraTicketCloser -- Faulted at 2026-06-16T15:40:03.860Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Service Desk (key `5a05a2b3-d4e5-4f60-8a05-000000000005`)
- Final error: `Transition Issue: ... 400 (Bad Request). {"errors":{"resolution":"Field 'resolution' is required"}}` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `TransitionIssue "Transition Issue"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the fault is on `Transition Issue`, not at scope open — auth ruled out.
- `Main.xaml` sets `TransitionIssue` with `IssueKey="OPS-1530"` and `TransitionName="Done"` and supplies **no field values**.
- The `400` body names the missing field explicitly: `"resolution":"Field 'resolution' is required"` — the `Done` transition screen requires `Resolution`. This is the **T1** signature.

---

**Immediate fix:**

Supply the required transition-screen field(s) when transitioning to `Done`.

### Fix path A -- discover and set the field on the transition
Call `Get Transitions` for the issue to see which fields the `Done` transition's
screen requires (`resolution` here), then pass that field/value on the
`Transition Issue` call (e.g. set `Resolution = "Done"`).

### Fix path B -- set the field with Update Issue first
Use `Update Issue` to set `Resolution` on `OPS-1530` immediately before
`Transition Issue`, then run the transition.

### Verification (hand to the user - off-host)
- Run `Get Transitions` for `OPS-1530` and confirm the `Done` transition lists
  `resolution` as a required field; supply it and re-run.

- **Source:** `jira-activities/playbooks/jira-transition-issue-failures.md` (T1)

---

**Preventive fix:**

1. **Discover required fields before transitioning** -- for any transition to a
   screen state (Done/Resolved), call `Get Transitions` and supply every
   required field, or set them with `Update Issue` first.
   - **Why:** transition screens can make fields mandatory; the UI prompts for
     them but `Transition Issue` does not send them unless you provide them.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Done transition screen requires Resolution; Transition Issue supplies no fields (T1) | High | Confirmed | Yes | `400 {"errors":{"resolution":"Field 'resolution' is required"}}`; TransitionIssue to "Done" with no field values; manual close prompts for a resolution | Supply the required field via Get Transitions, or Update Issue before the transition |
| H2 | Invalid / outdated transition ID (T2) | Low | Rejected | No | Error names a required field, not "transition is not valid"; the transition was found and attempted | -- |
| H3 | Workflow Condition/Validator or permission (T3) | Low | Rejected | No | The rejection is a field-validation error, not a rule/permission denial | -- |

---

Would you like the exact `Get Transitions` + field-set pattern (or the `Update
Issue` step) to add before `Transition Issue`, or help cleaning up the
`.local/investigations/` folder?
