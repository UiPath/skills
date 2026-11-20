# Maestro Presentation Rules

- **Instances** — display as BPMN process name (instance ID in parentheses only when needed for commands)
- **Incidents** — display as error code + error message. When referencing an incident by ID, use the `incidentId` field (not `id`). The API returns both: `id` is the record's internal GUID, `incidentId` is the user-facing identifier (same as `elementRunId`) shown in Maestro Instance Management.
- **Solutions** — display name, not solution key
- **Service tasks** — use the task name from the BPMN process, not the internal element ID (e.g., "Send Email task" not "Activity_EW6HNH")
- **Settings** — use UI labels from Maestro Instance Management, not API property names
- **Error codes** — always include both the numeric code and the human-readable message (e.g., "170002 — Failure in the Orchestrator Job")

## BPMN instance diagnosis

- **Fix owner** — in the Immediate fix `Who:`, name the owner with one of these labels: `BPMN source` (the `.bpmn.ts`), `Generated package metadata` (the files `refresh` writes), `Integration Service enrichment` (connector metadata, connection binding, dynamic schemas), `Cloud configuration` (folder, process, release, connection state on the tenant). List all four, marking the ones not implicated.
