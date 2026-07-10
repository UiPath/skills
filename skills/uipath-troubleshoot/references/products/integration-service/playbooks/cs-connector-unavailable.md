---
confidence: high
---

# Connection Service — Connector Unavailable (CNS1001, CNS1002, CNS1004, CNS1075, CNS2045)

> **Fault bucket: 👤 A for `CNS1001`/`CNS1002`/`CNS1004` (wrong/missing/disabled connector — customer fixes the reference or enables the connector) · 🛠 B1 for `CNS1075`/`CNS2045` (the connector's deployment state on the platform side is broken — escalate).** The *connector* (the integration template) is the problem here, not any connection. If the error names a connection GUID instead of a connector key, you are in [cs-connection-not-found.md](./cs-connection-not-found.md), not this page.

## Context

What this looks like:
- HTTP `404`/`400` (or `409` for `CNS1075`) from Connection Service, message naming a **connector key**, e.g. *"Connector [uipath-atlassian-bitbucket] is invalid"*
- Automations or API calls referencing a connector by key/ID fail before any connection is touched

| Code | Name | Exact meaning | HTTP | Bucket |
|------|------|---------------|:---:|:---:|
| `CNS1001` | ConnectorKeyOrIdInvalid | The connector key/ID does not resolve in this tenant — typo, not-installed custom connector, or deprecated key. ⚠ Also **reused** for an invalid *trigger* lookup on one path — read the message. | 404 (400 on favourites paths) | 👤 A |
| `CNS1002` | ConnectorKeyOrIdMissing | Create-connection request omitted the connector | 400 | 👤 A |
| `CNS1004` | ConnectorDisabled | Connector exists but is disabled in the tenant | 400 | 👤 A (admin) |
| `CNS1075` | ConnectorNotDeployed | The connector's backing deployment was unpublished/superseded on the platform — the connection references a connector build that is no longer live. Deliberately surfaced as **409, non-retryable**. | 409 | 🛠 B1 |
| `CNS2045` | ConnectorDoesNotExist | Event-configuration flow could not find the connector element / valid event type for a connection ("Invalid event type shell received") | 400 | 🛠 B1 |

What can cause it:
- Hard-coded connector keys promoted across tenants/environments where the (custom) connector isn't installed
- A custom connector was deleted or renamed while automations still reference it
- Admin disabled the connector, or a governance policy did (a governance block is `CNS3001` — see [cs-permission-denied.md](./cs-permission-denied.md))
- `CNS1075`: a connector publish/unpublish race on the platform — the tenant's connection points at a connector version no longer deployed. Known after custom-connector re-publish flows.
- `CNS2045`: connector catalog drift — an event type or element referenced by an existing trigger/connection no longer exists in the connector's current version

What to look for:
- The connector key in the message — check the tenant's Integration Service → Connectors catalog for exactly that key
- Whether the connector is a **custom** connector (customer-built keys) vs a UiPath first-party key — custom keys explain cross-tenant not-found
- For `CNS1075`: whether a custom-connector publish/import happened recently in the tenant

## Investigation

1. **Confirm the connector's presence**: open the tenant's connector catalog (or `uip is connectors list` where available) and search the exact key from the message. Present → move to state checks; absent → the reference is stale/wrong.
2. **`CNS1004`**: connector present but disabled — identify who/what disabled it (tenant admin action or policy). If the intent is to use it, enable it; if the disable was a policy, route to governance.
3. **`CNS1075`**: do not advise retrying — the 409 is deliberately non-retryable. Verify whether the connector shows as published in the catalog. This state means platform-side deployment metadata and the connection disagree; collect the connection ID, connector key, and `traceId`.
4. **`CNS2045`**: identify the trigger/connection whose event configuration references the missing element or event type, and whether the connector was recently upgraded — the event type may have been removed between versions.
5. **The `CNS1001`-on-trigger trap**: if the failing operation is a *trigger* lookup and the message doesn't mention a connector, the code was reused for "trigger not found" — triage as [cs-trigger-operation-failed.md](./cs-trigger-operation-failed.md).

## Resolution

- **`CNS1001`/`CNS1002`:** fix the connector reference — install the custom connector in the target tenant, correct the key, or rebind the automation to an existing connector. For environment promotions, make connector installation part of the deployment checklist.
- **`CNS1004`:** tenant admin enables the connector (Integration Service → Connectors), or the automation moves off a deliberately disabled connector.
- **`CNS1075`:** escalate to the Integration Service owner team with the connector key, connection ID, and `traceId` — republishing the connector version or repairing the deployment mapping is a platform action. If the customer owns the custom connector, re-publishing the connector version from their side often restores the mapping.
- **`CNS2045`:** if a connector upgrade removed the event type, recreate the trigger against a currently supported event type; if nothing changed on the customer side, escalate as connector-catalog drift.
