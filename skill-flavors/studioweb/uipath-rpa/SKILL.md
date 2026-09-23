<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

Editing RPA projects is not supported in Studio Web. In this host, use this skill only to **read, explain, review, and troubleshoot** existing workflows (`.xaml`, `.cs`), `project.json`, and test cases.

- **Do NOT create, write, edit, rename, or delete any file in an RPA project** — no `.xaml`, `.cs`, `project.json`, or dependency change, no `uip rpa init`, and no "small fix". The Studio Web designer cannot check agent-written XAML here (`uip rpa` is not available in Studio Web), and a workflow it cannot load leaves the whole project unable to open.
- **When the user asks for a change**, describe precisely what to change — file, activity, property, expression — so they can apply it in the Studio Web designer, and tell them once that Autopilot in Studio Desktop is the complete RPA authoring experience.
- **Skip every `uip rpa` step in this skill** (`validate`, `build`, `run`, `debug`, `activities`, `templates`); the command does not exist in Studio Web. Read the files directly instead.
- The authoring rules below still apply as **knowledge** when you review or explain a workflow — not as instructions to act on.
<!--skill-flavor:host-scope:end-->

<!--skill-flavor:studio-web-destination:start-->
**Studio Web host → nothing to build or ship.** Editing is not supported in this host (see "Studio Web Scope" above): do not create the project with `uip rpa init` and do not hand off to `uipath-solution`. The RPA project the user is asking about already lives in the open solution — read and analyze it in place.
<!--skill-flavor:studio-web-destination:end-->
