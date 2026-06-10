# Agents (Insights RTM) Reference

> **SDK availability:** The `agents` subpath ships with PR #438. If `node_modules/@uipath/uipath-typescript/dist/agents/` does not exist in the installed version, Phase 3.5 type verification will skip it — `tsc` catches any errors at build time.

## Import

```typescript
import { Agents } from '@uipath/uipath-typescript/agents';
```

## Scopes

`Insights` and `Insights.RealTimeData`

## Constructor

```typescript
const svc = new Agents(sdk as never)
```

The `as never` cast is required until the SDK's constructor overload is updated.

## Method signatures

All Insights methods take **positional `Date` parameters** — not an options object.

```typescript
// ✓ Correct
svc.getErrorsTimeline(THIRTY_DAYS_AGO, NOW)

// ✗ Wrong — Insights methods do not accept an options object
svc.getErrorsTimeline({ startTime: ..., endTime: ... })
```

| Method | Signature | Returns |
|--------|-----------|---------|
| `getAll` | `(startTime: Date, endTime: Date)` | `{ items: AgentListItem[] }` |
| `getErrorsTimeline` | `(startTime: Date, endTime: Date)` | `{ data: Array<{ date: string, value: number }> }` |
| `getConsumptionTimeline` | `(startTime: Date, endTime: Date)` | `{ data: Array<{ timeSlice: string, aguConsumption: number }> }` |
| `getLatencyTimeline` | `(startTime: Date, endTime: Date)` | `{ data: Array<{ name: 'P50' \| 'P95', value: number, date: string }> }` |
| `getTopErroredAgents` | `(startTime: Date, endTime: Date)` | `{ data: Array<{ name: string, count: number }> }` |
| `getIncidentDistribution` | `(startTime: Date, endTime: Date)` | `{ data: Array<{ name: string, count: number }> }` |

`AgentListItem` fields: `id`, `name`, `state`, `lastRunTime`

## What cannot be derived from this service

| Requested metric | Why not available | Alternative |
|-----------------|-------------------|-------------|
| Agent cost in dollars | Platform tracks AGU, not currency | `getConsumptionTimeline` for AGU |
| CPU / memory per agent | Not exposed by any Insights endpoint | `getLatencyTimeline` for fleet latency |
| Error messages / stack traces | No text aggregation endpoint | `getErrorsTimeline` for error counts |

## Usage example (dashboard fnBody pattern)

```typescript
const { Agents } = await import('@uipath/uipath-typescript/agents')
const svc = new Agents(sdk as never)
return (await svc.getErrorsTimeline(THIRTY_DAYS_AGO, NOW))?.data ?? []
```
