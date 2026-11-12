# Public Coded Web App (preview)

A public coded app is a Coded Web App that **anyone with the link can open without signing in** — customers, suppliers, event guests. It runs as a **confidential external application** of the tenant, through the Apps service: the browser never holds a token, only a session cookie, and the app can reach only the resources it declares.

> **Preview.** Public coded apps are enabled per organization and need preview builds of the SDK and CLI. If `uip codedapp publish --help` has no `--public` flag or `uip resources --help` fails, the user is on a released build: stop and tell them public apps need the preview builds from their UiPath contact. Do not hand-roll a workaround.

## When to use

- The user says "public", "no sign-in", "anonymous", "for customers / guests / suppliers", "anyone with the link".
- Otherwise build a normal (sign-in) Coded Web App — see [create-web-app.md](create-web-app.md).

## Hard rules

1. **Solutions only.** A public app must live in a solution: `uip solution init` → `uip codedapp init` inside it. Never use `uip codedapp publish/deploy` for it.
2. **No sign-in code.** `const sdk = new UiPath(); await sdk.initialize();` — public mode turns on from the platform-injected `uipath:app-key` tag. Never add login buttons, PKCE, or tokens.
3. **Only these calls work** (anything else throws `ValidationError` before a request is sent):

   | Service | Call | Visitor gets |
   |---|---|---|
   | `Processes` | `start(handle, { inputArguments })` | starts one job |
   | `Jobs` | `getOutput(jobKey)` | output of jobs this visitor started (or of a process open to all) |
   | `Entities` | `insertRecord(handle, data)` | inserts a record |
   | `Entities` | `getRecordByName(handle, recordId)` | records this visitor created (or any, if open to all) |
   | `Entities` | `getRecordsByName(handle, { pageSize, cursor })` | entities open to all only |
   | `Buckets` | `uploadFile(handle, fileName, content)` | uploads a file |

   Edit/delete, filtering, Action apps, tenant-level entities: **not supported**. Put that logic in a process (RPA, coded function, agent, Maestro, API workflow) and `start` it.
4. **Declare every resource with `uip resources add`** — never hand-write `bindings_v2.json`; it is derived at pack time from `uipath_resources.ts`. See [resource-declarations.md](resource-declarations.md). An undeclared resource is refused with 403.
5. **Data Fabric entities must be folder-scoped.**
6. **Never return secrets in a job's output** (session tokens, one-time codes). Orchestrator keeps job inputs/outputs and the visitor's browser receives its own job output. Send one-time codes by email from the process.
7. **Never handle the client secret in the conversation.** Ask the user to `export APP_CLIENT_SECRET=...` in their own shell; pass it as `"$APP_CLIENT_SECRET"`. `uip solution deploy config set ... clientSecret` echoes the value — always add `--output-filter Property`.

## Prerequisites (admin)

- A **confidential** external application with **application** scopes for what the app calls (see [oauth-scopes.md](oauth-scopes.md)). Always include `OR.Execution`. Data Fabric: `DataFabric.Data.Read DataFabric.Data.Write`; jobs: `OR.Jobs`; buckets: `OR.Buckets`.
  ```bash
  uip admin external-apps create "<App name>" --app-scope "OR.Execution DataFabric.Data.Read DataFabric.Data.Write" --output json
  ```
  The response contains the secret once — tell the user to store it; do not print or save it yourself.
- After the first deploy, the external app needs a role in the **deployment folder** for the resources it uses (for entities: Entity Records View + Create, e.g. *Automation User*). By design the platform does not grant it; ask the user/admin to assign it in Orchestrator → folder → Settings → Assign user/group → the external app.

## Build

```bash
uip solution init "Feedback"
cd Feedback
uip codedapp init ./feedback-app
# scaffold the React/Vite sources into feedback-app/source (create-web-app.md, Step 3), build output in source/dist
uip resources add EventFeedback --kind entity --project-path ./feedback-app/source   # writes source/uipath_resources.ts
```

