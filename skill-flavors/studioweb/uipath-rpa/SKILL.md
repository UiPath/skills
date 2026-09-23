<!--skill-flavor:host-scope:start-->
## Studio Web Scope: Read and Analyze Only

**The `uip rpa` CLI tool is not available in Studio Web.** The browser bundle does not ship it. Two verbs still work because the Studio Web host intercepts them and serves them itself: `uip rpa init <ProjectName>` creates the project from Studio Web's native template, and `uip rpa run` runs an existing project. Every other `uip rpa` verb — `validate`, `build`, `debug`, `activities`, `templates`, `files`, `analyzer-rules` — does not exist here.

Nothing in this host can check a workflow the agent writes: there is no `validate` and no `build`, and a workflow the Studio Web designer cannot load leaves the whole project unable to open. **Authoring RPA workflows is therefore not supported in Studio Web.** Use this skill to **read, explain, review, and troubleshoot** existing workflows (`.xaml`, `.cs`), `project.json`, and test cases.

- **Do NOT create, write, edit, rename, or delete any file in an RPA project** — no `.xaml`, `.cs`, `project.json`, or dependency change, and no "small fix". Creating the empty project with `uip rpa init` is fine; filling it in is not, so stop at the scaffold and hand the authoring over.
- **When the user asks for a change**, describe precisely what to change — file, activity, property, expression — so they can apply it in the Studio Web designer, and tell them once that Autopilot in Studio Desktop is the complete RPA authoring experience.
- **Do not write project-context files either** (`.claude/rules/project-context.md`, `AGENTS.md`); the Precondition step below is skipped in this host.
- **Skip every `uip rpa` step in this skill** except `init` and `run`, and read the files directly instead; do not try an unavailable command "just to check".
- The authoring rules below still apply as **knowledge** when you review or explain a workflow — not as instructions to act on.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:project-context-precondition:start-->
Not applicable in Studio Web: the agent does not write into RPA projects here, so there is no discovery agent and no `.claude/rules/project-context.md` or `AGENTS.md` to create or refresh. Read `project.json` and the workflows the user is asking about directly.
<!--skill-flavor:project-context-precondition:end-->

<!--skill-flavor:rules-project-creation:start-->
2. **`uip rpa init` creates the project, and that is where the agent stops.** The Studio Web host intercepts `init` and seeds its own native scaffold, so template flags are ignored and no template search applies. Do not author the workflow afterwards (§ Studio Web Scope) — hand it to the user in the Studio Web designer, or to Autopilot in Studio Desktop. Never write `project.json` or scaffolding by hand.
2a. *Not applicable in Studio Web — the host picks the framework for the project it creates.* When reviewing an existing project, `targetFramework` in `project.json` still tells you its mode: `Portable` is the only framework Studio Web edits; `Windows` and `Legacy` projects are Studio Desktop projects.
<!--skill-flavor:rules-project-creation:end-->

<!--skill-flavor:rules-validation-gate:start-->
3. **No validation gate exists in Studio Web.** `uip rpa validate` and `uip rpa build` do not exist here — which is exactly why the agent must not author workflows. When reviewing one, reason from the XAML and coded rules in the references directly and flag anything the designer or a build would reject; never claim a workflow "validates" or "builds".
4. **Never declare a workflow verified in Studio Web.** With no `validate` and no `build`, the honest framing is what you read and what you found. `uip rpa run` is available and its outcome is real evidence about an existing project, but a run is not a validation gate and proves nothing about a file the agent did not author.
<!--skill-flavor:rules-validation-gate:end-->

<!--skill-flavor:studio-web-destination:start-->
**Studio Web host → nothing to wrap or ship.** The project lives in the open solution already: `uip rpa init <NAME>` creates it there and the host registers it, so no solution wrapping, import, or upload step applies and there is no hand-off to `uipath-solution`. Authoring the workflow is not supported in this host (see "Studio Web Scope" above).
<!--skill-flavor:studio-web-destination:end-->

<!--skill-flavor:report-what-was-done:start-->
1. **What was done** — files read and what you found in them (list file paths), plus the project created if you ran `uip rpa init`; no workflow content was authored
<!--skill-flavor:report-what-was-done:end-->

<!--skill-flavor:report-validation-status:start-->
2. **Validation status** — not available in Studio Web (no `uip rpa validate` or `uip rpa build`); say so explicitly, and list what you checked by reading and what the designer or Studio Desktop still has to verify
<!--skill-flavor:report-validation-status:end-->

<!--skill-flavor:report-how-to-run:start-->
4. **How to run** — `uip rpa run` (host-served here), or the Run button in the Studio Web designer; `uip rpa debug start` is not available in this host
<!--skill-flavor:report-how-to-run:end-->
