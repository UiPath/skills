# Queue Planning

Use this reference when planning Orchestrator queue interactions from BPMN. Queue create is `bpmn:sendTask`; create-and-wait queue work is `bpmn:serviceTask`. See [task-recipes/queue.md](../../task-recipes/queue.md).

## When to use

- Creating queue items.
- Routing based on queue submission results.
- Adding transaction metadata or references.
- Using queue work as a handoff to another automation.

## Planning steps

1. Identify queue operation and whether BPMN only creates an item or also waits for downstream completion.
2. Define item payload, reference, priority, deadline, and result variables.
3. Plan queue resource binding with placeholders unless a public-safe binding is provided.
4. Add error handling for duplicate references, validation failures, and unavailable queues.
5. Keep downstream processing outside BPMN unless explicitly modeled as a wait or callback.

## Model may draft

- `bpmn:sendTask` with documented `Orchestrator.CreateQueueItem` shell, or `bpmn:serviceTask` with `Orchestrator.CreateAndWaitForQueueItem`.
- Queue payload CDATA with synthetic fields.
- Output mappings and error paths.
- Placeholder-safe binding references.

## Stop conditions

Stop before Operate when the queue resource, folder scope, payload schema, or retry/error behavior is unresolved.
