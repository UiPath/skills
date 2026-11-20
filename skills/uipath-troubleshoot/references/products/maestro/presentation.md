# Maestro Presentation Rules

- **Instances** — display as BPMN process name (instance ID in parentheses only when needed for commands)
- **Incidents** — display as error code + error message. When referencing an incident by ID, use the `incidentId` field (not `id`). The API returns both: `id` is the record's internal GUID, `incidentId` is the user-facing identifier (same as `elementRunId`) shown in Maestro Instance Management.
- **Solutions** — display name, not solution key
- **Service tasks** — use the task name from the BPMN process, not the internal element ID (e.g., "Send Email task" not "Activity_EW6HNH")
- **Settings** — use UI labels from Maestro Instance Management, not API property names
- **Error codes** — always include both the numeric code and the human-readable message (e.g., "170002 — Failure in the Orchestrator Job")

## BPMN instance diagnosis

- **Fix owner** — in `Who:`, name the owner with one of these labels: `BPMN source` (the `.bpmn.ts`), `Generated package metadata`, `Integration Service enrichment`, `Cloud configuration`. Show all four labels, marking the ones not implicated.
- **Next action** — the owner's repair, then one read-only re-check written as a literal command with the real ids, e.g. `uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json`. Name it, do not run it. With no repair needed, the re-check alone is the next action.
- **Lifecycle steps** — retry, re-run, cancel, pause, resume, migrate, debug, run, upload, publish and deploy are never the next action. When one fits later, put it on its own line as a later decision.
- Do not ask the user for approval when the request says not to.
