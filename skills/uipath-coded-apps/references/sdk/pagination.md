# Pagination Reference

## Imports

Import pagination types from `@uipath/uipath-typescript/core`:

```typescript
import type {
  PaginationCursor,
  PaginationOptions,
  PaginatedResponse,
  NonPaginatedResponse,
} from '@uipath/uipath-typescript/core';
```

- `PaginationCursor`: `{ value: string }` — an opaque cursor object. Pass it to `cursor` in pagination options.
- `PaginationOptions`: `{ pageSize?, cursor?, jumpToPage? }` (cursor and jumpToPage are mutually exclusive)
- `PaginatedResponse<T>`: `{ items, hasNextPage, nextCursor?, previousCursor?, totalCount?, currentPage?, totalPages?, supportsPageJump }`
- `NonPaginatedResponse<T>`: `{ items, totalCount? }`

## Behavior

- No pagination options passed -> returns `NonPaginatedResponse<T>`
- Any pagination option passed (pageSize, cursor, or jumpToPage) -> returns `PaginatedResponse<T>`

## Cursor Navigation

```typescript
// First page
const page1 = await service.getAll({ pageSize: 10 });

// Next page using cursor
if (page1.hasNextPage && page1.nextCursor) {
  const page2 = await service.getAll({ cursor: page1.nextCursor });
}

// Jump to page (only for offset-based services: Assets, Queues, Tasks, Entities)
const page5 = await service.getAll({ jumpToPage: 5, pageSize: 10 });
```

## Type Narrowing

TypeScript narrows the return type at compile-time based on whether pagination options are passed. At runtime, use `'hasNextPage' in result` to discriminate — this field exists only on `PaginatedResponse`, never on `NonPaginatedResponse`.

```typescript
import type { PaginatedResponse } from '@uipath/uipath-typescript/core';

// Pattern 1: When you always pass pagination options, assert the type
const result = await tasks.getAll({ pageSize: 10 });
// TypeScript already infers PaginatedResponse here, but if using dynamic options:
const paginated = result as PaginatedResponse<TaskGetResponse>;

// Pattern 2: When options are dynamic and you don't know the return type
const result = await tasks.getAll(options);
if ('hasNextPage' in result) {
  // PaginatedResponse — safe to access nextCursor, supportsPageJump, etc.
  if (result.hasNextPage && result.nextCursor) {
    const nextPage = await tasks.getAll({ cursor: result.nextCursor });
  }
} else {
  // NonPaginatedResponse — only has items and totalCount
  console.log(`All ${result.items.length} items returned`);
}
```
