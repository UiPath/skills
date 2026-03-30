# Web App File Templates

Ready-to-use boilerplate for a new UiPath Coded Web App (Vite + React + TypeScript). Replace `{{PLACEHOLDER}}` values with project-specific content.

---

## `.env`

```
VITE_UIPATH_CLIENT_ID={{CLIENT_ID}}
VITE_UIPATH_REDIRECT_URI=http://localhost:5173
VITE_UIPATH_SCOPE={{SCOPES}}
VITE_UIPATH_ORG_NAME={{ORG_NAME}}
VITE_UIPATH_TENANT_NAME={{TENANT_NAME}}
VITE_UIPATH_BASE_URL={{BASE_URL}}
```

`{{BASE_URL}}` values: `https://api.uipath.com` (cloud) · `https://staging.api.uipath.com` (staging) · `https://alpha.api.uipath.com` (alpha)

---

## `.env.example`

```
VITE_UIPATH_CLIENT_ID=
VITE_UIPATH_REDIRECT_URI=http://localhost:5173
VITE_UIPATH_SCOPE=
VITE_UIPATH_ORG_NAME=
VITE_UIPATH_TENANT_NAME=
VITE_UIPATH_BASE_URL=https://api.uipath.com
```

---

## `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Uncomment and set base path only if deploying under a sub-path:
  // base: '/{{ROUTING_NAME}}/',
});
```

---

## `src/uipath.ts`

```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
// Add service imports for each selected SDK service — see references/create-web-app.md
// import { Assets } from '@uipath/uipath-typescript/assets';
// import { Entities } from '@uipath/uipath-typescript/entities';
// import { Buckets } from '@uipath/uipath-typescript/buckets';
// import { Processes } from '@uipath/uipath-typescript/processes';
// import { Tasks } from '@uipath/uipath-typescript/tasks';
// import { Queues } from '@uipath/uipath-typescript/queues';
// import { MaestroProcesses, ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
// import { Cases, CaseInstances } from '@uipath/uipath-typescript/cases';
// import { ConversationalAgent } from '@uipath/uipath-typescript/conversational-agent';

export const sdk = new UiPath();

// Instantiate selected services (pass sdk as the argument):
// export const assets = new Assets(sdk);
// export const entities = new Entities(sdk);
```

---

## `src/App.tsx`

```typescript
import { useEffect, useState } from 'react';
import { sdk } from './uipath';

function App() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth();
        }
        if (!sdk.isAuthenticated()) {
          await sdk.initialize();
          return;
        }
        setReady(true);
      } catch (e) {
        setError(String(e));
      }
    };
    init();
  }, []);

  if (error) return <div>Error: {error}</div>;
  if (!ready) return <div>Loading...</div>;

  return (
    <div>
      {/* Your app content */}
    </div>
  );
}

export default App;
```
