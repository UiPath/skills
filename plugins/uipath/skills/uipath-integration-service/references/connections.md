# Connections

Connections are authenticated sessions for a specific connector. They store credentials and tokens, and can be shared across automations within a folder.

---

## List Connections

```bash
# List all connections across all connectors
uipcli is connections list --format json

# List connections for a specific connector
uipcli is connections list "<connector-key>" --format json

# Filter by folder
uipcli is connections list --folder-key "<GUID>" --format json

# Filter by specific connection ID
uipcli is connections list --connection-id "<ID>" --format json

# Force refresh (bypass cache)
uipcli is connections list "<connector-key>" --refresh --format json
```

> **Cache behavior:** Results are cached locally. If expected connections are not found, retry with `--refresh` to fetch latest from API.

### Response Fields

| Field | Description |
|---|---|
| `Id` | Connection ID (used in `--connection-id` for operations) |
| `Name` | Display name (e.g., "Salesforce Prod", "Apify") |
| `ConnectorKey` | The connector this connection belongs to |
| `State` | `Enabled` or other status. Only Enabled connections can be used. |
| `IsDefault` | `Yes` or `No`. Prefer the default connection when multiple exist. |
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
2. Look for a connection whose **Name** matches the target vendor
3. If found → use it
4. If not found → prompt user to choose from existing or create new

> **NEVER guess or hallucinate connection IDs.** Always list and select from real data.

---

## Create a Connection

Opens an OAuth flow in the browser:

```bash
uipcli is connections create "<connector-key>" --format json
```

For headless environments (prints the auth URL instead of opening a browser):
```bash
uipcli is connections create "<connector-key>" --no-browser --format json
```

**Example:**
```bash
# Find the connector key
uipcli is connectors list --filter "slack" --format json
# → Key: "uipath-salesforce-slack"

# Create the connection
uipcli is connections create "uipath-salesforce-slack" --format json
```

---

## Ping a Connection (Verify Health)

**Always ping before any operation.** A connection may report "Enabled" but the token may be expired or revoked.

```bash
uipcli is connections ping "<connection-id>" --format json
```

| Ping Result | Action |
|---|---|
| Returns `Enabled` | Connection is healthy. Proceed to use it. |
| Returns other status or fails | Try re-authenticating, choose different connection, or create new. |

---

## Edit a Connection (Re-authenticate)

Re-authenticate an existing connection. Opens the OAuth flow:

```bash
uipcli is connections edit "<connection-id>" --format json
```

Use this when:
- A ping returns non-enabled status
- The connection's OAuth token has expired
- The user changed their credentials

After editing, always **ping again** to verify:
```bash
uipcli is connections ping "<connection-id>" --format json
```

---

## Connection Lifecycle

```
List connections
  ├── Found (enabled) → Ping → Healthy → Use it
  ├── Found (disabled) → Edit (re-auth) → Ping → Use it
  ├── Found (multiple) → Prompt user to choose → Ping → Use it
  └── Not found → Create → Ping → Use it
```
