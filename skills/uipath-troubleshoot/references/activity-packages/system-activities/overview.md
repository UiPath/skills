# System Activities

Core workflow activities from the `UiPath.System.Activities` package that interact with Orchestrator resources at runtime. These activities are used inside workflows to read and write platform data — assets, credentials, queue items, storage buckets, and job metadata.

## Key Activity Types

- **Get Asset / Get Orchestrator Asset** — retrieve a text, integer, boolean, or JSON asset value from Orchestrator
- **Get Credential / Get Orchestrator Credential** — retrieve a username/password pair from Orchestrator (returns `String` + `SecureString`)
- **Get Robot Asset** — retrieve an asset value scoped to the executing robot (legacy; replaced by Get Orchestrator Asset in modern folders)
- **Add Queue Item / Add Transaction Item** — push items into Orchestrator queues
- **Get Transaction Item** — pull the next item from a queue for processing
- **Set Asset** — update an asset value in Orchestrator
- **Set Credential** — update a credential in Orchestrator

## Common Failure Patterns

- Asset or credential not found (name mismatch, wrong folder)
- Permission denied (robot account lacks View/Edit on Assets)
- Wrong activity for the asset type (Get Asset on a Credential, or vice versa)
- Folder scope mismatch (modern vs classic folders, incorrect `OrchestratorFolderPath`)
- External credential store unreachable (CyberArk, Azure Key Vault, Thycotic)
- Robot not authenticated or not licensed
- Network/TLS issues between robot and Orchestrator

## Package

NuGet: `UiPath.System.Activities`

Version-specific bugs are documented in the relevant playbooks.
