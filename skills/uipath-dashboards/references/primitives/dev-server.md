# dev-server

## Purpose
Boot Vite dev server and open the dashboard on localhost so the user can preview immediately after Build. Prompt the user for a PAT if `.env.local` isn't configured.

## Inputs
- Target project directory.
- Current state.json (for env / orgName / tenantName → `.env.local`).

## Outputs
Running Vite dev server in foreground; localhost URL surfaced to user.

## Rules
1. **Always foreground.** User must see HMR logs; Ctrl+C stops. Don't background-detach.
2. **Default port 5173.** Vite auto-bumps (5174, 5175, ...) if busy. Report the chosen port.
3. **Prompt for PAT on first preview.** If `.env.local` missing or lacks `VITE_UIPATH_PAT`, pause, explain how to generate one, wait for paste.
4. **No redirect URI management.** Secret-mode auth means no portal-bounce at preview time.
5. **`.env.local` is gitignored.** Never stage it.

## Pipeline

### 1. Check `.env.local`
If file missing or `VITE_UIPATH_PAT=` is empty:
```
Paste your UiPath PAT into .env.local as VITE_UIPATH_PAT=... then press Enter.

Generate one at: https://<env>.uipath.com/<orgName>/<tenantName>/portal_/accessTokens
Scope: at minimum OR.Folders.Read + OR.Jobs.Read (or whatever the dashboard needs).
```
Wait for user confirmation.

### 2. Verify `.env.local`
Read and verify `VITE_UIPATH_PAT=<non-empty>`. If still empty after user says "done", surface the issue + re-prompt.

### 3. Run dev server
```bash
cd <project>
npm run dev
```

### 4. Capture port
Vite's startup output includes `Local: http://localhost:<port>/`. Parse + report.

### 5. Surface URL
```
Dashboard preview: http://localhost:<port>/ — Ctrl+C to stop.
```
Block until user interrupts.

## `.env.local` template (what scaffold wrote)
```
VITE_UIPATH_BASE_URL=https://<env>.api.uipath.com
VITE_UIPATH_ORG_NAME=<orgName>
VITE_UIPATH_TENANT_NAME=<tenantName>
VITE_UIPATH_PAT=   # PASTE YOUR PAT HERE; do not commit
```

## Error paths
| Condition | Action |
|---|---|
| Port 5173 busy | Vite auto-bumps; report the chosen port. |
| `npm run dev` fails | Surface stderr. Common: missing deps → re-run `npm install`. |
| PAT empty at runtime | Auth-strategy throws clear error in the browser console; surface to user: "set VITE_UIPATH_PAT and restart dev server". |
| User pastes an invalid PAT | Authentication fails at SDK call time (not server start); user sees 401s in DevTools network tab. |
