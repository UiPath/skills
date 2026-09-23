<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

**The `uip function` CLI tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `new`, `init`, `serve`, `run`, `pack` and `publish` all fail here — and there is no local Python, Node, npm or dev server to fall back on. Studio Web cannot create a Function project either: the host creates flow, case, agent, api-workflow, bpmn and rpa projects only.

Nothing in this host can scaffold, run, test, pack or publish a function, so an edit cannot be verified — a broken entrypoint, contract or `uipath.json` map only surfaces at deploy. **Authoring functions is therefore not supported in Studio Web.** Use this skill to **read, explain, review, and troubleshoot** an existing function project: `pyproject.toml` / `package.json`, `uipath.json`, entrypoints, typed contracts, and the function source.

- **Do NOT create, write, edit, rename, or delete any file in a function project**, and do not scaffold one.
- **When the user asks for a change**, describe precisely what to change — file, function, schema field, `uipath.json` entry — so they can apply it in the Studio Web editor, or point them at the Node CLI on their machine for the full `new` → `run` → `pack` → `publish` loop.
- **Skip every `uip function` step in this skill** and read the files directly instead; do not try the command "just to check".
- Diagnosing a deployed failure is in scope, from the project files plus Orchestrator job logs through the commands that *are* bundled (`uip or`, `uip traces`).
- The authoring rules below still apply as **knowledge** when you review or explain a function — not as instructions to act on.

<!--skill-flavor:host-scope:end-->
