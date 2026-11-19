# Agent

*Exact signatures, fields, and defaults: `agent()`.*

Start a coded or low-code agent and wait for its output. It may be published in Orchestrator or registered as a sibling project in this solution.

Signature: `agent({ key?, name, folderPath?, location?, projectId?, inputs, returns?, flavour? })`

For a published process, leave `key` and `returns` out: `check` prints the `registry prepare --kind Process` command that records them, and `compile` fills both in ([Orchestrator Processes](or-processes.md#getting-the-inputs-and-outputs)). An in-solution sibling still takes `key`.

```ts
.step('count', agent({
  name: 'CountLetters', folderPath: 'Shared',
  inputs: { inputString: input('inputString') },
  flavour: 'coded'
}))
```

See [Orchestrator Processes](or-processes.md) and use the `Agent` process type to locate an agent process and determine its contract.

## At a glance

`agent()` references a published or in-solution sibling agent; it does not create one. For a task-created sibling, scaffold and register it before calling it. Verify resource identity and answer quality live. `.onError(...)` is supported.

## General

- *flavour* is either "coded" or "lowcode"; it affects presentation only, not the runtime contract. `uip or processes get` returns no equivalent field.
- `.onError(...)` is supported on agent steps.

## Reuse a published agent, or create one in the solution

Two shapes; the request decides which. When the request names an agent that may already exist, look for it first:

```bash
uip maestro flow registry search "uipath.core.agent" --output json
uip maestro flow registry get "uipath.core.agent.<key>" --output json
```

Registry reads are cached for 30 minutes. If the agent is missing or redeployed with a new schema, run `uip maestro flow registry pull --force` once, then search again.

To learn a published agent's argument names and return shape, write `name` and
`folderPath`, leave `key` and `returns` out, and run the
`uip maestro registry prepare --kind Process` command `check` prints. It records
the key and both schemas; see
[Orchestrator Processes](or-processes.md#getting-the-inputs-and-outputs).
`uip maestro registry` (the SDK's prepare) and `uip maestro flow registry` (node
manifests, above) are two command groups; both exist.
If `prepare` prints `not recorded` for a side, read it from `registry get`
instead: `inputDefinition.properties` and `outputDefinition`.

When asked to CREATE a coded agent in this solution, scaffold it as a sibling project; do not substitute an inline low-code agent. Creating one the tenant already publishes is duplication, and binding a pre-existing one when the request said to build it is a different task, so read the request; do not guess from what the registry happens to hold.

**Never invent `key` or `projectId`.** Tooling mints both; read them back. If no source below yields one, stop on that field rather than provide a plausible GUID: `check` and `validate` accept a well-formed GUID that resolves to nothing on the tenant, so a fabricated key fails at run time, not author time.

## Task-created in-solution coded agent

<!--skill-flavor:agent-scaffold:start-->
1. Scaffold the solution and Flow project.
2. Scaffold and implement the coded agent as a sibling directory.
3. Register the sibling with `uip solution projects add`.
4. Read both identifiers back, then author the Flow with `agent({ location: 'in-solution', ... })`.
5. Compile into the nested Flow project, validate, refresh resources, and debug the Flow ([ask first](operate.md#debug--a-real-end-to-end-run)).

```bash
uip solution init <SolutionName> --output json
( cd <SolutionName> && uip maestro flow init <FlowName> --output json )

mkdir -p <SolutionName>/<AgentProject>
( cd <SolutionName>/<AgentProject> \
  && uv venv --python 3.13 \
  && uv pip install <framework-package> \
  && uip codedagent setup --force --output json \
  && uip codedagent new <AgentName> )
```

**Install the framework package BEFORE `new`.** `new` defaults to `--type auto` and selects the template from the active venv; without an installed framework it scaffolds a coded FUNCTION.

Verify the scaffold before continuing: `<framework>.json` beside `main.py` (`langgraph.json` for `uipath-langchain`) indicates the agent template. `uipath.json` with a `functions` map and no `<framework>.json` is the function fallback; install the package, delete the generated files, and re-run `new`.

Scaffold from INSIDE the agent directory, with its framework venv already present. From the solution root (the directory containing `.uipx`), `uip codedagent new <AgentName>` creates `<AgentName>/`; elsewhere it scaffolds in place.

Implement the project, then run these commands from that directory:

```bash
uv sync
uip codedagent init
uip codedagent review . --output json
```

Run `uv sync` before `init`: `uip codedagent init` imports the entry-point graph and fails when declared dependencies are absent; a failed `init` leaves `uipath.json` scaffolded without its entry-point map.

**`uip codedagent run` is not part of this path.** It executes the graph and requires `UIPATH_ACCESS_TOKEN` plus access to the LLM gateway. If either is absent, `run` fails at the platform client; the import and virtualenv errors it emits on the way there are environmental, not project defects; do not chase them. `uip codedagent review` is the offline check and does not run the model.

Register the sibling, refresh, and read both identifiers back:

```bash
( cd <SolutionName> && \
  uip solution projects add <AgentProject> <SolutionName>.uipx --output json )
uip solution resources refresh --solution-folder <SolutionName> --output json
uip maestro flow registry list --local --output json
```

Run `registry list --local` from the Flow project directory; it is the authoritative source for the minted key. The generated resource file carries the same pair:

- `resource.key` → `key`
- `resource.projectKey` → `projectId`

Find that file; do not assume its path. `uip solution projects add` reads the project type from the manifest. A `uipath.json` without `ProjectType` falls back to `Function` when it has a `functions` map, including an empty scaffolded map, so the resource may be under `process/function/<AgentProject>.json` rather than `process/agent/`. Glob for it instead of hard-coding either:

```bash
ls <SolutionName>/resources/solution_folder/process/*/<AgentProject>.json
```

`uip solution projects list --output json` reports the type resolved from the manifest. `Type: Function` on a coded agent is this fallback, not a wiring error; re-adding the project or hand-editing `uipath.json` will not change it. Read the identifiers and wire the Flow instead.
<!--skill-flavor:agent-scaffold:end-->

```ts
.step('analyze', agent({
  key: localResourceKey,
  name: '<AgentProject>', location: 'in-solution',
  projectId: localProjectKey,
  inputs: { sentence: input('sentence') },
  returns: { result: 'integer' }, flavour: 'coded',
}))
```

An in-solution agent has no `folderPath`: its generated binding uses the bare local resource key and its definition carries the sibling project id. The SDK checker rejects a missing project id or a published agent with a missing folder, so resource forms cannot silently collapse.

## Name an in-solution sibling by project

Needs `@uipath/maestro-builder-sdk` 6.108.0 or later. Any of the five
process builders can then name a sibling of the solution by its project name
instead of copying the two ids:

```ts
.step('analyze', agent({
  location: 'in-solution',
  project: '<AgentProject>',
  inputs: { sentence: input('sentence') },
  flavour: 'coded',
}))
```

- `compile`, `check` and `flow merge` find the sibling's resource file under
  `resources/solution_folder/process/` themselves, and write its `key` and
  `projectId` into the `.flow`. Studio Web's Run node gets its `projectId`
  without you setting it. Run them from inside the solution: they look for
  the nearest folder at or above the flow that holds the `.uipx`, and refuse
  `project` without one (`IN_SOLUTION_NO_SOLUTION`).
- In a decompiled flow, the step keeps the `key` and `projectId` decompile
  wrote. Switching it to `project` is optional; both forms merge back.
- When the step declares no `returns`, they are read from the sibling's
  `entry-points.json` output schema. An RPA project that was never built, or
  an API workflow whose entry point has `output: null`, has none there:
  declare `returns` yourself, as before.
- The sibling still needs its resource file, made by the register step of
  the recipe above.
- They refuse a name the solution does not have
  (`IN_SOLUTION_PROJECT_NOT_FOUND`, with the nearest name) and the wrong
  builder for the sibling's type (`IN_SOLUTION_WRONG_BUILDER`, which names the
  right call; for example `publishedFunction()` on a coded agent filed under
  `process/function/`).
- An older SDK ignores `project` and refuses the step for its missing key
  (`AGENT_NO_KEY`, `RPA_NO_KEY`, …). Then use the id recipe above.

## Argument types (`inputSchema`)

Compile declares each passed input with a type taken from its value: a number,
boolean, array or object literal by its shape, and anything else (an expression,
`input()`, `out()`) as `string`. When the process types an argument differently
(an object filled from an expression, or an argument the step does not pass),
write the argument JSON Schema as `inputSchema`. Compile writes it verbatim as
the definition's `inputDefinition`:

```ts
inputs: { payload: input('request') },
inputSchema: { type: 'object', properties: { payload: { type: 'object' } } },
```

A decompiled step carries `inputSchema` when its saved definition holds more
than compile would infer; keep it. `check` reports an object or array literal
whose declared type does not allow it (`PROCESS_INPUT_SCHEMA_TYPE`; `flow
validate` reports the same value as `TYPE_MISMATCH`), and an `inputSchema` that
is not a plain object (`PROCESS_INPUT_SCHEMA_INVALID`). Needs a builder SDK
release that includes UiPath/builder-sdk#2198.

## Evidence boundary

A green live run proves only that a real job received inputs and returned the declared shape, not that the model answer is correct. Preserve the job identity, input/output witnesses, and a scenario-specific semantic assertion; offline seeds should also rule out a hard-coded answer.
