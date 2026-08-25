# Diagnose — Investigate Identity, Authorization & Platform Failures

Capability index for diagnosing identity/auth failures, permission denials, IP restriction lockouts, and tenant operation issues via `uip admin`.

> **Where you came from / where to go next.** Diagnose is downstream of Operate (a user, app, or tenant operation failed
> or behaved unexpectedly). Source fixes — role changes, user provisioning, config updates — are Operate actions requiring
> explicit user consent after root cause analysis.
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md).** Use `uip admin ... --output json` for all diagnostic reads.

## When to use this capability

- Investigate login failures (user can't sign in, auth errors).
- Diagnose external app OAuth2 flow failures (scope mismatch, expired secret, wrong grant type).
- Triage robot account authentication confusion (identity vs credential model).
- Investigate PAT rejection (expired, revoked, insufficient scopes).
- Diagnose SMTP email delivery failures (invitations not sending).
- Investigate HTTP 403 / permission denied errors (missing role, wrong scope).
- Triage role assignments not taking effect (ownerServiceName/scope-path mismatch).
- Diagnose IP restriction lockout or unexpected enforcement behavior.
- Investigate stuck or failed tenant lifecycle operations.
- Identify service provisioning no-ops (platform-pinned services).

## Critical rules

1. **Diagnose reads; Operate mutates.** Do not create/delete users, assign roles, or toggle enforcement while diagnosing — present findings and let the user decide the fix.
2. **Use the CLI as the diagnostic interface.** Run `uip admin ... --output json` for all reads.
3. **Resolve principals before investigating.** Use `users list --search`, `groups list`, `robot-accounts list`, or `external-apps get` to resolve names to IDs before deeper queries.
4. **Route to audit for historical investigation.** Login events are org-scoped (`audit org events`); tenant activity is tenant-scoped (`audit tenant events`). See [audit-workflow-guide.md](../audit-workflow-guide.md).
5. **Use check-access as the primary authorization diagnostic.** The PDP (`check-access`) is the source of truth for effective permissions — it folds in server-side rules that `roles assignments list` alone may not reflect. See [check-access.md](../authorization/check-access.md).
6. **Do not expose private data.** Redact tenant URLs, secrets, tokens, and user credentials in summaries.

## Workflow

| Journey | Read |
|---------|------|
| Triage an identity/auth failure (sequential ladder) | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize a known failure pattern (lookup) | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read |
|---|---|
| Investigate why a user can't log in | [troubleshooting guide → Step 1](references/troubleshooting-guide.md#step-1-identify-the-failure-domain) |
| Diagnose HTTP 403 / permission denied | [troubleshooting guide → Step 3](references/troubleshooting-guide.md#step-3-check-effective-access) |
| Check why a role assignment isn't working | [failure modes → Role assignment not taking effect](references/failure-modes.md#role-assignment-not-taking-effect) |
| Diagnose an external app OAuth2 failure | [failure modes → External app OAuth2 failing](references/failure-modes.md#external-app-oauth2-flow-failing) |
| Investigate PAT rejection | [failure modes → PAT rejected](references/failure-modes.md#pat-rejected) |
| Diagnose SMTP delivery failure | [failure modes → SMTP not delivering](references/failure-modes.md#smtp-emails-not-delivering) |
| Recover from IP restriction lockout | [failure modes → IP restriction lockout](references/failure-modes.md#ip-restriction-lockout) |
| Investigate a stuck tenant operation | [failure modes → Tenant operation stuck](references/failure-modes.md#tenant-operation-stuck-or-failed) |

## Anti-patterns

- **Never assign/revoke roles while diagnosing.** Present findings first; let the user authorize mutations.
- **Never retry auth failures.** On 401, the token is missing required scopes — tell user to `uip logout && uip login`.
- **Never assume audit scope.** Login events are org-scoped; resource events are tenant-scoped. Ask if ambiguous (Rule 23).
- **Never guess principal IDs.** Always resolve via `users list --search` or equivalent before high-risk operations.
- **Never start with traces when check-access can answer the question.** The PDP is faster and more authoritative.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](references/troubleshooting-guide.md) — diagnostic priority ladder
- [failure-modes.md](references/failure-modes.md) — recurring failure patterns

### Cross-capability

- [authorization/check-access.md](../authorization/check-access.md) — effective access PDP
- [audit-workflow-guide.md](../audit-workflow-guide.md) — audit investigation playbooks
- [identity-commands.md](../identity-commands.md) — CLI reference for identity operations
- [ip-restriction/enforcement-management.md](../ip-restriction/enforcement-management.md) — enforcement toggle + lockout safety
- [tenants-commands.md](../tenants-commands.md) — tenant lifecycle + async operations
