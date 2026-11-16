# UI Patterns Reference

## Polling for Real-Time Updates

When a component needs to auto-refresh data (e.g., monitoring process instance status or variables), create `src/hooks/usePolling.ts`:

```typescript
import { useEffect, useRef, useCallback, useState } from 'react';

interface UsePollingOptions<T> {
  fetchFn: () => Promise<T>;
  interval?: number;       // ms, default 5000
  enabled?: boolean;       // toggle on/off
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  immediate?: boolean;     // fetch on mount, default true
  deps?: unknown[];        // Reset and refetch immediately when any dep changes (e.g., [instanceId])
}

interface UsePollingResult<T> {
  data: T | null;
  isLoading: boolean;      // True only during initial fetch (before first data arrives)
  error: Error | null;
  refetch: () => Promise<void>;
  start: () => void;
  stop: () => void;
  isActive: boolean;       // Whether the polling interval is running (use for "Live" indicator)
  lastUpdated: Date | null;
}

export function usePolling<T>({
  fetchFn, interval = 5000, enabled = true,
  onSuccess, onError, immediate = true, deps = [],
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isActive, setIsActive] = useState(enabled);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => { setIsActive(enabled); }, [enabled]);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  const hasLoadedRef = useRef(false);

  useEffect(() => { fetchFnRef.current = fetchFn; }, [fetchFn]);
  useEffect(() => { onSuccessRef.current = onSuccess; }, [onSuccess]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const prevJsonRef = useRef<string>('');

  const executeFetch = useCallback(async () => {
    try {
      const result = await fetchFnRef.current();
      // Only update state if data actually changed — prevents unnecessary re-renders
      const json = JSON.stringify(result);
      if (json !== prevJsonRef.current) {
        prevJsonRef.current = json;
        setData(result);
        setLastUpdated(new Date());
      }
      // Clear any previous error only if it was set (avoid no-op setState)
      setError(prev => prev === null ? prev : null);
      onSuccessRef.current?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      // Only transition from loading → loaded once (on first successful or failed fetch)
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true;
        setIsLoading(false);
      }
    }
  }, []);

  const start = useCallback(() => setIsActive(true), []);
  const stop = useCallback(() => {
    setIsActive(false);
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
  }, []);
  const refetch = useCallback(async () => { await executeFetch(); }, [executeFetch]);

  // Serialize deps for comparison — when deps change, reset everything and refetch
  const depsKey = JSON.stringify(deps);
  const prevDepsKeyRef = useRef(depsKey);

  useEffect(() => {
    // Detect if deps changed (e.g., user selected a different instance)
    const depsChanged = depsKey !== prevDepsKeyRef.current;
    if (depsChanged) {
      prevDepsKeyRef.current = depsKey;
      // Full reset: clear old data, show loading, refetch immediately
      hasLoadedRef.current = false;
      prevJsonRef.current = '';
      setData(null);
      setIsLoading(true);
      setError(null);
    }

    if (!isActive || !enabled) {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      return;
    }
    if (intervalRef.current) { clearInterval(intervalRef.current); }
    if (immediate || depsChanged) executeFetch();
    intervalRef.current = setInterval(executeFetch, interval);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, enabled, interval, immediate, executeFetch, depsKey]);

  return { data, isLoading, error, refetch, start, stop, isActive, lastUpdated };
}
```

SDK usage:

```typescript
import { useMemo, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePolling } from '../hooks/usePolling';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';

function InstanceMonitor({ instanceId, folderKey }: { instanceId: string; folderKey: string }) {
  const { sdk, isAuthenticated } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);
  const fetchVariables = useCallback(
    () => processInstances.getVariables(instanceId, folderKey),
    [processInstances, instanceId, folderKey]
  );
  const { data: variables, isLoading, isActive, error } = usePolling({
    fetchFn: fetchVariables,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    immediate: true,
    deps: [instanceId],
  });
  // ...render variables
}
```

`deps` is **CRITICAL for master-detail UIs**: pass identity values such as `[instanceId]`; changing one clears stale `data`, sets `isLoading` true, and refetches immediately. Without it, switching items shows stale data without a loading indicator. Tie `enabled` to need (such as `!!selectedInstance`); use `immediate: false` when another effect loaded initial data. The default `interval` is 5000ms; increase it for less-critical data to reduce API load. For Data Fabric entities, use the interval and rules in [sdk/data-fabric.md](sdk/data-fabric.md) trap 10.

