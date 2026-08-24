# DataTable Widget

React datatable (ag-Grid) over a single **Data Fabric entity**: CRUD, inline editing with diff review, master-detail grouping by foreign key, choice sets, file fields, filtering/sorting/pagination — all prebuilt.

Package: [`@uipath/ui-widgets-datatable`](https://www.npmjs.com/package/@uipath/ui-widgets-datatable). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

## When to Use

- User asks to **browse, edit, or manage records** of a Data Fabric entity in a grid/table.
- Replaces a hand-rolled ag-Grid/table + entity CRUD plumbing. Do **not** rebuild this UI from scratch — the widget already handles schema-driven columns, per-field-type editors, diff/commit, choice-set and foreign-key resolution, and file upload/download.
- For custom read-only tables over *non-entity* data (Jobs, Tasks, etc.), use the standard table patterns in [../patterns.md](../patterns.md) instead — this widget only renders Data Fabric entities.

## Critical Rules

1. **Peer versions are hard requirements.** `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1`.
2. **Import the stylesheet once** or the grid renders unstyled: `import '@uipath/ui-widgets-datatable/DataTable.css'`.
3. **Body needs `light` or `dark` class** for theming.
4. **`entityId` is the entity UUID, not the display name.** Resolve it via `new Entities(sdk).getAll()` at runtime or `uip df entities list --output json` at build time. Passing the friendly name fails. See [../sdk/data-fabric.md](../sdk/data-fabric.md).
5. **Required scopes:** `DataFabric.Schema.Read DataFabric.Data.Read` to display; add `DataFabric.Data.Write` because the grid ships with editing enabled (commit/insert/delete/file upload 403 without it). See [../oauth-scopes.md](../oauth-scopes.md).
6. **There is no global read-only prop.** To present a read-only grid, disable editing per column via `columnConfig` (`editable: false`) — otherwise users can edit cells and the commit fails or writes data you didn't intend.
7. **`columnConfig` keys are column display names**, not entity field names (e.g. `"Edition Name"`, not `editionName`).
8. **The widget already paginates** (ag-Grid, `pageSize` default 50) — this satisfies the skill's table-pagination rule. Do not wrap it in your own pagination or fetch records yourself; there is no prop to inject rows — the widget fetches from the entity itself.
9. **Reuse the app's initialized `UiPath` instance** (`useAuth()`); do not construct a second SDK.
10. **No special `vite.config.ts` setup** — no asset plugins or `optimizeDeps` changes needed.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-datatable --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Key Props

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes | Initialized `UiPath` instance from `useAuth()`. |
| `entityId` | Yes | Data Fabric entity **UUID**. |
| `pageSize` | No | Rows per page (default 50). |
| `showIdColumn` | No | Show the record Id column. |
| `columnConfig` | No | `Record<displayName, ColDef>` — ag-Grid column overrides (width, `editable: false`, cell styles, class rules). |
| `rowClassRules` | No | ag-Grid conditional row classes, e.g. `{ 'row-alert': p => p.data.status === 'Failed' }`. |
| `customPaddingForExpandedRow` | No | Pixel padding for expanded rows in group-by mode. |

## Built-in Flows (what the toolbar does)

Know these so you don't duplicate them in the host app:

- **Read** — loads schema + records on mount (`expansionLevel: 2`, choice sets pre-fetched); **Refresh** reloads.
- **Update** — cell edits are tracked, **Show Diff (N)** opens original-vs-edited review with per-field revert, **Commit Changes** calls `updateRecords`.
- **Create** — **Add Row** pins an empty row on top; **Insert Records** persists, **Discard** drops them.
- **Delete** — checkbox selection → **Delete Records** → confirm dialog.
- **Group by** — pick a foreign-key column; rows nest under master records. Inline editing and row selection are **disabled in group-by mode**.
- **Field types** — text/multiline/number/date/boolean/single- and multi-choice sets/foreign keys handled automatically; DateTime renders read-only; File fields get upload/open/download/remove controls.

## Integration: Web App

```typescript
import { DataTable } from '@uipath/ui-widgets-datatable';
import '@uipath/ui-widgets-datatable/DataTable.css';
import { useAuth } from '../hooks/useAuth';

function RecordsPage({ entityId }: { entityId: string }) {
  const { sdk } = useAuth();

  return (
    <DataTable
      sdk={sdk}
      entityId={entityId}
      pageSize={50}
      columnConfig={{ 'Created At': { editable: false } }}
    />
  );
}

export default RecordsPage;
```

Entity UUID unknown up front? List entities and let the user pick:

```typescript
import { Entities } from '@uipath/uipath-typescript/entities';

const entities = await new Entities(sdk).getAll(); // [{ id, name, displayName }, ...]
```

## Anti-patterns

- **Do not rebuild an entity CRUD grid by hand** (ag-Grid + `getAllRecords` + custom editors) when this widget fits.
- **Do not pass the entity display name as `entityId`** — UUID only.
- **Do not fetch records yourself and expect to feed them in** — there is no `rows`/`data` prop; the widget owns fetching.
- **Do not ship with `DataFabric.Data.Read` only while editing is enabled** — edits fail at commit with 403; either add `DataFabric.Data.Write` or set columns `editable: false`.
- **Do not key `columnConfig` by field name** — keys are display names.
- **Do not seed or migrate data through the widget** — for bulk writes use the SDK/CLI directly; see [../sdk/data-fabric.md](../sdk/data-fabric.md) for choice-value translation traps.
