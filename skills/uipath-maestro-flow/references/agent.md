# Agent

*Exact signatures, fields, and defaults: `agent()`.*

Start a coded or low-code agent and wait for its output. The agent may be published in Orchestrator or registered as a sibling project in this solution; this references rather than creates it. Scaffold and register a task-created sibling before calling it. Verify resource identity and answer quality live. `.onError(...)` is supported.

Signature: `agent({ key, name, folderPath?, location?, projectId?, inputs, returns?, flavour? })`

```ts
.step('count', agent({
  key: 'BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D', name: 'CountLetters',
  folderPath: 'Shared', inputs: { inputString: input('inputString') },
  returns: { count: 'integer' }, flavour: 'coded'
}))
```

See [Orchestrator Processes](or-processes.md) and use the `Agent` process type to locate an agent and determine its contract.
## At a glance

Start a published coded/low-code agent, or a sibling agent registered in this
solution, and wait for its answer.

```ts
.step('count', agent({ key: releaseKey, name: 'CountLetters',
  folderPath: 'Shared', inputs: { word: input('word') },
  returns: { count: 'integer' }, flavour: 'coded' }))
```

## General

- *flavour* is either `"coded"` or `"lowcode"`; it affects presentation only, not the runtime contract. `uip or processes get` returns no equivalent field.

## Reuse a published agent, or create one in the solution

When a request names a possibly existing agent, search first:

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
uip maestro flow registry get "uipath.core.agent.<key>" --output json
```

Use `registry get` to read argument names and return shape from `inputDefinition.properties` and `outputDefinition`.

When asked to CREATE a coded agent in this solution, scaffold it as a sibling project; do not substitute an inline low-code agent. Do not duplicate an already published agent or bind a pre-existing one when asked to build it. Read the request to decide whether to create or bind; do not guess from what the registry happens to hold.

**Never invent `key` or `projectId`.** Tooling mints both; read them back. If no source yields one, stop: `check` and `validate` accept a well-formed GUID that resolves to nothing on the tenant, so a fabricated key fails at run time, not author time.

## Task-created in-solution coded agent

<!--skill-flavor:agent-scaffold:start-->
1. Scaffold the solution and Flow project.
2. Scaffold and implement the coded agent as a sibling directory.
3. Register the sibling with `uip solution projects add`.
4. Read both identifiers back, then author the Flow with `agent({ location: 'in-solution', ... })`.
5. Compile into the nested Flow project, validate, refresh resources, and debug the Flow ([ask first](operate.md#debug--a-real-end-to-end-run)).

Run:

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

**Install the framework package BEFORE `new`.** `new` defaults to `--type auto` and selects its template from the installed framework package; without one it creates a coded FUNCTION. Verify that `<framework>.json` is beside `main.py` (`langgraph.json` for `uipath-langchain`). If `uipath.json` instead has a `functions` map and no `<framework>.json`, install the package, delete the generated files, and re-run `new`.

Scaffold from INSIDE the agent directory. Do not run `codedagent new` from the solution root: it writes `main.py`, `pyproject.toml`, and `<framework>.json` there and requires manual cleanup.

Implement the project, then from that directory run:

```bash
uv sync
uip codedagent init
uip codedagent review . --output json
```

Run `uv sync` before `init`: `uip codedagent init` imports the entry-point graph and fails when declared dependencies are absent; a failed `init` leaves `uipath.json` scaffolded without its entry-point map. **Do not run `uip codedagent run` on this path.** It executes the graph and needs `UIPATH_ACCESS_TOKEN` and access to the LLM gateway; where either is absent, failures at the platform client, including intervening import or virtualenv errors, are environment, not defects in the project — do not chase them. Use `uip codedagent review` as the offline check; it does not run the model.

Register the sibling, refresh, then read both identifiers back. Run:

```bash
( cd <SolutionName> && \
  uip solution projects add <AgentProject> <SolutionName>.uipx --output json )
uip solution resources refresh --solution-folder <SolutionName> --output json
uip maestro flow registry list --local --output json
```

Run `registry list --local` from the Flow project directory; it is authoritative for the minted key. The generated resource file carries the same pair: `resource.key` → `key`, and `resource.projectKey` → `projectId`.

Find that file; do not assume its path. `uip solution projects add` reads the project type from the manifest, and a `uipath.json` without `ProjectType` falls back to `Function` whenever it has a `functions` map, including an empty scaffolded map. The resource may therefore be under `process/function/<AgentProject>.json` rather than `process/agent/`. Glob for it:

```bash
ls <SolutionName>/resources/solution_folder/process/*/<AgentProject>.json
```

`uip solution projects list --output json` reports the manifest-resolved type. `Type: Function` for a coded agent is this fallback, not a wiring error; do not re-add the project or hand-edit `uipath.json`—read the identifiers and wire the Flow.
<!--skill-flavor:agent-scaffold:end-->

```ts
.step('analyze', agent({
  key: localResourceKey,
  name: '<AgentProject>',
  location: 'in-solution',
  projectId: localProjectKey,
  inputs: { sentence: input('sentence') },
  returns: { result: 'integer' },
  flavour: 'coded',
}))
```

An in-solution agent intentionally has no `folderPath`. Its generated binding
uses the bare local resource key, and its definition carries the sibling
project id. The SDK checker rejects a missing project id or a published agent
with a missing folder, so the two resource forms cannot silently collapse into
one another.

## Evidence boundary

A green live run proves only that a real job received inputs and returned the declared shape—not that the model's answer is correct. Preserve the job identity, input/output witnesses, and a scenario-specific semantic assertion; offline seeds should also rule out a hard-coded answer.