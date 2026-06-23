# Identity & Authorization Troubleshooting Guide

Common investigation playbooks for identity, access, and security issues. Each starts from a user-reported symptom and resolves to a diagnosis using `uip admin` commands.

> Every command assumes the user has run `uip login`. Every command uses `--output json`.

---

## Playbook 1 — "User can't access resource X"

**Symptom:** "Alice can't publish to the Finance folder" / "Bob gets 403 on the API" / "The new contractor has no access to anything"

**Root causes (most → least common):**
1. Missing role assignment at the correct scope
2. Role exists but lacks the specific permission
3. User not in the expected group
4. User account disabled or not yet activated

### Step 1 — Resolve the principal

```bash
uip admin users list --search "<EMAIL_OR_NAME>" --output json
```

Extract the user's `id` (GUID) and `isActive` status. If `isActive` is `false`, the user is deactivated — that's the diagnosis. Otherwise proceed.

### Step 2 — Check effective access

```bash
uip admin authorization check-access <USER_GUID> --scope Tenant --output json
```

Or for folder-level:

```bash
uip admin authorization check-access <USER_GUID> --scope Folder --folder-id <FOLDER_UUID> --output json
```

Inspect `Data.roleAssignments[]` — each entry shows `roleName`, `scopeType`, and `securityPrincipalType` (`direct` = assigned to the user; `inherited` or `Group` = inherited from a group). Look for whether the needed permission (e.g., `Publish`) appears anywhere. If absent, that's the gap.

### Step 3 — List current role assignments

```bash
uip admin authorization roles assignments list --identity-id <USER_GUID> --output json
```

Compare the user's assignments against what's needed. Check `ownerServiceName` and `scopeType` — a role scoped to `Organization` won't grant folder-level permissions.

### Step 4 — Check group membership

```bash
uip admin groups list --output json
```

For each relevant group, check if the user is a member. If the user should inherit permissions via a group but isn't in it, that's the gap:

```bash
uip admin groups members list <GROUP_ID> --output json
```

### Step 5 — Diagnose and recommend

Present findings as:
- **Principal:** `<displayName> (<email>) — <id>`
- **Current access:** list of roles + scopes
- **Missing:** specific role or permission needed
- **Fix:** "Assign role X at scope Y" or "Add user to group Z"

---

## Playbook 2 — "Suspicious login activity"

**Symptom:** "Failed login attempts" / "Account may be compromised" / "Unknown logins from strange locations"

**Scope: `org`.** Login events (User Login, Robot Login, External App Login) are org-level audit events under Identity → Authentication.

### Step 1 — Resolve the user

```bash
uip admin users list --search "<EMAIL>" --output json
```

Extract the `id` for `--user-id` filtering.

### Step 2 — Discover login event types

```bash
uip admin audit org sources --output json > /tmp/sources.json
```

Extract the User Login type GUID:
```bash
jq -r '.Data[] | select(.name == "Identity") | .eventTargets[] | select(.name == "Authentication") | .eventTypes[] | select(.name == "User Login") | .id' /tmp/sources.json
```

### Step 3 — Query login events

```bash
uip admin audit org events \
  --user-id <USER_GUID> \
  --type    <USER_LOGIN_TYPE_GUID> \
  --from-date <START_ISO8601> \
  --to-date   <END_ISO8601> \
  --limit 100 \
  --output json
```

### Step 4 — Analyze

For each event in `Data.auditEvents[]`, check:
- `status` — `0` = Success, `1` = Failure
- `clientInfo` — parse JSON string for `ipAddress` and `ipCountry`
- `createdOn` — timestamp (UTC)

Flag: multiple failures from different IPs, logins from unexpected countries, or logins outside business hours.

---

## Playbook 3 — "Role misconfiguration"

**Symptom:** "Custom role doesn't grant what it should" / "User has a role but still can't do X"

### Step 1 — Inspect the role

```bash
uip admin authorization roles list --output json
```

Find the role by name, then:

```bash
uip admin authorization roles get <ROLE_ID> --output json
```

