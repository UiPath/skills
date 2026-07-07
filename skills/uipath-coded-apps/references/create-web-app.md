# Create a UiPath Coded Web App

Scaffold a new UiPath Coded Web Application using Vite + React + TypeScript with the `@uipath/uipath-typescript` SDK.

Order matters: the project is scaffolded and the SDK **installed before scopes are determined**, so the scope decision reads the per-method scope table shipped inside the installed package (version-exact) instead of relying on memorized tables.

## Pre-flight: Collect Required Information

**CRITICAL: You do NOT know these values. You CANNOT infer or assume them. Ask the user and wait for their reply before writing any files.**

### Step 1 — Ask the user for setup info

Output the following text directly. **Do NOT call any tools yet — just output this text and wait for the user's reply.**

---

Here's how OAuth will be set up:

**Redirect URI:** `http://localhost:5173` (the local dev URL — stored as `redirectUri` in `uipath.json` and injected as the `uipath:redirect-uri` meta tag; the platform injects the production URI automatically at deploy)

**OAuth scopes:** determined after the project is scaffolded — I'll read the exact per-method requirements from the installed SDK and configure them on the OAuth client in Step 4.

Please answer these questions to continue:

**1. App name** — lowercase kebab-case project folder name (e.g. `my-dashboard`)

**2. Environment** — which UiPath environment?
   - `cloud` — Production *(most common)*
   - `staging` — Staging
   - `alpha` — Alpha

**3. Org name** — your UiPath organization slug (from `cloud.uipath.com/<orgName>`)

**4. Tenant name** — your UiPath tenant (often `DefaultTenant`)

**5. Client ID** — do you have an existing OAuth External Application client ID you want to reuse?
   - If yes, paste it — I'll tell you the exact scopes it needs (and can add missing ones via browser automation) once they're determined in Step 4
   - If no, say **"create one"** and I'll set it up via browser automation with the right scopes

**6. Default UI styling** — apply UiPath's Apollo Vertex design system (`@uipath/apollo-wind` components, semantic tokens, and a light/dark theme toggle out of the box)?
   - `yes` *(recommended)* — apollo-wind + `next-themes` on top of Tailwind: Apollo Vertex design system, light/dark theme toggle out of the box
   - `no` — Tailwind only; bring your own component library

---

**Wait for the user's reply before proceeding.**

### Step 2 — Resolve org name (if not provided)

If the user typed their org name, use it. If they said "find from browser", navigate to the UiPath cloud host for their environment and extract the org name from the URL path (first segment after the domain).

---

## Step 3 — Scaffold the Project

Once you have the answers (app name, environment, org, tenant, styling), execute the steps below in order. All steps after Step 3.2 run from inside the new project directory.

> **Set `timeout: 300000`** (5 minutes) on every Bash call that runs `npm install` or `npm create vite` — these can take several minutes and the default 2-minute timeout is not enough.

### 3.1 — Resolve the base URL

Map the `<environment>` answer from Step 1 to a base URL using the table in [SKILL.md](../SKILL.md) (Production → `https://api.uipath.com`, Staging → `https://staging.api.uipath.com`, Alpha → `https://alpha.api.uipath.com`). If the user gave a custom URL, use that verbatim. Store as `<base-url>`.

### 3.2 — Create the Vite project

```bash
npx --yes create-vite@latest <app-name> --template react-ts
```

Then `cd` into `<app-name>`. Every subsequent step runs from this directory.

### 3.3 — Install dependencies

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

### 3.4 — Remove Vite defaults that will be overwritten

`npx create-vite` ships default versions of files we replace in Step 5. Delete them first so the Write tool can create them fresh — otherwise each Write requires a Read-first round-trip and produces a benign-but-noisy "Error writing file" message.

- **`default styling = yes`** — also overwrites `src/main.tsx` to wrap `<App>` in the theme provider:

  ```bash
  rm vite.config.ts src/App.tsx src/index.css src/main.tsx
  ```

- **`default styling = no`**:

  ```bash
  rm vite.config.ts src/App.tsx src/index.css
  ```

---

