# Full Apply — Configure All Recommended Settings

Applies the entire compliance standard in one command. Backend creates and deploys all recommended settings.

**Note:** This configures settings recommended by ISO 42001. Your organization's auditor determines compliance status — UiPath does not certify compliance.

## Pre-condition

Coverage (posture analysis) has been run and presented. At least one policy has `status: "new"`.

## Confirmation

Build this table from `catalog.clauses[].editorialPolicies[].controls[]` filtered to products where `coverage.deploymentPolicies[].status == "new"`. Group settings by impact. For settings needing user-supplied values (flagged by `synthesize-formdata` notEmpty warnings), list them with a plain-English prompt.

```
Configure ISO 42001 settings on <tenantName>?

┌──────────┬─────────────────────────────────────────────────────┐
│ Impact   │ Settings                                            │
├──────────┼─────────────────────────────────────────────────────┤
│ High     │ <comma-separated displayNames of High settings,     │
│ (<N>)    │ truncated to first 3 + "N more">                    │
├──────────┼─────────────────────────────────────────────────────┤
│ Medium   │ <comma-separated displayNames, first 3 + "N more">  │
│ (<N>)    │                                                     │
├──────────┼─────────────────────────────────────────────────────┤
│ Low (<N>)│ <comma-separated displayNames>                      │
└──────────┴─────────────────────────────────────────────────────┘

⚠ <N> settings need values from you:
  • <controlDisplayName>  — <plain-English prompt for the value>
  • ...
(omit the ⚠ section if no settings need user-supplied values)

Proceed? (y/n)
```

Require `y`. Halt on anything else.

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
ISO 42001 settings configured on <tenantName> ✓

SUMMARY
┌───────────────────────────────────┬───────────┐
│ Settings before                   │ <N> / <T> │
│ Settings after                    │ <T> / <T> │
│ High impact settings configured   │ <N>       │
└───────────────────────────────────┴───────────┘

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation from catalog>                │
└──────────────────────┴──────────────────────────────────────────────┘
(omit the ⚠ table if no SKIPped controls)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
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
Configure ISO 42001 settings across ALL tenants in your organization?
Organization: <UIPATH_ORGANIZATION_NAME from ~/.uipath/.auth>

<posture plan from coverage>

This configures settings on every tenant. Your auditor determines compliance status.
Continue? (y/n)
```

Require `y`. Halt on anything else.

Verify org-scope state:
```bash
uip gov compliance-packs state list organization $ORG_ID --output json
```

Report for org-scope:
```
ISO 42001 settings configured across all tenants in <UIPATH_ORGANIZATION_NAME> ✓

Settings configured: <N> per tenant
Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <UIPATH_ORGANIZATION_NAME>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Error handling

| Error | Action |
|---|---|
| `state enable` → 4xx | Halt. Report error verbatim. Do NOT retry. |
| `Data.active != true` after enable | Unexpected — ask user to run `state get` manually and report the output. |
