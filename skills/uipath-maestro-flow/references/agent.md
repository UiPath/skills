# Agent

*Exact signatures, fields, and defaults: `agent()`.*

Start a coded or low-code agent and wait for its output. The resource may be
published in Orchestrator or registered as a sibling project in this solution.

Signature: `agent({ key, name, folderPath?, location?, projectId?, inputs, returns?, flavour? })`

```ts
.step('count', 
  agent({ 
    key: 'BAADF00D-BAAD-F00D-BAAD-F00DBAADF00D',
    name: 'CountLetters',
    folderPath: 'Shared',
    inputs: { inputString: input('inputString') },
    returns: { count: 'integer' },
    flavour: 'coded'
  }))
```

See [Orchestrator Processes](or-processes.md) and use the `Agent` process type to locate an agent process and determine its contract.

## General

- *flavour* can be either "coded" or "lowcode". It does not affect the runtime contract, only presentation. There is no equivalent field returned from `uip or processes get`.

`.onError(...)` is supported on agent steps.

## Reuse a published agent, or create one in the solution

Two shapes, and the request decides which.
When the request names an agent that may already exist, look for it first.

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
uip maestro flow registry get "uipath.core.agent.<key>" --output json
```

`registry get` is also how you learn the agent's own argument names and its
return shape — `inputDefinition.properties` and `outputDefinition`.

When the request asks for a coded agent to be CREATED in this solution,
scaffold it as a sibling project instead; do not substitute an inline low-code
agent.
Creating one the tenant already publishes is duplication, and binding a
pre-existing one when the request said to build it is a different task — so
read the request, do not guess from what the registry happens to hold.

**Never invent `key` or `projectId`.**
Both are minted by the tooling and read back from it.
If no source below yields one, stop on that field rather than supply a
plausible GUID: `check` and `validate` both accept a well-formed GUID that
resolves to nothing on the tenant, so a fabricated key fails at run time, not
at author time.

## Task-created in-solution coded agent

1. Scaffold the solution and Flow project.
2. Scaffold and implement the coded agent as a sibling directory.
3. Register the sibling with `uip solution projects add`.
4. Read the two identifiers back, then author the Flow with `agent({
   location: 'in-solution', ... })`.
5. Compile into the nested Flow project, validate, refresh resources, and
   debug the Flow.

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

**Install the framework package BEFORE `new`.**
`new` defaults to `--type auto`, which picks the template from whichever
framework package is installed in the active venv — so with none installed it
scaffolds a coded FUNCTION instead, and nothing says so at the time.

Verify the scaffold before going further: a `<framework>.json` beside `main.py`
(`langgraph.json` for `uipath-langchain`) means the agent template was used.
A `uipath.json` carrying a `functions` map and no `<framework>.json` is the
function fallback — install the package, delete the generated files, and re-run
`new`.

Scaffold from INSIDE the agent directory.
Run `codedagent new` from the solution root and it writes `main.py`,
`pyproject.toml` and `<framework>.json` into the solution root, which then has
to be cleaned up by hand.

Implement the project, then from that directory:

```bash
uv sync
uip codedagent init
uip codedagent review . --output json
```

`uv sync` comes before `init` because `uip codedagent init` imports the
entry-point graph, so it fails on any declared dependency the venv does not
have yet — and a failed `init` leaves `uipath.json` scaffolded but with its
entry-point map never filled in.

**`uip codedagent run` is not part of this path.**
It executes the graph, which needs `UIPATH_ACCESS_TOKEN` and reach to the LLM
gateway.
Where either is absent it fails at the platform client, and the import and
virtualenv errors it emits on the way there are environment, not defects in the
project — do not chase them.
`uip codedagent review` is the offline rung: it checks the project without
running the model.

Register the sibling, refresh, then read both identifiers back:

```bash
( cd <SolutionName> && \
  uip solution projects add <AgentProject> <SolutionName>.uipx --output json )
uip solution resources refresh --solution-folder <SolutionName> --output json
uip maestro flow registry list --local --output json
```

`registry list --local`, run from the Flow project directory, is the
authoritative source for the minted key.
The generated resource file carries the same pair:

- `resource.key` → `key`
- `resource.projectKey` → `projectId`

**Find that file; do not assume its path.**
`uip solution projects add` reads the project type out of the manifest, and a
`uipath.json` with no `ProjectType` falls back to `Function` whenever it
carries a `functions` map — including an empty one, which a scaffolded project
has. So the resource can land under `process/function/<AgentProject>.json`
rather than `process/agent/`. Glob for it instead of hard-coding either:

```bash
ls <SolutionName>/resources/solution_folder/process/*/<AgentProject>.json
```

`uip solution projects list --output json` reports the type the manifest
resolved to.
`Type: Function` on a coded agent is that fallback, not a mistake in your
wiring: re-adding the project or hand-editing `uipath.json` will not change it,
so read the identifiers and wire the Flow rather than trying to correct it
first.

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

A green live run proves that a real job received inputs and returned the
declared shape. It does not prove the model's answer is correct. Preserve the
job identity, input/output witnesses, and a scenario-specific semantic
assertion; offline seeds should also rule out a hard-coded answer.