### Master-detail pattern — MANDATORY for list + detail layouts

Always do both:

1. Key the detail component by the selected item to unmount the old detail and reset hooks and local state:

```tsx
{selectedInstance && (
  <InstanceDetail
    key={selectedInstance.id}
    instanceId={selectedInstance.id}
    folderKey={selectedInstance.folderKey}
  />
)}
```

2. Pass identity `deps` inside it:

```typescript
const { data, isLoading, isActive } = usePolling({
  fetchFn: fetchInstanceData,
  interval: 5000,
  enabled: isAuthenticated && !!instanceId,
  deps: [instanceId],
});
```

`key` resets component state; `deps` resets polling refs (`hasLoadedRef`, `prevJsonRef`). Both are defense-in-depth: `key` can be lost during refactoring, while `deps` does not reset unrelated state such as tabs or expanded sections.

### Flicker-free updates — MANDATORY

Polling must NEVER cause visible UI flicker. Follow ALL three rules:

1. **No per-cycle state changes in the hook.** Never add `setIsPolling(true)`/`setIsPolling(false)` or `setIsLoading(true)`/`setIsLoading(false)` around each fetch: this creates two renders per cycle. `isLoading` only goes `true → false` after the first fetch and returns to `true` only on identity reset — NEVER set it back to `true` yourself; `isActive` changes only when polling starts/stops and drives the Live indicator. Use functional `setError` updates.

2. **Accumulate and sort rows. THIS IS THE MOST IMPORTANT RULE.** Never render `getVariables()` arrays directly: `getVariables()` returns different subsets of variables across polls, in non-deterministic order. Accumulate observed variables in `Map<string, GlobalVariableMetaData>` by `v.id`, and elements in a map by `elementId`; latest values win. Store only elements with nonempty inputs or outputs, sort variables by `name` and elements by `elementId`, and reset maps when `instanceId` changes:

```typescript
import type { GlobalVariableMetaData, ElementMetaData } from '@uipath/uipath-typescript/maestro-processes';

const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());
const accumulatedElementsRef = useRef<Map<string, {
  elementId: string; isMarker: boolean;
  inputs: Record<string, unknown>; outputs: Record<string, unknown>;
}>>(new Map());

// Single shared reset block (lastInstanceIdRef/lastDataRef declared in Rule 3)
if (instanceId !== lastInstanceIdRef.current) {
  lastInstanceIdRef.current = instanceId;
  lastDataRef.current = null;
  accumulatedVarsRef.current = new Map();
  accumulatedElementsRef.current = new Map();
}
if (displayData) {
  for (const v of displayData.variables.globalVariables)
    accumulatedVarsRef.current.set(v.id, v);
  for (const e of displayData.variables.elements)
    if (Object.keys(e.inputs).length > 0 || Object.keys(e.outputs).length > 0)
      accumulatedElementsRef.current.set(e.elementId, e);
}
const displayVars = [...accumulatedVarsRef.current.values()]
  .sort((a, b) => a.name.localeCompare(b.name));
const displayElements = [...accumulatedElementsRef.current.values()]
  .sort((a, b) => a.elementId.localeCompare(b.elementId));
```

Old rows remain, repeated variables get the latest value, order is stable, and instance changes cannot show stale data.

3. **Never tear down the data UI.** Preserve raw data in a ref, reset it on identity change, and show loading only without preserved data:

```typescript
const lastDataRef = useRef<InstanceData | null>(null);
const lastInstanceIdRef = useRef(instanceId);
if (instanceId !== lastInstanceIdRef.current) {
  lastInstanceIdRef.current = instanceId;
  lastDataRef.current = null;
}
if (data) lastDataRef.current = data;
const displayData = lastDataRef.current;
if (!displayData) {
  if (error) return <div>Error: {error.message}</div>;
  return <LoadingSpinner />;
}
```

Render only accumulated/sorted arrays, never `displayData.variables` directly. Show errors inside preserved UI after data exists; when `displayData` is absent and `error` is set, render the error message instead of the loading state; otherwise show initial/loading state only when `displayData` is absent. Use `isActive` for a pure CSS Live indicator, not a state toggle.

