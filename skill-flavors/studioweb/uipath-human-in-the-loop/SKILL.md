<!--skill-flavor:flow-sdk-hitl-stop:start-->
**Flow surface (a `.flow.ts`, a `.flow`, or a new flow) — the default: stop here.** Hand the HITL request to the `uipath-maestro-flow` skill: it authors `hitl(...)` in `<Name>.flow.ts` — decompiling an existing `.flow` first — and compiles ([hitl.md](../uipath-maestro-flow/references/hitl.md)). Never read or hand-edit the compiled `.flow`; the next `compile` overwrites it. Steps 2–6 below cover the Case, Low-Code Agent and Maestro surfaces.

<!--skill-flavor:flow-sdk-hitl-stop:end-->
<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` file exists and the surface is Flow**, create the Flow project with the `CreateProjects` tool.
<!--skill-flavor:flow-project-creation:end-->
