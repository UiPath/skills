# Solution

UiPath Solution management — creating, structuring, packing, publishing, deploying, and activating solutions.

## Overview

A Solution groups multiple automation projects (processes, libraries, tests) into a single deployable unit. Solutions enable bundled deployment, version management, configuration management, and multi-environment promotion.

## Lifecycle

```
Create → Add Projects → Pack → Publish → Deploy → Activate
```

## Solution Structure

```
MySolution/
├── MySolution.uipx                      ← Solution definition
├── SolutionStorage.json                 ← Project ID → path mapping
├── solutionResourcesDefinition.json     ← Resource declarations (queues, connections, assets)
├── .uipath/
│   ├── config.json                      ← Environment-specific config
│   └── sync.json                        ← Cloud sync state
├── resources/                           ← Shared resources (schemas, data contracts)
├── ProjectA/
│   ├── project.json
│   └── ...
└── ProjectB/
    └── ...
```

## Resource Declarations

Solutions declare platform resource dependencies in `solutionResourcesDefinition.json`. These are provisioned during deployment:

| Resource Kind | Example |
|---|---|
| Asset | API keys, configuration values |
| Queue | Work item queues for distributed processing |
| Connection | Integration Service connections |
| Storage Bucket | File storage for automation data |

## Commands

| Command | Purpose |
|---|---|
| `uip solution new` | Create empty solution (.uipx) |
| `uip solution project add` | Add project to solution |
| `uip solution project remove` | Remove project from solution |
| `uip solution pack` | Package into deployable .zip |
| `uip solution publish` | Upload to UiPath |
| `uip solution deploy run` | Deploy to target environment |
| `uip solution deploy status` | Check deployment status |
| `uip solution packages list` | List published packages |

## See Also

- Full command syntax and examples: [solution-guide.md](solution-guide.md)
- CI/CD pipeline setup: [solution-guide.md - CI/CD](solution-guide.md)
- CLI reference: [../cli/uip-commands.md - Solution](../cli/uip-commands.md)
