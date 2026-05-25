import React from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { <ICON> } from 'lucide-react'
import { useInsights } from '@/hooks/useInsights'
import { DeltaBadge, ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { fmtNumber } from '@/lib/format'

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { data, loading, error } = <DATA_HOOK>
  const chartData: Record<string, unknown>[] = <DATA_SELECTOR>

  if (loading) return <LoadingState />
  if (error) return <EmptyState message={error.message} />

  const total = chartData.reduce((sum, row) => sum + Number((row as Record<string, unknown>)['<Y_KEY>'] ?? 0), 0)

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => navigate('<DETAIL_ROUTE>')}
    >
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
      <div className="px-6 pb-2 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{fmtNumber(total)}</span>
        <DeltaBadge direction="<DELTA_DIR>" text="<DELTA_TEXT>" />
      </div>
      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData}>
            <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="<Y_KEY>" fill="hsl(var(--chart-1))" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
