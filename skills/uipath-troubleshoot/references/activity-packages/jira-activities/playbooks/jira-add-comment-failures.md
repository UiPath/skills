---
confidence: medium
---

# Add Comment — Comment Fails To Post

## Context

What this looks like:
- An `Add Comment` activity faults when appending a comment to a Jira issue. Common shapes:
  - `Authentication information is invalid` / the activity will not run because it is not inside a scope.
  - `Issue Not Found` / HTTP `404` for the target issue.
  - `403 Forbidden` even though the connection authenticated.
  - A comment-`Visibility` error (`400`) naming a group / project role.

`Add Comment` cannot run standalone — it must sit inside a **Jira Application Scope** (classic) or use an Integration Service Jira connection. Most failures are a mismatch between the activity's properties (or the account's Jira permissions) and the issue/project, not a code defect.

What can cause it (Add Comment-specific sub-cases):
- **C1 — missing / broken parent scope.** `Add Comment` is outside a `Jira Application Scope`, or the scope it sits in failed to authenticate. *(If the scope itself faults with `Authentication information is invalid` — bad token type, accountId-vs-email username, leftover OAuth params, or MFA/SSO blocking password auth — that is the scope's problem; see [jira-scope-authentication-failures.md](./jira-scope-authentication-failures.md).)*
- **C2 — Issue Not Found / bad `IssueKey` format.** The `IssueKey` is missing the project prefix (e.g. `1234` or `123` instead of `PROJ-123`), is the numeric internal ID instead of the key, or names an issue the account cannot see — Jira returns `Issue Not Found` / `404` and the comment is never attempted.
- **C3 — `403 Forbidden` / missing project permission.** The connection authenticated (the account is valid), but the account lacks the **Add Comments** permission in that project's permission scheme. Jira **authenticated** the request and then **authorized** it away — a `403`, distinct from a `401`/`Authentication information is invalid`.
- **C4 — comment `Visibility` restriction misconfigured.** The activity's `Visibility` (type + value) restricts the comment to a group or project role that does not exist, that the account is not a member of, or that the Jira instance's global comment-visibility setting does not allow — Jira rejects with a `400` naming the role/group.

What to look for:
- Whether `Add Comment` is inside a `Jira Application Scope` (C1).
- The literal / variable passed to `IssueKey` — does it carry the `PROJECT-NNN` prefix, or is it a bare number? (C2)
- The exact HTTP status: `401`/auth-invalid (scope) vs `404`/not-found (C2) vs `403`/forbidden (C3) vs `400`/visibility (C4).
- Whether `Visibility` (type/value) is populated on the activity, and what role/group it names (C4).

## Investigation

1. Read the error and classify it: `Authentication information is invalid` → scope auth (C1; see the auth playbook); `Issue Not Found` / `404` → C2; `403 Forbidden` → C3; a `400` naming a group/role under visibility → C4.
2. Confirm `Add Comment` is inside a `Jira Application Scope` in the `.xaml` (C1). If not, that is the cause.
3. For C2: read the `IssueKey` value. Check for a missing `PROJECT-` prefix, a bare number, or a `/browse/`-style value. Compare against the exact key format in Jira.
4. For C3: confirm the scope authenticated (a child `403`, not a scope-open `401`). The `403` means the account is valid but not permitted to comment on that project.
5. For C4: read the `Visibility` type/value on the activity; check it names a real group / project role the account belongs to and that the instance allows.

## Resolution

- **C1 — wrap in a scope:** place `Add Comment` inside a correctly configured `Jira Application Scope` (valid `Username` = account email, `Api Token` as a `SecureString`). For the auth-token / MFA specifics, see [jira-scope-authentication-failures.md](./jira-scope-authentication-failures.md).
- **C2 — fix the `IssueKey`:** pass the full issue key including the project prefix exactly as shown in Jira (e.g. `PROJ-123`, not `123`). If the value comes from upstream data, ensure the prefix is included and not stripped.
- **C3 — grant the project permission:** the account lacks **Add Comments** in the project's permission scheme. Contact the Jira administrator and have them add the robot/API account to the group or project role mapped to **Add Comments** for that project. Confirm by adding a comment manually as that account in the Jira UI.
- **C4 — fix or clear `Visibility`:** to post a public comment, leave the `Visibility` parameters blank. If a restriction is required, set it to a group / project role that exists and that the account is a member of, and ensure the instance allows it (*System → General Configuration → Comment visibility* set to **Groups & Project Roles**, not **Project Roles only**, when restricting to a group).
- **C5 — package / Studio compatibility:** if the failure is a compilation / activity-load error after a Studio upgrade (not one of the runtime errors above), it is a package-version conflict — see [jira-activity-missing-or-not-loaded.md](./jira-activity-missing-or-not-loaded.md) (upgrade `UiPath.Jira.Activities`, or migrate to the Integration Service Jira connector).

### Verification (hand to the user — off-host)
- For C3, add a comment manually as the robot's service account in the Jira UI; if it is blocked, the permission is missing.
- For C2, confirm the exact issue key (with prefix) in Jira and pass that literal.

This is medium-confidence: C2 and C4 are clearly signalled by the `IssueKey` value / `Visibility` config plus the error; C3 is confirmed by reproducing the comment as the service account (the `403` says "not permitted", not which scheme entry is missing), so treat the missing-permission cause as a hypothesis to confirm with the Jira admin.
