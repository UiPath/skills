# Final Resolution

---

**Root Cause:** The `Transition Issue` activity has a **hardcoded**
`TransitionId="31"`, but the target issue's **current** status has no legal
transition with that ID. Jira transition IDs are per-status edges, not global
constants — the ID that moved a ticket from one status does not exist from a
different starting status. The workflow never calls `Get Transitions` to resolve
the correct ID for the issue's current status, so Jira rejects the call with
`400 (Bad Request): Transition id '31' is not valid for issue OPS-1421 in its
current status`.

**What went wrong:** The `JiraStatusUpdater` job (started 2026-06-16T13:05:02Z)
authenticated and opened the Jira session (Trace log: "session opened"), then
faulted on `Transition Issue` with `[Transition Issue] Response status code does
not indicate success: 400 (Bad Request). Transition id '31' is not valid for
issue OPS-1421 in its current status.` The Trace log shows the request:
"requesting transition id 31 on issue OPS-1421 (current status: In Review)". The
scope opened (not an auth problem) and the transition target was rejected
specifically because ID 31 is not available from the `In Review` status.

**Why:** This is sub-case **T2** of the transition-issue playbook. The `.xaml`
sets `TransitionId="31"` as a literal — there is no `Get Transitions` call to
discover the legal transitions for the current status. "Worked on the tickets I
first tested" is the tell: those tickets were in a status where 31 happened to
be valid; tickets now in a different status (In Review) expose a different set of
transition IDs. This is not a missing required field (the call was rejected on
the ID, not on a `Field '<name>' is required`), not a permission/validator (the
rejection is "not valid", a routing error, not "you cannot perform this
transition"), and not a deserialization bug (no `IssueFieldEditMetadataOperation`
error).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraStatusUpdater -- Faulted at 2026-06-16T13:05:04.220Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Issue Sync (key `5a04a2b3-d4e5-4f60-8a04-000000000004`)
- Final error: `Transition Issue: ... 400 (Bad Request). Transition id '31' is not valid for issue OPS-1421 in its current status.` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `TransitionIssue "Transition Issue"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the fault is on the child `Transition Issue`, not at scope open — auth is ruled out.
- `Main.xaml` sets `TransitionIssue` with `IssueKey="OPS-1421"` and a hardcoded `TransitionId="31"`. No `Get Transitions` activity precedes it.
- Trace: "requesting transition id 31 on issue OPS-1421 (current status: In Review)" — the ID is invalid from the `In Review` status, the **T2** signature.

---

**Immediate fix:**

Resolve the transition ID **dynamically** instead of hardcoding it.

1. Add a `Get Transitions` activity for the issue (`OPS-1421`) before the
   transition; it returns the transitions legal from the issue's **current**
   status, each with a runtime `Id` and `name`.
2. Loop the returned transitions, match the one whose `name` is the target
   status (e.g. `Done`, `In Progress`), and read its `.Id`.
3. Pass that runtime `.Id` into `Transition Issue` instead of the literal `31`.

This survives tickets starting from different statuses, which the hardcoded ID
cannot.

### Verification (hand to the user - off-host)
- Run `Get Transitions` for `OPS-1421` in its current status and confirm which
  IDs are actually available; `31` will be absent.

- **Source:** `jira-activities/playbooks/jira-transition-issue-failures.md` (T2)

---

**Preventive fix:**

1. **Never hardcode transition IDs** -- always resolve them with `Get
   Transitions` at runtime and match on the transition `name`.
   - **Why:** transition IDs are per-status workflow edges; the same target has
     different IDs from different starting statuses, so a literal breaks as soon
     as a ticket starts elsewhere.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Hardcoded TransitionId=31 is not valid from the issue's current status (In Review); no Get Transitions (T2) | High | Confirmed | Yes | `TransitionId="31"` literal in Main.xaml, no Get Transitions; `400 ... Transition id '31' is not valid ... in its current status`; worked only on initially-tested statuses | Resolve the transition ID dynamically via Get Transitions |
| H2 | Missing required field on the transition screen (T1) | Low | Rejected | No | Error is "not valid", not "Field '<name>' is required" | -- |
| H3 | Workflow Condition/Validator or permission (T3) | Low | Rejected | No | Rejection is an invalid-transition routing error, not a rule/permission denial | -- |

---

Would you like the exact `Get Transitions` + loop pattern to drop in before
`Transition Issue`, or help cleaning up the `.local/investigations/` folder?
