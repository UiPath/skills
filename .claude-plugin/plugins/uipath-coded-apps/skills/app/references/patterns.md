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
}

interface UsePollingResult<T> {
  data: T | null;
  isPolling: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  start: () => void;
  stop: () => void;
  isActive: boolean;
  lastUpdated: Date | null;
}

export function usePolling<T>({
  fetchFn, interval = 5000, enabled = true,
  onSuccess, onError, immediate = true,
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isActive, setIsActive] = useState(enabled);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => { setIsActive(enabled); }, [enabled]);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => { fetchFnRef.current = fetchFn; }, [fetchFn]);
  useEffect(() => { onSuccessRef.current = onSuccess; }, [onSuccess]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const executeFetch = useCallback(async () => {
    setIsPolling(true);
    setError(null);
    try {
      const result = await fetchFnRef.current();
      setData(result);
      setLastUpdated(new Date());
      onSuccessRef.current?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      setIsPolling(false);
    }
  }, []);

  const start = useCallback(() => setIsActive(true), []);
  const stop = useCallback(() => {
    setIsActive(false);
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
  }, []);
  const refetch = useCallback(async () => { await executeFetch(); }, [executeFetch]);

  useEffect(() => {
    if (!isActive || !enabled) {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      return;
    }
    if (intervalRef.current) { clearInterval(intervalRef.current); }
    if (immediate) executeFetch();
    intervalRef.current = setInterval(executeFetch, interval);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [isActive, enabled, interval, immediate, executeFetch]);

  return { data, isPolling, error, refetch, start, stop, isActive, lastUpdated };
}
```

### Usage with SDK services

```typescript
import { useMemo, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePolling } from '../hooks/usePolling';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';

function InstanceMonitor({ instanceId, folderKey }: { instanceId: string; folderKey: string }) {
  const { sdk, isAuthenticated } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchVariables = useCallback(async () => {
    return processInstances.getVariables(instanceId, folderKey);
  }, [processInstances, instanceId, folderKey]);

  const { data: variables, isPolling, error } = usePolling({
    fetchFn: fetchVariables,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    immediate: true,
  });

  // Render variables...
}
```

### Key options

- `enabled` — tie to a condition (e.g., `!!selectedInstance`) so polling only runs when needed
- `immediate: false` — skip first fetch if the initial data is already loaded by another effect
- `interval` — default 5000ms; increase for less-critical data to reduce API load

## BPMN Diagram Rendering

To visualize Maestro process diagrams, use `bpmn-js` (from bpmn.io) with the BPMN XML returned by `ProcessInstances.getBpmn()`.

### Setup

```bash
npm install bpmn-js
```

Add CSS imports in `src/index.css` (or the component file):

```css
@import 'bpmn-js/dist/assets/diagram-js.css';
@import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';
```

### BPMN Viewer component

```typescript
import { useEffect, useRef } from 'react';
import BpmnViewer from 'bpmn-js/lib/Viewer';

interface BpmnDiagramProps {
  bpmnXml: string;
}

export const BpmnDiagram = ({ bpmnXml }: BpmnDiagramProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !bpmnXml) return;

    const viewer = new BpmnViewer({ container: containerRef.current });

    (async () => {
      try {
        await viewer.importXML(bpmnXml);
        viewer.get('canvas').zoom('fit-viewport');
      } catch (err) {
        console.error('Error rendering BPMN:', err);
      }
    })();

    return () => { viewer.destroy(); };
  }, [bpmnXml]);

  return <div ref={containerRef} style={{ width: '100%', height: '500px' }} />;
};
```

### Fetching BPMN XML

```typescript
// Via service method
const bpmnXml = await processInstances.getBpmn(instanceId, folderKey);

// Or via bound method on an instance object
const instance = await processInstances.getById(instanceId, folderKey);
const bpmnXml = await instance.getBpmn();
```

Then render: `<BpmnDiagram bpmnXml={bpmnXml} />`

## Embedding Action Center Tasks (HITL)

When a user needs to view or complete an Action Center task (human-in-the-loop task, action app, or escalation) inside the app, embed it via iframe using UiPath's embed URL format.

### Embed URL format

The standard Action Center URL looks like:
```
https://cloud.uipath.com/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

The **embed** URL inserts `embed_/` after the origin:
```
https://cloud.uipath.com/embed_/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

### API-to-Cloud URL mapping

**CRITICAL:** The API base URL (`VITE_UIPATH_BASE_URL`) and the cloud UI URL use different hostnames. You must map correctly when constructing task URLs:

| API URL | Cloud UI URL |
|---------|-------------|
| `https://api.uipath.com` | `https://cloud.uipath.com` |
| `https://staging.api.uipath.com` | `https://staging.uipath.com` |
| `https://alpha.api.uipath.com` | `https://alpha.uipath.com` |

**NEVER use naive string replacement** like `baseUrl.replace('api.', 'cloud.')` — this breaks for staging/alpha (produces `staging.cloud.uipath.com` which is wrong).

