---
description: Use when the user asks to create a new UiPath web app, build a React dashboard with UiPath data, add UiPath SDK services (@uipath/uipath-typescript) to an existing React project, or deploy a coded app to UiPath Cloud. Covers project scaffolding, OAuth authentication, SDK service integration (Entities, Tasks, Processes, Assets, Queues, Buckets, Maestro), pagination, polling, BPMN rendering, and deployment via UiPath CLI.
---

# Creating UiPath Coded Apps

## 1. Project Initialization

### Step 1: Ask for environment, org, tenant, and whether they have a client ID

Use a **single** `AskUserQuestion` call with exactly these 4 questions:

```
Question 1:
  question: "Which UiPath environment?"
  header: "Environment"
  options:
    - label: "cloud (Recommended)"   description: "Production — cloud.uipath.com"
    - label: "staging"               description: "Staging — staging.uipath.com"
    - label: "alpha"                 description: "Alpha — alpha.uipath.com"
  multiSelect: false

Question 2:
  question: "What is your UiPath organization name?"
  header: "Org name"
  options:
    - label: "I'll type it"   description: "Select Other and type your org name"
    - label: "Find from browser"   description: "I'm logged into UiPath — read org from URL"
  multiSelect: false

Question 3:
  question: "What is your UiPath tenant name?"
  header: "Tenant"
  options:
    - label: "DefaultTenant"   description: "Most common default tenant name"
    - label: "I'll type it"   description: "Select Other and type your tenant name"
  multiSelect: false

Question 4:
  question: "Do you have an existing OAuth client ID for this app?"
  header: "Client ID"
  options:
    - label: "Yes, I'll provide it"   description: "I already have a client ID — select Other and paste it"
    - label: "No, create one for me"  description: "Use browser automation to create one in UiPath admin"
  multiSelect: false
```

### Step 2: Resolve the org name

**If user typed their org name or selected "Other":** Use the value they provided.

