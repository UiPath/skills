---
confidence: high
---

# No Suitable Runtime Machine (409)

## Context

What this looks like:
- HTTP 409 error
- "No suitable runtime machine" or no available machine with required runtimes

What can cause it:
- No Unattended or NonProduction robots available in the folder
- All machines are currently busy or disconnected

## Investigation

1. Check robot/machine availability in the target folder
2. Check machine connectivity to Orchestrator

## Resolution

- Provision additional Unattended/NonProduction robots in the folder
- Check and resolve connectivity issues with Orchestrator machines
- Review and optimize robot allocation policies
