# Disable — Remove Recommended Settings

Removes all policy deployments configured by the compliance pack.

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

If `Data.active == false` or 404: "ISO 42001 recommended settings are not currently configured on this tenant." Stop.

## Confirmation

```
This will remove all ISO 42001 recommended settings from <tenantName>.

Policies that will be removed:
  <list Data.policies[].policyType: Data.policies[].externalPolicyId>

Are you sure? (y/n)
```

Require `y`. Halt on anything else.

## Disable

```bash
uip gov compliance-packs state disable tenant $TENANT_ID <packId> --output json
```

## Report

"ISO 42001 recommended settings removed from `<tenantName>`. All associated policy deployments have been deleted."
