# SDK-wide invariants (read this before writing any code)

These six behaviors are consistent across every service and have specifically burned real code. They produce silent wrong results, not loud errors. This file is the **dashboard-specific gotcha layer** — method signatures and filter-field catalogs live in the SDK's `https://uipath.github.io/uipath-typescript/llms-full-content.txt`, not here.

## 1. Pagination is cursor-based and manual (with PER-SERVICE caps)

`service.getAll()` with no pagination options returns **one page**. It does NOT auto-paginate. And the per-page cap is NOT universal — three families with different limits:

| Service family | Services | Max `pageSize` | Error on violation |
|---|---|---|---|
| Orchestrator OData | Jobs, Tasks, Releases/Processes, Assets, Queues, Buckets | **1000** | — |
| pims | CaseInstances, ProcessInstances | **500** | `PIMS-100048: pageSize must be less than or equal to 500` |
| autopilot | Conversations (param is named `limit`, NOT `pageSize`) | **100** | `Number must be less than or equal to 100` |

Hitting a pims or autopilot service with `pageSize: 1000` returns 400 with the error strings above. Use `PAGE_SIZE.pims` / `PAGE_SIZE.autopilot` from `src/lib/queries/_shared.ts` explicitly for those — `fetchAllPims()` already bakes in the 500 default.

For the full set (still cursor-based):

```ts
async function fetchAll<T>(call: (args: any) => Promise<any>, args: Record<string, unknown> = {}) {
  const items: T[] = [];
  let cursor: { value: string } | undefined;
  for (let page = 0; page < 50; page++) {
    const resp = await call(cursor ? { cursor } : { ...args, pageSize: 1000 });
    items.push(...(resp.items ?? []));
    cursor = resp.nextCursor;             // undefined when hasNextPage is false
    if (!cursor || (resp.items?.length ?? 0) === 0) break;
  }
  return items;
}
```

**Critical:**
- Pass **only `{ cursor }`** on subsequent calls (no filter, no pageSize — cursor encodes them).
- `resp.nextCursor` is an **object `{ value: string }`**, not a plain string. `typeof resp.nextCursor === 'string'` is always false — checking that breaks the loop after page 1.
- The SDK accepts ONLY `cursor`, `pageSize`, `jumpToPage` as pagination signals. Passing a custom `skip` is silently ignored and produces infinite repeats of page 1.

## 2. Field-name drift between OData filter and consumer code

Every service runs `pascalToCamelCaseKeys()` and a service-specific `JobMap`/`TaskMap`/etc. on raw responses before returning. OData `$filter` expressions run against the server's PascalCase names; your consumer code reads the SDK's renamed camelCase field.

**Jobs:** the gnarliest set.

| OData `$filter=` uses this | Your code receives this |
|---|---|
| `CreationTime` | `createdTime` |
| `ReleaseName` | `processName` |
| `OrganizationUnitId` | `folderId` |
| `OrganizationUnitFullyQualifiedName` | `folderName` |
| `LastModificationTime` | `lastModifiedTime` |
| `ProcessType` | `packageType` |
| `StartTime`, `EndTime`, `State`, `JobError` | `startTime`, `endTime`, `state`, `jobError` (case only) |

**Example**: to get agent-only jobs, filter on the server side — writing `packageType eq 'Agent'` is a no-op because the server has no field by that name.

```ts
// ✅ correct
jobs.getAll({ filter: "CreationTime gt 2026-04-01T00:00:00Z and ProcessType eq 'Agent'" });

// ❌ filters nothing (packageType is a client-side name)
jobs.getAll({ filter: "packageType eq 'Agent'" });
```

Every service has a similar rename table. When in doubt, inspect `node_modules/@uipath/uipath-typescript/dist/<service>/index.mjs` and search for a `Map` constant (e.g., `const JobMap = { ... }`).

### Filterable ≠ projected

Some fields appear on the *response row* but are NOT accepted as OData `$filter` predicates. The OData schema exposes a subset of server-side fields for filtering that's narrower than the projected row.

**Releases (Processes):** `packageType` is projected but NOT filterable.
```ts
// ❌ 400 Bad Request — PackageType isn't filterable on ReleaseDto
processes.getAll({ filter: "PackageType eq 'Agent'" });

// ✅ paginate all releases, filter client-side
import { filterAgentsClientSide } from '@/lib/queries/_shared';
const all = await fetchAllPaginated(processes.getAll.bind(processes));
const agents = filterAgentsClientSide(all);
```

Helpers ship in `_shared.ts`: `filterAgentsClientSide()`, `filterProcessesClientSide()`.

When a filter returns 400, first suspect "field projected but not filterable" before assuming a syntax error. Grep the SDK's `.d.ts` types for `Filterable` properties or inspect the OData `$metadata` endpoint.

## 3. Folder scoping

Most Orchestrator endpoints are folder-scoped. The SDK's pattern:

- **With `folderId` in options** → SDK sets the `X-UIPATH-OrganizationUnitId` header and scopes results to that folder.
- **Without `folderId`** → no folder header; UiPath returns a cross-folder / tenant-wide view (filtered by whatever folders the token can read).

Read the `folderId` (or `folderKey`, depending on the service) off returned rows to see which folder each record came from — it's on the normalized shape.

## 4. `new Date(0)` is not a "reasonable default"

When a raw field is missing, DO NOT fall back to the epoch. A missing `createdTime` becomes Jan 1 1970, passes client-side date comparisons silently, and zeros out every "last N days" metric. Drop the row with `console.warn` and move on. This is the same philosophy as the "fail loud" principle in database NULL handling.

## 5. Some paginated responses overlap across pages

On busy tenants, concurrent inserts between your page fetches can cause the same job/task id to appear on two consecutive pages. Always **dedup paginated results by id** (not by object reference). A `Set<string>` check while accumulating costs nothing.

## 6. Some fields are FolderId (number), some are FolderKey (GUID)

Different services disagree on folder identity format:

- **Jobs, Processes, Assets, Queues, Tasks, Buckets** use `folderId: number` (and the header `X-UIPATH-OrganizationUnitId` carries a number).
- **Cases, MaestroProcesses** use `folderKey: string` (a GUID).

Don't interchange. If a method signature says `folderId: number`, pass the numeric id; if it says `folderKey: string`, pass the GUID. The SDK's normalized `Job` exposes both `folderId` and (sometimes) `folderKey` — pass the right one back to the method that consumes it.

## 7. Zero-fill time-bucketed series

For any time-bucketed chart, always zero-fill missing buckets. A missing hour or day rendered as a gap misleads the eye into interpreting it as "less than a spike" when it actually means "no data". Pre-generate the full bucket array (e.g., 24 hourly slots, 7 daily slots), then assign counts from your data. The scaffold's `src/lib/utils.ts` ships a `zeroFill()` helper — use it.

## The "fail loud" rule

All seven invariants share a theme: the SDK's convenience layers can make a bug return zero/empty/partial data instead of throwing. When debugging a "tile shows 0" or "table is empty", always suspect one of these before blaming the tenant.
