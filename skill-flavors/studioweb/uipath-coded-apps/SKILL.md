<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

**The `uip codedapp` CLI tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `init`, `push`, `pull`, `pack`, `publish` and `deploy` all fail here. Neither is there a local Node, npm or `create-vite` to scaffold the React app, nor a dev server to run it. Studio Web cannot create an AppV2 project either: the host creates flow, case, agent, api-workflow, bpmn and rpa projects only.

Nothing in this host can scaffold, build, run, pack, publish or deploy a coded app, so an edit cannot be verified — a broken build or manifest only surfaces at deploy. **Authoring coded apps is therefore not supported in Studio Web.** Use this skill to **read, explain, review, and troubleshoot** an existing app: its React/TypeScript source, `package.json`, `uipath.json`, `webAppManifest.json`, OAuth scopes and SDK usage.

- **Do NOT create, write, edit, rename, or delete any file in a coded-app project**, and do not scaffold one.
- **When the user asks for a change**, describe precisely what to change — file, component, manifest field, scope — so they can apply it in the Studio Web editor, or point them at the Node CLI and npm on their machine for the full scaffold → build → `pack` → `publish` → `deploy` loop.
- **Skip every `uip codedapp`, `npm` and `create-vite` step in this skill** and read the files directly instead; do not try the command "just to check".
- Diagnosing a deployed failure is in scope, from the project files plus the commands that *are* bundled (`uip or`, `uip traces`).
- The authoring rules below still apply as **knowledge** when you review or explain an app — not as instructions to act on.

<!--skill-flavor:host-scope:end-->