#### Complete flicker-free component pattern

Combines Rules 1–3 with one shared reset block:

```typescript
import { useCallback, useMemo, useRef } from 'react';
import type {
  ProcessInstanceGetVariablesResponse,
  GlobalVariableMetaData,
} from '@uipath/uipath-typescript/maestro-processes';

function InstanceDataPanel({ instanceId, folderKey }: Props) {
  const { sdk, isAuthenticated } = useAuth();
  const svc = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchFn = useCallback(
    () => svc.getVariables(instanceId, folderKey),
    [svc, instanceId, folderKey]
  );

  const { data, isLoading, isActive, error } = usePolling({
    fetchFn,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    deps: [instanceId],  // Reset and refetch when instance changes
  });

  // --- Flicker prevention refs ---
  const lastDataRef = useRef<ProcessInstanceGetVariablesResponse | null>(null);
  const lastInstanceIdRef = useRef(instanceId);
  const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());
  const accumulatedElementsRef = useRef<
    Map<string, { elementId: string; isMarker: boolean; inputs: Record<string, unknown>; outputs: Record<string, unknown> }>
  >(new Map());

  // Reset everything when switching instances
  if (instanceId !== lastInstanceIdRef.current) {
    lastInstanceIdRef.current = instanceId;
    lastDataRef.current = null;
    accumulatedVarsRef.current = new Map();
    accumulatedElementsRef.current = new Map();
  }
  if (data) lastDataRef.current = data;
  const displayData = lastDataRef.current;

  // data here is the raw getVariables() response, so no `.variables` level
  if (displayData) {
    for (const v of displayData.globalVariables) {
      accumulatedVarsRef.current.set(v.id, v);
    }
    for (const e of displayData.elements) {
      if (Object.keys(e.inputs).length > 0 || Object.keys(e.outputs).length > 0) {
        accumulatedElementsRef.current.set(e.elementId, e);
      }
    }
  }

  const displayVars = [...accumulatedVarsRef.current.values()].sort((a, b) =>
    a.name.localeCompare(b.name)
  );
  const displayElements = [...accumulatedElementsRef.current.values()].sort((a, b) =>
    a.elementId.localeCompare(b.elementId)
  );

  // Loading — only on initial load or instance switch
  if (!displayData) {
    if (error) return <div>Error: {error.message}</div>;
    return <div>Loading...</div>;
  }

  return (
    <div>
      {error && (
        <div className="text-sm text-red-600 p-2 bg-red-50 rounded mb-2">
          {error.message}
        </div>
      )}
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold">Process Data</h3>
        {isActive && (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
            Live
          </span>
        )}
      </div>

      {/* Render from accumulated + sorted arrays — NOT raw displayData */}
      {displayVars.length > 0 && (
        <ProcessDataTable globalVariables={displayVars} />
      )}

      {displayElements.length > 0 && (
        <div className="mt-4 space-y-2">
          {displayElements.map(element => (
            <ElementCard key={element.elementId} element={element} />
          ))}
        </div>
      )}
    </div>
  );
}
```

## BPMN Diagram Rendering

Install the viewer by running:

```bash
npm install bpmn-js
```

Import in `src/index.css` (or the component) and hide the watermark:

```css
@import 'bpmn-js/dist/assets/diagram-js.css';
@import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';
.bjs-powered-by { display: none !important; }
```

Use `BpmnViewer` with XML from `ProcessInstances.getBpmn()`, import it in an effect, fit the canvas, and destroy it on cleanup:

```typescript
import { useEffect, useRef } from 'react';
import BpmnViewer from 'bpmn-js/lib/Viewer';

export const BpmnDiagram = ({ bpmnXml }: { bpmnXml: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!containerRef.current || !bpmnXml) return;
    const viewer = new BpmnViewer({ container: containerRef.current });
    (async () => {
      try { await viewer.importXML(bpmnXml); viewer.get('canvas').zoom('fit-viewport'); }
      catch (err) { console.error('Error rendering BPMN:', err); }
    })();
    return () => { viewer.destroy(); };
  }, [bpmnXml]);
  return <div ref={containerRef} style={{ width: '100%', height: '500px' }} />;
};
```

