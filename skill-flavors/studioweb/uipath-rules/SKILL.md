<!--skill-flavor:lifecycle-rules:start-->
6. **Scaffold a new project with `uip rules init`; after every edit, `format`, `refresh` then `validate`.** An existing project needs no `init`: edit its `.dmn` and run `refresh`. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the seeded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and `uip rules debug` returns what the reviewed design expects, from every decision and not only the last.** On a wrong output, read the trace with `uip traces spans get <TRACE_ID>`. Stop after 3 fix rounds and show the user the tables and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
<!--skill-flavor:scaffold:start-->
```bash
uip rules init <RULE_NAME>
```

Run `init` from `/solution`, the Studio Web solution the user has open; never create another. Studio Web creates the project in it at `/solution/<RULE_NAME>/`. The intercepted command prints plain text; `--output json` is ignored. The rule is `Business rule.dmn` in that folder; never create or rename to another `.dmn`. Treat whatever table the seeded `.dmn` holds as a placeholder; step 3 replaces it.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
```bash
uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'
```

Evaluates the rule saved in the open solution. Pass the project name, never a path. Always pass `--inputs`, one inline JSON object keyed by input-argument name; `@<FILE>` is not supported, and without `--inputs` the run uses the arguments saved in the designer. The reply is plain text: the status, the `Trace ID`, the run logs and the execution trace. Compare every decision's outputs with the expected values. On a mismatch, read the trace:

```bash
uip traces spans get <TRACE_ID> --output json
```

`<TRACE_ID>` is the `Trace ID` the reply prints. The trace shows which rules fired. When the reply prints none, compare the inputs against each row by hand.
<!--skill-flavor:verify:end-->
<!--skill-flavor:deployed-rules:start-->
```bash
uip rules list --folder-path <FOLDER_PATH> --output json
uip rules get <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules versions <RULE_NAME> --folder-path <FOLDER_PATH> --output json
```

Each command takes `--folder-path` or `--folder-key`, never both. `uip rules describe` is not available in Studio Web, so a deployed rule's inputs and outputs cannot be read here.

A deployed rule is held by the Business Rules service, or still by Orchestrator when it was deployed before rules moved there; each row's `Source` (`BusinessRules` or `Orchestrator`) says which. `get` and `versions` find a rule in either. `list` shows the service's rules in the folder, or Orchestrator's when the service holds none there. When it leaves Orchestrator's rules out, it says so on stderr: read those by name with `get`.
<!--skill-flavor:deployed-rules:end-->
