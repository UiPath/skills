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

- **If `base` is not `'./'`:** set `base: './'` in `vite.config.ts`, then rebuild and redeploy:

  ```bash
  npm run build
  uip codedapp deploy
  ```

- **If the router basename is hardcoded:** replace it with `getAppBase()` from `@uipath/uipath-typescript`, then rebuild and redeploy as above.

- **If `.uipath/app.config.json` has no valid `appUrl`:** the deploy did not finish. Re-run `uip codedapp deploy --output json` and confirm the output reports an `App URL`; resolve any error it prints before re-testing the URL.
