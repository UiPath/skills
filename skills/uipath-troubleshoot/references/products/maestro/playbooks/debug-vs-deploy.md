---
confidence: medium
---

# Process Works in Debug But Fails After Deploy

## Context

What this looks like:
- Process runs successfully in debug mode but fails after publishing/deploying
- Errors only appear in deployed mode, not during Studio Web debugging

What can cause it:
- Debug runs under the user's identity; deployed runs under the robot account which may lack folder-level permissions (Triggers, Connections.View, asset access)
- Robot/Studio version incompatibility — file type handling changed between Studio Desktop 24.10 and newer versions; agents expect File objects with metadata that older Robot versions do not produce
- `debug_overwrites.json` redirects folder bindings during debug; deployed mode resolves against the actual folder structure via `bindings_v2.json`
- For agent + index scenarios: context indexes accessible to the user account may not be accessible to the robot account
- For Integration Service triggers: the robot account needs "Triggers" permission in the folder where the connection resides, not just "Connections.View"

What to look for:
- Compare which identity runs in debug vs deployed (user vs robot account)
- Check folder permissions for the robot account
- Check Robot version compatibility

## Investigation

1. Identify the error message in deployed mode
2. Check robot account permissions in the target folder — specifically Triggers, Connections.View, asset access
3. Compare Robot version against Studio Web version requirements
4. Check `bindings_v2.json` for folder binding references and compare against actual folder structure
5. For agent tasks: verify context indexes are accessible to the robot account
6. For IS triggers: verify "Triggers" permission on the robot account in the connection folder

## Resolution

- **If permission issue:** grant the robot account the required permissions in the target folder
- **If version mismatch:** upgrade Robot to the latest version
- **If folder binding issue:** fix `bindings_v2.json` references to point to correct folders
- **If context index access:** grant robot account access to the required context indexes
