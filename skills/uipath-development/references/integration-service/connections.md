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
| **`IsDefault`** | `Yes` or `No`. Prefer the default connection when multiple exist. |
| `Owner` | Who created the connection |
| `Folder` | Folder this connection belongs to |

---

## Selecting a Connection

### For Native Connectors

1. List connections for the connector
2. Pick the **default** connection (`IsDefault: Yes`)
3. Check if its **State** is `Enabled`
4. If not enabled → prompt user to choose another enabled connection
5. If no connections are enabled → prompt user to create a new one
6. If no connections exist → prompt user to create one

### For HTTP Fallback

1. List connections for `uipath-uipath-http`
2. Look for a connection whose **Name** contains the target vendor (case-insensitive substring match, e.g., "Apify" matches "Apify", "Apify - Prod", "My Apify Connection")
3. If one match → use it. If multiple matches → present options to the user.
4. If no match → present all existing HTTP connections and ask the user to choose, or offer to create a new one

> **Note:** Name-based matching is best-effort. If connection names don't follow vendor naming conventions, present all HTTP connections to the user.
