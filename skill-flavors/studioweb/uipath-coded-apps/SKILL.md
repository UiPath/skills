<!--skill-flavor:codedapp-pipeline-host:start-->
**Do NOT pause between steps to ask "should I continue?" — execute the full pipeline. Only stop if you need auth credentials or an app name.**

> **In Studio Web the pipeline is shorter: there is no pack step.**
>
> - **Do not run `uip codedapp pack`.** The verb is not in the browser CLI bundle — the AppV2 packager is Node-only, so `./commands/pack` is excluded. Calling it returns a message telling you to publish instead.
> - **`uip codedapp publish` is routed to Studio Web's publish flow**, which packages the app for you. Packaging runs client-side, in the browser, using the same AppV2 packager the Node CLI uses — you do not invoke it and there is no `.nupkg` on disk.
> - **What gets packaged is the Studio Web project's content, not your local `dist/`.** Publish builds from a server-side snapshot, so run `uip codedapp push` first if you have local changes that must ship. There is no local build step in this path.
> - **Publish is asynchronous.** It returns once the request is accepted; packaging and upload continue in the background. Where the host supports it, the command waits and reports the real outcome; otherwise it says completion is not observable and points at the Studio Web Publish history. Do not treat "submitted" as "shipped" — check before telling the user the app is live.
> - **Keep the tab open until publish reports completion.** Packaging happens in the browser, so navigating away mid-publish strands the request in `Pending`.
>
> So the Studio Web pipeline is: **init → OAuth client → publish → deploy**. `uip codedapp init`, `push`, `pull` and `deploy` all work normally; only `pack` is absent.
>
> **A coded app cannot deploy without an OAuth client, and nothing creates one for you.** Deploy validation fails with *"missing required properties: externalClientId"*. Create it in-session — the command is in the browser bundle:
>
> ```bash
> uip admin external-apps create "<app name>" --non-confidential \
>   --redirect-uri "https://<org-host>.<env>.uipath.host/<routing-name>" \
>   --user-scope "<scopes the app needs>"
> ```
>
> Then pass the returned `Id` to deploy as `--client-id <id>`. `deploy` reads `--client-id`, not `uipath.json`, so no file edit is needed. **Order matters**: pick the routing name (`--path-name`) first, because the redirect URI must match the deployed URL exactly — `deploy` does **not** register redirect URIs on the client, despite what older guidance says.
>
> **`deploy` needs no local state.** It finds the published app server-side by name, so it works on an app published from the Studio Web UI. One rule: the Apps service allows **one deployment of a published app per folder** — deploying the same app into a folder that already has it fails with `400 / 1004 "app already deployed in folder"`. Use a different folder or upgrade the existing deployment instead.
>
> **Every step here runs same-origin inside Studio Web.** The Apps and Identity APIs do not accept the `Authorization` header cross-origin, so this flow works from the Autopilot shell (which lives on the UiPath origin) and not from an arbitrary external page.
<!--skill-flavor:codedapp-pipeline-host:end-->
