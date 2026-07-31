---
confidence: high
---

# Jira Scope — Authentication Information Is Invalid

## Context

What this looks like:
- `Jira Scope` faults immediately on scope open with:
  - `Jira Scope: Authentication information is invalid. Please check your credentials and try again.`
- The fault is at scope open — no child Jira activity (Get Issue, Search Issues) has run yet.
- The same credentials "work in the browser" or worked previously, so "the password is right, why is it invalid?"

What can cause it (four sub-cases — they share one error string):
- **A1 — `Api Token` passed as a plain `String`.** The `Api Token` (and `Password`) property expects a `SecureString`. Binding a plain `String` variable / literal breaks the authentication handler before the request is sent.
- **A2 — `Username` is an alphanumeric `accountId`, not the account email.** Jira Cloud expects the **full account email** (e.g. `user@company.com`) as the `Username` for basic / API-token auth. An alphanumeric Jira `accountId` (e.g. `557058:1a2b…`) is rejected.
- **A3 — leftover `Client Id` / `Client Secret` with `Authentication Type = Api Token`.** Credential properties from a different auth method (OAuth 2.0) left populated cause validation conflicts. With `Api Token` selected, `Client Id` and `Client Secret` must be empty.
- **A4 — basic password auth on an MFA/SSO-enforced org.** If the Atlassian org enforces MFA/SSO, Atlassian **blocks basic password authentication** for the API regardless of how correct the password is. The standard account password can never succeed; an API token is required.

What to look for:
- The data type bound to `Api Token` / `Password` — `SecureString` vs `String`.
- The `Username` value — an email address vs an alphanumeric `accountId`.
- Whether `Client Id` / `Client Secret` are populated while `Authentication Type = Api Token`.
- The configured `Authentication Type` (`Basic` password vs `Api Token`) against whether the org enforces MFA/SSO.

## Investigation

1. Read the error from job evidence. Confirm it is `Authentication information is invalid` at `Jira Scope` (scope open), not a `Response was not recognized as JSON` / HTTP `500` on a child activity (different playbook).
2. Read the `Jira Scope` properties from the `.xaml`: `Authentication Type`, `Username`, and which credential properties are set. Capture the **data type** bound to `Api Token` / `Password`.
3. Walk the four sub-cases against what you see:
   - `Api Token` bound from a `String` (not `SecureString`)? → A1.
   - `Username` is an alphanumeric `accountId` rather than an email? → A2.
   - `Client Id` / `Client Secret` populated under `Authentication Type = Api Token`? → A3.
   - `Authentication Type = Basic` with a password, on an org that enforces MFA/SSO? → A4.
4. If `Authentication Type = Basic`, establish out-of-band whether the org enforces MFA/SSO — that alone decides A4 (password auth can never succeed).

## Resolution

- **A1 — wrong token data type:** bind `Api Token` to a `SecureString`. Store the token in an Orchestrator credential asset and supply it via **Get Credential** (returns a `SecureString`), or convert with a secure-string step. Do not bind a plain `String` literal/variable.
- **A2 — username format:** set `Username` to the **full account email** (`user@company.com`), not the alphanumeric Jira `accountId`.
- **A3 — leftover OAuth parameters:** with `Authentication Type = Api Token`, clear `Client Id` and `Client Secret` completely so only the API-token properties are set.
- **A4 — MFA/SSO blocker:** stop using basic password auth. Generate an **API token** at *Atlassian Account → Security → Create and manage API tokens*, set `Authentication Type = Api Token`, `Username` = account email, and `Api Token` = the generated token (as a `SecureString`). The API token bypasses interactive MFA/SSO for programmatic calls.

After the fix, re-run; the scope opening successfully (and the first child activity returning data) is immediate confirmation.

This is a high-confidence configuration fix: the error pins the failure to credential validation at scope open, and the four sub-causes are each visible in the scope's properties (plus the org MFA policy for A4).
