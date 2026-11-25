# Public Coded Web App (preview)

A public coded app is a Coded Web App that **anyone with the link can use without signing in to UiPath** — customers, suppliers, event guests. It calls UiPath as a **confidential external application** of the organization, and only for the resources it declares.


> **Preview.** Public coded apps need:
> - SDK: `@uipath/uipath-typescript` `1.8.5` or later
> - CLI: `npm install -g @uipath/cli` (`1.206.0` or later)
> - Local runs: `@uipath/coded-apps-dev` `1.0.0` or later
>
> Today you write `bindings_v2.json` by hand. Generating it from the app code is coming soon.

## Decide: public or sign-in

Build a public app only when the people using it have no UiPath account. Otherwise build a normal sign-in Coded Web App — see [create-web-app.md](create-web-app.md).

Before building, confirm with the user that the app fits these limits:

- **Anyone with the link can use it.** No sensitive data (Social Security numbers, billing details) in or out.
- **The app doesn't know who the visitor is.** No per-user features, no calls that need the current user.
- **Visitors can add, never change.** They can start jobs, add and read records, and upload files. Anything else (send an email, update another system, edit or delete data) goes in a process the app starts.
- **Solution only.** The app is deployed with a solution. A coded app deployed on its own cannot be public. Coded action apps cannot be public.
- **Folder-scoped entities only.** Tenant-level Data Fabric entities are not supported.
- **IP restrictions.** If the organization restricts access by IP address, visitors outside the allowed ranges cannot use the app. The Trusted public apps list does not cover public coded apps yet.

## Design

### Access modes

For each resource the app reads, the developer sets one of two access modes in `uipath.json` `access`:

- `session` — a visitor can read only the data they added in their own session. Listing the resource is not allowed.
- `all` — the data in the declared resource is shared with every visitor. This is the default.

A visitor is identified by their browser session. Another browser, a private window, or cleared cookies start a new session, and a new session cannot read what an earlier session added. So show a visitor their results in the same visit (a confirmation screen after submit), not "come back later".

List every resource the app reads, and use `session` for anything personal.

### Data and security

- **Data Fabric Everyone group.** A role assigned to the Everyone group also applies to the app's external application. Ask the user to remove the Everyone group from entities the app must not read, and to use field-level access for fields it must not see.
- **No secrets in job output.** The visitor's browser receives the output of the jobs it starts. Keep secrets (one-time codes, tokens) inside the process — for example a coded function or an API workflow — and return only what the visitor may see.
- **No keys in the app.** Everything in the build output is public.
- **Validate input in the process.** Treat anything a visitor sends as untrusted.
- **One folder per public app**, so the external application's role covers only that app's resources.

## Hard rules

1. **Solutions only.** A public app must live in a solution: `uip solution init` → `uip codedapp init` inside it. Never use `uip codedapp publish/deploy` for it.
2. **No sign-in code.** `const sdk = new UiPath(); await sdk.initialize();` — the app runs without sign-in once it is deployed as public. Never add login buttons, PKCE, or tokens.
3. **Only these calls work** (anything else throws `ValidationError` before a request is sent):

   | Service | Call | Visitor gets |
   |---|---|---|
   | `Processes` | `start({ name }, { folderPath, inputArguments })` | starts one job |
   | `Jobs` | `getOutput(jobKey)` | output of jobs they started (any job of the process in `all` mode) |
   | `Entities` | `insertRecord({ name }, data)` | adds a record |
   | `Entities` | `getRecordByName(name, recordId)` | records they added (any record in `all` mode) |
   | `Entities` | `getRecordsByName(name, { pageSize, cursor })` | `all` mode only |
   | `Buckets` | `uploadFile({ name }, fileName, content, { folderPath })` | uploads a file under a new name, so it never overwrites one |

   Edit, delete, filtering, action apps and tenant-level entities are **not supported**. Put that logic in a process (RPA, coded function, agent, Maestro, API workflow) and `start` it.
