---
confidence: high
---

# Maestro Service Disabled

## Context

What this looks like:
- Error opening any Maestro workflow
- Designer pane is blank in Studio Web
- Studio Web shows errors after a license change

What can cause it:
- License entitlement revoked by OMS silently disables the Maestro service on the tenant

## Investigation

1. Check if the Maestro service is enabled on the tenant admin dashboard
2. Check if the user's license includes Maestro access

## Resolution

- Re-enable the Maestro service from the Admin dashboard on the affected tenant
- Verify license options are correctly assigned
- Confirm all Maestro workflows can be opened after re-enabling
