# Jira Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.Jira.Activities.JiraApplicationScope` / "Jira Scope", or a child activity like "Get Issue" / "Search Issues"). A fault **at scope open** (authentication) and a fault **on a child activity** (a bad response, a failed query) are different code paths — treat them as different.
- **Error string** — `Authentication information is invalid`, `Response was not recognized as JSON`, an HTTP `5xx`, and `This activity is either missing or could not be loaded properly` map to different playbooks. Read the literal message, not a paraphrase.
- **Jira instance identity** — the `Server URL` in the workflow matches the instance the user reports, and whether it is Jira **Cloud** (`https://<domain>.atlassian.net`) or an on-premises **Server / Data Center** host. The classic pack targets Cloud; the deployment type is load-bearing for the not-JSON / `500` family.
- **Authentication configuration** — the `Authentication Type` (`Api Token` / `Basic` / `OAuth 2.0`) and which credential properties are populated. A credential rejection is interpreted differently depending on which auth mode is configured and whether stray properties from another mode are still set.
- **Account / org policy** — whether the Atlassian org enforces MFA/SSO. Load-bearing for the password-vs-API-token sub-case: basic password auth fails under enforced MFA even with correct credentials.
- **Package + project dependencies** — the `UiPath.Jira.Activities` version from `project.json` and the other packages in the project (anything that also pins **RestSharp** or other shared transitive libraries). Load-bearing for the activity-load family.
- **Timestamp** — the failure occurred during the time window the user reported.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for `Jira Scope` failures, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity (`Jira Scope` vs a specific child) and the exact error string. Scope-open authentication faults, child-activity response faults, and activity-load faults are different families.
2. **Scope configuration** — from the `.xaml`, capture `Server URL`, `Authentication Type`, `Username`, and which credential properties (`Api Token`, `Password`, `Client Id`, `Client Secret`) are set. Note the **data type** bound to `Api Token` / `Password` (must be `SecureString`, not `String`).
3. **Username format** — whether `Username` is the account **email** (Cloud requirement) or an alphanumeric `accountId`.
4. **Server URL shape** — whether `Server URL` is the bare root instance (`https://<domain>.atlassian.net`) or has a path appended (`/secure/Dashboard.jspa`, a project key, a `/browse/...` link).
5. **Deployment type** — Jira Cloud vs on-premises Server / Data Center. Not always in the job log; the `Server URL` host and the user confirm it.
6. **Org auth policy** — whether MFA/SSO is enforced for the account. Determines whether basic password auth can ever succeed. Confirmed by the user / Atlassian org admin, not the job log.
7. **Project dependency set** — `UiPath.Jira.Activities` version and any sibling package that pins a conflicting **RestSharp** (or other shared assembly). Read from `project.json` and, when available, the build/restore log.

### Out-of-band confirmation

Two deciding proofs for Jira causes live outside the job log: whether the Atlassian org **enforces MFA/SSO** (org admin / Atlassian account settings), and whether a freshly generated **API token** authenticates the same `Server URL` (the user regenerates a token at *Atlassian Account → Security → API tokens* and retries). Record these as out-of-band confirmation steps — they do not block a hypothesis when no alternative cause is better supported, but they are how the user closes the case.
