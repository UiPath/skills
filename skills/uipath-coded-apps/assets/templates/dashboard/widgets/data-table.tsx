import React, { useState } from 'react'
import { useInsights } from '../hooks/useInsights'

// COLUMNS format: [{ key: 'fieldName', label: 'Column Header' }, ...]
const COLUMNS: { key: string; label: string }[] = <COLUMNS>

const PAGE_SIZE = 25

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>
  const [page, setPage] = useState(0)

  if (loading) return <div className="h-40 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  // Most Insights responses wrap the array in a nested object.
  // Extract using the path from insights-catalog.md Key response fields.
  // Example for agents.getAgents: const rows = (data as any)?.data?.agents ?? []
  // Example for agents.getTopErroredAgents: const rows = (data as any)?.data ?? []
  const rows: Record<string, unknown>[] = <DATA_SELECTOR>
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="rounded-lg border bg-card col-span-full overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-medium text-muted-foreground"><TITLE></h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              {COLUMNS.map((c) => (
                <th key={c.key} className="px-4 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                {COLUMNS.map((c) => (
                  <td key={c.key} className="px-4 py-2 max-w-xs truncate">
                    {String(row[c.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
          <span>
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
              className="px-2 py-1 rounded border disabled:opacity-40"
            >
              Prev
            </button>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
              className="px-2 py-1 rounded border disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
