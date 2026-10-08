# Business Rules Failure Modes

Failures `uip rules` reports, with the fix for each. DMN or FEEL syntax errors follow the standard and are not listed.

## `uip rules init`

| Message | Fix |
|---|---|
| `error: unknown command 'rules'` | The installed CLI predates `uip rules`; tell the user to update it with `npm install -g @uipath/cli@latest`. |
| `Invalid project name "<NAME>". Name can only contain letters, numbers, underscores (_), and hyphens (-).` | Rename the project with only those characters. |
| `Directory "<NAME>" already exists and is not empty. Use --force to overwrite.` | Pick another name, or pass `--force`. `--force` never overwrites an existing `.dmn` (`Data.RuleStatus: "Preserved"`). |

## Any command that takes a project path (`refresh`, `validate`, `debug`)

| Message | Fix |
|---|---|
| `<DIR> is not a business rules project.` | Pass the folder that holds `project.uiproj`, not the solution folder. |
| `Could not read <FILE>: it is not valid JSON.` | `project.uiproj` is malformed; fix it, or recreate it with `uip rules init <RULE_NAME> --force`. |

## `uip rules refresh`

| Message | Fix |
|---|---|
| `No .dmn file found in <DIR>.` | Put the rule's `.dmn` at the top level of the project, or scaffold one with `uip rules init`. |
| `Could not read <FILES>, so no package file was written. <REASONS>` | Fix the `.dmn` (`uip rules validate` names the reason), then run `refresh` again. |
| `<FILE> is not an entry-points document: it needs an "entryPoints" array.` | `entry-points.json` is malformed or not JSON; fix it, never delete it — deleting it gives every entry point a new `uniqueId` and breaks the consumers bound to them. |

## `uip rules validate`

Errors exit 1 with `Validation failed for <DIR>`; warnings are reported and do not fail. Each finding is a row in `Data.Diagnostics` with `File`, `Code`, `Severity`, `Message`, and, where the CLI names a fix, `Instructions`. Apply each fix, then run `refresh` and `validate` again. `RULES_ENTRY_POINTS_STALE` means `entry-points.json` no longer matches the `.dmn`; run `uip rules refresh <PROJECT_DIR>`.

## `uip rules debug`

| Message | Fix |
|---|---|
| `Business Rules is not enabled on tenant '<TENANT>'.` | Stop; the user asks their UiPath contact to enable it, or switches to a tenant that has it with `uip login tenant set <TENANT_NAME>`. |
| `<DIR> holds no .uipx, so the rules project is not inside a solution.` | Move the project directly inside its solution folder, or scaffold it with `rules init`. |
| `Studio Web returned no project named '<NAME>' for the uploaded solution.` | The project is missing from the solution's `.uipx`; register it with `uip solution projects add` (uipath-solution skill). |
| `Studio Web did not let the rules engine read the uploaded project.` | The account cannot open the uploaded solution in Studio Web; ask the user to check their access. |
| `--inputs must be a JSON object of input values.` | Pass one object keyed by input-argument name, not an array. |
| `Input file '<FILE>' could not be read: <REASON>.` | Point `--inputs @<FILE>` at an existing JSON file, or pass the object inline. |
| `Could not find your personal workspace to run the rules engine in.` | Re-run with `--folder-path <FOLDER_PATH>` or `--folder-key <FOLDER_KEY>` pointing at a folder the user can read. |
| `The rules engine did not answer within <SECONDS> seconds.` | Re-run, or pass a larger `--timeout`. |
| An input reported as unknown | Every input key must match an `inputData` name exactly; names are case-sensitive. |
| An input reported as a type mismatch | The value does not fit the input argument's `typeRef`; fix the value or the `typeRef`. |

No `Data.traceId` means the engine did not trace the run (tracing is off for the tenant, or publishing it failed); compare the inputs against each row by hand.

## `uip rules list` / `get` / `versions` / `describe`

| Message | Fix |
|---|---|
| `Missing required option --folder-path or --folder-key.` | Pass the rule's folder; `uip or folders list` finds folder paths. |
| `Options --folder-path and --folder-key cannot be used together.` | Pass one of them. |
| `Business rule '<NAME>' was not found in folder '<FOLDER_PATH>'.` | Run `uip rules list --folder-path "<FOLDER_PATH>"` to see the rules in that folder. |
| `Business rule '<NAME>' has no argument contract on its resource.` | The rule was deployed without `entry-points.json`; redeploy it from its solution with `uip solution publish` and `uip solution deploy run`. |
