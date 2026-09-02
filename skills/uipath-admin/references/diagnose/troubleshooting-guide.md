# Diagnostic Priority Ladder

Sequential triage workflow for identity, authorization, and platform failures. Work through in order — stop when you have enough to diagnose.

## Step 1: Identify the Failure Domain

Determine which area the symptom belongs to based on user description:

| Symptom | Domain | Next step |
|---------|--------|-----------|
| "Can't log in", auth error, login rejected | Identity — login | Step 2 (resolve user) |
| "403", "permission denied", "access denied", "the role I was assigned isn't working", "my <service> role doesn't work in <other service>" | Authorization — access | Step 3, then [failure-modes → Access denied](failure-modes.md#access-denied-http-403) |
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

Every permission symptom — 403, "can't do X", "the role isn't taking effect", "my Orchestrator role doesn't work in DU" — is the **same** investigation: compare what the principal effectively holds against what the denied action requires. The PDP answers the first half and is the primary diagnostic tool:

```bash
uip admin authorization check-access "<PRINCIPAL>" --output json
uip admin authorization check-access "<PRINCIPAL>" --service orchestrator --output json
```

Interpret the results:
- A permission reaches a principal by exactly two routes. Label each nested `roleAssignments[]` entry `direct` (role assigned to the principal) or `inherited from <Group>` (role assigned to a group the principal belongs to) by inspecting `securityPrincipalType`. The fix differs by route.
- Record role name, `ownerServiceName`, `scopeType`, and the grant's scope path for every granted role — the Step 3c branch needs all four.
- Cross-service grants do not apply: an Orchestrator role is not DU access.

See [check-access.md](../authorization/check-access.md) for the full interpretation guide.

### Step 3b: Identify the Permission the Denied Action Requires

The PDP says what the principal *has*; it never says what the action *needs*. Look the required permission up in the catalog before naming a fix — searching the whole catalog, not a guessed `--service` slice:

```bash
uip admin authorization permissions list --output json \
  --output-filter "[?contains(Name, 'ADMINISTRATION')]"
```

`contains` is case-sensitive: `Name` is UPPERCASE, `Description` is lowercase. A guessed `--service` returns `Data: []`, an unfiltered list is ~210 KB that truncates, and a slice of only the 10 cross-cutting `AUTHZ` rows means the wrong slice — none of the three proves the permission is absent. Read `ScopeType` from the hit; it fixes the role shape any fix must use. See [permission-catalog.md — Find the Permission Governing an Action](../authorization/permission-catalog.md#workflow-find-the-permission-governing-an-action).

State the diagnosis as: *principal holds `<roles>`, none of which carry `<PERMISSION.NAME>` (`ScopeType` `<SCOPE>`) → grant a `<SCOPE>`-shape role carrying it.* Never substitute a permission you did not find in the catalog.

### Step 3c: Branch — Missing Permission or Wrong Scope

With both halves in hand, exactly one of two causes holds. Follow the branch in [failure-modes → Access denied](failure-modes.md#step-3--branch-on-the-comparison):

| Step 3 vs Step 3b | Cause |
|---|---|
| No effective role carries the permission | [The permission is not granted](failure-modes.md#cause-a--the-permission-is-not-granted) — find a role that carries it |
| A role carries it, but the grant sits at another scope path | [The permission is granted at the wrong scope](failure-modes.md#cause-b--the-permission-is-granted-at-the-wrong-scope) — wrong or missing service segment, wrong scope level, or wrong tenant |

A mis-scoped grant is **invisible** to the default `assignments list` shapes; never read an empty listing as "the grant does not exist" before re-querying with `--scope-path`.

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

See [audit-workflow-guide.md](../audit-workflow-guide.md) for scope routing rules.

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
