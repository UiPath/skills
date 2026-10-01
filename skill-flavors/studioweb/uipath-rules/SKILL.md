<!--skill-flavor:lifecycle-rules:start-->
6. **Create with the `CreateProjects` host tool; after every edit, `refresh` then `validate`.** Never run `uip rules init` or `uip rules debug` here: `init` creates a folder that never becomes a Studio Web project, and `debug` is unavailable. Fix what `validate` reports. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`; edit the seeded `.dmn` in place, keeping its root element.
7. **A rule is done when `validate` passes and the `RunProject` host tool returns what the reviewed table expects.** Stop after 3 fix rounds and show the user the table and the failing inputs.
<!--skill-flavor:lifecycle-rules:end-->
<!--skill-flavor:scaffold:start-->
Create the project in the open solution with the `CreateProjects` host tool, project type BusinessRules. The rule is the one `.dmn` file in `/solution/<RULE_NAME>/`.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
Run the project with the `RunProject` host tool, passing one input object keyed by input-argument name, and compare the decision outputs with the expected values. On a mismatch, read the run's trace to see which rules fired.
<!--skill-flavor:verify:end-->
<!--skill-flavor:deployed-rules:start-->
```bash
uip rules list --folder-path <FOLDER_PATH> --output json
uip rules get <RULE_NAME> --folder-path <FOLDER_PATH> --output json
uip rules versions <RULE_NAME> --folder-path <FOLDER_PATH> --output json
```

Each command takes `--folder-path` or `--folder-key`, never both. `uip rules describe` is not available in Studio Web, so a deployed rule's inputs and outputs cannot be read here. Binding a rule into a process, workflow, or case belongs to that artifact's skill.
<!--skill-flavor:deployed-rules:end-->
