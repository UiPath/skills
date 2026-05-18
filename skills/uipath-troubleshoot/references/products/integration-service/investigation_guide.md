# Integration Service Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Connection identity** — the connection name and connector type match what the error message or user referenced
- **Folder** — connections can be folder-scoped; verify you're looking at the connection in the correct folder
- **Connector vs Connection** — a connector is the template (e.g., "uipath-microsoft365-o365"), a connection is an authenticated instance. Errors reference connections, not connectors.
- **Caller context** — determine whether the connection was called from an Orchestrator workflow, a Maestro BPMN process, or a Studio debug session. The calling identity (user vs robot account) affects permissions.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## First Step: Identify the Connection AND its Ownership

Always identify the specific connection AND determine where it lives before doing anything else. From the project's connection resource file (see "Connection Resource File" in [overview.md](./overview.md) for path pattern and field reference), you must answer four questions:

- **Which connector?**
- **Who owns the connection?**
- **Where is the connection bound?**
- **What is the connection ID?**

Together these answers determine whether the connection is in the runner's workspace, in a different user's workspace, or in a folder the runner cannot reach. **Always extract and compare them — do not stop after just the connector name.**

For the field-by-field extraction checklist for a specific error pattern, see the matched playbook's Investigation section — the playbook is authoritative for which fields and which comparisons matter for that error.

If no source code is available, the error message usually names the connection. Use `uip is connections list` to find it by name, then `uip is connections ping <connection-id>` to check its status. Without the resource file, ownership cannot be confirmed without asking the user.

**Do NOT infer the connector from the activity package name** — activity packages and connectors have different naming conventions (e.g., `UiPath.MicrosoftOffice365.Activities` uses connector "Microsoft OneDrive & SharePoint"). Always resolve from connection resource files or the connections API.

If the connection identity is still unclear, ask the user which connection or connector is involved.

## Domain-Specific Data Gathering

After the Orchestrator job data bundle (job details, logs, traces) is collected and the connection is identified:

1. **Connection status** — `uip is connections ping <connection-id>` to check if it's active
2. **Connection details** — `uip is connections list` to find connector type, status, and folder scope
3. **Connection resource file** — if source code is available, read the connection resource JSON from the project (see "Connection Resource File" in [overview.md](./overview.md) for path pattern)

## Testing Prerequisites

When testing hypotheses for Integration Service issues, gather and verify these before drawing conclusions:

1. **Connection status** — ping the connection to check if it's active and enabled (`uip is connections ping <id>`)
2. **Connection details** — list the connection to see its connector type, status, and folder scope
3. **Caller identity** — determine if the caller is a user (debug mode) or robot account (deployed mode). Robot accounts may lack permissions the user has.
4. **Folder permissions** — verify the caller has access to the folder where the connection resides. For Maestro triggers, the robot account needs "Triggers" permission, not just "Connections.View".
5. **OAuth token state** — if the connection uses OAuth, check whether the token may have expired or been revoked. A ping failure after a period of working correctly suggests token expiry.
6. **External service availability** — if the connection pings successfully but operations fail, the issue may be on the external service side (API changes, rate limits, outages)
