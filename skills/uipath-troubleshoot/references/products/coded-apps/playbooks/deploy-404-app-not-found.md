---
confidence: high
---

# 404 After Deploy / App Not Found

## Context

What this looks like:
- The deployed app URL (`https://cloud.uipath.com/<org>/apps_/<system-name>`) returns `404` or a blank white page
- The HTML document loads but its JS/CSS assets `404` in the network tab — asset requests point at a wrong, doubled, or absolute path
- The app works locally (`npm run dev`) but is broken only after `uip codedapp deploy`

What can cause it:
- `vite.config.ts` `base` is set to an absolute path or a routing name (e.g. `'/my-app/'`) instead of `'./'`. The platform's Cloudflare Worker owns URL routing, so assets must be referenced **relative** to the served location.
- The client-side router (React Router / Vue Router) `basename` is **hardcoded** instead of read from `getAppBase()`, so routes resolve against the wrong prefix once deployed.
- `deploy` did not complete — `.uipath/app.config.json` has no valid `appUrl` / `systemName`.

What to look for:
- The `base` value in `vite.config.ts`
- Whether the router basename comes from `getAppBase()` (from `@uipath/uipath-typescript`) or a literal string
- Whether `.uipath/app.config.json` contains a valid `appUrl`

## Investigation

1. Check the Vite base path:

   ```bash
   grep -n "base" vite.config.ts
   ```

   It must be `base: './'` (relative). An absolute path or route name breaks asset resolution behind the platform router.

2. Check the client-side router basename (if the app uses one):

   ```bash
   grep -rnE "basename|getAppBase" src/
   ```

   The basename must come from `getAppBase()` — not a hardcoded string. `getAppBase()` reads the `uipath:app-base` meta tag injected at runtime and falls back to `'/'` locally.

3. Confirm the deploy produced a valid app URL:

   ```bash
   cat .uipath/app.config.json
   ```

## Resolution

- **If `base` is not `'./'`:** set `base: './'` in `vite.config.ts`, then build and package an explicit new candidate:

  ```bash
  npm run build
  ```

- Before publishing or deploying that candidate, reconcile the authoritative deployment, system name, route, current version, target folder, OAuth client, and package versions. Execute a fresh guarded `create` or `upgrade` operation with the exact candidate; do not resume or repeat the failed write.

- **If the router basename is hardcoded:** replace it with `getAppBase()` from `@uipath/uipath-typescript`, then build/package a new candidate and follow the same reconciliation boundary.

- **If `.uipath/app.config.json` has no valid `appUrl`:** do not conclude that deploy failed or rerun it. Re-read remote Apps inventory. If the exact candidate is active, use and verify the authoritative hosted URL. If it is published but not deployed, prepare a fresh guarded operation bound to the reconciled deployment and versions. If remote state cannot be proven, stop and escalate.
