---
confidence: medium
---

# Deployment Failure

## Context

What this looks like:
- Solution deployment fails with various errors
- Errors during publish or deploy from Studio Web to Orchestrator

What can cause it:
- Duplicate entry points — multiple start points with the same ID cause deployment or runtime 404 errors
- Cross-tenant solution deployment trigger conflicts (SOL-6121) — deploying to a tenant that already has triggers from a previous version
- Manually deleted triggers from Orchestrator UI creating stale ServiceKey references and duplicate trigger name errors
- IS/packaging sync issues (see specific playbooks for EMAIL_RECEIVED, DateTime inputs)

What to look for:
- Check the specific error code and message
- Check if this is a fresh deployment or an upgrade of an existing solution
- Check if triggers were manually modified in Orchestrator UI

## Investigation

1. Get the exact deployment error message and code
2. Check for duplicate entry points in the BPMN process
3. Check if triggers were manually deleted from Orchestrator UI before this deployment
4. For cross-tenant deployments: check if the target tenant already has triggers from a previous version
5. For upgrade deployments: verify no manual trigger modifications were made outside Studio Web

## Resolution

- **If duplicate entry points:** delete the duplicate start points in Studio Web and republish
- **If cross-tenant trigger conflict (SOL-6121):** deploy to a fresh tenant as a workaround; fix scheduled for s190 release
- **If stale trigger references:** do not manually delete triggers from Orchestrator UI; redeploy the solution cleanly