## Step 4 — Determine Scopes & Configure the OAuth Client

The SDK is now installed, so the version-exact scope reference is on disk.

### 4.1 — Determine required scopes

1. From the user's **request**, identify which UiPath services the app will use (e.g., Entities, Tasks, Processes, Maestro, Conversational Agent, Buckets, etc.).
2. Start from the **Common Scope Bundles** table in [oauth-scopes.md](oauth-scopes.md) — bundles grant the service family, not just today's methods, so the app has headroom as it evolves.
3. For services or methods outside the bundles — and to verify write/action methods — read the per-method table shipped in the package: `node_modules/@uipath/uipath-typescript/docs/oauth-scopes.md`. If the installed SDK predates that file, use the fallback in [oauth-scopes.md](oauth-scopes.md).
4. If the app embeds a `@uipath/ui-widgets-*` component, add the widget scopes from [oauth-scopes.md](oauth-scopes.md) § Widgets.
5. Compose the full deduplicated space-separated scopes string. Store as `<scopes>` — Step 5 writes it into `uipath.json`.

### 4.2 — Create or verify the External Application

**If the user said "create one":** check Playwright availability first:

```bash
npx playwright --version 2>/dev/null
```

If the command fails or returns no output, follow [oauth-client-setup.md Step 2 (Setup B)](oauth-client-setup.md#step-2-ensure-playwright-is-available) to install Playwright into `~/.uipath-skills/playwright/`. Do **not** install into the user's app. Once confirmed available, read [oauth-client-setup.md](oauth-client-setup.md) and follow it exactly to create the External Application with `<scopes>` and redirect URI `http://localhost:5173`.

**If the user pasted an existing Client ID:** show them `<scopes>` and ask whether the External Application already has all of them. If scopes are missing, offer to add them via the `add-scopes` operation in [oauth-client-setup.md](oauth-client-setup.md), or let the user update the app manually. A missing scope at the External Application means the token request is rejected entirely; a scope granted to the app but missing from `uipath.json` causes silent `401`/`403` on first call.

---

## Step 5 — Write Project Files

### 5.1 — Write project files from templates

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

### 5.2 — `.gitignore`

Neither path writes a `.env`, and `uipath.json` is committed (it holds the SDK config — a public OAuth client ID plus org/tenant/base-URL/redirect-URI, no secrets), so no `.gitignore` change is needed for OAuth config. The project `.uipath/` directory created by `codedapp` commands must stay gitignored — it is covered by `npx create-vite`'s default plus `uip codedapp`'s conventions. Verify with `cat .gitignore | grep -i uipath` and add `.uipath/` if missing.

### 5.3 — Verify the scaffold

First, confirm all expected files for your Q6 branch exist. If any are missing, re-run the corresponding row from Step 5.1.

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

Subpaths and classes are discovered from the installed package — see the lookup protocol in [sdk/imports.md](sdk/imports.md). The `useAuth` hook implementation and the SDK methods it uses internally are documented in the `## src/hooks/useAuth.tsx` section of [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md).

---

## Calling SDK Services

After authentication, use the exported service instances:

```typescript
import { assets, entities } from './uipath';

// In a React component or effect:
const items = await assets.getAll({ folderId: 123 }); // replace 123 with your Orchestrator folder ID
const records = await entities.getAllRecords('<entity-id>'); // entity ID is a UUID — look it up via entities.getAll() or the Data Fabric portal (not the friendly name)
```

Method signatures come from the installed types (`node_modules/@uipath/uipath-typescript/dist/<subpath>/index.d.ts`); per-method scopes from the shipped `node_modules/@uipath/uipath-typescript/docs/oauth-scopes.md` — see [oauth-scopes.md](oauth-scopes.md) for bundles and the lookup protocol.

If the user wants a **Document Understanding validation UI** (review/correct extraction results), embed the Validation Station widget — see [widgets/validation-station.md](widgets/validation-station.md). Required scope: `OR.Buckets` (plus `OR.Tasks` if the widget completes an Action Center task on save). Add to the `scope` field in `uipath.json` during Step 4.

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
