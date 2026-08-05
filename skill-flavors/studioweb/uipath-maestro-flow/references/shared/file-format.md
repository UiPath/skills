<!-- skill-flavor:file-version-source:start -->
**Top-level `version`** is owned by the Studio Web-generated Flow scaffold. Preserve the exact value in the existing `.flow`; never hardcode it and never create a throwaway project with an init command to discover it. If the project has no generated `.flow` or version, report the incomplete host scaffold instead of inventing one.
<!-- skill-flavor:file-version-source:end -->

<!-- skill-flavor:generated-project-identifiers:start -->
`solutionId` and `projectId` may appear at the top level. They are owned by Studio Web project creation and publishing. Preserve them; do not add, replace, or derive them from local metadata.
<!-- skill-flavor:generated-project-identifiers:end -->

<!-- skill-flavor:project-structure:start -->
## Project structure in Studio Web

List `/solution/<project name>/` after `CreateProjects` completes and treat the returned tree as authoritative. A typical Flow project exposes a `.flow`, `project.uiproj`, `bindings_v2.json`, `entry-points.json`, and other sidecars, but the exact filenames are host-owned and may evolve.

- Edit only the existing `.flow` for user-owned Flow structure.
- Preserve `project.uiproj` and generated sidecars unless a live Studio Web capability explicitly owns their update.
- Do not expect a parent `.uipx`; Studio Web solutions are backend entities.
- Do not create missing scaffold files merely to reproduce a desktop layout.
<!-- skill-flavor:project-structure:end -->

<!-- skill-flavor:entry-points-ownership:start -->
## entry-points.json — generated, do not edit

Preserve the `entry-points.json` created by Studio Web. Declare Flow inputs and outputs through variables in the `.flow`. Use a live-advertised Flow or host capability to regenerate derived metadata when one exists; otherwise report that the derived-file refresh is unavailable. Do not run init, upload, or a desktop debug command merely to recreate this sidecar.
<!-- skill-flavor:entry-points-ownership:end -->
