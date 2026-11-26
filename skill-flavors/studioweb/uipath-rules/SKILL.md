<!--skill-flavor:lifecycle-rules:start-->
6. **Create with `uip rules init`, which the host serves, or the `CreateProjects` host tool; after every edit, `format`, `refresh` then `validate`.** Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the seeded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and a run returns what the reviewed design expects, from every decision and not only the last.** Run it with `uip rules debug`, which the host serves, or the `RunProject` host tool. Stop after 3 fix rounds and show the user the tables and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
<!--skill-flavor:scaffold:start-->
```bash
uip rules init <RULE_NAME>
```

The host serves this command: it creates a BusinessRules project in the open solution and prints text, not the CLI's JSON envelope. Pass the name alone; template flags, `--force` and `--skip-solution-registration` have no effect. The `CreateProjects` host tool, project type BusinessRules, creates the same project. The rule is the one `.dmn` file in `/solution/<RULE_NAME>/`, `Business rule.dmn`; never create or rename to another `.dmn`. Treat whatever table the seeded `.dmn` holds as a placeholder; step 3 replaces it.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
```bash
uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'
```

The host serves this command: it runs the project `<RULE_NAME>` saved in the open solution and prints the status, trace id, run logs and execution trace as text, not the CLI's JSON envelope. Pass the project name, never a path. `--inputs` takes one inline JSON object keyed by input-argument name; `@<FILE>` is not supported, and without `--inputs` the run uses the arguments saved in the designer. When the command reports it is unavailable, run the project with the `RunProject` host tool and the same input object. Either way the whole rule is evaluated, so compare every decision's outputs with the expected values. On a mismatch, read the run's trace to see which rules fired.
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
