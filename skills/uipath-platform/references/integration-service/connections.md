# Connections

Connections are authenticated sessions for a specific connector. They store credentials and tokens, and can be shared across automations within a folder.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## Response Fields

| Field | Show to user? | Description |
|---|---|---|
| **`Name`** | **Yes** | Display name — always use this as the primary identifier when presenting to the user (e.g., "Salesforce Prod", "bai.li") |
| **`State`** | **Yes** | `Enabled` or other status. Only Enabled connections can be used. |
| **`IsDefault`** | **Yes** | `Yes` or `No`. Recommend the default connection but always let the user confirm. |
| **`Owner`** | **Yes** | Who created the connection (email) |
| **`Folder`** | **Yes** | Folder name this connection belongs to (e.g., "Shared", "Personal") |
| `ConnectorName` | **Yes** | Human-readable connector name (e.g., "Slack", "Salesforce") |
| `ByoaConnection` | **Yes** | `Yes` or `No`. BYOA (Bring Your Own Account) connection — customer registered their own OAuth app with the external service. Required for some webhook triggers. |
| `Id` | Internal | Connection UUID — use only in `--connection-id` CLI args, never show to user |
| `ConnectorKey` | Internal | Connector key — use only in CLI args |
| `FolderKey` | Internal | Folder UUID — use only in `--folder-key` CLI args, never show to user |
| `ElementInstanceId` | Internal | Numeric instance ID — use only in `--element-instance-id` for `uip is webhooks config` |

---

## Selecting a Connection

**Always present connections to the user** — do not auto-select silently, even if there is only one default enabled connection. Recommend the default but let the user confirm.

### For Native Connectors

1. List connections for the connector
2. Present all enabled connections to the user using **Name, Owner, and Folder** (never UUIDs), **recommending** the default (`IsDefault: Yes`, `State: Enabled`):
   - "I found these connections: 1) **Salesforce Prod** by user@example.com (default, enabled, Shared folder) ← recommended 2) **Salesforce Dev** by admin@example.com (enabled, Shared folder). Which should I use?"
3. If only one enabled connection exists, still confirm: "I found connection **<Name>** by <Owner> in **<Folder>** folder (default, enabled). Should I use this one?"
4. If not enabled → prompt user to re-authenticate via `is connections edit <id>`
5. If no connections exist → retry with `--refresh` (`uip is connections list "<connector-key>" --refresh --output json`) to bypass the CLI cache. If still empty, prompt user to create one via `is connections create "<connector-key>"`.

### For BYOA Connections (Webhook Triggers)

BYOA (Bring Your Own Account) connections use an OAuth app the customer registered with the external service (e.g., a Slack app they own). Some webhook triggers require BYOA; many do not. **The requirement is per event object, not per connector** — read it from the `triggers objects` response.

**Decision flow:**

1. Get any enabled connection — needed only as `--connection-id` for the next call:

   ```bash
   uip is connections list "<connector-key>" --output json
   ```

2. Query trigger objects and read the `byoaConnection` flag for the matching event:

   ```bash
   uip is triggers objects "<connector-key>" "<OPERATION>" \
     --connection-id "<id>" --output json
   ```

3. **If `byoaConnection: true`** — the connection from step 1 is not usable. Filter to BYOA only:

   ```bash
   uip is connections list "<connector-key>" --byoa --output json
   ```

   If empty, retry with `--refresh` to bypass the CLI cache:

   ```bash
   uip is connections list "<connector-key>" --byoa --refresh --output json
   ```

   If still empty, **stop and tell the user**: "This trigger requires a BYOA connection for `<connector-key>`. None found. Create one in the Integration Service portal or with `uip is connections create "<connector-key>"`, then re-run."

4. **If `byoaConnection: false`** — use the connection from step 1. Verify health with `uip is connections ping "<id>" --output json`.

> Connector-specific OAuth-app setup instructions (e.g., what permissions a Slack app needs) come from the trigger's `design.textBlocks` field in the `triggers objects` response. Surface that text to the user verbatim — do not invent service-specific guidance.

For webhook URL retrieval after the trigger is configured, see [triggers.md — Webhook URL Retrieval](triggers.md#webhook-url-retrieval).

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
