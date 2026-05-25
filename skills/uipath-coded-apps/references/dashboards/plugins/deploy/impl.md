# Dashboard Deploy Plugin

## Pre-flight
1. Verify project has a `package.json` with a `build` script
2. Run: `npm run build`
   - If it fails → fix build errors before proceeding (see `../../debug.md` for common issues)
3. Bump `version` in `package.json` — re-publish without a version bump will fail

## Deploy Pipeline
Dashboard projects are standard Coded Web Apps. Follow the full pipeline:

→ Read [../../pack-publish-deploy.md](../../pack-publish-deploy.md) for all steps.

## Dashboard-specific Rules
- App type is always **Web** — never pass `-t Action` to `uip codedapp publish`
- The app name should match the dashboard title from the build plan
- After deploy, verify the live URL loads without auth errors before reporting success
- If the user has not yet created an OAuth external app, follow `../../oauth-client-setup.md`
