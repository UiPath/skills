import React, { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ColumnDef<T> {
  key: keyof T | string
  label: string
  align?: 'left' | 'right'
  render?: (value: unknown, row: T) => React.ReactNode
}

interface RecordsTableProps<T> {
  rows: T[]
  columns: ColumnDef<T>[]
  defaultSortKey?: string
  /** Initial sort direction (default descending). */
  defaultSortAsc?: boolean
  /** When set, rows become clickable and invoke this with the clicked row. */
  onRowClick?: (row: T) => void
  pageSize?: number
}

export function RecordsTable<T extends Record<string, unknown>>({
  rows,
  columns,
  defaultSortKey,
  defaultSortAsc = false,
  onRowClick,
  pageSize = 50,
}: RecordsTableProps<T>) {
  const [sortKey, setSortKey] = useState(defaultSortKey ?? (columns[0]?.key as string))
  const [sortAsc, setSortAsc] = useState(defaultSortAsc)
  const [page, setPage] = useState(0)

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av
    return sortAsc
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av))
  })

  const total = sorted.length
  const totalPages = Math.ceil(total / pageSize)
  const pageRows = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const toggle = (key: string) => {
    if (key === sortKey) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(false) }
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key as string}
                  onClick={() => toggle(col.key as string)}
                  className={cn(
                    'px-4 py-3 font-medium text-muted-foreground whitespace-nowrap cursor-pointer select-none hover:text-foreground transition-colors',
                    col.align === 'right' ? 'text-right' : 'text-left'
                  )}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr
                key={i}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn('border-b last:border-0 hover:bg-muted/30 transition-colors', onRowClick && 'cursor-pointer')}
              >
                {columns.map((col) => {
                  const val = row[col.key as string]
                  return (
                    <td
                      key={col.key as string}
                      className={cn('px-4 py-3 max-w-xs truncate', col.align === 'right' && 'text-right tabular-nums')}
                    >
                      {col.render ? col.render(val, row) : String(val ?? '—')}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
          <span>Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Prev</button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
