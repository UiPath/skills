# Identity & Authorization Troubleshooting Guide

Investigation playbooks for identity, access, and security issues using `uip admin` commands.

> Every command assumes the user has run `uip login`. Every command uses `--output json`.

---

## Playbook 1 — "Access denied (HTTP 403)"

**Symptoms:** A user cannot publish, receives a 403, has no access, or was assigned a role that appears to do nothing. These are one scenario, not several.

**Root causes (most → least common):** the principal holds no role carrying the required permission; the permission is granted but at the wrong scope path (wrong or missing service segment, wrong scope level, wrong tenant); the user is not in the expected group; the user is disabled or not activated.

The canonical branch — missing permission versus mis-scoped grant — is [diagnose/failure-modes.md → Access denied](diagnose/failure-modes.md#access-denied-http-403). Steps 1 and 3 below are the identity-side checks that come first.

### Step 1 — Resolve the principal and confirm it is active

Run:

```bash
uip admin users list --search "<EMAIL_OR_NAME>" --output json
```

Extract `id` (GUID) and `isActive`. If `isActive` is `false`, the user is deactivated; that is the root cause — stop.

### Step 2 — Check effective access

Run:

```bash
uip admin authorization check-access <USER_GUID> --scope Tenant --output json
```

For folder-level access, run:

```bash
uip admin authorization check-access <USER_GUID> --scope Folder --folder-id <FOLDER_UUID> --output json
```

Inspect `Data.roleAssignments[]`. Label every nested entry by `securityPrincipalType`: `User` with the queried id is a **direct** grant; `Group` is **inherited** through group membership. Record `roleName`, `ownerServiceName`, `scopeType`, and the grant's scope path for each granted role.

### Step 3 — Check group membership

When access is expected to arrive through a group, run:

```bash
uip admin groups list --output json
```

For each relevant group, run:

```bash
uip admin groups members list <GROUP_ID> --output json
```

If the user is absent from the group that carries the role, the gap is membership — not the role or its scope.

### Step 4 — Branch: missing permission, or right permission at the wrong scope

Look up the permission the denied action requires ([permission-catalog.md](authorization/permission-catalog.md#workflow-find-the-permission-governing-an-action)), then take the branch:

- **No effective role carries it** → [Cause A](diagnose/failure-modes.md#cause-a--the-permission-is-not-granted). Find a role that does with `roles list --service <SERVICE>` and `roles get <ROLE_ID>` (compare `ActionDetails[].Name`). To extend a custom role instead, re-fetch first and send the full action set — `roles update` is a PUT-style upsert (Rule 12).
- **A role carries it but the grant sits elsewhere** → [Cause B](diagnose/failure-modes.md#cause-b--the-permission-is-granted-at-the-wrong-scope). Verify `ownerServiceName` against the scope-path service segment (Rule 17). A `Tenant` role cannot provide folder-level access: use a `Project`-scoped role, or Orchestrator's own folder roles (`uip or roles`, `uipath-platform`).

### Step 5 — Diagnose and recommend

Report:
- **Principal:** `<displayName> (<email>) — <id>`
- **Current access:** roles, scopes, and whether each is direct or inherited
- **Missing:** the required permission, or the scope path the existing grant should sit at
- **Fix:** "Assign role X at scope Y", "Add user to group Z", or "Re-create the assignment at `<path>`" — present it; do not execute it

---

## Playbook 2 — "Suspicious login activity"

**Symptoms:** Failed logins, possible compromise, or unknown locations.

**Scope: `org`.** User Login, Robot Login, and External App Login events are org-level audit events under Identity → Authentication.

### Step 1 — Resolve the user

Run:

```bash
uip admin users list --search "<EMAIL>" --output json
```

Extract `id` for `--user-id`.

### Step 2 — Discover login event types

Run:

```bash
uip admin audit org sources --output json > /tmp/sources.json
```

Extract the User Login type GUID by running:

```bash
jq -r '.Data[] | select(.name == "Identity") | .eventTargets[] | select(.name == "Authentication") | .eventTypes[] | select(.name == "User Login") | .id' /tmp/sources.json
```

### Step 3 — Query login events

Run:

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

For each `Data.auditEvents[]`, check `status` (`0` = Success, `1` = Failure), parse the `clientInfo` JSON string for `ipAddress` and `ipCountry`, and use `createdOn` as the UTC timestamp. Flag multiple failures from different IPs, unexpected countries, or logins outside business hours.

---

## Playbook 3 — "IP restriction lockout"

**Symptoms:** Access fails from a new office or all users are blocked.

### Step 1 — Check enforcement status

Run:

```bash
uip admin ip-restriction enforcement get --output json
```

If `isEnabled` is `false`, investigate another cause.

### Step 2 — Check caller's IP

Run:

```bash
uip admin ip-restriction my-ip --output json
```

Use `Data.ipAddress` as the public IP seen by the platform.

### Step 3 — List allowed ranges

Run:

```bash
uip admin ip-restriction ip-ranges list --output json
```

Compare the caller's IP with every entry's CIDR range. If none covers it, identify that as the lockout cause.

### Step 4 — Check bypass rules

Run:

```bash
uip admin ip-restriction bypass-rules list --output json
```

Bypass rules exempt matching URL patterns. If the affected API endpoint matches one, investigate another cause.

### Step 5 — Resolution options

- Add the IP/CIDR by running: `ip-ranges create --name "<LOCATION>" --cidr <CIDR> --output json`
- Temporarily disable enforcement by running: `ip-restriction enforcement disable --output json` (if accessible from an allowed IP)
- If fully locked out, use the Portal recovery flow; no CLI bypass exists (Rule 32).

---

## Playbook 4 — "PAT or external app not working"

**Symptoms:** API calls return 401, a PAT stopped working, or an external app cannot authenticate.

### Step 1 — List PATs or external apps

For PATs, run:

```bash
uip admin pat list --output json
```

Check `expiration`; expired PATs return 401 silently. If a token is absent, it was revoked; revocation is a hard delete and has no `isRevoked` flag.

For external apps, run:

```bash
uip admin external-apps list --output json
```

### Step 2 — Verify scopes

Compare token or app scopes with the endpoint requirement. For example, an endpoint requiring `OR.Execution` fails when the token has only `OR.Folders.Read`. Re-create a PAT with the correct `--scope`.

### Step 3 — Check audit for revocation

Discover sources by running:

```bash
uip admin audit org sources --output json
```

Find the Identity source → PersonalAccessTokens or ExternalApps target, then query recent events by running:

```bash
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
