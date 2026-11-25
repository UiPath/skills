<!--skill-flavor:lifecycle-rules:start-->
6. **Create with the `CreateProjects` host tool; after every edit, `format`, `refresh` then `validate`.** Never run `uip rules init` or `uip rules debug` here: `init` creates a folder that never becomes a Studio Web project, and `debug` is unavailable. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; keep the seeded `.dmn` file and its root element.
7. **A rule is done when `validate` passes and the `RunProject` host tool returns what the reviewed design expects, from every decision and not only the last.** Stop after 3 fix rounds and show the user the tables and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
<!--skill-flavor:scaffold:start-->
Create the project in the open solution with the `CreateProjects` host tool, project type BusinessRules. The rule is the one `.dmn` file in `/solution/<RULE_NAME>/`. Treat whatever table the seeded `.dmn` holds as a placeholder; step 3 replaces it.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
Run the project with the `RunProject` host tool, passing one input object keyed by input-argument name. It evaluates the whole rule, so compare every decision's outputs with the expected values. On a mismatch, read the run's trace to see which rules fired.
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
