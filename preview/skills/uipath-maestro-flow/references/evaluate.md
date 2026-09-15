# Flow Evaluation Assets

Evaluators, eval sets, and data points are project assets managed by
`uip maestro flow eval`; defining an `inlineAgent(...)` node does not create
them. Use this workflow when the request explicitly asks for evaluation assets.

Probe the installed CLI once, then let it write the JSON formats and generated
file references:

```bash
uip maestro flow eval --help --output json

uip maestro flow eval evaluator add response-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score the response against the expected result" \
  --target-key '*' \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval evaluator list \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval set add "Smoke Tests" \
  --entry-point start \
  --path ./MySolution/MyFlow --output json

uip maestro flow eval add "basic case" \
  --set "Smoke Tests" \
  --inputs '{"request":"hello"}' \
  --expected '{"reply":"hello"}' \
  --path ./MySolution/MyFlow --output json
```

`llm-judge-output` produces
`evaluatorTypeId: "uipath-llm-judge-output-semantic-similarity"`. Always pin a
model for an LLM judge. For deterministic values, prefer `exact-match`,
`json-similarity`, or `contains`.

Use the generated evaluator id or filename when explicitly passing
`--evaluators`; a display name alone is not a stable reference. Omitting the
flag on `eval set add` links all evaluators that currently exist. The data-point
input keys must match declared Flow inputs.

Local add/list/remove commands edit project files and do not require login.
Starting an eval run requires a matching solution in Studio Web. Do not upload
or overwrite a solution unless the user explicitly authorizes that mutation.

After authoring, list the evaluator and eval set and inspect the generated JSON.
Confirm the evaluator has the requested `evaluatorTypeId`, the set contains its
generated file reference, and the selected entry point matches the Flow.
