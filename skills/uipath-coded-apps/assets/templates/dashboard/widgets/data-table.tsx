import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { useInsights } from '@/hooks/useInsights'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

const COLUMNS: { key: string; label: string; align?: 'left' | 'right' }[] = <COLUMNS>
const PAGE_SIZE = 10

export function <COMPONENT_NAME>() {
  const [page, setPage] = useState(0)
  const navigate = useNavigate()
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <LoadingState height="h-48" />
  if (error) return <EmptyState message={error.message} />

  const rows: Record<string, unknown>[] = <DATA_SELECTOR>
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <Card className="col-span-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2">
            <<ICON> className="w-4 h-4 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <CardContent className="pt-0 px-0">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>{COLUMNS.map(c => <th key={c.key} className="px-4 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => navigate('<DETAIL_ROUTE>')}>
                {COLUMNS.map(c => <td key={c.key} className="px-4 py-2 max-w-xs truncate">{String(row[c.key] ?? '—')}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
            <span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}</span>
            <div className="flex gap-2">
              <button disabled={page === 0} onClick={e => { e.stopPropagation(); setPage(p => p - 1) }} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Prev</button>
              <button disabled={page >= totalPages - 1} onClick={e => { e.stopPropagation(); setPage(p => p + 1) }} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Next</button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
