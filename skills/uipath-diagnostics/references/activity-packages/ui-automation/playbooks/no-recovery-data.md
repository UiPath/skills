---
confidence: low
---

# Healing Agent — No Recovery Data

## Context

Healing Agent is enabled but no recovery data was generated after a UI automation failure.

What this looks like:
- Job faulted with a UI automation exception
- AutopilotForRobots shows Enabled: true, HealingEnabled: true
- But `healing-fixes.json` is empty or doesn't exist
- No files in `healing-agent/uia/` directory

What to look for:
- Confirm HA is enabled by checking both `AutopilotForRobots.Enabled` and `AutopilotForRobots.HealingEnabled` (both must be true)
- Do NOT rely on the legacy `EnableAutopilotHealing` field — it can be false even when HA is properly enabled
- Check if the failure activity type is UIAutomation (HA only works with UI activities)

What can cause it:
- The activity uses classic UI automation (`UiPath.UIAutomation.*`) — HA may have limited support for classic activities depending on version
- The failure happened before HA could capture the UI tree (application crashed, window closed)
- The robot machine lost connectivity to Semantic Proxy / LLM Gateway during recovery attempt
- HA analysis timed out — the UI tree was too complex or the LLM response was too slow
- The activity uses image-based targeting which HA doesn't support for recovery
- The robot does not have the required permissions to upload the files

## Resolution

- Verify the activity uses modern UI activities (`UiPath.UIAutomationNext.*`) for full HA support
- Check Semantic Proxy and LLM Gateway health on the deployment
- Check robot machine connectivity to cloud services and has the correct permisions
- If HA consistently fails to produce data, escalate to platform team with the job ID and robot logs
