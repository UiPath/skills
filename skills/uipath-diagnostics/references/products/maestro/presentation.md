# Maestro Presentation Rules

- **Instances** — display as BPMN process name (instance ID in parentheses only when needed for commands)
- **Incidents** — display as error code + error message. When referencing an incident by ID, use the `incidentId` field (not `id`). The API returns both: `id` is the record's internal GUID, `incidentId` is the user-facing identifier (same as `elementRunId`) shown in Maestro Instance Management.
- **Solutions** — display name, not solution key
- **Service tasks** — use the task name from the BPMN process, not the internal element ID (e.g., "Send Email task" not "Activity_EW6HNH")
- **Settings** — use UI labels from Maestro Instance Management, not API property names
- **Error codes** — always include both the numeric code and the human-readable message (e.g., "170002 — Failure in the Orchestrator Job")
