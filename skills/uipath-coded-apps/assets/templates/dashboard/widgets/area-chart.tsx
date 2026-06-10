import React from 'react'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { <ICON> } from 'lucide-react'
<HOOK_IMPORT>
<RESPONSE_TYPE_IMPORT>
<SDK_IMPORT_LINE>
import { DeltaBadge, ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { fmtNumber } from '@/lib/format'
import { headline, delta } from '@/lib/widget'

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { data, loading, error } = <DATA_HOOK>
  const chartData: Record<string, unknown>[] = <DATA_SELECTOR>

  if (loading) return <LoadingState />
  if (error) return <EmptyState message={error.message} />

  const head = fmtNumber(headline(chartData, '<Y_KEY>', '<HEADLINE_MODE>'))
  const d = delta(chartData, '<Y_KEY>', '<DELTA_POLARITY>')

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
      <div className="px-6 pb-2 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{head}</span>
        {d.text && <DeltaBadge direction={d.direction} text={d.text} />}
      </div>
      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={chartData}>
            <XAxis
              dataKey="<X_KEY>"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string | number) => {
                const dt = new Date(String(v))
                return isNaN(dt.getTime()) ? String(v) : dt.toLocaleDateString([], { month: 'short', day: 'numeric' })
              }}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Area
              dataKey="<Y_KEY>"
              fill="hsl(var(--chart-1))"
              stroke="hsl(var(--chart-1))"
              fillOpacity={0.2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
