<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

**The `uip rpa` CLI tool is not available in Studio Web.** The browser bundle does not ship it, so every `uip rpa` command in this skill — `init`, `validate`, `build`, `run`, `debug`, `activities`, `templates` — fails here, and nothing can check a workflow the agent writes. Editing RPA projects is therefore not supported in Studio Web. In this host, use this skill only to **read, explain, review, and troubleshoot** existing workflows (`.xaml`, `.cs`), `project.json`, and test cases.

- **Do NOT create, write, edit, rename, or delete any file in an RPA project** — no `.xaml`, `.cs`, `project.json`, or dependency change, no `uip rpa init`, no "small fix", and no project-context files either (`.claude/rules/project-context.md`, `AGENTS.md` — the Precondition step below is skipped in this host). A workflow the Studio Web designer cannot load leaves the whole project unable to open, and nothing here can validate it first.
- **When the user asks for a change**, describe precisely what to change — file, activity, property, expression — so they can apply it in the Studio Web designer, and tell them once that Autopilot in Studio Desktop is the complete RPA authoring experience.
- **Skip every `uip rpa` step in this skill** and read the files directly instead; do not try the command "just to check".
- The authoring rules below still apply as **knowledge** when you review or explain a workflow — not as instructions to act on.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:project-context-precondition:start-->
Not applicable in Studio Web: the agent does not write into RPA projects here, so there is no discovery agent and no `.claude/rules/project-context.md` or `AGENTS.md` to create or refresh. Read `project.json` and the workflows the user is asking about directly.
<!--skill-flavor:project-context-precondition:end-->

<!--skill-flavor:rules-project-creation:start-->
2. **Do NOT create RPA projects in Studio Web.** `uip rpa init` is not available here and editing is not supported (§ Studio Web Scope). When the user wants a new RPA project, point them to the Studio Web designer's project creation or to Autopilot in Studio Desktop; never write `project.json` or scaffolding by hand as a substitute.
2a. *Not applicable in Studio Web — no project is created here.* When reviewing an existing project, `targetFramework` in `project.json` still tells you its mode: `Portable` is the only framework Studio Web edits; `Windows` and `Legacy` projects are Studio Desktop projects.
<!--skill-flavor:rules-project-creation:end-->

<!--skill-flavor:rules-validation-gate:start-->
3. **No validation gate exists in Studio Web.** `uip rpa validate`, `uip rpa build`, and `uip rpa run` are all unavailable here — which is exactly why the agent must not edit. When reviewing a workflow, reason from the XAML and coded rules in the references directly and flag anything the designer or a build would reject; never claim a workflow "validates" or "builds".
4. **Never declare a workflow verified in Studio Web.** With no `validate`, `build`, or `run`, the honest framing is what you read and what you found; verification happens in the Studio Web designer or in Studio Desktop.
<!--skill-flavor:rules-validation-gate:end-->

<!--skill-flavor:studio-web-destination:start-->
**Studio Web host → nothing to build or ship.** Editing is not supported in this host (see "Studio Web Scope" above): do not create the project with `uip rpa init` and do not hand off to `uipath-solution`. The RPA project the user is asking about already lives in the open solution — read and analyze it in place.
<!--skill-flavor:studio-web-destination:end-->

<!--skill-flavor:report-what-was-done:start-->
1. **What was done** — files read and what you found in them (list file paths); nothing was created, edited, or deleted
<!--skill-flavor:report-what-was-done:end-->

<!--skill-flavor:report-validation-status:start-->
2. **Validation status** — not available in Studio Web (no `uip rpa validate` or `uip rpa build`); say so explicitly, and list what you checked by reading and what the designer or Studio Desktop still has to verify
<!--skill-flavor:report-validation-status:end-->

<!--skill-flavor:report-how-to-run:start-->
4. **How to run** — from the Studio Web designer (`uip rpa run` and `uip rpa debug start` are not available here)
<!--skill-flavor:report-how-to-run:end-->
