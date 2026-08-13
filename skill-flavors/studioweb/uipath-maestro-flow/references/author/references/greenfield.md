<!--skill-flavor:greenfield-t1-execution:start-->
| **T1 — Setup + discovery** | 0, 1, 2, 3 | One host project-creation call through the live `proxy-tools-Solution` / `CreateProjects` schema **+** parallel `Bash` (one `registry get` per independent OOTB type you'll inline) **+** parallel `Read` (plugin `impl.md`s). After creation succeeds, locate the host-generated project and `.flow` entrypoint in the Studio Web workspace/VFS. |
<!--skill-flavor:greenfield-t1-execution:end-->

<!--skill-flavor:greenfield-init-batching:start-->
- **Local project setup.** Never substitute `solution init`, `flow init`, or manual metadata edits for Studio Web project creation. Inspect and invoke the live `CreateProjects` schema once, then locate the generated project in the workspace/VFS.
- **Sequential `registry get`s.** Emit every independent `registry get` as a parallel `Bash` in the same message as the host setup call.
<!--skill-flavor:greenfield-init-batching:end-->

<!--skill-flavor:greenfield-step-zero-concurrency:start-->
This probe is read-only — emit it in parallel with the Step 2 host project-creation call. It does not need its own turn.
<!--skill-flavor:greenfield-step-zero-concurrency:end-->

<!--skill-flavor:greenfield-author-login-boundary:start-->
Studio Web owns authentication for Step 2 project creation. Local `validate`, `format`, OOTB registry queries, and `Edit` / `Write` authoring do not require `uip login`; tenant-specific connector/resource discovery and Operate actions may still require authenticated host or CLI capabilities.
<!--skill-flavor:greenfield-author-login-boundary:end-->

<!--skill-flavor:project-creation:start-->
## Step 2 — Create the Flow project through Studio Web **[T1]**

Studio Web already supplies the target solution and owns its project scaffolding and metadata. Do not inspect the workspace for `.uipx` files, create a local solution, or run `uip maestro flow init`.

<a id="canonical-t1-chain--issue-this-as-one-bash-call"></a>

### Canonical T1 chain — issue setup in ONE assistant message

1. Inspect the live ProxyTool schema for `proxy-tools-Solution` and its `CreateProjects` operation.
2. Invoke `CreateProjects` for a Flow project using only the fields and enum values declared by that live schema. Never guess or hardcode the ProxyTool request shape.
3. In parallel, refresh the Flow registry as described in Step 3 and fetch any independent OOTB node definitions needed for authoring.
4. After project creation succeeds, inspect the Studio Web workspace/VFS, locate the generated project and `.flow` entrypoint, and use that host-exposed tree as the source of truth for every subsequent edit.

Do not create project folders, `project.uiproj`, generated support files, or solution registration metadata by hand. If `CreateProjects` or the Flow project type is not exposed, report the capability gap and stop project creation instead of falling back to a local CLI scaffold.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:greenfield-registry-transition:start-->
## Step 3 — Refresh the registry **[T1 — after Step 2]**

After the host creates the project and exposes its `.flow` entrypoint, refresh the registry:
<!--skill-flavor:greenfield-registry-transition:end-->

<!--skill-flavor:greenfield-end-node-discovery:start-->
**Parallel `registry get`** — in the same T1 assistant message, emit one separate `Bash` per OOTB node type whose definition you'll inline in T2. Inspect the host-generated `.flow`; if it does not contain `core.control.end`, fetch that definition before Step 4.
<!--skill-flavor:greenfield-end-node-discovery:end-->

<!--skill-flavor:greenfield-build-scaffold-assumptions:start-->
> **Treat the host-generated `.flow` as authoritative.** Inspect its initial nodes and edges instead of assuming a local scaffold shape. A new Flow commonly contains only the manual trigger (`start` / `core.trigger.manual`) with zero edges; add any missing user-owned nodes, including End, via `Edit` / `Write`. Preserve any host- or CLI-owned connector nodes and their `bindings[]` / `inputs.detail`.
<!--skill-flavor:greenfield-build-scaffold-assumptions:end-->

<!--skill-flavor:greenfield-t2-read-source:start-->
1. **One `Read`** of the host-generated `<ProjectName>.flow` — required before any Edit/Write; the Step 2 project-creation operation produced the file, and the workspace file-state tracker does not auto-refresh after host mutations.
<!--skill-flavor:greenfield-t2-read-source:end-->
