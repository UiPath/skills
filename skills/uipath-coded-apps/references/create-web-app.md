# Create a UiPath Coded Web App

Scaffold a new UiPath Coded Web Application using Vite + React + TypeScript with the `@uipath/uipath-typescript` SDK.

## Pre-flight: Collect Required Information

**CRITICAL: You do NOT know these values. You CANNOT infer or assume them. Ask the user and wait for their reply before writing any files.**

### Step 1 — Determine required scopes first

**Before asking the user any setup questions**, figure out what the app needs:

1. From the user's **request**, identify which UiPath services the app will use (e.g., Entities, Tasks, Processes, Maestro, Conversational Agent, Buckets, etc.).
2. Read [oauth-scopes.md](oauth-scopes.md) and collect the exact scopes required for every method those services expose.
3. Compose the full deduplicated space-separated scopes string.

You need these scopes **before** Step 2 so you can tell the user exactly what scopes to configure on their Client ID.

### Step 2 — Ask the user for setup info

Output the following text directly (replace `<scopes>` with the actual scopes from Step 1). **Do NOT call any tools yet — just output this text and wait for the user's reply.**

---

Here's what your app needs:

**OAuth scopes:** `<scopes>`

**Redirect URI:** `http://localhost:5173` (the local dev URL — stored as `redirectUri` in `uipath.json` and injected as the `uipath:redirect-uri` meta tag; the platform injects the production URI automatically at deploy)

Please answer these questions to continue:

**1. App name** — lowercase kebab-case project folder name (e.g. `my-dashboard`)

**2. Environment** — which UiPath environment?
   - `cloud` — Production *(most common)*
   - `staging` — Staging
   - `alpha` — Alpha

**3. Org name** — your UiPath organization slug (from `cloud.uipath.com/<orgName>`)

**4. Tenant name** — your UiPath tenant (often `DefaultTenant`)

**5. Client ID** — do you have an existing OAuth External Application client ID with the scopes above?
   - If yes, paste it
   - If no, say **"create one"** and I'll create it via the `uip admin` CLI

**6. Default UI styling** — apply UiPath's Apollo Vertex design system (`@uipath/apollo-wind` components, semantic tokens, and a light/dark theme toggle out of the box)?
   - `yes` *(recommended)* — apollo-wind + `next-themes` on top of Tailwind: Apollo Vertex design system, light/dark theme toggle out of the box
   - `no` — Tailwind only; bring your own component library

---

**Wait for the user's reply before proceeding.**

### Step 2.5 — Create the External Application (only if user said "create one")

Create it with the `uip admin external-apps` CLI — read [oauth-client-setup.md](oauth-client-setup.md) for prerequisites and full flags. Confirm `uip` is authenticated (`uip login status --output json`), then:

```bash
uip admin external-apps create "<app name>" \
  --non-confidential \
  --user-scope "<scopes from Step 1>" \
  --redirect-uri "http://localhost:5173,http://localhost:5173/" \
  --output json
```

Parse `id` from the response — that is the Client ID. If the CLI returns `403` (no admin permission) or can't authenticate, use the [Manual portal fallback](oauth-client-setup.md#manual-portal-fallback).

### Step 3 — Resolve org name (if not provided)

If the user typed their org name, use it. If they said "find from browser", navigate to the UiPath cloud host for their environment and extract the org name from the URL path (first segment after the domain).

---

## Step 4 — Scaffold the Project

Once you have all values (app name, org, tenant, client ID, environment, scopes), execute the steps below in order. All steps after Step 4.2 run from inside the new project directory.

> **Set `timeout: 300000`** (5 minutes) on every Bash call that runs `npm install` or `npm create vite` — these can take several minutes and the default 2-minute timeout is not enough.

### 4.1 — Resolve the base URL

Map the `<environment>` answer from Step 2 to a base URL using the table in [SKILL.md](../SKILL.md) (Production → `https://api.uipath.com`, Staging → `https://staging.api.uipath.com`, Alpha → `https://alpha.api.uipath.com`). If the user gave a custom URL, use that verbatim. Store as `<base-url>`.

### 4.2 — Create the Vite project

```bash
npx --yes create-vite@latest <app-name> --template react-ts
```

Then `cd` into `<app-name>`. Every subsequent step runs from this directory.

