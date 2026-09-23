<!--skill-flavor:host-scope:start-->
## Studio Web Command Scope

**The `uip function` CLI tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `new`, `init`, `serve`, `run`, `pack` and `publish` all fail here — and there is no local Python, Node, npm or dev server to fall back on. Studio Web cannot create a Function project either: the host creates flow, case, agent, api-workflow, bpmn and rpa projects only.

Everything else in this skill applies. Read and edit the function project's files directly — `pyproject.toml` / `package.json`, `uipath.json`, entrypoints, typed contracts and the function source — following the authoring rules below. What you cannot do here is scaffold, serve, run, test, pack, publish or deploy, so do not run those commands or report a function as run, tested or published. Make the edit, then tell the user which step to run with the Node CLI on their machine. Diagnosing a deployed failure works from the project files plus the families that *are* bundled (`uip or`, `uip traces`).

<!--skill-flavor:host-scope:end-->
