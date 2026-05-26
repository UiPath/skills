import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { useAuth } from '@/hooks/useAuth'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

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

  const chartData: Record<string, unknown>[] = <DATA_SELECTOR>

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('<DETAIL_ROUTE>')}>
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
      <CardContent className="pt-2">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
            <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, border: 'none', background: 'hsl(var(--card))', borderRadius: 6, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              cursor={{ fill: 'hsl(var(--muted))' }}
            />
            <Bar dataKey="<Y_KEY>" radius={[4, 4, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={`hsl(var(--chart-${(i % 5) + 1}))`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
