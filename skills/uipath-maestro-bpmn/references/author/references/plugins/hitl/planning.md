# HITL Planning

Use this reference when planning human-in-the-loop Action Center tasks in BPMN. HITL is `bpmn:userTask`, not a generic service task. See [task-recipes/hitl.md](../../task-recipes/hitl.md).

## When to use

- Human approval, validation, enrichment, or exception handling.
- A task must pause the process until a person completes work.
- Outcomes route the process through gateways.
- Escalation or timeout paths are required.

## Planning steps

1. Define the human decision or data entry outcome.
2. Decide required inputs, task payload, outputs, assignee/routing intent, due date, and escalation behavior.
3. Plan result variables and gateway routes after completion.
4. Add timeout or cancellation paths when the process cannot wait indefinitely.
5. Use public-safe placeholders for queues, groups, folders, apps, and task titles.
6. Confirm whether any Action Center resource must be resolved by tooling or the operator.

## Model may draft

- `bpmn:userTask` wrapper and `Actions.HITL` shell when the contract is documented.
- Input/output mappings and outcome routes.
- Boundary timeout/error paths.
- Public-safe labels and diagram geometry.

## Stop conditions

Stop before Operate when real assignee, folder, app, task form, schema, or resource binding is unresolved.