```typescript
// Via service method
const bpmnXml = await processInstances.getBpmn(instanceId, folderKey);

// Or via bound method on an instance object
const instance = await processInstances.getById(instanceId, folderKey);
const bpmnXml = await instance.getBpmn();
```

Then render: `<BpmnDiagram bpmnXml={bpmnXml} />`

## Rendering Process Instance Data (Variables & Elements)

Never dump `getVariables()` or raw JSON. Render structured UI: global variables as a key-value table and elements as collapsible cards with inputs and outputs. Use `GlobalVariableMetaData`, `ElementMetaData`, and type badges; skip zero-item sections and empty elements; poll while the process is running. Values are sometimes double-serialized JSON strings (e.g., `"{\"key\": \"value\"}"`); always try `JSON.parse()` on string values that start with `{` or `[`.

For a single domain-specific process use a meaningful label such as **"Loan Details"**, **"Application Data"**, or **"Extraction Results"**. For generic multi-process monitoring use **"Process Data"**, not "Variables" (a developer term meaningless to end users); use **"Activity Details"** for element data when appropriate.

### Rendering `globalVariables`

Display as a clean key-value table. Format values by type.

```typescript
import type { GlobalVariableMetaData } from '@uipath/uipath-typescript/maestro-processes';

interface ProcessDataTableProps {
  globalVariables: GlobalVariableMetaData[];
}

function ProcessDataTable({ globalVariables }: ProcessDataTableProps) {
  if (globalVariables.length === 0) {
    return <p className="text-sm text-gray-500 p-4">No data available</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {globalVariables.map((v) => (
            <tr key={v.id}>
              <td className="px-4 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">{v.name}</td>
              <td className="px-4 py-3 text-sm text-gray-700 max-w-md">
                <FormattedValue value={v.value} type={v.type} />
              </td>
              <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">{v.type}</span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">{v.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Rendering `elements` (activity step data)

Each element represents an executed activity with inputs and outputs. Render as collapsible cards — show the element name (derived from `elementId`) as the header, then inputs and outputs as structured sections inside. Make element cards collapsible — elements can have very large nested input/output structures; don't expand all by default.

```typescript
import { useState } from 'react';
import type { ElementMetaData } from '@uipath/uipath-typescript/maestro-processes';

interface ElementCardProps {
  element: ElementMetaData;
}

