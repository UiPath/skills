# Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Platform & Experiences connectors (e.g., Salesforce, Jira, ServiceNow), explore the connector's capabilities before writing XAML:

```bash
# What activities does this connector offer?
uip ipe activities list <connector-key> --format json

# What data objects/resources does it expose?
uip ipe resources list <connector-key> --format json

# What fields does a specific resource have? (essential for configuring dynamic activity properties)
uip ipe resources describe <connector-key> <object-name> --format json
```

## Connection Management

**Check if a connection exists:**
```bash
uip ipe connections list <connector-key> --format json
```

**If no connection exists**, you have two options:
1. **Create one** (requires user interaction for OAuth): `uip ipe connections create <connector-key>`
2. **Use a placeholder** — insert the dynamic activity with an empty `connectionId` and inform the user they need to configure the connection in Studio

**Verify a connection is active:**
```bash
uip ipe connections ping <connection-id>
```

If the ping fails, offer to re-authenticate: `uip ipe connections edit <connection-id>`
