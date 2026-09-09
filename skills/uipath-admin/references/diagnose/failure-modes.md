# Failure Modes — Identity, Authorization & Platform

Named failure patterns with symptom → cause → investigation → fix. Match the user's symptom to a pattern, then follow the investigation steps.

---

## User Cannot Log In

**Symptom:** User reports login failure — `uip login` returns error, Portal/UI login redirects or rejects.

**Causes:**
1. User not provisioned (never invited or deleted)
2. Bad credentials (password expired or incorrect)
3. IP restriction blocking the user's IP
4. Account locked (too many failed attempts)
5. No org access (user exists in identity but not assigned to org)

**Investigation:**
1. Verify user exists: `uip admin users list --search "<USER_EMAIL>" --output json`
2. If found, check login history at **org** scope:
   ```bash
   uip admin audit org events --user-id "<USER_ID>" --status "Failure" \
     --from-date "<7_DAYS_AGO>" --to-date "<TODAY>" --output json
   ```
3. Check IP restriction: `uip admin ip-restriction enforcement get --output json`

**Fix:** Cause 1 → invite user. Cause 2 → user resets password via Portal. Cause 3 → add IP to allowlist. Cause 4 → wait or admin unlock via Portal. Cause 5 → re-invite.

---

## External App OAuth2 Flow Failing

**Symptom:** CI/CD pipeline or integration returns auth errors using external app Client ID.

**Causes:**
1. Grant type / scope mismatch — `client_credentials` with `--user-scope` (or vice versa)
2. Secret expired or never generated
3. Redirect URI mismatch (authorization_code flow)
4. Non-confidential app used with `--app-scope` (rejected)
5. Scopes don't cover the required API

**Investigation:**
1. Inspect app config: `uip admin external-apps get "<CLIENT_ID>" --output json`
2. Check `resources` list for scope registration vs grant type
3. For `authorization_code` flow, verify redirect URI matches exactly

**Fix:** Cause 1 → recreate with correct scope type. Cause 2 → `external-apps generate-secret "<CLIENT_ID>" --output json` (secret shown only once). Cause 3 → `external-apps update --redirect-uri`. Cause 4 → use confidential app for app-only scopes. Cause 5 → update scopes (note: `--app-scope` on update **replaces** all scopes).

---

## Robot Account Not Authenticating

**Symptom:** Automation fails with "robot not authenticated" or similar credential errors.

**Causes:**
1. Robot account does not exist
2. Confusion between robot account (identity) and robot credentials (Orchestrator)
3. Robot account not in the correct groups

**Investigation:**
1. Verify robot exists: `uip admin robot-accounts list --search "<ROBOT_NAME>" --output json`
2. Check group membership: `uip admin groups list --output json`, then `groups members list "<GROUP_ID>" --output json`

**Fix:** Cause 1 → create robot account. Cause 2 → robot accounts are **identities only** — they don't carry API credentials (Client ID + Secret). For API access, create an **external app** instead. For unattended execution, Orchestrator provisions credentials via machine connection. Cause 3 → add to appropriate group.

---

## PAT Rejected

**Symptom:** API call with a personal access token returns 401 or 403.