Add this helper to `src/utils/formatters.ts`:

```typescript
/** Maps an API base URL to the corresponding cloud UI URL */
export function apiToCloudUrl(apiBaseUrl: string): string {
  try {
    const url = new URL(apiBaseUrl);
    // "api.uipath.com" → "cloud.uipath.com"
    // "staging.api.uipath.com" → "staging.uipath.com"
    // "alpha.api.uipath.com" → "alpha.uipath.com"
    let cloudHost = url.hostname.replace('api.uipath.com', 'uipath.com');
    if (cloudHost === 'uipath.com') cloudHost = 'cloud.uipath.com';
    return `${url.protocol}//${cloudHost}`;
  } catch {
    return apiBaseUrl;
  }
}
```

### URL helper functions

Create `src/utils/formatters.ts` (or add to existing):

```typescript
/** Converts a standard Action Center URL to an embeddable iframe URL */
export const getEmbedTaskUrl = (taskUrl: string): string => {
  try {
    const url = new URL(taskUrl);
    const parts = url.pathname.split('/');
    const orgId = parts[1];
    const tenantId = parts[2];
    const taskId = parts[parts.length - 1];
    return `${url.origin}/embed_/${orgId}/${tenantId}/actions_/current-task/tasks/${taskId}`;
  } catch (e) {
    console.error('Error parsing task URL:', e);
    return taskUrl;
  }
};

/** Constructs a standard Action Center task URL from components */
export function buildTaskUrl(taskId: number | string): string {
  const baseUrl = import.meta.env.VITE_UIPATH_BASE_URL || '';
  const org = import.meta.env.VITE_UIPATH_ORG_NAME || '';
  const tenant = import.meta.env.VITE_UIPATH_TENANT_NAME || '';
  const cloudHost = apiToCloudUrl(baseUrl);
  return `${cloudHost}/${org}/${tenant}/actions_/current-task/tasks/${taskId}`;
}
```

### Getting the task link

The **preferred** source for a task link is the `actionCenterTaskLink` field from **execution history**. When an execution step is a "User Task" (HITL), the `attributes` JSON contains this link.

**IMPORTANT — match by `elementId`, not by scanning all entries.** Execution history may contain multiple HITL tasks. Always match the specific entry using its `elementId` from BPMN XML or from execution state:

```typescript
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';

// Fetch execution history — always pass folderKey for correct results
const history = await processInstances.getExecutionHistory(instanceId, folderKey);

// Find the SPECIFIC user task entry by elementId
const userTaskEntry = history.find(entry => {
  const attrs = typeof entry.attributes === 'string'
    ? JSON.parse(entry.attributes)
    : entry.attributes;
  return attrs?.elementId === targetElementId;
});

// Extract the task link
let taskLink: string | null = null;
if (userTaskEntry) {
  const attrs = typeof userTaskEntry.attributes === 'string'
    ? JSON.parse(userTaskEntry.attributes)
    : userTaskEntry.attributes;
  taskLink = attrs?.actionCenterTaskLink ?? null;
}

// Fallback: construct URL using buildTaskUrl (only if you have the task ID)
if (!taskLink && taskId) {
  taskLink = buildTaskUrl(taskId);
}
```

**When `actionCenterTaskLink` is NOT available:**
- The execution history entry doesn't exist yet (task just created)
- The process is a case instance and execution history may not include action center links
- The entry exists but has no `actionCenterTaskLink` in attributes

In these cases, use `buildTaskUrl(taskId)` as a fallback. **Do NOT construct the URL manually** — always use the `apiToCloudUrl` + `buildTaskUrl` helpers to ensure correct environment mapping.

### iframe component

```typescript
import { getEmbedTaskUrl } from '../utils/formatters';

interface TaskEmbedProps {
  taskLink: string;
  onClose: () => void;
}

export const TaskEmbed = ({ taskLink, onClose }: TaskEmbedProps) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl w-[90vw] h-[90vh] flex flex-col">
      <div className="flex justify-between items-center p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Task Details</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      <div className="flex-1 p-1">
        <iframe
          src={getEmbedTaskUrl(taskLink)}
          className="w-full h-full rounded border-0"
          title="Action Center Task"
        />
      </div>
    </div>
  </div>
);
```

### Key points

- **No extra auth needed**: The iframe loads from the same UiPath domain, so the user's existing browser session handles authentication automatically.
- **`embed_/` prefix is required**: Without it, the action center page renders with full navigation chrome. The embed URL gives a clean, frameable view.
- **Task link source**: Prefer `actionCenterTaskLink` from execution history (matched by `elementId`). Fall back to `buildTaskUrl(taskId)` only when history doesn't have a link.
- **Always pass `folderKey`** to `getExecutionHistory()` — omitting it may return empty results or incorrect data.
- **Use `apiToCloudUrl()`** — never manually convert API URLs to cloud URLs with string replacement.
- **Use a modal overlay**: Render the iframe in a modal (like the example above) so the user can close it and return to the app.
