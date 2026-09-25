# Inline Agent

*Exact signatures, fields, and defaults: `inlineAgent()`.*

An inline agent is defined inside this Flow project and may be connected to
tenant context, callable tools, and human escalation resources.

Signature:
`inlineAgent({ model, systemPrompt, userPrompt, inputs?, returns?, source?, temperature?, maxTokenPerResponse?, modelMaxTokens?, maxIterations?, mode?, guardrails?, context?, tools?, escalation? })`.

```ts
.step('triage', inlineAgent({ model: 'gpt-5.4',
  systemPrompt: 'Return a result conforming to the output schema. category: billing | technical | account.',
  userPrompt: 'Classify {{input.body}}', inputs: { body: input('body') },
  returns: { category: 'string' } }))
```

## Model and answer judgment

Select a model currently available to the tenant (`uip agent model list`) and
write prompts that make the requested decision and answer contract explicit.
Static checks can establish wiring and output shape, never the semantic quality
of the model's answer.

`returns` is the answer contract: the agent runtime returns those fields as a
typed object, so describe what each field holds ("Return a result conforming to
the output schema. `<field>`: `<how to fill it>`.") and never ask for JSON text,
which makes the model pack its whole answer into one string field.

## Context grounding

Context signature:
`{ name, id, folderPath?, folderKey?, query?, retrievalMode?, resultCount?, threshold?, fileExtension? }`.

Resolve the index name and id together from the tenant, with ONE of the two commands below — `uip solution resources list` when you know the name, the `uip context-grounding` bridge when you are discovering what exists.
Neither is `uip maestro flow registry`, which serves node manifests, nor `uip maestro registry`, which is the connector library: a registry search for an index name answers nothing and the near-identical spellings make that look like a missing index.
Listing Orchestrator folders to hunt for it is slower still — a tenant has hundreds.

```bash
uip solution resources list --kind Index --source remote --search "<index-name>" --output json
```

Local execution has no semantic retrieval service, so an inline-agent answer is ungrounded even when the resource wiring is present.
Platform evidence must establish that the intended index was used and that its retrieved knowledge influenced the answer.

The `uip context-grounding` bridge runs in the project's Python environment.
Activate the existing environment and run setup once before list/search; setup
is the command itself, not a `setup --help` probe:

```bash
source .venv/bin/activate
uip context-grounding setup
uip context-grounding list --folder-path "<folder-path>" --format json
uip context-grounding search \
  --index-name "<index-name>" --query "<one bounded evidence query>" \
  --folder-path "<folder-path>" --limit 5 --format json
```

Use `--folder-key` instead of `--folder-path` when that is the known identity.
The delegated command uses `--format json`; it does not use the outer CLI's
`--output json` spelling. One search that answers the stated grounding claim is
enough; do not repeat paraphrases solely for confidence.

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

## Guardrails and harness mode

`guardrails` is Agent Builder's own array, carried on the node and in the
sidecar. Each rail is `$guardrailType: 'custom'` (with `rules`) or
`'builtInValidator'` (with `validatorType` + `validatorParameters`), plus
`id`, `name`, `selector: { scopes: ['Agent'|'Llm'|'Tool'] }`, an `action`
(`block` with a reason, `filter` over fields, or `log` with a severity), and
`enabledForEvals`. Custom rules are `$ruleType: 'word' | 'number' | 'boolean'`
over a field selector, or `'always'`. A rail with no scopes or an empty rules
array can never fire — `check` rejects both.

`mode: 'standard' | 'advanced'` picks the harness; naming it selects the
node's 1.3 definition (omitting it keeps 1.2 byte-identically) and lands on
the sidecar's `settings.mode`. Guardrail/harness behavior is runtime-side:
offline rungs prove the emitted shape only.
