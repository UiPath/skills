---
confidence: medium
---

# Trigger Not Firing

## Context

What this looks like:
- Integration Service trigger is configured but events don't start jobs or Maestro instances
- External events occur but no corresponding execution is created
- Trigger appears configured correctly in the UI

What can cause it:
- Connection used by the trigger is inactive or expired
- Robot account lacks "Triggers" permission in the folder (not just "Connections.View")
- Trigger subscription was not created or was deleted in the external service
- Event payload doesn't match the trigger's expected schema or object type
- For Maestro: the trigger was configured in debug mode with `debug_overwrites.json` bindings that don't apply in deployed mode

What to look for:
- Check connection status for the trigger's connector
- Check folder permissions for the robot account
- Check if the trigger subscription exists in the external service
- Compare debug vs deployed trigger configuration

## Investigation

1. **Read the connection resource file** — if source code is available, find and read the connection JSON (see "Connection Resource File" in [overview.md](../overview.md)) to identify the connector and connection
2. `uip is connections ping <connection-id>` — verify the connection is active
3. Check folder permissions for the robot account — verify "Triggers" permission exists
4. `uip is triggers objects <connector-key> <operation>` — verify the trigger object type is correct
5. Check if the issue is debug-only or deploy-only (identity and bindings differ)

## Resolution

- **If connection inactive:** re-authenticate via `uip is connections edit <connection-id>`
- **If permission missing:** grant "Triggers" permission to the robot account in the target folder
- **If trigger object mismatch:** reconfigure the trigger with the correct object type and operation
- **If debug-vs-deploy issue:** verify `bindings_v2.json` folder bindings match the folder where the connection and trigger are configured
