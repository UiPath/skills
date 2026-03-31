# Maestro Presentation Rules

- **Instances** — display as BPMN process name (instance ID in parentheses only when needed for commands)
- **Incidents** — display as error code + error message. Reference the incident ID only when needed for commands.
- **Solutions** — display name, not solution key
- **Service tasks** — use the task name from the BPMN process, not the internal element ID (e.g., "Send Email task" not "Activity_EW6HNH")
- **Settings** — use UI labels from Maestro Instance Management, not API property names
- **Error codes** — always include both the numeric code and the human-readable message (e.g., "170002 — Failure in the Orchestrator Job")
