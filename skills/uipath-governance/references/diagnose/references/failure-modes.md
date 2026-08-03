# Failure Modes — Governance Policies

Named failure patterns with symptom → cause → investigation → fix. Match the user's symptom to a pattern, then follow the investigation steps.

---

## Policy Not Taking Effect (Deployment Precedence Issue)

**Symptom:** Admin deployed a policy to a tenant (or group), but a specific user still sees the old behavior or no policy at all.

**Causes:**
1. A user-level assignment overrides the group/tenant assignment (user > group > tenant)
2. A group-level assignment overrides the tenant assignment for members of that group
3. User belongs to multiple groups with different policies — the group with the **lower priority number wins** (lower = more important)
4. User has an explicit `null` (No Policy) override at a narrower scope
5. Policy deployed to wrong subject (e.g. wrong group ID)

**Investigation:**
1. Check effective policy for the user:
   ```bash
   uip gov aops-policy deployed-policy get \
     "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
     --output json
   ```
2. List all applicable policies to see the full chain:
   ```bash
   uip gov aops-policy deployed-policy list \
     "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
     --output json
   ```
3. Check user-level override:
   ```bash
   uip gov aops-policy deployment user get "$USER_ID" --output json
   ```
4. Check group-level override:
   ```bash
   uip gov aops-policy deployment group get "$GROUP_ID" --output json
   ```
5. Check tenant-level assignment:
   ```bash
   uip gov aops-policy deployment tenant get "$TENANT_ID" --output json
   ```

**Fix:** Cause 1/2 → remove the narrower-scope override (`deployment user delete` or `deployment group delete`) or update it to match intent. Cause 3 → lower the priority number of the intended group's policy to make it win (lower priority = more important). Cause 4 → remove the explicit `null` override. Cause 5 → redeploy to the correct subject after resolving the right ID.

---

## Wrong Policy Applied (License-Type Mismatch)

**Symptom:** Tenant has a policy deployed but the wrong rules are enforced — or a policy has no effect on certain users.

**Causes:**
1. Policy deployed to wrong `(product, license type)` pair — e.g. Assistant policy on `Unattended Robot` license (which has no Assistant slot)
2. User's actual license type differs from the one the policy was deployed to
3. Multiple license types exist and only one has the policy

**Investigation:**
1. List license types to see available options:
   ```bash
   uip gov aops-policy license-type list --output json
   ```
2. Check tenant deployment to see which `(product, licenseType)` pairs have assignments:
   ```bash
   uip gov aops-policy deployment tenant get "$TENANT_ID" --output json
   ```