Check `actions[]` — these are the permission strings (e.g., `OR.Folders.Create`). Compare against the Permission Catalog:

```bash
uip admin authorization permissions list --service <SERVICE> --output json
```

### Step 2 — Verify scope alignment

The role's `scopeType` (Organization / TenantGlobal / Tenant / Project) must match the assignment scope. A role scoped to `Organization` cannot be assigned at `Folder` scope. Check the assignment:

```bash
uip admin authorization roles assignments list --identity-id <USER_GUID> --output json
```

Verify `ownerServiceName` matches the scope-path service segment (Rule 17 from SKILL.md).

### Step 3 — Diagnose

Common misconfigurations:
- **Scope mismatch:** role is `Tenant` but user needs folder-level access → create a `Project`-scoped role or use Orchestrator folder roles instead (`uip or roles`)
- **Missing actions:** role omits required permissions → `roles update` with the full action set (re-fetch first — Rule 12)
- **Wrong service:** role's `ownerServiceName` doesn't match the target service

---

## Playbook 4 — "IP restriction lockout"

**Symptom:** "Can't access the platform from new office" / "All users blocked" / "IP restriction locked us out"

### Step 1 — Check enforcement status

```bash
uip admin ip-restriction enforcement get --output json
```

If `isEnabled` is `false`, IP restriction is not the cause — look elsewhere.

### Step 2 — Check caller's IP

```bash
uip admin ip-restriction my-ip --output json
```

Returns `Data.ipAddress` — the public IP the platform sees for the caller.

### Step 3 — List allowed ranges

```bash
uip admin ip-restriction ip-ranges list --output json
```

Compare the caller's IP against every entry's CIDR range. If the IP is not covered by any entry, that's the lockout cause.

### Step 4 — Check bypass rules

```bash
uip admin ip-restriction bypass-rules list --output json
```

Bypass rules exempt specific URL patterns from IP restriction. If the affected access is via an API endpoint matching a bypass pattern, the IP restriction should not apply — investigate other causes.

### Step 5 — Resolution options

- **Add the new IP/CIDR:** `ip-ranges create --name "<LOCATION>" --cidr <CIDR> --output json`
- **Disable enforcement temporarily:** `ip-restriction enforcement disable --output json` (if accessible from an allowed IP)
- **Platform recovery:** if fully locked out, use the Portal recovery flow (no CLI bypass exists — Rule 32)

---

## Playbook 5 — "PAT or external app not working"

**Symptom:** "API calls return 401" / "PAT stopped working" / "External app can't authenticate"

### Step 1 — List PATs or external apps

For PATs:
```bash
uip admin pat list --output json
```

Check `expiration` — expired PATs return 401 silently. If the token is absent from the list, it was revoked (revocation is a hard delete — no `isRevoked` flag exists).

For external apps:
```bash
uip admin external-apps list --output json
```

### Step 2 — Verify scopes

PATs and external apps are scoped — if the API call requires `OR.Execution` but the token only has `OR.Folders.Read`, the call fails.

For external apps, check the declared scopes against the API endpoint's requirement. For PATs, re-create with the correct `--scope`.

### Step 3 — Check audit for revocation

Query org audit for recent identity events — a PAT or app secret may have been revoked:

```bash
uip admin audit org sources --output json
# Find Identity source → PersonalAccessTokens or ExternalApps target
uip admin audit org events \
  --source <IDENTITY_SOURCE_GUID> \
  --from-date <RECENT_WINDOW> \
  --to-date <NOW> \
  --limit 50 \
  --output json
```

---

## Cross-reference

- Audit event investigation workflows → [audit-workflow-guide.md](audit-workflow-guide.md)
- Role management (create/update custom roles) → [authorization/role-management.md](authorization/role-management.md)
- Role assignment scope validation → [authorization/role-assignment-management.md](authorization/role-assignment-management.md)
- Permission catalog lookup → [authorization/permission-catalog.md](authorization/permission-catalog.md)
- IP restriction management → [ip-restriction/ip-restriction-commands.md](ip-restriction/ip-restriction-commands.md)
