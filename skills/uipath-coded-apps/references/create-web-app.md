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

**Redirect URI:** `http://localhost:5173` (computed automatically at runtime — works in both local dev and production)

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
   - If no, say **"create one"** and I'll set it up via browser automation

---

**Wait for the user's reply before proceeding.**

### Step 2.5 — Ensure Playwright CLI is available (only if user said "create one")

Before running browser automation, check if Playwright is installed:

```bash
npx playwright --version 2>/dev/null
```

If the command fails or returns no output, follow [oauth-client-setup.md Step 2 (Setup B)](oauth-client-setup.md#step-2-ensure-playwright-is-available) to install Playwright into `~/.uipath-skills/playwright/`. Do **not** install into the user's app.

Once confirmed available, read [oauth-client-setup.md](oauth-client-setup.md) and follow it exactly to create the External Application with the scopes from Step 1 and redirect URI `http://localhost:5173`. That reference has all the browser automation details.

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

Run these as **two separate commands** in order. The `--@uipath:registry` flag binds only to the first command (the SDK install) — do not apply it to the second, and do not run a bare `npm install` with the flag.

```bash
# 1. UiPath SDK (registry flag forces public npm to bypass GitHub Packages auth)
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org

# 2. Remaining runtime + Tailwind dependencies
npm install path-browserify tailwindcss@3 postcss autoprefixer
```

> **Why the registry flag?** Users may have `@uipath` scoped to GitHub Packages in their `.npmrc`, which requires authentication and causes a 401. The flag forces `@uipath/uipath-typescript` to install from the public npm registry.

### 4.4 — Remove Vite defaults that will be overwritten

`npx create-vite` ships default versions of three files we replace in Step 4.5. Delete them first so the Write tool can create them fresh — otherwise each Write requires a Read-first round-trip and produces a benign-but-noisy "Error writing file" message.

```bash
rm vite.config.ts src/App.tsx src/index.css
```

### 4.5 — Write project files from templates

All file content lives in [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md). For each row below, copy the named section from that file verbatim into the path shown, applying the listed substitutions. Create `src/hooks/` first; the rest of the directories already exist from `create-vite`.

| Path | Template section | Substitutions |
|------|------------------|---------------|
| `vite.config.ts` | `## vite.config.ts` | none |
| `uipath.json` | `## uipath.json` | `{{SCOPES}}`, `{{CLIENT_ID}}` |
| `.env` | `## .env` | `{{CLIENT_ID}}`, `{{SCOPES}}`, `{{ORG_NAME}}`, `{{TENANT_NAME}}`, `{{BASE_URL}}` |
| `.env.example` | `## .env.example` | none |
| `src/hooks/useAuth.tsx` | `## src/hooks/useAuth.tsx` | none |
| `src/App.tsx` | `## src/App.tsx` | none |
| `tailwind.config.js` | `## tailwind.config.js` | none |
| `postcss.config.js` | `## postcss.config.js` | none |
| `src/index.css` | `## src/index.css` | none |

### 4.6 — Append `.env` to `.gitignore`

```bash
echo ".env" >> .gitignore
```

### 4.7 — Verify the scaffold

First, confirm all files exist: `vite.config.ts`, `uipath.json`, `.env`, `.env.example`, `tailwind.config.js`, `postcss.config.js`, `src/hooks/useAuth.tsx`, `src/App.tsx`, `src/index.css`. If any are missing, re-run the corresponding row from Step 4.5.

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
