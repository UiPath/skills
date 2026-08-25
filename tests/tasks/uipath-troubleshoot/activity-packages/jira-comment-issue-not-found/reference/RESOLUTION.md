# Final Resolution

---

**Root Cause:** The `Add Comment` activity's `IssueKey` is `1450` — a bare number
missing the project prefix. A Jira issue key is `PROJECT-NUMBER` (e.g.
`OPS-1450`); `1450` alone is not a valid key, so Jira cannot locate the issue and
returns `404 (Not Found) — Issue Not Found` before the comment is posted.

**What went wrong:** The `JiraCommentBot` job (started 2026-06-17T10:18:02Z)
authenticated and opened the Jira session (Trace log: "session opened"), then
faulted on `Add Comment` (Trace: "posting comment to issue 1450") with `[Add
Comment] Response status code does not indicate success: 404 (Not Found). Issue
Not Found. The issue '1450' does not exist...`. The scope authenticated (not an
auth problem) and the issue lookup failed on the malformed key.

**Why:** This is sub-case **C2** of the add-comment playbook. `Main.xaml` sets
`AddComment` with `IssueKey="1450"` — the project prefix is missing. Jira keys
are `PROJECT-NNN`; passing the bare issue number (or the numeric internal ID)
does not resolve to an issue, producing `Issue Not Found` / `404`. "It exists in
my browser" confirms the issue is real — the browser URL is `.../browse/OPS-1450`
— so the fix is to pass the full key `OPS-1450`, not `1450`. This is not an
authentication failure (the scope opened), not a `403` permission problem (the
status is `404`, not `403`), and not a visibility issue (no `Visibility` is set
and the failure is issue lookup, not comment posting).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraCommentBot -- Faulted at 2026-06-17T10:18:04.050Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Issue Sync (key `5a07a2b3-d4e5-4f60-8a07-000000000007`)
- Final error: `Add Comment: ... 404 (Not Found). Issue Not Found. The issue '1450' does not exist...` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `AddComment "Add Comment"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the fault is on `Add Comment`, not at scope open — auth ruled out.
- `Main.xaml` sets `AddComment` with `IssueKey="1450"` — a bare number, no `PROJECT-` prefix.
- The error names the exact bad value: `The issue '1450' does not exist`. `404` (not `403`), and no `Visibility` is configured — isolating the malformed `IssueKey` (**C2**).

---

**Immediate fix:**

Pass the **full issue key including the project prefix** to `Add Comment` —
`OPS-1450`, exactly as it appears in Jira (the browser URL `.../browse/OPS-1450`
confirms it), not the bare number `1450`. If the key comes from upstream data,
ensure the `PROJECT-` prefix is included and not stripped. Re-run; the comment
should post.

- Wrong: `IssueKey = "1450"`
- Correct: `IssueKey = "OPS-1450"`

### Verification (hand to the user - off-host)
- Confirm the exact key in Jira (the `.../browse/<KEY>` URL) and pass that
  literal into `Add Comment`.

- **Source:** `jira-activities/playbooks/jira-add-comment-failures.md` (C2)

---

**Preventive fix:**

1. **Always pass the full `PROJECT-NNN` issue key** -- never a bare number or the
   numeric internal ID; validate that upstream data carries the project prefix.
   - **Why:** Jira resolves issues by their key, not the bare number; a
     prefix-less value yields `Issue Not Found`.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | IssueKey="1450" is missing the project prefix; Jira can't find the issue (C2) | High | Confirmed | Yes | `IssueKey="1450"` (bare number) in Main.xaml; `404 ... The issue '1450' does not exist`; scope authenticated; real key is OPS-1450 | Pass the full key `OPS-1450` |
| H2 | Authentication failure | Low | Rejected | No | Trace shows the session opened; the fault is on the child activity | -- |
| H3 | 403 missing Add Comments permission (C3) | Low | Rejected | No | Status is `404 Not Found`, not `403 Forbidden` | -- |

---

Would you like the exact `IssueKey` edit (or a guard that validates the
`PROJECT-NNN` format upstream), or help cleaning up the `.local/investigations/`
folder?
