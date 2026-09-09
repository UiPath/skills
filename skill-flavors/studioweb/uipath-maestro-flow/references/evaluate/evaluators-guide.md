<!--skill-flavor:sw-eval-evaluator-add-examples:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-evaluator-add-examples:end-->

<!--skill-flavor:sw-eval-evaluator-add-examples-2:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-evaluator-add-examples-2:end-->

<!--skill-flavor:sw-eval-evaluator-json-intro:start-->
The CLI writes evaluator JSON files into the project's evaluator directory — in Studio Web `/solution/<Project>/evals/default/evaluators/` (or `/solution/<Project>/evals/evaluators/` when that folder already exists); a fresh project has no `evals/` folder and the CLI creates it on first use. Prefer `evaluator add` so the CLI mints the `id` and the `<name>-<suffix>.json` filename. If you must hand-write a file, generate its `id` with `node -e "console.log('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return (c==='x'?r:(r&3|8)).toString(16)}))"` — this shell has no `crypto` module and no `uuidgen`. Let `eval set add` write `evaluatorRefs` instead of hand-editing them.
<!--skill-flavor:sw-eval-evaluator-json-intro:end-->

<!--skill-flavor:sw-eval-custom-prompt-example:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-custom-prompt-example:end-->

<!--skill-flavor:sw-eval-evaluator-remove-examples:start-->
  --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-evaluator-remove-examples:end-->

<!--skill-flavor:sw-eval-evaluator-remove-examples-2:start-->
uip maestro flow eval set list --path /solution/<Project> --output json
<!--skill-flavor:sw-eval-evaluator-remove-examples-2:end-->
