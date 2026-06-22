# Pagination Reference

> **Foot-gun: every "list" call returns ONE page, even when you pass no pagination options.** `getAll`, `getAllRecords`, `queryRecordsById`, `getFileMetaData`, etc. all make exactly one HTTP call. Whether the response is typed as `PaginatedResponse` or `NonPaginatedResponse` is purely about whether you passed pagination options — it does NOT control how many rows you get back.
>
> - `getAll()` (no options) → `NonPaginatedResponse` → SDK sends no `pageSize` param; the **server** applies its own default cap and returns one page. You can't override it client-side without explicitly paginating. Despite the name, `NonPaginatedResponse` is NOT "all rows in one shot."
> - `getAll({ pageSize: 200 })` → `PaginatedResponse` → API returns up to 200, plus `hasNextPage` / `nextCursor`.
>
> **There is no "give me everything" call.** To list every row from a source that may have more than the cap, you MUST loop the cursor:
>
> ```typescript
> const all: T[] = [];
> let cursor: PaginationCursor | undefined;
> while (true) {
>   const page = await service.getAll(cursor ? { pageSize: 100, cursor } : { pageSize: 100 });
>   all.push(...page.items);
>   if (!page.hasNextPage || !page.nextCursor) break;
>   cursor = page.nextCursor;
> }
> ```
>
> Code that does `result.items.length` after a single call is almost always a bug — it returns at most the page size, not the total. Use `totalCount` for cardinality, the cursor loop for full retrieval. If the source has fewer rows than the default cap (e.g., 30 of a 100-cap), a single call works but you cannot rely on that as data grows.
>
> **Dashboard widgets:** don't hand-write this loop in `fnBody` — the dashboard scaffold ships a typed helper: `const { fetchAll } = await import('@/lib/paginate')` then `return await fetchAll(cursor => svc.getAll({ pageSize: 200, cursor }))`.

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

- No pagination options passed → returns `NonPaginatedResponse<T>` (response wrapper has no pagination metadata; data is still capped at the **server's** default page limit, applied on the API side because the SDK sends no `pageSize`; see foot-gun above).
- Any pagination option passed (pageSize, cursor, or jumpToPage) → returns `PaginatedResponse<T>` with `hasNextPage`/`nextCursor` for cursor-loop retrieval.

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
