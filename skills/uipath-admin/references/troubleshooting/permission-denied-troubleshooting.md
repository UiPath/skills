# Permission Denied Troubleshooting

Diagnostic workflows for authorization failures (HTTP 403, missing permissions, role assignment issues). Uses the Authorization PDP (`check-access`) as the primary investigation tool.

## Playbook 6: User Gets HTTP 403 (Permission Denied)

**Symptom:** User or integration receives 403 when calling a platform API or performing a UI action.

1. Resolve the user's identity:
   ```bash
   uip admin users list --search "<USER_EMAIL>" --output json
   ```
   Record the user's `id` (UUID).

2. Check effective access at the relevant scope:
   ```bash
   uip admin authorization check-access "<USER_ID>" --output json
   ```
   For a specific service (narrows the result):
   ```bash
   uip admin authorization check-access "<USER_ID>" \
     --service orchestrator --output json
   ```

3. Compare effective permissions against the required permission:
   - Find the required permission: `uip admin authorization permissions list --service <SERVICE> --output json`
   - If the permission is absent from `check-access` results → user lacks a role granting it

4. Identify the gap:
   - **No role at all for the service** → assign one: `uip admin authorization roles assignments create --role-id <ROLE_ID> --identity-id <USER_ID> --identity-type User --output json`
   - **Role exists but at wrong scope** (e.g., role assigned at org level but needed at tenant) → create assignment at correct scope
   - **Role exists but missing the specific action** → update the custom role's actions, or assign an additional role that includes the action

5. Label each result as `direct` or `inherited from <Group>` — see [check-access.md](../authorization/check-access.md#direct-vs-inherited--always-surface-the-distinction) for the interpretation rules.

## Playbook 7: Role Assignment Not Taking Effect

**Symptom:** Admin assigned a role to a principal but the principal still cannot perform the expected action.

1. Verify the assignment exists:
   ```bash
   uip admin authorization roles assignments list \
     --filter "<PRINCIPAL_NAME>" --output json
   ```

2. Inspect the role definition:
   ```bash
   uip admin authorization roles get "<ROLE_ID>" --output json
   ```
   Check `ownerServiceName` and `scopeType`.

3. Validate ownerServiceName vs scope-path (SKILL.md Rule 17):
   - `CentralizedAccess` → scope-path has no service segment (`/` or `/tenant/<tid>`)
   - Any other value → scope-path MUST include `lowercase(ownerServiceName)` as a segment
   - **Mismatch here is the most common cause** of "assigned but not working"

4. Check scope level alignment:
   - Role `scopeType: TenantGlobal` → applies as a template across all tenants. If user needs access on a specific tenant only, use a `Tenant`-scoped role instead.
   - Role `scopeType: Tenant` → applies only on the specific tenant where assigned
   - If assigned at wrong tenant → re-assign at the correct one

5. Verify via PDP:
   ```bash
   uip admin authorization check-access "<PRINCIPAL_ID>" --output json
   ```
   If role does NOT appear in `check-access` results despite assignment existing → the ownerServiceName/scope-path mismatch or scope-level issue is confirmed.

6. Check role's actions:
   - The role may be assigned correctly but not contain the needed permission action
   - Compare `roles get` response's actions array against `permissions list --service <SERVICE>` to verify the action exists and is included

## Playbook 8: Cross-Service Permission Confusion

**Symptom:** "I have a role in Orchestrator but can't access DU projects" or "CentralizedAccess role doesn't grant service-specific permissions."

1. Check effective access **without** service filter to see the full picture:
   ```bash
   uip admin authorization check-access "<USER_ID>" --output json
   ```

2. Then check with a specific service filter:
   ```bash
   uip admin authorization check-access "<USER_ID>" \
     --service documentunderstanding --output json
   ```

3. Compare the two results:
   - Permissions are **service-scoped** — an Orchestrator role does NOT grant DU access
   - Each service has its own permission catalog: `uip admin authorization permissions list --service <SERVICE> --output json`

4. Verify the role's `ownerServiceName` matches the service the user needs access to:
   - `ownerServiceName: CentralizedAccess` → cross-service role (authz-native permissions only, not service-specific permissions like `OR.Folders.Create`)
   - `ownerServiceName: Orchestrator` → only Orchestrator permissions
   - `ownerServiceName: Reinfer` → only IXP permissions

5. Resolution: assign a role owned by the correct service, or create a new custom role scoped to that service with the needed actions.