**If user selected "Find from browser":** Use Playwright MCP to check the current browser tab. Navigate to the UiPath cloud host for the chosen environment (e.g., `https://staging.uipath.com`). Take a `browser_snapshot` — if the user is logged in, the URL or page content will contain the org name. Extract it from the URL path (it's the first segment after the domain: `https://staging.uipath.com/{orgName}/...`).

### Step 3: Get or create the client ID

**If the user provided a client ID** (selected "Other" and pasted it): Use it directly.

**If the user chose "No, create one for me":** First determine which OAuth scopes are needed based on the services the app will use (read `references/oauth-scopes.md`). Then use Playwright MCP browser automation to create an external application in the UiPath admin portal. Follow the detailed steps in [oauth-client-setup.md](references/oauth-client-setup.md).

The browser automation will:
1. Navigate to `https://{cloud-host}/{orgName}/portal_/admin/external-apps/oauth`
2. Click "Add application"
3. Set app name, select "Non-Confidential application"
4. Add the required OAuth scopes
5. Enter the redirect URI (`http://localhost:5173`)
6. Click "Add" and extract the generated Application ID (client ID)

### Step 4: Run setup script

Once you have all values (org, tenant, client ID, environment, scopes), run the setup script.

**Script paths:** The setup and validate scripts are in this skill's `scripts/` subdirectory. Use the **"Base directory for this skill"** path shown at the top when this skill was loaded — that is the absolute path to this skill's directory.

```bash
bash <skill-base-dir>/scripts/setup.sh <app-name> <org-name> <tenant-name> <client-id> "<scopes>" <environment>
```

All 4 required values are passed as positional arguments — the script has no interactive prompts.

It creates the full project:
- Vite project with React + TypeScript template
- `.env` with UiPath OAuth configuration (see `.env` structure below)
- `src/hooks/useAuth.tsx` — auth hook handling OAuth callback detection (`sdk.isInOAuthCallback()` / `sdk.completeOAuth()`) and login (`sdk.initialize()`)
- `src/App.tsx` — wraps app with `<AuthProvider config={authConfig}>`, builds `UiPathSDKConfig` from env vars
- Tailwind CSS configured with directives in `src/index.css`

### `.env` structure

The `.env` file uses this structure:

```env
UIPATH_BASE_URL=https://api.uipath.com
UIPATH_REDIRECT_URI=http://localhost:5173
UIPATH_ORG_NAME=<org-name>
UIPATH_TENANT_NAME=<tenant-name>

VITE_UIPATH_BASE_URL=${UIPATH_BASE_URL}
VITE_UIPATH_REDIRECT_URI=${UIPATH_REDIRECT_URI}
VITE_UIPATH_CLIENT_ID=<client-id>
VITE_UIPATH_ORG_NAME=<org-name>
VITE_UIPATH_TENANT_NAME=<tenant-name>
VITE_UIPATH_SCOPES=<scopes>
```

**Why `${}` for BASE_URL and REDIRECT_URI only:** When the app is deployed via the UiPath CLI, the CLI overwrites `UIPATH_BASE_URL` and `UIPATH_REDIRECT_URI` with production values. The `VITE_` versions reference them via `${}` so they automatically pick up the new values. The other variables (client ID, org, tenant, scopes) are set directly.

**Port availability:** Before writing `http://localhost:5173` as the redirect URI, check that port 5173 is free (e.g., `lsof -i :5173`). If it's in use, pick the port which you get on doing npm run dev and put that in `UIPATH_REDIRECT_URI`. and then stop npm run dev server

After setup, validate the project:

```bash
bash <skill-base-dir>/scripts/validate.sh ./<app-name>
```

Customize the `AppContent` component in `src/App.tsx` for the user's needs.

### Build workflow — start writing immediately

**Execute these steps in order immediately after validate passes:**

1. **Read the reference files** for the services you already chose scopes for (you decided the services when picking scopes — use the same list). Do NOT read scaffolded files (`useAuth.tsx`, `App.tsx`, `vite.config.ts`, `.env`) — this skill documents their contents.
2. **Write `src/App.tsx`** — replace the generated one with the actual layout (sidebar, main content area, routing). Define component imports and shared state here.
3. **Write components one by one** — simplest first (list views), then complex (detail panels). Each component you write can reference previous ones, keeping exports consistent.
4. **Run the smoke test** (see below).

**Do NOT:**
- Re-read files you just wrote to "review quality"

### Local smoke test

After scaffolding is complete and the app has been customized, **always** run the dev server to verify the app compiles and starts without errors:

```bash
cd <app-name> && npm run dev
```

Run this in the background. Wait a few seconds for Vite to start, then check the output for:
- **Success**: `Local: http://localhost:<port>` — the app is running. Report the URL to the user.
- **Failure**: compilation errors or missing dependencies — fix them before considering the task done.

**IMPORTANT — verify the port matches the redirect URI:** Vite may start on a different port than 5173 if that port is busy (e.g., 5174, 5175). Check the actual port in Vite's output. If it differs from `UIPATH_REDIRECT_URI` in `.env`, update `.env` to match (e.g., `UIPATH_REDIRECT_URI=http://localhost:5174`). OAuth will fail silently if the redirect URI doesn't match the running port.

If there are TypeScript or build errors, fix the issues and re-run `npm run dev` until the app starts cleanly. Do not mark the task as complete until the dev server starts successfully.

## 2. UiPath Services Overview

Understand what each service area represents before using its SDK module:

- **Orchestrator Processes** — the core execution unit in UiPath. A "process" can be an RPA automation, an agentic process (AI agent), or a case management process. **To start any of these — including Maestro processes, cases, or agents — use `Processes.start()`** from `@uipath/uipath-typescript/processes`. The SDK does not have a dedicated agent service, but agents are processes and can be started the same way.
- **Buckets** — cloud storage buckets used by automations to store and retrieve files (documents, data exports, etc.).
- **Assets** — key-value configuration stored in Orchestrator (credentials, settings, connection strings) that automations read at runtime.
- **Queues** — work queues that hold transaction items for automations to process (e.g., invoice records, customer requests).
- **Entities (Data Fabric)** — structured data tables in UiPath's Data Service. Think of them as database tables with schema, records, and relationships. ChoiceSets are enum-like picklists for entity fields.
- **Tasks (Action Center)** — human-in-the-loop tasks or escalations created by automations when human input/approval is needed. Users can create, assign, reassign, and complete tasks.
- **Maestro Processes & Cases** — orchestration layer for complex workflows. MaestroProcesses are monitored process definitions; ProcessInstances are running executions. Cases are long-running business cases with stages. **To start a Maestro process or case, use `Processes.start()`** (they are Orchestrator processes underneath).
- **Process Incidents** — errors or exceptions that occur during process instance execution.

## 3. SDK Module Import Table

| Subpath | Classes |
|---------|---------|
| `@uipath/uipath-typescript/core` | `UiPath`, `UiPathError`, `UiPathSDKConfig`, pagination types |
| `@uipath/uipath-typescript/entities` | `Entities`, `ChoiceSets` |
| `@uipath/uipath-typescript/tasks` | `Tasks` |
| `@uipath/uipath-typescript/maestro-processes` | `MaestroProcesses`, `ProcessInstances`, `ProcessIncidents` |
| `@uipath/uipath-typescript/cases` | `Cases`, `CaseInstances` |
| `@uipath/uipath-typescript/assets` | `Assets` |
| `@uipath/uipath-typescript/queues` | `Queues` |
| `@uipath/uipath-typescript/buckets` | `Buckets` |
| `@uipath/uipath-typescript/processes` | `Processes` |

Types, enums, and option interfaces are exported from the same subpath as their service class.

## 4. Type-Driven Development Rules

When using any SDK service method, follow these rules strictly:

1. **Always import the response type** from the same subpath as the service class. Example: `import type { AssetGetResponse } from '@uipath/uipath-typescript/assets'`
2. **Read the imported interface** to know what fields are available. Only access properties defined in the type. Never guess field names.
3. **Import option types** for method parameters. Example: `import type { AssetGetAllOptions } from '@uipath/uipath-typescript/assets'`
4. **Import enums** from the SDK for any field that uses an enum value. Example: `import { TaskPriority, TaskType, TaskStatus } from '@uipath/uipath-typescript/tasks'`
5. **Use `OperationResponse<T>`** type for mutation results (import from `@uipath/uipath-typescript`). Has shape `{ success: boolean; data: T }`.
6. **Method-attached responses**: Some `getById`/`getAll` responses include callable methods. The response type is a union: `EntityGetResponse = RawEntityGetResponse & EntityMethods`. Read the `*Methods` interface to know available instance methods.
7. **Reference files are your primary source.** The `references/` files in this skill contain all method signatures, types, enums, and fields you need. **Do NOT explore `node_modules` or the SDK source code if the information is already in a reference file.** Only fall back to `node_modules/@uipath/uipath-typescript/` as a last resort when the reference files don't cover something (e.g., a newly added method or an edge case not documented). Check `.d.ts` files for types if you must.

## 5. Anti-Patterns — NEVER Do These

- **NEVER import service classes from the root package** (`import { Entities } from '@uipath/uipath-typescript'`). Service classes are only available via subpath imports: `@uipath/uipath-typescript/entities`, `/tasks`, `/processes`, etc. The root export only has the deprecated legacy `UiPath` class and type interfaces.
- **NEVER use deprecated dot-chain access** like `sdk.entities.getAll()` or `sdk.maestro.processes.instances.getVariables(...)`. The legacy `UiPath` class from `@uipath/uipath-typescript` supports this but it is **deprecated**. Always use constructor-based DI: `import { UiPath } from '@uipath/uipath-typescript/core'` and `const entities = new Entities(sdk)`.
- **NEVER guess field names** on response objects. Import the response type and read its interface. Fields differ across services and don't follow a single pattern.
- **NEVER hardcode `VITE_UIPATH_BASE_URL` or `VITE_UIPATH_REDIRECT_URI`.** These two must reference their `UIPATH_` counterparts via `${}` (e.g., `VITE_UIPATH_BASE_URL=${UIPATH_BASE_URL}`) so the CLI can overwrite them during deployment. Other `VITE_` vars (`CLIENT_ID`, `ORG_NAME`, `TENANT_NAME`, `SCOPES`) are set directly.
- **NEVER add `offline_access` to the scopes string.** It is not a valid scope for this SDK. Only use scopes from `references/oauth-scopes.md`.
- **NEVER call paginated methods without `pageSize`** for production use. Unpaginated calls fetch all records and can be slow or hit limits.
- **NEVER store or manage tokens manually.** The SDK handles token persistence in `sessionStorage` and automatic refresh on 401. Do not read/write `sessionStorage` for auth tokens.
- **NEVER call `sdk.initialize()` more than once.** It triggers the full OAuth redirect. Use `sdk.isAuthenticated()` or `useAuth().isAuthenticated` to check status first.
- **NEVER mix `folderId` (number) with `folderKey` (string).** Orchestrator services (Assets, Queues, Buckets, Processes) use numeric `folderId`. Maestro services (ProcessInstances, CaseInstances) use string `folderKey`. Using the wrong type will silently fail or return empty results.
- **NEVER explore `node_modules` or SDK source code when the skill's `references/` files already contain the information.** The reference files have all method signatures, types, enums, and fields. Exploring `node_modules` wastes tokens and time. Only use `node_modules` as a last resort for information not covered in any reference file.

## 6. Authentication

The setup script generates `src/hooks/useAuth.tsx` which provides an `AuthProvider` context and `useAuth` hook. This is the primary auth interface for components.

### useAuth hook API

```typescript
const { isAuthenticated, isLoading, sdk, login, logout, error } = useAuth();
```

| Field | Type | Description |
|---|---|---|
| `isAuthenticated` | `boolean` | Whether the user has a valid token |
| `isLoading` | `boolean` | True during login/initialization |
| `sdk` | `UiPath` | The SDK instance — pass to service constructors |
| `login` | `() => Promise<void>` | Triggers OAuth login flow (redirects to UiPath) |
| `logout` | `() => void` | Clears tokens from sessionStorage and creates a fresh SDK instance |
| `error` | `string \| null` | Auth error message, if any |

### How auth works

1. **On mount**, `AuthProvider` checks `sdk.isInOAuthCallback()`. If the user is returning from the OAuth redirect, it calls `sdk.completeOAuth()` to exchange the auth code for tokens.
2. **Login** calls `sdk.initialize()`, which redirects the user to UiPath's OAuth consent page.
3. **After consent**, UiPath redirects back to the app. Step 1 detects the callback and completes the flow.
4. **Logout** must clear the token from `sessionStorage` **before** creating a new `UiPath` instance. The SDK stores OAuth tokens in `sessionStorage` under the key `uipath_sdk_user_token-{clientId}`, and a new UiPath instance auto-loads tokens from storage on construction. If you don't clear storage first, the new instance immediately reloads the old token and the user stays logged in. The correct logout pattern:
   ```typescript
   const logout = () => {
     // Clear OAuth tokens from sessionStorage FIRST
     sessionStorage.removeItem(`uipath_sdk_user_token-${clientId}`);
     sessionStorage.removeItem('uipath_sdk_oauth_context');
     sessionStorage.removeItem('uipath_sdk_code_verifier');
     setIsAuthenticated(false);
     setError(null);
     setSdk(new UiPath(config));
   };
   ```
5. **Token refresh** is automatic. When a service call gets a 401, the SDK refreshes the token using the refresh token internally. App code never needs to handle this.
6. **Token persistence**: OAuth tokens are stored in `sessionStorage` (key: `uipath_sdk_user_token-{clientId}`), so they survive page refreshes within the same tab.

### Additional UiPath methods

These are available on the `sdk` instance from `useAuth()` but not directly exposed by the hook:

- **`sdk.isInitialized()`** — returns `boolean`. Check if SDK has completed initialization before making service calls.
- **`sdk.getToken()`** — returns `string | undefined`. The raw access token. Only needed for direct API calls outside the SDK or debugging.
- **`sdk.config`** — read-only `{ baseUrl, orgName, tenantName }`. Useful for displaying the connected org/tenant in the UI.

### When to use what

| Scenario | What to use |
|---|---|
| Check if user is logged in | `isAuthenticated` from `useAuth()` |
| Show a login button | `login` from `useAuth()` |
| Log the user out | `logout` from `useAuth()` |
| Create a service instance | `new ServiceClass(sdk)` where `sdk` is from `useAuth()` |
| Pass token to a non-SDK API | `sdk.getToken()` |
| Show which org is connected | `sdk.config.orgName` |
| Guard a route before auth completes | `isLoading` from `useAuth()` |

## 7. OAuth Scopes

**CRITICAL: Only use scopes from [oauth-scopes.md](references/oauth-scopes.md).** That file is the single source of truth for which OAuth scopes each SDK method requires.

Rules:
- **Read `references/oauth-scopes.md`** before deciding scopes. Find the exact methods the app will use and collect their scopes from the tables.
- **Only include scopes listed in that file.** Never guess or invent scopes. Do NOT add scopes that don't appear there (e.g., `offline_access` is NOT a valid scope for the `scopes` field).
- **Only request scopes the app actually needs** based on which SDK methods it calls. Don't add broad scopes "just in case."

## 8. Service Usage Pattern in Components

**Data fetching rules — follow these for every component:**

1. **Always use pagination when available.** If a service method supports pagination, always pass `pageSize` and build pagination controls in the UI (next/previous buttons, page indicators). Never call `getAll()` without pagination options for methods that support it.
2. **Show data as it arrives.** Don't wait for all fetches to complete before rendering. Use independent loading states per data source so each section renders as soon as its data is ready.
3. **Fetch in parallel.** When a component needs data from multiple services, use `Promise.all()` or separate `useEffect` hooks with independent state — never await one fetch before starting another unrelated one.

SDK service pattern (use in every component):

```typescript
const { sdk } = useAuth();
const service = useMemo(() => new ServiceClass(sdk), [sdk]);
// Paginated: await service.getAll({ pageSize: 20 })
// Non-paginated: await service.getAll()
// By ID: await service.getById(id, folderId)
// Errors: catch (err) { err instanceof UiPathError ? err.message : 'Failed' }
// Parallel: const [a, b] = await Promise.all([svcA.getAll(...), svcB.getAll(...)])
```

## 9. Pagination

Import pagination types from `@uipath/uipath-typescript/core`:

- `PaginationOptions`: `{ pageSize?, cursor?, jumpToPage? }` (cursor and jumpToPage are mutually exclusive)
- `PaginatedResponse<T>`: `{ items, hasNextPage, nextCursor?, previousCursor?, totalCount?, currentPage?, totalPages?, supportsPageJump }`
- `NonPaginatedResponse<T>`: `{ items, totalCount? }`

Behavior:
- No pagination options passed -> returns `NonPaginatedResponse<T>`
- Any pagination option passed (pageSize, cursor, or jumpToPage) -> returns `PaginatedResponse<T>`

Cursor navigation example:

```typescript
// First page
const page1 = await service.getAll({ pageSize: 10 });

// Next page using cursor
if (page1.hasNextPage && page1.nextCursor) {
  const page2 = await service.getAll({ cursor: page1.nextCursor });
}

// Jump to page (only for offset-based services: Assets, Queues, Tasks, Entities)
const page5 = await service.getAll({ jumpToPage: 5, pageSize: 10 });
```

### Type narrowing for pagination responses

TypeScript narrows the return type at compile-time based on whether pagination options are passed. At runtime, use `'hasNextPage' in result` to discriminate — this field exists only on `PaginatedResponse`, never on `NonPaginatedResponse`.

```typescript
import type { PaginatedResponse } from '@uipath/uipath-typescript/core';

// Pattern 1: When you always pass pagination options, assert the type
const result = await tasks.getAll({ pageSize: 10 });
// TypeScript already infers PaginatedResponse here, but if using dynamic options:
const paginated = result as PaginatedResponse<TaskGetResponse>;

// Pattern 2: When options are dynamic and you don't know the return type
const result = await tasks.getAll(options);
if ('hasNextPage' in result) {
  // PaginatedResponse — safe to access nextCursor, supportsPageJump, etc.
  if (result.hasNextPage && result.nextCursor) {
    const nextPage = await tasks.getAll({ cursor: result.nextCursor });
  }
} else {
  // NonPaginatedResponse — only has items and totalCount
  console.log(`All ${result.items.length} items returned`);
}
```

## 10. Polling, BPMN Rendering & Embedding Action Tasks

For real-time data updates, process diagram visualization, and embedding HITL tasks, see the patterns reference.

**MANDATORY — read [patterns.md](references/patterns.md)** when building components that need:
- Auto-refreshing data (polling hook implementation + SDK usage example)
- BPMN diagram rendering (`bpmn-js` setup, viewer component, fetching XML)
- Embedding Action Center tasks / HITL tasks / action apps inside the app via iframe (embed URL format, task link extraction from execution history, iframe component)

## 11. Error Handling

All SDK errors extend `UiPathError` (import from `@uipath/uipath-typescript/core`).

Specific error types: `AuthenticationError`, `AuthorizationError`, `ValidationError`, `NotFoundError`, `RateLimitError`, `ServerError`, `NetworkError`.

```typescript
import { UiPathError, AuthenticationError, NotFoundError } from '@uipath/uipath-typescript/core';

try {
  const result = await service.getById(id, folderId);
} catch (err) {
  if (err instanceof AuthenticationError) {
    // Token expired, trigger re-login
  } else if (err instanceof NotFoundError) {
    // Resource not found
  } else if (err instanceof UiPathError) {
    // Other SDK error
    console.error(err.message);
  }
}
```

## 12. Service Reference Files

**MANDATORY — read the reference file for each service your component uses** before writing any service code. These contain exact method signatures, types, enums, and bound methods.

**When determining OAuth scopes:** MANDATORY — read [oauth-scopes.md](references/oauth-scopes.md) first. Do NOT guess scopes.

**Do NOT load** `deployment.md` unless the user asks about deploying. Do NOT load reference files for services the app doesn't use.

| Reference | Services | When to load |
|-----------|----------|--------------|
| [data-fabric.md](references/data-fabric.md) | Entities, ChoiceSets | App reads/writes Data Service entities |
| [maestro.md](references/maestro.md) | MaestroProcesses, ProcessInstances, ProcessIncidents, Cases, CaseInstances | App monitors or manages process/case instances |
| [orchestrator.md](references/orchestrator.md) | Assets, Queues, Buckets, Processes | App uses Orchestrator resources or starts processes |
| [action-center.md](references/action-center.md) | Tasks | App creates, assigns, or completes Action Center tasks |
| [patterns.md](references/patterns.md) | usePolling hook, BPMN viewer, embedded action tasks | App needs auto-refreshing data, process diagram rendering, or embedded HITL tasks |
| [deployment.md](references/deployment.md) | UiPath CLI | User asks to deploy the app to UiPath Cloud |
| [oauth-scopes.md](references/oauth-scopes.md) | All | **Always** — read before setting scopes in setup |
| [oauth-client-setup.md](references/oauth-client-setup.md) | Playwright browser automation | User doesn't have a client ID and needs one created via UiPath admin portal |