**Causes:**
1. Token expired
2. Token revoked
3. Scope mismatch (token scopes don't cover the API)
4. Per-user token limit reached (new token couldn't be created)

**Investigation:**
1. List tokens: `uip admin pat list --output json`
2. Check `expiration` — if past today, token is expired
3. If the token is **absent from the list**, it was revoked (revocation is a hard delete — there is no `isRevoked` flag)
4. Compare `scopes` against the API being called

**Fix:** Cause 1 → regenerate: `pat regenerate "<PAT_ID>" --output json`. Cause 2 → create new token (revoked tokens are deleted, not recoverable). Cause 3 → create new token with correct scopes. Cause 4 → revoke unused tokens first: `pat revoke "<PAT_ID>" --output json`.

---

## SMTP Emails Not Delivering

**Symptom:** Platform invitation emails, password resets, or notifications not received.

**Causes:**
1. SMTP not configured (never set up or deleted)
2. Connection refused (wrong host/port or firewall)
3. Authentication failure (wrong credentials)
4. SSL/TLS mismatch
5. DNS resolution failure

**Investigation:**
1. Check config: `uip admin smtp get --output json`
2. Test delivery: `uip admin smtp test --recipient "<TEST_EMAIL>" --output json`
3. Branch on test result error message

**Fix:** Update config with correct values: `uip admin smtp update --host "<HOST>" --port <PORT> --secure <true|false> --user "<USER>" --password "<PASS>" --output json`. Re-test after each change.

---

## Access Denied (HTTP 403)

**Symptom:** A principal — user, group member, robot account, or external app — receives 403 / "permission denied" from a platform API or a UI action. This is one investigation, not several. It covers "the user has no access," "the admin assigned a role and it isn't taking effect," and "the Orchestrator role doesn't work in Document Understanding."

**The diagnosis is a single comparison in two halves:** what the principal *effectively holds* (Step 1, from the PDP) against what the denied action *requires* (Step 2, from the catalog). Step 3 branches on which half of the comparison failed. Do not name a cause before both halves are in hand.

### Step 1 — Establish what the principal effectively holds

Resolve the principal first (Rule 5): `users list --search`, `groups list`, `robot-accounts list`, or `external-apps get`. If the principal does not exist, that is the root cause — stop.

Then run the PDP. It is authoritative for effective permissions, including the server-side role catalogs that `roles assignments list` never returns:

```bash
uip admin authorization check-access "<PRINCIPAL>" --output json
uip admin authorization check-access "<PRINCIPAL>" --service <SERVICE> --output json
```

The principal is the positional argument (UUID, name, or email — there is no `--identity-id` on this command). `--scope` accepts only `Tenant` or `Folder`. Never pass `--service centralizedaccess`; omit `--service` for the umbrella view.

A permission reaches a principal by exactly two routes, and the fix differs by route. Label every nested `roleAssignments[]` entry; never collapse them:

| Nested entry | Route | Report as |
|---|---|---|
| `securityPrincipalType: "User"`, id == queried principal | Role assigned to the principal | `direct` |
| `securityPrincipalType: "Group"` | Role assigned to a group the principal belongs to | `inherited from <Group>` |
| `securityPrincipalType: "Robot"` / `"ExternalApplication"` | Role assigned to that non-user principal | `via <Robot\|ExternalApplication> <name>` |

Repairing a direct grant targets the principal's own assignment; repairing an inherited grant requires changing group membership or the group's role binding. See [check-access.md](../authorization/check-access.md).

Record four fields per granted role: role name, `ownerServiceName`, `scopeType`, and the scope path the grant sits at. Step 3 needs all four.

### Step 2 — Establish what the denied action requires

The PDP reports what the principal *has*; it never reports what the action *needs*. Look the required permission up in the catalog, searching the whole catalog rather than a guessed `--service` slice:

```bash
uip admin authorization permissions list --output json \
  --output-filter "[?contains(Name, 'ADMINISTRATION')]"
```

`contains` is case-sensitive: `Name` is UPPERCASE, `Description` is lowercase. Three results that do **not** prove the permission is absent — never conclude "not found" from any of them:

1. `Data: []` from a guessed `--service`.
2. A truncated unfiltered list (the catalog is ~210 KB).
3. A slice returning only the 10 cross-cutting `AUTHZ` rows — that floor signals a wrong `--service` / `--scope` pair, not an empty service.

Narrow by role shape with `--scope`, never with a guessed `--service`. See [permission-catalog.md — Find the Permission Governing an Action](../authorization/permission-catalog.md#workflow-find-the-permission-governing-an-action).

Read `ScopeType` from the hit. It fixes the role shape any fix must use (`TENANT` → a `Tenant`- or `TenantGlobal`-shape role).

### Step 3 — Branch on the comparison

| Step 1 vs Step 2 | Cause |
|---|---|
| No effective role carries the permission | [Cause A — the permission is not granted](#cause-a--the-permission-is-not-granted) |
| A role carries the permission, but its grant sits at a scope path other than the one the denied call evaluates against | [Cause B — the permission is granted at the wrong scope](#cause-b--the-permission-is-granted-at-the-wrong-scope) |

#### Cause A — The permission is not granted

No role the principal effectively holds carries the permission from Step 2. Find which role does:

```bash
uip admin authorization roles list --service <SERVICE> --output json
uip admin authorization roles get "<ROLE_ID>" --output json
```

`roles get` returns `ActionDetails[].Name`; match it against the permission name from Step 2. Use the permission's own owning service for `--service`, not a guess.

State the diagnosis as: *principal holds `<roles>`, none of which carry `<PERMISSION.NAME>` (`ScopeType <SCOPE>`) → grant a `<SCOPE>`-shape role carrying it.* Never substitute a permission you did not find in Step 2.

**Fix (Operate — present it, do not run it):** assign a role that carries the permission, directly or through a group the principal belongs to; or add the action to a custom role the principal already holds. `roles update` is a PUT-style upsert — run `roles get` first and resend the full action set (Rule 12). Built-in roles cannot be edited.

#### Cause B — The permission is granted at the wrong scope

The principal holds the permission and the PAP accepted the assignment; it simply never applies at the scope the denied call evaluates. Permissions are service-scoped and scope-path-bound: an Orchestrator role never grants Document Understanding, IXP, or any other service's access, whatever its actions say.

Four shapes, most common first:

| Shape | Example | Detect by |
|---|---|---|
| Wrong service segment | Denied call evaluates `/tenant/<tid>/documentunderstanding`; grant sits at `/tenant/<tid>/orchestrator` | Grant path's service segment ≠ the denied action's service |
| Missing service segment (Rule 17 mismatch) | A `DocumentUnderstanding`-owned role granted at the bare `/tenant/<tid>` | `ownerServiceName` ≠ `CentralizedAccess` yet the path has no service segment |
| Wrong scope level | A `Tenant` grant for a Folder- or Project-level action; an `Organization` role expected to cover a folder | Role `scopeType` ≠ the permission's `ScopeType` from Step 2 |
| Wrong tenant | Grant on tenant A; the call runs on tenant B | Grant path's `<tid>` ≠ the failing tenant |

Confirm a service split by running `check-access` with and without `--service <SERVICE>`: the missing service's permissions are absent from the filtered result while the umbrella view still shows the role.

Validate the binding (Rule 17):

1. `uip admin authorization roles get "<ROLE_ID>" --output json` — read `ownerServiceName` and `scopeType`.
2. `CentralizedAccess` → the path carries **no** service segment (`/` for Organization, `/tenant/<tid>` for Tenant/TenantGlobal). Any other value → the path must contain `lowercase(ownerServiceName)`, e.g. `Reinfer` → `/tenant/<tid>/reinfer`. Display names (`Reinfer` → IXP, `DocumentUnderstanding` → Document Understanding) belong in prose only; echoed paths keep CLI slugs.
3. Retrieve the grant and compare its actual path against the expected one:
   ```bash
   uip admin authorization roles assignments list --identity-id "<PRINCIPAL_ID>" --output json
   ```
   `--filter` is **not** a valid flag here — it exists on `roles list`, not on `assignments list`.

> **A mis-scoped grant is invisible to the default listing — use `--scope-path` to see it.**
> `assignments list` filters on a scope path **and** a service, both derived from your flags:
>
> | flags | server scope | server serviceName |
> |---|---|---|
> | none, `--identity-id`, `--scope Tenant` | `/tenant/<tid>` | `centralizedaccess` |
> | `--service <svc>` | `/tenant/<tid>/<svc>` | `<svc>` |
> | `--scope-path <path>` (no `--service`) | `<path>` verbatim | **unset** |
>
> A missing-service-segment grant — a `<svc>`-owned role granted at the bare `/tenant/<tid>` —
> matches neither of the first two shapes: the centralized-access shapes exclude it on service,
> and the `--service` shape excludes it on path. So it is absent from the default
> listing, from `--identity-id`, from `--scope Tenant` (with or without
> `--include-inherited`) and from `--service <svc>`. Retrieve it with the one shape that
> applies no service filter:
>
> ```bash
> uip admin authorization roles assignments list --scope-path "/tenant/<TENANT_ID>" --output json
> ```
>
> Verified on a live tenant: this returns the mis-scoped grant while every other shape
> returns only the principal's other grants. **Never read an empty centralized-access
> listing as "the grant does not exist"** — re-query with `--scope-path` first, and never
> re-create the assignment on that basis, which reproduces the original mismatch.

**Fix (Operate — present it, do not run it):** re-create the assignment at the scope path that matches the role's `ownerServiceName` and the permission's `ScopeType`, using `--service <slug>` or an explicit `--scope-path`. Derive `<slug>` as `lowercase(ownerServiceName)` from this role's own `roles get`; never copy a service segment off another role's grant, and do not add a project segment for a `Tenant`-scope role. `Reinfer` (display name IXP) and `DocumentUnderstanding` are different services with different segments. Never widen a scope to make the call pass, and never coerce a path onto a role that does not own that service — if no role owns the intended service, author one under it. For folder-level access to Orchestrator resources, use Orchestrator's own folder roles (`uip or roles`, `uipath-platform`). See [role-assignment-management.md — Validate Role Service Binding and Scope Path](../authorization/role-assignment-management.md#validate-role-service-binding-and-scope-path).

---

## IP Restriction Lockout

**Symptom:** User or admin locked out of org after enabling IP restriction enforcement.

**Causes:**
1. Caller's IP not in allowlist when enforcement was enabled
2. Allowlist entry expired or was deleted

**Investigation:**
1. Attempt: `uip admin ip-restriction enforcement get --output json`
2. If succeeds → caller is not locked out; other users are. Check: `ip-ranges list --output json` and compare IPs
3. If fails → caller IS locked out. Recovery: access from an in-allowlist IP, or Portal recovery flow

**Fix:** Once recovered: `enforcement disable --output json`, fix allowlist, then re-enable with pre-flight safety check (Rule 31).

---

## Enforcement Not Blocking as Expected

**Symptom:** IP restriction is supposedly enabled but unwanted IPs can still access the org.

**Causes:**
1. Enforcement not actually enabled
2. Overly permissive CIDR entry (e.g., `0.0.0.0/0`)
3. Bypass rule too broad (regex matches all traffic)

**Investigation:**
1. `uip admin ip-restriction enforcement get --output json`
2. `uip admin ip-restriction ip-ranges list --output json` — check for broad CIDRs
3. `uip admin ip-restriction bypass-rules list --output json` — check regex patterns

**Fix:** Cause 1 → enable enforcement. Cause 2 → narrow or remove overly permissive entries. Cause 3 → tighten bypass rule regex.

---

## Tenant Operation Stuck or Failed

**Symptom:** `tenants create/update/delete/enable/disable` returned `operationId` but operation hasn't completed.

**Causes:**
1. Region unavailable or at capacity
2. Required services not available in region
3. Backend timeout (transient)
4. Quota exceeded

**Investigation:**
1. Poll: `uip admin organizations operation get "<OPERATION_ID>" --output json`
2. Interpret status: `Pending`/`Queued`/`Creating`/`Updating`/`Enabling`/`Disabling`/`Deleting`/`InProgress` → still in progress (auto-poll 3× at 5s, Rule 18). `Failed` → inspect `Data.error` / `Data.message`. Terminal success statuses are verb-specific: `Created`/`Updated`/`Enabled`/`Disabled`/`Deleted`/`Done` → verify with `tenants get "<TENANT_ID>" --output json`

**Fix:** Cause 1 → try different region: `organizations regions list --output json`. Cause 2 → check catalog: `tenants services list-available --region "<REGION>" --output json`. Cause 3 → retry. Cause 4 → contact support. Do NOT auto-retry failed mutations.

---

## Service Provisioning No-Op

**Symptom:** `tenants services disable` or `remove` returned Success but service still shows Enabled.

**Cause:** Always-provisioned services return Success on `disable`/`remove` but the state never changes. The always-provision list is configuration-driven and varies by deployment — always re-list after mutating to confirm the actual state changed.

**Investigation:**
1. Verify state: `uip admin tenants services list --tenant-id "<TENANT_ID>" --output json`
2. Compare state before and after the mutation — if unchanged, the service is always-provisioned

**Fix:** CLI cannot disable/remove always-provisioned services. Redirect to UiPath Portal. Always re-list after any service mutation (Rule 22).
