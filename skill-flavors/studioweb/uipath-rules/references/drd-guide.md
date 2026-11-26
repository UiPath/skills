<!--skill-flavor:graph-verify:start-->
Then run the whole rule:

```bash
uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'
```

`debug` names no decision, so the engine evaluates the graph and returns them all. **Check the output for every decision you authored, not only the last one.** A decision the engine skipped or answered wrongly is a passing run as far as the exit code is concerned.
<!--skill-flavor:graph-verify:end-->
