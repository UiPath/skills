# SDK Module Imports

Read this when writing TypeScript code that imports classes, types, or options from `@uipath/uipath-typescript`. The SDK uses subpath exports — service classes are **not** importable from the package root.

## Subpath → Exports

| Subpath | Classes |
|---------|---------|
| `@uipath/uipath-typescript/core` | `UiPath`, `UiPathError`, `UiPathSDKConfig`, `PaginationCursor`, `PaginationOptions`, `PaginatedResponse`, `NonPaginatedResponse` |
| `@uipath/uipath-typescript/entities` | `Entities`, `ChoiceSets` |
| `@uipath/uipath-typescript/tasks` | `Tasks` |
| `@uipath/uipath-typescript/maestro-processes` | `MaestroProcesses`, `ProcessInstances`, `ProcessIncidents` |
| `@uipath/uipath-typescript/cases` | `Cases`, `CaseInstances` |
| `@uipath/uipath-typescript/assets` | `Assets` |
| `@uipath/uipath-typescript/queues` | `Queues` |
| `@uipath/uipath-typescript/buckets` | `Buckets` |
| `@uipath/uipath-typescript/processes` | `Processes` |
| `@uipath/uipath-typescript/jobs` | `Jobs` |
| `@uipath/uipath-typescript/attachments` | `Attachments` |
| `@uipath/uipath-typescript/conversational-agent` | `ConversationalAgent`, `Exchanges`, `Messages` |

## Type Imports

Types, enums, and option interfaces are exported from the **same subpath** as their service class. Use `import type` for type-only imports:

```typescript
import type { AssetGetResponse } from '@uipath/uipath-typescript/assets';
import type { ProcessInstanceGetResponse } from '@uipath/uipath-typescript/maestro-processes';
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core';
```

## Anti-patterns

### Never import service classes from the package root

Service classes are only available via subpath imports. Root-level imports will fail at build time.

```typescript
// ❌ Wrong — service classes are not exported from the root
import { Entities } from '@uipath/uipath-typescript';

// ✓ Correct — use the subpath
import { Entities } from '@uipath/uipath-typescript/entities';
```

### Never use the deprecated dot-chain access pattern

The `sdk.entities.getAll()` style is deprecated. Use constructor dependency injection instead.

```typescript
// ❌ Wrong — dot-chain is deprecated
const items = await sdk.entities.getAll();

// ✓ Correct — constructor DI
const entities = new Entities(sdk);
const items = await entities.getAll();
```
