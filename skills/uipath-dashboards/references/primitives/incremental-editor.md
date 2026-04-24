# incremental-editor

## Purpose
On subsequent Build runs (existing state.json + code), read the current dashboard tree and patch it to match the new prompt — without wiping hand edits. Implements Rule 8.

## Inputs
- Current `src/` tree.
- New user prompt.
- data-router + chart-selector outputs for any new widgets.

## Outputs
Targeted edits to `src/dashboard/Dashboard.tsx`, `src/dashboard/widgets/*.tsx`, `src/lib/queries/*.ts`.

## Rules
1. **Diff BEFORE write.** For every file this primitive touches, compute a diff against current content. If any line it's about to modify appears hand-edited (see signals below), surface diff + ask for confirmation.
2. **Widgets are files.** One widget per file in `src/dashboard/widgets/<PascalCase>.tsx`. Adding a widget creates a new file — never inlines into `Dashboard.tsx`.
3. **Queries are files.** One query hook per file in `src/lib/queries/<kebab>.ts`. Same isolation discipline.
4. **`Dashboard.tsx` is the only composition file.** Adding/removing widgets means import-line edits + JSX-block edits in exactly this one file.
5. **Reject edits that introduce security anti-patterns** — `dangerouslySetInnerHTML`, `console.log(sdk)`, localStorage access for tokens. Halt + explain.

## Hand-edit detection signals
Treat as hand-edited (trigger confirmation):
- Variable name differs from what the generator would produce (e.g., renamed `data` → `jobsList`).
- Custom comments added (anything not matching `// generated` patterns).
- Formatting changes (indentation, line breaks the generator doesn't emit).
- Restructured JSX layout (KPI row reordered, new grouping `<div>` wrappers).
- New imports from non-shadcn, non-project paths.

Compute a diff; if any of the above triggers in lines the new edit would touch, STOP and show:
```
The following file appears to have hand edits:
  src/dashboard/widgets/TopAgentsTable.tsx
    Line 42 was renamed from `data` to `jobsList`

I plan to change line 42 from:
  const { data } = useTopAgents(...)
to:
  const { data } = useTopAgents({limit: 20, ...})

Overwrite? (y/n)
```

## Add-widget recipe
1. **Create widget file:** copy `assets/templates/widgets/<chartType>.tsx.template` → `<project>/src/dashboard/widgets/<PascalName>.tsx`; substitute series names, data-hook name, ChartConfig.
2. **Create query file:** write `<project>/src/lib/queries/<kebab>.ts` with the data-router's SDK call.
3. **Update `Dashboard.tsx`:**
   - Add `import { PascalName } from './widgets/PascalName'` at top (insert alphabetically).
   - Insert the `<PascalName />` JSX block in the correct layout slot per [../aesthetic/layout-patterns.md](../aesthetic/layout-patterns.md).
4. **Diff check on `Dashboard.tsx`** — if the layout file has hand-edit signals, surface + confirm.

## Edit-widget recipe
1. Read widget file.
2. Apply targeted edit (e.g., change time window constant, filter).
3. Diff check — confirm if touching hand-edited lines.
4. Write.
5. **Verify the write physically landed.** Immediately read the file back (or grep for the exact string you just wrote). Do NOT trust the tool's "updated successfully" message alone — there are reproducible cases where an `Edit` retry after a "File has not been read" error reports success but leaves the file unchanged. Silent no-ops here cause hidden regressions (e.g., a `pageSize: 1000` retry that's actually still 500 in the file). This is a cheap one-line discipline that costs nothing on the happy path and catches catastrophic drift on the failure path.

## Remove-widget recipe
1. Delete widget file.
2. Delete corresponding query file (if not referenced elsewhere — grep first).
3. Remove import + JSX from `Dashboard.tsx`.
4. Diff check throughout.

## Rule 12 enforcement (security anti-patterns)
Before writing, regex-check the edit for:
- `dangerouslySetInnerHTML`
- `console.log(sdk)` (case-insensitive)
- `localStorage.*token`
- `document.cookie`
- `window.location.href =.*token`

On hit: halt with "This edit introduces a security anti-pattern; see references/primitives/security.md". Never auto-write.

## Error paths
| Condition | Action |
|---|---|
| Plan says "remove widget X" but X doesn't exist | Halt; ask user to clarify. |
| Plan says "add widget X" but X already exists | Offer "rename new one / skip / replace (with diff check)". |
| Dashboard.tsx doesn't parse (user broke it) | Halt; point at parse error; don't attempt repair. |
