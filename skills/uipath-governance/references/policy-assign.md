# Policy Assign — tenant / group / user deployment

Primitive: bind created policies to scopes. Used by **Apply** (Phase 2 deployment) and **Advise** (when creating a new policy with group/user scope).

> ## ⚠ The full-replace contract
>
> **`deployment tenant|group|user configure` is a FULL REPLACE, not a merge.** The API (`tenantSaveTenantPolicies` / `groupSaveGroupPolicies` / `userSaveUserPolicies`) rewrites the entire assignment list for the target. Entries you omit are **deleted**.
>
> The previous `assign-tenant` / `assign-group` / `assign-user` CLI commands are gone. They had a known bug where sequential single-policy calls would wipe prior assignments — "last deploy wins." The new `configure` commands take one JSON array with every (product, licenseType, policyId) triple, submitted in a single atomic call, which fixes the bug but requires the caller to construct the complete final state.
>
> **Always read current state first, merge in new assignments, then configure.**

## Input contract (orchestrator → this primitive)

```jsonc
{
  "scope": {
    "level":      "tenant | group | user",
    "targetId":   "<GUID — tenant, group, or user>",
    "targetName": "<human name — required for tenant/group configure>"
  },
  "assignments": [
    {
      "productIdentifier":     "AITrustLayer",
      "licenseTypeIdentifier": "NoLicense",
      "policyIdentifier":      "<policy GUID>"   // or null to pin 'No Policy'
    },
    ...
  ]
}
```

## Recipe

### Step 1 — Read current state

```bash
# For tenant:
uip gov aops-policy deployment tenant get "<targetId>" --output json

# For group:
uip gov aops-policy deployment group get "<targetId>" --output json

# For user:
uip gov aops-policy deployment user get "<targetId>" --output json
```

Response includes `tenantPolicies[]` / `groupPolicies[]` / `userPolicies[]` — each entry is a `(productIdentifier, licenseTypeIdentifier, policyIdentifier)` triple. Entries with no `policyIdentifier` or `policyIdentifier: null` mean no custom policy is pinned at that scope.

### Step 2 — Merge current + new into the final assignment list

Rules:

| Case | Resolution |
|---|---|
| New assignment for `(productA, licenseA)` matches existing entry with same triple | Replace `policyIdentifier` with new value. |
| New assignment for `(productA, licenseA)` with no prior entry | Add to list. |
| Prior entry for `(productB, licenseB)` not mentioned in new assignments | **Keep it** (preserve existing state). |
| Caller explicitly wants to unpin `(productA, licenseA)` | Include it with `policyIdentifier: null` (or omit to leave inherited). |

The merge happens in the orchestrator, not here. This primitive just accepts the final array.

### Step 3 — Write JSON input file

```bash
tmpDir="$(mktemp -d)"
inputFile="$tmpDir/deployment-input.json"
# assignments is a pure JSON array — no outer object
printf '%s' '[
  { "productIdentifier": "AITrustLayer", "licenseTypeIdentifier": "NoLicense", "policyIdentifier": "<guid>" },
  { "productIdentifier": "Robot",        "licenseTypeIdentifier": "Attended",  "policyIdentifier": "<guid>" }
]' > "$inputFile"
```

### Step 4 — Call configure

#### Tenant

```bash
uip gov aops-policy deployment tenant configure "<targetId>" \
  --tenant-name "<targetName>" \
  --input "$inputFile" \
  --output json
```

`--tenant-name` is the tenant display name (e.g., `DefaultTenant`) from `UIPATH_TENANT_NAME` in `~/.uipath/.auth`. Must match the tenant's governance-service record.

#### Group

```bash
uip gov aops-policy deployment group configure "<targetId>" \
  --group-name "<targetName>" \
  --input "$inputFile" \
  --output json
```

#### User

```bash
uip gov aops-policy deployment user configure "<targetId>" \
  --user-name "<targetName>" \
  --input "$inputFile" \
  --output json
```

Confirm exact flag names for group/user with `--help` on first run — the tenant variant uses `--tenant-name` and the others should follow the same pattern, but verify before assuming.

## License-type awareness

Every assignment carries a `licenseTypeIdentifier`. A given product may have multiple license-type slots (Robot has `Attended`, `Unattended`, `Development`, `StudioX`, `StudioPro`) and you can pin a different policy per license type.

Enumerate available license types via:

```bash
uip gov aops-policy license-type list --output json
```

When applying a compliance pack, use the license type from the pack's policy file. If the pack doesn't specify, use `NoLicense` for cloud-native tenant-level products (AITrustLayer, AssistantWeb) and consult the product's supported license types otherwise.

## Return shape (from caller's perspective)

```jsonc
{
  "status": "success" | "failed",
  "scope":  { "level": "...", "targetId": "...", "targetName": "..." },
  "mergedAssignmentCount":   <N>,         // final size of the assignment list
  "addedAssignmentCount":    <M>,         // new ones added this call
  "replacedAssignmentCount": <K>,         // prior entries whose policyIdentifier changed
  "warnings": []
}
```

## Error map

| HTTP / message | Action |
|---|---|
| `400` — invalid license type / product identifier | Halt. Verify via `license-type list` / `product list`. |
| `400` — assignment array shape | Halt. Each entry must have all three fields: `productIdentifier`, `licenseTypeIdentifier`, `policyIdentifier` (or `null`). |
| `401 / 403` | Halt. Permission — user may not have assignment rights. |
| `404` | Halt. Target (tenant/group/user) not found — check the GUID. |
| `5xx` | Retry once after 3s. |

## Resolution order at runtime

AOPS resolves `USER → GROUP → TENANT → GLOBAL` at request time. This primitive creates the binding at one scope; effective-policy resolution for a request is handled by the backend. Verify the effective state after a large apply with:

```bash
uip gov aops-policy deployed-policy get <licenseType> <productName> "$UIPATH_TENANT_ID" --output json
```
