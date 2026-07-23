# Diagnostic Priority Ladder

Sequential triage workflow for governance policy failures. Work through in order — stop when you have enough to diagnose.

## Step 1: Identify the Policy Branch

Determine whether the symptom belongs to AOps (product-layer) or Access (tool-use) based on user description:

| Symptom | Branch | Next step |
|---------|--------|-----------|
| "Policy not enforced in Studio/Assistant/Robot" | AOps | Step 2 (check deployed) |
| "Wrong rules applied to a product" | AOps | Step 2 (check deployed) |
| "Policy not taking effect for a user/group" | AOps | Step 3 (check precedence) |
| "Agent/Flow blocked from invoking a process" | Access | Step 4 (evaluate) |
| "Tool invocation going through when it shouldn't" | Access | Step 4 (evaluate) |
| "Policy create/update rejected" | Either | Step 5 (inspect definition) |
| "Deployed-policy returns empty" | AOps | Step 2 (check deployed) |

If the branch is unclear, ask the user: "Is this about product behavior (Studio/Robot features) or tool invocation (one workflow calling another)?" See [disambiguation-guide.md](../../disambiguation-guide.md).

## Step 2: Check What's Deployed

For AOps policy issues, start by querying the effective deployed policy.

Get the effective policy for a `(license type, product, tenant)` tuple:
```bash
uip gov aops-policy deployed-policy get \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --output json
```

List every applicable policy in priority order:
```bash
uip gov aops-policy deployed-policy list \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --output json
```

Interpret:
- `Data` present with `policyIdentifier` → a policy applies. Verify it matches the expected one.
- `Data` is `null` / `{}` / `{ "Message": "No policy applies." }` → no policy applies. See [failure modes → Deployed policy returns empty](failure-modes.md#deployed-policy-returns-empty).
- `Data` is an array (on `list`) → inspect `source` column (User/Group/Tenant) to understand where each policy comes from.

If the policy does not exist at all, check whether it was created:
```bash
uip gov aops-policy list --output json
```

## Step 3: Check Precedence

AOps deployment precedence: **User > Group > Tenant**. A user-level assignment always wins.

Check each scope level:
```bash
uip gov aops-policy deployment user get "$USER_ID" --output json
uip gov aops-policy deployment group get "$GROUP_ID" --output json
uip gov aops-policy deployment tenant get "$TENANT_ID" --output json
```

Compare the assignments at each level for the target product:
- If a user override exists (including explicit `null`), it wins over group and tenant.
- If a group override exists, it wins over tenant for members of that group.
- If the user belongs to **multiple groups** with different policies, the group with the **lower priority number wins** (lower = more important). Compare group priorities to identify which policy takes effect.
- A `null` override means explicit "No Policy" — it is NOT the same as "no assignment" (which would inherit from the next level).

List all deployment subjects to find unexpected overrides:
```bash
uip gov aops-policy deployment user list --output json
uip gov aops-policy deployment group list --output json
uip gov aops-policy deployment tenant list --output json
```

## Step 4: For Access — Evaluate with Test Inputs

For access-policy issues, `evaluate` is the primary diagnostic tool.

```bash
uip gov access-policy evaluate \
  --resource-type "<RESOURCE_TYPE>" \
  --resource-id "<RESOURCE_UUID>" \
  --actor-process-type "<ACTOR_PROCESS_TYPE>" \
  --actor-process-id "<ACTOR_PROCESS_UUID>" \
  --output json
```

Interpret `Data.enforcement`:
- `Allow` → policy working as intended; the invocation is permitted.
- `Deny` → a policy is blocking. Inspect `Data.effectivePolicies[]` for the blocking policy ID.
- `NoOp` → no policy matched. Either no policy covers this context (expected with untagged/unknown resources) or the selector/actor/executable rules don't match.

Fetch the blocking or candidate policy:
```bash
uip gov access-policy get "<POLICY_ID>" --output json
```

List all active policies:
```bash
uip gov access-policy list --filter "status in ('Active')" --output json
```

Check whether a robot/external-app actor is involved — `actorRule` only matches `User`/`Group`. See [plugins/actor/impl.md](../../access-policy/plugins/actor/impl.md).

## Step 5: Inspect the Policy Definition

When the deployment and evaluate steps don't reveal the issue, inspect the policy definition itself.

For AOps:
```bash
uip gov aops-policy get "<POLICY_ID>" --output json
```

Verify:
- `data` payload contains the expected rules for the product
- Product identifier matches the deployment target
- Template structure is valid

For Access:
```bash
uip gov access-policy get "<POLICY_ID>" --output json
```

Verify:
- `status` is `Active` (not `Inactive`)
- `selectors[].resourceType` matches the target resource type
- `selectors[].values` includes `["*"]` (required even when tags narrow scope)
- `executableRule` covers the actor process type
- `actorRule` (if present) includes the calling user/group
- `enforcement` is `Allow` (only authorable value)
- `organizationId` and `tenantId` match the current context

## Outputs

After completing the relevant steps, present:
1. **Root cause** — what specifically failed and why
2. **Evidence** — which CLI commands confirmed the diagnosis
3. **Fix ownership** — whether the fix requires redeployment, policy editing, scope change, or policy creation
4. **Recommended action** — specific next step (do not execute; present for user approval)
