# Connections

Connections are authenticated sessions for a specific connector. They store credentials and tokens, and can be shared across automations within a folder.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Response Fields

| Field | Description |
|---|---|
| **`Id`** | Connection ID (used in `--connection-id` for all operations) |
| `Name` | Display name (e.g., "Salesforce Prod", "Apify") |
| `ConnectorKey` | The connector this connection belongs to |
| **`State`** | `Enabled` or other status. Only Enabled connections can be used. |
| **`IsDefault`** | `Yes` or `No`. Recommend the default connection but always let the user confirm. |
| `Owner` | Who created the connection |
| `ByoaConnection` | `Yes` or `No`. Whether this is a BYOA (Bring Your Own Account) connection — the customer registered their own OAuth app with the external service. Required for some webhook triggers. |
| `ElementInstanceId` | Numeric instance ID for this connection's element. Used with `uip is webhooks config` to retrieve webhook URLs. |
| `Folder` | Folder this connection belongs to |

---

## Selecting a Connection

**Always present connections to the user** — do not auto-select silently, even if there is only one default enabled connection. Recommend the default but let the user confirm.

### For Native Connectors

1. List connections for the connector
2. Present all enabled connections to the user, **recommending** the default (`IsDefault: Yes`, `State: Enabled`):
   - "I found these connections: 1) **Salesforce Prod** (default, enabled) ← recommended 2) Salesforce Dev (enabled). Which should I use?"
3. If only one enabled connection exists, still confirm: "I found connection **<name>** (default, enabled). Should I use this one?"
4. If not enabled → prompt user to re-authenticate via `is connections edit <id>`
5. If no connections exist → prompt user to create one via `is connections create "<connector-key>"`

### For BYOA Connections (Webhook Triggers)

Some webhook triggers require a BYOA (Bring Your Own Account) connection — the customer must have registered their own OAuth app with the external service. The `byoaConnection` flag on the trigger objects response indicates this requirement.

1. Filter to BYOA connections only:

   ```bash
   uip is connections list "<connector-key>" --byoa --output json
   ```

2. If no BYOA connections exist, tell the user they need to create one in the Integration Service portal
3. BYOA connections have `ByoaConnection: Yes` in the response

### For HTTP Fallback

1. List connections for `uipath-uipath-http`
2. Look for a connection whose **Name** contains the target vendor (case-insensitive substring match, e.g., "Apify" matches "Apify", "Apify - Prod", "My Apify Connection")
3. Present matches to the user. If multiple matches → let them choose.
4. If no match → present all existing HTTP connections and ask the user to choose, or offer to create a new one

> **Note:** Name-based matching is best-effort. If connection names don't follow vendor naming conventions, present all HTTP connections to the user.

---

## Scope-Related Errors

A connection can be `Enabled` but lack optional OAuth scopes needed for specific activities. This typically surfaces as a **403 Forbidden** error during execute.

**Symptoms:**
- Connection pings successfully (`State: Enabled`)
- Execute fails with 403 or a vendor-specific "insufficient permissions" error
- The same operation works with a different connection that has broader scopes

**Recovery:**
1. Inform the user that the connection may need broader OAuth scopes for this activity
2. Re-authorize with broader scopes: `uip is connections edit <connection-id>`
3. After re-auth, ping again to verify, then retry the operation
