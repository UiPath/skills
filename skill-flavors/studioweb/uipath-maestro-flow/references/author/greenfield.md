<!--skill-flavor:greenfield-execution-map-intro:start-->
## Three-turn execution map

Studio Web prepends **T0 — project creation**: `CreateProjects` is its own host tool call, and its output (generated project + `.flow` entrypoint) is required before T1 can run. T1–T3 then follow the canonical map unchanged, so every `[T1]` / `[T2]` / `[T3]` tag on the steps below keeps its canonical meaning. Emit every tool call inside the same Turn as one assistant message.

| Turn | Steps | What you emit in ONE assistant message |
|---|---|---|
<!--skill-flavor:greenfield-execution-map-intro:end-->

<!--skill-flavor:greenfield-t1-execution:start-->
| **T0 — Project creation** | 2 | One `CreateProjects` tool call. After it succeeds, locate the host-generated project and `.flow` entrypoint before starting T1. |
| **T1 — Setup + discovery** | 0, 3 | One chained `Bash` (register + pull + `node add` for each CLI-owned node) **+** parallel `Bash` (one `registry get` per independent OOTB type you'll inline) **+** parallel `Read` (plugin `impl.md`s). |
| **T2 — Read + author** | 4 | One `Read` of the `.flow` **+** a batch of `Edit` calls (or one `Write` if ≥70% of nodes change). Claude Code serializes Edits on the same file, so they don't race |
| **T3 — Finalize** | 5, 6 | One chained `Bash` (`node configure && validate && format`). On validate failure: one Edit turn, then re-chain `validate && format` |
<!--skill-flavor:greenfield-t1-execution:end-->

<!--skill-flavor:greenfield-init-batching:start-->
- **One CLI per turn.** Never issue `node configure`, then `validate`, then `format` as three separate Bash calls — chain them as `node configure && validate && format`.
<!--skill-flavor:greenfield-init-batching:end-->

<!--skill-flavor:greenfield-step-zero-concurrency:start-->
Emit this read-only probe in parallel with the T1 setup chain after project creation succeeds.
<!--skill-flavor:greenfield-step-zero-concurrency:end-->

<!--skill-flavor:greenfield-author-login-boundary:start-->
<!--skill-flavor:greenfield-author-login-boundary:end-->

<!--skill-flavor:project-creation:start-->
## Step 2 — Create the Flow project through Studio Web **[T0]**

Studio Web supplies the target solution and owns its project scaffolding and metadata.

### T0 project-creation turn

1. Inspect the live `CreateProjects` schema.
2. Invoke `CreateProjects` for a Flow project using only the fields and enum values declared by that live schema. Treat the live schema as the request contract.
3. After project creation succeeds, inspect the Studio Web workspace/VFS, locate the generated project and `.flow` entrypoint, and use that host-exposed tree as the source of truth for every subsequent edit.

If `CreateProjects` or the Flow project type is unavailable, report the capability gap and await user direction.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:greenfield-registry-transition:start-->
## Step 3 — Refresh the registry **[T1 — after project creation]**

After T0 succeeds, run registration, registry refresh, and each CLI-owned `node add` in the T1 chained `Bash`.
<!--skill-flavor:greenfield-registry-transition:end-->

<!--skill-flavor:greenfield-end-node-discovery:start-->
**Parallel `registry get`** — in the same T1 assistant message, emit one separate `Bash` per OOTB node type whose definition you'll inline in T2. Inspect the host-generated `.flow`; if it does not contain `core.control.end`, fetch that definition before Step 4.
<!--skill-flavor:greenfield-end-node-discovery:end-->

<!--skill-flavor:greenfield-build-scaffold-assumptions:start-->
> **Treat the host-generated `.flow` as authoritative.** Inspect its initial nodes and edges. A new Flow commonly contains only the manual trigger (`start` / `core.trigger.manual`) with zero edges; add any missing user-owned nodes, including End, via `Edit` / `Write`. Preserve any host- or CLI-owned connector nodes and their `bindings[]` / `inputs.detail`.
<!--skill-flavor:greenfield-build-scaffold-assumptions:end-->

<!--skill-flavor:greenfield-t2-read-source:start-->
1. **One `Read`** of the host-generated `<ProjectName>.flow` — required before any Edit/Write because Step 2 produced the file and host mutations require a fresh workspace read.
<!--skill-flavor:greenfield-t2-read-source:end-->
