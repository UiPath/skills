# HITL Recipe

Use this pass-2 recipe for confirmed Action Center human work. In pass 1, model
the human decision or data-entry step in the BPMN skeleton; apply this recipe
after the skeleton is chosen and the human task should receive UiPath metadata.

The current supported implementation wrapper is `bpmn:userTask` with
`Actions.HITL`.

The model may draft:

- User task wrapper, variable mappings, boundary timer/error paths, and post-task gateways.
- Public-safe form field names, outcome variable names, and decision routes.
- Placeholder-safe assignment or routing intent when the user explicitly provides it.

CLI or operator must resolve:

- Real Action Center app/form, folder, queue, group, user, and notification metadata.
- Dynamic form schemas and generated resources.

No personal names, email addresses, tenant URLs, or exported form payloads should appear in authored examples.
