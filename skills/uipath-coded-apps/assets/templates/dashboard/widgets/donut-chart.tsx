import React from 'react'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { <ICON> } from 'lucide-react'
<HOOK_IMPORT>
<RESPONSE_TYPE_IMPORT>
<SDK_IMPORT_LINE>
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { fmtNumber } from '@/lib/format'
import { headline } from '@/lib/widget'

const CHART_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))']

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { data, loading, error } = <DATA_HOOK>
  const chartData = <DATA_SELECTOR>

  if (loading) return <LoadingState />
  if (error) return <EmptyState message={error.message} />

  const head = fmtNumber(headline(chartData as Record<string, unknown>[], '<DATA_KEY>', 'sum'))

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
            <CardDescription><SUBTITLE></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <div className="px-6 pb-2">
        <span className="text-3xl font-semibold tabular-nums">{head}</span>
        <span className="ml-2 text-sm text-muted-foreground">total</span>
      </div>
      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie data={chartData as Record<string, unknown>[]} dataKey="<DATA_KEY>" nameKey="<NAME_KEY>" innerRadius={50} outerRadius={75}>
              {(chartData as Record<string, unknown>[]).map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
