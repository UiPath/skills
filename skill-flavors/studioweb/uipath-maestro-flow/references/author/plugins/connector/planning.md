<!--skill-flavor:connector-intro:start-->
Connector activity nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded — not built-in — and appear in the registry after `uip maestro flow registry pull` (auth is host-provided).
<!--skill-flavor:connector-intro:end-->

<!--skill-flavor:connector-prerequisites:start-->
- Auth is host-provided — connector nodes appear in the registry after `registry pull`; a 401/403 means the signed-in user lacks rights
- A healthy IS connection must exist for the connector — if none exists, the user must create one before proceeding
- `uip maestro flow registry pull` must be run to cache connector node types locally
<!--skill-flavor:connector-prerequisites:end-->
