# HITL Recipe

The current supported implementation wrapper for confirmed Action Center human
work is `bpmn:userTask` with `Actions.HITL`.

The model may draft:

- User task wrapper, variable mappings, boundary timer/error paths, and post-task gateways.
- Public-safe form field names, outcome variable names, and decision routes.
- Placeholder-safe assignment or routing intent when the user explicitly provides it.

CLI or operator must resolve:

- Real Action Center app/form, folder, queue, group, user, and notification metadata.
- Dynamic form schemas and generated resources.

No personal names, email addresses, tenant URLs, or exported form payloads should appear in authored examples.
