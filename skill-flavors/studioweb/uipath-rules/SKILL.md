<!--skill-flavor:lifecycle-rules:start-->
6. **Scaffold a new project with `init`; after every edit, `format`, `refresh` then `validate`.** An existing project needs no `init`: edit its `.dmn` and run `refresh`. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the scaffolded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and `debug` returns what the reviewed design expects, from every decision and not only the last.** On a wrong output, read the trace with `uip traces spans get <TRACE_ID>`. Stop after 3 fix rounds and show the user the tables and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
<!--skill-flavor:scaffold:start-->
```bash
uip rules init <RULE_NAME>
```

Run `init` from `/solution`, the Studio Web solution the user has open; never create another. Studio Web creates the project in the open solution at `/solution/<RULE_NAME>/`. The intercepted command prints plain text; `--output json` is ignored. The rule is the one `.dmn` file in the project folder. Treat whatever table the scaffolded `.dmn` holds as a placeholder; step 3 replaces it. The **table** is the placeholder — not the root element, and not its `extensionElements`, which already carry the right authoring surface.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
```bash
uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'
```

`<RULE_NAME>` is a project name in the open solution, not a path. Debug runs the rule saved in the open solution, so there is no pack or upload step. Always pass `--inputs`: the input values as inline JSON, one object keyed by input-argument name; `@file` is not supported. The output is plain text, not JSON: the status, `Trace ID: <id>` when one was found, the run logs and the execution trace. Exit 1 means `Faulted` or `Failed`. Compare every decision's outputs with the expected values. On a mismatch, read the trace:

```bash
uip traces spans get <TRACE_ID> --output json
```

`<TRACE_ID>` is the `Trace ID` the output prints. The trace shows which rules fired. Without a `Trace ID`, compare the inputs against each row by hand.
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
