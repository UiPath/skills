# Final Resolution

---

**Root Cause:** The `Jira Scope` `Server URL` is set to
`https://acme.atlassian.net/secure/Dashboard.jspa` - a dashboard page path
appended past the instance root. The classic pack builds `/rest/api/...` paths
onto `Server URL`, so the `Search Issues` REST call is routed at the HTML
dashboard page instead of the REST API. The response is HTML, not JSON, and the
pack fails to parse it with `Response was not recognized as JSON`.

**What went wrong:** The `JiraWeeklyReport` job (started 2026-06-15T06:00:02Z)
authenticated and opened the Jira session successfully (Trace log: "Jira Scope:
session opened to https://acme.atlassian.net/secure/Dashboard.jspa"), then
faulted on the child `Search Issues` activity with `[Search Issues] Response was
not recognized as JSON.` -> `UiPath.Jira.Activities.JiraException` at
`SearchIssues "Search Issues"`. The scope opened, so this is **not** an
authentication failure - the failure is on the REST call.

**Why:** This is sub-case **R1** of the response-not-JSON playbook. The classic
`UiPath.Jira.Activities` pack expects `Server URL` to be the bare instance root
(`https://<domain>.atlassian.net`) and appends its own REST paths. With
`/secure/Dashboard.jspa` (a Jira web UI page) appended, the constructed request
targets an HTML page; the body returned is HTML markup, which the JSON
deserializer rejects. The host is `acme.atlassian.net` (Jira **Cloud**), so the
on-premises Server / Data Center sub-case (R2) does not apply - the only problem
is the appended path. "Works in my browser" is expected: the browser is meant to
render that dashboard HTML; the REST client is not.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraWeeklyReport -- Faulted at 2026-06-15T06:00:05.110Z (ran ~3 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Reporting (key `5a02a2b3-d4e5-4f60-8a02-000000000002`)
- Final error: `Search Issues: Response was not recognized as JSON.` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `SearchIssues "Search Issues"`

### Jira Activities (Root Cause)
- The scope authenticated and opened the session (Trace: "session opened ... Authentication Type: Api Token"); the fault is on the child `Search Issues`, not at scope open. This separates it from the authentication family.
- Scope config in `Main.xaml`: `ServerUrl="https://acme.atlassian.net/secure/Dashboard.jspa"`. The `/secure/Dashboard.jspa` segment is a Jira web UI dashboard page, not the REST root.
- Host is `*.atlassian.net` = Jira Cloud, so R2 (on-prem Server / Data Center) is ruled out; the appended path (**R1**) is the cause.

---

**Immediate fix:**

Set the `Jira Scope` `Server URL` to the bare instance root only:
`https://acme.atlassian.net` (remove `/secure/Dashboard.jspa`). Let the
activities append their own `/rest/api/...` paths. Re-run; `Search Issues`
should return a parsed result.

- Wrong: `https://acme.atlassian.net/secure/Dashboard.jspa`
- Correct: `https://acme.atlassian.net`

### Verification (hand to the user - off-host)
- Confirm the root instance URL in *Jira → top-left product home* is
  `https://acme.atlassian.net` and use exactly that (no dashboard, project, or
  `/browse/...` path) as the `Server URL`.

- **Source:** `jira-activities/playbooks/jira-scope-response-not-json-or-500.md` (R1)

---

**Preventive fix:**

1. **Server URL is the root instance only** -- in every `Jira Scope`, set
   `Server URL` to `https://<domain>.atlassian.net` with no trailing path. Never
   paste a dashboard / project / `/browse/<KEY>` link from the browser address
   bar.
   - **Why:** the pack appends `/rest/api/...`; any path you add past the root
     routes the REST call to the wrong place and returns non-JSON.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Server URL has /secure/Dashboard.jspa appended past the root; REST call hits HTML, response is not JSON (R1) | High | Confirmed | Yes | `ServerUrl="https://acme.atlassian.net/secure/Dashboard.jspa"` in Main.xaml; scope opened OK then `Response was not recognized as JSON` on Search Issues; host is *.atlassian.net (Cloud) | Set Server URL to `https://acme.atlassian.net` |
| H2 | Authentication failure | Low | Rejected | No | Trace shows the session opened successfully; the fault is on the child activity, not scope open | -- |
| H3 | On-premises Server / Data Center endpoint mismatch (R2) | Low | Rejected | No | Host is `acme.atlassian.net` = Jira Cloud | -- |

---

Would you like the exact `Server URL` edit to apply to the `Jira Scope`, or help
cleaning up the `.local/investigations/` folder?
