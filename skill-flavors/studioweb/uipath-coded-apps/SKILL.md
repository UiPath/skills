<!--skill-flavor:codedapp-pipeline-host:start-->
**Do NOT pause between steps to ask "should I continue?" — execute the full pipeline. Only stop if you need auth credentials or an app name.**

> **In Studio Web the whole coded-app lifecycle runs in the browser — no local machine, no build step, no push.**
>
> The pipeline is: **CreateProjects → `uip codedapp init` → `uip codedapp publish` → OAuth client → `uip codedapp deploy` → open the URL.**
>
> **1. Create the project with the CreateProjects tool** (`projectType: "AppV2"`). This makes the coded-app project inside the open solution and registers it there. It arrives **empty** — just `project.uiproj` and `webAppManifest.json` under `/solution/<ProjectName>/`. Do not use `uip codedapp init` to create a *new* project here (that path needs the desktop resource builder); CreateProjects is the creation step.
>
> **2. Initialize the project in place:** `uip codedapp init /solution/<ProjectName>`. Because the folder already holds `project.uiproj` + `webAppManifest.json`, init runs in **Studio Web mode**: it writes a ready-to-serve starter bundle to `source/dist/` (plus `source/uipath.json`, `source/package.json`) and sets the manifest's `config.bundlePath` to `source/dist` — exactly the state a developer's `uip codedapp push` would produce. The result carries `Data.StudioWebProject: { bundlePath: "source/dist", manifestUpdated: true }` and `SolutionRegistration.Status: "Skipped"` (Studio Web owns registration). No `--force` is needed even though the folder is not empty. **The `/solution/...` filesystem is the Studio Web project itself** — files you write there are the project's files, so you may edit `source/dist/index.html` (or add `.js`/`.css` next to it) to build the real app before publishing. Text files only; nothing under `/solution` can be deleted.
>
> **Before publishing: every coded app in the solution needs a bundle.** Studio Web packages the *whole solution*; one coded-app project without `source/dist` fails the entire publish with *"Compiled bundle not found at …/<Project>/source/dist"* — and that failure is only visible in Studio Web's Publish history, not to the command that submitted it. List the solution's projects (`ls /solution`) and run `uip codedapp init /solution/<Name>` for **each** coded app that still has only `project.uiproj` + `webAppManifest.json`.
>
> **3. Publish:** `uip codedapp publish` (bare — no pack, no package argument). In Studio Web this is routed to Studio Web's own publish flow, which packages the app client-side from `source/dist` and uploads it. There is **no `uip codedapp pack`** in the browser (the packager is Node-only); calling it only tells you to publish. Publish waits for the background packaging and reports the real outcome — `Failed` comes back with the packager's error text (fix it and publish again); if it reports the request still `Pending` after the wait, the packaging never ran (tab reloaded mid-publish) — publish again. Only a reported success means there is something to deploy. Keep the tab open until it completes — packaging happens in the browser.
>
> **4. Create the OAuth client — deploy fails without one** (*"missing required properties: externalClientId"*), and nothing creates it for you. Decide the routing name first (the app's URL path, e.g. `expense-app`) because the redirect URI must match the deployed URL exactly — `deploy` does **not** register redirect URIs:
>
> ```bash
> uip admin external-apps create "<app name>" --non-confidential \
>   --redirect-uri "https://<org-host>.<env>.uipath.host/<routing-name>" \
>   --user-scope "<scopes the app needs>"
> ```
>
> `<org-host>` is the org name with `_` → `-`; `<env>` is `alpha`/`staging` (omit the `.<env>` segment on production `cloud.uipath.com`). Pass the returned `Id` to deploy as `--client-id`.
>
> **5. Deploy:** `uip codedapp deploy -n <app name> --path-name <routing-name> --client-id <id> --folder-key <folder key>`. `deploy` finds the published app server-side by name, so it needs no local state. `--folder-key` is required in the browser (there is no interactive folder picker): list folders with `uip or folders list --output json` and pick one — ask the user only if the choice is not obvious. One rule: the Apps service allows **one deployment of a published app per folder** — a second deploy into the same folder fails with `400 / 1004 "app already deployed in folder"`; use another folder or upgrade the existing deployment.
>
> **6. View:** deploy returns the app URL (`https://<org-host>.<env>.uipath.host/<routing-name>`). Give it to the user and, if you can, open it to confirm it loads. "Publish submitted" is not "live" — only a successful deploy with a URL is.
>
> **Every step runs same-origin inside Studio Web.** The Apps and Identity APIs do not accept the `Authorization` header cross-origin, so this works from the Autopilot shell (on the UiPath origin), not from an arbitrary page. `uip codedapp push` / `pull` are for syncing with a developer's IDE and are not part of this flow.
<!--skill-flavor:codedapp-pipeline-host:end-->