function ElementCard({ element }: ElementCardProps) {
  const [expanded, setExpanded] = useState(false);

  const hasInputs = Object.keys(element.inputs).length > 0;
  const hasOutputs = Object.keys(element.outputs).length > 0;

  if (!hasInputs && !hasOutputs) return null; // Skip empty elements

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{element.elementId}</span>
          {element.isMarker && (
            <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded">Marker</span>
          )}
        </div>
        <span className="text-gray-400 text-sm">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="p-4 space-y-4">
          {hasInputs && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Inputs</h4>
              <KeyValueRenderer data={element.inputs} />
            </div>
          )}
          {hasOutputs && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Outputs</h4>
              <KeyValueRenderer data={element.outputs} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Value formatting helpers

Use these `FormattedValue` and recursive `KeyValueRenderer` helpers to render any value cleanly — primitives as text, objects/arrays as structured UI:

```typescript
/** Renders a typed value from globalVariables */
function FormattedValue({ value, type }: { value: unknown; type: string }) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">—</span>;
  }
  if (typeof value === 'boolean') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        value ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}>
        {value ? 'True' : 'False'}
      </span>
    );
  }
  if (typeof value === 'number') {
    return <span className="font-mono text-sm">{value.toLocaleString()}</span>;
  }
  if (typeof value === 'string') {
    // Detect JSON strings that were double-serialized
    if (value.startsWith('{') || value.startsWith('[')) {
      try {
        const parsed = JSON.parse(value);
        return <KeyValueRenderer data={parsed} />;
      } catch {
        // Not JSON, render as string
      }
    }
    return <span className="text-sm">{value}</span>;
  }
  if (Array.isArray(value)) {
    return <KeyValueRenderer data={value} />;
  }
  if (typeof value === 'object') {
    return <KeyValueRenderer data={value} />;
  }
  return <span className="text-sm">{String(value)}</span>;
}

/** Recursively renders a Record or array as a structured key-value list */
function KeyValueRenderer({ data }: { data: Record<string, any> | any[] }) {
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-gray-400 text-sm italic">Empty list</span>;
    return (
      <div className="space-y-2">
        {data.map((item, i) => (
          <div key={i} className="pl-3 border-l-2 border-gray-200">
            <span className="text-xs text-gray-400 mb-1 block">#{i + 1}</span>
            {typeof item === 'object' && item !== null
              ? <KeyValueRenderer data={item} />
              : <span className="text-sm text-gray-700">{String(item)}</span>
            }
          </div>
        ))}
      </div>
    );
  }

  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="text-gray-400 text-sm italic">Empty</span>;

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
      {entries.map(([key, val]) => (
        <div key={key} className="contents">
          <dt className="text-xs text-gray-500 py-1 whitespace-nowrap">{formatKey(key)}</dt>
          <dd className="text-sm text-gray-700 py-1 min-w-0 break-words">
            {val === null || val === undefined ? (
              <span className="text-gray-400 italic">—</span>
            ) : typeof val === 'object' ? (
              <KeyValueRenderer data={val} />
            ) : typeof val === 'boolean' ? (
              <span className={val ? 'text-green-600' : 'text-red-600'}>{String(val)}</span>
            ) : (
              String(val)
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Converts camelCase/snake_case keys to readable labels */
function formatKey(key: string): string {
  return key
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}
```

`KeyValueRenderer` renders arrays with `#1`, `#2`, etc. and a left border, and objects as a key/value `<dl>`; recurse and use readable labels. Global tables include Name, Value, Type, and Source, keyed by `v.id`. Element cards show `element.elementId`, a Marker badge when `element.isMarker`, and collapsible Inputs/Outputs sections; use `useState(false)` so they are collapsed by default and skip empty elements.

The complete detail-panel pattern ("Complete flicker-free component pattern" above) combines `usePolling`, `deps: [instanceId]`, `lastDataRef`, identity reset, map accumulation, stable sorting, an error message, loading state, pure CSS `Live`, `ProcessDataTable globalVariables={displayVars}`, and `ElementCard key={element.elementId}`. Never render raw polled arrays. This also applies to HITL panels. Follow Flicker-free updates Rules 2 and 3.

## HITL Detection (Human-in-the-Loop)

Use `getVariables()` plus `getBpmn()`, not `getExecutionHistory()`: the last `variables.elements` item is the active BPMN element; find its type in BPMN XML; `<bpmn:userTask>` means the process awaits a human task. **IMPORTANT:** `latestRunStatus` on the instance is NOT useful for HITL detection — a process waiting on a human task still shows as `"Running"`.

```typescript
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
import type { BpmnXmlString, ProcessInstanceGetVariablesResponse } from '@uipath/uipath-typescript/maestro-processes';

interface HitlStatus {
  isUserTask: boolean;
  activityType: string;  // e.g., "user task", "service task", "script task"
  elementId: string | null;
}

export async function detectHitlStatus(
  processInstances: ProcessInstances,
  instanceId: string,
  folderKey: string,
  // Optional: pass pre-fetched data to avoid redundant calls
  prefetchedVariables?: ProcessInstanceGetVariablesResponse,
  prefetchedBpmn?: BpmnXmlString,
): Promise<HitlStatus> {
  const variables = prefetchedVariables ?? await processInstances.getVariables(instanceId, folderKey);
  const lastElement = variables.elements[variables.elements.length - 1];
  const elementId = lastElement?.elementId ?? null;
  if (!elementId) return { isUserTask: false, activityType: 'Unknown', elementId: null };
  const bpmnXml = prefetchedBpmn ?? await processInstances.getBpmn(instanceId, folderKey);
  const match = bpmnXml.match(new RegExp(`<bpmn:(\\w+)\\s+id="${elementId}"`));
  if (!match?.[1]) return { isUserTask: false, activityType: 'Unknown', elementId };
  const activityType = match[1].replace(/([A-Z])/g, ' $1').trim().toLowerCase();
  return { isUserTask: activityType === 'user task', activityType, elementId };
}
```

### Usage in a component

```typescript
import { useMemo, useCallback, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePolling } from '../hooks/usePolling';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
import type { GlobalVariableMetaData } from '@uipath/uipath-typescript/maestro-processes';
import { detectHitlStatus } from '../utils/hitl';

interface InstanceData {
  variables: ProcessInstanceGetVariablesResponse;
  bpmnXml: BpmnXmlString;
  hitl: HitlStatus;
}

function InstancePanel({ instanceId, folderKey }: { instanceId: string; folderKey: string }) {
  const { sdk, isAuthenticated } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchInstanceData = useCallback(async () => {
    const [variables, bpmnXml] = await Promise.all([
      processInstances.getVariables(instanceId, folderKey),
      processInstances.getBpmn(instanceId, folderKey),
    ]);
    const hitl = await detectHitlStatus(processInstances, instanceId, folderKey, variables, bpmnXml);
    return { variables, bpmnXml, hitl };
  }, [processInstances, instanceId, folderKey]);

  const { data, isLoading, isActive } = usePolling<InstanceData>({
    fetchFn: fetchInstanceData,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    deps: [instanceId],  // Reset and refetch when instance changes
  });

  // Flicker prevention — see "Flicker-free updates" for full explanation
  const lastDataRef = useRef<InstanceData | null>(null);
  const lastInstanceIdRef = useRef(instanceId);
  const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());

  if (instanceId !== lastInstanceIdRef.current) {
    lastInstanceIdRef.current = instanceId;
    lastDataRef.current = null;
    accumulatedVarsRef.current = new Map();
  }
  if (data) lastDataRef.current = data;
  const displayData = lastDataRef.current;

  if (displayData) {
    for (const v of displayData.variables.globalVariables) {
      accumulatedVarsRef.current.set(v.id, v);
    }
  }
  const displayVars = [...accumulatedVarsRef.current.values()].sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  if (!displayData) return <div>Loading...</div>;

  // Render using displayVars (accumulated + sorted) and displayData.hitl
}
```

Render `data.hitl.isUserTask` as **"Waiting on Human Review"** / **"This instance requires human input to continue"**; otherwise **"Automated Process"** and `data.hitl.activityType`. Render `data.bpmnXml` in `BpmnDiagram` and `displayVars` in the stable process-data table. When `displayData` is absent, render loading.

Render HITL status:

```tsx
{data?.hitl.isUserTask ? (
  <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
    <div className="p-2 bg-amber-100 rounded-lg">
      <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    </div>
    <div>
      <h4 className="font-semibold text-amber-900">Waiting on Human Review</h4>
      <p className="text-sm text-amber-700">This instance requires human input to continue</p>
    </div>
    {/* Add "Open Task" button if task link is available */}
  </div>
) : (
  <div className="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
    <div className="p-2 bg-gray-100 rounded-lg">
      <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <div>
      <h4 className="font-semibold text-gray-900">Automated Process</h4>
      <p className="text-sm text-gray-600">Current step: {data?.hitl.activityType}</p>
    </div>
  </div>
)}
```

### Getting the task for the instance

When HITL is detected, you may also want to open the task in Action Center: find it with the `CreatorJobKey` OData filter; `instanceId` **is** the `CreatorJobKey`:

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
import { buildTaskUrl, getEmbedTaskUrl } from '../utils/formatters';

const result = await tasks.getAll({
  filter: `CreatorJobKey eq ${instanceId}`,
  pageSize: 10,
});
const pendingTask = result.items.find(t => !t.isCompleted) ?? null;
if (pendingTask) {
  const taskLink = buildTaskUrl(pendingTask.id);
  const embedUrl = getEmbedTaskUrl(taskLink);
  // Open in iframe (TaskEmbed below)...
}
```

## Embedding Action Center Tasks (HITL)

Embed a human-in-the-loop task, action app, or escalation in an iframe. Standard URL:

```text
https://cloud.uipath.com/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

The embed URL inserts `embed_/` after the origin:

```text
https://cloud.uipath.com/embed_/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

### API-to-Cloud URL mapping

**CRITICAL:** The API base URL comes from `<meta name="uipath:base-url">`; API and cloud UI hostnames differ. You must map them using this table:

| API URL | Cloud UI URL |
|---|---|
| `https://api.uipath.com` | `https://cloud.uipath.com` |
| `https://<PREFIX>.api.uipath.com` | `https://<PREFIX>.uipath.com` |
| Any other host (Automation Suite, custom) | Same host, unchanged |

**Never use naive replacement** such as `baseUrl.replace('api.', 'cloud.')`; it breaks prefixed hosts (produces `<PREFIX>.cloud.uipath.com`, which is wrong). Add to `src/utils/formatters.ts`:

```typescript
export function apiToCloudUrl(apiBaseUrl: string): string {
  try {
    const url = new URL(apiBaseUrl);
    let cloudHost = url.hostname.replace('api.uipath.com', 'uipath.com');
    if (cloudHost === 'uipath.com') cloudHost = 'cloud.uipath.com';
    return `${url.protocol}//${cloudHost}`;
  } catch { return apiBaseUrl; }
}
```

### URL helper functions

Create or extend `src/utils/formatters.ts`:

```typescript
export const getEmbedTaskUrl = (taskUrl: string): string => {
  try {
    const url = new URL(taskUrl);
    const parts = url.pathname.split('/');
    const orgId = parts[1], tenantId = parts[2], taskId = parts[parts.length - 1];
    return `${url.origin}/embed_/${orgId}/${tenantId}/actions_/current-task/tasks/${taskId}`;
  } catch (e) {
    console.error('Error parsing task URL:', e);
    return taskUrl;
  }
};

