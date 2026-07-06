# Agent Feedback Reference — Scopes, Traps

Method signatures, parameters, return types, and usage examples: read the installed types — `node_modules/@uipath/uipath-typescript/dist/feedback/index.d.ts` (full JSDoc; matches your installed SDK version). This file covers ONLY what the `.d.ts` cannot tell you.

## Imports

```typescript
import { Feedback } from '@uipath/uipath-typescript/feedback';
```

Types, options, and enums export from the same subpath as their service class.

## Scopes

`Traces.Api` — for **every** method (reads, writes, and category management).

## Traps

- **`options.folderKey` is required** on `getById`, `submit`, `updateById`, and `deleteById` — get it from a `getAll()` item or wherever the feedback originated.
- `getAll()` returns one page — see [pagination.md](pagination.md) for cursor-loop retrieval if the source has more rows than the server's default cap.
- Default categories (Output, Agent Error, Agent Plan Execution) are auto-created per tenant. Default tenant categories cannot be removed via `deleteCategory()`.
- `createCategory()`: `isPositive?` defaults `true`, `isNegative?` defaults `true` — set the flags to scope the category to one rating direction.
