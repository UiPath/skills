<!--skill-flavor:greenfield-execution-map-intro:start-->
## Three-turn execution map

Steps 0–6 are **logical phases**, not separate turns. In Studio Web project creation is a `uip` command (`uip flow init <ProjectName>`), so Step 2 chains into the same T1 `Bash` as `registry pull` and `node add` — a greenfield build collapses to **three assistant turns** (universal SKILL.md rule #10). Each step heading below carries a `[T1]` / `[T2]` / `[T3]` tag — emit every tool call inside the same Turn as one assistant message.

| Turn | Steps | What you emit in ONE assistant message |
|---|---|---|
<!--skill-flavor:greenfield-execution-map-intro:end-->

<!--skill-flavor:greenfield-t1-execution:start-->
| **T1 — Create + discover** | 0, 2, 3 | One chained `Bash` (`uip flow init <ProjectName> && cd /solution/<ProjectName> && uip maestro flow registry pull && uip maestro flow node add new.flow <type> …` — one `node add` per CLI-owned node; drop the `flow init` segment when the user already has the Flow project open) **+** parallel `Bash` (one `registry get` per OOTB type you'll inline) **+** parallel `Read` (plugin `impl.md`s). |
| **T2 — Read + author** | 4 | One `Read` of `/solution/<ProjectName>/new.flow` **+** a batch of `Edit` calls (or one `Write` if ≥70% of nodes change). Same-file Edits must not overlap — anchor each on its own top-level array (see the anchor table below); when in doubt, serialize them across two turns |
| **T3 — Finalize** | 5, 6 | One chained `Bash` (`node configure && validate && format`). On validate failure: one Edit turn, then re-chain `validate && format` |
<!--skill-flavor:greenfield-t1-execution:end-->

<!--skill-flavor:greenfield-init-batching:start-->
- **One CLI per turn.** Never issue `flow init`, then `cd`, then `registry pull` as three separate Bash calls — chain with `&&`, the `cd` included as its own segment. Same for `node configure && validate && format`.
- **Sequential `registry get`s.** Emit every `registry get` as a parallel `Bash` in one message alongside the T1 chain.
<!--skill-flavor:greenfield-init-batching:end-->

<!--skill-flavor:greenfield-step-zero-heading:start-->
## Step 0 — Command prefix **[T1]**

In Studio Web `uip` is pre-installed and its version is fixed by the host — **never probe it** (`uip --version`, `which uip`, `command -v uip`, `npm install`, and `uip tools update` are forbidden; report a capability gap instead). Authoring commands use the `uip maestro flow <verb>` form written below. The one exception is debugging: the verb is the two-token `uip flow debug` — the `maestro flow` form of debug is not intercepted by the host and fails. <!-- uip-check-skip -->
<!--skill-flavor:greenfield-step-zero-heading:end-->

<!--skill-flavor:greenfield-step-zero-concurrency:start-->
<!--skill-flavor:greenfield-step-zero-concurrency:end-->

<!--skill-flavor:greenfield-author-login-boundary:start-->
<!--skill-flavor:greenfield-author-login-boundary:end-->

<!--skill-flavor:project-creation:start-->
## Step 2 — Create the Flow project in the open solution **[T1]**

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another — the host refuses solution creation and `mkdir /solution/<Name>` is rejected. If the user already has a Flow project open (`CurrentProject.AbsolutePath`), skip this step and edit that project's `new.flow`. Otherwise create the project as the first segment of the T1 chain.

### Canonical T1 chain — issue this as ONE `Bash` call

This is the consolidated command that does Step 2 + Step 3 + (optionally) one `node add` per CLI-owned node, in one chained Bash. `node add` signature is `<file> <node-type>` (file first):

```bash
uip flow init "<ProjectName>" \
  && cd "/solution/<ProjectName>" \
  && uip maestro flow registry pull \
  && uip maestro flow node add new.flow core.action.http.v2 --label "<NodeLabel>" --output json
```

`uip flow init <ProjectName>` (alias `uip maestro flow init`) is intercepted by the host: it creates the Flow project entity through Unified Build — the same path as the New Project dialog — and prints `Created Flow project "<ProjectName>" in the open solution. Its files are under /solution/<ProjectName>.` Pass just the name (or `/solution/<ProjectName>`); a nested path is rejected and template-shaping flags are ignored. Registration into the solution is automatic — there is no `uip solution projects add` step and no solution manifest on disk to edit. Empty stdout is normal for some commands; judge success by the exit code.

Tail-append one `node add` per CLI-owned node (`uipath.connector.*`, `uipath.connector.trigger.*`, `core.action.http.v2`). Each `node add` returns the new node `id` in `Data` — capture it from the chained output for T2/T3. Drop the trailing `node add` segment when the flow is OOTB-only.

In the SAME assistant message (parallel to this chain): emit one `Bash` per OOTB `registry get <NODE_TYPE>` you'll need in T2 (always `core.control.end` — see Step 4), and parallel `Read` calls for any plugin `impl.md`s you'll consult.

### Expected layout after Step 2

```
/solution/                         ← the open solution (workspace root; no solution file on disk)
└── <ProjectName>/                 ← from `uip flow init`
    ├── new.flow                   ← the file you edit (manual trigger only, version 1.9, empty edges/definitions/bindings)
    └── project.uiproj             ← host-owned
```

Host-generated files (`entry-points.json`, `new.bpmn`, `operate.json`, `package-descriptor.json`, `simulations.json`, `evals/`) appear after the first debug/publish, and `node configure` writes `bindings_v2.json` into the project directory — never hand-edit any of them and never treat their absence as an error.

> **Bash session state persists across tool calls.** The `cd` into `/solution/<ProjectName>` stays in effect for every later `Bash` call (cwd is clamped inside `/solution`), so the commands below use the bare `new.flow`; use the absolute `/solution/<ProjectName>/new.flow` whenever the cwd is in doubt.

See [shared/file-format.md](../shared/file-format.md) for the full project structure.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:greenfield-registry-transition:start-->
## Step 3 — Refresh the registry **[T1 — chained tail of Step 2]**

This is already a segment of the [canonical T1 chain](#canonical-t1-chain--issue-this-as-one-bash-call) above: `registry pull` and each CLI-owned `node add new.flow <type>` follow `uip flow init … && cd /solution/<ProjectName>` in the same `Bash`. Standalone:
<!--skill-flavor:greenfield-registry-transition:end-->

<!--skill-flavor:greenfield-end-node-discovery:start-->
**Parallel `registry get`** — in the same T1 assistant message, emit one separate `Bash` per OOTB node type whose definition you'll inline in T2. **Always fetch `core.control.end`** — the host-seeded `new.flow` contains only the manual trigger (see Step 4):
<!--skill-flavor:greenfield-end-node-discovery:end-->

<!--skill-flavor:greenfield-registry-auth-note:start-->
> **Auth note**: Authentication is host-provided — your Studio Web session is injected on every `uip` call, so `registry pull` already returns OOTB **and** tenant connector/resource nodes; there is no login step. A 401/403 means the signed-in user lacks rights on the tenant or folder — report it, do not retry. **In-solution sibling projects** are listed with `uip solution resources list` — see below.
<!--skill-flavor:greenfield-registry-auth-note:end-->

<!--skill-flavor:greenfield-local-discovery:start-->
**In-solution discovery:**

```bash
uip solution resources list --kind Process --output json   # solutionResources = projects in the open solution; availableResources = deployed processes per folder
```

`solutionResources` lists the in-solution projects as `{key, name, kind: "process", type: "flow" | "api"}`; `availableResources` lists deployed processes per folder. `registry list|search|get --local` needs a local solution manifest and is unavailable in Studio Web. Resolve a sibling's node type and manifest through the tenant registry (`uip maestro flow registry search "<name>" --output json`, then `registry get`); if the sibling is not published yet and the search finds nothing, land a `core.logic.mock` and record it in **Open Questions**.
<!--skill-flavor:greenfield-local-discovery:end-->

<!--skill-flavor:greenfield-build-scaffold-assumptions:start-->
> **Treat the host-seeded `new.flow` as authoritative.** A fresh project's `new.flow` contains only the manual trigger (`manualTrigger1` / `core.trigger.manual` — not `start`) with empty `edges`, `definitions`, and `bindings`, and it may have no `layout` or `variables` block until `node add` or `flow format` creates one — so anchor every Edit on the text you actually `Read`, not on the `start` / `layout.nodes` examples below. Every other user-owned node — **including the End node** — is yours to add via `Edit` / `Write`. Any HTTP / connector / connector-trigger node you `node add`-ed in T1 is already in `nodes[]` and `definitions[]` but has empty `inputs.detail` (filled in T3) and is not wired yet; preserve its `bindings[]` / `inputs.detail`.
<!--skill-flavor:greenfield-build-scaffold-assumptions:end-->

<!--skill-flavor:greenfield-t2-read-source:start-->
1. **One `Read`** of `/solution/<ProjectName>/new.flow` — required before any Edit/Write because Step 2 produced the file and the T1 `node add` calls mutated it; anchor every Edit on the text this read returns.
<!--skill-flavor:greenfield-t2-read-source:end-->

<!--skill-flavor:greenfield-edit-target-file:start-->
Edit `new.flow` directly in `/solution/<ProjectName>/`. Do not hand-edit the `bindings_v2.json` that `node configure` writes into the same directory.
<!--skill-flavor:greenfield-edit-target-file:end-->

<!--skill-flavor:greenfield-t3-chain:start-->
```bash
uip maestro flow node configure new.flow "<httpNodeId>" --detail '<DETAIL_JSON>' --output json \
  && uip maestro flow validate new.flow --output json \
  && uip maestro flow format new.flow --output json
```
<!--skill-flavor:greenfield-t3-chain:end-->

<!--skill-flavor:greenfield-format-standalone:start-->
```bash
uip maestro flow format new.flow --output json
```
<!--skill-flavor:greenfield-format-standalone:end-->

<!--skill-flavor:greenfield-whats-next-dropdown:start-->
| Option | What it does |
| --- | --- |
| **Publish** | Publish the open solution with `uip solution publish --location "<key or name>"`. Read the destinations from `uip solution publish --help` (`PublishLocations`) and ask the user which one when more than one exists and none was named; the personal workspace auto-deploys. |
| **Debug** | Run the saved project with `uip flow debug` (two-token verb). Consent comes from the mandate, not from this menu — see the `flow debug` rule in [SKILL.md](../../SKILL.md). Selecting it here is the user asking for a run. |
| **Something else** | Last option. Accept free-form string input and act on it (e.g., "just leave it", "publish to folder X"). |
<!--skill-flavor:greenfield-whats-next-dropdown:end-->
