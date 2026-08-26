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
> So the Studio Web pipeline is: **push → publish → deploy**. `uip codedapp init`, `push`, `pull` and `deploy` all work normally; only `pack` is absent.
<!--skill-flavor:codedapp-pipeline-host:end-->
