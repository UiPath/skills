# Final Resolution

---

**Root Cause:** The Jira bot account (`rpa-bot@company.com`) **authenticated**
successfully but lacks the **Add Comments** permission in the target project's
permission scheme. Jira accepted the credential and then **authorized** the
request away, returning `403 (Forbidden): You do not have permission to comment
on this issue`. This is an authorization (permission) problem, not an
authentication one.

**What went wrong:** The `JiraCommentSync` job (started 2026-06-17T14:02:02Z)
authenticated and opened the Jira session (Trace log: "session opened"), located
the issue, and attempted the comment (Trace: "posting comment to issue OPS-1502
as rpa-bot@company.com"), then faulted with `[Add Comment] Response status code
does not indicate success: 403 (Forbidden). You do not have permission to comment
on this issue.` The account can read the issue (per the user) but cannot comment.

**Why:** This is sub-case **C3** of the add-comment playbook. A `403 Forbidden`
means the request was authenticated (the API token is valid — otherwise it would
be a `401` / `Authentication information is invalid`) but the account is not
permitted to perform this action on this project. Jira projects map the **Add
Comments** permission to specific groups / project roles in their permission
scheme; if the bot account is not in a group/role mapped to **Add Comments**, the
comment is rejected even though reading works. The `IssueKey` is well-formed
(`OPS-1502`) and no `Visibility` is set, ruling out C2 and C4.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraCommentSync -- Faulted at 2026-06-17T14:02:03.940Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Issue Sync (key `5a08a2b3-d4e5-4f60-8a08-000000000008`)
- Final error: `Add Comment: ... 403 (Forbidden). You do not have permission to comment on this issue.` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `AddComment "Add Comment"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the account even located and attempted to comment on `OPS-1502` — so the credential is valid (not a `401`).
- The status is `403 Forbidden` with `You do not have permission to comment on this issue` — authenticated but not authorized.
- `Main.xaml` sets a well-formed `IssueKey="OPS-1502"` and no `Visibility` — ruling out C2 (bad key / `404`) and C4 (visibility / `400`). The cause is the missing **Add Comments** project permission (**C3**).

---

**Immediate fix:**

Grant the bot account the **Add Comments** permission in the target project.
This is a Jira-side change, not a workflow change.

1. Contact the **Jira administrator**.
2. Have them open the project's **permission scheme** and confirm which group /
   project role is mapped to **Add Comments**.
3. Have them add the bot account (`rpa-bot@company.com`) to that group / project
   role (or add the account directly if the scheme allows).

### Verification (hand to the user - off-host)
- Sign in to the Jira UI **as the bot account** and try to add a comment to
  `OPS-1502`. If the comment box is unavailable or rejects, the **Add Comments**
  permission is missing — confirm the fix once the admin grants it.

- **Source:** `jira-activities/playbooks/jira-add-comment-failures.md` (C3)

---

**Preventive fix:**

1. **Provision the bot account's project permissions explicitly** -- when onboarding
   an automation to a Jira project, confirm the service account is in a group /
   role mapped to every permission it needs (Add Comments, Transition, etc.), not
   just read access.
   - **Why:** authentication (a valid token) does not imply authorization; each
     project's permission scheme gates actions independently.
   - **Who:** Jira administrator / RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Bot account authenticated but lacks the Add Comments project permission (C3) | High | Confirmed | Yes | `403 Forbidden: You do not have permission to comment on this issue`; session opened and issue located; reading works, only commenting fails | Jira admin grants the account the Add Comments permission in the project scheme |
| H2 | Invalid credential / authentication failure | Low | Rejected | No | `403` (authorized away), not `401`/`Authentication information is invalid`; the session opened | -- |
| H3 | Bad IssueKey (C2) | Low | Rejected | No | `IssueKey="OPS-1502"` is well-formed; status is `403`, not `404` | -- |

---

Would you like the exact wording to send the Jira administrator (which
permission and account), or help cleaning up the `.local/investigations/`
folder?
