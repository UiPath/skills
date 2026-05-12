# Queue Recipe

Use the BPMN wrapper that matches the queue behavior.

| Operation | BPMN element | Extension type |
| --- | --- | --- |
| Create queue item and continue | `bpmn:sendTask` | `Orchestrator.CreateQueueItem` |
| Create queue item and wait for completion | `bpmn:serviceTask` | `Orchestrator.CreateAndWaitForQueueItem` |

The model may draft:

- Queue task wrapper, variables, payload mappings, outputs, and BPMN DI.
- Public-safe payload fields, reference, priority, deadline, and transaction metadata.
- Duplicate-reference and unavailable-queue error paths.

CLI or operator must resolve:

- Queue identity, folder binding, generated package resources, and any downstream callback contract.
- Tenant-specific queue names, queue IDs, and folder keys.

Do not model downstream processing implicitly. Add an explicit wait, callback, or follow-up task when the process needs a completion result.
