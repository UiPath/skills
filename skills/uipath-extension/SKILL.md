---
name: uipath-extension
description: "UiPath Maestro Extensions community nodes (`uip extension validate|upload|submit`; a JavaScript job function with a `maestro-extensions.json` template). Adopt a `uip function new` project, run the community-index gates, upload a dev build or a release to Orchestrator, and open the pull request that registers the node in the community index. For a plain coded function with no node →uipath-functions. For LLM or agent projects →uipath-agents. For authoring or running a `.flow` →uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Extension

A Maestro community node is a JavaScript job function that Maestro Flow can call as a node. You build it with `uip function` and add the Maestro Extensions parts at submit time. The `uip extension` tool has three commands, `validate`, `upload` and `submit`. It carries the gate library, so no other command or package is needed.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## When to Use This Skill

- Check a function project against the community-index gates (`uip extension validate`)
- Upload a dev build to a personal workspace, or a release to a tenant folder (`uip extension upload`)
- Register a node in the community index by opening the pull request (`uip extension submit`)
- Turn a plain `uip function new` project into a node (the `submit` adopt step)
- Read a gate report or an adopt diff and fix what it names

Do NOT use this skill for:
- Writing or debugging the function itself, or a function that is not a node → `uipath-functions`
- LLM or agent projects → `uipath-agents`

## Critical Rules

1. **Create the project with `uip function new` first.** The tool has no `init` or scaffold command. `submit` adopts the project it runs in.
2. **Run `submit` before `upload`.** `upload` fails before any other call when the project has no `maestro-extensions.json`, when its `package.json` name is not `maestro-extensions.<PUBLISHER>.<NAME>`, or when the template has any problem. It adds `run uip extension submit <publisher>.<name> --yes first` to every one of these. Read the problem line above that hint. If it names a template field, such as a `TODO`, fix the field and run `validate`. Do not run `submit --yes` on an adopted project, because it skips the adopt step and takes the pull request path.
3. **A node is one job function.** The gates fail a package whose `operate.json` `targetRuntime` is not `javascript`, one with more than one entry point, and one whose `bindings_v2.json` holds an `HttpTrigger` resource.
4. **Pass the identity as `<PUBLISHER>.<NAME>`.** It holds no slash and exactly one dot. On a terminal `submit` asks for it. Off a terminal, pass it as the argument, or the run fails with `pass <publisher>.<name>`.
5. **Show the adopt diff before you write it.** The first `submit` run prints the files it would write and stops. Show them to the user. Run `submit --yes` only after the user agrees.
6. **Replace every `TODO` in `maestro-extensions.json`.** The gates fail a field that still holds the placeholder. The template lists `license`, `display.label`, `display.description`, the first tag, the first `egress` entry and `maestro.min`.
7. **Never open the index pull request without the user's go-ahead.** Run `submit --dry-run` first, show the result, then run `submit` without it. The first registration of a node needs `--security-contact <SECURITY_CONTACT>`.
8. **`upload` needs a login.** Run `uip login` first. No `uip extension` command takes `--tenant`, because they read the tenant from that session.
9. **A release upload names one folder.** `upload --release` needs `--yes` and exactly one of `--folder-path` or `--folder-key`. It runs the gates first and never takes `--feed-id`.
10. **Read the outcome code, not only the exit code.** An expected stop such as `AdoptWritten` or `ConfirmationRequired` exits 1.

## Choose a Destination

Ask the user where the node goes with `AskUserQuestion`, then follow that row.

| Destination | Command | Notes |
|---|---|---|
| Personal workspace, for a quick try | `uip extension upload --run --input '<INPUT_JSON>' --output json` | Uploads `<PACKAGE_VERSION>-dev.<TIMESTAMP>` to your personal workspace feed and runs a job. No gates run. |
| A tenant folder | `uip extension upload --release --folder-path "<FOLDER_PATH>" --yes --output json` | Runs the gates, then uploads the package version. |
| The community index | `uip extension submit --security-contact "<SECURITY_CONTACT>" --output json` | Needs `gh` signed in with push access to the index repository. |

Every command takes `--path <PROJECT_DIR>`. The default is the current folder.

## Workflow

1. Create the project and enter it.

   ```bash
   uip function new <PROJECT_NAME> --language ts
   cd <PROJECT_NAME>
   ```

2. Adopt it. This run prints the files and stops.

   ```bash
   uip extension submit <PUBLISHER>.<NAME> --output json
   ```

   Adopt reads the template schema from the index repository through `gh`. Sign `gh` in with access to that repository before the first adopt, whatever the destination.

   After the user agrees, write them. The command exits 1 with `AdoptWritten`, which is the expected stop.

   ```bash
   uip extension submit <PUBLISHER>.<NAME> --yes --output json
   ```

   Adopt writes `maestro-extensions.json`, renames the package to `maestro-extensions.<PUBLISHER>.<NAME>`, and adds `maestro/connection.ts` when the function reads connection inputs. It reports a missing icon file in the project's assets folder and entry point inputs that have no description, and it never deletes a file.

3. Fill the `TODO` fields, then check the project.

   ```bash
   uip extension validate --output json
   ```

   `validate` runs the gates in local mode. It needs no login and reads no index. Its pack step still creates `.uipath/`.

4. Run the command from the destination table. For the index, check first.

   ```bash
   uip extension submit --security-contact "<SECURITY_CONTACT>" --dry-run --output json
   ```

   Run it again without `--dry-run` after the user approves the pull request.

## Outcome Codes

A success prints an envelope with the code `ExtensionValidate`, `ExtensionUpload` or `ExtensionSubmit`. Any other outcome prints a failure envelope and exits 1.

| Code | Meaning | Next step |
|---|---|---|
| `GatesFailed` | A gate failed. `Data` holds the report. | Fix each finding, then run `validate` again. After 3 failing runs, show the user the report and ask how to proceed. |
| `ConfirmationRequired` | The command needs `--yes`. | Show the user what it will do, then repeat with `--yes`. |
| `InputRequired` | An input is missing or two inputs conflict. | Read `Instructions` and pass the missing input. For `submit`, keep `--dry-run` until the user approves the pull request. |
| `AdoptWritten` | `submit` wrote the adopt files. | Review them, fill the `TODO` fields, run `validate`, then run `submit --dry-run` and show the result. |
| `Failed` | The project or a tool it needs has a problem. | Read `Message` and `Instructions`. A missing `gh` says how to install it. |

## What NOT to Do

- Do not install or call the `maestro-extensions` command. `uip extension` replaces it.
- Do not add `@uipath/maestro-extensions-sdk` to the node. A node depends on `@uipath/coded-functions-js-sdk`.
- Do not copy a `maestro-extensions.json` from an older node. Adopt writes the template schema the index accepts.
