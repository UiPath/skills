<!--skill-flavor:graph-verify:start-->
Then run the whole rule with `uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'`, or with the `RunProject` host tool when that command is unavailable, passing one input object keyed by input-argument name. It evaluates the graph and returns every decision. **Check the result for every decision you authored, not only the last one.** A decision the engine skipped or answered wrongly still reads as a completed run. On a mismatch, read the run's trace to see which rules fired.
<!--skill-flavor:graph-verify:end-->
<!--skill-flavor:graph-anti-debug:start-->
- Reading only the last decision in the run result
<!--skill-flavor:graph-anti-debug:end-->