function readUipathMeta(key: string): string {
  return document.querySelector(`meta[name="uipath:${key}"]`)?.getAttribute('content') ?? '';
}

export function buildTaskUrl(taskId: number | string): string {
  const baseUrl = readUipathMeta('base-url');
  const org = readUipathMeta('org-name');
  const tenant = readUipathMeta('tenant-name');
  return `${apiToCloudUrl(baseUrl)}/${org}/${tenant}/actions_/current-task/tasks/${taskId}`;
}
```

Find tasks with ``tasks.getAll({ filter: `CreatorJobKey eq ${instanceId}`, pageSize: 10 })``, select `result.items.find(t => !t.isCompleted) ?? null`, then use `buildTaskUrl(pendingTask.id)` and `getEmbedTaskUrl(taskLink)`. **Do NOT construct URLs manually.** Use `apiToCloudUrl()` and `buildTaskUrl()` for all environments.

Render the embed in a closeable modal overlay:

```tsx
import { getEmbedTaskUrl } from '../utils/formatters';

export const TaskEmbed = ({ taskLink, onClose }: { taskLink: string; onClose: () => void }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl w-[90vw] h-[90vh] flex flex-col">
      <div className="flex justify-between items-center p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Task Details</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      <div className="flex-1 p-1"><iframe src={getEmbedTaskUrl(taskLink)} className="w-full h-full rounded border-0" title="Action Center Task" /></div>
    </div>
  </div>
);
```

No extra auth is needed: the iframe shares the UiPath browser session. The `embed_/` prefix is required; without it the page renders full navigation chrome. Detect HITL with `getVariables()` + `getBpmn()`, never `latestRunStatus`. Use a modal overlay so the user can close it and return to the app.

## Tabular Data: Don't Dump Every Row in One Scroll

Operational tables may contain 100–10,000+ rows. Do not render all rows in one scroll:

- **Paginated rows** (default for >50 rows): page size 25–50, next/previous/page-number controls, and `Showing X–Y of Z`.
- **Virtualized scroll** for very large lists, 5k+: use `react-window` or `@tanstack/react-virtual` only when genuinely needed.
- **Top-N + "see all"** for informational tables such as Top 10 oldest open.

For mixed KPI/chart/table screens prefer pagination. A scroll-everything layout is acceptable for CSV export, never for a dashboard.

## Preventing Text Overflow

Apply these rules whenever rendering dynamic strings:

- Flex/grid text parents need `min-w-0`; text needs `truncate` or `line-clamp-N`. `truncate` alone does nothing without `min-w-0` because flex children default to intrinsic width.
- **Pair every truncation (e.g. flex, table cell, card) with `title={fullValue}`** so the full string is readable on hover.
- SVG chart axes do not honor CSS truncation: shorten with the library's `tickFormatter`, keep the full value in the tooltip, prefer `displayName` over `name` for long choice values, or use a horizontal bar chart.
- Tables need `table-fixed`, explicit column widths, `max-w-0` on `<td>`, and a truncated inner element.
- Fixed-height cards need `overflow-hidden` and `line-clamp-N`.