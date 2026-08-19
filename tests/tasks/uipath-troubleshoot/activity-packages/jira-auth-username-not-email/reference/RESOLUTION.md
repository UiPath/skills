# Final Resolution

---

**Root Cause:** The `Jira Scope` `Username` is set to an alphanumeric Jira
`accountId` (`557058:9d8c7b6a-1f2e-4a3b-bc01-aabbccddeeff`) instead of the
account **email**. Jira Cloud requires the full account email (e.g.
`user@company.com`) as the `Username` for API-token (and basic) authentication,
so Atlassian rejects the credential at scope open with `Authentication
information is invalid`.

**What went wrong:** The `JiraIssueSync` job (started 2026-06-15T09:12:03Z)
faulted ~2 seconds after launch inside `Jira Scope`, before any child activity
ran. The job error and Error-level logs show `[Jira Scope] Authentication
information is invalid. Please check your credentials and try again.` ->
`UiPath.Jira.Activities.JiraException` at `JiraApplicationScope "Jira Scope"`.
The scope reached the authentication step (Trace log: "opening session to
https://acme.atlassian.net (Authentication Type: Api Token)") and the credential
was rejected.

**Why:** This is sub-case **A2** of the authentication-failures playbook. The
other three sub-causes are ruled out by the project:
- **A1 (token data type):** `Api Token` is bound from `in_ApiToken`, an
  `InArgument(SecureString)` - already a `SecureString`, not a plain `String`.
- **A3 (leftover OAuth params):** no `Client Id` / `Client Secret` are set on the
  scope; `Authentication Type = Api Token` only.
- **A4 (MFA/password blocker):** the scope uses `Authentication Type = Api Token`,
  not basic password auth, so MFA/SSO password-blocking does not apply.

That leaves the `Username`. The configured value `557058:9d8c7b6a-...` is a Jira
Cloud `accountId`, not an email address. Atlassian authenticates API-token calls
against the account **email** as the username; an `accountId` there is not a
valid identity and is rejected. "Works in the browser" does not clear it - the
browser logs in with the email/SSO, not the accountId string.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraIssueSync -- Faulted at 2026-06-15T09:12:04.905Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Issue Sync (key `5a01a2b3-d4e5-4f60-8a01-000000000001`)
- Final error: `Jira Scope: Authentication information is invalid. Please check your credentials and try again.` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"`

### Jira Activities (Root Cause)
- Activity surface: `UiPath.Jira.Activities.JiraApplicationScope` (Jira Scope). The fault is at scope open; no child activity (Search Issues) ran.
- Scope config in `Main.xaml`: `ServerUrl="https://acme.atlassian.net"` (root, correct), `AuthenticationType="ApiToken"`, `ApiToken="[in_ApiToken]"` (a `SecureString` in-argument), no `Client Id` / `Client Secret`, and `Username="557058:9d8c7b6a-1f2e-4a3b-bc01-aabbccddeeff"`.
- The `Username` is a Jira `accountId` (numeric prefix + colon + GUID), not an email. Every other auth property is valid, isolating the username format as the cause (**A2**).

---

**Immediate fix:**

Set the `Jira Scope` `Username` to the **full account email** of the Atlassian
account that owns the API token (e.g. `automation@company.com`), replacing the
`accountId` string. Re-run; the scope should open and `Search Issues` should
return results.

### Verification (hand to the user - off-host)
- In *Atlassian Account → Profile*, confirm the account **email**; use that exact
  email as the `Jira Scope` `Username`.
- Confirm the `Api Token` was generated for that same account (*Atlassian Account
  → Security → API tokens*).

- **Source:** `jira-activities/playbooks/jira-scope-authentication-failures.md` (A2)

---

**Preventive fix:**

1. **Use the account email as Username** -- in every `Jira Scope`, set `Username`
   to the account email, never the `accountId` shown on the Jira profile URL.
   - **Why:** Jira Cloud authenticates API-token / basic calls against the email;
     the `accountId` is an internal identifier, not a login username.
   - **Who:** RPA developer.

2. **Store the token as a credential asset** -- keep the `Api Token` in an
   Orchestrator credential asset and bind it as a `SecureString`, so the token
   type is correct by construction.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Username is a Jira accountId, not the account email; Jira Cloud rejects it at scope open (A2) | High | Confirmed | Yes | `Username="557058:9d8c7b6a-..."` (accountId) in Main.xaml; ApiToken is SecureString, no Client Id/Secret, AuthType=ApiToken -> A1/A3/A4 ruled out; `Authentication information is invalid` at Jira Scope | Set Username to the account email |
| H2 | Bad / expired Api Token (A1) | Low | Rejected | No | Token regenerated and valid per user; `Api Token` bound from a `SecureString` in-argument | -- |
| H3 | MFA/SSO blocking password auth (A4) | Low | Rejected | No | Scope uses `Authentication Type = Api Token`, not basic password auth | -- |

---

Would you like the exact `Username` edit to apply to the `Jira Scope`, or help
cleaning up the `.local/investigations/` folder?
