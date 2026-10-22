<!--skill-flavor:generic-event-import:start-->
```ts
// Studio Web has no ./connectors/ tree: import the descriptor `prepare` wrote.
import { RecordCreated, RecordUpdated } from './connectors-local/uipath-uipath-dataservice.ts';

// Start when a ContractRegistry record is created with dueDate before 2026-08-04.
.trigger(onEvent(RecordCreated, {
  object: 'ContractRegistry',
  filters: [{ field: 'dueDate', lessThan: '2026-08-04' }],
  connection: 'dataFabric', folder: 'shared',
}))

// Pause until a FileUploadVerify_20260618 record is updated.
.step('updated', waitForEvent(RecordUpdated, {
  object: 'FileUploadVerify_20260618', connection: 'dataFabric', folder: 'shared',
}))
```
<!--skill-flavor:generic-event-import:end-->