4. **List every resource the app uses in `bindings_v2.json`** at the app project root (see [Declare the resources](#declare-the-resources)). A resource that isn't listed is refused with 403.
5. **Never handle the client secret in the conversation.** The user puts it in their own shell (`export APP_CLIENT_SECRET=...`) or their own `.env.local`; pass it as `"$APP_CLIENT_SECRET"`. `uip solution deploy config set ... clientSecret` echoes the value — always add `--output-filter Property`.

## Prerequisites (admin)

- A **confidential** external application with **application** scopes for what the app calls (see [oauth-scopes.md](oauth-scopes.md)). Always include `OR.Execution`. Data Fabric: `DataFabric.Data.Read DataFabric.Data.Write`; jobs: `OR.Jobs`; buckets: `OR.Buckets`.
  ```bash
  uip admin external-apps create "<App name>" --app-scope "OR.Execution DataFabric.Data.Read DataFabric.Data.Write" --output json
  ```
  The response contains the secret once — tell the user to store it; do not print or save it yourself.
- After the first deploy, the external application needs a role in the **deployment folder** for the resources it uses. The deployment does not grant it. Ask the user or an admin to assign it: Orchestrator → **Tenant** → **Folders** → the deployment folder → **Assign accounts/group/external app** → the external application → a role such as **Automation User** (for entities: Entity Records **View** and **Create**).

## Build

```bash
uip solution init "Feedback"
cd Feedback
uip codedapp init ./feedback-app
# scaffold the React/Vite sources into feedback-app/source (create-web-app.md, Step 3), build output in source/dist
```

### Declare the resources

Write `feedback-app/bindings_v2.json` (the project root, next to `source/`), one entry per resource:

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "entity",
      "key": "EventFeedback",
      "value": {
        "name": { "defaultValue": "EventFeedback", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": ".", "isExpression": false, "displayName": "Folder Path" }
      },
      "metadata": { "BindingsVersion": "2.2" }
    },
    {
      "resource": "process",
      "key": "Summarize.Shared",
      "value": {
        "name": { "defaultValue": "Summarize", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": "Shared", "isExpression": false, "displayName": "Folder Path" }
      },
      "metadata": { "BindingsVersion": "2.2" }
    }
  ]
}
```

- `resource` is `process`, `entity` or `bucket`.
- `key` is `Name.FolderPath` for processes and buckets, and the name alone for entities (folder path `"."`).
- Then run `uip solution resources refresh` from the solution root to add them to the solution. It reads the file only at the project root.

### Call the resources

Pass the same name and folder as in `bindings_v2.json`. The SDK sends `Name.FolderPath`, and anything that doesn't match an entry is refused.

```ts
import { UiPath } from '@uipath/uipath-typescript/core';
import { Entities } from '@uipath/uipath-typescript/entities';
import { Processes } from '@uipath/uipath-typescript/processes';

const sdk = new UiPath();
await sdk.initialize();                       // no sign-in in public mode
await new Entities(sdk).insertRecord({ name: 'EventFeedback' }, { guestName, comment });
await new Processes(sdk).start({ name: 'Summarize' }, { folderPath: 'Shared', inputArguments: JSON.stringify({ text }) });
```

`uipath.json` goes into the build output (Vite: `source/public/uipath.json`, so it lands in `source/dist`). It must list the scopes the app needs, and the access mode of each resource it reads:

```json
{
  "scope": "OR.Execution DataFabric.Data.Read DataFabric.Data.Write",
  "access": [{ "resource": "entity", "key": "EventFeedback", "mode": "session" }]
}
```

`key` is the same key as in `bindings_v2.json`.

Then:

```bash
(cd feedback-app/source && npm run build)      # checks it compiles; pack also builds it
uip solution resources refresh
uip solution pack . ./output --version 1.0.0
uip solution publish ./output/Feedback_1.0.0.zip
```

Wait for `publish` to finish before deploying or upgrading.

## Run locally

`@uipath/coded-apps-dev` runs the app as a public app on the developer's machine, with the same access rules as after deploy. It works with the Vite and webpack dev servers.

1. Point the plugin at the app's `uipath.json` and add the local-run fields to it (they are not secrets):
   ```ts
   // vite.config.ts
   plugins: [react(), uipathCodedApps({ configPath: 'public/uipath.json' })]
   ```
   ```json
   { "orgName": "<org>", "tenantName": "<tenant>", "baseUrl": "https://cloud.uipath.com", "scope": "...", "access": [...] }
   ```
2. Ask the user to create `source/.env.local` themselves (never write the secret yourself), and check `.env.local` is gitignored:
   ```bash
   UIPATH_PUBLIC_APP=true
   UIPATH_PUBLIC_APP_CLIENT_ID=<external app id>
   UIPATH_PUBLIC_APP_CLIENT_SECRET=<client secret>
   UIPATH_PUBLIC_APP_FOLDER_KEY=<folder key>   # optional: the folder for resources declared without a folder
   ```
3. `npm run dev`, then open the app on `localhost`. To act as a second visitor, open it in a private window.

Locally, resources use the name and folder in `bindings_v2.json` (solution overrides apply only after deploy), and sessions reset when the dev server restarts. The external application needs a role in the folders that hold the resources. Set `UIPATH_PUBLIC_APP=false` to go back to signing in as the developer.

## Deploy — Studio Web (preferred)

In Studio Web, open the solution → arrow on **Publish** → **Deploy** → pick version, deployment name, location and solution folder → arrow on **Deploy** → **Customize** → in the coded app's settings set `routingName`, `externalClientId` (the confidential external application), `runtimeAuthMode` = `application`, and `clientSecret` → continue. The app opens at `https://<org>.uipath.host/<routingName>`.

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

Keep `config.json` out of source control (it holds the secret). `runtimeAuthMode application` is what makes the app public; the same package deploys as a sign-in app with `user`.

## Upgrade and secret rotation

```bash
uip solution pack . ./output --version 1.0.1 && uip solution publish ./output/Feedback_1.0.1.zip
uip solution deploy upgrade <deployment key> --version 1.0.1     # add --discard-draft if a stale draft blocks it
```

The upgrade keeps the stored secret **and its scope** (a changed `scope` in `uipath.json` does not apply to a running deployment). To rotate the secret: Orchestrator → the deployment folder → **Apps** → ⋮ → **Edit** → client secret. It is checked when you save.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `ValidationError`, no request sent | Call not supported in public mode (rule 3) |
| 403 on every call | Resource not in `bindings_v2.json`, name or folder in the code doesn't match its entry, or not connected at deploy |
| 403 `Missing permissions: EntityRecords.Create` | External application has no role in the deployment folder |
| 403 on a list call | The entity is in `session` mode |
| 404 reading a record or job output | Another visitor added it, or the visitor is in a new session |
| `invalid_client` or `invalid_scope` on every call | Wrong secret, a scope missing on the external application, or `uipath.json` missing from `source/dist` |
| Upgrade 404 | Version not published yet |
| 401 on every call in one browser only | The browser blocks third-party cookies; allow them for the app, or try another browser |
| Deploy screen does not list the external application | It is not confidential; or deploy with the CLI |
| Local run: `answers only to pages served from localhost` | Open the app on `localhost` or `127.0.0.1`, not a network address |
