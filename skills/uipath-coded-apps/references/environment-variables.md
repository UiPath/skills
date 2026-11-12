# Environment Variables for Coded Apps

Per-deployment configuration for a coded app: values such as a region, a brand colour, a support email or a feature toggle that differ between the deployments of one app, set by whoever deploys it, read by the app before sign-in. The platform writes them into a small `env.js` next to the app's `index.html`, so **anyone who can open the app URL can read them**. They are for public configuration only.

> **Availability.** Two gates, check both before relying on this:
> 1. **The CLI.** `uip codedapp deploy -h` must list `--env-vars-file`; `uip` 1.205.0 and earlier do not have it, nor the `.env.example` sync on push. If it is absent, run `uip update` (or `npm install -g @uipath/cli@latest`) and check again.
> 2. **The tenant.** The platform enables the feature per tenant. Where it is off, the Environment variables field is absent from the deploy forms and a deploy that carries variables is refused with `Environment variables are not enabled for this tenant`. Do not retry; tell the user the tenant does not have the feature yet and fall back to a build-time constant or an Orchestrator asset (see the table below).

## When to use which

| Need | Use | Why |
|------|-----|-----|
| A value that differs per deployment and is fine for anyone to see (region, brand colour, API base URL, a customer's feature toggle) | **Environment variable** (`UIPATH_CLIENT_*`) | Set at deploy, changed without a redeploy, readable before sign-in |
| A value that is the same everywhere | A constant in the code | No configuration needed |
| A value a signed-in user may see, but not the public | **Text asset** read with `Assets.getByName` | Needs an authenticated call, so it is not public |
| A value the browser must never hold (API key, password, token) | **Secret asset** read inside a coded function (`uip function`, `Functions.invoke()` from the app) | The function runs server-side and returns only the result |

Never put a secret in an environment variable. The value is served in a public file.

## Names and format

The text is dotenv syntax, one `NAME=value` per line, and the platform validates it on deploy, on edit and in the solution deploy wizard:

- Every name starts with `UIPATH_CLIENT_` and appears once. Other names are refused on deploy; the CLI and the dev plugin skip them silently when they read a `.env` file, so the developer's private names never reach the app. `UIPATH_CLIENT_ID` and `UIPATH_CLIENT_SECRET` are the platform's OAuth credential names and are refused everywhere, even though they carry the prefix.
- Blank lines and `#` comments are allowed. **A blank value (`UIPATH_CLIENT_REGION=`) leaves the variable unset**, so `env.UIPATH_CLIENT_REGION ?? 'EU'` falls back; it does not read as an empty string.
- A value fits on one line. Quote a value that contains `#` (`UIPATH_CLIENT_ACCENT='#0f2f27'`): unquoted, dotenv reads `#` as a comment and the value is refused rather than published cut.
- No `%ASSETS/...%` references: for an agent that syntax resolves a secret server-side; in a public file it would expose it, so it is refused.
- The whole text is at most 4000 characters.

## Reading them in the app

```typescript
import { env } from '@uipath/uipath-typescript';

const region = env.UIPATH_CLIENT_REGION ?? 'EU';            // property access
const accent = env.get('UIPATH_CLIENT_ACCENT') ?? '#0f2f27'; // same read as a method
```

`env` is synchronous and needs no `UiPath` instance, so it works before sign-in, in a router basename, in the first render. A name the deployment did not set reads as `undefined`; always give a fallback. To type the names the app uses, augment `UiPathEnvironment`:

```typescript
declare module '@uipath/uipath-typescript' {
  interface UiPathEnvironment {
    UIPATH_CLIENT_REGION?: string;
    UIPATH_CLIENT_ACCENT?: string;
  }
}
```

The `env` export exists from `@uipath/uipath-typescript` 1.8.2. Read `node_modules/@uipath/uipath-typescript/dist/index.d.ts` for the exact surface (Critical Rule 19).

## Local development

`@uipath/coded-apps-dev` injects the `UIPATH_CLIENT_*` values from `.env.local`, `.env.development` and `.env.development.local` (later files win, as in Vite) into the dev server's page, so `env` reads the same way locally and deployed. Plain `.env` is not read for app variables; it holds `UIPATH_PROJECT_ID` and other CLI settings. `create-vite`'s `.gitignore` already ignores `*.local`, so `.env.local` stays on the machine.

> The plugin reads these files from the release after `@uipath/coded-apps-dev` 1.0.0-beta.1. On an older plugin `env` is empty locally and every read falls back; check `grep -l UIPATH_CLIENT_ node_modules/@uipath/coded-apps-dev/dist/*.js` and update the plugin if it prints nothing.

## `.env.example`: list the names once

Commit a `.env.example` that lists every `UIPATH_CLIENT_*` variable the app reads, with a comment and the default a deployment should start from (or blank for "the deployer fills this in"):

```bash
# Region the app serves: EU or US
UIPATH_CLIENT_REGION=EU
# Shown in the footer; set per customer
UIPATH_CLIENT_SUPPORT_EMAIL=
```

`uip codedapp init` scaffolds a commented starter. Values in this file are the defaults every deployment starts from, so keep real defaults there, never placeholders or secrets. For an in-solution app, `uip codedapp push` reads the file (or `.env.template`) and adds its names and values to the app resource's environment variables in the solution, so the deploy wizard shows what can be configured instead of an empty field. Push only adds names the solution does not list yet: a value edited in Studio Web is never changed, and a name removed from the file stays until someone removes it there.

## Standalone app: set at deploy, change without a redeploy

The **Deploy app** form in Orchestrator has an Environment variables field; **Edit app details** shows the current text and saves changes to the running version. From the CLI:

```bash
# Publish the UIPATH_CLIENT_* variables in a .env file; other names in it are skipped
uip codedapp deploy -n <APP_NAME> --folder-key <FOLDER_KEY> --env-vars-file .env.production

# Add or override single values on top of the file; repeatable
uip codedapp deploy -n <APP_NAME> --folder-key <FOLDER_KEY> --env UIPATH_CLIENT_REGION=EU --env UIPATH_CLIENT_SUPPORT_EMAIL=<SUPPORT_EMAIL>
```

- Omit both flags to keep the deployed values. An empty file clears them on purpose; a file whose names are all private is refused, so a typo cannot wipe the values.
- A change to the values rewrites only `env.js`: no rebuild, no new version. The edge keeps `env.js` for about 60 seconds, so a reload inside that window can still show the old values.
- A version deployed before the app had any variables does not load `env.js`. Adding variables to it saves them with a warning (`This version was deployed without environment variables...`); deploy a new version to apply them.

## In-solution app: defaults in the package, values per deployment

The app resource carries the defaults (the Environment variables field on the app resource in Studio Web, or what `uip codedapp push` added from `.env.example`). Each customer's deployment overrides them in the Solutions deploy wizard, or from the CLI:

```bash
uip solution deploy config get "<PACKAGE_NAME>" -d config.json --output json
uip solution deploy config set config.json <APP_RESOURCE_NAME> environmentVariables "UIPATH_CLIENT_REGION=US"
uip solution deploy run -n "<DEPLOYMENT_NAME>" \
  --package-name "<PACKAGE_NAME>" --package-version "<VERSION>" \
  --folder-name "<FOLDER_NAME>" --config-file config.json --output json
```

Two rules the server applies:

- **A deployment's text replaces the package defaults as a whole.** A default the deployment's text leaves out is unset for that deployment, so write the full set, not just the changed line.
- **An upgrade keeps the deployment's existing text.** A name added in a later version does not appear for a deployment already on an earlier version; the app uses its code fallback there until someone adds the line to that deployment's configuration.

Do not set a solution-installed app's variables through the standalone **Edit app details** form; it refuses them, because the next configuration change from Solutions would overwrite them.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `env.UIPATH_CLIENT_X` is `undefined` after a deploy | Name lacks the prefix, is misspelled, or was left blank | Check the deployed text; a blank value is unset by design |
| Value is cut, or a colour is empty | Unquoted `#` in the value | Quote it: `UIPATH_CLIENT_ACCENT='#0f2f27'` |
| New values do not show after an edit | Edge cache, up to about 60 seconds | Reload after a minute; `env.js` is served with `no-cache`, so the browser itself does not keep it |
| Edit saved but the app never loads the values | Version deployed before it had variables, so `index.html` does not link `env.js` | Deploy a new version |
| Deploy refused: `not enabled for this tenant` | Feature is off for the tenant | Remove the variables; use a constant or an asset until the tenant has the feature |
| Deploy refused: `must start with UIPATH_CLIENT_` | A private name in `--env`, or in the solution's text | Rename it, or move it to `.env.local` if it is only for local dev |
