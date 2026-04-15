---
confidence: medium
---

# Get Asset Failed — Robot Not Authenticated or Unlicensed

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed because the robot is not authenticated or not licensed against Orchestrator.

What this looks like:
- Error message contains `"You are not authenticated! Error code: 0"`
- Robot shows as `Connected, Unlicensed` in Orchestrator
- Only Background Process template jobs fail while RE-Framework jobs succeed (package version conflict)

What can cause it:
- Robot is not licensed in Orchestrator
- Machine key or client credentials do not match what is configured in Orchestrator
- `UiPath.System.Activities` package upgrade introduced an authentication regression (versions 20.10.1+ and 2021.10.5)
- Interactive sign-in not enabled for the tenant

What to look for:
- Robot connection status in the UiPath Assistant tray icon (Connected + Licensed vs Connected + Unlicensed)
- `UiPath.System.Activities` package version in the project
- Whether the issue started after a package upgrade

## Investigation

1. Check the UiPath Robot tray icon — verify it shows "Connected, Licensed".
2. If unlicensed, check the license assignment in Orchestrator > Tenant > Licenses.
3. Verify the robot's machine key or client credentials match what is configured in Orchestrator.
4. Check whether the issue started after a `UiPath.System.Activities` package upgrade — versions 20.10.1+ and 2021.10.5 introduced authentication regressions.
5. If only Background Process template jobs fail (not RE-Framework), the cause is likely a package version conflict.

## Resolution

- **If unlicensed:** assign a Runtime license to the robot in Orchestrator.
- **If machine key mismatch:** reconnect the robot using the correct key from Orchestrator > Machines.
- **If package regression:** downgrade `UiPath.System.Activities` to v20.4.x as a workaround, or update to the latest stable version.
- **If interactive sign-in not enabled:** enable "Allow both user authentication and robot key authentication" in Tenant Settings > Security.
