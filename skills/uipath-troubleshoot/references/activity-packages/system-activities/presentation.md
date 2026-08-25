# System Activities Presentation Rules

- **Activities** — use the display name (e.g., "Get Asset", "Get Credential"), not the fully qualified class name (e.g., `UiPath.Core.Activities.GetAsset`)
- **Assets** — refer to assets by their Orchestrator name and type (e.g., "asset 'ApiBaseUrl' (Text)"), not by variable names used in the workflow
- **Credentials** — refer to credentials by their Orchestrator name (e.g., "credential 'SAPLogin'"), not by the username or password variable names
- **Folders** — use the full folder path as shown in Orchestrator (e.g., "Production/Finance"), not internal IDs
- **Robots** — refer to robots by their display name or username, not by machine key or internal ID