3. Verify the product is included in the target license type (see [aops-policy-deploy-guide.md — License-type → product compatibility](../../aops-policy/aops-policy-deploy-guide.md#license-type--product-compatibility)).

**Fix:** Cause 1 → redeploy to a license type that includes the target product. Cause 2 → deploy to the license type the affected users actually hold. Cause 3 → deploy to all relevant license types.

---

## Access Policy Blocking Legitimate Tool Invocation

**Symptom:** Agent, Flow, or automation reports "denied" or fails to invoke a child resource that should be allowed.

**Causes:**
1. Selector rule too broad — matches resources beyond the intended scope
2. Actor rule excludes the calling user/group
3. Executable rule blocks the actor process type
4. Tags on the resource or executable trigger a deny-intent policy
5. Robot/ExternalApplication actor — `actorRule` only matches `User`/`Group`, so robot actors return `NoOp` on all policies with `actorRule`

**Investigation:**
1. Evaluate the exact request context:
   ```bash
   uip gov access-policy evaluate \
     --resource-type "<RESOURCE_TYPE>" \
     --resource-id "<RESOURCE_UUID>" \
     --actor-process-type "<ACTOR_PROCESS_TYPE>" \
     --actor-process-id "<ACTOR_PROCESS_UUID>" \
     --output json
   ```
2. Inspect `Data.enforcement` and `Data.effectivePolicies[]` to identify which policy contributed.
3. Fetch the blocking policy:
   ```bash
   uip gov access-policy get "<POLICY_ID>" --output json
   ```
4. List all active access policies:
   ```bash
   uip gov access-policy list --filter "status in ('Active')" --output json
   ```

**Fix:** Cause 1 → narrow selector `resourceType`/`tags`. Cause 2 → add the calling user/group to `actorRule`. Cause 3 → add the actor process type to `executableRule`. Cause 4 → adjust tags on the resource or policy. Cause 5 → see [plugins/actor/impl.md — Robot intent](../../access-policy/plugins/actor/impl.md) for the User-fallback pattern.

---

## Access Policy Not Blocking

**Symptom:** Expected a deny/restrict behavior but the invocation goes through. `evaluate` returns `NoOp` or `Allow` when `Deny` was expected.

**Causes:**
1. No policy matches the request context (selector/actor/executable don't cover it)
2. Policy status is `Inactive` (not enforced)
3. Tags on the resource don't match the selector's tag filter
4. Policy uses `enforcement: "Allow"` (the only authorable value) — deny intent requires targeting what should be allowed, not what should be blocked
5. `evaluate` called with wrong resource-type or actor-process-type enum

**Investigation:**
1. Evaluate:
   ```bash
   uip gov access-policy evaluate \
     --resource-type "<RESOURCE_TYPE>" \
     --resource-id "<RESOURCE_UUID>" \
     --output json
   ```
2. List policies and check status:
   ```bash
   uip gov access-policy list --output json
   ```
3. Inspect each candidate policy's selectors, executableRule, and actorRule:
   ```bash
   uip gov access-policy get "<POLICY_ID>" --output json
   ```
4. Verify the resource's tags in the Resource Catalog match the selector's tag filter.

**Fix:** Cause 1 → broaden selector or add a new policy covering the gap. Cause 2 → update status to `Active`. Cause 3 → correct tags on resource or policy. Cause 4 → reframe deny intent as allow-only (see [plugins/tags/planning.md — Deny-to-Allow flip](../../access-policy/plugins/tags/planning.md#deny-to-allow-flip)). Cause 5 → use correct enum values from [plugins/selector/impl.md](../../access-policy/plugins/selector/impl.md).

---

## Deployed Policy Returns Empty

**Symptom:** `deployed-policy get` returns `null`, `{}`, `{ "Message": "No policy applies." }`, or HTTP 204. `deployed-policy list` returns `[]`.

**Causes:**
1. No policy deployed at any scope (user/group/tenant) for this `(license type, product, tenant)` tuple
2. Policy deployed to wrong tenant ID
3. Policy deployed to wrong product name or license type
4. User/group has an explicit `null` override (No Policy) and no fallback exists

**Investigation:**
1. Check tenant deployment:
   ```bash
   uip gov aops-policy deployment tenant get "$TENANT_ID" --output json
   ```
2. List all tenants with deployments:
   ```bash
   uip gov aops-policy deployment tenant list --output json
   ```
3. Verify the product name matches exactly:
   ```bash
   uip gov aops-policy product list --output json
   ```
4. Check user-level override:
   ```bash
   uip gov aops-policy deployment user get "$USER_ID" --output json
   ```

**Fix:** Cause 1 → deploy a policy via [aops-policy-deploy-guide.md](../../aops-policy/aops-policy-deploy-guide.md). Cause 2 → redeploy to the correct tenant. Cause 3 → use the product `name` (not label) from `product list`. Cause 4 → remove the `null` override or deploy a policy at a broader scope.

---

## Policy Create/Update Rejected

**Symptom:** `aops-policy create` or `access-policy create/update` returns 400, validation errors, or rejects the JSON payload.

**Causes:**
1. Invalid `productIdentifier` — used label instead of `name`
2. Malformed JSON (missing required fields, wrong types)
3. Access policy: `enforcement: "Deny"` used (only `Allow` is authorable)
4. Access policy: `Selectors[].Values` missing `["*"]`
5. Access policy: name collision (409 Conflict)
6. AOps policy: invalid template structure

**Investigation:**
1. For AOps — verify product identifier:
   ```bash
   uip gov aops-policy product list --output json
   ```
2. For AOps — verify template structure:
   ```bash
   uip gov aops-policy template list --output json
   uip gov aops-policy template get "<PRODUCT_NAME>" --output json
   ```
3. For Access — validate JSON structure:
   ```bash
   jq type "<POLICY_FILE>"
   jq '.[0] | keys' "<POLICY_FILE>"  2>/dev/null || jq 'keys' "<POLICY_FILE>"
   ```
4. For Access — check error message in response `Data.errors`.

**Fix:** Cause 1 → use `name` from `product list`. Cause 2 → fix JSON (validate with `jq`). Cause 3 → switch to `enforcement: "Allow"`. Cause 4 → add `"values": ["*"]` to selector entries. Cause 5 → choose a different name. Cause 6 → regenerate from template via [configure-aops-policy-data-guide.md](../../aops-policy/configure-aops-policy-data-guide.md).