### 4.3 — Install dependencies

Run these as **separate commands** in order. The `--@uipath:registry` flag binds only to commands installing `@uipath/*` packages — do not apply it to the others, and do not run a bare `npm install` with the flag.

**Common (always run):** both Q6 paths use `new UiPath()` (no config) — the SDK reads `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, and `redirectUri` from `<meta name="uipath:*">` tags injected by `@uipath/coded-apps-dev` (locally) or by the platform (in production). Tailwind is shared too.

```bash
# UiPath SDK (registry flag forces public npm to bypass GitHub Packages auth)
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org

# coded-apps-dev Vite plugin — injects <meta name="uipath:*"> tags from
# uipath.json so `new UiPath()` (no config) works in local dev
npm install -D @uipath/coded-apps-dev --@uipath:registry=https://registry.npmjs.org

# Tailwind — shared across both Q6 paths
npm install -D tailwindcss@4 @tailwindcss/postcss postcss autoprefixer
```

> **Why the registry flag?** Users may have `@uipath` scoped to GitHub Packages in their `.npmrc`, which requires authentication and causes a 401. The flag forces `@uipath/*` packages to install from the public npm registry.

**Then branch on the Q6 styling answer for the component layer only:**

- **If `default styling = yes`** *(recommended)* — apollo-wind brings Apollo Vertex tokens, dark-mode toggle, and React components:

  ```bash
  # apollo-wind + apollo-core (UiPath design system, public on npm)
  npm install @uipath/apollo-wind @uipath/apollo-core --@uipath:registry=https://registry.npmjs.org

  # Theme toggle deps
  npm install next-themes lucide-react
  ```

- **If `default styling = no`** — keep the SDK + Tailwind baseline above and bring your own component library. No extra dependencies needed.

### 4.4 — Remove Vite defaults that will be overwritten

`npx create-vite` ships default versions of files we replace in Step 4.5. Delete them first so the Write tool can create them fresh — otherwise each Write requires a Read-first round-trip and produces a benign-but-noisy "Error writing file" message.

- **`default styling = yes`** — also overwrites `src/main.tsx` to wrap `<App>` in the theme provider:

  ```bash
  rm vite.config.ts src/App.tsx src/index.css src/main.tsx
  ```

- **`default styling = no`**:

  ```bash
  rm vite.config.ts src/App.tsx src/index.css
  ```

### 4.5 — Write project files from templates

All file content lives in [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md). For each row below, copy the named section from that file verbatim into the path shown, applying the listed substitutions. Create `src/hooks/` first; the rest of the directories already exist from `create-vite`.

**Pick the template-section column based on the Q6 styling answer.** When the column says `—`, skip that row entirely (the file isn't needed on that path). `uipath.json` and `useAuth.tsx` are shared verbatim — the same SDK init (`new UiPath()` no config) runs on both paths.

| Path | Template section — `default styling = yes` | Template section — `default styling = no` | Substitutions |
|------|---|---|---|
| `vite.config.ts` | `## vite.config.ts` | `## vite.config.ts` | none |
| `uipath.json` | `## uipath.json` | `## uipath.json` | `{{CLIENT_ID}}`, `{{SCOPES}}`, `{{ORG_NAME}}`, `{{TENANT_NAME}}`, `{{BASE_URL}}` |
| `src/hooks/useAuth.tsx` | `## src/hooks/useAuth.tsx` | `## src/hooks/useAuth.tsx` | none |
| `src/components/Theme.tsx` | `## src/components/Theme.tsx (Q6 = yes only)` | — | none |
| `src/main.tsx` | `## src/main.tsx (Q6 = yes only)` | — | none |
| `src/App.tsx` | `## src/App.tsx` → `### Q6 = yes (apollo-wind)` | `## src/App.tsx` → `### Q6 = no (bare Tailwind)` | none |
| `postcss.config.js` | `## postcss.config.js` → `### Q6 = yes (apollo-wind)` | `## postcss.config.js` → `### Q6 = no (bare Tailwind)` | none |
| `src/index.css` | `## src/index.css` → `### Q6 = yes (apollo-wind)` | `## src/index.css` → `### Q6 = no (bare Tailwind)` | none |

> **No `tailwind.config.js` on either path** — Tailwind configuration lives directly in `src/index.css`. No `.env` file either — `uipath.json` (committed) is the single config source for the SDK.

### 4.6 — `.gitignore`

Neither path writes a `.env`, and `uipath.json` is committed (it holds the SDK config — a public OAuth client ID plus org/tenant/base-URL/redirect-URI, no secrets), so no `.gitignore` change is needed for OAuth config. The project `.uipath/` directory created by `codedapp` commands must stay gitignored — it is covered by `npx create-vite`'s default plus `uip codedapp`'s conventions. Verify with `cat .gitignore | grep -i uipath` and add `.uipath/` if missing.

### 4.7 — Verify the scaffold

First, confirm all expected files for your Q6 branch exist. If any are missing, re-run the corresponding row from Step 4.5.

- **`default styling = yes`:** `vite.config.ts`, `uipath.json`, `postcss.config.js`, `src/index.css`, `src/hooks/useAuth.tsx`, `src/components/Theme.tsx`, `src/main.tsx`, `src/App.tsx`
- **`default styling = no`:** `vite.config.ts`, `uipath.json`, `postcss.config.js`, `src/index.css`, `src/hooks/useAuth.tsx`, `src/App.tsx`

Then run `npm run build` to verify the scaffold compiles and SDK imports resolve:

```bash
npm run build
```

If the build fails, parse the error, fix the offending file (most likely the template row you just wrote), and re-run. Cap at 5 fix attempts before asking the user for guidance.

---

## SDK Setup

To call SDK services from the app, create `src/uipath.ts` to instantiate services. Get the `sdk` instance from the `useAuth` hook rather than creating a new one:

```typescript
import { useAuth } from './hooks/useAuth';
import { Assets } from '@uipath/uipath-typescript/assets';
// import other services as needed

// In a component or hook:
const { sdk } = useAuth();
export const assets = new Assets(sdk);
```

See the **SDK Module Imports** table in `SKILL.md` for all subpath imports. The `useAuth` hook implementation and the SDK methods it uses internally are documented in the `## src/hooks/useAuth.tsx` section of [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md).

---

## Calling SDK Services

After authentication, use the exported service instances:

```typescript
import { assets, entities } from './uipath';

// In a React component or effect:
const items = await assets.getAll({ folderId: 123 }); // replace 123 with your Orchestrator folder ID
const records = await entities.getAllRecords('<entity-id>'); // entity ID is a UUID — look it up via entities.getAll() or the Data Fabric portal (not the friendly name)
```

See [oauth-scopes.md](oauth-scopes.md) for the full list of methods and their required scopes.

If the user wants a **Document Understanding validation UI** (review/correct extraction results), embed the Validation Station widget — see [widgets/validation-station.md](widgets/validation-station.md). Required scope: `OR.Buckets` (plus `OR.Tasks` if the widget completes an Action Center task on save). Add to the `scope` field in `uipath.json` during scaffold (Step 1).

When implementing specific SDK services, read the corresponding reference:

| Service | Reference |
|---------|-----------|
| Assets, Queues, Buckets, Processes, Tasks | [sdk/orchestrator.md](sdk/orchestrator.md) |
| Data Fabric Entities / ChoiceSets | [sdk/data-fabric.md](sdk/data-fabric.md) |
| Maestro Processes / Cases | [sdk/maestro.md](sdk/maestro.md) |
| Action Center Tasks | [sdk/action-center.md](sdk/action-center.md) |
| Conversational Agent | [sdk/conversational-agent.md](sdk/conversational-agent.md) |
| Pagination patterns | [sdk/pagination.md](sdk/pagination.md) |
| UI patterns (polling, BPMN, HITL) | [patterns.md](patterns.md) |

---

## Router Base Path (optional)

If the app uses a client-side router (React Router, Vue Router), see the **Optional: Router base path** section of [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md) for `getAppBase()` patterns covering React Router v5/v6 and Vue Router.

---

## Run Locally

```bash
npm run dev
```

Open `http://localhost:5173`. The app redirects to UiPath login on first load. After login, it returns to the app.

If login fails, see [debug.md](debug.md).

---

## Deploy

When ready, follow [pack-publish-deploy.md](pack-publish-deploy.md) for the full deployment pipeline. `uip codedapp deploy` registers the production redirect URIs on the External Application automatically — no manual step is required.
