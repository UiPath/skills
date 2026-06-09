# Full Apply — Configure All Recommended Settings

Applies the entire compliance pack in one command. Backend creates and deploys all recommended policy settings.

**Note:** This configures settings recommended by ISO 42001. Your organization's auditor determines compliance status — UiPath does not certify compliance.

## Pre-condition

Coverage (posture analysis) has been run and presented. At least one policy has `status: "new"`.

## Confirmation

```
Configure recommended ISO 42001 settings on <tenantName>?

Settings to be configured:
  <list products from coverage where status == "new">

This improves your posture towards ISO 42001 by configuring recommended settings.
Proceed? (y/n)
```

Require `y`. Anything else: halt, no mutations.

## Apply

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --output json
```

`state enable` is idempotent — safe to call even if partially applied.

## Verify

```bash
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Parse `Data.active` (must be `true`) and `Data.policies[]` (policy UUIDs created).

## Report

```
ISO 42001 recommended settings configured on DefaultTenant.

Configured products:
  AI Trust Layer
  Development
  Robot
  StudioWeb

These settings improve your posture towards ISO 42001 requirements.
Pack active: iso-42001-2023 v3.0.0
```

## Org-scope deployment (all tenants)

When the user says "apply to all tenants", "organization-wide", or "entire org", use the organization scope. One command configures recommended settings across every tenant in the organization.

```bash
ORG_ID=$(grep '^UIPATH_ORGANIZATION_ID=' ~/.uipath/.auth | cut -d'=' -f2-)

# Run posture analysis at org scope first
uip gov compliance-packs state coverage organization $ORG_ID <packId> --output json

# Configure after confirmation
uip gov compliance-packs state enable organization $ORG_ID <packId> --output json
```

**Confirmation for org-scope:**

```
Configure ISO 42001 recommended settings across ALL tenants in your organization?
Organization: <UIPATH_ORGANIZATION_NAME from ~/.uipath/.auth>

<posture plan from coverage>

This applies recommended settings to every tenant. Your auditor determines compliance status.
Continue? (y/n)
```

Verify org-scope state:
```bash
uip gov compliance-packs state list organization $ORG_ID --output json
```

Report for org-scope:
```
ISO 42001 recommended settings configured across all tenants in <UIPATH_ORGANIZATION_NAME>.

These settings improve your posture towards ISO 42001 requirements.
```

## Error handling

| Error | Action |
|---|---|
| `state enable` → 4xx | Halt. Report error verbatim. Do NOT retry. |
| `Data.active != true` after enable | Unexpected — ask user to run `state get` manually and report the output. |
