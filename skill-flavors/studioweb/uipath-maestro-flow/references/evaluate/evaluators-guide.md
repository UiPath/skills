<!--skill-flavor:sw-eval-evaluator-add-examples:start-->
```bash
# Deterministic — no model needed
uip maestro flow eval evaluator add exact-greeting \
  --type exact-match \
  --target-key "greeting" \
  --path /solution/<Project> --output json

# LLM-judge — model is effectively required
uip maestro flow eval evaluator add greeting-quality \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --description "Score greeting tone and completeness" \
  --path /solution/<Project> --output json
```
<!--skill-flavor:sw-eval-evaluator-add-examples:end-->

<!--skill-flavor:sw-eval-evaluator-json-intro:start-->
The CLI writes evaluator JSON files into the project's evaluator directory — in Studio Web `/solution/<Project>/evals/default/evaluators/` (or `/solution/<Project>/evals/evaluators/` when that folder already exists); a fresh project has no `evals/` folder and the CLI creates it on first use. Prefer `evaluator add` so the CLI mints the `id` and the `<name>-<suffix>.json` filename. If you must hand-write a file, generate its `id` with `node -e "console.log('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return (c==='x'?r:(r&3|8)).toString(16)}))"` — this shell has no `crypto` module and no `uuidgen`. Let `eval set add` write `evaluatorRefs` instead of hand-editing them.
<!--skill-flavor:sw-eval-evaluator-json-intro:end-->

<!--skill-flavor:sw-eval-custom-prompt-example:start-->
```bash
uip maestro flow eval evaluator add strict-match \
  --type llm-judge-output \
  --model gpt-4.1-2025-04-14 \
  --prompt 'Score 0-1 how closely {{ActualOutput}} matches {{ExpectedOutput}}. Return JSON {"score": N, "reason": "..."}.' \
  --path /solution/<Project> --output json
```
<!--skill-flavor:sw-eval-custom-prompt-example:end-->

<!--skill-flavor:sw-eval-evaluator-remove-examples:start-->
```bash
uip maestro flow eval evaluator remove greeting-quality \
  --path /solution/<Project> --output json
```

Removing an evaluator does NOT auto-clean `evaluatorRefs` arrays in eval sets that reference it. After removing, re-list eval sets and reconcile any stale refs:

```bash
uip maestro flow eval set list --path /solution/<Project> --output json
```
<!--skill-flavor:sw-eval-evaluator-remove-examples:end-->
