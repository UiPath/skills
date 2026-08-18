# Inline Agent

*Behavior and worked examples. Exact signatures, fields, and defaults: [`inlineAgent()`](api.md#inlineagent-function).*

An inline agent is defined inside this Flow project and may be connected to
tenant context, callable tools, and human escalation resources.

Signature:
`inlineAgent({ model, systemPrompt, userPrompt, inputs?, returns?, source?, temperature?, maxTokenPerResponse?, modelMaxTokens?, maxIterations?, context?, tools?, escalation? })`.

```ts
.step('triage', inlineAgent({ model: 'gpt-5.4',
  systemPrompt: 'Return JSON with category.',
  userPrompt: 'Classify {{input.body}}', inputs: { body: input('body') },
  returns: { category: 'string' } }))
```

## Model and answer judgment

Select a model currently available to the tenant (`uip agent model list`) and
write prompts that make the requested decision and answer contract explicit.
Static checks can establish wiring and output shape, never the semantic quality
of the model's answer.

## Context grounding

Context signature:
`{ name, id, folderPath?, folderKey?, query?, retrievalMode?, resultCount?, threshold?, fileExtension? }`.

Resolve the index name and id together from the tenant registry. Local execution
has no semantic retrieval service, so an inline-agent answer is ungrounded even
when the resource wiring is present. Platform evidence must establish that the
intended index was used and that its retrieved knowledge influenced the answer.

## Tools

Tool signatures:

- `{ kind: 'builtin', tool: 'analyzefiles' | 'summarize' | 'batchtransform', ... }`
- `{ kind: 'connector', connector, operation, version?, object?, name? }`
- `{ kind: 'process' | 'agent' | 'api' | 'flow' | 'maestro', key, name, folderPath, inputs?, returns? }`
- `{ kind: 'ixp', projectId, name, description?, versionTag?, attachment? }`

A tool is invoked by the model, not by a control-flow edge. Local execution
skips tool resources, so it proves their wiring but not that the model called
them. A live test needs a tool-specific side effect or returned witness.

## Human escalation

Escalation signature:
`{ name, description?, app: { key, name, folderPath?, inputs?, outputs? }, recipients?, outcomes?, taskTitle?, priority?, labels? }`.

Whether and when to escalate is model judgment, and completion additionally
depends on a deployed app and a human. Local execution proves only resource and
contract wiring; live evidence must show the task, reviewer outcome, and resumed
agent behavior.

## Live-evidence limit

Headless local live mode calls a real model but substitutes a reachable model
and remains ungrounded; it has no tenant tool loop or human escalation. Treat it
as evidence that a real prompt produced the declared shape. Product debug is
the evidence for the actual configured model and cloud resources.

Compile emits the node plus a stable `<source>/agent.json` sidecar. Prompt variables
use `{{input.<name>}}`; `inputs` binds those names to flow references and `returns`
declares what the agent hands back.
