import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { useAuth } from '@/hooks/useAuth'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

const COLUMNS: { key: string; label: string; align?: 'left' | 'right' }[] = <COLUMNS>
const MAX_ROWS = 10

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [result, setResult] = useState<<SDK_RESULT_TYPE> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setResult(r) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-48" />
  if (error) return <EmptyState message={error.message} />

  const rows: Record<string, unknown>[] = (<DATA_SELECTOR>).slice(0, MAX_ROWS)

  return (
    <Card className="col-span-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><<ICON> className="w-4 h-4 text-muted-foreground" /></div>
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
            <tr>
              <th className="px-4 py-2 text-left font-medium text-muted-foreground w-8">#</th>
              {COLUMNS.map(c => (
                <th key={c.key} className={`px-4 py-2 font-medium text-muted-foreground whitespace-nowrap ${c.align === 'right' ? 'text-right' : 'text-left'}`}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => navigate('<DETAIL_ROUTE>')}>
                <td className="px-4 py-2 text-muted-foreground text-xs">{i + 1}</td>
                {COLUMNS.map(c => (
                  <td key={c.key} className={`px-4 py-2 max-w-xs truncate ${c.align === 'right' ? 'text-right tabular-nums' : ''}`}>
                    {String(row[c.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}
