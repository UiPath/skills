# Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Service connectors (e.g., Salesforce, Jira, ServiceNow), explore the connector's capabilities before writing XAML:

```bash
# What activities does this connector offer?
uipcli is activities list <connector-key> --format json

# What data objects/resources does it expose?
uipcli is resources list <connector-key> --format json

# What fields does a specific resource have? (essential for configuring dynamic activity properties)
uipcli is resources describe <connector-key> <object-name> --format json
```

## Connection Management

**Check if a connection exists:**
```bash
uipcli is connections list <connector-key> --format json
```

**If no connection exists**, you have two options:
1. **Create one** (requires user interaction for OAuth): `uipcli is connections create <connector-key>`
2. **Use a placeholder** — insert the dynamic activity with an empty `connectionId` and inform the user they need to configure the connection in Studio

**Verify a connection is active:**
```bash
uipcli is connections ping <connection-id>
```

If the ping fails, offer to re-authenticate: `uipcli is connections edit <connection-id>`
