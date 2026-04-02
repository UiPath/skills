# Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Service connectors (e.g., Salesforce, Jira, ServiceNow), explore the connector's capabilities before writing XAML:

```bash
# What activities does this connector offer?
uip is activities list <connector-key> --output json

# What data objects/resources does it expose?
uip is resources list <connector-key> --output json

# What fields does a specific resource have? (essential for configuring dynamic activity properties)
uip is resources describe <connector-key> <object-name> --output json
```

## Connection Management

**Check if a connection exists:**
```bash
uip is connections list <connector-key> --output json
```

**If no connection exists**, you have two options:
1. **Create one** (requires user interaction for OAuth): `uip is connections create <connector-key>`
2. **Use a placeholder** — insert the dynamic activity with an empty `connectionId` and inform the user they need to configure the connection in Studio

**Verify a connection is active:**
```bash
uip is connections ping <connection-id>
```

If the ping fails, offer to re-authenticate: `uip is connections edit <connection-id>`
