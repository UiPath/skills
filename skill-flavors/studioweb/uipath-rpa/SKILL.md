<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

**The `uip rpa` CLI tool is not available in Studio Web.** The browser bundle does not ship it, so every `uip rpa` command in this skill — `init`, `validate`, `build`, `run`, `debug`, `activities`, `templates` — fails here, and nothing can check a workflow the agent writes. Editing RPA projects is therefore not supported in Studio Web. In this host, use this skill only to **read, explain, review, and troubleshoot** existing workflows (`.xaml`, `.cs`), `project.json`, and test cases.

- **Do NOT create, write, edit, rename, or delete any file in an RPA project** — no `.xaml`, `.cs`, `project.json`, or dependency change, no `uip rpa init`, and no "small fix". A workflow the Studio Web designer cannot load leaves the whole project unable to open, and nothing here can validate it first.
- **When the user asks for a change**, describe precisely what to change — file, activity, property, expression — so they can apply it in the Studio Web designer, and tell them once that Autopilot in Studio Desktop is the complete RPA authoring experience.
- **Skip every `uip rpa` step in this skill** and read the files directly instead; do not try the command "just to check".
- The authoring rules below still apply as **knowledge** when you review or explain a workflow — not as instructions to act on.
<!--skill-flavor:host-scope:end-->

<!--skill-flavor:studio-web-destination:start-->
**Studio Web host → nothing to build or ship.** Editing is not supported in this host (see "Studio Web Scope" above): do not create the project with `uip rpa init` and do not hand off to `uipath-solution`. The RPA project the user is asking about already lives in the open solution — read and analyze it in place.
<!--skill-flavor:studio-web-destination:end-->
