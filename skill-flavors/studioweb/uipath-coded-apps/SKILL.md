<!--skill-flavor:host-scope:start-->
## Studio Web Command Scope

**The `uip codedapp` CLI tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `init`, `push`, `pull`, `pack`, `publish` and `deploy` all fail here. Neither is there a local Node, npm or `create-vite` to scaffold the React app, nor a dev server to run it. Studio Web cannot create an AppV2 project either: the host creates flow, case, agent, api-workflow, bpmn and rpa projects only.

Everything else in this skill applies. Read and edit the app's files directly — React/TypeScript source, `package.json`, `uipath.json`, `webAppManifest.json`, OAuth scopes and SDK usage — following the authoring rules below. What you cannot do here is scaffold, install dependencies, build, run, pack, publish or deploy, so do not run those commands or report an app as built, run or deployed. Make the edit, then tell the user which step to run with the Node CLI and npm on their machine. Diagnosing a deployed failure works from the project files plus the families that *are* bundled (`uip or`, `uip traces`).

<!--skill-flavor:host-scope:end-->
