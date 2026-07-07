# SDK Module Imports

Read this when writing TypeScript code that imports classes, types, or options from `@uipath/uipath-typescript`. The SDK uses subpath exports — service classes are **not** importable from the package root.

## Method Signatures — Read the Installed Types, Never Guess

Authoritative reference for method signatures, parameters, return types, and usage examples: the installed SDK's type declarations at

```
node_modules/@uipath/uipath-typescript/dist/<subpath>/index.d.ts
```

Full JSDoc (descriptions, `@param`, `@example`) ships in these files, and they match the **installed** SDK version exactly — hand-written docs cannot make that guarantee. Per-subpath files are small (≈500–2,400 lines); read the one for the service you are using before calling methods you have not used in this session.

1. Before calling a service, Read `dist/<subpath>/index.d.ts` for its exact method signatures.
2. If `node_modules` is absent, run the install step first (the app cannot build without it — see the scaffold workflow).
3. NEVER guess or recall method names from memory — SDK versions differ; the `.d.ts` of the installed version is the contract.
4. Scopes: if `node_modules/@uipath/uipath-typescript/docs/oauth-scopes.md` exists (newer SDK versions ship it), it is the version-exact per-method scope reference — prefer it. If absent, use [../oauth-scopes.md](../oauth-scopes.md). Scope *bundles* (which scopes an app needs for a given feature set) are always in [../oauth-scopes.md](../oauth-scopes.md).

The remaining files in this `sdk/` folder deliberately do NOT duplicate signatures. They cover only what the `.d.ts` cannot tell you: OAuth scopes per method ([../oauth-scopes.md](../oauth-scopes.md)), calling conventions, response-shape gotchas, and cross-service traps.

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
| `@uipath/uipath-typescript/agents` | `Agents`, `AgentListSortColumn`, `AgentErrorSortColumn` (Insights RTM — SDK ≥ 1.4.1) |
| `@uipath/uipath-typescript/traces` | `AgentTraces`, `AgentTraceExecutionType`, `Traces` (generic spans — `Traces.getById(traceId)`) (Insights RTM — SDK ≥ 1.4.1) |
| `@uipath/uipath-typescript/agent-memory` | `AgentMemory`, `AgentMemoryExecutionType` (SDK ≥ 1.4.1) |
| `@uipath/uipath-typescript/governance` | `Governance`, `PolicyEvaluationResult` (SDK ≥ 1.4.1) |
| `@uipath/uipath-typescript/conversational-agent` | `ConversationalAgent`, `Exchanges`, `Messages` |
| `@uipath/uipath-typescript/feedback` | `Feedback` |

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
