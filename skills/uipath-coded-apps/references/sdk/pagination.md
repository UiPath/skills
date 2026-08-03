# Pagination — Server Behavior & Patterns

Types (`PaginationOptions`, `PaginationCursor`, `PaginatedResponse`, `NonPaginatedResponse`) and per-method pagination examples: `dist/core/index.d.ts` + each service's own `dist/<subpath>/index.d.ts` JSDoc. This file covers only server behavior and skill patterns neither documents.

> **Foot-gun: every "list" call returns ONE page, even when you pass no pagination options.** `getAll`, `getAllRecords`, `queryRecordsById`, `getFileMetaData`, etc. all make exactly one HTTP call.
>
> - `getAll()` (no options) → SDK sends no `pageSize` param; the **server** applies its own default cap and returns one page, wrapped in a misleadingly-named `NonPaginatedResponse`. It is NOT "all rows in one shot," and you can't override the cap client-side without explicitly paginating.
> - **There is no "give me everything" call.** To list every row from a source that may exceed the cap, loop the cursor:
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
> **Dashboard widgets:** don't hand-write this loop in `fnBody` — the dashboard scaffold ships a typed helper: `const { fetchAll } = await import('@/lib/paginate')` then `const items = await fetchAll(cursor => svc.getAll({ pageSize: 200, cursor }))` and return `items.map(x => ({ ...x }))` (project SDK rows into `Row` objects).

Server behavior the types don't show:

- `jumpToPage` works only on offset-based services (Assets, Queues, Tasks, Entities) — check `supportsPageJump` on the response before offering page-jump UI.
- Runtime discrimination when options are dynamic: `'hasNextPage' in result` — the field exists only on `PaginatedResponse`, never on `NonPaginatedResponse`.
