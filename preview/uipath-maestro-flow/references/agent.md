# Agent

*Behavior and worked examples. Exact signatures, fields, and defaults: [`agent()`](api.md#agent-function).*

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

## Task-created in-solution coded agent

When the request says to create a coded agent inside the same solution, do not
search for a published release and do not substitute an inline low-code agent.
The shortest complete path is:

1. Scaffold the solution and Flow project.
2. Scaffold and implement the coded agent as a sibling directory. Run one local
   input through it; an evaluation suite is optional unless the request asks for
   one.
3. Register the sibling with `uip solution projects add`.
4. Read the generated resource file, then author the Flow with `agent({
   location: 'in-solution', ... })`.
5. Compile directly into the nested Flow project, validate, refresh resources,
   and debug the Flow.

```bash
uip solution init <SolutionName> --output json
( cd <SolutionName> && uip maestro flow init <FlowName> --output json )

mkdir <SolutionName>/<AgentProject>
( cd <SolutionName>/<AgentProject> && \
  uv venv --python 3.13 && . .venv/bin/activate && \
  uv pip install <framework-package> && \
  uip codedagent setup --force --output json && \
  uip codedagent new <AgentName> )
# Implement the generated project, then from that directory:
#   . .venv/bin/activate && uv sync && uip codedagent init
#   uip codedagent run <entry-point> '<one representative JSON input>'

( cd <SolutionName> && \
  uip solution projects add <AgentProject> <SolutionName>.uipx --output json )
```

Read both identifiers from
`<SolutionName>/resources/solution_folder/process/agent/<AgentProject>.json`:

- `resource.key` → `key`
- `resource.projectKey` → `projectId`

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
