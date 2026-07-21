# Final Resolution

---

**Root Cause:** The `Add Comment` activity restricts the comment's visibility to a
project role the bot account is not a member of. `Main.xaml` sets
`VisibilityType="Role"` and `VisibilityValue="Service Desk Team"`; Jira rejects a
comment whose visibility is restricted to a role the commenting account does not
belong to, returning `400 (Bad Request): You are currently not a member of the
project role 'Service Desk Team' that you are restricting the comment visibility
to`.

**What went wrong:** The `JiraNoteBot` job (started 2026-06-17T16:25:02Z)
authenticated and opened the Jira session (Trace log: "session opened"), located
the issue, and attempted the comment (Trace: "posting comment to issue OPS-1605
(visibility: Role 'Service Desk Team')"), then faulted with `[Add Comment] ... 400
(Bad Request). You are currently not a member of the project role 'Service Desk
Team' ...`. The user only wants a normal public comment, so the visibility
restriction is unnecessary and is the sole cause of the rejection.

**Why:** This is sub-case **C4** of the add-comment playbook. When `Add Comment`
sets a `Visibility` restriction, Jira requires the commenting account to be a
member of the named group / project role — you cannot restrict a comment to an
audience you are not part of. The bot account is not in the `Service Desk Team`
role, so the call is rejected. This is not an authentication failure (the scope
opened), not a bad `IssueKey` (the status is `400` about visibility, not `404`),
and not a missing **Add Comments** permission (the account reached the comment
step and was rejected specifically on the visibility role, a `400`, not a blanket
`403`).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraNoteBot -- Faulted at 2026-06-17T16:25:04.020Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Service Desk (key `5a09a2b3-d4e5-4f60-8a09-000000000009`)
- Final error: `Add Comment: ... 400 (Bad Request). You are currently not a member of the project role 'Service Desk Team' that you are restricting the comment visibility to.` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `AddComment "Add Comment"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the fault is on `Add Comment`, not at scope open — auth ruled out.
- `Main.xaml` sets `AddComment` with a valid `IssueKey="OPS-1605"` **and** `VisibilityType="Role"`, `VisibilityValue="Service Desk Team"`.
- The error names the visibility role explicitly: `not a member of the project role 'Service Desk Team' ... restricting the comment visibility to`. `400` (not `404`/`403`) — isolating the **Visibility** misconfiguration (**C4**).

---

**Immediate fix:**

The user wants a normal public comment, so remove the visibility restriction.

### Fix path A -- clear Visibility (preferred here)
On the `Add Comment` activity, leave the `Visibility` parameters blank
(`VisibilityType` / `VisibilityValue` empty). The comment posts publicly (subject
to the issue's normal permissions) and the role-membership check no longer
applies.

### Fix path B -- set a valid restriction (only if a restriction is required)
If the comment genuinely must be restricted, set `Visibility` to a group /
project role that **exists** and that the bot account is a **member of**, and
ensure the instance allows it (*System -> General Configuration -> Comment
visibility* set to **Groups & Project Roles** when restricting to a group).

### Verification (hand to the user - off-host)
- Confirm whether the comment needs to be audience-restricted. If not, clear
  `Visibility` and re-run. If it must be restricted, confirm the bot account is a
  member of the chosen role/group.

- **Source:** `jira-activities/playbooks/jira-add-comment-failures.md` (C4)

---

**Preventive fix:**

1. **Default to public comments** -- leave `Add Comment` `Visibility` blank unless
   a restriction is genuinely required; a restriction the bot account cannot
   satisfy fails the call.
   - **Why:** Jira requires the commenter to belong to the role/group a restricted
     comment targets; a bot account rarely belongs to human project roles.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Comment Visibility restricted to project role 'Service Desk Team' the bot account is not in (C4) | High | Confirmed | Yes | `VisibilityType="Role"`, `VisibilityValue="Service Desk Team"` in Main.xaml; `400 ... not a member of the project role 'Service Desk Team' ... restricting the comment visibility to`; user only wants a public comment | Clear Visibility (or set a role/group the account belongs to) |
| H2 | Authentication failure | Low | Rejected | No | Trace shows the session opened; the fault is on the child activity | -- |
| H3 | Missing Add Comments permission (C3) | Low | Rejected | No | The `400` is specifically about the visibility role, not a blanket `403 Forbidden` | -- |

---

Would you like the exact `Add Comment` edit to clear `Visibility`, or help
cleaning up the `.local/investigations/` folder?
