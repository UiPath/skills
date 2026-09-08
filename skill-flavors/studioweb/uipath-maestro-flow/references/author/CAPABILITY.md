<!--skill-flavor:project-creation-scope:start-->
- Create a new Flow project in the open solution with `uip flow init <ProjectName>` (alias `uip maestro flow init`) — the host creates the project entity and seeds `/solution/<ProjectName>/new.flow`; never try to create a second solution (the host refuses it)
<!--skill-flavor:project-creation-scope:end-->

<!--skill-flavor:author-rule-edit-flow-only:start-->
4. **Edit `new.flow` only** (`/solution/<ProjectName>/new.flow`) — `project.uiproj` is host-owned, and the host-generated `entry-points.json`, `new.bpmn`, `operate.json`, `package-descriptor.json`, `simulations.json`, `evals/` (which appear after the first debug/publish) plus the `bindings_v2.json` written by `node configure` are never hand-edited; never treat their absence as an error. To declare flow inputs/outputs, add variables in the `.flow` file (see [shared/file-format.md](../shared/file-format.md)).
<!--skill-flavor:author-rule-edit-flow-only:end-->

<!--skill-flavor:author-rule-format-after-edits:start-->
12. **Always run `flow format` after edits** — `uip maestro flow format new.flow` is the canonical layout step. Format arranges nodes horizontally, sets each node's `size` by its canvas shape (inline agents → 288×96, containers → 560×320, everything else → 96×96), and recurses into subflows (`subflows[<id>].layout`). Skipping format is the most common cause of misshapen nodes in Studio Web.
<!--skill-flavor:author-rule-format-after-edits:end-->

<!--skill-flavor:project-creation-antipatterns:start-->
- **Never create a second solution or a project directory by hand** — Studio Web works on one open solution (`/solution`); the host refuses solution creation and `mkdir /solution/<Name>` is rejected. Create Flow projects only with `uip flow init <ProjectName>`; registration into the solution is automatic and there is no solution manifest on disk to edit.
<!--skill-flavor:project-creation-antipatterns:end-->

<!--skill-flavor:author-antipattern-generated-files-and-local:start-->
- **Never hand-edit the host-generated `new.bpmn`** — the host derives it from `new.flow` on debug/publish and overwrites it.
- **Never use `core.logic.mock` when the resource is in the same solution** — list the in-solution projects with `uip solution resources list --kind Process --output json` (`solutionResources`) and wire them. Mock placeholders are only for resources that are not in the current solution and not yet published.
<!--skill-flavor:author-antipattern-generated-files-and-local:end-->

<!--skill-flavor:author-antipattern-resource-bindings:start-->
- **Never author `model.context[]` on resource-node instances** — resource-node instances have no `model` block. For `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl), the definition (from `registry get`) already carries `model.context[]` with `<bindings.{name}>` placeholders. Your job is to add matching entries to the top-level `bindings[]` array — two entries per resource node (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. At BPMN emit, the runtime rewrites `<bindings.{name}>` → `=bindings.{id}` via `(resourceKey, name)` matching. Without the top-level `bindings[]` entries, `uip maestro flow validate` passes but `uip flow debug` fails with "Folder does not exist or the user does not have access to the folder." See the resource plugin's `impl.md`.
<!--skill-flavor:author-antipattern-resource-bindings:end-->
