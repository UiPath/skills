# Diagnostic Priority Ladder

Sequential triage workflow for identity, authorization, and platform failures. Work through in order — stop when you have enough to diagnose.

## Step 1: Identify the Failure Domain

Determine which area the symptom belongs to based on user description:

| Symptom | Domain | Next step |
|---------|--------|-----------|
| "Can't log in", auth error, login rejected | Identity — login | Step 2 (resolve user) |
| "403", "permission denied", "access denied" | Authorization — access | Step 3 (check-access) |
| "Token not working", "PAT rejected" | Identity — PAT | Step 2 (resolve user), then [failure-modes → PAT rejected](failure-modes.md#pat-rejected) |
| "OAuth failing", "client_credentials error" | Identity — external app | [failure-modes → OAuth2 failing](failure-modes.md#external-app-oauth2-flow-failing) |
| "Robot not authenticating" | Identity — robot account | [failure-modes → Robot account](failure-modes.md#robot-account-not-authenticating) |
| "Emails not sending", "SMTP broken" | Identity — SMTP | [failure-modes → SMTP](failure-modes.md#smtp-emails-not-delivering) |
| "Locked out", "can't access org" | IP restriction | [failure-modes → IP lockout](failure-modes.md#ip-restriction-lockout) |
| "Tenant create stuck", "operation not completing" | OMS — tenant ops | [failure-modes → Tenant operation](failure-modes.md#tenant-operation-stuck-or-failed) |
| "Service still enabled after remove" | OMS — services | [failure-modes → Service no-op](failure-modes.md#service-provisioning-no-op) |

## Step 2: Resolve the Principal

Before any deeper investigation, resolve the named user/app/robot to its ID:

```bash
uip admin users list --search "<USER_EMAIL_OR_NAME>" --output json
```

For robot accounts:
```bash
uip admin robot-accounts list --search "<ROBOT_NAME>" --output json
```

For external apps:
```bash
uip admin external-apps get "<CLIENT_ID>" --output json
```

If the principal is not found → they were never provisioned or were deleted. This is the root cause.

## Step 3: Check Effective Access

For any permission-related symptom (403, "can't do X", role not working), the PDP is the primary diagnostic tool:

```bash
uip admin authorization check-access "<USER_ID>" --output json
```

To narrow to a specific service:
```bash
uip admin authorization check-access "<USER_ID>" --service orchestrator --output json
```

Interpret the results:
- Label each role as `direct` or `inherited from <Group>` by inspecting `roleAssignments[].securityPrincipalType`
- Compare effective permissions against the required permission for the denied action
- Check `ownerServiceName` on each role — cross-service grants don't apply (Orchestrator role ≠ DU access)

See [check-access.md](../../authorization/check-access.md) for full interpretation guide.

## Step 4: Check Audit History

For historical investigation (login failures, "who changed X", "when did access break"):

Login events are **org-scoped** (not tenant-scoped):
```bash
uip admin audit org sources --output json
uip admin audit org events \
  --user-id "<USER_ID>" --status "Failure" \
  --from-date "<START>" --to-date "<END>" \
  --output json
```

Resource changes (roles, assets, folders) are **tenant-scoped**:
```bash
uip admin audit tenant sources --output json
uip admin audit tenant events \
  --from-date "<START>" --to-date "<END>" \
  --output json
```

See [audit-workflow-guide.md](../../audit-workflow-guide.md) for scope routing rules.

## Step 5: Inspect Configuration

For config-related failures (SMTP, IP restriction, tenant services), read the current state:

```bash
uip admin smtp get --output json
uip admin ip-restriction enforcement get --output json
uip admin ip-restriction ip-ranges list --output json
uip admin tenants services list --tenant-id "<TENANT_ID>" --output json
```

Compare actual config against expected. For SMTP, run a test:
```bash
uip admin smtp test --recipient "<TEST_EMAIL>" --output json
```

## Outputs

After completing the relevant steps, present:
1. **Root cause** — what specifically failed and why
2. **Evidence** — which CLI commands confirmed the diagnosis
3. **Fix ownership** — whether the fix requires identity changes, authz changes, config changes, or platform support
4. **Recommended action** — specific next step (do not execute; present for user approval)
