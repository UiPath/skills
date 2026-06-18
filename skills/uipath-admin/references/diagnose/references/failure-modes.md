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

## User Gets HTTP 403 (Permission Denied)

**Symptom:** User or integration receives 403 when calling a platform API or performing a UI action.

**Causes:**
1. No role at all for the required service
2. Role exists but at wrong scope (org vs tenant vs folder)
3. Role missing the specific permission action
4. Cross-service confusion (Orchestrator role ≠ DU access)

**Investigation:**
1. Resolve user: `uip admin users list --search "<USER_EMAIL>" --output json`
2. Check effective access: `uip admin authorization check-access "<USER_ID>" --output json`
3. Narrow to service: `uip admin authorization check-access "<USER_ID>" --service <SERVICE> --output json`
4. Compare against required permission: `uip admin authorization permissions list --service <SERVICE> --output json`
5. Label each result as `direct` or `inherited from <Group>` — see [check-access.md](../../authorization/check-access.md)

**Fix:** Cause 1 → assign a role for the service. Cause 2 → re-assign at correct scope. Cause 3 → update custom role actions or assign additional role. Cause 4 → assign role owned by the correct service.

---

## Role Assignment Not Taking Effect

**Symptom:** Admin assigned a role but the principal still cannot perform the expected action.

**Causes:**
1. `ownerServiceName` / scope-path mismatch (Rule 17) — most common
2. Role assigned at wrong scope level (TenantGlobal vs Tenant vs Folder)
3. Role missing the needed permission action
4. Assignment at wrong tenant

**Investigation:**
1. Verify assignment exists: `uip admin authorization roles assignments list --filter "<PRINCIPAL_NAME>" --output json`
2. Inspect role: `uip admin authorization roles get "<ROLE_ID>" --output json` — check `ownerServiceName` and `scopeType`
3. Validate Rule 17: `CentralizedAccess` → no service segment in scope-path; any other value → path must include `lowercase(ownerServiceName)`
4. Verify via PDP: `uip admin authorization check-access "<PRINCIPAL_ID>" --output json`

**Fix:** Cause 1 → re-create assignment with correct scope-path matching ownerServiceName. Cause 2 → re-assign at correct scope. Cause 3 → update role actions. Cause 4 → re-assign at correct tenant.

---

## Cross-Service Permission Confusion

**Symptom:** "I have a role in Orchestrator but can't access DU projects" or "CentralizedAccess role doesn't grant service-specific permissions."

**Cause:** Permissions are service-scoped — an Orchestrator role does NOT grant DU, IXP, or other service access.

**Investigation:**
1. Check without service filter: `uip admin authorization check-access "<USER_ID>" --output json`
2. Check with service filter: `uip admin authorization check-access "<USER_ID>" --service documentunderstanding --output json`
3. Compare — the missing service's permissions will be absent
4. Check role's `ownerServiceName` to confirm it belongs to the wrong service

**Fix:** Assign a role owned by the correct service, or create a new custom role scoped to that service.

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