Use the generated handles:

```ts
import { UiPath } from '@uipath/uipath-typescript/core';
import { Entities } from '@uipath/uipath-typescript/entities';
import { ProjectResources } from '../uipath_resources';   // src/main.ts -> source/uipath_resources.ts

const sdk = new UiPath();
await sdk.initialize();                       // no sign-in in public mode
const entities = new Entities(sdk);
await entities.insertRecord(ProjectResources.eventFeedback, { guestName, comment });
```

`uipath.json` goes into the build output (Vite: `source/public/uipath.json`, so it lands in `source/dist`). It must list the scopes explicitly — without `scope` the token request falls back to every scope of the external app and Identity rejects it (`invalid_scope`):

```json
{
  "scope": "OR.Execution DataFabric.Data.Read DataFabric.Data.Write",
  "access": [{ "resource": "entity", "key": "EventFeedback", "mode": "session" }]
}
```

`access.mode`: `session` = only the visitor who created a record/job can read it; `all` = every visitor. `key` is the binding key (`Name.FolderPath` for processes/buckets, the entity name for entities — run `uip resources list` to see them).

Then:

```bash
(cd feedback-app/source && npm run build)      # pack does not build
uip solution resources refresh
uip solution pack . ./output --version 1.0.0
uip solution publish ./output/Feedback_1.0.0.zip
```

Wait for `publish` to finish before deploying or upgrading.

## Deploy — Orchestrator UI (preferred for first-time users)

Orchestrator → **Deployments** → **Manage** → **Deploy** → pick the package and version → location **Shared** (a folder on the tenant feed) → configure the app resource: routing name, **external application** (the confidential one), auth mode **Application**, **client secret** → Deploy. The app opens at `https://<org>.uipath.host/<routingName>`.

## Deploy — CLI

```bash
uip solution deploy config get "Feedback" -d config.json
uip solution deploy config set config.json feedback-app routingName feedback --output-filter Property
uip solution deploy config set config.json feedback-app externalClientId "<external app id>" --output-filter Property
uip solution deploy config set config.json feedback-app runtimeAuthMode application --output-filter Property
uip solution deploy config set config.json feedback-app clientSecret "$APP_CLIENT_SECRET" --output-filter Property
uip solution deploy run -n "Feedback" --package-name "Feedback" --package-version 1.0.0 \
  --folder-name "Feedback" --parent-folder-path "Shared" --config-file config.json
```

Keep `config.json` out of source control (it holds the secret). `runtimeAuthMode application` is what makes the app public; the same package deploys private with `user`.

## Upgrade and secret rotation

```bash
uip solution pack . ./output --version 1.0.1 && uip solution publish ./output/Feedback_1.0.1.zip
uip solution deploy upgrade <deployment key> --version 1.0.1     # add --discard-draft if a stale draft blocks it
```

The upgrade keeps the stored secret **and its scope** (a changed `scope` in `uipath.json` is not applied to a running deployment). To rotate the secret: Orchestrator → the deployment folder → **Apps** → ⋮ → **Edit** → Client secret (validated against Identity on save).

## Troubleshooting

| Symptom | Cause |
|---|---|
| `ValidationError`, no request sent | Call not supported in public mode (rule 3) |
| 403 on every call | Resource not declared, or deployed outside a tenant-feed folder |
| 403 `Missing permissions: EntityRecords.Create` | External app has no role in the deployment folder |
| 403 `isn't open to all` on a list | Entity `access.mode` is `session` |
| 404 reading a record/job | Another visitor created it, or the session expired |
| `Identity rejected the app's client credentials` | Wrong secret, missing scope on the external app, or `uipath.json` missing from `source/dist` |
| Upgrade 404 | Version not published yet |
| Deploy screen does not list the external app | It is not confidential, or the Solutions build predates the picker fix — deploy with the CLI |
