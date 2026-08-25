---
confidence: medium
---

# Document Understanding — Not enabled on tenant / tenant key

## Context

A DU activity faults while resolving the Document Understanding tenant context — listing projects or retrieving the tenant key — before processing any document. The tenant either doesn't have DU enabled/licensed, or the tenant context couldn't be resolved.

What this looks like — verbatim:

- `Failed to fetch Document Understanding projects list. Please connect to a tenant that has Document Understanding enabled.` — the project list couldn't be retrieved; DU is not enabled/licensed on the connected tenant (or the robot is connected to the wrong tenant).
- `Couldn't retrieve a tenant key.` — the DU tenant key couldn't be obtained (auth/entitlement to DU not in place).
- `Information about tenant <id> couldn't be retrieved.` — tenant metadata lookup failed.

What can cause it:
- **DU not enabled / licensed on the tenant** — the tenant has no Document Understanding entitlement, so the project list / tenant key can't be resolved.
- **Wrong tenant** — the robot is connected to a tenant other than the one where DU is set up.
- **Auth / entitlement gap** — the running identity can't obtain the DU tenant key.

What to look for:
- These fire at **setup / tenant resolution**, not on a per-document endpoint call. There is no HTTP status / `DUApiException` here — it's a tenant-enablement problem, not a license-key-on-endpoint problem.

> **Different cause — do not apply this playbook:**
> - `DUApiException` with an HTTP status (401/403/400/...) → the tenant resolved and an **endpoint** call was rejected → use [du-license-or-endpoint-rejected.md](./du-license-or-endpoint-rejected.md).
> - `No such bucket ...` / `Could not find Orchestrator Folder ...` → storage/folder access → use [du-storage-or-taxonomy-missing.md](./du-storage-or-taxonomy-missing.md).

## Investigation

1. **Confirm the message** is the projects-list / tenant-key / tenant-info form (no HTTP status).
2. **Identify the connected tenant** and confirm whether Document Understanding is enabled/licensed on it.
3. **Confirm the robot is connected to the intended tenant** — not a different tenant that lacks DU.

## Resolution

- **If `Failed to fetch Document Understanding projects list. Please connect to a tenant that has Document Understanding enabled.`:** enable / license Document Understanding on the tenant, or connect the robot to the tenant where DU is set up.
- **If `Couldn't retrieve a tenant key.` / `Information about tenant <id> couldn't be retrieved.`:** confirm DU entitlement and that the running identity can resolve the tenant context; re-check the tenant connection. Escalate to the DU/tenant admin if the entitlement is present but the key still can't be retrieved.
