---
confidence: high
---

# No Machine With Unattended/NonProduction Runtimes (409, #2818)

## Context

What this looks like:
- HTTP 409 from Orchestrator surfaced by Maestro
- Error message: `Operation returned invalid status code '409'. Could not find a machine with Unattended or NonProduction runtimes in the current folder`
- Orchestrator error code `#2818`

What can cause it:
- Folder has no machine templates with Unattended or NonProduction runtime slots assigned
- Folder only has Test Runtimes but Maestro defaults to NonProduction runtime type (tracked historically as `MST-6775`)
- Tenant has no available runtime licenses
- Machines exist but are all currently busy or disconnected

What to look for:
- Folder `Machines` tab — what runtime types are assigned
- Tenant `License Management` — runtime allocation
- Package requirements in the Maestro process — which runtime type is selected

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. List machines in the folder: `uip or machines list --folder-key <folder-key> --output json` — check runtime slot types
3. Check tenant runtime license allocation: Orchestrator UI → **Tenant > License Management**
4. Check the Maestro process's package requirements for the configured runtime type

## Resolution

- **If folder has no compatible runtimes:** add a machine template with Unattended or NonProduction slots via **Folder > Machines**
- **If tenant only has Test Runtimes:** change the Maestro process's package requirements to a runtime type that matches what the tenant has — see [Managing Package Requirements](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-package-requirements#linking-execution-settings)
- **If no runtime licenses available:** allocate more in Tenant License Management or contact the UiPath account manager
- **If all machines busy/disconnected:** verify machine connectivity to Orchestrator; reduce concurrent load

## References

- [Forum: Error #2818](https://forum.uipath.com/t/could-not-find-a-machine-with-unattended-or-nonproduction-runtimes-in-the-current-folder-2818/297757)
- [Docs: Managing Package Requirements](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-package-requirements#linking-execution-settings)
